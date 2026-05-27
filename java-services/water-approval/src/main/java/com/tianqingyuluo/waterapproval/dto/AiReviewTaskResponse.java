package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

@Data
public class AiReviewTaskResponse {
    private String aiTaskId;
    private String status;
    private String createdAt;
}
