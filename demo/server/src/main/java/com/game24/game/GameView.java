package com.game24.game;

import java.util.Map;

public record GameView(
        String gameId,
        long revision,
        String status,
        String mode,
        String level,
        String serverTime,
        String guestId,
        PuzzleView puzzle,
        int correct,
        int wrong,
        int skipped,
        long penaltyMs,
        Long remainingMs,
        long elapsedMs,
        Long lastScoringMs,
        int targetCorrect,
        String lastResult,
        Map<String, Object> result
) {
}
