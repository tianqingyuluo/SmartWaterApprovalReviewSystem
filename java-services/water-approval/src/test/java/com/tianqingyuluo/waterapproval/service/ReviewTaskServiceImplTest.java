package com.tianqingyuluo.waterapproval.service;

import com.tianqingyuluo.waterapproval.dto.ResultWriteRequest;
import com.tianqingyuluo.waterapproval.dto.ReviewerResultResponse;
import com.tianqingyuluo.waterapproval.dto.TaskListResponse;
import com.tianqingyuluo.waterapproval.entity.MaterialSlot;
import com.tianqingyuluo.waterapproval.entity.ReviewResult;
import com.tianqingyuluo.waterapproval.entity.ReviewTask;
import com.tianqingyuluo.waterapproval.mapper.MaterialSlotMapper;
import com.tianqingyuluo.waterapproval.mapper.ReviewResultMapper;
import com.tianqingyuluo.waterapproval.mapper.ReviewTaskMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
@ActiveProfiles("test")
class ReviewTaskServiceImplTest {

    @Autowired
    private ReviewTaskService reviewTaskService;

    @Autowired
    private ReviewTaskMapper taskMapper;

    @Autowired
    private MaterialSlotMapper materialSlotMapper;

    @Autowired
    private ReviewResultMapper resultMapper;

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

    @Test
    void repeatedWriteResultShouldUpdateExistingRowsWithoutDuplicatingResults() {
        String taskId = "task-idempotent-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-idempotent", "PROCESSING");
        taskMapper.insert(task);

        ResultWriteRequest first = new ResultWriteRequest();
        first.setStatus("COMPLETED");
        first.setApplicantResult(Map.of("summary", "首次申请人结果"));
        first.setReviewerResult(Map.of("summary", "首次审批结果"));

        ResultWriteRequest second = new ResultWriteRequest();
        second.setStatus("COMPLETED");
        second.setApplicantResult(Map.of("summary", "重复回调后的申请人结果"));
        second.setReviewerResult(Map.of("summary", "重复回调后的审批结果"));

        reviewTaskService.writeResult(taskId, first);
        reviewTaskService.writeResult(taskId, second);

        List<ReviewResult> rows = resultMapper.selectList(null).stream()
                .filter(row -> row.getTaskId().equals(taskId))
                .toList();
        assertEquals(2, rows.size(), "applicant/reviewer results should be upserted, not duplicated");

