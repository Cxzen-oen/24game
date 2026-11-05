package com.game24.config;

import com.game24.auth.PlayerArgumentResolver;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.List;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    private final PlayerArgumentResolver playerArgumentResolver;

    public WebConfig(PlayerArgumentResolver playerArgumentResolver) {
        this.playerArgumentResolver = playerArgumentResolver;
    }

    @Override
    public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
        resolvers.add(playerArgumentResolver);
    }
}
