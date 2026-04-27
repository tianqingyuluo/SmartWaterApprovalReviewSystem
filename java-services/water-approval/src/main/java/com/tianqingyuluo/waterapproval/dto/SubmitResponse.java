package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class SubmitResponse {
    private String taskId;
    private String sessionId;
    private String status;
    private LocalDateTime submittedAt;
    private List<MaterialInfo> materials;

    @Data
    public static class MaterialInfo {
        private String materialType;
        private String originalFileName;
        private Boolean uploaded;
    }
}
