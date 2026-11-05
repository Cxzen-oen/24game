package com.game24.rules;

/** 一次合并：引用两个操作数与算符。left/right 可以是原始牌位或更早步骤的 id。 */
public record OperationStep(String leftRef, String rightRef, String operator) {
}
