-- SmartWater MVP 数据库权威建表脚本
-- 若需初始化数据库，请由 init-db.sh / init-db.bat 调用本文件

CREATE DATABASE IF NOT EXISTS smartwater
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE smartwater;

CREATE TABLE IF NOT EXISTS review_task (
    id BIGINT PRIMARY KEY COMMENT '主键ID',
    task_id VARCHAR(64) NOT NULL COMMENT '任务ID',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    status VARCHAR(32) NOT NULL COMMENT '任务状态',
    submitted_at DATETIME NOT NULL COMMENT '提交时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL COMMENT '更新时间',
    knowledge_pack_version VARCHAR(64) DEFAULT NULL COMMENT '知识包版本',
    deleted TINYINT(1) DEFAULT 0 COMMENT '逻辑删除 0-未删除 1-已删除',
    UNIQUE INDEX uk_task_id (task_id),
    UNIQUE INDEX uk_session_id (session_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审核任务表';

CREATE TABLE IF NOT EXISTS material_slot (
    id BIGINT PRIMARY KEY COMMENT '主键ID',
    material_id VARCHAR(64) NOT NULL COMMENT '材料ID',
    task_id VARCHAR(64) NOT NULL COMMENT '任务ID',
    material_type VARCHAR(32) NOT NULL COMMENT '材料类型',
    original_file_name VARCHAR(255) DEFAULT NULL COMMENT '原始文件名',
    content_type VARCHAR(128) DEFAULT NULL COMMENT '内容类型',
    file_extension VARCHAR(16) DEFAULT NULL COMMENT '文件扩展名',
    file_size BIGINT DEFAULT NULL COMMENT '文件大小',
    storage_key VARCHAR(512) DEFAULT NULL COMMENT '存储键',
    uploaded_at DATETIME DEFAULT NULL COMMENT '上传时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT(1) DEFAULT 0 COMMENT '逻辑删除 0-未删除 1-已删除',
    UNIQUE INDEX uk_task_material (task_id, material_type),
    UNIQUE INDEX uk_material_id (material_id),
    INDEX idx_task_id (task_id),
    INDEX idx_material_type (material_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='材料槽位表';

CREATE TABLE IF NOT EXISTS review_result (
    id BIGINT PRIMARY KEY COMMENT '主键ID',
    task_id VARCHAR(64) NOT NULL COMMENT '任务ID',
    result_type VARCHAR(32) NOT NULL COMMENT '结果类型 APPLICANT/REVIEWER',
    content TEXT COMMENT '结果内容 JSON',
    created_at DATETIME NOT NULL COMMENT '创建时间',
    updated_at DATETIME NOT NULL COMMENT '更新时间',
    deleted TINYINT(1) DEFAULT 0 COMMENT '逻辑删除 0-未删除 1-已删除',
    UNIQUE INDEX uk_task_result (task_id, result_type),
    INDEX idx_task_id (task_id),
    INDEX idx_result_type (result_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审核结果表';
