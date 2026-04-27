package com.tianqingyuluo.waterapproval.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("material_slot")
public class MaterialSlot {

    @TableId(type = IdType.ASSIGN_ID)
    private Long id;

    private String taskId;

    private String materialType;

    private String originalFileName;

    private String contentType;

    private String fileExtension;

    private Long fileSize;

    private String storageKey;

    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime uploadedAt;

    @TableLogic
    private Integer deleted;
}
