package com.tianqingyuluo.waterapproval.service;

import com.tianqingyuluo.waterapproval.ai.AiMcpToolCallException;
import com.tianqingyuluo.waterapproval.ai.AiServiceClient;
import com.tianqingyuluo.waterapproval.ai.AiServiceProperties;
import com.tianqingyuluo.waterapproval.common.BusinessException;
import com.tianqingyuluo.waterapproval.dto.AiHealthResponse;
import com.tianqingyuluo.waterapproval.dto.AiIngestOperationResponse;
import com.tianqingyuluo.waterapproval.dto.AiMcpCompletenessRequest;
import com.tianqingyuluo.waterapproval.dto.AiMcpCompletenessResponse;
import com.tianqingyuluo.waterapproval.dto.AiMcpKnowledgeSearchRequest;
import com.tianqingyuluo.waterapproval.dto.AiMcpKnowledgeSearchResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class AiOpsService {

    private final AiServiceClient aiServiceClient;
    private final AiServiceProperties properties;

    public AiHealthResponse getHealth() {
        return aiServiceClient.checkHealth();
    }

    public AiIngestOperationResponse getIngestOperation() {
        AiServiceProperties.Ingest ingest = properties.getIngest();

        List<String> command = new ArrayList<>();
        command.add("uv");
        command.add("run");
        command.add("python");
        command.add("-m");
        command.add("src.ingest.cli");
        command.add("--source-dir");
        command.add(ingest.getSourceDir());
        command.add("--chunk-size");
        command.add(String.valueOf(ingest.getChunkSize()));
        command.add("--chunk-overlap");
        command.add(String.valueOf(ingest.getChunkOverlap()));
        if (ingest.isRebuild()) {
            command.add("--rebuild");
        }

        AiIngestOperationResponse response = new AiIngestOperationResponse();
        response.setMode("ops-command");
        response.setWorkdir(ingest.getWorkdir());
        response.setSourceDir(ingest.getSourceDir());
        response.setChunkSize(ingest.getChunkSize());
        response.setChunkOverlap(ingest.getChunkOverlap());
        response.setRebuild(ingest.isRebuild());
        response.setCommand(command);
        response.setVerificationCommand("uv run python -m src.mcp_server.demo --run-samples");
        response.setNote("Python 当前提供 ingest CLI 和 MCP 原生 transport；Java 侧输出可复现运维命令，不伪造 REST ingest。");
        return response;
    }

    public AiMcpKnowledgeSearchResponse callKnowledgeSearch(AiMcpKnowledgeSearchRequest request) {
        try {
            return aiServiceClient.callKnowledgeSearch(request);
        } catch (AiMcpToolCallException e) {
            throw new BusinessException(502, e.getMessage());
        }
    }

    public AiMcpCompletenessResponse callCheckCompleteness(AiMcpCompletenessRequest request) {
        try {
            return aiServiceClient.callCheckCompleteness(request);
        } catch (AiMcpToolCallException e) {
            throw new BusinessException(502, e.getMessage());
        }
    }
}
