import Fraction from 'fraction.js';

export interface Card {
  id: string;
  value: Fraction;
  origin: number | null;
  left: Card | null;
  right: Card | null;
  op: string | null;
}

export interface StepRecord {
  stepId: string;
  leftRef: string;
  rightRef: string;
  operator: string;
}

interface Snapshot {
  cards: Card[];
  selected: string | null;
  pendingOp: string | null;
  steps: StepRecord[];
}

export interface EditorState {
  cards: Card[];
  /** 已选中的第一个操作数（最多一个） */
  selected: string | null;
  /** 已点下的算符，等待第二个操作数 */
  pendingOp: string | null;
  steps: StepRecord[];
  history: Snapshot[];
}

const SYMBOLS: Record<string, string> = { '+': '+', '-': '−', '*': '×', '/': '÷' };

export function initialState(numbers: number[]): EditorState {
  return {
    cards: numbers.map((n, i) => ({
      id: 'c' + i,
      value: new Fraction(n),
      origin: n,
      left: null,
      right: null,
      op: null
    })),
    selected: null,
    pendingOp: null,
    steps: [],
    history: []
  };
}

export function displayValue(card: Card): string {
  // fraction.js 的 n 恒为非负、符号在 s 上，必须用 toFraction() 才能保留负号
  return card.value.toFraction();
}

export function expressionOf(card: Card): string {
  if (!card.left || !card.right) {
    return card.origin !== null ? String(card.origin) : displayValue(card);
  }
  const wrap = (c: Card): string => (c.left || c.right ? '(' + expressionOf(c) + ')' : expressionOf(c));
  return wrap(card.left) + ' ' + SYMBOLS[card.op || '+'] + ' ' + wrap(card.right);
}

export function symbolOf(op: string): string {
  return SYMBOLS[op] || op;
}

function snapshot(state: EditorState): Snapshot {
  return {
    cards: state.cards,
    selected: state.selected,
    pendingOp: state.pendingOp,
    steps: state.steps
  };
}

/** 选数字：未选时选中；再点同一个取消；已有算符时点第二个数字立即合并。 */
export function selectCard(state: EditorState, id: string): EditorState {
  if (!state.cards.some((c) => c.id === id)) return state;
  if (state.selected === id) {
    return { ...state, selected: null, pendingOp: null };
  }
  if (state.selected === null) {
    return { ...state, selected: id };
  }
  if (!state.pendingOp) {
    // 还没点算符，改选另一个数
    return { ...state, selected: id };
  }
  return mergeSelected(state, id);
}

/** 点算符：必须先选中一个数。 */
export function chooseOperator(state: EditorState, operator: string): EditorState {
  if (!state.selected) throw new Error('先点一个数字');
  return { ...state, pendingOp: operator };
}

/** 当前是否可点算符（已选一个数，且还没合并完成）。 */
export function canChooseOperator(state: EditorState): boolean {
  return state.selected !== null && !isComplete(state);
}

/** 是否两个操作数都已就位、可以马上计算。 */
export function canMerge(state: EditorState): boolean {
  return state.selected !== null && state.pendingOp !== null;
}

function mergeSelected(state: EditorState, rightId: string): EditorState {
  const leftId = state.selected as string;
  if (!leftId || !state.pendingOp) return state;
  const a = state.cards.find((c) => c.id === leftId);
  const b = state.cards.find((c) => c.id === rightId);
  if (!a || !b) return state;
  if (a.id === b.id) return state;

  const operator = state.pendingOp;
  let value: Fraction;
  switch (operator) {
    case '+': value = a.value.add(b.value); break;
    case '-': value = a.value.sub(b.value); break;
    case '*': value = a.value.mul(b.value); break;
    case '/':
      if (b.value.equals(0)) throw new Error('不能除以 0');
      value = a.value.div(b.value);
      break;
    default: throw new Error('不支持的算符');
  }

  const stepId = 's' + state.steps.length;
  const merged: Card = { id: stepId, value, origin: null, left: a, right: b, op: operator };

  return {
    ...state,
    cards: [...state.cards.filter((c) => c.id !== a.id && c.id !== b.id), merged],
    selected: null,
    pendingOp: null,
    steps: [...state.steps, { stepId, leftRef: a.id, rightRef: b.id, operator }],
    history: [...state.history, snapshot(state)]
  };
}

export function undo(state: EditorState): EditorState {
  if (state.history.length === 0) return state;
  const prev = state.history[state.history.length - 1];
  return {
    cards: prev.cards,
    selected: prev.selected,
    pendingOp: prev.pendingOp,
    steps: prev.steps,
    history: state.history.slice(0, -1)
  };
}

export function isComplete(state: EditorState): boolean {
  return state.cards.length === 1 && state.steps.length === 3;
}

export function toOperations(state: EditorState) {
  return state.steps.map((s) => ({ leftRef: s.leftRef, rightRef: s.rightRef, operator: s.operator }));
}

export interface Preview {
  text: string;
  tone: 'idle' | 'ready' | 'done';
}

/** 牌面上方的实时算式提示。 */
export function previewText(state: EditorState): Preview {
  if (isComplete(state)) {
    const card = state.cards[0];
    return { text: expressionOf(card) + ' = ' + displayValue(card), tone: 'done' };
  }
  if (state.selected) {
    const card = state.cards.find((c) => c.id === state.selected);
    if (card) {
      const left = card.left || card.right ? '(' + expressionOf(card) + ')' : displayValue(card);
      if (state.pendingOp) {
        return { text: left + ' ' + symbolOf(state.pendingOp) + ' ?', tone: 'ready' };
      }
      return { text: left + ' ?', tone: 'ready' };
    }
  }
  // 刚合并出中间结果时，先把这一步的算式留在牌面上
  if (state.cards.length > 1) {
    const last = state.cards[state.cards.length - 1];
    if (last.left) return { text: expressionOf(last) + ' = ' + displayValue(last), tone: 'done' };
  }
  return { text: '点数字 → 点算符 → 再点数字', tone: 'idle' };
}
