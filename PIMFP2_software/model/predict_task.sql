CREATE TABLE IF NOT EXISTS pimfp.`predict_task`
(
    `id`               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT '自增id',
    `flow_no`          VARCHAR(32)     NOT NULL UNIQUE COMMENT '任务流水号',
    `email`            VARCHAR(255)    NOT NULL COMMENT '用户邮箱',
    `prediction_type`  TINYINT         NOT NULL COMMENT '预测类型 0-背膘厚图像 1-眼肌面积图像 2-背膘厚和眼肌面积图像',
    `ultrasound_type`  TINYINT         NOT NULL COMMENT '超声波/图像类型 0-EXPRO 1-Unicorn Vet',
    `pig_type`         TINYINT         NOT NULL COMMENT '猪只类型 0-瘦肉型猪 1-脂肪型猪',
    `summary`          MEDIUMTEXT               DEFAULT NULL COMMENT '描述文件内容',
    `total_images`     INT UNSIGNED    NOT NULL COMMENT '总图片数量',
    `uploading_images` INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '正在上传的图片数量',
    `uploaded_images`  INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '已上传完成的图片数量',
    `result`           MEDIUMTEXT               DEFAULT NULL COMMENT '预测结果',
    `status`           TINYINT         NOT NULL DEFAULT 0 COMMENT '预测任务状态 0-INITIAL-初始化 1-PREPARED-数据准备完成 2-QUEUEING-排队中 3-PROCESSING-计算中 4-ACCOMPLISHED-计算完成 5-FAILED-失败 6-REJECTED-拒绝任务',
    `reason`           VARCHAR(64)              DEFAULT NULL COMMENT '失败或拒绝原因',
    `submit_at`        DATETIME        NOT NULL COMMENT '预测任务提交时间',
    `queue_at`         DATETIME                 DEFAULT NULL COMMENT '任务进入队列排队时间',
    `prepared_at`      DATETIME                 DEFAULT NULL COMMENT '任务数据准备完成时间',
    `processing_at`    DATETIME                 DEFAULT NULL COMMENT '任务开始计算时间',
    `completed_at`     DATETIME                 DEFAULT NULL COMMENT '任务完成(计算完成 计算失败 计算拒绝)时间',
    `created_at`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at`       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci COMMENT ='预测任务表';