package com.tianqingyuluo.waterapproval.controller;

import com.tianqingyuluo.waterapproval.common.R;
import com.tianqingyuluo.waterapproval.dto.AiHealthResponse;
import com.tianqingyuluo.waterapproval.dto.AiIngestOperationResponse;
import com.tianqingyuluo.waterapproval.service.AiOpsService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
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
}
