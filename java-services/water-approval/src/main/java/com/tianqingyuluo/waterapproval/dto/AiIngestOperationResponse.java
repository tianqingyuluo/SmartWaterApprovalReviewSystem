package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.util.List;

@Data
public class AiIngestOperationResponse {
    private String mode;
    private String workdir;
    private String sourceDir;
    private int chunkSize;
    private int chunkOverlap;
    private boolean rebuild;
    private List<String> command;
    private String verificationCommand;
    private String note;
}
