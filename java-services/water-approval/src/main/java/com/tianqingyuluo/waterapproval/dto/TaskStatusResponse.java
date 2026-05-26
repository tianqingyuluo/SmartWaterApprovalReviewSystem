package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class TaskStatusResponse {
    private String taskId;
    private String status;
    private String handlingStatus;
    private String handlingStatusLabel;
    private String reviewerRemark;
    private LocalDateTime submittedAt;
    private LocalDateTime updatedAt;
    private List<MaterialStatus> materials;

    @Data
    public static class MaterialStatus {
        private String materialType;
        private String originalFileName;
        private Boolean uploaded;
    }
}
