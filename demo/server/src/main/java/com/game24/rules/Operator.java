package com.game24.rules;

import org.apache.commons.numbers.fraction.Fraction;

public enum Operator {
    ADD("+"), SUB("-"), MUL("*"), DIV("/");

    private final String symbol;

    Operator(String symbol) {
        this.symbol = symbol;
    }

    public String symbol() {
        return symbol;
    }

    public static Operator fromSymbol(String s) {
        for (Operator op : values()) {
            if (op.symbol.equals(s)) return op;
        }
        throw new IllegalArgumentException("unsupported operator: " + s);
    }

    /** 返回 null 表示非法（除零）。 */
    public Fraction apply(Fraction left, Fraction right) {
        return switch (this) {
            case ADD -> left.add(right);
            case SUB -> left.subtract(right);
            case MUL -> left.multiply(right);
            case DIV -> right.getNumerator() == 0 ? null : left.divide(right);
        };
    }
}
