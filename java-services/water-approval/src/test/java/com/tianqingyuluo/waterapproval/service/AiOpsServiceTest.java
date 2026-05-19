package com.tianqingyuluo.waterapproval.service;

import com.tianqingyuluo.waterapproval.ai.AiServiceClient;
import com.tianqingyuluo.waterapproval.ai.AiServiceProperties;
import com.tianqingyuluo.waterapproval.dto.AiIngestOperationResponse;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;

class AiOpsServiceTest {

    @Test
    void shouldBuildIngestOpsCommandFromConfiguration() {
        AiServiceProperties properties = new AiServiceProperties();
        properties.getIngest().setWorkdir("../python-services/smart-water-approval-review-system-py");
        properties.getIngest().setSourceDir("docs/参考资料");
        properties.getIngest().setChunkSize(768);
        properties.getIngest().setChunkOverlap(96);
        properties.getIngest().setRebuild(true);

        AiOpsService service = new AiOpsService(mock(AiServiceClient.class), properties);

        AiIngestOperationResponse response = service.getIngestOperation();

        assertEquals("ops-command", response.getMode());
        assertEquals("../python-services/smart-water-approval-review-system-py", response.getWorkdir());
        assertEquals("docs/参考资料", response.getSourceDir());
        assertTrue(response.isRebuild());
        assertTrue(response.getCommand().contains("--rebuild"));
        assertEquals("768", response.getCommand().get(response.getCommand().indexOf("--chunk-size") + 1));
        assertEquals("96", response.getCommand().get(response.getCommand().indexOf("--chunk-overlap") + 1));
    }

    @Test
    void shouldOmitRebuildFlagWhenDisabled() {
        AiServiceProperties properties = new AiServiceProperties();
        properties.getIngest().setRebuild(false);

        AiOpsService service = new AiOpsService(mock(AiServiceClient.class), properties);

        AiIngestOperationResponse response = service.getIngestOperation();

        assertFalse(response.getCommand().contains("--rebuild"));
    }
}
