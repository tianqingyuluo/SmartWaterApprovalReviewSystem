package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class ApplicantResultResponse {
    private String taskId;
    private String status;
    private String handlingStatus;
    private String handlingStatusLabel;
    private String reviewerRemark;
    private LocalDateTime reviewerActionAt;
    private String summary;
    private List<IssueItem> issues;
    private List<String> missingMaterials;

    @Data
    public static class IssueItem {
        private String code;
        private String severity;
        private String message;
    }
}
