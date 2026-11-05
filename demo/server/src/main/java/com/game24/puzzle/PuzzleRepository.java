package com.game24.puzzle;

import com.game24.rules.Level;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Repository;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** 加载离线生成的题池，并按对局洗牌。 */
@Repository
public class PuzzleRepository {

    private final ObjectMapper mapper = new ObjectMapper();
    private final List<int[]> l1 = new ArrayList<>();
    private final List<int[]> l2 = new ArrayList<>();

    public PuzzleRepository() throws IOException {
        l1.addAll(load("puzzles/puzzles-L1.json"));
        l2.addAll(load("puzzles/puzzles-L2.json"));
    }

    private List<int[]> load(String path) throws IOException {
        ClassPathResource resource = new ClassPathResource(path);
        if (!resource.exists()) {
            throw new IllegalStateException("题池缺失，请先运行 PuzzleGenerator: " + path);
        }
        try (InputStream in = resource.getInputStream()) {
            int[][] raw = mapper.readValue(in, int[][].class);
            List<int[]> out = new ArrayList<>();
            for (int[] row : raw) out.add(row);
            return out;
        }
    }

    public List<int[]> deckFor(Level level) {
        List<int[]> source = level == Level.L1 ? l1 : l2;
        List<int[]> deck = new ArrayList<>(source);
        Collections.shuffle(deck);
        return deck;
    }

    public int poolSize(Level level) {
        return level == Level.L1 ? l1.size() : l2.size();
    }
}
