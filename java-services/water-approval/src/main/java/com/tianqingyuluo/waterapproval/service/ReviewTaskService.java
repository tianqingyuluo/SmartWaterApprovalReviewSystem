package com.tianqingyuluo.waterapproval.service;

import com.tianqingyuluo.waterapproval.dto.*;

import java.io.InputStream;
import java.util.List;

public interface ReviewTaskService {
    SubmitResponse submit(SubmitRequest request, UserProfileResponse currentUser);
    TaskStatusResponse getStatus(String taskId, String sessionId, UserProfileResponse currentUser);
    ApplicantResultResponse getApplicantResult(String taskId, String sessionId, UserProfileResponse currentUser);
    ReviewerResultResponse getReviewerResult(String taskId, String sessionId, UserProfileResponse currentUser);

    List<PendingTaskResponse> getPendingTasks();
    TaskListResponse getTaskList(int page, int size, UserProfileResponse currentUser);
    void updateStatus(String taskId, String status);
    void writeResult(String taskId, ResultWriteRequest request);
    InputStream downloadMaterial(String storageKey);
    String getMaterialContentType(String storageKey);
}
