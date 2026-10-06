CREATE TABLE IF NOT EXISTS pimfp.`app_user_role`
(
    `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '自增id',
    `user_id`    BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    `email`      VARCHAR(255)    NOT NULL COMMENT '用户邮箱',
    `role_id`    BIGINT UNSIGNED NOT NULL COMMENT '角色ID',
    `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_user_id_role_id` (`user_id`, `role_id`),
    UNIQUE KEY `uk_email_role_id` (`email`, `role_id`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci COMMENT ='用户角色关联表';
