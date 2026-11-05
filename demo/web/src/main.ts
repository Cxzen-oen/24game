import {
  abandon, bootstrapAuth, createGame, getGame, getLeaderboard, getRecords,
  login, logout, register, skip, submit,
  type Account, type GameView, type Leaderboard, type Level, type Mode, type Records
} from './api';
import {
  canChooseOperator, chooseOperator, displayValue, expressionOf, initialState,
  isComplete, previewText, selectCard, toOperations, undo,
  type EditorState
} from './merge';

type View = 'home' | 'play' | 'result' | 'records' | 'leaderboard';
type Tone = '' | 'ok' | 'err';

const A_DURATION_MS = 300000;
const OP_ORDER = ['+', '-', '*', '/'];
const OP_SYMBOL: Record<string, string> = { '+': '+', '-': '−', '*': '×', '/': '÷' };
const MODE_NAME: Record<string, string> = { A: 'A 限时', B: 'B 定量' };
const LEVEL_NAME: Record<string, string> = { L1: 'L1 加减级', L2: 'L2 四则级' };

const app = document.getElementById('app') as HTMLDivElement;

let view: View = 'home';
let game: GameView | null = null;
let editor: EditorState | null = null;
let level: Level = 'L2';
let mode: Mode | null = null;
let clockTimer: number | undefined;
let clockBase = 0;
let clockAnchor = 0;
let clockDown = true;
let expiring = false;
let busy = false;
let lastMessage = '';
let lastTone: Tone = '';
let isNewRecord = false;
let renderSeq = 0;
let account: Account | null = null;
let lbMode: Mode = 'A';
let lbLevel: Level = 'L1';
let lbPage = 0;
let recMode: Mode | 'ALL' = 'ALL';
let recLevel: Level | 'ALL' = 'ALL';

/* ---------- 基础工具 ---------- */

function el(html: string): HTMLElement {
  const d = document.createElement('div');
  d.innerHTML = html;
  return d.firstElementChild as HTMLElement;
}

function pad(n: number): string {
  return (n < 10 ? '0' : '') + n;
}

/** 默认精确到秒（向上取整，倒计时不会提前显示 0）；tenths 为 true 时显示 0.1 秒。 */
function fmtTime(ms: number, tenths = false): string {
  const safe = Number.isFinite(ms) ? Math.max(0, ms) : 0;
  if (tenths) {
    const t = Math.floor(safe / 100);
    return pad(Math.floor(t / 600)) + ':' + pad(Math.floor((t % 600) / 10)) + '.' + (t % 10);
  }
  const total = Math.ceil(safe / 1000);
  return pad(Math.floor(total / 60)) + ':' + pad(total % 60);
}

function fmtTimeShort(ms: number): string {
  const total = Math.ceil(Math.max(0, ms) / 1000);
  return Math.floor(total / 60) + ':' + pad(total % 60);
}

