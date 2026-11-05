package com.game24.puzzle;

import com.game24.rules.GameRules;
import com.game24.rules.Level;
import com.game24.rules.Operator;
import org.apache.commons.numbers.fraction.Fraction;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * 离线题池生成：穷举 1..13 的无序四元组，用判题内核筛出可解牌组。
 * 用法：mvn exec:java -Dexec.mainClass=com.game24.puzzle.PuzzleGenerator
 */
public final class PuzzleGenerator {

    public static final int MIN = 1;
    public static final int MAX = 13;

    public static void main(String[] args) throws IOException {
        int expectedL1 = 220;
        int expectedL2 = 1362;
        int expectedTotal = 1820;

        List<int[]> candidates = candidates();
        if (candidates.size() != expectedTotal) {
            throw new IllegalStateException("candidate count mismatch: " + candidates.size());
        }
        List<int[]> l1 = select(candidates, Level.L1);
        List<int[]> l2 = select(candidates, Level.L2);
        if (l1.size() != expectedL1) {
            throw new IllegalStateException("L1 mismatch: " + l1.size());
        }
        if (l2.size() != expectedL2) {
            throw new IllegalStateException("L2 mismatch: " + l2.size());
        }

        Path dir = Path.of("src", "main", "resources", "puzzles");
        Files.createDirectories(dir);
        write(dir.resolve("puzzles-L1.json"), l1);
        write(dir.resolve("puzzles-L2.json"), l2);
        System.out.println("generated candidates=" + candidates.size()
                + " L1=" + l1.size() + " L2=" + l2.size());
    }

    public static List<int[]> candidates() {
        List<int[]> out = new ArrayList<>();
        for (int a = MIN; a <= MAX; a++)
            for (int b = a; b <= MAX; b++)
                for (int c = b; c <= MAX; c++)
                    for (int d = c; d <= MAX; d++)
                        out.add(new int[]{a, b, c, d});
        return out;
    }

    static List<int[]> select(List<int[]> candidates, Level level) {
        List<Operator> ops = GameRules.operatorsFor(level);
        List<int[]> out = new ArrayList<>();
        for (int[] nums : candidates) {
            List<Fraction> values = new ArrayList<>(4);
            for (int n : nums) values.add(Fraction.of(n));
            if (GameRules.solvable(values, ops)) out.add(nums);
        }
        return out;
    }

    private static void write(Path file, List<int[]> puzzles) throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append("[\n");
        for (int i = 0; i < puzzles.size(); i++) {
            int[] p = puzzles.get(i);
            sb.append("  [").append(p[0]).append(',').append(p[1]).append(',')
              .append(p[2]).append(',').append(p[3]).append(']');
            if (i < puzzles.size() - 1) sb.append(',');
            sb.append('\n');
        }
        sb.append("]\n");
        Files.writeString(file, sb.toString(), StandardCharsets.UTF_8);
    }
}
