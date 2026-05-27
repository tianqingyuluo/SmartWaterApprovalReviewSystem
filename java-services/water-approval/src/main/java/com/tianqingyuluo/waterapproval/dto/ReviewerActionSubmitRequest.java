package com.tianqingyuluo.waterapproval.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class ReviewerActionSubmitRequest {

    @NotBlank(message = "actionCode不能为空")
    @Size(max = 64, message = "actionCode长度不能超过64")
    private String actionCode;

    @Size(max = 1000, message = "审批备注长度不能超过1000")
    private String reviewerRemark;
}
