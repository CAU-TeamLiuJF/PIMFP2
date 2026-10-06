CREATE TABLE IF NOT EXISTS pimfp.`image_mapping`
(
    `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '自增id',
    `flow_no`    VARCHAR(32)     NOT NULL COMMENT '任务流水号',
    `filename`   VARCHAR(255)    NOT NULL COMMENT '原始图片文件名',
    `local_path` VARCHAR(512)    NOT NULL COMMENT '本地安全存储路径',
    `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_flow_no` (`flow_no`),
    UNIQUE KEY `uk_flow_no_filename` (`flow_no`, `filename`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci COMMENT ='预测任务图片映射表';
