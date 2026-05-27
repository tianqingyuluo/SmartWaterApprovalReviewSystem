package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.util.List;

@Data
public class AiReviewTaskRequest {
    private String taskId;
    private String sessionId;
    private List<Material> materials;
    private String idempotencyKey;

    @Data
    public static class Material {
        private String materialType;
        private String originalFileName;
        private String storageKey;
        private String fileExtension;
        private Boolean uploaded;
    }
}
