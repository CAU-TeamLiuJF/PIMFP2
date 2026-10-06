CREATE TABLE IF NOT EXISTS pimfp.`app_user`
(
    `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '自增id',
    `email`        VARCHAR(255)    NOT NULL UNIQUE COMMENT '用户邮箱',
    `organization` VARCHAR(255)    NOT NULL COMMENT '所属组织/机构',
    `password`     VARCHAR(128)    NOT NULL COMMENT '密码',
    `status`       TINYINT         NOT NULL DEFAULT 1 COMMENT '用户状态 0-禁用 1-正常',
    `created_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci COMMENT ='用户表';