function num(value: unknown): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function esc(value: unknown): string {
  const table: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  return String(value).replace(/[&<>"']/g, function (ch) { return table[ch]; });
}

function day(iso: unknown): string {
  return String(iso || '').slice(5, 10);
}

function delay(ms: number): Promise<void> {
  return new Promise(function (resolve) { window.setTimeout(resolve, ms); });
}

function penaltyText(g: GameView, kind: 'wrong' | 'skip'): string {
  const sec = kind === 'skip' ? 10 : 5;
  return g.mode === 'A' ? '剩余时间 −' + sec + ' 秒' : '总用时 +' + sec + ' 秒';
}

function header(): string {
  const playing = view === 'play' && game !== null && game.status === 'RUNNING';
  const identity = account
    ? '<span class="avatar">' + esc(account.nickname.slice(0, 1)) + '</span>' +
      '<span class="account-name">' + esc(account.nickname) + '</span>'
    : '';
  const who = account
    ? (playing
        ? '<span class="account-chip" title="对局进行中，暂不能退出登录">' + identity + '</span>'
        : '<button type="button" class="account-chip" data-auth="logout" title="退出登录">' + identity + '</button>')
    : '<button type="button" class="btn ghost btn-sm" data-auth="login">登录 / 注册</button>';
  return '<header class="header"><div class="logo">24</div>' +
    '<div class="brand">24 点 · 单人挑战</div>' +
    '<div class="header-right">' + who + '</div></header>';
}

function bindHeader(root: HTMLElement): void {
  root.querySelectorAll('[data-auth]').forEach(function (node) {
    node.addEventListener('click', function () {
      const action = (node as HTMLElement).dataset.auth;
      if (action === 'login') openAuth('login');
      else if (action === 'logout') askLogout();
    });
  });
}

const TAB_ICONS: Record<string, string> = {
  home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10.5 12 4l8 6.5"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-5h4v5"/></svg>',
  records: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="4" width="14" height="16" rx="2"/><path d="M9 9h6M9 13h6M9 17h4"/></svg>',
  leaderboard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 4h8v4a4 4 0 0 1-8 0V4Z"/><path d="M8 5H5v2a3 3 0 0 0 3 3M16 5h3v2a3 3 0 0 1-3 3"/><path d="M12 12v5M9 20h6"/></svg>'
};

const MODE_ICON: Record<string, string> = {
  A: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="13" r="7"/><path d="M12 13V9.5"/><path d="M9 3h6"/><path d="M12 3v2"/></svg>',
  B: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/></svg>'
};

const SUITS: Record<string, string> = { c0: '♠', c1: '♥', c2: '♦', c3: '♣' };

function faceOf(n: number): string {
  if (n === 1) return 'A';
  if (n === 11) return 'J';
  if (n === 12) return 'Q';
  if (n === 13) return 'K';
  return String(n);
}

function tabbar(active: View): string {
  const items: { id: View; label: string }[] = [
    { id: 'home', label: '首页' },
    { id: 'records', label: '成绩' },
    { id: 'leaderboard', label: '排行' }
  ];
  return '<nav class="tabbar" aria-label="主导航"><div class="tabbar-inner">' +
    items.map(function (item) {
      return '<button type="button" class="tab' + (active === item.id ? ' active' : '') +
        '" data-nav="' + item.id + '">' + TAB_ICONS[item.id] + '<span>' + item.label + '</span></button>';
    }).join('') +
    '</div></nav>';
}

function bindNav(root: HTMLElement): void {
  root.querySelectorAll('[data-nav]').forEach(function (b) {
    b.addEventListener('click', function () {
      const target = (b as HTMLElement).dataset.nav as View;
      if (target === 'home') {
        stopClock();
        game = null;
        editor = null;
        expiring = false;
      }
      view = target;
      render();
    });
  });
}

function confirmDialog(message: string, onConfirm: () => void): void {
  const box = el('<div class="overlay"><div class="modal" role="dialog" aria-modal="true">' +
    '<h4>请确认</h4><p></p>' +
    '<div class="actions"><button type="button" class="btn ghost" data-cancel>取消</button>' +
    '<button type="button" class="btn danger" data-ok>确定</button></div></div></div>');
  (box.querySelector('p') as HTMLElement).textContent = message;
  const close = function () { box.remove(); };
  (box.querySelector('[data-cancel]') as HTMLButtonElement).addEventListener('click', close);
  box.addEventListener('click', function (e) { if (e.target === box) close(); });
  (box.querySelector('[data-ok]') as HTMLButtonElement).addEventListener('click', function () {
    close();
    onConfirm();
  });
  document.body.appendChild(box);
  (box.querySelector('[data-ok]') as HTMLButtonElement).focus();
}

/* ---------- 账号 ---------- */

function toast(message: string): void {
  const box = el('<div class="toast" role="status"></div>');
  box.textContent = message;
  document.body.appendChild(box);
  window.setTimeout(function () { box.remove(); }, 2600);
}

function openAuth(initial: 'login' | 'register'): void {
  document.querySelectorAll('.overlay').forEach(function (o) { o.remove(); });
  let tab: 'login' | 'register' = initial;
  const box = el(
    '<div class="overlay"><div class="modal auth-modal" role="dialog" aria-modal="true">' +
      '<button type="button" class="modal-close" data-close aria-label="关闭">×</button>' +
      '<h4 class="auth-title">登录 24 点</h4>' +
      '<div class="auth-tabs">' +
        '<button type="button" data-tab="login">登录</button>' +
        '<button type="button" data-tab="register">注册</button>' +
      '</div>' +
      '<form class="auth-form" novalidate>' +
        '<label class="auth-field"><span>用户名</span>' +
          '<input name="username" autocomplete="username" maxlength="20" placeholder="4-20 位，字母开头" required></label>' +
        '<label class="auth-field" data-nickname><span>昵称</span>' +
          '<input name="nickname" maxlength="12" placeholder="2-12 个字符，排行榜显示"></label>' +
        '<label class="auth-field"><span>密码</span>' +
          '<input name="password" type="password" minlength="8" maxlength="64" required></label>' +
        '<p class="auth-error" data-error></p>' +
        '<button type="submit" class="btn auth-submit">登录</button>' +
        '<p class="auth-hint">游客成绩会在登录或注册时自动并入账号；只有账号成绩参与排行榜。</p>' +
      '</form></div></div>');
  const form = box.querySelector('form') as HTMLFormElement;
  const nicknameRow = box.querySelector('[data-nickname]') as HTMLElement;
  const errorEl = box.querySelector('[data-error]') as HTMLElement;
  const submit = box.querySelector('.auth-submit') as HTMLButtonElement;
  const password = form.querySelector('input[name="password"]') as HTMLInputElement;

  function close(): void {
    box.remove();
  }

  function paint(): void {
    box.querySelectorAll('[data-tab]').forEach(function (b) {
      b.classList.toggle('active', (b as HTMLElement).dataset.tab === tab);
    });
    nicknameRow.hidden = tab !== 'register';
    (box.querySelector('.auth-title') as HTMLElement).textContent = tab === 'register' ? '注册账号' : '登录 24 点';
    submit.textContent = tab === 'register' ? '注册并开始' : '登录';
    password.autocomplete = tab === 'register' ? 'new-password' : 'current-password';
    errorEl.textContent = '';
  }

  box.querySelectorAll('[data-tab]').forEach(function (b) {
    b.addEventListener('click', function () {
      tab = (b as HTMLElement).dataset.tab as 'login' | 'register';
      paint();
    });
  });
  (box.querySelector('[data-close]') as HTMLElement).addEventListener('click', close);
  box.addEventListener('click', function (e) { if (e.target === box) close(); });

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    if (submit.disabled) return;
    const data = new FormData(form);
    const username = String(data.get('username') || '').trim();
    const pass = String(data.get('password') || '');
    const nickname = String(data.get('nickname') || '').trim();
    if (!username || !pass) {
      errorEl.textContent = '请填写用户名和密码';
      return;
    }
    submit.disabled = true;
    const label = submit.textContent;
    submit.textContent = '请稍候…';
    const task = tab === 'register'
      ? register(username, pass, nickname)
      : login(username, pass);
    task.then(function (result) {
      account = result.account;
      close();
      if (result.claimedGames > 0) {
        toast('已并入本机 ' + result.claimedGames + ' 局记录');
      } else {
        toast('已登录：' + result.account.nickname);
      }
      render();
    }).catch(function (e: Error) {
      errorEl.textContent = e.message;
      submit.disabled = false;
      submit.textContent = label;
    });
  });

  document.body.appendChild(box);
  (form.querySelector('input[name="username"]') as HTMLInputElement).focus();
  paint();
}

