package com.tianqingyuluo.waterapproval.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("review_result")
public class ReviewResult {

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private String taskId;

    private String resultType;

    private String content;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    @TableLogic
    private Integer deleted;
}
