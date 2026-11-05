package com.game24.auth;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

/**
 * 把本机游客的对局、成绩和最佳并入账号。
 * 同账号并发登录时用账号行锁串行化；最佳成绩按规则严格更好才替换。
 */
@Service
public class GuestClaimService {

    private record GuestBest(String mode, String level, UUID resultId, Instant achievedAt,
                             int correct, long scoring) {
    }

    private final JdbcTemplate jdbc;

    public GuestClaimService(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @Transactional
    public int claim(UUID accountId, String guestId) {
        if (guestId == null || guestId.isBlank()) {
            return 0;
        }
        // 锁账号行，避免同一账号并发合并时唯一键冲突或最佳成绩互相覆盖
        jdbc.queryForObject("SELECT id FROM accounts WHERE id = ? FOR UPDATE", UUID.class, accountId);

        int games = jdbc.update("UPDATE games SET account_id = ? WHERE guest_id = ? AND account_id IS NULL",
                accountId, guestId);
        jdbc.update("UPDATE game_results SET account_id = ? WHERE guest_id = ? AND account_id IS NULL",
                accountId, guestId);

        List<GuestBest> bests = jdbc.query("""
                SELECT mode, level, result_id, achieved_at, best_correct, best_scoring_ms
                  FROM personal_bests WHERE guest_id = ?
                """, (rs, i) -> new GuestBest(
                rs.getString("mode"), rs.getString("level"),
                UUID.fromString(rs.getString("result_id")),
                rs.getTimestamp("achieved_at").toInstant(),
                rs.getInt("best_correct"), rs.getLong("best_scoring_ms")), guestId);

        // 先删游客纪录：result_id 全局唯一，账号纪录要重新引用同一条 result
        jdbc.update("DELETE FROM personal_bests WHERE guest_id = ?", guestId);

        for (GuestBest best : bests) {
            jdbc.update("""
                    INSERT INTO personal_bests (account_id, guest_id, mode, level, result_id,
                                                achieved_at, best_correct, best_scoring_ms)
                    VALUES (?, NULL, ?::game_mode, ?::game_level, ?, ?, ?, ?)
                    ON CONFLICT (account_id, mode, level) WHERE account_id IS NOT NULL DO UPDATE
                       SET result_id = EXCLUDED.result_id,
                           achieved_at = EXCLUDED.achieved_at,
                           best_correct = EXCLUDED.best_correct,
                           best_scoring_ms = EXCLUDED.best_scoring_ms
                     WHERE (EXCLUDED.best_correct > personal_bests.best_correct)
                        OR (EXCLUDED.best_correct = personal_bests.best_correct
                            AND EXCLUDED.best_scoring_ms < personal_bests.best_scoring_ms)
                    """, accountId, best.mode(), best.level(), best.resultId(),
                    java.sql.Timestamp.from(best.achievedAt()), best.correct(), best.scoring());
        }
        return games;
    }
}