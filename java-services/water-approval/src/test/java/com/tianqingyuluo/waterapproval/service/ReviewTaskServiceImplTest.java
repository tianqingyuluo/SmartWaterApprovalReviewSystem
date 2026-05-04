package com.tianqingyuluo.waterapproval.service;

import com.tianqingyuluo.waterapproval.dto.ResultWriteRequest;
import com.tianqingyuluo.waterapproval.entity.ReviewTask;
import com.tianqingyuluo.waterapproval.mapper.ReviewTaskMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.assertEquals;

@SpringBootTest
@ActiveProfiles("test")
class ReviewTaskServiceImplTest {

    @Autowired
    private ReviewTaskService reviewTaskService;

    @Autowired
    private ReviewTaskMapper taskMapper;

    @Test
    void writeResultShouldPersistKnowledgePackVersion() {
        ReviewTask task = new ReviewTask();
        task.setTaskId("task-kp-version");
        task.setSessionId("session-kp-version");
        task.setStatus("PROCESSING");
        task.setSubmittedAt(LocalDateTime.now());
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.insert(task);

        ResultWriteRequest request = new ResultWriteRequest();
        request.setStatus("COMPLETED");
        request.setKnowledgePackVersion("water-permit-mvp-2026-04-27");

        reviewTaskService.writeResult("task-kp-version", request);

        ReviewTask updated = taskMapper.selectById(task.getId());
        assertEquals("COMPLETED", updated.getStatus());
        assertEquals("water-permit-mvp-2026-04-27", updated.getKnowledgePackVersion());
    }
}
