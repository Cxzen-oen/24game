package com.game24.game;

import java.util.List;
import java.util.Map;

public record RecordsView(List<Map<String, Object>> history, List<Map<String, Object>> bests) {
}
