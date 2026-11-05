package com.game24.auth;

import com.game24.api.ApiException;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Locale;
import java.util.Optional;
import java.util.UUID;
import java.util.regex.Pattern;

/**
 * 注册、登录、刷新。账号安全相关的规则只在这里实现，Controller 不重复判断。
 */
@Service
public class AuthService {

    private static final Pattern USERNAME = Pattern.compile("^[a-z][a-z0-9_]{3,19}$");
    private static final Pattern GUEST_ID = Pattern.compile("^[A-Za-z0-9_-]{8,64}$");
    private static final Pattern CONTROL = Pattern.compile("\\p{Cntrl}");
    private static final Pattern HAS_LETTER = Pattern.compile(".*[A-Za-z].*");
    private static final Pattern HAS_DIGIT = Pattern.compile(".*[0-9].*");

    public record AccountView(String id, String username, String nickname, String createdAt) {
    }

    public record AuthSession(String accessToken, Instant accessExpiresAt,
                              String refreshToken, Instant refreshExpiresAt,
                              AccountView account, int claimedGames) {
    }

    public record RegisterCommand(String username, String password, String nickname, String guestId) {
    }

    public record LoginCommand(String username, String password, String guestId) {
    }

    private final JdbcTemplate jdbc;
    private final PasswordEncoder encoder;
    private final AccountDirectory accounts;
    private final TokenService tokens;
    private final GuestClaimService guestClaim;
    private final AuthRateLimiter limiter;
    private final Clock clock;
    private final AuthProperties props;
    private final String dummyHash;

    public AuthService(JdbcTemplate jdbc, PasswordEncoder encoder, AccountDirectory accounts,
                       TokenService tokens, GuestClaimService guestClaim, AuthRateLimiter limiter,
                       Clock clock, AuthProperties props) {
        this.jdbc = jdbc;
        this.encoder = encoder;
        this.accounts = accounts;
        this.tokens = tokens;
        this.guestClaim = guestClaim;
        this.limiter = limiter;
        this.clock = clock;
        this.props = props;
        // 用户名不存在时也跑一次 BCrypt，避免通过响应时间枚举账号
        this.dummyHash = encoder.encode("dummy-password-42");
    }

    @Transactional
    public AuthSession register(RegisterCommand cmd, String userAgent, String ip) {
        limiter.check("register:ip:" + ip, 10, Duration.ofHours(1));

        String username = normalizeUsername(cmd.username());
        String nickname = normalizeNickname(cmd.nickname(), username);
        validatePassword(cmd.password());
        String guestId = normalizeGuestId(cmd.guestId());

        UUID id = UUID.randomUUID();
        Instant now = clock.instant();
        try {
            jdbc.update("""
                    INSERT INTO accounts (id, username, nickname, password_hash, status, token_version,
                                          created_at, updated_at)
                    VALUES (?,?,?,?, 'ACTIVE', 0, ?, ?)
                    """, id, username, nickname, encoder.encode(cmd.password()),
                    java.sql.Timestamp.from(now), java.sql.Timestamp.from(now));
        } catch (DuplicateKeyException e) {
            throw new ApiException(HttpStatus.CONFLICT, "USERNAME_TAKEN", "用户名已被占用");
        }

        int claimed = guestClaim.claim(id, guestId);
        AccountDirectory.AccountRow account = accounts.find(id).orElseThrow();
        return session(account, userAgent, ip, claimed);
    }

