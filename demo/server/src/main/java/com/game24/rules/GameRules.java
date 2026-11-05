package com.game24.rules;

import org.apache.commons.numbers.fraction.Fraction;

import java.util.ArrayList;
import java.util.List;

/** 判题与求解：全程有理数，不使用浮点数。 */
public final class GameRules {

    public static final Fraction TARGET = Fraction.of(24);

    private GameRules() {
    }

    public static List<Operator> operatorsFor(Level level) {
        return level == Level.L1 ? List.of(Operator.ADD, Operator.SUB)
                : List.of(Operator.ADD, Operator.SUB, Operator.MUL, Operator.DIV);
    }

    /**
     * 递归判断四个数字能否算出 24。无缓存，避免提前写入未确定状态导致误判。
     */
    public static boolean solvable(List<Fraction> values, List<Operator> ops) {
        if (values.isEmpty()) return false;
        return search(values, ops);
    }

    private static boolean search(List<Fraction> values, List<Operator> ops) {
        if (values.size() == 1) {
            return values.get(0).equals(TARGET);
        }
        for (int i = 0; i < values.size(); i++) {
            for (int j = i + 1; j < values.size(); j++) {
                List<Fraction> rest = new ArrayList<>(values.size() - 2);
                for (int k = 0; k < values.size(); k++) {
                    if (k != i && k != j) rest.add(values.get(k));
                }
                for (Operator op : ops) {
                    // 非交换运算尝试两种操作数顺序
                    boolean ordered = op == Operator.SUB || op == Operator.DIV;
                    Fraction a = op.apply(values.get(i), values.get(j));
                    if (a != null) {
                        rest.add(a);
                        if (search(rest, ops)) return true;
                        rest.remove(rest.size() - 1);
                    }
                    if (ordered) {
                        Fraction b = op.apply(values.get(j), values.get(i));
                        if (b != null) {
                            rest.add(b);
                            if (search(rest, ops)) return true;
                            rest.remove(rest.size() - 1);
                        }
                    }
                }
            }
        }
        return false;
    }
}
