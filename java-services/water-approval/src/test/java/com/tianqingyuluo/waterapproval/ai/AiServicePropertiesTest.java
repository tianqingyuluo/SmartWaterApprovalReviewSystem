package com.tianqingyuluo.waterapproval.ai;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AiServicePropertiesTest {

    @Test
    void shouldNormalizeBaseUrlAndPaths() {
        AiServiceProperties properties = new AiServiceProperties();
        properties.setBaseUrl("http://localhost:8000/");
        properties.setHealthPath("health");
        properties.setMcpPath("mcp");
        properties.getReviewTask().setPath("api/review/tasks");

        assertEquals("http://localhost:8000", properties.normalizedBaseUrl());
        assertEquals("/health", properties.normalizedHealthPath());
        assertEquals("http://localhost:8000/health", properties.healthUrl());
        assertEquals("http://localhost:8000/mcp", properties.mcpUrl());
        assertEquals("/api/review/tasks", properties.normalizedReviewTaskPath());
        assertEquals("http://localhost:8000/api/review/tasks", properties.reviewTaskUrl());
        assertEquals(3, properties.getReviewTask().safeMaxAttempts());
    }

    @Test
    void shouldDetectConfiguredInternalToken() {
        AiServiceProperties properties = new AiServiceProperties();

        assertFalse(properties.hasInternalToken());

        properties.setInternalToken(" token ");

        assertTrue(properties.hasInternalToken());
    }

    @Test
    void shouldClampReviewTaskAttempts() {
        AiServiceProperties properties = new AiServiceProperties();
        properties.getReviewTask().setMaxAttempts(0);

        assertEquals(1, properties.getReviewTask().safeMaxAttempts());
    }
}
