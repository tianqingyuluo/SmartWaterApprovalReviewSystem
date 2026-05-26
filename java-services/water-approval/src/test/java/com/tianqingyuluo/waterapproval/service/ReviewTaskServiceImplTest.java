package com.tianqingyuluo.waterapproval.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tianqingyuluo.waterapproval.common.BusinessException;
import com.tianqingyuluo.waterapproval.dto.PendingTaskResponse;
import com.tianqingyuluo.waterapproval.dto.ResultWriteRequest;
import com.tianqingyuluo.waterapproval.dto.ReviewerActionResponse;
import com.tianqingyuluo.waterapproval.dto.ReviewerActionSubmitRequest;
import com.tianqingyuluo.waterapproval.dto.ReviewerResultResponse;
import com.tianqingyuluo.waterapproval.dto.SubmitRequest;
import com.tianqingyuluo.waterapproval.dto.SubmitResponse;
import com.tianqingyuluo.waterapproval.dto.TaskListResponse;
import com.tianqingyuluo.waterapproval.dto.UserProfileResponse;
import com.tianqingyuluo.waterapproval.entity.MaterialSlot;
import com.tianqingyuluo.waterapproval.entity.ReviewActionLog;
import com.tianqingyuluo.waterapproval.entity.ReviewResult;
import com.tianqingyuluo.waterapproval.entity.ReviewTask;
import com.tianqingyuluo.waterapproval.mapper.ReviewActionLogMapper;
import com.tianqingyuluo.waterapproval.mapper.MaterialSlotMapper;
import com.tianqingyuluo.waterapproval.mapper.ReviewResultMapper;
import com.tianqingyuluo.waterapproval.mapper.ReviewTaskMapper;
import com.tianqingyuluo.waterapproval.storage.StorageService;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentMatchers;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.ActiveProfiles;

