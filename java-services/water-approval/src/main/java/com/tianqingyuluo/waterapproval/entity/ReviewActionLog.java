package com.tianqingyuluo.waterapproval.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("review_action_log")
public class ReviewActionLog {

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private String taskId;

    private String actionCode;

    private String actionLabel;

    private String reviewerRemark;

    private Long operatorUserId;

    private String operatorUsername;

    private String operatorDisplayName;

    private String fromHandlingStatus;

    private String toHandlingStatus;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createdAt;

    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updatedAt;

    @TableLogic
    private Integer deleted;
}
