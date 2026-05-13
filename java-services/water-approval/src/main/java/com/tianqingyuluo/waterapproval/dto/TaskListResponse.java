package com.tianqingyuluo.waterapproval.dto;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class TaskListResponse {
    private List<TaskListItem> items;
    private long total;
    private int page;
    private int size;

    @Data
    public static class TaskListItem {
        private String taskId;
        private String sessionId;
        private String status;
        private LocalDateTime submittedAt;
        private LocalDateTime updatedAt;
        private String knowledgePackVersion;
        private List<MaterialStatus> materials;
    }

    @Data
    public static class MaterialStatus {
        private String materialType;
        private String originalFileName;
        private Boolean uploaded;
    }
}
