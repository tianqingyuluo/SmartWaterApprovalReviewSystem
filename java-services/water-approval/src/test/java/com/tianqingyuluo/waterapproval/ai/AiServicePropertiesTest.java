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

        assertEquals("http://localhost:8000", properties.normalizedBaseUrl());
        assertEquals("/health", properties.normalizedHealthPath());
        assertEquals("http://localhost:8000/health", properties.healthUrl());
        assertEquals("http://localhost:8000/mcp", properties.mcpUrl());
    }

    @Test
    void shouldDetectConfiguredInternalToken() {
        AiServiceProperties properties = new AiServiceProperties();

        assertFalse(properties.hasInternalToken());

        properties.setInternalToken(" token ");

        assertTrue(properties.hasInternalToken());
    }
}
