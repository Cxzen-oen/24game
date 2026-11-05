// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const B_GAME = {
  gameId: 'g1', revision: 0, status: 'RUNNING', mode: 'B', level: 'L2',
  serverTime: new Date().toISOString(), guestId: 'guest',
  puzzle: { puzzleId: 'p1', numbers: [3, 3, 8, 8], open: true },
  correct: 0, wrong: 0, skipped: 0, penaltyMs: 0, remainingMs: null,
  elapsedMs: 1200, lastScoringMs: null, targetCorrect: 10, lastResult: null, result: null
};

function jsonResponse(body: unknown) {
  return Promise.resolve({
    ok: true,
    json: function () { return Promise.resolve(body); }
  } as Response);
}

interface StubOptions {
  game?: unknown;
  onSubmit?: unknown;
  onGet?: unknown;
}

function stubApi(options: StubOptions = {}) {
  const game = options.game || B_GAME;
  vi.stubGlobal('fetch', vi.fn(function (url: string) {
    const u = String(url);
    if (u.indexOf('/api/records') >= 0) return jsonResponse({ history: [], bests: [] });
    if (u.indexOf('/submit') >= 0) return jsonResponse(options.onSubmit || game);
    if (u.indexOf('/skip') >= 0) return jsonResponse(options.onSubmit || game);
    if (u.indexOf('/api/games/') >= 0) return jsonResponse(options.onGet || game);
    if (u.indexOf('/api/games') >= 0) return jsonResponse(game);
    return jsonResponse({});
  }));
}

async function flush(times = 8) {
  for (let i = 0; i < times; i++) await vi.advanceTimersByTimeAsync(0);
}

async function startGame(selectedMode: 'A' | 'B' = 'B') {
  await import('../src/main');
  (document.querySelector('[data-mode="' + selectedMode + '"]') as HTMLElement).click();
  (document.getElementById('start') as HTMLButtonElement).click();
  await flush();
}

function tiles(): HTMLElement[] {
  return Array.from(document.querySelectorAll('#tiles .tile')) as HTMLElement[];
}

function tileValues(): string[] {
  return tiles().map(function (t) {
    const v = t.querySelector('.card-value');
    return v ? (v.textContent || '') : (t.textContent || '');
  });
}

function ops(): HTMLButtonElement[] {
  return Array.from(document.querySelectorAll('#ops .op-key')) as HTMLButtonElement[];
}

function clockText(): string {
  return (document.getElementById('clock') as HTMLElement).textContent || '';
}

beforeEach(function () {
  vi.useFakeTimers();
  vi.resetModules();
  document.body.innerHTML = '<div id="app"></div>';
});

