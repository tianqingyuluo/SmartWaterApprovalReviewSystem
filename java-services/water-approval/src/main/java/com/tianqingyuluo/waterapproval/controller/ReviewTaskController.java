package com.tianqingyuluo.waterapproval.controller;

import com.tianqingyuluo.waterapproval.common.R;
import com.tianqingyuluo.waterapproval.dto.*;
import com.tianqingyuluo.waterapproval.service.AuthService;
import com.tianqingyuluo.waterapproval.service.ReviewTaskService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.CacheControl;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.TimeUnit;

@Slf4j
@RestController
@RequestMapping("/task")
@RequiredArgsConstructor
public class ReviewTaskController {

    private final ReviewTaskService reviewTaskService;
    private final AuthService authService;

    @PostMapping("/submit")
    public R<SubmitResponse> submit(SubmitRequest request) {
        log.info("收到提交请求");
        SubmitResponse response = reviewTaskService.submit(request, authService.currentUser());
        return R.ok(response);
    }

    @GetMapping("/pending")
    @WorkerApi
    public R<List<PendingTaskResponse>> getPendingTasks() {
        log.info("查询待处理任务");
        List<PendingTaskResponse> tasks = reviewTaskService.getPendingTasks();
        return R.ok(tasks);
    }

    @GetMapping("/list")
    public R<TaskListResponse> getTaskList(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        page = Math.max(page, 1);
        size = Math.min(Math.max(size, 1), 100);
        log.info("查询任务列表: page={}, size={}", page, size);
        TaskListResponse response = reviewTaskService.getTaskList(page, size, authService.currentUser());
        return R.ok(response);
    }

    @GetMapping("/{taskId}/status")
    public R<TaskStatusResponse> getStatus(
            @PathVariable String taskId,
            @RequestParam(required = false) String sessionId) {
        log.info("查询任务状态: taskId={}", taskId);
        TaskStatusResponse response = reviewTaskService.getStatus(taskId, sessionId, authService.currentUser());
        return R.ok(response);
    }

    @GetMapping("/{taskId}/material/{materialType}/preview")
    public ResponseEntity<InputStreamResource> previewMaterial(
            @PathVariable String taskId,
            @PathVariable String materialType,
            @RequestParam(required = false) String sessionId) {
        MaterialPreviewResource resource =
                reviewTaskService.previewMaterial(taskId, materialType, sessionId, authService.currentUser());

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(resource.getContentType()))
                .cacheControl(CacheControl.maxAge(5, TimeUnit.MINUTES).cachePrivate().mustRevalidate())
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        org.springframework.http.ContentDisposition.inline()
                                .filename(resource.getOriginalFileName(), StandardCharsets.UTF_8)
                                .build()
                                .toString())
                .header("X-Content-Type-Options", "nosniff")
                .header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'self'; sandbox")
                .body(new InputStreamResource(resource.getInputStream()));
    }

    @PutMapping("/{taskId}/status")
    @WorkerApi
    public R<Void> updateStatus(@PathVariable String taskId, @RequestBody StatusUpdateRequest request) {
        log.info("更新任务状态: taskId={}, status={}", taskId, request.getStatus());
        reviewTaskService.updateStatus(taskId, request.getStatus());
        return R.ok();
    }

    @PutMapping("/{taskId}/result")
    @WorkerApi
    public R<Void> writeResult(@PathVariable String taskId, @RequestBody ResultWriteRequest request) {
        log.info("回写审核结果: taskId={}, status={}", taskId, request.getStatus());
        reviewTaskService.writeResult(taskId, request);
        return R.ok();
    }

    @GetMapping("/{taskId}/result/applicant")
    public R<ApplicantResultResponse> getApplicantResult(
            @PathVariable String taskId,
            @RequestParam(required = false) String sessionId) {
        log.info("查询申请人结果: taskId={}", taskId);
        ApplicantResultResponse response = reviewTaskService.getApplicantResult(taskId, sessionId, authService.currentUser());
        return R.ok(response);
    }

    @GetMapping("/{taskId}/result/reviewer")
    public R<ReviewerResultResponse> getReviewerResult(
            @PathVariable String taskId,
            @RequestParam(required = false) String sessionId) {
        log.info("查询审批人员结果: taskId={}", taskId);
        ReviewerResultResponse response = reviewTaskService.getReviewerResult(taskId, sessionId, authService.currentUser());
        return R.ok(response);
    }

    @PostMapping("/{taskId}/reviewer-action")
    public R<ReviewerActionResponse> submitReviewerAction(
            @PathVariable String taskId,
            @Validated @RequestBody ReviewerActionSubmitRequest request) {
        log.info("提交审核动作: taskId={}, actionCode={}", taskId, request.getActionCode());
        ReviewerActionResponse response =
                reviewTaskService.submitReviewerAction(taskId, request, authService.currentUser());
        return R.ok(response);
    }
}
