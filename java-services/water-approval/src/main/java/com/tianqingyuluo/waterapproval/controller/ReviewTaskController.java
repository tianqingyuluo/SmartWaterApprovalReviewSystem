package com.tianqingyuluo.waterapproval.controller;

import com.tianqingyuluo.waterapproval.common.R;
import com.tianqingyuluo.waterapproval.dto.*;
import com.tianqingyuluo.waterapproval.service.ReviewTaskService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/task")
public class ReviewTaskController {

    @Autowired
    private ReviewTaskService reviewTaskService;

    @PostMapping("/submit")
    public R<SubmitResponse> submit(SubmitRequest request) {
        log.info("收到提交请求");
        SubmitResponse response = reviewTaskService.submit(request);
        return R.ok(response);
    }

    @GetMapping("/pending")
    public R<List<Map<String, Object>>> getPendingTasks() {
        log.info("查询待处理任务");
        List<Map<String, Object>> tasks = reviewTaskService.getPendingTasks();
        return R.ok(tasks);
    }

    @GetMapping("/{taskId}/status")
    public R<TaskStatusResponse> getStatus(@PathVariable String taskId) {
        log.info("查询任务状态: taskId={}", taskId);
        TaskStatusResponse response = reviewTaskService.getStatus(taskId);
        return R.ok(response);
    }

    @PutMapping("/{taskId}/status")
    public R<Void> updateStatus(@PathVariable String taskId, @RequestBody StatusUpdateRequest request) {
        log.info("更新任务状态: taskId={}, status={}", taskId, request.getStatus());
        reviewTaskService.updateStatus(taskId, request.getStatus());
        return R.ok();
    }

    @PutMapping("/{taskId}/result")
    public R<Void> writeResult(@PathVariable String taskId, @RequestBody ResultWriteRequest request) {
        log.info("回写审核结果: taskId={}, status={}", taskId, request.getStatus());
        reviewTaskService.writeResult(taskId, request);
        return R.ok();
    }

    @GetMapping("/{taskId}/result/applicant")
    public R<ApplicantResultResponse> getApplicantResult(@PathVariable String taskId) {
        log.info("查询申请人结果: taskId={}", taskId);
        ApplicantResultResponse response = reviewTaskService.getApplicantResult(taskId);
        return R.ok(response);
    }

    @GetMapping("/{taskId}/result/reviewer")
    public R<ReviewerResultResponse> getReviewerResult(@PathVariable String taskId) {
        log.info("查询审批人员结果: taskId={}", taskId);
        ReviewerResultResponse response = reviewTaskService.getReviewerResult(taskId);
        return R.ok(response);
    }
}
