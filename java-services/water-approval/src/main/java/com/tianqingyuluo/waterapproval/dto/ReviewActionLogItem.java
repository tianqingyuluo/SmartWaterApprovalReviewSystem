package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ReviewActionLogItem {
    private String actionCode;
    private String actionLabel;
    private String reviewerRemark;
    private Long operatorUserId;
    private String operatorDisplayName;
    private String fromHandlingStatus;
    private String toHandlingStatus;
    private LocalDateTime operatedAt;
}
