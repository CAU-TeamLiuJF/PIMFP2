CREATE TABLE IF NOT EXISTS pimfp.`daily_quota`
(
    `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '自增id',
    `email`      VARCHAR(255)    NOT NULL COMMENT '用户邮箱',
    `quota_date` DATE            NOT NULL COMMENT '额度归属日期',
    `used_quota` INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '当日已使用额度',
    `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_email_quota_date` (`email`, `quota_date`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci COMMENT ='用户每日使用额度表';
