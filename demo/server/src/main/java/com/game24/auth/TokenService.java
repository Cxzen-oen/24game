package com.game24.auth;

import com.game24.api.ApiException;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.oauth2.jose.jws.MacAlgorithm;
import org.springframework.security.oauth2.jwt.JwsHeader;
import org.springframework.security.oauth2.jwt.JwtClaimsSet;
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.jwt.JwtEncoderParameters;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.sql.ResultSet;
import java.sql.Timestamp;
import java.sql.SQLException;
import java.time.Clock;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;
import java.util.List;
import java.util.UUID;

/**
 * 令牌服务：
 * - access token：JWT，30 分钟，放 Authorization: Bearer；
 * - refresh token：32 字节随机串，仅存 SHA-256，放 HttpOnly + SameSite=Strict Cookie；
 * - 每次刷新轮换，旧令牌被重放时撤销该账号全部刷新令牌。
 */
@Service
public class TokenService {

    public record Access(String token, Instant expiresAt) {
    }

    public record Rotation(AccountDirectory.AccountRow account, Access access,
                           String refreshToken, Instant refreshExpiresAt) {
    }

    private record RefreshRow(UUID id, UUID accountId, Instant expiresAt,
                              Instant revokedAt, UUID replacedBy) {
    }

    private final JwtEncoder encoder;
    private final JdbcTemplate jdbc;
    private final Clock clock;
    private final AuthProperties props;
    private final AccountDirectory accounts;
    private final SecureRandom random = new SecureRandom();

    public TokenService(JwtEncoder encoder, JdbcTemplate jdbc, Clock clock,
                        AuthProperties props, AccountDirectory accounts) {
        this.encoder = encoder;
        this.jdbc = jdbc;
        this.clock = clock;
        this.props = props;
        this.accounts = accounts;
    }

    public Access issueAccess(AccountDirectory.AccountRow account) {
        Instant now = clock.instant();
        Instant expiresAt = now.plus(props.accessTtl());
        JwtClaimsSet claims = JwtClaimsSet.builder()
                .issuer(props.issuer())
                .subject(account.id().toString())
                .issuedAt(now)
                .expiresAt(expiresAt)
                .id(UUID.randomUUID().toString())
                .claim("nick", account.nickname())
                .claim("tv", account.tokenVersion())
                .build();
        JwsHeader header = JwsHeader.with(MacAlgorithm.HS256).build();
        String token = encoder.encode(JwtEncoderParameters.from(header, claims)).getTokenValue();
        return new Access(token, expiresAt);
    }

    public String newRefreshToken(UUID accountId, String userAgent, String ip, Instant expiresAt) {
        String raw = randomToken();
        jdbc.update("""
                INSERT INTO refresh_tokens (id, account_id, token_hash, issued_at, expires_at, user_agent, ip)
                VALUES (?,?,?,?,?,?,?)
                """, UUID.randomUUID(), accountId, sha256(raw),
                Timestamp.from(clock.instant()), Timestamp.from(expiresAt),
                truncate(userAgent, 300), truncate(ip, 60));
        return raw;
    }

    @Transactional
    public Rotation rotate(String rawToken, String userAgent, String ip) {
        if (rawToken == null || rawToken.isBlank()) {
            throw unauthorized("登录已过期，请重新登录");
        }
        List<RefreshRow> rows = jdbc.query("""
                SELECT id, account_id, expires_at, revoked_at, replaced_by
                  FROM refresh_tokens WHERE token_hash = ? FOR UPDATE
                """, this::mapRefresh, sha256(rawToken));
        if (rows.isEmpty()) {
            throw unauthorized("登录已过期，请重新登录");
        }
        RefreshRow row = rows.get(0);
        Instant now = clock.instant();
        if (row.revokedAt() != null) {
            // 已轮换的旧令牌被再次使用：视为泄露，撤销该账号全部刷新令牌。
            // 这里不能抛异常，否则事务回滚，撤销会丢失；返回 null 由调用方转成 401。
            if (row.replacedBy() != null) {
                jdbc.update("UPDATE refresh_tokens SET revoked_at = ? WHERE account_id = ? AND revoked_at IS NULL",
                        Timestamp.from(now), row.accountId());
            }
            return null;
        }
        if (!now.isBefore(row.expiresAt())) {
            throw unauthorized("登录已过期，请重新登录");
        }
        AccountDirectory.AccountRow account = accounts.find(row.accountId())
                .filter(AccountDirectory.AccountRow::active)
                .orElseThrow(() -> unauthorized("账号状态异常，请重新登录"));

        String newRaw = randomToken();
        UUID newId = UUID.randomUUID();
        Instant newExpires = now.plus(props.refreshTtl());
        jdbc.update("""
                UPDATE refresh_tokens SET revoked_at = ?, replaced_by = ? WHERE id = ?
                """, Timestamp.from(now), newId, row.id());
        jdbc.update("""
                INSERT INTO refresh_tokens (id, account_id, token_hash, issued_at, expires_at, user_agent, ip)
                VALUES (?,?,?,?,?,?,?)
                """, newId, row.accountId(), sha256(newRaw),
                Timestamp.from(now), Timestamp.from(newExpires),
                truncate(userAgent, 300), truncate(ip, 60));
        return new Rotation(account, issueAccess(account), newRaw, newExpires);
    }

    @Transactional
    public void revoke(String rawToken) {
        if (rawToken == null || rawToken.isBlank()) {
            return;
        }
        jdbc.update("UPDATE refresh_tokens SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
                Timestamp.from(clock.instant()), sha256(rawToken));
    }

    @Transactional
    public void revokeAll(UUID accountId) {
        jdbc.update("UPDATE refresh_tokens SET revoked_at = ? WHERE account_id = ? AND revoked_at IS NULL",
                Timestamp.from(clock.instant()), accountId);
    }

    private String randomToken() {
        byte[] bytes = new byte[32];
        random.nextBytes(bytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }

    static String sha256(String value) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(value.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }

    private RefreshRow mapRefresh(ResultSet rs, int index) throws SQLException {
        var replacedBy = rs.getString("replaced_by");
        var revokedAt = rs.getTimestamp("revoked_at");
        return new RefreshRow(
                UUID.fromString(rs.getString("id")),
                UUID.fromString(rs.getString("account_id")),
                rs.getTimestamp("expires_at").toInstant(),
                revokedAt == null ? null : revokedAt.toInstant(),
                replacedBy == null ? null : UUID.fromString(replacedBy));
    }

    private static String truncate(String value, int max) {
        if (value == null) {
            return null;
        }
        return value.length() <= max ? value : value.substring(0, max);
    }

    private static ApiException unauthorized(String message) {
        return new ApiException(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", message);
    }
}