package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.util.List;

@Data
public class AiMcpKnowledgeSearchResponse {
    private String query;
    private Integer requestedTopK;
    private int topK;
    private int total;
    private List<AiMcpKnowledgeSearchResultItem> results;
    private String knowledgePackVersion;
}
