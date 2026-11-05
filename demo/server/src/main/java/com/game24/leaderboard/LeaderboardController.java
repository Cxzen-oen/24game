package com.game24.leaderboard;

import com.game24.api.ApiException;
import com.game24.rules.Level;
import com.game24.rules.Mode;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/leaderboard")
public class LeaderboardController {

    private final LeaderboardService service;

    public LeaderboardController(LeaderboardService service) {
        this.service = service;
    }

    @GetMapping
    public LeaderboardService.BoardView board(
            @RequestParam String mode,
            @RequestParam String level,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @AuthenticationPrincipal Jwt jwt) {
        return service.board(parseMode(mode), parseLevel(level), page, size, viewer(jwt));
    }

    @GetMapping("/me")
    public List<LeaderboardService.Standing> mine(@AuthenticationPrincipal Jwt jwt) {
        if (jwt == null) {
            throw new ApiException(HttpStatus.UNAUTHORIZED, "UNAUTHORIZED", "请先登录");
        }
        return service.standings(UUID.fromString(jwt.getSubject()));
    }

    private static UUID viewer(Jwt jwt) {
        return jwt == null ? null : UUID.fromString(jwt.getSubject());
    }

    private static Mode parseMode(String raw) {
        try {
            return Mode.valueOf(raw);
        } catch (RuntimeException e) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_MODE", "mode 只能是 A 或 B");
        }
    }

    private static Level parseLevel(String raw) {
        try {
            return Level.valueOf(raw);
        } catch (RuntimeException e) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_LEVEL", "level 只能是 L1 或 L2");
        }
    }
}
