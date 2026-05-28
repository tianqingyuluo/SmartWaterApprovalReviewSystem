package com.tianqingyuluo.waterapproval.controller;

import com.tianqingyuluo.waterapproval.common.R;
import com.tianqingyuluo.waterapproval.dto.AiHealthResponse;
import com.tianqingyuluo.waterapproval.dto.AiIngestOperationResponse;
import com.tianqingyuluo.waterapproval.dto.AiMcpCompletenessRequest;
import com.tianqingyuluo.waterapproval.dto.AiMcpCompletenessResponse;
import com.tianqingyuluo.waterapproval.dto.AiMcpKnowledgeSearchRequest;
import com.tianqingyuluo.waterapproval.dto.AiMcpKnowledgeSearchResponse;
import com.tianqingyuluo.waterapproval.service.AiOpsService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/ai")
@RequiredArgsConstructor
public class AiOpsController {

    private final AiOpsService aiOpsService;

    @GetMapping("/health")
    public R<AiHealthResponse> getHealth() {
        log.info("查询 AI 服务健康状态");
        return R.ok(aiOpsService.getHealth());
    }

    @PostMapping("/ingest")
    public R<AiIngestOperationResponse> getIngestOperation() {
        log.info("查询知识库 ingest 运维触发命令");
        return R.ok(aiOpsService.getIngestOperation());
    }

    @PostMapping("/mcp/knowledge-search")
    public R<AiMcpKnowledgeSearchResponse> callKnowledgeSearch(
            @Valid @RequestBody AiMcpKnowledgeSearchRequest request) {
        log.info("调用 MCP knowledge_search: topK={}", request.getTopK());
        return R.ok(aiOpsService.callKnowledgeSearch(request));
    }

    @PostMapping("/mcp/check-completeness")
    public R<AiMcpCompletenessResponse> callCheckCompleteness(
            @RequestBody AiMcpCompletenessRequest request) {
        log.info("调用 MCP check_completeness: materials={}",
                request.getMaterials() == null ? 0 : request.getMaterials().size());
        return R.ok(aiOpsService.callCheckCompleteness(request));
    }
}
