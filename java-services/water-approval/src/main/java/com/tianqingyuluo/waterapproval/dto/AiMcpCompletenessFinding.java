package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.util.List;

@Data
public class AiMcpCompletenessFinding {
    private String code;
    private String severity;
    private String materialType;
    private String materialId;
    private String materialDisplayName;
    private String message;
    private String applicantMessage;
    private List<String> basisRefs;
    private List<String> sourceRefs;
}
