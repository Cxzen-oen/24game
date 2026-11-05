package com.game24.leaderboard;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

class LeaderboardNicknameMaskTest {

    @Test
    void masksFirstChineseCharacter() {
        assertEquals("*算王", LeaderboardService.maskNickname("心算王"));
        assertEquals("*明", LeaderboardService.maskNickname("小明"));
    }

    @Test
    void doesNotBreakSurrogatePair() {
        assertEquals("*小明", LeaderboardService.maskNickname("😀小明"));
    }

    @Test
    void handlesNullAndEmpty() {
        assertNull(LeaderboardService.maskNickname(null));
        assertEquals("", LeaderboardService.maskNickname(""));
    }
}
