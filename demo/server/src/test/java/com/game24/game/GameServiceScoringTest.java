package com.game24.game;

import com.game24.rules.Mode;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class GameServiceScoringTest {

    @Test
    void modeAUsesTheLastCorrectAnswerTime() {
        // 答对最后一题时用时 238 秒，之后即使继续玩到 300 秒，计榜仍是 238 秒
        assertEquals(238000L, GameService.scoringFor(Mode.A, 238000L, 300000L));
    }

    @Test
    void modeAWithoutAnyCorrectAnswerScoresZero() {
        assertEquals(0L, GameService.scoringFor(Mode.A, null, 300000L));
    }

    @Test
    void modeBUsesElapsedPlusPenalty() {
        assertEquals(185000L, GameService.scoringFor(Mode.B, 120000L, 185000L));
    }
}
