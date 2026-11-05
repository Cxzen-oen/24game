package com.game24.auth;

import com.game24.api.ApiException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.core.MethodParameter;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;

import java.util.UUID;
import java.util.regex.Pattern;

/**
 * 把「登录账号或本机游客」解析成 Player 参数。
 * 前端只需要在未登录时带 X-Guest-Id 头。
 */
@Component
public class PlayerArgumentResolver implements HandlerMethodArgumentResolver {

    private static final Pattern GUEST_ID = Pattern.compile("^[A-Za-z0-9_-]{8,64}$");

    @Override
    public boolean supportsParameter(MethodParameter parameter) {
        return Player.class.equals(parameter.getParameterType());
    }

    @Override
    public Object resolveArgument(MethodParameter parameter, ModelAndViewContainer mavContainer,
                                  NativeWebRequest webRequest, WebDataBinderFactory binderFactory) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication instanceof JwtAuthenticationToken token) {
            return Player.of(UUID.fromString(token.getToken().getSubject()));
        }
        HttpServletRequest request = webRequest.getNativeRequest(HttpServletRequest.class);
        String guestId = request == null ? null : request.getHeader("X-Guest-Id");
        if (guestId == null || !GUEST_ID.matcher(guestId).matches()) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "GUEST_ID_REQUIRED",
                    "缺少访客标识，请刷新页面后重试");
        }
        return Player.guest(guestId);
    }
}
