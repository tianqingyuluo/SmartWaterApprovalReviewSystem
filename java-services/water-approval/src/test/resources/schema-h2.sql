CREATE TABLE IF NOT EXISTS review_task (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    owner_user_id BIGINT,
    status VARCHAR(32) NOT NULL DEFAULT 'SUBMITTED',
    handling_status VARCHAR(64),
    handling_status_label VARCHAR(64),
    reviewer_action_code VARCHAR(64),
    reviewer_remark CLOB,
    reviewer_user_id BIGINT,
    reviewer_display_name VARCHAR(128),
    reviewer_action_at TIMESTAMP NULL,
    submitted_at TIMESTAMP NULL,
    knowledge_pack_version VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS material_slot (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    material_id VARCHAR(64),
    task_id VARCHAR(64) NOT NULL,
    material_type VARCHAR(64) NOT NULL,
    original_file_name VARCHAR(255),
    content_type VARCHAR(128),
    file_extension VARCHAR(16),
    file_size BIGINT DEFAULT 0,
    storage_key VARCHAR(255),
    uploaded_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS review_result (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    result_type VARCHAR(32) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS review_action_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    action_code VARCHAR(64) NOT NULL,
    action_label VARCHAR(64) NOT NULL,
    reviewer_remark CLOB,
    operator_user_id BIGINT,
    operator_username VARCHAR(64),
    operator_display_name VARCHAR(128),
    from_handling_status VARCHAR(64),
    to_handling_status VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_account (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_code VARCHAR(32) NOT NULL,
    enabled INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted INT DEFAULT 0
);