afterEach(function () {
  vi.clearAllTimers();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('home', function () {
  beforeEach(function () { stubApi(); });

  it('shows modes first and reveals the level step after picking one', async function () {
    await import('../src/main');
    const app = document.getElementById('app') as HTMLElement;
    expect(app.textContent).toContain('24 点 · 单人挑战');
    expect(app.textContent).not.toContain('服务端判题');
    expect(app.querySelectorAll('[data-mode]')).toHaveLength(2);

    const config = document.getElementById('config') as HTMLElement;
    expect(config.hidden).toBe(true);
    expect((document.getElementById('start') as HTMLElement).closest('#config')).toBe(config);

    (document.querySelector('[data-mode="A"]') as HTMLElement).click();
    expect(config.hidden).toBe(false);
    expect((document.querySelector('[data-mode="A"]') as HTMLElement).className).toContain('selected');
  });

  it('updates mode and level in place without rebuilding the page', async function () {
    await import('../src/main');
    const modeCard = document.querySelector('[data-mode="B"]') as HTMLElement;
    modeCard.click();
    const appNode = document.getElementById('app') as HTMLElement;
    const page = appNode.firstElementChild;

    (document.querySelector('[data-level="L1"]') as HTMLElement).click();
    expect((document.querySelector('[data-level="L1"]') as HTMLElement).className).toContain('selected');
    expect(document.querySelector('[data-mode="B"]')).toBe(modeCard);
    expect(appNode.firstElementChild).toBe(page);
  });
});

describe('play interaction', function () {
  it('shows four tiles and starts with operators disabled', async function () {
    stubApi();
    await startGame();
    expect(tileValues()).toEqual(['3', '3', '8', '8']);
    expect(ops()).toHaveLength(4);
    expect(ops()[0].disabled).toBe(true);
    expect(document.body.textContent).toContain('跳题');
    expect(document.body.textContent).not.toContain('提交答案');
    expect((document.getElementById('expr') as HTMLElement).textContent).toContain('点数字');
    expect((document.getElementById('skip') as HTMLElement).textContent).toContain('+10s');
  });

  it('merges number → operator → number in click order', async function () {
    stubApi({ game: { ...B_GAME, puzzle: { puzzleId: 'p2', numbers: [2, 4, 8, 1], open: true } } });
    await startGame();

    tiles()[0].click();
    expect(ops()[0].disabled).toBe(false);
    ops()[1].click();
    expect(ops()[1].className).toContain('active');

    tiles()[1].click();
    expect(tiles()).toHaveLength(3);
    expect(tileValues()[2]).toBe('-2');
    expect((document.getElementById('expr') as HTMLElement).textContent).toBe('2 − 4 = -2');
  });

  it('uses A/J/Q/K on card corners while showing numeric values', async function () {
    stubApi({ game: { ...B_GAME, puzzle: { puzzleId: 'p5', numbers: [11, 12, 13, 1], open: true } } });
    await startGame();

    const ranks = tiles().map(function (t) {
      const r = t.querySelector('.card-rank');
      return r ? (r.textContent || '') : '';
    });
    expect(ranks).toEqual(['J', 'Q', 'K', 'A']);
    expect(tileValues()).toEqual(['11', '12', '13', '1']);
  });

  it('treats 4 - 2 as 2, not -2', async function () {
    stubApi({ game: { ...B_GAME, puzzle: { puzzleId: 'p3', numbers: [2, 4, 8, 1], open: true } } });
    await startGame();

    tiles()[1].click();
    ops()[1].click();
    tiles()[0].click();
    expect(tiles()).toHaveLength(3);
    expect(tileValues()[2]).toBe('2');
  });

  it('auto-submits the third merge with ordered steps', async function () {
    const calls: { url: string; body: string }[] = [];
    vi.stubGlobal('fetch', vi.fn(function (url: string, init?: RequestInit) {
      const u = String(url);
      const body = init && init.body ? String(init.body) : '';
      calls.push({ url: u, body });
      if (u.indexOf('/api/records') >= 0) return jsonResponse({ history: [], bests: [] });
      if (u.indexOf('/submit') >= 0) {
        return jsonResponse({
          ...B_GAME, status: 'FINISHED', correct: 1, revision: 3,
          result: { correct_count: 1, wrong_count: 0, skipped_count: 0, actual_ms: 5000, penalty_ms: 0, scoring_ms: 5000 }
        });
      }
      if (u.indexOf('/api/games') >= 0) return jsonResponse(B_GAME);
      return jsonResponse({});
    }));

    await startGame();

    // 8 ÷ 3
    tiles()[2].click();
    ops()[3].click();
    tiles()[0].click();
    // 3 − 8/3
    tiles()[0].click();
    ops()[1].click();
    tiles()[2].click();
    // 8 ÷ (1/3) = 24
    tiles()[0].click();
    ops()[3].click();
    tiles()[1].click();
    await flush();

    const submitCall = calls.find(function (c) { return c.url.indexOf('/submit') >= 0; });
    expect(submitCall).toBeTruthy();
    const payload = JSON.parse(submitCall!.body);
    expect(payload.operations).toEqual([
      { leftRef: 'c2', rightRef: 'c0', operator: '/' },
      { leftRef: 'c1', rightRef: 's0', operator: '-' },
      { leftRef: 'c3', rightRef: 's1', operator: '/' }
    ]);
    expect(document.body.textContent).toContain('本局成绩');
  });

  it('moves to the next puzzle after a wrong answer', async function () {
    stubApi({
      onSubmit: {
        ...B_GAME, revision: 2, wrong: 1, penaltyMs: 5000, elapsedMs: 6000,
        puzzle: { puzzleId: 'p4', numbers: [1, 5, 5, 5], open: true },
        lastResult: 'wrong'
      }
    });
    await startGame();

    tiles()[2].click(); ops()[3].click(); tiles()[0].click();
    tiles()[0].click(); ops()[1].click(); tiles()[2].click();
    tiles()[0].click(); ops()[3].click(); tiles()[1].click();
    await flush();

    expect(tileValues()).toEqual(['1', '5', '5', '5']);
    expect((document.getElementById('fb') as HTMLElement).textContent).toContain('不是 24');
    expect((document.getElementById('fb') as HTMLElement).textContent).toContain('总用时 +5 秒');
    // B 模式的表盘包含罚时：6 秒实际用时 + 5 秒罚时
    expect(clockText()).toBe('00:11.0');
  });
});

describe('clock', function () {
  it('keeps ticking up in mode B', async function () {
    stubApi();
    await startGame();
    expect(clockText()).toBe('00:01.2');
    await vi.advanceTimersByTimeAsync(350);
    expect(clockText()).toBe('00:01.5');
  });

  it('counts down in mode A', async function () {
    stubApi({ game: { ...B_GAME, mode: 'A', remainingMs: 120000, elapsedMs: 0 } });
    await startGame('A');
    expect(clockText()).toBe('02:00');
    await vi.advanceTimersByTimeAsync(1100);
    expect(clockText()).toBe('01:59');
  });

  it('settles automatically when mode A reaches zero', async function () {
    const running = { ...B_GAME, mode: 'A', remainingMs: 500, elapsedMs: 0 };
    const finished = {
      ...B_GAME, mode: 'A', status: 'FINISHED', remainingMs: null, elapsedMs: 800,
      correct: 1, revision: 2,
      result: { correct_count: 1, wrong_count: 0, skipped_count: 0, actual_ms: 800, penalty_ms: 0, scoring_ms: 800 }
    };
    stubApi({ game: running, onGet: finished });
    await startGame('A');
    expect(clockText()).toBe('00:01');
    await vi.advanceTimersByTimeAsync(700);
    await flush(12);
    expect(document.body.textContent).toContain('本局成绩');
  });
});

describe('skip and quit actions', function () {
  beforeEach(function () { stubApi(); });

  it('skips immediately without a confirmation dialog', async function () {
    const fetchMock = vi.fn(function (url: string) {
      const u = String(url);
      if (u.indexOf('/api/records') >= 0) return jsonResponse({ history: [], bests: [] });
      if (u.indexOf('/skip') >= 0) return jsonResponse({ ...B_GAME, skipped: 1, revision: 1 });
      if (u.indexOf('/api/games') >= 0) return jsonResponse(B_GAME);
      return jsonResponse({});
    });
    vi.stubGlobal('fetch', fetchMock);

    await startGame();
    (document.getElementById('skip') as HTMLButtonElement).click();
    await flush();

    expect(fetchMock.mock.calls.some(function (c) {
      return String(c[0]).indexOf('/skip') >= 0;
    })).toBe(true);
    expect(document.querySelector('.overlay')).toBeNull();
  });

  it('opens an in-page dialog for quit and can be cancelled', async function () {
    await startGame();
    (document.getElementById('quit') as HTMLButtonElement).click();
    const overlay = document.querySelector('.overlay') as HTMLElement;
    expect(overlay).not.toBeNull();
    (overlay.querySelector('[data-cancel]') as HTMLButtonElement).click();
    expect(document.querySelector('.overlay')).toBeNull();
  });
});
