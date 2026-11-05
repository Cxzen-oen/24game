export type Mode = 'A' | 'B';
export type Level = 'L1' | 'L2';

export interface PuzzleView {
  puzzleId: string;
  numbers: number[];
  open: boolean;
}

export interface GameView {
  gameId: string;
  revision: number;
  status: string;
  mode: Mode;
  level: Level;
  serverTime: string;
  guestId?: string;
  puzzle: PuzzleView | null;
  correct: number;
  wrong: number;
  skipped: number;
  penaltyMs: number;
  remainingMs: number | null;
  elapsedMs: number;
  lastScoringMs: number | null;
  targetCorrect: number;
  lastResult: string | null;
  result: Record<string, number> | null;
}

export interface OperationStep {
  leftRef: string;
  rightRef: string;
  operator: string;
}

export interface Records {
  history: Record<string, unknown>[];
  bests: Record<string, unknown>[];
}

export interface Account {
  id: string;
  username: string;
  nickname: string;
  createdAt: string;
}

export interface AuthResult {
  accessToken: string;
  accessExpiresAt: string;
  account: Account;
  claimedGames: number;
}

export interface LeaderboardEntry {
  rank: number;
  accountId: string;
  nickname: string;
  correct: number;
  scoringMs: number;
  achievedAt: string;
}

export interface Standing {
  mode: Mode;
  level: Level;
  rank: number | null;
  correct: number | null;
  scoringMs: number | null;
  achievedAt: string | null;
}

export interface Leaderboard {
  mode: Mode;
  level: Level;
  total: number;
  page: number;
  size: number;
  entries: LeaderboardEntry[];
  me: Standing | null;
}

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(message: string, status: number, code: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

const GUEST_KEY = 'game24.guestId';
const TOKEN_KEY = 'game24.accessToken';
const SESSION_FLAG = 'game24.hasSession';

let accessToken: string | null = sessionStorage.getItem(TOKEN_KEY);

function ensureGuestId(): string {
  let id = localStorage.getItem(GUEST_KEY);
  if (!id) {
    id = 'g-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
    localStorage.setItem(GUEST_KEY, id);
  }
  return id;
}

export function getGuestId(): string {
  return ensureGuestId();
}

export function currentAccountToken(): string | null {
  return accessToken;
}

function setSession(result: AuthResult): void {
  accessToken = result.accessToken;
  sessionStorage.setItem(TOKEN_KEY, result.accessToken);
  localStorage.setItem(SESSION_FLAG, '1');
}

function clearSession(): void {
  accessToken = null;
  sessionStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(SESSION_FLAG);
}

async function readError(res: Response): Promise<ApiError> {
  let message = '请求失败';
  let code = 'UNKNOWN';
  try {
    const body = await res.json();
    message = body.message || body.code || message;
    code = body.code || code;
  } catch {
    /* 忽略解析失败 */
  }
  return new ApiError(message, res.status, code);
}

async function request<T>(path: string, init?: RequestInit, retry = true): Promise<T> {
  const headers: Record<string, string> = {
    'X-Guest-Id': getGuestId(),
    ...((init && init.headers) as Record<string, string> | undefined)
  };
  if (init && init.body) headers['Content-Type'] = 'application/json';
  if (accessToken) headers['Authorization'] = 'Bearer ' + accessToken;

  const res = await fetch('/api' + path, { ...init, headers, credentials: 'same-origin' });

  if (res.status === 401 && retry && accessToken && path !== '/auth/refresh') {
    const account = await refreshSession();
    if (account) return request<T>(path, init, false);
  }
  if (!res.ok) throw await readError(res);
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function refreshSession(): Promise<Account | null> {
  try {
    const res = await fetch('/api/auth/refresh', { method: 'POST', credentials: 'same-origin' });
    if (!res.ok) {
      clearSession();
      return null;
    }
    const data = (await res.json()) as AuthResult;
    if (!data || !data.accessToken) {
      clearSession();
      return null;
    }
    setSession(data);
    return data.account;
  } catch {
    clearSession();
    return null;
  }
}

/** 页面启动时静默恢复登录态；没有登录过就不发请求。 */
export async function bootstrapAuth(): Promise<Account | null> {
  if (localStorage.getItem(SESSION_FLAG) !== '1') return null;
  return refreshSession();
}

async function authCall(path: string, body: Record<string, unknown>): Promise<AuthResult> {
  const res = await fetch('/api' + path, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...body, guestId: getGuestId() })
  });
  if (!res.ok) throw await readError(res);
  const data = (await res.json()) as AuthResult;
  setSession(data);
  return data;
}

export function register(username: string, password: string, nickname: string): Promise<AuthResult> {
  return authCall('/auth/register', { username, password, nickname });
}

export function login(username: string, password: string): Promise<AuthResult> {
  return authCall('/auth/login', { username, password });
}

export async function logout(): Promise<void> {
  try {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' });
  } catch {
    /* 网络失败也清本地状态 */
  }
  clearSession();
}

export function me(): Promise<Account> {
  return request('/auth/me');
}

export function createGame(mode: Mode, level: Level): Promise<GameView> {
  return request('/games', {
    method: 'POST',
    body: JSON.stringify({ requestId: actionId('r'), mode, level })
  });
}

export function getGame(gameId: string): Promise<GameView> {
  return request('/games/' + gameId);
}

export function submit(gameId: string, puzzleId: string, revision: number, steps: OperationStep[]): Promise<GameView> {
  return request('/games/' + gameId + '/submit', {
    method: 'POST',
    body: JSON.stringify({ puzzleId, revision, actionId: actionId('a'), operations: steps })
  });
}

export function skip(gameId: string, puzzleId: string, revision: number): Promise<GameView> {
  return request('/games/' + gameId + '/skip', {
    method: 'POST',
    body: JSON.stringify({ puzzleId, revision, actionId: actionId('s') })
  });
}

export function abandon(gameId: string, revision: number): Promise<GameView> {
  return request('/games/' + gameId + '/abandon', {
    method: 'POST',
    body: JSON.stringify({ revision, actionId: actionId('x') })
  });
}

export function getRecords(limit = 50, mode?: Mode, level?: Level): Promise<Records> {
  let path = '/records?limit=' + limit;
  if (mode) path += '&mode=' + encodeURIComponent(mode);
  if (level) path += '&level=' + encodeURIComponent(level);
  return request(path);
}

export function getLeaderboard(mode: Mode, level: Level, page = 0, size = 20): Promise<Leaderboard> {
  return request('/leaderboard?mode=' + mode + '&level=' + level + '&page=' + page + '&size=' + size);
}

export function getMyStandings(): Promise<Standing[]> {
  return request('/leaderboard/me');
}

function actionId(prefix: string): string {
  return prefix + '-' + Date.now() + '-' + Math.random().toString(36).slice(2);
}
