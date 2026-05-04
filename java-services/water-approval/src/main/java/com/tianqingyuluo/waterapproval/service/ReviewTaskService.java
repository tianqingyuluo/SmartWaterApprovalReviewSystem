package com.tianqingyuluo.waterapproval.service;

import com.tianqingyuluo.waterapproval.dto.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.List;

public interface ReviewTaskService {
    SubmitResponse submit(SubmitRequest request);
    TaskStatusResponse getStatus(String taskId, String sessionId);
    ApplicantResultResponse getApplicantResult(String taskId, String sessionId);
    ReviewerResultResponse getReviewerResult(String taskId, String sessionId);

    List<PendingTaskResponse> getPendingTasks();
    void updateStatus(String taskId, String status);
    void writeResult(String taskId, ResultWriteRequest request);
    InputStream downloadMaterial(String storageKey);
    String getMaterialContentType(String storageKey);
}
