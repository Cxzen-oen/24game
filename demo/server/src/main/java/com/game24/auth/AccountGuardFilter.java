package com.game24.auth;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.game24.api.ErrorResponse;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

/**
 * JWT 通过签名校验后，再确认账号仍存在、未被封禁、令牌版本一致。
 * 这样封禁/改密后，已签发但未过期的 access token 也会立即失效。
 */
@Component
public class AccountGuardFilter extends OncePerRequestFilter {

    private final AccountDirectory accounts;
    private final ObjectMapper mapper;

    public AccountGuardFilter(AccountDirectory accounts, ObjectMapper mapper) {
        this.accounts = accounts;
        this.mapper = mapper;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication instanceof JwtAuthenticationToken token) {
            boolean valid = false;
            try {
                UUID accountId = UUID.fromString(token.getToken().getSubject());
                Object versionClaim = token.getToken().getClaim("tv");
                int version = versionClaim instanceof Number number ? number.intValue() : -1;
                AccountDirectory.AccountRow account = accounts.find(accountId).orElse(null);
                valid = account != null && account.active() && account.tokenVersion() == version;
            } catch (RuntimeException ignored) {
                valid = false;
            }
            if (!valid) {
                SecurityContextHolder.clearContext();
                response.setStatus(HttpStatus.UNAUTHORIZED.value());
                response.setContentType("application/json;charset=UTF-8");
                mapper.writeValue(response.getWriter(),
                        new ErrorResponse("UNAUTHORIZED", "登录状态已失效，请重新登录"));
                return;
            }
        }
        filterChain.doFilter(request, response);
    }
}
