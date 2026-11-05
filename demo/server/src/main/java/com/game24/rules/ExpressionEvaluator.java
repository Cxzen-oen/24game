package com.game24.rules;

import org.apache.commons.numbers.fraction.Fraction;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** 校验并重算提交的三步操作树，返回精确有理数结果。 */
public final class ExpressionEvaluator {

    private ExpressionEvaluator() {
    }

    /**
     * @param numbers 题目四个原始数字
     * @param steps   恰好三步合并
     * @return 计算结果
     */
    public static Fraction evaluate(int[] numbers, List<OperationStep> steps, Level level) {
        if (steps == null || steps.size() != 3) {
            throw new IllegalArgumentException("必须恰好三步合并");
        }
        List<Operator> allowed = GameRules.operatorsFor(level);

        Map<String, Fraction> values = new HashMap<>();
        for (int i = 0; i < numbers.length; i++) {
            values.put("c" + i, Fraction.of(numbers[i]));
        }

        Set<String> usedLeaves = new HashSet<>();
        Set<String> consumed = new HashSet<>();
        Set<String> produced = new HashSet<>();
        int stepIndex = 0;
        for (OperationStep step : steps) {
            // 每个引用（原始牌或中间结果）只能被消费一次
            for (String ref : new String[]{step.leftRef(), step.rightRef()}) {
                if (!values.containsKey(ref)) {
                    throw new IllegalArgumentException("无效引用: " + ref);
                }
                if (!consumed.add(ref)) {
                    throw new IllegalArgumentException("同一张牌不可重复使用: " + ref);
                }
                if (ref.startsWith("c")) {
                    usedLeaves.add(ref);
                }
            }
            Fraction left = values.get(step.leftRef());
            Fraction right = values.get(step.rightRef());
            Operator op = Operator.fromSymbol(step.operator());
            if (!allowed.contains(op)) {
                throw new IllegalArgumentException("该难度不支持此算符: " + step.operator());
            }
            Fraction result = op.apply(left, right);
            if (result == null) {
                throw new IllegalArgumentException("不能除以 0");
            }
            String id = "s" + stepIndex++;
            values.put(id, result);
            produced.add(id);
        }

        String root = "s" + (steps.size() - 1);
        if (!produced.contains(root)) {
            throw new IllegalArgumentException("缺少最终合并结果");
        }
        for (String p : produced) {
            if (!p.equals(root) && !consumed.contains(p)) {
                throw new IllegalArgumentException("存在未被合并的中间结果: " + p);
            }
        }

        if (usedLeaves.size() != numbers.length) {
            throw new IllegalArgumentException("四个数字必须各用一次");
        }
        return values.get("s2");
    }

    private static Fraction resolve(String ref, Map<String, Fraction> values, Set<String> usedLeaves) {
        Fraction value = values.get(ref);
        if (value == null) {
            throw new IllegalArgumentException("无效引用: " + ref);
        }
        if (ref.startsWith("c")) {
            usedLeaves.add(ref);
        }
        return value;
    }
}
