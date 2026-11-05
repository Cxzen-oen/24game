package com.game24.api;

import com.game24.auth.Player;
import com.game24.game.GameService;
import com.game24.game.GameView;
import com.game24.game.RecordsView;
import com.game24.rules.Level;
import com.game24.rules.Mode;
import com.game24.rules.OperationStep;
import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api")
public class GameController {

    private final GameService service;
    private final JdbcTemplate jdbc;

    public GameController(GameService service, JdbcTemplate jdbc) {
        this.service = service;
        this.jdbc = jdbc;
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("status", "UP");
        body.put("serverTime", service.clock().instant().toString());
        try {
            jdbc.queryForObject("SELECT 1", Integer.class);
            body.put("db", "UP");
            return ResponseEntity.ok(body);
        } catch (DataAccessException e) {
            body.put("status", "DOWN");
            body.put("db", "DOWN");
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(body);
        }
    }

    @PostMapping("/games")
    public GameView create(Player player, @RequestBody CreateRequest body) {
        return service.createGame(player, body.requestId(),
                Mode.valueOf(body.mode()), Level.valueOf(body.level()));
    }

    @GetMapping("/games/{id}")
    public GameView get(@PathVariable UUID id, Player player) {
        return service.loadGame(id, player);
    }

    @PostMapping("/games/{id}/submit")
    public GameView submit(@PathVariable UUID id, Player player, @RequestBody SubmitRequest body) {
        return service.submit(id, player, body.puzzleId(), body.revision(),
                body.actionId(), body.operations());
    }

    @PostMapping("/games/{id}/skip")
    public GameView skip(@PathVariable UUID id, Player player, @RequestBody ActionRequest body) {
        return service.skip(id, player, body.puzzleId(), body.revision(), body.actionId());
    }

    @PostMapping("/games/{id}/abandon")
    public GameView abandon(@PathVariable UUID id, Player player, @RequestBody AbandonRequest body) {
        return service.abandon(id, player, body.revision(), body.actionId());
    }

    @GetMapping("/records")
    public RecordsView records(Player player,
                               @RequestParam(defaultValue = "50") int limit,
                               @RequestParam(required = false) String mode,
                               @RequestParam(required = false) String level) {
        return service.records(player, limit, parseMode(mode), parseLevel(level));
    }

    private static Mode parseMode(String raw) {
        if (raw == null || raw.isBlank() || "ALL".equalsIgnoreCase(raw)) {
            return null;
        }
        try {
            return Mode.valueOf(raw);
        } catch (IllegalArgumentException e) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_MODE", "mode 只能是 A 或 B");
        }
    }

    private static Level parseLevel(String raw) {
        if (raw == null || raw.isBlank() || "ALL".equalsIgnoreCase(raw)) {
            return null;
        }
        try {
            return Level.valueOf(raw);
        } catch (IllegalArgumentException e) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "INVALID_LEVEL", "level 只能是 L1 或 L2");
        }
    }

    public record CreateRequest(String requestId, String mode, String level) {
    }

    public record SubmitRequest(String puzzleId, long revision, String actionId,
                                List<OperationStep> operations) {
    }

    public record ActionRequest(String puzzleId, long revision, String actionId) {
    }

    public record AbandonRequest(long revision, String actionId) {
    }

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ErrorResponse> handle(ApiException e) {
        return ResponseEntity.status(e.status()).body(new ErrorResponse(e.code(), e.getMessage()));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorResponse> handleBad(IllegalArgumentException e) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(new ErrorResponse("BAD_REQUEST", e.getMessage()));
    }
}