    @Transactional
    public AuthSession login(LoginCommand cmd, String userAgent, String ip) {
        limiter.check("login:ip:" + ip, 60, Duration.ofMinutes(10));

        String username = cmd.username() == null ? "" : cmd.username().trim().toLowerCase(Locale.ROOT);
        String failKey = "login:fail:" + ip + ":" + username;
        limiter.ensureBelow(failKey, 8, Duration.ofMinutes(15));

        String password = cmd.password() == null ? "" : cmd.password();
        Optional<AccountDirectory.Credential> credential = accounts.findCredential(username);
        if (credential.isEmpty()) {
            encoder.matches(password, dummyHash);
            limiter.hit(failKey, Duration.ofMinutes(15));
            throw invalidCredentials();
        }
        if (!encoder.matches(password, credential.get().passwordHash())) {
            limiter.hit(failKey, Duration.ofMinutes(15));
            throw invalidCredentials();
        }
        limiter.reset(failKey);

        AccountDirectory.AccountRow account = credential.get().account();
        if (!account.active()) {
            throw new ApiException(HttpStatus.FORBIDDEN, "ACCOUNT_BANNED", "账号已被封禁");
        }
        String guestId = normalizeGuestId(cmd.guestId());
        Instant now = clock.instant();
        jdbc.update("UPDATE accounts SET last_login_at = ? WHERE id = ?",
                java.sql.Timestamp.from(now), account.id());
        int claimed = guestClaim.claim(account.id(), guestId);
        return session(account, userAgent, ip, claimed);
    }

    public AuthSession refresh(String rawToken, String userAgent, String ip) {
        TokenService.Rotation rotation = tokens.rotate(rawToken, userAgent, ip);
        if (rotation == null) {
            throw new ApiException(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "登录状态已失效，请重新登录");
        }
        return new AuthSession(rotation.access().token(), rotation.access().expiresAt(),
                rotation.refreshToken(), rotation.refreshExpiresAt(),
                toView(rotation.account()), 0);
    }

    public AccountView me(UUID accountId) {
        AccountDirectory.AccountRow account = accounts.find(accountId)
                .orElseThrow(() -> new ApiException(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "请先登录"));
        return toView(account);
    }

    public void logout(String rawToken) {
        tokens.revoke(rawToken);
    }

    private AuthSession session(AccountDirectory.AccountRow account, String userAgent, String ip, int claimed) {
        TokenService.Access access = tokens.issueAccess(account);
        Instant refreshExpiresAt = clock.instant().plus(props.refreshTtl());
        String refreshToken = tokens.newRefreshToken(account.id(), userAgent, ip, refreshExpiresAt);
        return new AuthSession(access.token(), access.expiresAt(), refreshToken, refreshExpiresAt,
                toView(account), claimed);
    }

    private AccountView toView(AccountDirectory.AccountRow account) {
        return new AccountView(account.id().toString(), account.username(), account.nickname(),
                account.createdAt().toString());
    }

    private static ApiException invalidCredentials() {
        return new ApiException(HttpStatus.UNAUTHORIZED, "INVALID_CREDENTIALS", "用户名或密码错误");
    }

    static String normalizeUsername(String raw) {
        String username = raw == null ? "" : raw.trim().toLowerCase(Locale.ROOT);
        if (!USERNAME.matcher(username).matches()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_USERNAME",
                    "用户名需 4-20 位，字母开头，只能包含小写字母、数字和下划线");
        }
        return username;
    }

    static String normalizeNickname(String raw, String username) {
        String nickname = raw == null ? "" : raw.trim();
        if (nickname.isEmpty()) {
            nickname = username.length() <= 12 ? username : username.substring(0, 12);
        }
        int length = nickname.codePointCount(0, nickname.length());
        if (length < 2 || length > 12 || CONTROL.matcher(nickname).find()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_NICKNAME",
                    "昵称需 2-12 个字符，且不能包含控制字符");
        }
        return nickname;
    }

    static void validatePassword(String password) {
        if (password == null || password.length() < 8 || password.length() > 64
                || !HAS_LETTER.matcher(password).matches()
                || !HAS_DIGIT.matcher(password).matches()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_PASSWORD",
                    "密码需 8-64 位，且同时包含字母和数字");
        }
    }

    static String normalizeGuestId(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        String guestId = raw.trim();
        if (!GUEST_ID.matcher(guestId).matches()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_GUEST_ID", "访客标识格式不正确");
        }
        return guestId;
    }
}