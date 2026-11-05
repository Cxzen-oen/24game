package com.game24.auth;

import com.game24.api.ApiException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

import java.time.Clock;
import java.time.Duration;
import java.util.Iterator;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 单机固定窗口限流。只用于登录/注册这类低频入口；
 * 多实例部署时换成 Redis（见上云架构文档），接口保持不变。
 */
@Component
public class AuthRateLimiter {

    private static final class Bucket {
        long windowStart;
        int count;

        Bucket(long windowStart) {
            this.windowStart = windowStart;
        }
    }

    private final Clock clock;
    private final Map<String, Bucket> buckets = new ConcurrentHashMap<>();
    private final AtomicLong puts = new AtomicLong();

    public AuthRateLimiter(Clock clock) {
        this.clock = clock;
    }

    /** 计数 +1，超过上限立即 429。 */
    public void check(String key, int limit, Duration window) {
        Bucket bucket = bucket(key, window);
        synchronized (bucket) {
            roll(bucket, window);
            bucket.count++;
            if (bucket.count > limit) {
                throw tooMany();
            }
        }
        maybePurge(window);
    }

    /** 只检查、不计数；用于"失败次数达到上限后锁定"。 */
    public void ensureBelow(String key, int limit, Duration window) {
        Bucket bucket = bucket(key, window);
        synchronized (bucket) {
            roll(bucket, window);
            if (bucket.count >= limit) {
                throw tooMany();
            }
        }
    }

    /** 记录一次失败。 */
    public void hit(String key, Duration window) {
        Bucket bucket = bucket(key, window);
        synchronized (bucket) {
            roll(bucket, window);
            bucket.count++;
        }
        maybePurge(window);
    }

    public void reset(String key) {
        buckets.remove(key);
    }

    /** 仅供测试与运维重载使用。 */
    public void clear() {
        buckets.clear();
    }

    private Bucket bucket(String key, Duration window) {
        return buckets.compute(key, (k, existing) -> {
            long now = clock.millis();
            if (existing == null) {
                return new Bucket(now);
            }
            if (now - existing.windowStart >= window.toMillis()) {
                existing.windowStart = now;
                existing.count = 0;
            }
            return existing;
        });
    }

    private void roll(Bucket bucket, Duration window) {
        long now = clock.millis();
        if (now - bucket.windowStart >= window.toMillis()) {
            bucket.windowStart = now;
            bucket.count = 0;
        }
    }

    private void maybePurge(Duration window) {
        if (puts.incrementAndGet() % 512 != 0 || buckets.size() < 10_000) {
            return;
        }
        long now = clock.millis();
        Iterator<Map.Entry<String, Bucket>> it = buckets.entrySet().iterator();
        while (it.hasNext()) {
            Bucket b = it.next().getValue();
            synchronized (b) {
                if (now - b.windowStart >= window.toMillis() * 2) {
                    it.remove();
                }
            }
        }
    }

    private ApiException tooMany() {
        return new ApiException(HttpStatus.TOO_MANY_REQUESTS, "TOO_MANY_ATTEMPTS",
                "尝试次数过多，请稍后再试");
    }
}