import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

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

    @Autowired
    private ReviewActionLogMapper reviewActionLogMapper;

    private static UserProfileResponse applicantUser(long id) {
        UserProfileResponse user = new UserProfileResponse();
        user.setUserId(id);
        user.setUsername("applicant-" + id);
        user.setDisplayName("申请人" + id);
        user.setRole("APPLICANT");
        return user;
    }

    private static UserProfileResponse reviewerUser() {
        UserProfileResponse user = new UserProfileResponse();
        user.setUserId(9001L);
        user.setUsername("reviewer");
        user.setDisplayName("审批员");
        user.setRole("REVIEWER");
        return user;
    }

    private static UserProfileResponse adminUser() {
        UserProfileResponse user = new UserProfileResponse();
        user.setUserId(9002L);
        user.setUsername("admin");
        user.setDisplayName("管理员");
        user.setRole("ADMIN");
        return user;
    }

    @Test
    void submittedMaterialsShouldBeClaimedByWorkerAndAcceptResultWriteback() {
        UserProfileResponse applicant = applicantUser(8101L);
        SubmitRequest request = new SubmitRequest();
        request.setApplicationForm(new MockMultipartFile(
                "applicationForm",
                "application.pdf",
                "application/pdf",
                "申请书内容".getBytes(StandardCharsets.UTF_8)
        ));
        request.setBusinessLicense(new MockMultipartFile(
                "businessLicense",
                "license.jpg",
                "image/jpeg",
                "营业执照内容".getBytes(StandardCharsets.UTF_8)
        ));
        request.setIdCard(new MockMultipartFile(
                "idCard",
                "id-card.png",
                "image/png",
                "身份证内容".getBytes(StandardCharsets.UTF_8)
        ));

        SubmitResponse submitResponse = reviewTaskService.submit(request, applicant);

        assertEquals("SUBMITTED", submitResponse.getStatus());
        assertNotNull(submitResponse.getTaskId());
        assertNotNull(submitResponse.getSessionId());
        assertEquals(3, submitResponse.getMaterials().size());
        assertTrue(submitResponse.getMaterials().stream().allMatch(SubmitResponse.MaterialInfo::getUploaded));

        ReviewTask created = taskMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<ReviewTask>()
                        .eq(ReviewTask::getTaskId, submitResponse.getTaskId())
        );
        assertNotNull(created);
        assertEquals(8101L, created.getOwnerUserId());

        created.setSubmittedAt(LocalDateTime.now().minusYears(1));
        taskMapper.updateById(created);

        List<PendingTaskResponse> pendingTasks = reviewTaskService.getPendingTasks();
        PendingTaskResponse claimedTask = pendingTasks.stream()
                .filter(item -> item.getTaskId().equals(submitResponse.getTaskId()))
                .findFirst()
                .orElseThrow();

        assertEquals("PROCESSING", claimedTask.getStatus());
        assertEquals(3, claimedTask.getMaterials().size());
        PendingTaskResponse.PendingMaterial applicationForm =
                findPendingMaterial(claimedTask.getMaterials(), "APPLICATION_FORM");
        assertEquals(Boolean.TRUE, applicationForm.getUploaded());
        assertEquals("application.pdf", applicationForm.getOriginalFileName());
        assertNotNull(applicationForm.getStorageKey());
        assertEquals("pdf", applicationForm.getFileExtension());

        ReviewTask processing = taskMapper.selectById(created.getId());
        assertEquals("PROCESSING", processing.getStatus());

        ResultWriteRequest result = new ResultWriteRequest();
        result.setStatus("COMPLETED");
        result.setApplicantResult(Map.of(
                "summary", "申请人可见结果已生成",
                "materialCompleteness", Map.of("missing", List.of())
        ));
        result.setReviewerResult(Map.of(
                "summary", "审批人员结构化结果已生成",
                "extractedFields", List.of(Map.of(
                        "fieldKey", "applicant.name",
                        "fieldValue", "某某科技有限公司",
                        "sourceMaterial", "APPLICATION_FORM"
                ))
        ));

        reviewTaskService.writeResult(submitResponse.getTaskId(), result);

        assertEquals(
                "申请人可见结果已生成",
                reviewTaskService.getApplicantResult(
                        submitResponse.getTaskId(),
                        submitResponse.getSessionId(),
                        applicant
                ).getSummary()
        );
        assertEquals(
                "审批人员结构化结果已生成",
                reviewTaskService.getReviewerResult(
                        submitResponse.getTaskId(),
                        null,
                        reviewerUser()
                ).getSummary()
        );
    }

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

        ReviewerResultResponse response = reviewTaskService.getReviewerResult(taskId, null, reviewerUser());
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

        ReviewerResultResponse response = reviewTaskService.getReviewerResult(taskId, null, reviewerUser());

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

        task1.setOwnerUserId(1001L);
        taskMapper.updateById(task1);
        task2.setOwnerUserId(1001L);
        taskMapper.updateById(task2);

        TaskListResponse response = reviewTaskService.getTaskList(1, 100, adminUser());

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

        reviewTaskService.getTaskList(1, 20, adminUser());

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

        TaskListResponse page1 = reviewTaskService.getTaskList(1, 2, adminUser());
        assertEquals(beforeCount + 5, page1.getTotal());
        assertTrue(page1.getItems().size() <= 2);

        TaskListResponse page2 = reviewTaskService.getTaskList(2, 2, adminUser());
        assertTrue(page2.getItems().size() <= 2);

        // Verify total count is consistent across pages
        TaskListResponse page3 = reviewTaskService.getTaskList(3, 2, adminUser());
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

        task.setOwnerUserId(1001L);
        taskMapper.updateById(task);
        TaskListResponse response = reviewTaskService.getTaskList(0, 0, applicantUser(1001L));

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

    @Test
    void applicantShouldOnlySeeOwnTaskInList() {
        String ownerTaskId = "task-owner-" + System.nanoTime();
        String otherTaskId = "task-other-" + System.nanoTime();
        ReviewTask ownerTask = newReviewTask(ownerTaskId, "session-owner", "SUBMITTED");
        ownerTask.setOwnerUserId(2001L);
        taskMapper.insert(ownerTask);

        ReviewTask otherTask = newReviewTask(otherTaskId, "session-other", "SUBMITTED");
        otherTask.setOwnerUserId(2002L);
        taskMapper.insert(otherTask);

        TaskListResponse response = reviewTaskService.getTaskList(1, 50, applicantUser(2001L));

        assertTrue(response.getItems().stream().anyMatch(item -> item.getTaskId().equals(ownerTaskId)));
        assertFalse(response.getItems().stream().anyMatch(item -> item.getTaskId().equals(otherTaskId)));
    }

    @Test
    void reviewerShouldOnlySeeCompletedLikeTasks() {
        ReviewTask submitted = newReviewTask("task-submitted-" + System.nanoTime(), "session-1", "SUBMITTED");
        submitted.setOwnerUserId(3001L);
        taskMapper.insert(submitted);

        ReviewTask completed = newReviewTask("task-completed-" + System.nanoTime(), "session-2", "COMPLETED");
        completed.setOwnerUserId(3001L);
        taskMapper.insert(completed);

        TaskListResponse response = reviewTaskService.getTaskList(1, 50, reviewerUser());

        assertFalse(response.getItems().stream().anyMatch(item -> item.getTaskId().equals(submitted.getTaskId())));
        assertTrue(response.getItems().stream().anyMatch(item -> item.getTaskId().equals(completed.getTaskId())));
    }

    @Test
    void applicantCannotReadOtherApplicantTask() {
        String taskId = "task-private-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-private", "COMPLETED");
        task.setOwnerUserId(4001L);
        taskMapper.insert(task);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> reviewTaskService.getStatus(taskId, "session-private", applicantUser(4002L)));
        assertEquals(403, ex.getCode());
    }

    @Test
    void reviewerCanReadCompletedTaskWithoutSessionId() {
        String taskId = "task-reviewer-read-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-review", "COMPLETED");
        task.setOwnerUserId(5001L);
        taskMapper.insert(task);

        ReviewerResultResponse response = reviewTaskService.getReviewerResult(taskId, null, reviewerUser());
        assertEquals(taskId, response.getTaskId());
    }

    @Test
    void reviewerCannotReadSubmittedTaskDetails() {
        String taskId = "task-reviewer-deny-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-deny", "SUBMITTED");
        task.setOwnerUserId(5002L);
        taskMapper.insert(task);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> reviewTaskService.getStatus(taskId, null, reviewerUser()));
        assertEquals(403, ex.getCode());
    }

    @Test
    void reviewerRoleCannotSubmit() {
        BusinessException ex = assertThrows(BusinessException.class,
                () -> reviewTaskService.submit(new SubmitRequest(), reviewerUser()));
        assertEquals(403, ex.getCode());
    }

    @Test
    void applicantCannotReadReviewerResult() {
        String taskId = "task-reviewer-result-private-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-private", "COMPLETED");
        task.setOwnerUserId(6001L);
        taskMapper.insert(task);

        BusinessException ex = assertThrows(BusinessException.class,
                () -> reviewTaskService.getReviewerResult(taskId, "session-private", applicantUser(6001L)));
        assertEquals(403, ex.getCode());
    }

    @Test
    void reviewerActionShouldPersistTaskSnapshotAndOperationLogAndApplicantProjection() {
        String taskId = "task-review-action-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-review-action", "COMPLETED");
        task.setOwnerUserId(7001L);
        taskMapper.insert(task);
        insertReviewerResultRow(taskId, "AI初审结论已生成");

        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("RETURN_FOR_CORRECTION");
        request.setReviewerRemark("请补充营业执照副本并重新提交");

        ReviewerActionResponse actionResponse =
                reviewTaskService.submitReviewerAction(taskId, request, reviewerUser());

        assertEquals("RETURN_FOR_CORRECTION", actionResponse.getActionCode());
        assertEquals("CORRECTION_REQUIRED", actionResponse.getHandlingStatus());
        assertEquals("退回补正", actionResponse.getHandlingStatusLabel());
        assertEquals("请补充营业执照副本并重新提交", actionResponse.getReviewerRemark());
        assertNotNull(actionResponse.getOperatedAt());

        ReviewTask updatedTask = taskMapper.selectOne(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<ReviewTask>()
                        .eq(ReviewTask::getTaskId, taskId)
        );
        assertEquals("COMPLETED", updatedTask.getStatus(), "reviewer action should not mutate processing status");
        assertEquals("CORRECTION_REQUIRED", updatedTask.getHandlingStatus());
        assertEquals("退回补正", updatedTask.getHandlingStatusLabel());
        assertEquals("RETURN_FOR_CORRECTION", updatedTask.getReviewerActionCode());
        assertEquals("请补充营业执照副本并重新提交", updatedTask.getReviewerRemark());
        assertEquals(9001L, updatedTask.getReviewerUserId());
        assertEquals("审批员", updatedTask.getReviewerDisplayName());
        assertNotNull(updatedTask.getReviewerActionAt());

        List<ReviewActionLog> logs = reviewActionLogMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<ReviewActionLog>()
                        .eq(ReviewActionLog::getTaskId, taskId)
        );
        assertEquals(1, logs.size());
        assertEquals("RETURN_FOR_CORRECTION", logs.get(0).getActionCode());
        assertEquals("CORRECTION_REQUIRED", logs.get(0).getToHandlingStatus());
        assertEquals(9001L, logs.get(0).getOperatorUserId());

        var applicantView = reviewTaskService.getApplicantResult(taskId, "session-review-action", applicantUser(7001L));
        assertEquals("CORRECTION_REQUIRED", applicantView.getHandlingStatus());
        assertEquals("退回补正", applicantView.getHandlingStatusLabel());
        assertEquals("请补充营业执照副本并重新提交", applicantView.getReviewerRemark());
        assertNotNull(applicantView.getReviewerActionAt());
    }

    @Test
    void reviewerActionShouldRejectInvalidActionCode() {
        String taskId = "task-review-action-invalid-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-review-action-invalid", "COMPLETED");
        task.setOwnerUserId(7101L);
        taskMapper.insert(task);

        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("INVALID_ACTION");

        BusinessException ex = assertThrows(BusinessException.class,
                () -> reviewTaskService.submitReviewerAction(taskId, request, reviewerUser()));
        assertEquals(400, ex.getCode());
    }

    @Test
    void reviewerActionShouldRejectDuplicateSubmission() {
        String taskId = "task-review-action-dup-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-review-action-dup", "COMPLETED");
        task.setOwnerUserId(7201L);
        task.setHandlingStatus("INITIAL_REVIEW_PASSED");
        task.setHandlingStatusLabel("通过初审");
        task.setReviewerActionCode("APPROVE_INITIAL_REVIEW");
        task.setReviewerUserId(9001L);
        task.setReviewerDisplayName("审批员");
        task.setReviewerActionAt(LocalDateTime.now().minusMinutes(1));
        taskMapper.insert(task);
        insertReviewerResultRow(taskId, "AI初审结论已生成");

        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("TRANSFER_MANUAL_REVIEW");
        request.setReviewerRemark("二次提交应被拒绝");

        BusinessException ex = assertThrows(BusinessException.class,
                () -> reviewTaskService.submitReviewerAction(taskId, request, reviewerUser()));
        assertEquals(409, ex.getCode());

        List<ReviewActionLog> logs = reviewActionLogMapper.selectList(
                new com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper<ReviewActionLog>()
                        .eq(ReviewActionLog::getTaskId, taskId)
        );
        assertEquals(0, logs.size(), "duplicate reject should not create new operation log");
    }

    @Test
    void reviewerActionShouldRejectWhenConditionalTaskUpdateFailsWithoutCreatingLog() {
        ReviewTaskMapper mockedTaskMapper = mock(ReviewTaskMapper.class);
        MaterialSlotMapper mockedMaterialSlotMapper = mock(MaterialSlotMapper.class);
        ReviewResultMapper mockedResultMapper = mock(ReviewResultMapper.class);
        ReviewActionLogMapper mockedLogMapper = mock(ReviewActionLogMapper.class);
        StorageService mockedStorageService = mock(StorageService.class);
        ReviewTaskServiceImpl service = new ReviewTaskServiceImpl(
                mockedTaskMapper,
                mockedMaterialSlotMapper,
                mockedResultMapper,
                mockedLogMapper,
                mockedStorageService,
                new ObjectMapper()
        );

        String taskId = "task-review-action-stale-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-stale-action", "COMPLETED");
        ReviewResult reviewerResult = new ReviewResult();
        reviewerResult.setTaskId(taskId);
        reviewerResult.setResultType("REVIEWER");
        reviewerResult.setContent("{\"summary\":\"AI初审结论已生成\"}");

        when(mockedTaskMapper.selectOne(ArgumentMatchers.any())).thenReturn(task);
        when(mockedResultMapper.selectOne(ArgumentMatchers.any())).thenReturn(reviewerResult);
        when(mockedTaskMapper.update(
                ArgumentMatchers.<ReviewTask>isNull(),
                ArgumentMatchers.any()
        )).thenReturn(0);

        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("APPROVE_INITIAL_REVIEW");

        BusinessException ex = assertThrows(BusinessException.class,
                () -> service.submitReviewerAction(taskId, request, reviewerUser()));
        assertEquals(409, ex.getCode());
        verify(mockedLogMapper, never()).insert(ArgumentMatchers.any(ReviewActionLog.class));
    }

    @Test
    void reviewerActionShouldRejectWhenTaskStatusNotReady() {
        String taskId = "task-review-action-status-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-review-action-status", "PROCESSING");
        task.setOwnerUserId(7301L);
        taskMapper.insert(task);

        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("APPROVE_INITIAL_REVIEW");

        BusinessException ex = assertThrows(BusinessException.class,
                () -> reviewTaskService.submitReviewerAction(taskId, request, reviewerUser()));
        assertEquals(409, ex.getCode());
    }

    @Test
    void reviewerActionShouldRejectWhenAiReviewerResultMissing() {
        String taskId = "task-review-action-no-ai-result-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-review-action-no-ai-result", "COMPLETED");
        task.setOwnerUserId(7302L);
        taskMapper.insert(task);

        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("APPROVE_INITIAL_REVIEW");

        BusinessException ex = assertThrows(BusinessException.class,
                () -> reviewTaskService.submitReviewerAction(taskId, request, reviewerUser()));
        assertEquals(409, ex.getCode());
    }

    @Test
    void reviewerActionShouldRejectApplicantRole() {
        String taskId = "task-review-action-role-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-review-action-role", "COMPLETED");
        task.setOwnerUserId(7401L);
        taskMapper.insert(task);
        insertReviewerResultRow(taskId, "AI初审结论已生成");

        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("APPROVE_INITIAL_REVIEW");

        BusinessException ex = assertThrows(BusinessException.class,
                () -> reviewTaskService.submitReviewerAction(taskId, request, applicantUser(7401L)));
        assertEquals(403, ex.getCode());
    }

    @Test
    void reviewerResultShouldExposeActionLogsAndAllowEmptyRemark() {
        String taskId = "task-review-action-log-view-" + System.nanoTime();
        ReviewTask task = newReviewTask(taskId, "session-review-action-log-view", "PARTIAL_SUCCESS");
        task.setOwnerUserId(7501L);
        taskMapper.insert(task);
        insertReviewerResultRow(taskId, "AI初审结论已生成");

        ReviewerActionSubmitRequest request = new ReviewerActionSubmitRequest();
        request.setActionCode("TRANSFER_MANUAL_REVIEW");
        request.setReviewerRemark("   ");
        reviewTaskService.submitReviewerAction(taskId, request, reviewerUser());

        ReviewerResultResponse reviewerResult = reviewTaskService.getReviewerResult(taskId, null, reviewerUser());
        assertEquals("MANUAL_REVIEW_REQUIRED", reviewerResult.getHandlingStatus());
        assertEquals("转人工复核", reviewerResult.getHandlingStatusLabel());
        assertNull(reviewerResult.getReviewerRemark());
        assertEquals("TRANSFER_MANUAL_REVIEW", reviewerResult.getReviewerActionCode());
        assertEquals(1, reviewerResult.getActionLogs().size());
        assertEquals("TRANSFER_MANUAL_REVIEW", reviewerResult.getActionLogs().get(0).getActionCode());
        assertEquals("MANUAL_REVIEW_REQUIRED", reviewerResult.getActionLogs().get(0).getToHandlingStatus());
        assertNull(reviewerResult.getActionLogs().get(0).getReviewerRemark());
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

    private void insertReviewerResultRow(String taskId, String summary) {
        ReviewResult reviewResult = new ReviewResult();
        reviewResult.setTaskId(taskId);
        reviewResult.setResultType("REVIEWER");
        reviewResult.setContent("{\"summary\":\"" + summary + "\"}");
        reviewResult.setCreatedAt(LocalDateTime.now());
        reviewResult.setUpdatedAt(LocalDateTime.now());
        resultMapper.insert(reviewResult);
    }

    private PendingTaskResponse.PendingMaterial findPendingMaterial(
            List<PendingTaskResponse.PendingMaterial> materials,
            String materialType) {
        return materials.stream()
                .filter(item -> materialType.equals(item.getMaterialType()))
                .findFirst()
                .orElseThrow();
    }
}
