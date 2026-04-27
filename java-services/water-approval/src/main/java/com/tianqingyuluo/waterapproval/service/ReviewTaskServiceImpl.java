package com.tianqingyuluo.waterapproval.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.tianqingyuluo.waterapproval.common.BusinessException;
import com.tianqingyuluo.waterapproval.dto.*;
import com.tianqingyuluo.waterapproval.entity.MaterialSlot;
import com.tianqingyuluo.waterapproval.entity.ReviewResult;
import com.tianqingyuluo.waterapproval.entity.ReviewTask;
import com.tianqingyuluo.waterapproval.mapper.MaterialSlotMapper;
import com.tianqingyuluo.waterapproval.mapper.ReviewResultMapper;
import com.tianqingyuluo.waterapproval.mapper.ReviewTaskMapper;
import com.tianqingyuluo.waterapproval.storage.StorageService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.time.LocalDateTime;
import java.util.*;

@Slf4j
@Service
public class ReviewTaskServiceImpl implements ReviewTaskService {

    @Autowired
    private ReviewTaskMapper taskMapper;

    @Autowired
    private MaterialSlotMapper materialSlotMapper;

    @Autowired
    private ReviewResultMapper resultMapper;

    @Autowired
    private StorageService storageService;

    @Autowired
    private ObjectMapper objectMapper;

    private static final List<String> ACCEPTED_FILE_TYPES = Arrays.asList("jpg", "jpeg", "png", "pdf");
    private static final List<String> MATERIAL_TYPES = Arrays.asList("APPLICATION_FORM", "BUSINESS_LICENSE", "ID_CARD");

    @Override
    @Transactional
    public SubmitResponse submit(SubmitRequest request) {
        String taskId = generateTaskId();
        String sessionId = generateSessionId();

        ReviewTask task = new ReviewTask();
        task.setTaskId(taskId);
        task.setSessionId(sessionId);
        task.setStatus("SUBMITTED");
        task.setSubmittedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.insert(task);

        List<SubmitResponse.MaterialInfo> materialInfos = new ArrayList<>();

        materialInfos.add(processMaterial(taskId, "APPLICATION_FORM", request.getApplicationForm()));
        materialInfos.add(processMaterial(taskId, "BUSINESS_LICENSE", request.getBusinessLicense()));
        materialInfos.add(processMaterial(taskId, "ID_CARD", request.getIdCard()));

        SubmitResponse response = new SubmitResponse();
        response.setTaskId(taskId);
        response.setSessionId(sessionId);
        response.setStatus("SUBMITTED");
        response.setSubmittedAt(task.getSubmittedAt());
        response.setMaterials(materialInfos);

        log.info("Task submitted: taskId={}, sessionId={}", taskId, sessionId);
        return response;
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
            throw new BusinessException(400, "不支持的文件格式: " + extension + ", 只允许: jpg, jpeg, png, pdf");
        }

        String storageKey = taskId + "/" + materialType + "/" + UUID.randomUUID() + "." + extension;

        try {
            storageService.upload(storageKey, file.getInputStream(), file.getSize(), file.getContentType());
        } catch (IOException e) {
            log.error("文件上传失败: {}", originalFileName, e);
            throw new BusinessException(500, "文件上传失败");
        }

        MaterialSlot slot = new MaterialSlot();
        slot.setTaskId(taskId);
        slot.setMaterialType(materialType);
        slot.setOriginalFileName(originalFileName);
        slot.setContentType(file.getContentType());
        slot.setFileExtension(extension);
        slot.setFileSize(file.getSize());
        slot.setStorageKey(storageKey);
        slot.setUploadedAt(LocalDateTime.now());
        materialSlotMapper.insert(slot);

        info.setUploaded(true);
        info.setOriginalFileName(originalFileName);

