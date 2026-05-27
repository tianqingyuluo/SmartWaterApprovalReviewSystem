package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class ReviewerResultResponse {
    private String taskId;
    private String status;
    private String handlingStatus;
    private String handlingStatusLabel;
    private String reviewerRemark;
    private String reviewerActionCode;
    private Long reviewerUserId;
    private String reviewerDisplayName;
    private LocalDateTime reviewerActionAt;
    private List<ReviewActionLogItem> actionLogs;
    private String summary;
    private List<IssueItem> issues;
    private List<RiskHint> riskHints;
    private String draftOpinion;
    private String manualReviewNotice;
    private List<String> missingMaterials;
    private Object extractedFields;
    private String modelMetadata;

    @Data
    public static class IssueItem {
        private String code;
        private String severity;
        private String message;
        private String materialType;
        private String fieldKey;
        private List<String> basisRefs;
        private Boolean applicantVisible;
    }

    @Data
    public static class RiskHint {
        private String riskLevel;
        private String description;
        private List<String> basisRefs;
        private Boolean requiresManualReview;
    }
}
