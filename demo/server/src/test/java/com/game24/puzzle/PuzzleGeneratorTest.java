package com.game24.puzzle;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class PuzzleGeneratorTest {

    @Test
    void candidateCountIs1820() {
        assertEquals(1820, PuzzleGenerator.candidates().size());
    }

    @Test
    void solvableCountsMatchVerifiedNumbers() {
        List<int[]> candidates = PuzzleGenerator.candidates();
        assertEquals(220, PuzzleGenerator.select(candidates, com.game24.rules.Level.L1).size());
        assertEquals(1362, PuzzleGenerator.select(candidates, com.game24.rules.Level.L2).size());
    }
}