        return info;
    }

    @Override
    public TaskStatusResponse getStatus(String taskId) {
        ReviewTask task = taskMapper.selectOne(
                new LambdaQueryWrapper<ReviewTask>().eq(ReviewTask::getTaskId, taskId)
        );

        if (task == null) {
            throw new BusinessException(404, "任务不存在");
        }

        List<MaterialSlot> slots = materialSlotMapper.selectList(
                new LambdaQueryWrapper<MaterialSlot>().eq(MaterialSlot::getTaskId, taskId)
        );

        TaskStatusResponse response = new TaskStatusResponse();
        response.setTaskId(task.getTaskId());
        response.setStatus(task.getStatus());
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
                status.setUploaded(true);
                status.setOriginalFileName(slot.get().getOriginalFileName());
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
    public ApplicantResultResponse getApplicantResult(String taskId) {
        ReviewTask task = taskMapper.selectOne(
                new LambdaQueryWrapper<ReviewTask>().eq(ReviewTask::getTaskId, taskId)
        );

        if (task == null) {
            throw new BusinessException(404, "任务不存在");
        }

        ReviewResult result = resultMapper.selectOne(
                new LambdaQueryWrapper<ReviewResult>()
                        .eq(ReviewResult::getTaskId, taskId)
                        .eq(ReviewResult::getResultType, "APPLICANT")
        );

        ApplicantResultResponse response = new ApplicantResultResponse();
        response.setTaskId(task.getTaskId());
        response.setStatus(task.getStatus());

        if (result != null) {
            try {
                Map<String, Object> content = objectMapper.readValue(result.getContent(), Map.class);
                response.setSummary((String) content.getOrDefault("summary", ""));
                response.setIssues(parseIssues(content.get("issues")));
                response.setMissingMaterials(parseMissingMaterials(content.get("missingMaterials")));
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
    public ReviewerResultResponse getReviewerResult(String taskId) {
        ReviewTask task = taskMapper.selectOne(
                new LambdaQueryWrapper<ReviewTask>().eq(ReviewTask::getTaskId, taskId)
        );

        if (task == null) {
            throw new BusinessException(404, "任务不存在");
        }

        ReviewResult result = resultMapper.selectOne(
                new LambdaQueryWrapper<ReviewResult>()
                        .eq(ReviewResult::getTaskId, taskId)
                        .eq(ReviewResult::getResultType, "REVIEWER")
        );

        ReviewerResultResponse response = new ReviewerResultResponse();
        response.setTaskId(task.getTaskId());
        response.setStatus(task.getStatus());

        if (result != null) {
            try {
                Map<String, Object> content = objectMapper.readValue(result.getContent(), Map.class);
                response.setSummary((String) content.getOrDefault("summary", ""));
                response.setIssues(parseReviewerIssues(content.get("issues")));
                response.setRiskHints(parseRiskHints(content.get("riskHints")));
                response.setDraftOpinion((String) content.getOrDefault("draftOpinion", ""));
                response.setMissingMaterials(parseMissingMaterials(content.get("missingMaterials")));
                response.setExtractedFields(content.get("extractedFields"));
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
            response.setMissingMaterials(new ArrayList<>());
        }

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

    private List<String> parseMissingMaterials(Object missingObj) {
        if (missingObj instanceof List) {
            return (List<String>) missingObj;
        }
        return new ArrayList<>();
    }

    private String getFileExtension(String fileName) {
        if (fileName == null || !fileName.contains(".")) {
            return "";
        }
        return fileName.substring(fileName.lastIndexOf(".") + 1).toLowerCase();
    }

    private String generateTaskId() {
        return "SW" + UUID.randomUUID().toString().replace("-", "").substring(0, 16).toUpperCase();
    }

    private String generateSessionId() {
        return UUID.randomUUID().toString().replace("-", "");
    }

    @Override
    public List<Map<String, Object>> getPendingTasks() {
        List<ReviewTask> tasks = taskMapper.selectList(
                new LambdaQueryWrapper<ReviewTask>()
                        .in(ReviewTask::getStatus, Arrays.asList("SUBMITTED", "QUEUED"))
                        .orderByAsc(ReviewTask::getSubmittedAt)
        );

        List<Map<String, Object>> result = new ArrayList<>();
        for (ReviewTask task : tasks) {
            Map<String, Object> item = new java.util.LinkedHashMap<>();
            item.put("taskId", task.getTaskId());
            item.put("status", task.getStatus());

            List<MaterialSlot> slots = materialSlotMapper.selectList(
                    new LambdaQueryWrapper<MaterialSlot>().eq(MaterialSlot::getTaskId, task.getTaskId())
            );

            List<Map<String, Object>> materials = new ArrayList<>();
            for (String type : MATERIAL_TYPES) {
                Map<String, Object> mat = new java.util.LinkedHashMap<>();
                mat.put("materialType", type);

                Optional<MaterialSlot> slot = slots.stream()
                        .filter(s -> s.getMaterialType().equals(type))
                        .findFirst();

                mat.put("uploaded", slot.isPresent());
                mat.put("originalFileName", slot.map(MaterialSlot::getOriginalFileName).orElse(null));
                mat.put("storageKey", slot.map(MaterialSlot::getStorageKey).orElse(null));
                mat.put("fileExtension", slot.map(MaterialSlot::getFileExtension).orElse(null));
                materials.add(mat);
            }
            item.put("materials", materials);
            result.add(item);
        }

        return result;
    }

    @Override
    public void updateStatus(String taskId, String status) {
        ReviewTask task = taskMapper.selectOne(
                new LambdaQueryWrapper<ReviewTask>().eq(ReviewTask::getTaskId, taskId)
        );

        if (task == null) {
            throw new BusinessException(404, "任务不存在");
        }

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

        task.setStatus(request.getStatus() != null ? request.getStatus() : task.getStatus());
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
}
