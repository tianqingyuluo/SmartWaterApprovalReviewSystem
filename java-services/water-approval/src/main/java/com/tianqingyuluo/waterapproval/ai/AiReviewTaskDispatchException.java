package com.tianqingyuluo.waterapproval.ai;

import lombok.Getter;

@Getter
public class AiReviewTaskDispatchException extends RuntimeException {
    private final String failureCategory;
    private final boolean retryable;
    private final Integer statusCode;

    public AiReviewTaskDispatchException(
            String message,
            String failureCategory,
            boolean retryable,
            Integer statusCode,
            Throwable cause) {
        super(message, cause);
        this.failureCategory = failureCategory;
        this.retryable = retryable;
        this.statusCode = statusCode;
    }
}