function askLogout(): void {
  confirmDialog('退出登录后，账号成绩仍会保留。确定退出？', function () {
    void logout().then(function () {
      account = null;
      toast('已退出登录');
      render();
    });
  });
}

/* ---------- 计时 ---------- */

function anchorClock(g: GameView): void {
  clockDown = g.mode === 'A';
  clockBase = g.mode === 'A'
    ? Math.max(0, g.remainingMs === null ? 0 : g.remainingMs)
    : Math.max(0, g.elapsedMs + g.penaltyMs);
  clockAnchor = Date.now();
}

function clockValue(): number {
  const delta = Date.now() - clockAnchor;
  return clockDown ? clockBase - delta : clockBase + delta;
}

function paintClock(): void {
  const box = document.getElementById('clock');
  if (!box) return;
  const value = Math.max(0, clockValue());
  box.textContent = clockDown ? fmtTime(value) : fmtTime(value, true);
  const danger = clockDown && value <= 10000;
  const warn = clockDown && value <= 30000;
  box.className = 'clock' + (clockDown ? '' : ' count-up') + (danger ? ' danger' : warn ? ' warn' : '');
  const fill = document.getElementById('progressFill');
  if (fill && clockDown) {
    fill.style.width = Math.max(0, Math.min(100, value / A_DURATION_MS * 100)) + '%';
  }
}

function tickClock(): void {
  paintClock();
  if (clockDown && clockValue() <= 0) void timeUp();
}

function startClock(): void {
  stopClock();
  if (view !== 'play' || !game || game.status !== 'RUNNING' || expiring) return;
  clockTimer = window.setInterval(tickClock, 100);
  paintClock();
}

function stopClock(): void {
  if (clockTimer !== undefined) window.clearInterval(clockTimer);
  clockTimer = undefined;
}

async function timeUp(): Promise<void> {
  if (expiring || !game || view !== 'play') return;
  const gameId = game.gameId;
  expiring = true;
  stopClock();
  paintClock();
  const qcard = document.getElementById('qcard');
  if (qcard) qcard.classList.add('locked');
  setFeedbackDom('时间到，正在结算…');
  for (let i = 0; i < 12; i++) {
    try {
      const g = await getGame(gameId);
      if (!game || game.gameId !== gameId || view !== 'play') {
        expiring = false;
        return;
      }
      if (g.status === 'FINISHED') {
        expiring = false;
        handleNext(g);
        return;
      }
    } catch (e) {
      /* 重试 */
    }
    await delay(250);
  }
  expiring = false;
  setFeedbackDom('结算失败，请检查网络后重试', 'err');
}

/* ---------- 首页 ---------- */

