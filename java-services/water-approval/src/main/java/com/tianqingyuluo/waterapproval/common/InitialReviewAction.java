package com.tianqingyuluo.waterapproval.common;

import java.util.Arrays;

public enum InitialReviewAction {
    APPROVE_INITIAL_REVIEW("INITIAL_REVIEW_PASSED", "通过初审"),
    RETURN_FOR_CORRECTION("CORRECTION_REQUIRED", "退回补正"),
    TRANSFER_MANUAL_REVIEW("MANUAL_REVIEW_REQUIRED", "转人工复核");

    private final String handlingStatus;
    private final String handlingStatusLabel;

    InitialReviewAction(String handlingStatus, String handlingStatusLabel) {
        this.handlingStatus = handlingStatus;
        this.handlingStatusLabel = handlingStatusLabel;
    }

    public String handlingStatus() {
        return handlingStatus;
    }

    public String handlingStatusLabel() {
        return handlingStatusLabel;
    }

    public static InitialReviewAction fromCode(String code) {
        if (code == null) {
            return null;
        }
        return Arrays.stream(values())
                .filter(action -> action.name().equals(code))
                .findFirst()
                .orElse(null);
    }
}
