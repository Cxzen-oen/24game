package com.game24.leaderboard;

import com.game24.api.ApiException;
import com.game24.rules.Level;
import com.game24.rules.Mode;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 排行榜直接从 personal_bests 派生：每个账号每个「模式 × 难度」只有一条最佳成绩，
 * 不另存一份排名数据，避免最佳成绩与榜单不一致。
 *
 * 排序口径（规则文档 5.3）：
 *   A：答对题数降序 → 计榜用时升序 → 先取得者优先 → 账号 ID 兜底
 *   B：计榜用时升序 → 先取得者优先 → 账号 ID 兜底
 */
@Service
public class LeaderboardService {

    public record Entry(int rank, String accountId, String nickname, int correct,
                        long scoringMs, Instant achievedAt) {
    }

    /** rank 为 null 表示该账号在这个榜上还没有有效成绩。 */
    public record Standing(String mode, String level, Integer rank, Integer correct,
                           Long scoringMs, Instant achievedAt) {
    }

    public record BoardView(String mode, String level, long total, int page, int size,
                            List<Entry> entries, Standing me) {
    }

    private record BestRow(int correct, long scoring, Instant achievedAt) {
    }

    /**
     * 排行榜展示用：隐藏昵称第一个字符（按 Unicode 码点，避免把 emoji 截断）。
     */
    static String maskNickname(String nickname) {
        if (nickname == null || nickname.isEmpty()) {
            return nickname;
        }
        int end = nickname.offsetByCodePoints(0, 1);
        return "*" + nickname.substring(end);
    }

    private final JdbcTemplate jdbc;

    public LeaderboardService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public BoardView board(Mode mode, Level level, int page, int size, UUID viewer) {
        int safeSize = Math.max(1, Math.min(50, size));
        int safePage = Math.max(0, page);
        long offset = (long) safePage * safeSize;
        if (offset > 5_000) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "PAGE_OUT_OF_RANGE", "翻页过深，请缩小范围");
        }
        String order = mode == Mode.A
                ? "b.best_correct DESC, b.best_scoring_ms ASC, b.achieved_at ASC, b.account_id ASC"
                : "b.best_scoring_ms ASC, b.achieved_at ASC, b.account_id ASC";

        String entriesSql = """
                SELECT b.account_id, a.nickname, b.best_correct, b.best_scoring_ms, b.achieved_at
                  FROM personal_bests b
                  JOIN accounts a ON a.id = b.account_id
                 WHERE b.account_id IS NOT NULL
                   AND b.mode = ?::game_mode
                   AND b.level = ?::game_level
                   AND a.status = 'ACTIVE'
                 ORDER BY %s
                 LIMIT ? OFFSET ?
                """.formatted(order);

        List<Entry> entries = jdbc.query(entriesSql, (rs, i) -> new Entry(
                        (int) offset + i + 1,
                        rs.getString("account_id"),
                        maskNickname(rs.getString("nickname")),
                        rs.getInt("best_correct"),
                        rs.getLong("best_scoring_ms"),
                        rs.getTimestamp("achieved_at").toInstant()),
                mode.name(), level.name(), safeSize, offset);

        Long total = jdbc.queryForObject("""
                SELECT count(*)
                  FROM personal_bests b
                  JOIN accounts a ON a.id = b.account_id
                 WHERE b.account_id IS NOT NULL
                   AND b.mode = ?::game_mode
                   AND b.level = ?::game_level
                   AND a.status = 'ACTIVE'
                """, Long.class, mode.name(), level.name());

        Standing me = viewer == null ? null : standing(mode, level, viewer);
        return new BoardView(mode.name(), level.name(), total == null ? 0 : total,
                safePage, safeSize, entries, me);
    }

    public Standing standing(Mode mode, Level level, UUID accountId) {
        List<BestRow> rows = jdbc.query("""
                SELECT best_correct, best_scoring_ms, achieved_at
                  FROM personal_bests
                 WHERE account_id = ? AND mode = ?::game_mode AND level = ?::game_level
                """, (rs, i) -> new BestRow(rs.getInt("best_correct"),
                rs.getLong("best_scoring_ms"), rs.getTimestamp("achieved_at").toInstant()),
                accountId, mode.name(), level.name());
        if (rows.isEmpty()) {
            return new Standing(mode.name(), level.name(), null, null, null, null);
        }
        BestRow own = rows.get(0);
        int rank = countAhead(mode, level, accountId, own) + 1;
        return new Standing(mode.name(), level.name(), rank, own.correct(), own.scoring(), own.achievedAt());
    }

    public List<Standing> standings(UUID accountId) {
        List<Standing> out = new ArrayList<>();
        for (Mode mode : Mode.values()) {
            for (Level level : Level.values()) {
                out.add(standing(mode, level, accountId));
            }
        }
        return out;
    }

    private int countAhead(Mode mode, Level level, UUID accountId, BestRow own) {
        String sql = mode == Mode.A ? """
                SELECT count(*)
                  FROM personal_bests b
                  JOIN accounts a ON a.id = b.account_id
                 WHERE b.account_id IS NOT NULL
                   AND b.mode = ?::game_mode
                   AND b.level = ?::game_level
                   AND a.status = 'ACTIVE'
                   AND (b.best_correct > ?
                        OR (b.best_correct = ? AND b.best_scoring_ms < ?)
                        OR (b.best_correct = ? AND b.best_scoring_ms = ? AND b.achieved_at < ?)
                        OR (b.best_correct = ? AND b.best_scoring_ms = ? AND b.achieved_at = ? AND b.account_id < ?))
                """ : """
                SELECT count(*)
                  FROM personal_bests b
                  JOIN accounts a ON a.id = b.account_id
                 WHERE b.account_id IS NOT NULL
                   AND b.mode = ?::game_mode
                   AND b.level = ?::game_level
                   AND a.status = 'ACTIVE'
                   AND (b.best_scoring_ms < ?
                        OR (b.best_scoring_ms = ? AND b.achieved_at < ?)
                        OR (b.best_scoring_ms = ? AND b.achieved_at = ? AND b.account_id < ?))
                """;
        Integer count = mode == Mode.A
                ? jdbc.queryForObject(sql, Integer.class, mode.name(), level.name(),
                own.correct(), own.correct(), own.scoring(),
                own.correct(), own.scoring(), java.sql.Timestamp.from(own.achievedAt()),
                own.correct(), own.scoring(), java.sql.Timestamp.from(own.achievedAt()), accountId)
                : jdbc.queryForObject(sql, Integer.class, mode.name(), level.name(),
                own.scoring(), own.scoring(), java.sql.Timestamp.from(own.achievedAt()),
                own.scoring(), java.sql.Timestamp.from(own.achievedAt()), accountId);
        return count == null ? 0 : count;
    }
}