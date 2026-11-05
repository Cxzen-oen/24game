import { describe, expect, it } from 'vitest';
import {
  chooseOperator, displayValue, expressionOf, initialState, isComplete,
  previewText, selectCard, toOperations, undo
} from '../src/merge';

describe('点数字 → 点算符 → 点数字', function () {
  it('starts with four cards and nothing selected', function () {
    const s = initialState([2, 4, 8, 1]);
    expect(s.cards).toHaveLength(4);
    expect(s.selected).toBeNull();
    expect(s.pendingOp).toBeNull();
    expect(isComplete(s)).toBe(false);
  });

  it('keeps operand order: 2 - 4 = -2', function () {
    let s = initialState([2, 4, 8, 1]);
    s = selectCard(s, 'c0');
    expect(s.pendingOp).toBeNull();
    s = chooseOperator(s, '-');
    expect(s.pendingOp).toBe('-');
    s = selectCard(s, 'c1');
    expect(s.cards).toHaveLength(3);
    expect(s.steps).toHaveLength(1);
    expect(s.steps[0]).toMatchObject({ leftRef: 'c0', rightRef: 'c1', operator: '-' });
    expect(displayValue(s.cards[2])).toBe('-2');
    expect(expressionOf(s.cards[2])).toBe('2 − 4');
  });

  it('keeps operand order: 4 - 2 = 2', function () {
    let s = initialState([2, 4, 8, 1]);
    s = selectCard(s, 'c1');
    s = chooseOperator(s, '-');
    s = selectCard(s, 'c0');
    expect(displayValue(s.cards[2])).toBe('2');
    expect(s.steps[0]).toMatchObject({ leftRef: 'c1', rightRef: 'c0', operator: '-' });
  });

  it('requires a selected number before an operator', function () {
    const s = initialState([2, 4, 8, 1]);
    expect(function () { chooseOperator(s, '+'); }).toThrow('先点一个数字');
  });

  it('replaces the first operand when no operator has been chosen', function () {
    let s = initialState([2, 4, 8, 1]);
    s = selectCard(s, 'c0');
    s = selectCard(s, 'c2');
    expect(s.selected).toBe('c2');
    expect(s.steps).toHaveLength(0);
  });

  it('tapping the selected number again cancels the selection', function () {
    let s = initialState([2, 4, 8, 1]);
    s = selectCard(s, 'c0');
    s = chooseOperator(s, '+');
    s = selectCard(s, 'c0');
    expect(s.selected).toBeNull();
    expect(s.pendingOp).toBeNull();
  });

  it('keeps fractions exact', function () {
    let s = initialState([3, 3, 8, 8]);
    s = selectCard(s, 'c2');
    s = chooseOperator(s, '/');
    s = selectCard(s, 'c0');
    expect(displayValue(s.cards[2])).toBe('8/3');
  });

  it('rejects division by zero without changing the state', function () {
    let s = initialState([3, 0, 8, 8]);
    s = selectCard(s, 'c0');
    s = chooseOperator(s, '/');
    expect(function () { selectCard(s, 'c1'); }).toThrow('不能除以 0');
    expect(s.cards).toHaveLength(4);
    expect(s.selected).toBe('c0');
    expect(s.pendingOp).toBe('/');
  });

  it('undo restores the previous cards and steps', function () {
    let s = initialState([2, 4, 8, 1]);
    s = selectCard(s, 'c0');
    s = chooseOperator(s, '+');
    s = selectCard(s, 'c1');
    s = undo(s);
    expect(s.cards).toHaveLength(4);
    expect(s.steps).toHaveLength(0);
    expect(s.selected).toBe('c0');
    expect(s.pendingOp).toBe('+');
  });

  it('completes after three merges', function () {
    let s = initialState([4, 4, 4, 4]);
    s = selectCard(s, 'c0');
    s = chooseOperator(s, '*');
    s = selectCard(s, 'c1');
    s = selectCard(s, 's0');
    s = chooseOperator(s, '+');
    s = selectCard(s, 'c2');
    s = selectCard(s, 's1');
    s = chooseOperator(s, '+');
    s = selectCard(s, 'c3');
    expect(isComplete(s)).toBe(true);
    expect(displayValue(s.cards[0])).toBe('24');
    expect(toOperations(s)).toHaveLength(3);
    expect(toOperations(s)[0]).toMatchObject({ leftRef: 'c0', rightRef: 'c1', operator: '*' });
    expect(toOperations(s)[2]).toMatchObject({ leftRef: 's1', rightRef: 'c3', operator: '+' });
  });

  it('describes the current step in the preview', function () {
    let s = initialState([2, 4, 8, 1]);
    expect(previewText(s).tone).toBe('idle');
    s = selectCard(s, 'c0');
    expect(previewText(s)).toMatchObject({ text: '2 ?', tone: 'ready' });
    s = chooseOperator(s, '-');
    expect(previewText(s)).toMatchObject({ text: '2 − ?', tone: 'ready' });
    s = selectCard(s, 'c1');
    expect(previewText(s).text).toBe('2 − 4 = -2');
    expect(previewText(s).tone).toBe('done');
  });
});
