package com.tianqingyuluo.waterapproval.service;

import com.tianqingyuluo.waterapproval.dto.*;
import org.springframework.web.multipart.MultipartFile;

public interface ReviewTaskService {
    SubmitResponse submit(SubmitRequest request);
    TaskStatusResponse getStatus(String taskId);
    ApplicantResultResponse getApplicantResult(String taskId);
    ReviewerResultResponse getReviewerResult(String taskId);
}
