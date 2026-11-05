package com.game24.game;

import com.game24.rules.Level;
import com.game24.rules.Mode;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

class GameRow {
    UUID id;
    UUID accountId;
    String guestId;
    Mode mode;
    Level level;
    GameStatus status;
    Instant startedAt;
    Instant deadline;
    int correct;
    int wrong;
    int skipped;
    long penalty;
    Long lastScoring;
    List<int[]> deck;
    int deckPosition;
    long revision;
}
