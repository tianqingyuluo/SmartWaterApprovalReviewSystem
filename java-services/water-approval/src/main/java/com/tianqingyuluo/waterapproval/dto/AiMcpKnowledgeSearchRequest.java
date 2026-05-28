package com.tianqingyuluo.waterapproval.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class AiMcpKnowledgeSearchRequest {
    @NotBlank(message = "查询词不能为空")
    private String query;

    @Min(value = 1, message = "topK 不能小于 1")
    @Max(value = 50, message = "topK 不能大于 50")
    private Integer topK = 5;
}