        ReviewerResultResponse response = reviewTaskService.getReviewerResult(taskId, "session-idempotent");
        assertEquals("COMPLETED", response.getStatus());
        assertEquals("重复回调后的审批结果", response.getSummary());
    }

    @Test
    void getReviewerResultShouldExposeExtractedFieldSnapshotFromCallback() {
        String taskId = "task-fields-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-fields", "PROCESSING");
        taskMapper.insert(task);

        ResultWriteRequest request = new ResultWriteRequest();
        request.setStatus("COMPLETED");
        request.setReviewerResult(Map.of(
                "summary", "字段快照已生成",
                "extractedFields", List.of(Map.of(
                        "fieldKey", "applicant.name",
                        "fieldValue", "某某科技有限公司",
                        "confidence", 0.93,
                        "sourceMaterial", "APPLICATION_FORM"
                ))
        ));

        reviewTaskService.writeResult(taskId, request);

        ReviewerResultResponse response = reviewTaskService.getReviewerResult(taskId, "session-fields");

        assertEquals("字段快照已生成", response.getSummary());
        assertNotNull(response.getExtractedFields());
        List<Map<String, Object>> fields = (List<Map<String, Object>>) response.getExtractedFields();
        assertEquals("applicant.name", fields.get(0).get("fieldKey"));
        assertEquals("某某科技有限公司", fields.get(0).get("fieldValue"));
    }

    @Test
    void getTaskListShouldReturnTasksInDescOrder() {
        ReviewTask task1 = new ReviewTask();
        task1.setTaskId("task-list-1-" + System.currentTimeMillis());
        task1.setSessionId("session-list-1");
        task1.setStatus("SUBMITTED");
        task1.setSubmittedAt(LocalDateTime.now().minusDays(2));
        task1.setCreatedAt(LocalDateTime.now().minusDays(2));
        task1.setUpdatedAt(LocalDateTime.now().minusDays(2));
        taskMapper.insert(task1);

        ReviewTask task2 = new ReviewTask();
        task2.setTaskId("task-list-2-" + System.currentTimeMillis());
        task2.setSessionId("session-list-2");
        task2.setStatus("COMPLETED");
        task2.setSubmittedAt(LocalDateTime.now().minusDays(1));
        task2.setCreatedAt(LocalDateTime.now().minusDays(1));
        task2.setUpdatedAt(LocalDateTime.now().minusDays(1));
        taskMapper.insert(task2);

        TaskListResponse response = reviewTaskService.getTaskList(1, 20);

        assertNotNull(response);
        assertTrue(response.getTotal() >= 2);
        assertTrue(response.getItems().size() >= 2);

        int idx1 = -1, idx2 = -1;
        for (int i = 0; i < response.getItems().size(); i++) {
            if (response.getItems().get(i).getTaskId().equals(task2.getTaskId())) idx2 = i;
            if (response.getItems().get(i).getTaskId().equals(task1.getTaskId())) idx1 = i;
        }
        assertTrue(idx2 >= 0, "task2 should be in results");
        assertTrue(idx1 >= 0, "task1 should be in results");
        assertTrue(idx2 < idx1, "newer task should appear before older task");
    }

    @Test
    void getTaskListShouldNotChangeTaskStatus() {
        ReviewTask task = new ReviewTask();
        task.setTaskId("task-list-status");
        task.setSessionId("session-list-status");
        task.setStatus("QUEUED");
        task.setSubmittedAt(LocalDateTime.now());
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.insert(task);

        reviewTaskService.getTaskList(1, 20);

        ReviewTask after = taskMapper.selectById(task.getId());
        assertEquals("QUEUED", after.getStatus());
    }

    @Test
    void getTaskListShouldRespectPagination() {
        long beforeCount = taskMapper.selectCount(null);

        for (int i = 0; i < 5; i++) {
            ReviewTask task = new ReviewTask();
            task.setTaskId("task-page-" + i + "-" + System.currentTimeMillis());
            task.setSessionId("session-page-" + i);
            task.setStatus("SUBMITTED");
            task.setSubmittedAt(LocalDateTime.now().minusMinutes(i));
            task.setCreatedAt(LocalDateTime.now().minusMinutes(i));
            task.setUpdatedAt(LocalDateTime.now().minusMinutes(i));
            taskMapper.insert(task);
        }

        TaskListResponse page1 = reviewTaskService.getTaskList(1, 2);
        assertEquals(beforeCount + 5, page1.getTotal());
        assertTrue(page1.getItems().size() <= 2);

        TaskListResponse page2 = reviewTaskService.getTaskList(2, 2);
        assertTrue(page2.getItems().size() <= 2);

        // Verify total count is consistent across pages
        TaskListResponse page3 = reviewTaskService.getTaskList(3, 2);
        assertEquals(page1.getTotal(), page3.getTotal());
    }

    @Test
    void getTaskListShouldNormalizePageAndSizeAndReturnFixedMaterialSlots() {
        ReviewTask task = new ReviewTask();
        task.setTaskId("task-list-materials-" + System.currentTimeMillis());
        task.setSessionId("session-list-materials");
        task.setStatus("SUBMITTED");
        task.setSubmittedAt(LocalDateTime.now());
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.insert(task);

        MaterialSlot applicationForm = new MaterialSlot();
        applicationForm.setMaterialId("mat-list-application-" + System.currentTimeMillis());
        applicationForm.setTaskId(task.getTaskId());
        applicationForm.setMaterialType("APPLICATION_FORM");
        applicationForm.setOriginalFileName("application.pdf");
        applicationForm.setCreatedAt(LocalDateTime.now());
        applicationForm.setUpdatedAt(LocalDateTime.now());
        materialSlotMapper.insert(applicationForm);

        TaskListResponse response = reviewTaskService.getTaskList(0, 0);

        TaskListResponse.TaskListItem item = response.getItems().stream()
                .filter(candidate -> candidate.getTaskId().equals(task.getTaskId()))
                .findFirst()
                .orElseThrow();

        assertEquals(1, response.getPage());
        assertEquals(1, response.getSize());
        assertEquals(3, item.getMaterials().size());
        assertEquals("APPLICATION_FORM", item.getMaterials().get(0).getMaterialType());
        assertEquals("application.pdf", item.getMaterials().get(0).getOriginalFileName());
        assertEquals(Boolean.TRUE, item.getMaterials().get(0).getUploaded());
        assertEquals("BUSINESS_LICENSE", item.getMaterials().get(1).getMaterialType());
        assertEquals(Boolean.FALSE, item.getMaterials().get(1).getUploaded());
        assertEquals("ID_CARD", item.getMaterials().get(2).getMaterialType());
        assertEquals(Boolean.FALSE, item.getMaterials().get(2).getUploaded());
    }

    private ReviewTask newReviewTask(String taskId, String sessionId, String status) {
        ReviewTask task = new ReviewTask();
        task.setTaskId(taskId);
        task.setSessionId(sessionId);
        task.setStatus(status);
        task.setSubmittedAt(LocalDateTime.now());
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        return task;
    }
}
