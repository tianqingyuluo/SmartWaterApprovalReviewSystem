package com.tianqingyuluo.waterapproval.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("review_task")
public class ReviewTask {

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private String taskId;

    private String sessionId;

    private String status;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime submittedAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    private String knowledgePackVersion;

    @TableLogic
    private Integer deleted;
}
