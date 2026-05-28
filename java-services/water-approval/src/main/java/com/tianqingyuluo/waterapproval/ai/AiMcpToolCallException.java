package com.tianqingyuluo.waterapproval.ai;

import lombok.Getter;

@Getter
public class AiMcpToolCallException extends RuntimeException {
    private final Integer statusCode;

    public AiMcpToolCallException(String message, Integer statusCode, Throwable cause) {
        super(message, cause);
        this.statusCode = statusCode;
    }
}
