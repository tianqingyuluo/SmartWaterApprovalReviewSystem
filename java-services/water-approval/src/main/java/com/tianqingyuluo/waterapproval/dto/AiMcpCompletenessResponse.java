package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.util.List;

@Data
public class AiMcpCompletenessResponse {
    private List<String> submitted;
    private List<String> required;
    private List<String> missing;
    private boolean complete;
    private List<AiMcpCompletenessFinding> findings;
    private String knowledgePackVersion;
}
