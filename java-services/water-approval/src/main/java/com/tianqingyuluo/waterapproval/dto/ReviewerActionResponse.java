package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ReviewerActionResponse {
    private String taskId;
    private String actionCode;
    private String actionLabel;
    private String handlingStatus;
    private String handlingStatusLabel;
    private String reviewerRemark;
    private Long operatorUserId;
    private String operatorDisplayName;
    private LocalDateTime operatedAt;
}
