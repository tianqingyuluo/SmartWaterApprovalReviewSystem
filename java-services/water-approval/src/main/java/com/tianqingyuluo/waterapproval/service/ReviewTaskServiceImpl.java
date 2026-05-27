package com.tianqingyuluo.waterapproval.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.tianqingyuluo.waterapproval.ai.AiReviewTaskDispatchException;
import com.tianqingyuluo.waterapproval.ai.AiServiceClient;
import com.tianqingyuluo.waterapproval.common.BusinessException;
import com.tianqingyuluo.waterapproval.common.InitialReviewAction;
import com.tianqingyuluo.waterapproval.common.ProcessingStatus;
import com.tianqingyuluo.waterapproval.common.RoleConstants;
import com.tianqingyuluo.waterapproval.dto.*;
import com.tianqingyuluo.waterapproval.entity.MaterialSlot;
import com.tianqingyuluo.waterapproval.entity.ReviewActionLog;
import com.tianqingyuluo.waterapproval.entity.ReviewResult;
import com.tianqingyuluo.waterapproval.entity.ReviewTask;
import com.tianqingyuluo.waterapproval.mapper.ReviewActionLogMapper;
import com.tianqingyuluo.waterapproval.mapper.MaterialSlotMapper;
import com.tianqingyuluo.waterapproval.mapper.ReviewResultMapper;
import com.tianqingyuluo.waterapproval.mapper.ReviewTaskMapper;
import com.tianqingyuluo.waterapproval.storage.StorageService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.time.LocalDateTime;
import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReviewTaskServiceImpl implements ReviewTaskService {

    private final ReviewTaskMapper taskMapper;
    private final MaterialSlotMapper materialSlotMapper;
    private final ReviewResultMapper resultMapper;
    private final ReviewActionLogMapper reviewActionLogMapper;
    private final StorageService storageService;
    private final ObjectMapper objectMapper;
    private final AiServiceClient aiServiceClient;

    private static final List<String> ACCEPTED_FILE_TYPES = Arrays.asList("jpg", "jpeg", "png", "pdf", "docx");
    private static final List<String> MATERIAL_TYPES = Arrays.asList("APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD");
    private static final Set<String> REVIEWER_VISIBLE_STATUSES = Set.of("PARTIAL_SUCCESS", "COMPLETED", "FAILED");
    private static final Set<String> REVIEWER_ACTION_ALLOWED_TASK_STATUSES = Set.of("PARTIAL_SUCCESS", "COMPLETED");
    private static final Map<String, String> PREVIEW_CONTENT_TYPES = Map.of(
            "pdf", "application/pdf",
            "jpg", "image/jpeg",
            "jpeg", "image/jpeg",
            "png", "image/png"
    );

    @Override
    @Transactional
    public SubmitResponse submit(SubmitRequest request, UserProfileResponse currentUser) {
        if (!canSubmit(currentUser)) {
            throw new BusinessException(403, "当前角色不允许提交申请");
        }

        String taskId = generateTaskId();
        String sessionId = generateSessionId();

        ReviewTask task = new ReviewTask();
        task.setTaskId(taskId);
        task.setSessionId(sessionId);
        task.setOwnerUserId(currentUser.getUserId());
        task.setStatus("SUBMITTED");
        task.setSubmittedAt(LocalDateTime.now());
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.insert(task);

        List<SubmitResponse.MaterialInfo> materialInfos = new ArrayList<>();

        materialInfos.add(processMaterial(taskId, "APPLICATION_FORM", request.getApplicationForm()));
        materialInfos.add(processMaterial(taskId, "BUSINESS_LICENSE", request.getBusinessLicense()));
        materialInfos.add(processMaterial(taskId, "ID_CARD", request.getIdCard()));

        String submissionStatus = dispatchSubmittedTask(task);

        SubmitResponse response = new SubmitResponse();
        response.setTaskId(taskId);
        response.setSessionId(sessionId);
        response.setStatus(submissionStatus);
        response.setSubmittedAt(task.getSubmittedAt());
        response.setMaterials(materialInfos);

        log.info("Task submitted: taskId={}, ownerUserId={}", taskId, currentUser.getUserId());
        return response;
    }

    private String dispatchSubmittedTask(ReviewTask task) {
        if (!aiServiceClient.isReviewTaskDispatchEnabled()) {
            return "SUBMITTED";
        }

        AiReviewTaskRequest request = buildAiReviewTaskRequest(task);
        try {
            aiServiceClient.dispatchReviewTask(request);
            transitionTask(task, "PROCESSING");
            log.info("Task dispatched to AI service: taskId={}, status=PROCESSING", task.getTaskId());
            return "PROCESSING";
        } catch (AiReviewTaskDispatchException e) {
            markDispatchFailure(task, e);
            log.warn(
                    "Task dispatch failed and was marked FAILED: taskId={}, category={}, retryable={}, statusCode={}",
                    task.getTaskId(),
                    e.getFailureCategory(),
                    e.isRetryable(),
                    e.getStatusCode()
            );
            return "FAILED";
        }
    }

    private AiReviewTaskRequest buildAiReviewTaskRequest(ReviewTask task) {
        List<MaterialSlot> slots = materialSlotMapper.selectList(
                new LambdaQueryWrapper<MaterialSlot>().eq(MaterialSlot::getTaskId, task.getTaskId())
        );

        AiReviewTaskRequest request = new AiReviewTaskRequest();
        request.setTaskId(task.getTaskId());
        request.setSessionId(task.getSessionId());
        request.setIdempotencyKey(task.getTaskId());

        List<AiReviewTaskRequest.Material> materials = new ArrayList<>();
        for (String type : MATERIAL_TYPES) {
            Optional<MaterialSlot> slot = slots.stream()
                    .filter(item -> item.getMaterialType().equals(type))
                    .findFirst();

            AiReviewTaskRequest.Material material = new AiReviewTaskRequest.Material();
            material.setMaterialType(type);
            material.setUploaded(slot.isPresent());
            material.setOriginalFileName(slot.map(MaterialSlot::getOriginalFileName).orElse(null));
            material.setStorageKey(slot.map(MaterialSlot::getStorageKey).orElse(null));
            material.setFileExtension(slot.map(MaterialSlot::getFileExtension).orElse(null));
            materials.add(material);
        }
        request.setMaterials(materials);
        return request;
    }

    private void transitionTask(ReviewTask task, String status) {
        ProcessingStatus.validateTransition(task.getStatus(), status);
        task.setStatus(status);
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.updateById(task);
    }

    private void markDispatchFailure(ReviewTask task, AiReviewTaskDispatchException e) {
        transitionTask(task, "FAILED");

        Map<String, Object> applicantResult = new LinkedHashMap<>();
        applicantResult.put("summary", "AI审查服务调度失败，未生成智能审查结论。");
        applicantResult.put("issues", List.of(Map.of(
                "code", e.getFailureCategory(),
                "severity", "BLOCKER",
                "message", "AI审查服务暂不可用，请稍后重试或联系管理员。"
        )));
        applicantResult.put("materialCompleteness", Map.of("missing", List.of()));

        Map<String, Object> metadata = new LinkedHashMap<>();
        metadata.put("provider", "python-fastapi");
        metadata.put("failureCategory", e.getFailureCategory());
        metadata.put("retryable", e.isRetryable());
        if (e.getStatusCode() != null) {
            metadata.put("statusCode", e.getStatusCode());
        }

        Map<String, Object> reviewerIssue = new LinkedHashMap<>();
        reviewerIssue.put("code", e.getFailureCategory());
        reviewerIssue.put("severity", "BLOCKER");
        reviewerIssue.put("message", e.getMessage());
        reviewerIssue.put("applicantVisible", false);

        Map<String, Object> reviewerResult = new LinkedHashMap<>();
        reviewerResult.put("summary", "Java主动调度Python FastAPI失败，未生成AI审查结论。");
        reviewerResult.put("issues", List.of(reviewerIssue));
        reviewerResult.put("riskHints", List.of(Map.of(
                "riskLevel", "HIGH",
                "description", "Python审查服务不可用时不得伪造成功结果，需要人工复核或重试调度。",
                "requiresManualReview", true
        )));
        reviewerResult.put("draftOpinion", "");
        reviewerResult.put("manualReviewNotice", "AI审查服务调度失败，本次任务没有智能审查结论。");
        reviewerResult.put("materialCompleteness", Map.of("missing", List.of()));
        reviewerResult.put("modelMetadata", metadata);

        saveResult(task.getTaskId(), "APPLICANT", applicantResult);
        saveResult(task.getTaskId(), "REVIEWER", reviewerResult);
    }

    private SubmitResponse.MaterialInfo processMaterial(String taskId, String materialType, MultipartFile file) {
        SubmitResponse.MaterialInfo info = new SubmitResponse.MaterialInfo();
        info.setMaterialType(materialType);

        if (file == null || file.isEmpty()) {
            info.setUploaded(false);
            info.setOriginalFileName(null);
            return info;
        }

        String originalFileName = file.getOriginalFilename();
        String extension = getFileExtension(originalFileName);

        if (!ACCEPTED_FILE_TYPES.contains(extension.toLowerCase())) {
            throw new BusinessException(400, "不支持的文件格式: " + extension + ", 只允许: jpg, jpeg, png, pdf, docx");
        }

        String storageKey = taskId + "/" + materialType + "/" + UUID.randomUUID() + "." + extension;

        try {
            storageService.upload(storageKey, file.getInputStream(), file.getSize(), file.getContentType());
        } catch (IOException e) {
            log.error("文件上传失败: {}", originalFileName, e);
            throw new BusinessException(500, "文件上传失败");
        }

        MaterialSlot slot = new MaterialSlot();
        slot.setMaterialId("MAT" + UUID.randomUUID().toString().replace("-", "").substring(0, 16).toUpperCase());
        slot.setTaskId(taskId);
        slot.setMaterialType(materialType);
        slot.setOriginalFileName(originalFileName);
        slot.setContentType(file.getContentType());
        slot.setFileExtension(extension);
        slot.setFileSize(file.getSize());
        slot.setStorageKey(storageKey);
        slot.setUploadedAt(LocalDateTime.now());
        slot.setCreatedAt(LocalDateTime.now());
        slot.setUpdatedAt(LocalDateTime.now());
        materialSlotMapper.insert(slot);

        info.setUploaded(true);
        info.setOriginalFileName(originalFileName);
        info.setFileSize(slot.getFileSize());
        info.setFileExtension(slot.getFileExtension());
        info.setUploadedAt(slot.getUploadedAt());

        return info;
    }

    @Override
    public TaskStatusResponse getStatus(String taskId, String sessionId, UserProfileResponse currentUser) {
        ReviewTask task = getTaskWithAccessCheck(taskId, sessionId, currentUser);

        List<MaterialSlot> slots = materialSlotMapper.selectList(
                new LambdaQueryWrapper<MaterialSlot>().eq(MaterialSlot::getTaskId, taskId)
        );

        TaskStatusResponse response = new TaskStatusResponse();
        response.setTaskId(task.getTaskId());
        response.setStatus(task.getStatus());
        response.setHandlingStatus(task.getHandlingStatus());
        response.setHandlingStatusLabel(task.getHandlingStatusLabel());
        response.setReviewerRemark(task.getReviewerRemark());
        response.setSubmittedAt(task.getSubmittedAt());
        response.setUpdatedAt(task.getUpdatedAt());

        List<TaskStatusResponse.MaterialStatus> materialStatuses = new ArrayList<>();
        for (String type : MATERIAL_TYPES) {
            TaskStatusResponse.MaterialStatus status = new TaskStatusResponse.MaterialStatus();
            status.setMaterialType(type);

            Optional<MaterialSlot> slot = slots.stream()
                    .filter(s -> s.getMaterialType().equals(type))
                    .findFirst();

            if (slot.isPresent()) {
                applyMaterialStatus(status, slot.get());
            } else {
                status.setUploaded(false);
                status.setOriginalFileName(null);
            }

            materialStatuses.add(status);
        }

        response.setMaterials(materialStatuses);
        return response;
    }

    @Override
    public ApplicantResultResponse getApplicantResult(String taskId, String sessionId, UserProfileResponse currentUser) {
        ReviewTask task = getTaskWithAccessCheck(taskId, sessionId, currentUser);

        ReviewResult result = resultMapper.selectOne(
                new LambdaQueryWrapper<ReviewResult>()
                        .eq(ReviewResult::getTaskId, taskId)
                        .eq(ReviewResult::getResultType, "APPLICANT")
        );

        ApplicantResultResponse response = new ApplicantResultResponse();
        response.setTaskId(task.getTaskId());
        response.setStatus(task.getStatus());
        response.setHandlingStatus(task.getHandlingStatus());
        response.setHandlingStatusLabel(task.getHandlingStatusLabel());
        response.setReviewerRemark(task.getReviewerRemark());
        response.setReviewerActionAt(task.getReviewerActionAt());

        if (result != null) {
            try {
                Map<String, Object> content = objectMapper.readValue(result.getContent(), Map.class);
                response.setSummary((String) content.getOrDefault("summary", ""));
                response.setIssues(parseIssues(content.get("issues")));
                response.setMissingMaterials(parseMissingMaterialsFromContent(content));
            } catch (JsonProcessingException e) {
                log.error("解析结果失败: {}", taskId, e);
                throw new BusinessException(500, "结果解析失败");
            }
        } else {
            response.setSummary("审核结果处理中，请稍后查询");
            response.setIssues(new ArrayList<>());
            response.setMissingMaterials(new ArrayList<>());
        }

        return response;
    }

    @Override
    public ReviewerResultResponse getReviewerResult(String taskId, String sessionId, UserProfileResponse currentUser) {
        if (!isReviewer(currentUser) && !isAdmin(currentUser)) {
            throw new BusinessException(403, "当前角色无权查看审批结果");
        }

        ReviewTask task = getTaskWithAccessCheck(taskId, sessionId, currentUser);

        ReviewResult result = resultMapper.selectOne(
                new LambdaQueryWrapper<ReviewResult>()
                        .eq(ReviewResult::getTaskId, taskId)
                        .eq(ReviewResult::getResultType, "REVIEWER")
        );

        ReviewerResultResponse response = new ReviewerResultResponse();
        response.setTaskId(task.getTaskId());
        response.setStatus(task.getStatus());
        response.setHandlingStatus(task.getHandlingStatus());
        response.setHandlingStatusLabel(task.getHandlingStatusLabel());
        response.setReviewerRemark(task.getReviewerRemark());
        response.setReviewerActionCode(task.getReviewerActionCode());
        response.setReviewerUserId(task.getReviewerUserId());
        response.setReviewerDisplayName(task.getReviewerDisplayName());
        response.setReviewerActionAt(task.getReviewerActionAt());
        response.setActionLogs(loadActionLogs(taskId));

        if (result != null) {
            try {
                Map<String, Object> content = objectMapper.readValue(result.getContent(), Map.class);
                response.setSummary((String) content.getOrDefault("summary", ""));
                response.setIssues(parseReviewerIssues(content.get("issues")));
                response.setRiskHints(parseRiskHints(content.get("riskHints")));
                response.setDraftOpinion((String) content.getOrDefault("draftOpinion", ""));
                response.setManualReviewNotice((String) content.getOrDefault("manualReviewNotice", ""));
                response.setMissingMaterials(parseMissingMaterialsFromContent(content));
                response.setExtractedFields(content.get("extractedFields"));
                response.setToolCallTraces(parseToolCallTraces(content.get("toolCallTraces")));
                Object modelMeta = content.get("modelMetadata");
                if (modelMeta instanceof String) {
                    response.setModelMetadata((String) modelMeta);
                } else if (modelMeta != null) {
                    response.setModelMetadata(objectMapper.writeValueAsString(modelMeta));
                }
            } catch (JsonProcessingException e) {
                log.error("解析结果失败: {}", taskId, e);
                throw new BusinessException(500, "结果解析失败");
            }
        } else {
            response.setSummary("审核结果处理中，请稍后查询");
            response.setIssues(new ArrayList<>());
            response.setRiskHints(new ArrayList<>());
            response.setDraftOpinion("");
            response.setManualReviewNotice("");
            response.setMissingMaterials(new ArrayList<>());
            response.setToolCallTraces(new ArrayList<>());
        }

        return response;
    }

    @Override
    @Transactional
    public ReviewerActionResponse submitReviewerAction(
            String taskId,
            ReviewerActionSubmitRequest request,
            UserProfileResponse currentUser) {
        if (!isReviewer(currentUser) && !isAdmin(currentUser)) {
            throw new BusinessException(403, "当前角色无权执行审核动作");
        }

        InitialReviewAction action = InitialReviewAction.fromCode(request.getActionCode());
        if (action == null) {
            throw new BusinessException(400, "无效的审核动作: " + request.getActionCode());
        }

        ReviewTask task = taskMapper.selectOne(
                new LambdaQueryWrapper<ReviewTask>().eq(ReviewTask::getTaskId, taskId)
        );
        if (task == null) {
            throw new BusinessException(404, "任务不存在");
        }

        if (!REVIEWER_ACTION_ALLOWED_TASK_STATUSES.contains(task.getStatus())) {
            throw new BusinessException(409, "当前任务状态不允许提交审核动作: " + task.getStatus());
        }

        ReviewResult reviewerResult = resultMapper.selectOne(
                new LambdaQueryWrapper<ReviewResult>()
                        .eq(ReviewResult::getTaskId, taskId)
                        .eq(ReviewResult::getResultType, "REVIEWER")
        );
        if (reviewerResult == null) {
            throw new BusinessException(409, "AI初审结果尚未生成，暂不能提交审核动作");
        }

        if (task.getReviewerActionCode() != null && !task.getReviewerActionCode().isBlank()) {
            throw new BusinessException(409, "该任务已提交过审核动作，不允许重复提交");
        }

        LocalDateTime now = LocalDateTime.now();
        String toHandlingStatus = action.handlingStatus();
        String trimmedRemark = trimToNull(request.getReviewerRemark());
        String fromHandlingStatus = task.getHandlingStatus();

        int updated = taskMapper.update(null,
                new LambdaUpdateWrapper<ReviewTask>()
                        .set(ReviewTask::getHandlingStatus, toHandlingStatus)
                        .set(ReviewTask::getHandlingStatusLabel, action.handlingStatusLabel())
                        .set(ReviewTask::getReviewerActionCode, action.name())
                        .set(ReviewTask::getReviewerRemark, trimmedRemark)
                        .set(ReviewTask::getReviewerUserId, currentUser.getUserId())
                        .set(ReviewTask::getReviewerDisplayName, currentUser.getDisplayName())
                        .set(ReviewTask::getReviewerActionAt, now)
                        .set(ReviewTask::getUpdatedAt, now)
                        .eq(ReviewTask::getTaskId, taskId)
                        .in(ReviewTask::getStatus, REVIEWER_ACTION_ALLOWED_TASK_STATUSES)
                        .and(wrapper -> wrapper
                                .isNull(ReviewTask::getReviewerActionCode)
                                .or()
                                .eq(ReviewTask::getReviewerActionCode, ""))
        );
        if (updated == 0) {
            throw new BusinessException(409, "任务状态已变化或已提交过审核动作，请刷新后重试");
        }

        ReviewActionLog actionLog = new ReviewActionLog();
        actionLog.setTaskId(taskId);
        actionLog.setActionCode(action.name());
        actionLog.setActionLabel(action.handlingStatusLabel());
        actionLog.setReviewerRemark(trimmedRemark);
        actionLog.setOperatorUserId(currentUser.getUserId());
        actionLog.setOperatorUsername(currentUser.getUsername());
        actionLog.setOperatorDisplayName(currentUser.getDisplayName());
        actionLog.setFromHandlingStatus(fromHandlingStatus);
        actionLog.setToHandlingStatus(toHandlingStatus);
        actionLog.setCreatedAt(now);
        actionLog.setUpdatedAt(now);
        reviewActionLogMapper.insert(actionLog);

        ReviewerActionResponse response = new ReviewerActionResponse();
        response.setTaskId(taskId);
        response.setActionCode(action.name());
        response.setActionLabel(action.handlingStatusLabel());
        response.setHandlingStatus(toHandlingStatus);
        response.setHandlingStatusLabel(action.handlingStatusLabel());
        response.setReviewerRemark(trimmedRemark);
        response.setOperatorUserId(currentUser.getUserId());
        response.setOperatorDisplayName(currentUser.getDisplayName());
        response.setOperatedAt(now);

        log.info(
                "Reviewer action submitted: taskId={}, actionCode={}, operatorUserId={}",
                taskId,
                action.name(),
                currentUser.getUserId()
        );
        return response;
    }

    private List<ApplicantResultResponse.IssueItem> parseIssues(Object issuesObj) {
        List<ApplicantResultResponse.IssueItem> issues = new ArrayList<>();
        if (issuesObj instanceof List) {
            List<Map<String, Object>> issueList = (List<Map<String, Object>>) issuesObj;
            for (Map<String, Object> issueMap : issueList) {
                ApplicantResultResponse.IssueItem item = new ApplicantResultResponse.IssueItem();
                item.setCode((String) issueMap.get("code"));
                item.setSeverity((String) issueMap.get("severity"));
                item.setMessage((String) issueMap.get("message"));
                issues.add(item);
            }
        }
        return issues;
    }

    private List<ReviewerResultResponse.IssueItem> parseReviewerIssues(Object issuesObj) {
        List<ReviewerResultResponse.IssueItem> issues = new ArrayList<>();
        if (issuesObj instanceof List) {
            List<Map<String, Object>> issueList = (List<Map<String, Object>>) issuesObj;
            for (Map<String, Object> issueMap : issueList) {
                ReviewerResultResponse.IssueItem item = new ReviewerResultResponse.IssueItem();
                item.setCode((String) issueMap.get("code"));
                item.setSeverity((String) issueMap.get("severity"));
                item.setMessage((String) issueMap.get("message"));
                item.setMaterialType((String) issueMap.get("materialType"));
                item.setFieldKey((String) issueMap.get("fieldKey"));
                item.setBasisRefs((List<String>) issueMap.get("basisRefs"));
                item.setApplicantVisible((Boolean) issueMap.get("applicantVisible"));
                issues.add(item);
            }
        }
        return issues;
    }

    private List<ReviewerResultResponse.RiskHint> parseRiskHints(Object riskHintsObj) {
        List<ReviewerResultResponse.RiskHint> riskHints = new ArrayList<>();
        if (riskHintsObj instanceof List) {
            List<Map<String, Object>> hintList = (List<Map<String, Object>>) riskHintsObj;
            for (Map<String, Object> hintMap : hintList) {
                ReviewerResultResponse.RiskHint hint = new ReviewerResultResponse.RiskHint();
                hint.setRiskLevel((String) hintMap.get("riskLevel"));
                hint.setDescription((String) hintMap.get("description"));
                hint.setBasisRefs((List<String>) hintMap.get("basisRefs"));
                hint.setRequiresManualReview((Boolean) hintMap.get("requiresManualReview"));
                riskHints.add(hint);
            }
        }
        return riskHints;
    }

    @SuppressWarnings("unchecked")
    private List<ReviewerResultResponse.ToolCallTrace> parseToolCallTraces(Object tracesObj) {
        List<ReviewerResultResponse.ToolCallTrace> traces = new ArrayList<>();
        if (tracesObj instanceof List) {
            List<Map<String, Object>> traceList = (List<Map<String, Object>>) tracesObj;
            for (Map<String, Object> traceMap : traceList) {
                ReviewerResultResponse.ToolCallTrace trace = new ReviewerResultResponse.ToolCallTrace();
                trace.setToolName((String) traceMap.get("toolName"));
                trace.setInputSummary((String) traceMap.get("inputSummary"));
                trace.setOutputSummary((String) traceMap.get("outputSummary"));
                trace.setSourceRefs((List<String>) traceMap.get("sourceRefs"));
                trace.setStatus((String) traceMap.get("status"));
                Object latency = traceMap.get("latencyMs");
                if (latency instanceof Number latencyNumber) {
                    trace.setLatencyMs(latencyNumber.intValue());
                }
                trace.setError((String) traceMap.get("error"));
                traces.add(trace);
            }
        }
        return traces;
    }

    private List<ReviewActionLogItem> loadActionLogs(String taskId) {
        List<ReviewActionLog> logs = reviewActionLogMapper.selectList(
                new LambdaQueryWrapper<ReviewActionLog>()
                        .eq(ReviewActionLog::getTaskId, taskId)
                        .orderByDesc(ReviewActionLog::getCreatedAt)
        );
        List<ReviewActionLogItem> items = new ArrayList<>();
        for (ReviewActionLog logItem : logs) {
            ReviewActionLogItem item = new ReviewActionLogItem();
            item.setActionCode(logItem.getActionCode());
            item.setActionLabel(logItem.getActionLabel());
            item.setReviewerRemark(logItem.getReviewerRemark());
            item.setOperatorUserId(logItem.getOperatorUserId());
            item.setOperatorDisplayName(logItem.getOperatorDisplayName());
            item.setFromHandlingStatus(logItem.getFromHandlingStatus());
            item.setToHandlingStatus(logItem.getToHandlingStatus());
            item.setOperatedAt(logItem.getCreatedAt());
            items.add(item);
        }
        return items;
    }

    private List<String> parseMissingMaterialsFromContent(Map<String, Object> content) {
        Object mcObj = content.get("materialCompleteness");
        if (mcObj instanceof Map) {
            Object missingObj = ((Map<String, Object>) mcObj).get("missing");
            if (missingObj instanceof List) {
                return (List<String>) missingObj;
            }
        }
        // Fallback: try top-level missingMaterials
        Object topLevel = content.get("missingMaterials");
        if (topLevel instanceof List) {
            return (List<String>) topLevel;
        }
        return new ArrayList<>();
    }

    private String getFileExtension(String fileName) {
        if (fileName == null || !fileName.contains(".")) {
            return "";
        }
        return fileName.substring(fileName.lastIndexOf(".") + 1).toLowerCase();
    }

    private ReviewTask getTaskWithAccessCheck(
            String taskId,
            String sessionId,
            UserProfileResponse currentUser) {
        ReviewTask task = taskMapper.selectOne(
                new LambdaQueryWrapper<ReviewTask>().eq(ReviewTask::getTaskId, taskId)
        );

        if (task == null) {
            throw new BusinessException(404, "任务不存在");
        }

        if (isAdmin(currentUser)) {
            return task;
        }

        if (isReviewer(currentUser)) {
            if (REVIEWER_VISIBLE_STATUSES.contains(task.getStatus())) {
                return task;
            }
            throw new BusinessException(403, "当前任务不在审批可见范围");
        }

        if (currentUser.getUserId() == null || task.getOwnerUserId() == null
                || !Objects.equals(task.getOwnerUserId(), currentUser.getUserId())) {
            throw new BusinessException(403, "无权访问该任务");
        }

        if (sessionId != null && !sessionId.isBlank() && !sessionId.equals(task.getSessionId())) {
            throw new BusinessException(403, "无权访问该任务");
        }

        return task;
    }

    private String generateTaskId() {
        return "SW" + UUID.randomUUID().toString().replace("-", "").substring(0, 16).toUpperCase();
    }

    private String generateSessionId() {
        return UUID.randomUUID().toString().replace("-", "");
    }

    @Override
    public TaskListResponse getTaskList(int page, int size, UserProfileResponse currentUser) {
        int safePage = Math.max(page, 1);
        int safeSize = Math.min(Math.max(size, 1), 100);

        LambdaQueryWrapper<ReviewTask> queryWrapper = new LambdaQueryWrapper<>();
        if (isAdmin(currentUser)) {
            // admin sees all tasks
        } else if (isReviewer(currentUser)) {
            queryWrapper.in(ReviewTask::getStatus, REVIEWER_VISIBLE_STATUSES);
        } else {
            queryWrapper.eq(ReviewTask::getOwnerUserId, currentUser.getUserId());
        }
        queryWrapper.orderByDesc(ReviewTask::getSubmittedAt);

        Page<ReviewTask> taskPage = taskMapper.selectPage(
                new Page<>(safePage, safeSize),
                queryWrapper
        );
        List<ReviewTask> tasks = taskPage.getRecords();
        long total = taskPage.getTotal();

        List<String> taskIds = tasks.stream().map(ReviewTask::getTaskId).toList();
        List<MaterialSlot> slots = taskIds.isEmpty()
                ? List.of()
                : materialSlotMapper.selectList(
                        new LambdaQueryWrapper<MaterialSlot>().in(MaterialSlot::getTaskId, taskIds)
                );
        Map<String, List<MaterialSlot>> slotsByTaskId = new HashMap<>();
        for (MaterialSlot slot : slots) {
            slotsByTaskId.computeIfAbsent(slot.getTaskId(), ignored -> new ArrayList<>()).add(slot);
        }

        List<TaskListResponse.TaskListItem> items = new ArrayList<>();
        for (ReviewTask task : tasks) {
            TaskListResponse.TaskListItem item = new TaskListResponse.TaskListItem();
            item.setTaskId(task.getTaskId());
            if (isApplicant(currentUser)) {
                item.setSessionId(task.getSessionId());
            } else {
                item.setSessionId(null);
            }
            item.setStatus(task.getStatus());
            item.setHandlingStatus(task.getHandlingStatus());
            item.setHandlingStatusLabel(task.getHandlingStatusLabel());
            item.setReviewerRemark(task.getReviewerRemark());
            item.setReviewerDisplayName(task.getReviewerDisplayName());
            item.setReviewerActionAt(task.getReviewerActionAt());
            item.setSubmittedAt(task.getSubmittedAt());
            item.setUpdatedAt(task.getUpdatedAt());
            item.setKnowledgePackVersion(task.getKnowledgePackVersion());

            List<MaterialSlot> taskSlots = slotsByTaskId.getOrDefault(task.getTaskId(), List.of());

            List<TaskListResponse.MaterialStatus> materialStatuses = new ArrayList<>();
            for (String type : MATERIAL_TYPES) {
                TaskListResponse.MaterialStatus status = new TaskListResponse.MaterialStatus();
                status.setMaterialType(type);

                Optional<MaterialSlot> slot = taskSlots.stream()
                        .filter(s -> s.getMaterialType().equals(type))
                        .findFirst();

                if (slot.isPresent()) {
                    applyTaskListMaterialStatus(status, slot.get());
                } else {
                    status.setUploaded(false);
                    status.setOriginalFileName(null);
                }

                materialStatuses.add(status);
            }
            item.setMaterials(materialStatuses);
            items.add(item);
        }

        TaskListResponse response = new TaskListResponse();
        response.setItems(items);
        response.setTotal(total);
        response.setPage(safePage);
        response.setSize(safeSize);

        log.info("Task list queried: page={}, size={}, total={}, returned={}", safePage, safeSize, total, items.size());
        return response;
    }

    @Override
    @Transactional
    public List<PendingTaskResponse> getPendingTasks() {
        List<ReviewTask> tasks = taskMapper.selectList(
                new LambdaQueryWrapper<ReviewTask>()
                        .in(ReviewTask::getStatus, Arrays.asList("SUBMITTED", "QUEUED"))
                        .orderByAsc(ReviewTask::getSubmittedAt)
                        .last("LIMIT 10")
        );

        List<PendingTaskResponse> result = new ArrayList<>();
        for (ReviewTask task : tasks) {
            ReviewTask updateEntity = new ReviewTask();
            updateEntity.setStatus("PROCESSING");
            updateEntity.setUpdatedAt(LocalDateTime.now());
            int updated = taskMapper.update(updateEntity,
                    new LambdaQueryWrapper<ReviewTask>()
                            .eq(ReviewTask::getTaskId, task.getTaskId())
                            .in(ReviewTask::getStatus, Arrays.asList("SUBMITTED", "QUEUED"))
            );

            if (updated > 0) {
                PendingTaskResponse item = new PendingTaskResponse();
                item.setTaskId(task.getTaskId());
                item.setSessionId(task.getSessionId());
                item.setStatus("PROCESSING");

                List<MaterialSlot> slots = materialSlotMapper.selectList(
                        new LambdaQueryWrapper<MaterialSlot>().eq(MaterialSlot::getTaskId, task.getTaskId())
                );

                List<PendingTaskResponse.PendingMaterial> materials = new ArrayList<>();
                for (String type : MATERIAL_TYPES) {
                    PendingTaskResponse.PendingMaterial mat = new PendingTaskResponse.PendingMaterial();
                    mat.setMaterialType(type);

                    Optional<MaterialSlot> slot = slots.stream()
                            .filter(s -> s.getMaterialType().equals(type))
                            .findFirst();

                    mat.setUploaded(slot.isPresent());
                    mat.setOriginalFileName(slot.map(MaterialSlot::getOriginalFileName).orElse(null));
                    mat.setStorageKey(slot.map(MaterialSlot::getStorageKey).orElse(null));
                    mat.setFileExtension(slot.map(MaterialSlot::getFileExtension).orElse(null));
                    materials.add(mat);
                }
                item.setMaterials(materials);
                result.add(item);
            }
        }

        return result;
    }

    @Override
    public void updateStatus(String taskId, String status) {
        if (!ProcessingStatus.isValid(status)) {
            throw new BusinessException(400, "无效的任务状态: " + status);
        }

        ReviewTask task = taskMapper.selectOne(
                new LambdaQueryWrapper<ReviewTask>().eq(ReviewTask::getTaskId, taskId)
        );

        if (task == null) {
            throw new BusinessException(404, "任务不存在");
        }

        ProcessingStatus.validateTransition(task.getStatus(), status);

        task.setStatus(status);
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.updateById(task);

        log.info("Task status updated: taskId={}, status={}", taskId, status);
    }

    @Override
    @Transactional
    public void writeResult(String taskId, ResultWriteRequest request) {
        ReviewTask task = taskMapper.selectOne(
                new LambdaQueryWrapper<ReviewTask>().eq(ReviewTask::getTaskId, taskId)
        );

        if (task == null) {
            throw new BusinessException(404, "任务不存在");
        }

        String newStatus = request.getStatus();
        if (newStatus != null) {
            if (!ProcessingStatus.isValid(newStatus)) {
                throw new BusinessException(400, "无效的任务状态: " + newStatus);
            }
            ProcessingStatus.validateTransition(task.getStatus(), newStatus);
            task.setStatus(newStatus);
        }
        if (request.getKnowledgePackVersion() != null) {
            task.setKnowledgePackVersion(request.getKnowledgePackVersion());
        }
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.updateById(task);

        if (request.getApplicantResult() != null) {
            saveResult(taskId, "APPLICANT", request.getApplicantResult());
        }

        if (request.getReviewerResult() != null) {
            saveResult(taskId, "REVIEWER", request.getReviewerResult());
        }

        log.info("Result written for task: taskId={}, status={}", taskId, request.getStatus());
    }

    private void saveResult(String taskId, String resultType, Map<String, Object> content) {
        ReviewResult existing = resultMapper.selectOne(
                new LambdaQueryWrapper<ReviewResult>()
                        .eq(ReviewResult::getTaskId, taskId)
                        .eq(ReviewResult::getResultType, resultType)
        );

        try {
            String json = objectMapper.writeValueAsString(content);

            if (existing != null) {
                existing.setContent(json);
                existing.setUpdatedAt(LocalDateTime.now());
                resultMapper.updateById(existing);
            } else {
                ReviewResult result = new ReviewResult();
                result.setTaskId(taskId);
                result.setResultType(resultType);
                result.setContent(json);
                result.setCreatedAt(LocalDateTime.now());
                result.setUpdatedAt(LocalDateTime.now());
                resultMapper.insert(result);
            }
        } catch (JsonProcessingException e) {
            log.error("Failed to serialize result for task: {}", taskId, e);
            throw new BusinessException(500, "结果序列化失败");
        }
    }

    @Override
    public MaterialPreviewResource previewMaterial(
            String taskId,
            String materialType,
            UserProfileResponse currentUser) {
        getTaskWithAccessCheck(taskId, null, currentUser);

        if (!MATERIAL_TYPES.contains(materialType)) {
            throw new BusinessException(400, "无效的材料类型: " + materialType);
        }

        MaterialSlot slot = materialSlotMapper.selectOne(
                new LambdaQueryWrapper<MaterialSlot>()
                        .eq(MaterialSlot::getTaskId, taskId)
                        .eq(MaterialSlot::getMaterialType, materialType)
        );
        if (slot == null || slot.getStorageKey() == null || slot.getStorageKey().isBlank()) {
            throw new BusinessException(404, "材料未上传或不存在");
        }

        String extension = Optional.ofNullable(slot.getFileExtension())
                .map(value -> value.toLowerCase(Locale.ROOT))
                .orElse("");
        String previewContentType = PREVIEW_CONTENT_TYPES.get(extension);
        if (previewContentType == null) {
            throw new BusinessException(415, "当前材料格式暂不支持浏览器预览");
        }

        try {
            InputStream inputStream = storageService.download(slot.getStorageKey());
            return new MaterialPreviewResource(
                    inputStream,
                    previewContentType,
                    safePreviewFileName(slot),
                    slot.getFileSize(),
                    extension
            );
        } catch (Exception e) {
            log.error("Failed to preview material: taskId={}, materialType={}", taskId, materialType, e);
            throw new BusinessException(404, "材料文件不存在或无法访问");
        }
    }

    @Override
    public InputStream downloadMaterial(String storageKey) {
        try {
            return storageService.download(storageKey);
        } catch (Exception e) {
            log.error("Failed to download material: {}", storageKey, e);
            throw new BusinessException(404, "材料文件不存在或无法访问");
        }
    }

    @Override
    public String getMaterialContentType(String storageKey) {
        MaterialSlot slot = materialSlotMapper.selectOne(
                new LambdaQueryWrapper<MaterialSlot>().eq(MaterialSlot::getStorageKey, storageKey)
        );
        return slot != null ? slot.getContentType() : "application/octet-stream";
    }

    private boolean canSubmit(UserProfileResponse currentUser) {
        return isApplicant(currentUser) || isAdmin(currentUser);
    }

    private void applyMaterialStatus(TaskStatusResponse.MaterialStatus status, MaterialSlot slot) {
        status.setUploaded(true);
        status.setOriginalFileName(slot.getOriginalFileName());
        status.setFileSize(slot.getFileSize());
        status.setFileExtension(slot.getFileExtension());
        status.setUploadedAt(slot.getUploadedAt());
    }

    private void applyTaskListMaterialStatus(TaskListResponse.MaterialStatus status, MaterialSlot slot) {
        status.setUploaded(true);
        status.setOriginalFileName(slot.getOriginalFileName());
        status.setFileSize(slot.getFileSize());
        status.setFileExtension(slot.getFileExtension());
        status.setUploadedAt(slot.getUploadedAt());
    }

    private String safePreviewFileName(MaterialSlot slot) {
        String originalFileName = trimToNull(slot.getOriginalFileName());
        if (originalFileName != null) {
            return originalFileName.replace("\r", "").replace("\n", "");
        }
        String extension = trimToNull(slot.getFileExtension());
        return extension == null ? slot.getMaterialType() : slot.getMaterialType() + "." + extension;
    }

    private boolean isApplicant(UserProfileResponse currentUser) {
        return currentUser != null && RoleConstants.APPLICANT.equals(currentUser.getRole());
    }

    private boolean isReviewer(UserProfileResponse currentUser) {
        return currentUser != null && RoleConstants.REVIEWER.equals(currentUser.getRole());
    }

    private boolean isAdmin(UserProfileResponse currentUser) {
        return currentUser != null && RoleConstants.ADMIN.equals(currentUser.getRole());
    }

    private String trimToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }
}
