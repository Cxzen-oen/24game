package com.game24.auth;

import com.game24.api.ApiException;
import com.game24.api.ErrorResponse;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    public static final String REFRESH_COOKIE = "g24_rt";

    public record RegisterRequest(String username, String password, String nickname, String guestId) {
    }

    public record LoginRequest(String username, String password, String guestId) {
    }

    public record AuthResponse(String accessToken, String accessExpiresAt,
                               AuthService.AccountView account, int claimedGames) {
    }

    private final AuthService auth;
    private final AuthProperties props;

    public AuthController(AuthService auth, AuthProperties props) {
        this.auth = auth;
        this.props = props;
    }

    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@RequestBody(required = false) RegisterRequest body,
                                                 HttpServletRequest request) {
        if (body == null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "BAD_REQUEST", "请求体不能为空");
        }
        AuthService.AuthSession session = auth.register(
                new AuthService.RegisterCommand(body.username(), body.password(), body.nickname(), body.guestId()),
                userAgent(request), clientIp(request));
        return withCookie(session);
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@RequestBody(required = false) LoginRequest body,
                                              HttpServletRequest request) {
        if (body == null) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "BAD_REQUEST", "请求体不能为空");
        }
        AuthService.AuthSession session = auth.login(
                new AuthService.LoginCommand(body.username(), body.password(), body.guestId()),
                userAgent(request), clientIp(request));
        return withCookie(session);
    }

    @PostMapping("/refresh")
    public ResponseEntity<?> refresh(
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken,
            HttpServletRequest request) {
        try {
            return withCookie(auth.refresh(refreshToken, userAgent(request), clientIp(request)));
        } catch (ApiException e) {
            // 令牌失效时顺手清掉浏览器里的旧 Cookie
            return ResponseEntity.status(e.status())
                    .header(HttpHeaders.SET_COOKIE, clearCookie().toString())
                    .body(new ErrorResponse(e.code(), e.getMessage()));
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<Map<String, Object>> logout(
            @CookieValue(name = REFRESH_COOKIE, required = false) String refreshToken) {
        auth.logout(refreshToken);
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, clearCookie().toString())
                .body(Map.of("ok", true));
    }

    @GetMapping("/me")
    public AuthService.AccountView me(@AuthenticationPrincipal Jwt jwt) {
        return auth.me(UUID.fromString(jwt.getSubject()));
    }

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ErrorResponse> handle(ApiException e) {
        return ResponseEntity.status(e.status()).body(new ErrorResponse(e.code(), e.getMessage()));
    }

    private ResponseEntity<AuthResponse> withCookie(AuthService.AuthSession session) {
        Duration maxAge = Duration.between(Instant.now(), session.refreshExpiresAt());
        if (maxAge.isNegative()) {
            maxAge = Duration.ZERO;
        }
        ResponseCookie cookie = ResponseCookie.from(REFRESH_COOKIE, session.refreshToken())
                .httpOnly(true)
                .secure(props.cookieSecure())
                .sameSite("Strict")
                .path("/api/auth")
                .maxAge(maxAge)
                .build();
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE, cookie.toString())
                .body(new AuthResponse(session.accessToken(), session.accessExpiresAt().toString(),
                        session.account(), session.claimedGames()));
    }

    private ResponseCookie clearCookie() {
        return ResponseCookie.from(REFRESH_COOKIE, "")
                .httpOnly(true)
                .secure(props.cookieSecure())
                .sameSite("Strict")
                .path("/api/auth")
                .maxAge(0)
                .build();
    }

    private static String userAgent(HttpServletRequest request) {
        return request.getHeader("User-Agent");
    }

    private static String clientIp(HttpServletRequest request) {
        return request.getRemoteAddr();
    }
}