function renderHome(): HTMLElement {
  const root = el('<div class="wrap home"></div>');

  const modeCards = (['A', 'B'] as Mode[]).map(function (m) {
    const selected = mode === m;
    const isA = m === 'A';
    return '<button type="button" class="mode-card mode-' + m.toLowerCase() + (selected ? ' selected' : '') + '"' +
      ' data-mode="' + m + '" data-code="' + m + '" aria-pressed="' + (selected ? 'true' : 'false') + '">' +
      '<span class="mode-title"><span class="mode-icon">' + MODE_ICON[m] + '</span>' +
        '<span class="mode-name">' + (isA ? 'A 限时挑战' : 'B 定量挑战') + '</span></span>' +
      '<span class="mode-desc">' + (isA ? '300 秒 · 答对越多越好' : '答对 10 题 · 用时越短越好') + '</span>' +
      '<span class="mode-check" aria-hidden="true">✓</span>' +
    '</button>';
  }).join('');

  const config = '<section class="config" id="config"' + (mode === null ? ' hidden' : '') + '>' +
    '<h2 class="step-title">选择难度</h2>' +
    '<div class="level-grid">' +
      '<button type="button" class="level-card' + (level === 'L1' ? ' selected' : '') + '" data-level="L1" aria-pressed="' + (level === 'L1') + '">L1 加减级</button>' +
      '<button type="button" class="level-card' + (level === 'L2' ? ' selected' : '') + '" data-level="L2" aria-pressed="' + (level === 'L2') + '">L2 四则级</button>' +
    '</div>' +
    '<button type="button" class="btn start' + (mode === 'B' ? ' mode-b' : '') + '" id="start">' +
      '<span>开始挑战</span><span class="start-arrow" aria-hidden="true">→</span>' +
    '</button>' +
  '</section>';

  root.innerHTML = header() +
    '<section class="home-hero"><h1>先选模式，<br><span>再挑难度</span></h1></section>' +
    '<section class="step">' +
      '<h2 class="step-title">选择模式</h2>' +
      '<div class="mode-grid">' + modeCards + '</div>' +
    '</section>' +
    config +
    '<div class="best-strip" id="homeBest"></div>' +
    (account ? '' : '<p class="home-hint">游客成绩只存本机，' +
      '<button type="button" class="link-btn" data-auth="login">登录</button>后自动并入账号并参与排行</p>') +
    tabbar('home');

  const modeEls = Array.from(root.querySelectorAll('[data-mode]')) as HTMLButtonElement[];
  const levelEls = Array.from(root.querySelectorAll('[data-level]')) as HTMLButtonElement[];
  const configEl = root.querySelector('#config') as HTMLElement;
  const startEl = root.querySelector('#start') as HTMLButtonElement;

  function syncSelection(reveal: boolean): void {
    const hasMode = mode !== null;
    modeEls.forEach(function (card) {
      const on = card.dataset.mode === mode;
      card.classList.toggle('selected', on);
      card.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    levelEls.forEach(function (card) {
      const on = card.dataset.level === level;
      card.classList.toggle('selected', on);
      card.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    startEl.classList.toggle('mode-b', mode === 'B');
    configEl.hidden = !hasMode;
    if (reveal && hasMode) {
      configEl.classList.remove('reveal');
      void configEl.offsetWidth;
      configEl.classList.add('reveal');
    }
  }

  modeEls.forEach(function (card) {
    card.addEventListener('click', function () {
      const next = card.dataset.mode as Mode;
      if (next === mode) return;
      const wasHidden = configEl.hidden;
      mode = next;
      syncSelection(wasHidden);
    });
  });

  levelEls.forEach(function (card) {
    card.addEventListener('click', function () {
      level = card.dataset.level as Level;
      syncSelection(false);
    });
  });

  startEl.addEventListener('click', startGame);
  syncSelection(false);
  bindNav(root);
  void loadHomeBest(root.querySelector('#homeBest') as HTMLElement);
  return root;
}

async function loadHomeBest(box: HTMLElement): Promise<void> {
  try {
    const rec = await getRecords(5);
    if (!rec.bests.length) {
      box.innerHTML = '';
      return;
    }
    box.innerHTML = rec.bests.map(function (b: Record<string, unknown>) {
      const m = String(b.mode);
      const lv = String(b.level);
      const score = m === 'A'
        ? '答对 ' + num(b.best_correct) + ' 题 · ' + fmtTime(num(b.best_scoring_ms))
        : fmtTime(num(b.best_scoring_ms), true);
      return '<div class="best-item"><span>' + (MODE_NAME[m] || m) + ' · ' + lv +
        '</span><b>' + score + '</b></div>';
    }).join('');
  } catch (e) {
    box.innerHTML = '';
  }
}

async function startGame(): Promise<void> {
  const selectedMode = mode;
  const selectedLevel = level;
  if (busy || selectedMode === null) return;
  busy = true;
  stopClock();
  expiring = false;
  try {
    const g = await createGame(selectedMode, selectedLevel);
    game = g;
    editor = g.puzzle ? initialState(g.puzzle.numbers) : null;
    lastMessage = '';
    lastTone = '';
    isNewRecord = false;
    view = 'play';
    anchorClock(g);
    busy = false;
    render();
  } catch (e) {
    alert('开局失败：' + (e as Error).message);
  } finally {
    busy = false;
  }
}

/* ---------- 作答页 ---------- */

function setFeedbackDom(msg: string, tone: Tone = ''): void {
  lastMessage = msg;
  lastTone = tone;
  const fb = document.getElementById('fb');
  if (fb) {
    fb.textContent = msg;
    fb.className = 'feedback' + (tone ? ' ' + tone : '');
  }
}

function renderPlay(): HTMLElement {
  const root = el('<div class="wrap play"></div>');
  const g = game as GameView;
  const symbols = g.level === 'L1' ? ['+', '-'] : OP_ORDER;
  const progress = g.mode === 'A'
    ? Math.max(0, Math.min(100, (g.remainingMs === null ? 0 : g.remainingMs) / A_DURATION_MS * 100))
    : Math.min(100, g.correct / Math.max(1, g.targetCorrect) * 100);

  root.innerHTML = header() +
    '<div class="hud">' +
      '<span class="chip">' + (g.mode === 'A' ? 'A 限时' : 'B 定量') + ' · ' + g.level + '</span>' +
      '<span class="hud-score">答对 <b>' + g.correct + '</b>' +
        (g.mode === 'B' ? '<span class="target"> / ' + g.targetCorrect + '</span>' : '') +
      '</span>' +
    '</div>' +
    '<div class="clock-block">' +
      '<span class="clock' + (g.mode === 'A' ? '' : ' count-up') + '" id="clock">' +
        (g.mode === 'A' ? fmtTime(clockValue()) : fmtTime(Math.max(0, clockValue()), true)) +
      '</span>' +
    '</div>' +
    '<div class="progress"><div id="progressFill" style="width:' + progress + '%"></div></div>' +
    '<div class="board">' +
      '<section class="qcard" id="qcard">' +
        '<div class="tiles" id="tiles"></div>' +
        '<div class="expr" id="expr"></div>' +
      '</section>' +
      '<div class="ops' + (symbols.length === 2 ? ' two' : '') + '" id="ops"></div>' +
      '<div class="feedback' + (lastMessage && lastTone ? ' ' + lastTone : '') + '" id="fb" aria-live="polite">' +
        lastMessage + '</div>' +
    '</div>' +
    '<div class="play-actions">' +
      '<button type="button" class="btn ghost" id="undo">撤销</button>' +
      '<button type="button" class="btn ghost" id="skip">跳题 ' + (g.mode === 'A' ? '−10s' : '+10s') + '</button>' +
      '<button type="button" class="btn ghost" id="quit">退出</button>' +
    '</div>';

  const tiles = root.querySelector('#tiles') as HTMLElement;
  const ops = root.querySelector('#ops') as HTMLElement;
  const expr = root.querySelector('#expr') as HTMLElement;

  function clearFeedback(): void {
    lastMessage = '';
    lastTone = '';
    const fb = root.querySelector('#fb') as HTMLElement | null;
    if (fb) {
      fb.textContent = '';
      fb.className = 'feedback';
    }
  }

  function paint(): void {
    const state = editor;
    if (!state) return;
    tiles.innerHTML = '';
    state.cards.forEach(function (c) {
      const text = displayValue(c);
      const suit = SUITS[c.id];
      const b = el('<button type="button" class="tile"></button>') as HTMLButtonElement;
      if (suit) {
        const face = c.origin === null ? text : faceOf(c.origin);
        b.classList.add(suit === '♥' || suit === '♦' ? 'red' : 'black');
        b.innerHTML = '<span class="card-corner tl"><span class="card-rank">' + face + '</span>' +
          '<span class="card-suit">' + suit + '</span></span>' +
          '<span class="card-value">' + text + '</span>' +
          '<span class="card-corner br"><span class="card-rank">' + face + '</span>' +
          '<span class="card-suit">' + suit + '</span></span>';
      } else {
        b.classList.add('merged');
        b.innerHTML = '<span class="card-value">' + text + '</span>';
      }
      if (text.length >= 5) b.classList.add('tiny');
      else if (text.length >= 4) b.classList.add('small');
      b.classList.toggle('selected', state.selected === c.id);
      b.title = expressionOf(c);
      b.setAttribute('aria-label', expressionOf(c));
      b.disabled = busy || expiring;
      b.addEventListener('click', function () { onTile(c.id); });
      tiles.appendChild(b);
    });
    tiles.classList.toggle('single', state.cards.length === 1);

    ops.innerHTML = '';
    symbols.forEach(function (sym) {
      const b = el('<button type="button" class="op-key">' + OP_SYMBOL[sym] + '</button>') as HTMLButtonElement;
      const canUse = canChooseOperator(state) && !busy && !expiring;
      b.classList.toggle('active', state.pendingOp === sym);
      b.classList.toggle('ready', canUse && state.pendingOp !== sym);
      b.disabled = !canUse;
      b.setAttribute('aria-label', '算符 ' + OP_SYMBOL[sym]);
      b.addEventListener('click', function () { onOperator(sym); });
      ops.appendChild(b);
    });

    const pv = previewText(state);
    expr.textContent = pv.text;
    expr.className = 'expr ' + pv.tone;
  }

  function onTile(id: string): void {
    if (busy || expiring || !editor) return;
    clearFeedback();
    const before = editor;
    try {
      const next = selectCard(before, id);
      const completed = !isComplete(before) && isComplete(next);
      editor = next;
      paint();
      if (completed) void submitAnswer();
    } catch (err) {
      setFeedbackDom((err as Error).message, 'err');
    }
  }

  function onOperator(op: string): void {
    if (busy || expiring || !editor) return;
    clearFeedback();
    try {
      editor = chooseOperator(editor, op);
      paint();
    } catch (err) {
      setFeedbackDom((err as Error).message, 'err');
    }
  }

  async function submitAnswer(): Promise<void> {
    if (busy || expiring || !game || !game.puzzle || !editor) return;
    const state = editor;
    if (!isComplete(state)) return;
    const valueText = displayValue(state.cards[0]);
    busy = true;
    setFeedbackDom('判定中…');
    paint();
    try {
      const next = await submit(game.gameId, game.puzzle.puzzleId, game.revision, toOperations(state));
      busy = false;
      handleNext(next, valueText);
    } catch (e) {
      busy = false;
      setFeedbackDom('提交失败：' + (e as Error).message, 'err');
      await sync();
    }
  }

  paint();

  (root.querySelector('#undo') as HTMLButtonElement).addEventListener('click', function () {
    if (busy || expiring) return;
    clearFeedback();
    editor = undo(editor as EditorState);
    paint();
  });

  (root.querySelector('#skip') as HTMLButtonElement).addEventListener('click', async function () {
    if (busy || expiring) return;
    busy = true;
    try {
      const next = await skip(g.gameId, g.puzzle!.puzzleId, g.revision);
      busy = false;
      handleNext(next);
    } catch (e) {
      busy = false;
      setFeedbackDom('跳题失败：' + (e as Error).message, 'err');
      await sync();
    }
  });

  (root.querySelector('#quit') as HTMLButtonElement).addEventListener('click', function () {
    if (busy || expiring) return;
    confirmDialog('退出后本局无效，不写入历史或最佳成绩。', async function () {
      try {
        await abandon(g.gameId, g.revision);
        stopClock();
        game = null;
        editor = null;
        view = 'home';
        render();
      } catch (e) {
        setFeedbackDom('退出失败：' + (e as Error).message, 'err');
      }
    });
  });

  return root;
}

/* ---------- 下一题 / 结算 ---------- */

function handleNext(next: GameView, answeredValue?: string): void {
  game = next;
  if (next.status === 'FINISHED') {
    stopClock();
    editor = null;
    void finishView();
    return;
  }
  if (!next.puzzle) {
    stopClock();
    editor = null;
    view = 'home';
    render();
    return;
  }
  editor = initialState(next.puzzle.numbers);
  if (next.lastResult === 'correct') {
    lastMessage = '回答正确';
    lastTone = 'ok';
  } else if (next.lastResult === 'wrong') {
    lastMessage = (answeredValue ? '答案 ' + answeredValue + '，不是 24；' : '答案不对；') +
      penaltyText(next, 'wrong');
    lastTone = 'err';
  } else if (next.lastResult === 'skipped') {
    lastMessage = '已跳过；' + penaltyText(next, 'skip');
    lastTone = '';
  } else {
    lastMessage = '';
    lastTone = '';
  }
  anchorClock(next);
  render();
}

async function finishView(): Promise<void> {
  const g = game as GameView;
  isNewRecord = false;
  try {
    const rec: Records = await getRecords(20);
    const best = rec.bests.find(function (b: Record<string, unknown>) {
      return String(b.mode) === g.mode && String(b.level) === g.level;
    });
    if (best && g.result) {
      const sameTime = num(best.best_scoring_ms) === num(g.result.scoring_ms);
      const sameCorrect = g.mode === 'A'
        ? num(best.best_correct) === num(g.result.correct_count)
        : true;
      isNewRecord = sameTime && sameCorrect;
    }
  } catch (e) {
    /* 忽略 */
  }
  view = 'result';
  render();
}

function statCell(label: string, value: string): string {
  return '<div class="stat-cell"><span>' + label + '</span><b>' + value + '</b></div>';
}

function renderResult(): HTMLElement {
  const root = el('<div class="wrap result"></div>');
  const g = game as GameView;
  const r = g.result || {};
  const isA = g.mode === 'A';
  const title = isA ? '时间到' : '完成 ' + g.targetCorrect + ' 题';
  const scoring = num(r.scoring_ms);
  const hasScoring = !isA || num(r.correct_count) > 0;

  root.innerHTML = header() +
    '<section class="result-hero">' +
      '<div class="result-kicker">' + (isA ? 'A 限时' : 'B 定量') + ' · ' + (LEVEL_NAME[g.level] || g.level) + '</div>' +
      '<h1 class="result-title">' + title + '</h1>' +
      '<div class="result-sub">' + (isA
        ? '答对 ' + num(r.correct_count) + ' 题'
        : '总用时 ' + fmtTime(scoring, true)) + '</div>' +
      (isNewRecord ? '<div class="record-badge">新纪录</div>' : '') +
    '</section>' +
    '<section class="card"><h3>本局成绩</h3><div class="stat-grid">' +
      statCell('答对', num(r.correct_count) + ' 题') +
      statCell('答错', num(r.wrong_count) + ' 次') +
      statCell('跳题', num(r.skipped_count) + ' 次') +
      statCell('累计罚时', fmtTime(num(r.penalty_ms))) +
      statCell('实际用时', fmtTime(num(r.actual_ms), true)) +
      statCell(isA
        ? (num(r.correct_count) > 0 ? '第 ' + num(r.correct_count) + ' 题用时' : '用时')
        : '总用时', hasScoring ? fmtTime(scoring, true) : '—') +
    '</div></section>' +
    '<div class="result-actions">' +
      '<button type="button" class="btn" id="again">再来一局</button>' +
      '<button type="button" class="btn ghost" id="torecords">查看我的成绩</button>' +
      '<button type="button" class="btn ghost" id="toleaderboard">查看排行榜</button>' +
      '<button type="button" class="btn ghost" id="home">返回首页</button>' +
    '</div>' +
    (account ? '' : '<p class="home-hint center">登录后本局成绩可上榜</p>');

  (root.querySelector('#again') as HTMLButtonElement).addEventListener('click', startGame);
  (root.querySelector('#torecords') as HTMLButtonElement).addEventListener('click', function () {
    view = 'records';
    render();
  });
  (root.querySelector('#toleaderboard') as HTMLButtonElement).addEventListener('click', function () {
    view = 'leaderboard';
    render();
  });
  (root.querySelector('#home') as HTMLButtonElement).addEventListener('click', function () {
    stopClock();
    game = null;
    editor = null;
    view = 'home';
    render();
  });
  return root;
}

/* ---------- 成绩 / 排行 ---------- */

async function renderRecords(): Promise<HTMLElement> {
  const root = el('<div class="wrap records"></div>');
  root.innerHTML = header() + '<div class="empty">加载中…</div>';
  try {
    const rec: Records = await getRecords(50,
      recMode === 'ALL' ? undefined : recMode,
      recLevel === 'ALL' ? undefined : recLevel);
    let html = header();
    if (!account) {
      html += '<section class="card notice"><p>你正在以游客身份游玩，成绩只保存在这台设备。' +
        '注册账号后自动并入，并参与排行榜。</p>' +
        '<button type="button" class="btn btn-sm" data-auth="login">登录 / 注册</button></section>';
    }
    html += '<section class="card"><h3>我的最佳成绩</h3>';
    if (!rec.bests.length) {
      html += '<div class="empty small">还没有最佳成绩</div>';
    } else {
      html += '<div class="list">';
      rec.bests.forEach(function (b: Record<string, unknown>) {
        const m = String(b.mode);
        const bestCorrect = num(b.best_correct);
        const score = m === 'A'
          ? (bestCorrect > 0
              ? '答对 ' + bestCorrect + ' 题 · 第 ' + bestCorrect + ' 题用时 ' + fmtTimeShort(num(b.best_scoring_ms))
              : '未答对')
          : fmtTime(num(b.best_scoring_ms), true);
        html += '<div class="list-row"><div class="list-main"><b>' +
          (MODE_NAME[m] || m) + ' · ' + String(b.level) + '</b><span>' + score + '</span></div>' +
          '<div class="list-side">' + String(b.achieved_at).replace('T', ' ').slice(0, 16) + '</div></div>';
      });
      html += '</div>';
    }
    html += '</section>';

    const modeSeg = (['ALL', 'A', 'B'] as const).map(function (m) {
      const label = m === 'ALL' ? '全部' : (m === 'A' ? 'A 限时' : 'B 定量');
      return '<button type="button" class="seg-btn sm' + (recMode === m ? ' active' : '') +
        '" data-rec-mode="' + m + '" aria-pressed="' + (recMode === m) + '">' + label + '</button>';
    }).join('');
    const levelSeg = (['ALL', 'L1', 'L2'] as const).map(function (lv) {
      return '<button type="button" class="seg-btn sm' + (recLevel === lv ? ' active' : '') +
        '" data-rec-level="' + lv + '" aria-pressed="' + (recLevel === lv) + '">' + (lv === 'ALL' ? '全部' : lv) + '</button>';
    }).join('');

    html += '<section class="card"><h3>最近挑战</h3>' +
      '<div class="filter-line"><span>模式</span><div class="seg">' + modeSeg + '</div></div>' +
      '<div class="filter-line"><span>等级</span><div class="seg">' + levelSeg + '</div></div>';
    if (!rec.history.length) {
      const filtered = recMode !== 'ALL' || recLevel !== 'ALL';
      html += '<div class="empty small">' + (filtered ? '没有符合筛选条件的挑战' : '还没有完成的挑战') + '</div>';
    } else {
      html += '<div class="list">';
      rec.history.forEach(function (h: Record<string, unknown>) {
        const m = String(h.mode);
        const histCorrect = num(h.correct_count);
        const histScore = m === 'A'
          ? (histCorrect > 0
              ? '答对 ' + histCorrect + ' 题 · 第 ' + histCorrect + ' 题用时 ' + fmtTimeShort(num(h.scoring_ms))
              : '未答对')
          : '答对 ' + histCorrect + ' 题 · 总用时 ' + fmtTime(num(h.scoring_ms), true);
        html += '<div class="list-row"><div class="list-main"><b>' +
          (MODE_NAME[m] || m) + ' · ' + String(h.level) + '</b><span>' + histScore + '</span></div>' +
          '<div class="list-side">' + String(h.finished_at).replace('T', ' ').slice(5, 16) + '</div></div>';
      });
      html += '</div>';
    }
    html += '</section>' + tabbar('records');
    root.innerHTML = html;
    bindNav(root);
    bindHeader(root);
    root.querySelectorAll('[data-rec-mode]').forEach(function (b) {
      b.addEventListener('click', function () {
        recMode = (b as HTMLElement).dataset.recMode as Mode | 'ALL';
        view = 'records';
        render();
      });
    });
    root.querySelectorAll('[data-rec-level]').forEach(function (b) {
      b.addEventListener('click', function () {
        recLevel = (b as HTMLElement).dataset.recLevel as Level | 'ALL';
        view = 'records';
        render();
      });
    });
  } catch (e) {
    root.innerHTML = header() + '<div class="empty">加载失败：' + (e as Error).message + '</div>' + tabbar('records');
    bindNav(root);
    bindHeader(root);
  }
  return root;
}

async function renderLeaderboard(): Promise<HTMLElement> {
  const root = el('<div class="wrap leaderboard"></div>');
  root.innerHTML = header() + '<div class="empty">加载中…</div>' + tabbar('leaderboard');
  bindHeader(root);
  bindNav(root);

  try {
    const data: Leaderboard = await getLeaderboard(lbMode, lbLevel, lbPage, 20);
    const pages = Math.max(1, Math.ceil(data.total / data.size));
    const rows = data.entries.map(function (entry) {
      const mine = account !== null && entry.accountId === account.id;
      const score = lbMode === 'A'
        ? '<b>答对 ' + entry.correct + ' 题</b><span>第 ' + entry.correct + ' 题用时 ' + fmtTimeShort(entry.scoringMs) + '</span>'
        : '<b>' + fmtTime(entry.scoringMs, true) + '</b>';
      return '<div class="board-row' + (mine ? ' mine' : '') + '">' +
        '<span class="board-rank r' + entry.rank + '">' + entry.rank + '</span>' +
        '<span class="board-name">' + esc(entry.nickname) + (mine ? '<i>我</i>' : '') + '</span>' +
        '<span class="board-score">' + score + '</span>' +
        '<span class="board-time">' + day(entry.achievedAt) + '</span></div>';
    }).join('');

    let me = '';
    if (!account) {
      me = '<div class="me-line">登录后可上榜，成绩也会跟账号跨设备保留。' +
        '<button type="button" class="link-btn" data-auth="login">登录 / 注册</button></div>';
    } else if (data.me && typeof data.me.rank === 'number') {
      const mine = data.me;
      const score = lbMode === 'A'
        ? '答对 ' + num(mine.correct) + ' 题 · 第 ' + num(mine.correct) + ' 题用时 ' + fmtTimeShort(num(mine.scoringMs))
        : fmtTime(num(mine.scoringMs), true);
      me = '<div class="me-line"><span class="me-rank">我的排名 <b>第 ' + mine.rank + ' 名</b></span>' +
        '<span class="me-score">' + score + '</span></div>';
    } else {
      me = '<div class="me-line">你还没有这个榜的成绩，完成一局即可上榜。</div>';
    }

    const modeSeg = (['A', 'B'] as Mode[]).map(function (m) {
      return '<button type="button" class="seg-btn' + (lbMode === m ? ' active' : '') +
        '" data-lb-mode="' + m + '">' + (m === 'A' ? 'A 限时' : 'B 定量') + '</button>';
    }).join('');
    const levelSeg = (['L1', 'L2'] as Level[]).map(function (lv) {
      return '<button type="button" class="seg-btn' + (lbLevel === lv ? ' active' : '') +
        '" data-lb-level="' + lv + '">' + lv + '</button>';
    }).join('');

    root.innerHTML = header() +
      '<section class="hero small-hero"><h1>排行榜</h1><p>' +
        (lbMode === 'A' ? '答对题数越多越好，同题数比第 N 题用时' : '答对 10 题，总用时越短越好') +
      '</p></section>' +
      '<div class="seg-row"><div class="seg">' + modeSeg + '</div><div class="seg">' + levelSeg + '</div></div>' +
      '<section class="card board-card">' +
        '<div class="board-head"><span>名次</span><span>玩家</span><span>成绩</span><span>日期</span></div>' +
        (rows || '<div class="empty small">这个榜单还没有成绩</div>') +
        '<div class="board-foot">共 ' + data.total + ' 人上榜' +
          (pages > 1 ? ' · 第 ' + (lbPage + 1) + ' / ' + pages + ' 页' : '') + '</div>' +
        (pages > 1
          ? '<div class="pager">' +
              '<button type="button" class="btn ghost btn-sm" data-page="prev"' + (lbPage === 0 ? ' disabled' : '') + '>上一页</button>' +
              '<button type="button" class="btn ghost btn-sm" data-page="next"' + (lbPage + 1 >= pages ? ' disabled' : '') + '>下一页</button>' +
            '</div>'
          : '') +
      '</section>' +
      '<section class="me-card">' + me + '</section>' +
      tabbar('leaderboard');

    root.querySelectorAll('[data-lb-mode]').forEach(function (b) {
      b.addEventListener('click', function () {
        lbMode = (b as HTMLElement).dataset.lbMode as Mode;
        lbPage = 0;
        view = 'leaderboard';
        render();
      });
    });
    root.querySelectorAll('[data-lb-level]').forEach(function (b) {
      b.addEventListener('click', function () {
        lbLevel = (b as HTMLElement).dataset.lbLevel as Level;
        lbPage = 0;
        view = 'leaderboard';
        render();
      });
    });
    root.querySelectorAll('[data-page]').forEach(function (b) {
      b.addEventListener('click', function () {
        const dir = (b as HTMLElement).dataset.page;
        lbPage = Math.max(0, lbPage + (dir === 'next' ? 1 : -1));
        view = 'leaderboard';
        render();
      });
    });
  } catch (e) {
    root.innerHTML = header() + '<div class="empty">排行榜加载失败：' + esc((e as Error).message) +
      '</div>' + tabbar('leaderboard');
  }

  bindNav(root);
  bindHeader(root);
  return root;
}

/* ---------- 入口 ---------- */

async function sync(): Promise<void> {
  if (!game) return;
  try {
    const g = await getGame(game.gameId);
    handleNext(g);
  } catch (e) {
    /* 忽略 */
  }
}

function render(): void {
  stopClock();
  document.querySelectorAll('.overlay').forEach(function (o) { o.remove(); });
  const seq = ++renderSeq;
  let node: HTMLElement;
  if (view === 'home') {
    node = renderHome();
  } else if (view === 'play' && game) {
    node = renderPlay();
  } else if (view === 'result' && game) {
    node = renderResult();
  } else if (view === 'records') {
    app.innerHTML = '';
    void renderRecords().then(function (n) {
      if (seq !== renderSeq) return;
      app.innerHTML = '';
      app.appendChild(n);
    });
    return;
  } else if (view === 'leaderboard') {
    app.innerHTML = '';
    void renderLeaderboard().then(function (n) {
      if (seq !== renderSeq) return;
      app.innerHTML = '';
      app.appendChild(n);
    });
    return;
  } else {
    node = renderHome();
  }
  app.innerHTML = '';
  app.appendChild(node);
  bindHeader(node);
  if (view === 'play' && game && game.status === 'RUNNING' && !expiring) startClock();
}

document.addEventListener('visibilitychange', function () {
  if (!document.hidden && view === 'play' && game && game.status === 'RUNNING' && !expiring) {
    tickClock();
  }
});

render();
void bootstrapAuth().then(function (acc) {
  if (!acc) return;
  account = acc;
  render();
});