package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;
import java.util.Map;

@Data
public class ResultWriteRequest {
    private String status;
    private String resultSummary;
    private Map<String, Object> applicantResult;
    private Map<String, Object> reviewerResult;
    private String errorMessage;
}
