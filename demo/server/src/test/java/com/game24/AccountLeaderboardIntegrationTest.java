package com.game24;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.game24.auth.AuthRateLimiter;
import jakarta.servlet.http.Cookie;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.jdbc.Sql;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.nio.charset.StandardCharsets;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * 需要真实 PostgreSQL（默认连 127.0.0.1:5432 的 game24_test schema）。
 * 默认 mvn test 不执行；用 mvn test -Pintegration 跑。
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Tag("integration")
@Sql(scripts = "/truncate.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
class AccountLeaderboardIntegrationTest {

    private static final String PASSWORD = "passw0rd";

    @Autowired
    private MockMvc mvc;
    @Autowired
    private JdbcTemplate jdbc;
    @Autowired
    private AuthRateLimiter rateLimiter;
    private final ObjectMapper mapper = new ObjectMapper();

    @BeforeEach
    void resetRateLimits() {
        rateLimiter.clear();
    }

    @Test
    void registerLoginAndMe() throws Exception {
        String token = register("alice01", "爱丽丝", null).get("accessToken").asText();

        mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username").value("alice01"))
                .andExpect(jsonPath("$.nickname").value("爱丽丝"));

        mvc.perform(post("/api/auth/register").contentType(MediaType.APPLICATION_JSON)
                        .content(json("""
                                {"username":"alice01","password":"passw0rd","nickname":"另一个人"}
                                """)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.code").value("USERNAME_TAKEN"));

        mvc.perform(post("/api/auth/login").contentType(MediaType.APPLICATION_JSON)
                        .content(json("""
                                {"username":"alice01","password":"wrong-pass1"}
                                """)))
                .andExpect(status().isUnauthorized())
                .andExpect(jsonPath("$.code").value("INVALID_CREDENTIALS"));
    }

    @Test
    void refreshRotatesAndDetectsReuse() throws Exception {
        MvcResult registered = mvc.perform(post("/api/auth/register").contentType(MediaType.APPLICATION_JSON)
                        .content(json("""
                                {"username":"bob0001","password":"passw0rd","nickname":"鲍勃"}
                                """)))
                .andExpect(status().isOk())
                .andReturn();
        String firstCookie = refreshCookie(registered);

        MvcResult refreshed = mvc.perform(post("/api/auth/refresh").cookie(new Cookie("g24_rt", firstCookie)))
                .andExpect(status().isOk())
                .andReturn();
        String secondCookie = refreshCookie(refreshed);
        assertThat(secondCookie).isNotEqualTo(firstCookie);

        // 旧令牌重放：拒绝，并撤销该账号全部刷新令牌
        mvc.perform(post("/api/auth/refresh").cookie(new Cookie("g24_rt", firstCookie)))
                .andExpect(status().isUnauthorized());
        mvc.perform(post("/api/auth/refresh").cookie(new Cookie("g24_rt", secondCookie)))
                .andExpect(status().isUnauthorized());
    }

    @Test
    void guestScoresAreClaimedByNewAccount() throws Exception {
        UUID gameId = UUID.randomUUID();
        UUID resultId = UUID.randomUUID();
        String guestId = "guest-claim-0001";
        insertFinishedGame(gameId, resultId, null, guestId, "A", "L1", 5, 120000, Instant.now());
        jdbc.update("""
                INSERT INTO personal_bests (guest_id, mode, level, result_id, achieved_at, best_correct, best_scoring_ms)
                VALUES (?, 'A', 'L1', ?, now(), 5, 120000)
                """, guestId, resultId);

        JsonNode registered = register("carol01", "卡罗尔", guestId);
        UUID accountId = UUID.fromString(registered.get("account").get("id").asText());
        assertThat(registered.get("claimedGames").asInt()).isEqualTo(1);

        Integer accountBests = jdbc.queryForObject(
                "SELECT count(*) FROM personal_bests WHERE account_id = ?", Integer.class, accountId);
        Integer guestBests = jdbc.queryForObject(
                "SELECT count(*) FROM personal_bests WHERE guest_id = ?", Integer.class, guestId);
        assertThat(accountBests).isEqualTo(1);
        assertThat(guestBests).isZero();

        String token = registered.get("accessToken").asText();
        mvc.perform(get("/api/records").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.history.length()").value(1))
                .andExpect(jsonPath("$.bests.length()").value(1));

        mvc.perform(get("/api/records?mode=A&level=L1").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.history.length()").value(1));
        mvc.perform(get("/api/records?mode=B&level=L1").header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.history.length()").value(0));
        mvc.perform(get("/api/records?mode=X").header("Authorization", "Bearer " + token))
                .andExpect(status().isBadRequest());
    }

    @Test
    void leaderboardOrderAndMyRank() throws Exception {
        JsonNode alice = register("alice02", "阿尔法", null);
        JsonNode bob = register("bob0002", "贝塔", null);
        JsonNode carol = register("carol02", "伽马", null);

        UUID aliceId = UUID.fromString(alice.get("account").get("id").asText());
        UUID bobId = UUID.fromString(bob.get("account").get("id").asText());
        UUID carolId = UUID.fromString(carol.get("account").get("id").asText());

        Instant base = Instant.parse("2026-01-01T00:00:00Z");
        insertBest(aliceId, "A", "L1", 15, 238000, base);
        insertBest(bobId, "A", "L1", 15, 245000, base.plusSeconds(60));
        insertBest(carolId, "A", "L1", 16, 300000, base.plusSeconds(120));

        mvc.perform(get("/api/leaderboard?mode=A&level=L1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total").value(3))
                .andExpect(jsonPath("$.entries[0].nickname").value("*马"))
                .andExpect(jsonPath("$.entries[1].nickname").value("*尔法"))
                .andExpect(jsonPath("$.entries[2].nickname").value("*塔"))
                .andExpect(jsonPath("$.entries[1].rank").value(2));

        mvc.perform(get("/api/leaderboard?mode=A&level=L1")
                        .header("Authorization", "Bearer " + bob.get("accessToken").asText()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.me.rank").value(3))
                .andExpect(jsonPath("$.me.correct").value(15));

        // B 榜只按用时排序
        insertBest(aliceId, "B", "L1", 10, 185000, base);
        insertBest(bobId, "B", "L1", 10, 181000, base.plusSeconds(30));
        mvc.perform(get("/api/leaderboard?mode=B&level=L1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.entries[0].nickname").value("*塔"))
                .andExpect(jsonPath("$.entries[1].nickname").value("*尔法"));
    }

    private JsonNode register(String username, String nickname, String guestId) throws Exception {
        String body = mapper.writeValueAsString(new java.util.HashMap<String, Object>() {{
            put("username", username);
            put("password", PASSWORD);
            put("nickname", nickname);
            if (guestId != null) {
                put("guestId", guestId);
            }
        }});
        MvcResult result = mvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(body.getBytes(StandardCharsets.UTF_8)))
                .andExpect(status().isOk())
                .andReturn();
        return mapper.readTree(result.getResponse().getContentAsByteArray());
    }

    private static String refreshCookie(MvcResult result) {
        String header = result.getResponse().getHeader("Set-Cookie");
        assertThat(header).isNotNull();
        String value = header.split(";", 2)[0];
        return value.substring("g24_rt=".length());
    }

    private static byte[] json(String body) {
        return body.strip().getBytes(StandardCharsets.UTF_8);
    }

    private void insertFinishedGame(UUID gameId, UUID resultId, UUID accountId, String guestId,
                                    String mode, String level, int correct, long scoring, Instant achievedAt) {
        jdbc.update("""
                INSERT INTO games (id, account_id, guest_id, request_id, mode, level, status, started_at,
                                   correct_count, wrong_count, skipped_count, penalty_ms, last_scoring_ms,
                                   deck, deck_position, revision, finished_at)
                VALUES (?,?,?,?,?::game_mode,?::game_level,'FINISHED',?,?,0,0,0,?, '[]'::jsonb,0,1,?)
                """, gameId, accountId, guestId, "req-" + gameId, mode, level,
                Timestamp.from(achievedAt.minusSeconds(200)), correct, scoring, Timestamp.from(achievedAt));
        jdbc.update("""
                INSERT INTO game_results (result_id, game_id, account_id, guest_id, mode, level, correct_count,
                                          wrong_count, skipped_count, actual_ms, penalty_ms, scoring_ms,
                                          started_at, finished_at)
                VALUES (?,?,?,?,?::game_mode,?::game_level,?,0,0,200000,0,?,?,?)
                """, resultId, gameId, accountId, guestId, mode, level, correct, scoring,
                Timestamp.from(achievedAt.minusSeconds(200)), Timestamp.from(achievedAt));
    }

    private void insertBest(UUID accountId, String mode, String level, int correct, long scoring,
                            Instant achievedAt) {
        UUID gameId = UUID.randomUUID();
        UUID resultId = UUID.randomUUID();
        insertFinishedGame(gameId, resultId, accountId, null, mode, level, correct, scoring, achievedAt);
        jdbc.update("""
                INSERT INTO personal_bests (account_id, guest_id, mode, level, result_id,
                                            achieved_at, best_correct, best_scoring_ms)
                VALUES (?, NULL, ?::game_mode, ?::game_level, ?, ?, ?, ?)
                """, accountId, mode, level, resultId, Timestamp.from(achievedAt), correct, scoring);
    }
}
