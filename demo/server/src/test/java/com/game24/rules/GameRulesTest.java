package com.game24.rules;

import org.apache.commons.numbers.fraction.Fraction;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class GameRulesTest {

    private static List<Fraction> f(int... nums) {
        return java.util.Arrays.stream(nums).mapToObj(Fraction::of).toList();
    }

    @Test
    void fractionIntermediateValueIsExact() {
        // 8 / (3 - 8/3) = 24
        Fraction inner = Fraction.of(3).subtract(Fraction.of(8, 3));
        Fraction result = Fraction.of(8).divide(inner);
        assertEquals(Fraction.of(24), result);
    }

    @Test
    void classicFractionPuzzlesAreSolvable() {
        List<Operator> ops = GameRules.operatorsFor(Level.L2);
        assertTrue(GameRules.solvable(f(3, 3, 8, 8), ops));
        assertTrue(GameRules.solvable(f(1, 5, 5, 5), ops));
        assertTrue(GameRules.solvable(f(1, 1, 6, 8), ops));
    }

    @Test
    void divisionByZeroIsRejected() {
        assertNull(Operator.DIV.apply(Fraction.of(5), Fraction.of(0)));
    }

    @Test
    void operatorOrderMatters() {
        assertEquals(Fraction.of(2), Operator.SUB.apply(Fraction.of(5), Fraction.of(3)));
        assertEquals(Fraction.of(-2), Operator.SUB.apply(Fraction.of(3), Fraction.of(5)));
    }

    @Test
    void l1ForbidsMultiplicationAndDivision() {
        List<Operator> ops = GameRules.operatorsFor(Level.L1);
        assertEquals(List.of(Operator.ADD, Operator.SUB), ops);
        // 3,3,8,8 必须分数，L1 下不可解
        assertFalse(GameRules.solvable(f(3, 3, 8, 8), ops));
    }

    @Test
    void unsolvablePuzzleIsRejected() {
        List<Operator> ops = GameRules.operatorsFor(Level.L2);
        assertFalse(GameRules.solvable(f(1, 1, 1, 1), ops));
    }
}
