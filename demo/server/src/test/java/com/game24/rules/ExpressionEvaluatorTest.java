package com.game24.rules;

import org.apache.commons.numbers.fraction.Fraction;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class ExpressionEvaluatorTest {

    @Test
    void fractionSolutionEvaluatesTo24() {
        // 8 / (3 - 8/3) = 24，全程有理数
        int[] numbers = {3, 3, 8, 8};
        List<OperationStep> steps = List.of(
                new OperationStep("c2", "c0", "/"),
                new OperationStep("c1", "s0", "-"),
                new OperationStep("c3", "s1", "/")
        );
        assertEquals(Fraction.of(24), ExpressionEvaluator.evaluate(numbers, steps, Level.L2));
    }

    @Test
    void chainedAdditionIsAllowed() {
        int[] numbers = {3, 4, 4, 12};
        List<OperationStep> steps = List.of(
                new OperationStep("c0", "c1", "+"),
                new OperationStep("s0", "c2", "+"),
                new OperationStep("s1", "c3", "+")
        );
        // 3+4+4+12 = 23
        assertEquals(Fraction.of(23), ExpressionEvaluator.evaluate(numbers, steps, Level.L2));
    }

    @Test
    void reusingSameCardIsRejected() {
        int[] numbers = {3, 4, 4, 12};
        List<OperationStep> steps = List.of(
                new OperationStep("c0", "c0", "+"),
                new OperationStep("s0", "c2", "+"),
                new OperationStep("s1", "c3", "+")
        );
        assertThrows(IllegalArgumentException.class,
                () -> ExpressionEvaluator.evaluate(numbers, steps, Level.L2));
    }

    @Test
    void wrongStepCountIsRejected() {
        int[] numbers = {3, 4, 4, 12};
        List<OperationStep> steps = List.of(new OperationStep("c0", "c1", "+"));
        assertThrows(IllegalArgumentException.class,
                () -> ExpressionEvaluator.evaluate(numbers, steps, Level.L2));
    }

    @Test
    void l1RejectsMultiplication() {
        int[] numbers = {3, 4, 4, 12};
        List<OperationStep> steps = List.of(
                new OperationStep("c0", "c1", "*"),
                new OperationStep("s0", "c2", "+"),
                new OperationStep("s1", "c3", "+")
        );
        assertThrows(IllegalArgumentException.class,
                () -> ExpressionEvaluator.evaluate(numbers, steps, Level.L1));
    }

    @Test
    void divisionByZeroIsRejected() {
        int[] numbers = {3, 3, 8, 8};
        List<OperationStep> steps = List.of(
                new OperationStep("c0", "c0", "-"),
                new OperationStep("c2", "s0", "/"),
                new OperationStep("s1", "c3", "+")
        );
        assertThrows(IllegalArgumentException.class,
                () -> ExpressionEvaluator.evaluate(numbers, steps, Level.L2));
    }
}
