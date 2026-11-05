package com.game24.auth;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * 账号只读查询。登录校验需要密码哈希，其余场景不读取。
 */
@Service
public class AccountDirectory {

    public record AccountRow(UUID id, String username, String nickname, String status,
                             int tokenVersion, Instant createdAt) {
        public boolean active() {
            return "ACTIVE".equals(status);
        }
    }

    public record Credential(AccountRow account, String passwordHash) {
    }

    private final JdbcTemplate jdbc;

    public AccountDirectory(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public Optional<AccountRow> find(UUID id) {
        List<AccountRow> rows = jdbc.query("""
                SELECT id, username, nickname, status, token_version, created_at
                  FROM accounts WHERE id = ?
                """, this::map, id);
        return rows.stream().findFirst();
    }

    public Optional<AccountRow> findByUsername(String username) {
        List<AccountRow> rows = jdbc.query("""
                SELECT id, username, nickname, status, token_version, created_at
                  FROM accounts WHERE username = ?
                """, this::map, username);
        return rows.stream().findFirst();
    }

    public Optional<Credential> findCredential(String username) {
        List<Credential> rows = jdbc.query("""
                SELECT id, username, nickname, status, token_version, created_at, password_hash
                  FROM accounts WHERE username = ?
                """, (rs, i) -> new Credential(map(rs, i), rs.getString("password_hash")), username);
        return rows.stream().findFirst();
    }

    private AccountRow map(ResultSet rs, int i) throws SQLException {
        return new AccountRow(
                UUID.fromString(rs.getString("id")),
                rs.getString("username"),
                rs.getString("nickname"),
                rs.getString("status"),
                rs.getInt("token_version"),
                rs.getTimestamp("created_at").toInstant());
    }
}
