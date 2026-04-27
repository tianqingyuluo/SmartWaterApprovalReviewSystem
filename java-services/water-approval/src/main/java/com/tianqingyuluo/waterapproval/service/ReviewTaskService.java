package com.tianqingyuluo.waterapproval.service;

import com.tianqingyuluo.waterapproval.dto.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.List;
import java.util.Map;

public interface ReviewTaskService {
    SubmitResponse submit(SubmitRequest request);
    TaskStatusResponse getStatus(String taskId);
    ApplicantResultResponse getApplicantResult(String taskId);
    ReviewerResultResponse getReviewerResult(String taskId);

    List<Map<String, Object>> getPendingTasks();
    void updateStatus(String taskId, String status);
    void writeResult(String taskId, ResultWriteRequest request);
    InputStream downloadMaterial(String storageKey);
    String getMaterialContentType(String storageKey);
}
