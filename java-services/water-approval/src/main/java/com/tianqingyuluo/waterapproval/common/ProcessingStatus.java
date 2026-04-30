package com.tianqingyuluo.waterapproval.common;

import java.util.Arrays;
import java.util.Map;
import java.util.Set;

public enum ProcessingStatus {
    SUBMITTED,
    QUEUED,
    PROCESSING,
    PARTIAL_SUCCESS,
    COMPLETED,
    FAILED;

    private static final Set<ProcessingStatus> TERMINAL_STATES = Set.of(
            PARTIAL_SUCCESS, COMPLETED, FAILED
    );

    private static final Map<ProcessingStatus, Set<ProcessingStatus>> ALLOWED_TRANSITIONS = Map.of(
            SUBMITTED, Set.of(QUEUED, PROCESSING, FAILED),
            QUEUED, Set.of(PROCESSING, FAILED),
            PROCESSING, Set.of(COMPLETED, PARTIAL_SUCCESS, FAILED)
    );

    public static boolean isValid(String status) {
        return Arrays.stream(values()).anyMatch(s -> s.name().equals(status));
    }

    public static boolean isTerminal(String status) {
        return TERMINAL_STATES.stream().anyMatch(s -> s.name().equals(status));
    }

    public static void validateTransition(String currentStatus, String newStatus) {
        if (!isValid(newStatus)) {
            throw new IllegalArgumentException("无效的任务状态: " + newStatus);
        }
        if (currentStatus.equals(newStatus)) {
            return;
        }
        ProcessingStatus current = valueOf(currentStatus);
        ProcessingStatus target = valueOf(newStatus);

        Set<ProcessingStatus> allowed = ALLOWED_TRANSITIONS.get(current);
        if (allowed == null || !allowed.contains(target)) {
            throw new IllegalArgumentException(
                    "不允许的状态流转: " + currentStatus + " -> " + newStatus
            );
        }
    }
}
