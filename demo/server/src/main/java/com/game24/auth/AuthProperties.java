package com.game24.auth;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

/**
 * 账号与令牌配置。密钥只从环境变量读取，仓库里给的是仅限本机开发的默认值。
 */
@ConfigurationProperties(prefix = "game24.auth")
public record AuthProperties(
        String jwtSecret,
        String issuer,
        Duration accessTtl,
        Duration refreshTtl,
        boolean cookieSecure
) {
}
