package com.game24.auth;

import java.util.UUID;

/**
 * 一次请求的玩家身份：登录账号优先；未登录时用本机游客标识。
 * 两者至少有一个非空。
 */
public record Player(UUID accountId, String guestId) {

    public boolean isAccount() {
        return accountId != null;
    }

    public static Player of(UUID accountId) {
        return new Player(accountId, null);
    }

    public static Player guest(String guestId) {
        return new Player(null, guestId);
    }
}
