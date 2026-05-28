package com.tianqingyuluo.waterapproval.ai;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.time.Duration;

@Data
@Component
@ConfigurationProperties(prefix = "water-approval.ai-service")
public class AiServiceProperties {

    private String baseUrl = "http://localhost:8000";
    private String healthPath = "/health";
    private String internalToken = "";
    private Duration timeout = Duration.ofSeconds(3);
    private String mcpTransport = "streamable-http";
    private String mcpPath = "/mcp";
    private McpTools mcpTools = new McpTools();
    private Ingest ingest = new Ingest();
    private ReviewTask reviewTask = new ReviewTask();

    public String normalizedBaseUrl() {
        return trimTrailingSlash(baseUrl);
    }

    public String normalizedHealthPath() {
        return normalizePath(healthPath);
    }

    public String normalizedMcpPath() {
        return normalizePath(mcpPath);
    }

    public String healthUrl() {
        return normalizedBaseUrl() + normalizedHealthPath();
    }

    public String mcpUrl() {
        return normalizedBaseUrl() + normalizedMcpPath();
    }

    public String normalizedReviewTaskPath() {
        return normalizePath(reviewTask.getPath());
    }

    public String reviewTaskUrl() {
        return normalizedBaseUrl() + normalizedReviewTaskPath();
    }

    public String normalizedKnowledgeSearchPath() {
        return normalizePath(mcpTools.getKnowledgeSearchPath());
    }

    public String normalizedCheckCompletenessPath() {
        return normalizePath(mcpTools.getCheckCompletenessPath());
    }

    public boolean hasInternalToken() {
        return internalToken != null && !internalToken.isBlank();
    }

    private static String trimTrailingSlash(String value) {
        if (value == null || value.isBlank()) {
            return "";
        }
        String trimmed = value.trim();
        while (trimmed.endsWith("/")) {
            trimmed = trimmed.substring(0, trimmed.length() - 1);
        }
        return trimmed;
    }

    private static String normalizePath(String value) {
        if (value == null || value.isBlank()) {
            return "";
        }
        String trimmed = value.trim();
        return trimmed.startsWith("/") ? trimmed : "/" + trimmed;
    }

    @Data
    public static class Ingest {
        private String workdir = "../../python-services/smart-water-approval-review-system-py";
        private String sourceDir = "../../docs/参考资料";
        private int chunkSize = 512;
        private int chunkOverlap = 64;
        private boolean rebuild = false;
    }

    @Data
    public static class McpTools {
        private String knowledgeSearchPath = "/api/mcp/tools/knowledge_search";
        private String checkCompletenessPath = "/api/mcp/tools/check_completeness";
    }

    @Data
    public static class ReviewTask {
        private boolean enabled = true;
        private String path = "/api/review/tasks";
        private int maxAttempts = 3;

        public int safeMaxAttempts() {
            return Math.max(maxAttempts, 1);
        }
    }
}
