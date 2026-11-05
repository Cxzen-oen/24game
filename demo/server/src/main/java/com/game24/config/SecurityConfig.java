package com.game24.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.game24.api.ErrorResponse;
import com.game24.auth.AccountGuardFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.security.oauth2.server.resource.web.authentication.BearerTokenAuthenticationFilter;

import java.io.IOException;

/**
 * 无状态 JWT 资源服务器。
 * 公开接口：健康检查、注册登录、刷新、排行榜、对局（游客也能玩）。
 * 需要登录：/api/auth/me。
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        // BCrypt 成本 12，单次校验约 250ms；登录入口已有限流
        return new BCryptPasswordEncoder(12);
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http,
                                                   AccountGuardFilter accountGuardFilter,
                                                   ObjectMapper objectMapper) throws Exception {
        http
                .csrf(csrf -> csrf.disable())
                .cors(cors -> cors.disable())
                .httpBasic(basic -> basic.disable())
                .formLogin(form -> form.disable())
                .logout(logout -> logout.disable())
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/api/auth/me").authenticated()
                        // 对局与排行榜对游客开放，归属校验在业务层完成
                        .requestMatchers("/api/**").permitAll()
                        .anyRequest().permitAll())
                .oauth2ResourceServer(oauth -> oauth
                        .jwt(Customizer.withDefaults())
                        .authenticationEntryPoint(jsonEntryPoint(objectMapper)))
                .exceptionHandling(ex -> ex
                        .authenticationEntryPoint(jsonEntryPoint(objectMapper))
                        .accessDeniedHandler(jsonAccessDenied(objectMapper)))
                .headers(headers -> headers.frameOptions(frame -> frame.deny()))
                .addFilterAfter(accountGuardFilter, BearerTokenAuthenticationFilter.class);
        return http.build();
    }

    private AuthenticationEntryPoint jsonEntryPoint(ObjectMapper mapper) {
        return (request, response, ex) -> writeJson(mapper, response, HttpStatus.UNAUTHORIZED,
                new ErrorResponse("UNAUTHORIZED", "请先登录"));
    }

    private AccessDeniedHandler jsonAccessDenied(ObjectMapper mapper) {
        return (request, response, ex) -> writeJson(mapper, response, HttpStatus.FORBIDDEN,
                new ErrorResponse("FORBIDDEN", "没有权限"));
    }

    private void writeJson(ObjectMapper mapper, jakarta.servlet.http.HttpServletResponse response,
                           HttpStatus status, ErrorResponse body) throws IOException {
        response.setStatus(status.value());
        response.setContentType("application/json;charset=UTF-8");
        mapper.writeValue(response.getWriter(), body);
    }
}
