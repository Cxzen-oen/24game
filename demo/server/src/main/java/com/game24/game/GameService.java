package com.game24.game;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.game24.api.ApiException;
import com.game24.auth.Player;
import com.game24.puzzle.PuzzleRepository;
import com.game24.rules.ExpressionEvaluator;
import com.game24.rules.Level;
import com.game24.rules.Mode;
import com.game24.rules.OperationStep;
import com.game24.rules.GameRules;
import org.apache.commons.numbers.fraction.Fraction;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
public class GameService {

    private final JdbcTemplate jdbc;
    private final PuzzleRepository puzzles;
    private final Clock clock;
    private final ObjectMapper mapper = new ObjectMapper();

    private final long aDurationMs;
    private final int bTargetCorrect;
    private final long wrongPenaltyMs;
    private final long skipPenaltyMs;

    public GameService(JdbcTemplate jdbc,
                       PuzzleRepository puzzles,
                       Clock clock,
                       @Value("${game24.a-duration-ms}") long aDurationMs,
                       @Value("${game24.b-target-correct}") int bTargetCorrect,
                       @Value("${game24.wrong-penalty-ms}") long wrongPenaltyMs,
                       @Value("${game24.skip-penalty-ms}") long skipPenaltyMs) {
        this.jdbc = jdbc;
        this.puzzles = puzzles;
        this.clock = clock;
        this.aDurationMs = aDurationMs;
        this.bTargetCorrect = bTargetCorrect;
        this.wrongPenaltyMs = wrongPenaltyMs;
        this.skipPenaltyMs = skipPenaltyMs;
    }

    public Clock clock() {
        return clock;
    }

    @Transactional
    public GameView createGame(Player player, String requestId, Mode mode, Level level) {
        UUID id = UUID.randomUUID();
        Instant now = clock.instant();
        List<int[]> deck = puzzles.deckFor(level);
        // 用 ON CONFLICT DO NOTHING 而不是捕获异常：PostgreSQL 里唯一键冲突会让整个事务进入 aborted 状态，
        // 之后同事务的 SELECT 也会失败。幂等创建必须不产生错误。
        String insert = player.isAccount()
                ? """
                    INSERT INTO games (id, account_id, guest_id, request_id, mode, level, status, started_at,
                                       deadline_at, deck, deck_position, revision)
                    VALUES (?,?,?,?,?::game_mode,?::game_level,'RUNNING',?,?,?::jsonb,0,0)
                    ON CONFLICT (account_id, request_id) WHERE account_id IS NOT NULL DO NOTHING
                    """
                : """
                    INSERT INTO games (id, account_id, guest_id, request_id, mode, level, status, started_at,
                                       deadline_at, deck, deck_position, revision)
                    VALUES (?,?,?,?,?::game_mode,?::game_level,'RUNNING',?,?,?::jsonb,0,0)
                    ON CONFLICT (guest_id, request_id) DO NOTHING
                    """;
        int inserted = jdbc.update(insert,
                id, player.accountId(), player.guestId(), requestId, mode.name(), level.name(), ts(now),
                mode == Mode.A ? ts(now.plusMillis(aDurationMs)) : null,
                toJson(deck));
        if (inserted == 0) {
            UUID existing = jdbc.queryForObject("""
                    SELECT id FROM games
                     WHERE request_id = ?
                       AND account_id IS NOT DISTINCT FROM ?
                       AND guest_id IS NOT DISTINCT FROM ?
                    """, UUID.class, requestId, player.accountId(), player.guestId());
            return loadGame(existing, player);
        }
        return advance(id, player, "opening", null);
    }

    @Transactional
    public GameView loadGame(UUID gameId, Player player) {
        GameRow row = lockGame(gameId, player);
        // A 模式刷新/回连时补结算：倒计时已归零就立即按正常结束处理，不把 RUNNING 留在 0 秒
        Instant now = clock.instant();
        if (row.status == GameStatus.RUNNING && row.mode == Mode.A && !now.isBefore(row.deadline)) {
            finish(row, now, row.correct);
            row = lockGame(gameId, player);
        }
        return toView(row);
    }

