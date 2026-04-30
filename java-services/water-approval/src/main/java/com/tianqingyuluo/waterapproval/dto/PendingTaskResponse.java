package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.util.List;

@Data
public class PendingTaskResponse {
    private String taskId;
    private String status;
    private List<PendingMaterial> materials;

    @Data
    public static class PendingMaterial {
        private String materialType;
        private Boolean uploaded;
        private String originalFileName;
        private String storageKey;
        private String fileExtension;
    }
}
