package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.util.List;

@Data
public class AiMcpKnowledgeSearchResultItem {
    private int rank;
    private String section;
    private String id;
    private String title;
    private String materialType;
    private String fieldPath;
    private String excerpt;
    private Double score;
    private List<String> sourceIds;
    private List<String> sourceRefs;
    private List<String> basisRefs;
}