    @Transactional
    public GameView submit(UUID gameId, Player player, String puzzleId, long revision,
                           String actionId, List<OperationStep> steps) {
        Map<String, Object> fingerprint = new LinkedHashMap<>();
        fingerprint.put("puzzleId", puzzleId);
        fingerprint.put("revision", revision);
        fingerprint.put("steps", steps);
        return withIdempotency(gameId, player, actionId, "SUBMIT", fingerprint,
                () -> {
                    GameRow row = lockGame(gameId, player);
                    requireRevision(row, revision);
                    requireRunning(row);
                    PuzzleRow puzzle = loadPuzzle(gameId, puzzleId);
                    requireOpen(puzzle);

                    Instant now = clock.instant();
                    checkNotExpired(row, now);

                    Level level = row.level;
                    boolean correct;
                    try {
                        Fraction value = ExpressionEvaluator.evaluate(puzzle.numbers, steps, level);
                        correct = value.equals(GameRules.TARGET);
                    } catch (IllegalArgumentException e) {
                        throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "INVALID_STEPS", e.getMessage());
                    }

                    if (correct) {
                        long scoring = elapsedWithPenalty(row, now, 0);
                        jdbc.update("UPDATE game_puzzles SET status='SOLVED' WHERE id=?", UUID.fromString(puzzle.id));
                        int nextCorrect = row.correct + 1;
                        boolean finishB = row.mode == Mode.B && nextCorrect >= bTargetCorrect;
                        jdbc.update("""
                                UPDATE games SET correct_count=?, last_scoring_ms=?, revision=revision+1
                                 WHERE id=?
                                """, nextCorrect, scoring, gameId);
                        if (finishB) {
                            finish(row, now, nextCorrect);
                        }
                    } else {
                        // 答错即关闭本题，advance 会直接开下一题，不再重复同一道题
                        jdbc.update("UPDATE game_puzzles SET status='WRONG' WHERE id=?", UUID.fromString(puzzle.id));
                        jdbc.update("""
                                UPDATE games SET wrong_count=wrong_count+1, penalty_ms=penalty_ms+?,
                                       deadline_at = CASE WHEN mode='A' THEN deadline_at - (? * INTERVAL '1 millisecond')
                                                          ELSE deadline_at END,
                                       revision=revision+1
                                 WHERE id=?
                                """, wrongPenaltyMs, wrongPenaltyMs, gameId);
                    }
                    return advance(gameId, player, correct ? "correct" : "wrong", null);
                });
    }

    @Transactional
    public GameView skip(UUID gameId, Player player, String puzzleId, long revision, String actionId) {
        Map<String, Object> fingerprint = new LinkedHashMap<>();
        fingerprint.put("puzzleId", puzzleId);
        fingerprint.put("revision", revision);
        return withIdempotency(gameId, player, actionId, "SKIP", fingerprint,
                () -> {
                    GameRow row = lockGame(gameId, player);
                    requireRevision(row, revision);
                    requireRunning(row);
                    PuzzleRow puzzle = loadPuzzle(gameId, puzzleId);
                    requireOpen(puzzle);

                    Instant now = clock.instant();
                    // 倒计时已经归零时，跳题不再额外罚时，直接进入结算
                    checkNotExpired(row, now);
                    jdbc.update("UPDATE game_puzzles SET status='SKIPPED' WHERE id=?", UUID.fromString(puzzle.id));
                    jdbc.update("""
                            UPDATE games SET skipped_count=skipped_count+1, penalty_ms=penalty_ms+?,
                                   deadline_at = CASE WHEN mode='A' THEN deadline_at - (? * INTERVAL '1 millisecond')
                                                      ELSE deadline_at END,
                                   revision=revision+1
                             WHERE id=?
                            """, skipPenaltyMs, skipPenaltyMs, gameId);

                    GameRow after = lockGame(gameId, player);
                    if (after.mode == Mode.A && !now.isBefore(after.deadline)) {
                        finish(after, now, after.correct);
                    }
                    return advance(gameId, player, "skipped", after);
                });
    }

    @Transactional
    public GameView abandon(UUID gameId, Player player, long revision, String actionId) {
        Map<String, Object> fingerprint = new LinkedHashMap<>();
        fingerprint.put("revision", revision);
        return withIdempotency(gameId, player, actionId, "ABANDON", fingerprint,
                () -> {
                    GameRow row = lockGame(gameId, player);
                    requireRevision(row, revision);
                    if (row.status != GameStatus.RUNNING) {
                        return toView(row);
                    }
                    jdbc.update("""
                            UPDATE games SET status='ABANDONED', finished_at=?, revision=revision+1 WHERE id=?
                            """, ts(clock.instant()), gameId);
                    return toView(lockGame(gameId, player));
                });
    }

    public RecordsView records(Player player, int limit, Mode mode, Level level) {
        int size = Math.max(1, Math.min(100, limit));
        List<Map<String, Object>> history = history(player, size, mode, level);
        List<Map<String, Object>> bests;
        if (player.isAccount()) {
            bests = jdbc.queryForList("""
                    SELECT mode, level, best_correct, best_scoring_ms, achieved_at
                      FROM personal_bests WHERE account_id=?
                    """, player.accountId());
        } else {
            bests = jdbc.queryForList("""
                    SELECT mode, level, best_correct, best_scoring_ms, achieved_at
                      FROM personal_bests WHERE guest_id=? AND account_id IS NULL
                    """, player.guestId());
        }
        return new RecordsView(history, bests);
    }

    private List<Map<String, Object>> history(Player player, int size, Mode mode, Level level) {
        StringBuilder sql = new StringBuilder("""
                SELECT r.result_id, r.mode, r.level, r.correct_count, r.wrong_count, r.skipped_count,
                       r.actual_ms, r.penalty_ms, r.scoring_ms, r.started_at, r.finished_at
                  FROM game_results r
                 WHERE 1=1
                """);
        List<Object> args = new ArrayList<>();
        if (player.isAccount()) {
            sql.append(" AND r.account_id=?");
            args.add(player.accountId());
        } else {
            sql.append(" AND r.guest_id=? AND r.account_id IS NULL");
            args.add(player.guestId());
        }
        if (mode != null) {
            sql.append(" AND r.mode=?::game_mode");
            args.add(mode.name());
        }
        if (level != null) {
            sql.append(" AND r.level=?::game_level");
            args.add(level.name());
        }
        sql.append(" ORDER BY r.finished_at DESC LIMIT ?");
        args.add(size);
        return jdbc.queryForList(sql.toString(), args.toArray());
    }

    // ---------- 内部 ----------

    private GameView advance(UUID gameId, Player player, String lastResult, GameRow knownRow) {
        GameRow row = knownRow != null ? knownRow : lockGame(gameId, player);
        if (row.status != GameStatus.RUNNING) {
            return toView(row);
        }
        Instant now = clock.instant();
        if (row.mode == Mode.A && !now.isBefore(row.deadline)) {
            finish(row, now, row.correct);
            return toView(lockGame(gameId, player));
        }
        PuzzleRow current = currentPuzzle(gameId);
        if (current != null && current.open) {
            return toView(row, current, lastResult);
        }
        if (row.mode == Mode.B && row.correct >= bTargetCorrect) {
            finish(row, now, row.correct);
            return toView(lockGame(gameId, player));
        }
        PuzzleRow next = openNextPuzzle(row, now);
        return toView(lockGame(gameId, player), next, lastResult);
    }

    private PuzzleRow openNextPuzzle(GameRow row, Instant now) {
        List<int[]> deck = row.deck;
        if (row.deckPosition >= deck.size()) {
            List<int[]> fresh = puzzles.deckFor(row.level);
            jdbc.update("UPDATE games SET deck=?::jsonb, deck_position=0 WHERE id=?", toJson(fresh), row.id);
            deck = fresh;
            row.deck = fresh;
            row.deckPosition = 0;
        }
        int[] numbers = deck.get(row.deckPosition);
        UUID puzzleId = UUID.randomUUID();
        int seq = row.deckPosition + 1;
        jdbc.update("""
                INSERT INTO game_puzzles (id, game_id, sequence_no, puzzle_key, numbers_json, status)
                VALUES (?,?,?,?,?::jsonb,'OPEN')
                """, puzzleId, row.id, seq, Arrays.toString(numbers), toJson(numbers));
        jdbc.update("UPDATE games SET deck_position=? WHERE id=?", seq, row.id);
        row.deckPosition = seq;
        return new PuzzleRow(puzzleId.toString(), seq, numbers, true);
    }

    private void finish(GameRow row, Instant now, int correct) {
        long actual = java.time.Duration.between(row.startedAt, now).toMillis();
        long scoring = scoringFor(row.mode, row.lastScoring, elapsedWithPenalty(row, now, 0));
        UUID resultId = UUID.randomUUID();
        jdbc.update("""
                INSERT INTO game_results (result_id, game_id, account_id, guest_id, mode, level, correct_count,
                                          wrong_count, skipped_count, actual_ms, penalty_ms, scoring_ms,
                                          started_at, finished_at)
                VALUES (?,?,?,?,?::game_mode,?::game_level,?,?,?,?,?,?,?,?)
                """, resultId, row.id, row.accountId, row.guestId, row.mode.name(), row.level.name(),
                correct, row.wrong, row.skipped, actual, row.penalty, scoring,
                ts(row.startedAt), ts(now));
        jdbc.update("UPDATE games SET status='FINISHED', finished_at=?, revision=revision+1 WHERE id=?",
                ts(now), row.id);
        // A 模式零题不上榜；B 模式已完成必然有效
        if (row.mode == Mode.A && correct < 1) {
            return;
        }
        if (row.accountId != null) {
            jdbc.update("""
                    INSERT INTO personal_bests (account_id, guest_id, mode, level, result_id, achieved_at,
                                                best_correct, best_scoring_ms)
                    VALUES (?, NULL, ?::game_mode, ?::game_level, ?, ?, ?, ?)
                    ON CONFLICT (account_id, mode, level) WHERE account_id IS NOT NULL DO UPDATE
                       SET result_id = EXCLUDED.result_id,
                           achieved_at = EXCLUDED.achieved_at,
                           best_correct = EXCLUDED.best_correct,
                           best_scoring_ms = EXCLUDED.best_scoring_ms
                     WHERE (EXCLUDED.best_correct > personal_bests.best_correct)
                        OR (EXCLUDED.best_correct = personal_bests.best_correct
                            AND EXCLUDED.best_scoring_ms < personal_bests.best_scoring_ms)
                    """, row.accountId, row.mode.name(), row.level.name(), resultId, ts(now), correct, scoring);
        } else {
            jdbc.update("""
                    INSERT INTO personal_bests (guest_id, mode, level, result_id, achieved_at,
                                                best_correct, best_scoring_ms)
                    VALUES (?,?::game_mode,?::game_level,?,?,?,?)
                    ON CONFLICT (guest_id, mode, level) DO UPDATE
                       SET result_id = EXCLUDED.result_id,
                           achieved_at = EXCLUDED.achieved_at,
                           best_correct = EXCLUDED.best_correct,
                           best_scoring_ms = EXCLUDED.best_scoring_ms
                     WHERE (EXCLUDED.best_correct > personal_bests.best_correct)
                        OR (EXCLUDED.best_correct = personal_bests.best_correct
                            AND EXCLUDED.best_scoring_ms < personal_bests.best_scoring_ms)
                    """, row.guestId, row.mode.name(), row.level.name(), resultId, ts(now), correct, scoring);
        }
    }

    private GameView withIdempotency(UUID gameId, Player player, String actionId, String type,
                                     Map<String, Object> payload, java.util.function.Supplier<GameView> action) {
        String fingerprint;
        try {
            fingerprint = mapper.writeValueAsString(payload);
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
        List<String> existing = jdbc.queryForList(
                "SELECT request_fingerprint FROM game_actions WHERE game_id=? AND action_id=?",
                String.class, gameId, actionId);
        if (!existing.isEmpty()) {
            if (!existing.get(0).equals(fingerprint)) {
                throw new ApiException(HttpStatus.CONFLICT, "ACTION_REUSED", "同一 actionId 不得用于不同请求");
            }
            return loadGame(gameId, player);
        }
        GameView view = action.get();
        jdbc.update("""
                INSERT INTO game_actions (game_id, action_id, action_type, request_fingerprint, response_jsonb)
                VALUES (?,?,?,?,?::jsonb)
                """, gameId, actionId, type, fingerprint, toJson(view));
        return view;
    }

    private static java.sql.Timestamp ts(Instant instant) {
        return java.sql.Timestamp.from(instant);
    }

    private long elapsedWithPenalty(GameRow row, Instant now, long extraPenalty) {
        long elapsed = java.time.Duration.between(row.startedAt, now).toMillis();
        return Math.max(0, elapsed + row.penalty + extraPenalty);
    }

    /**
     * A 榜比"答对最后一题时的计榜用时"，不能用倒计时归零时的实际用时；
     * B 榜比完成第 10 题时的实际用时 + 罚时。
     */
    static long scoringFor(Mode mode, Long lastScoring, long elapsedWithPenalty) {
        return mode == Mode.A ? (lastScoring == null ? 0L : lastScoring) : elapsedWithPenalty;
    }

    private void checkNotExpired(GameRow row, Instant now) {
        if (row.mode == Mode.A && !now.isBefore(row.deadline)) {
            finish(row, now, row.correct);
            throw new ApiException(HttpStatus.CONFLICT, "GAME_EXPIRED", "本局已结束");
        }
    }

    private void requireRevision(GameRow row, long revision) {
        if (row.revision != revision) {
            throw new ApiException(HttpStatus.CONFLICT, "REVISION_MISMATCH", "状态已更新，请同步后重试");
        }
    }

    private void requireRunning(GameRow row) {
        if (row.status != GameStatus.RUNNING) {
            throw new ApiException(HttpStatus.CONFLICT, "GAME_CLOSED", "本局已结束");
        }
    }

    private void requireOpen(PuzzleRow puzzle) {
        if (puzzle == null || !puzzle.open) {
            throw new ApiException(HttpStatus.CONFLICT, "PUZZLE_CLOSED", "题目已关闭");
        }
    }

    private GameRow lockGame(UUID gameId, Player player) {
        List<GameRow> rows = jdbc.query("""
                SELECT id, account_id, guest_id, mode, level, status, started_at, deadline_at, correct_count,
                       wrong_count, skipped_count, penalty_ms, last_scoring_ms, deck, deck_position,
                       revision, finished_at
                  FROM games WHERE id=? FOR UPDATE
                """, this::mapRow, gameId);
        if (rows.isEmpty()) {
            throw new ApiException(HttpStatus.NOT_FOUND, "GAME_NOT_FOUND", "对局不存在");
        }
        GameRow row = rows.get(0);
        boolean owner;
        if (row.accountId != null) {
            owner = row.accountId.equals(player.accountId());
        } else {
            owner = player.accountId() == null && row.guestId != null && row.guestId.equals(player.guestId());
        }
        if (!owner) {
            throw new ApiException(HttpStatus.FORBIDDEN, "PLAYER_MISMATCH", "无权访问该对局");
        }
        return row;
    }

    private PuzzleRow loadPuzzle(UUID gameId, String puzzleId) {
        List<PuzzleRow> rows = jdbc.query("""
                SELECT id, sequence_no, numbers_json, status FROM game_puzzles WHERE game_id=? AND id=?
                """, this::mapPuzzle, gameId, UUID.fromString(puzzleId));
        return rows.isEmpty() ? null : rows.get(0);
    }

    private PuzzleRow currentPuzzle(UUID gameId) {
        List<PuzzleRow> rows = jdbc.query("""
                SELECT id, sequence_no, numbers_json, status FROM game_puzzles
                 WHERE game_id=? ORDER BY sequence_no DESC LIMIT 1
                """, this::mapPuzzle, gameId);
        return rows.isEmpty() ? null : rows.get(0);
    }

    private GameRow mapRow(ResultSet rs, int i) throws SQLException {
        GameRow r = new GameRow();
        r.id = UUID.fromString(rs.getString("id"));
        String accountId = rs.getString("account_id");
        r.accountId = accountId == null ? null : UUID.fromString(accountId);
        r.guestId = rs.getString("guest_id");
        r.mode = Mode.valueOf(rs.getString("mode"));
        r.level = Level.valueOf(rs.getString("level"));
        r.status = GameStatus.valueOf(rs.getString("status"));
        r.startedAt = rs.getTimestamp("started_at").toInstant();
        var deadline = rs.getTimestamp("deadline_at");
        r.deadline = deadline == null ? Instant.MAX : deadline.toInstant();
        r.correct = rs.getInt("correct_count");
        r.wrong = rs.getInt("wrong_count");
        r.skipped = rs.getInt("skipped_count");
        r.penalty = rs.getLong("penalty_ms");
        r.lastScoring = rs.getObject("last_scoring_ms", Long.class);
        r.deck = readDeck(rs.getString("deck"));
        r.deckPosition = rs.getInt("deck_position");
        r.revision = rs.getLong("revision");
        return r;
    }

    private PuzzleRow mapPuzzle(ResultSet rs, int i) throws SQLException {
        int[] numbers;
        try {
            numbers = mapper.readValue(rs.getString("numbers_json"), int[].class);
        } catch (com.fasterxml.jackson.core.JsonProcessingException e) {
            throw new java.sql.SQLException(e);
        }
        return new PuzzleRow(rs.getString("id"), rs.getInt("sequence_no"), numbers,
                "OPEN".equals(rs.getString("status")));
    }

    private List<int[]> readDeck(String json) {
        try {
            int[][] raw = mapper.readValue(json, int[][].class);
            List<int[]> out = new ArrayList<>();
            for (int[] r : raw) out.add(r);
            return out;
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    private String toJson(Object value) {
        try {
            return mapper.writeValueAsString(value);
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    private GameView toView(GameRow row) {
        return toView(row, currentPuzzle(row.id), null);
    }

    private GameView toView(GameRow row, PuzzleRow puzzle, String lastResult) {
        Instant now = clock.instant();
        long elapsed = java.time.Duration.between(row.startedAt, now).toMillis();
        Long remaining = row.mode == Mode.A
                ? Math.max(0, aDurationMs - elapsed - row.penalty)
                : null;
        return new GameView(
                row.id.toString(), row.revision, row.status.name(), row.mode.name(), row.level.name(),
                now.toString(), row.guestId,
                puzzle == null ? null : new PuzzleView(puzzle.id, puzzle.numbers, puzzle.open),
                row.correct, row.wrong, row.skipped, row.penalty,
                remaining, elapsed, row.lastScoring,
                bTargetCorrect, lastResult,
                row.status == GameStatus.FINISHED ? resultOf(row.id) : null);
    }

    private Map<String, Object> resultOf(UUID gameId) {
        List<Map<String, Object>> rows = jdbc.queryForList("""
                SELECT correct_count, wrong_count, skipped_count, actual_ms, penalty_ms, scoring_ms
                  FROM game_results WHERE game_id=?
                """, gameId);
        return rows.isEmpty() ? null : rows.get(0);
    }
}