package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.util.List;

@Data
public class ReviewerResultResponse {
    private String taskId;
    private String status;
    private String summary;
    private List<IssueItem> issues;
    private List<RiskHint> riskHints;
    private String draftOpinion;
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
