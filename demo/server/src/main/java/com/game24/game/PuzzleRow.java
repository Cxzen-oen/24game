package com.game24.game;

class PuzzleRow {
    final String id;
    final int sequence;
    final int[] numbers;
    final boolean open;

    PuzzleRow(String id, int sequence, int[] numbers, boolean open) {
        this.id = id;
        this.sequence = sequence;
        this.numbers = numbers;
        this.open = open;
    }
}
