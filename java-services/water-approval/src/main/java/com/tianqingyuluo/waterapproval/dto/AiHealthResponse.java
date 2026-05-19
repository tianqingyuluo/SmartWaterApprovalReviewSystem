package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AiHealthResponse {
    private String baseUrl;
    private String healthUrl;
    private boolean reachable;
    private Integer statusCode;
    private String message;
    private String responseBody;
    private String mcpTransport;
    private String mcpUrl;
    private boolean internalTokenConfigured;
    private LocalDateTime checkedAt;
}
