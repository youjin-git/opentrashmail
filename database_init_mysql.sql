-- OpenTrashMail MySQL数据库初始化脚本
-- 创建邮件存储的数据库表结构

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建数据库（如果需要）
-- CREATE DATABASE IF NOT EXISTS tempmail DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE tempmail;

-- 邮件主表
DROP TABLE IF EXISTS `emails`;
CREATE TABLE `emails` (
    `id` int NOT NULL AUTO_INCREMENT,
    `timestamp` decimal(15,6) NOT NULL COMMENT '时间戳',
    `datetime` varchar(32) NOT NULL COMMENT 'ISO格式时间',
    `sender_ip` varchar(45) DEFAULT NULL COMMENT '发送者IP',
    `mail_from` varchar(255) NOT NULL COMMENT '发件人邮箱',
    `subject` text COMMENT '邮件主题',
    `plaintext_body` longtext COMMENT '纯文本正文',
    `html_body` longtext COMMENT 'HTML正文',
    `raw_content` longblob COMMENT '原始邮件内容',
    `raw_size` int DEFAULT '0' COMMENT '原始邮件大小',
    `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_timestamp` (`timestamp`),
    KEY `idx_datetime` (`datetime`),
    KEY `idx_mail_from` (`mail_from`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='邮件主表';

-- 收件人表（一封邮件可能有多个收件人）
DROP TABLE IF EXISTS `email_recipients`;
CREATE TABLE `email_recipients` (
    `id` int NOT NULL AUTO_INCREMENT,
    `email_id` int NOT NULL COMMENT '邮件ID',
    `recipient_email` varchar(255) NOT NULL COMMENT '收件人邮箱',
    `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_email_id` (`email_id`),
    KEY `idx_recipient_email` (`recipient_email`),
    CONSTRAINT `fk_recipients_email_id` FOREIGN KEY (`email_id`) REFERENCES `emails` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='邮件收件人表';

-- 附件表
DROP TABLE IF EXISTS `email_attachments`;
CREATE TABLE `email_attachments` (
    `id` int NOT NULL AUTO_INCREMENT,
    `email_id` int NOT NULL COMMENT '邮件ID',
    `filename` varchar(255) NOT NULL COMMENT '附件文件名',
    `content_type` varchar(100) DEFAULT NULL COMMENT '文件类型',
    `file_size` int DEFAULT '0' COMMENT '文件大小（字节）',
    `file_path` varchar(500) DEFAULT NULL COMMENT '附件存储路径',
    `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_email_id` (`email_id`),
    KEY `idx_filename` (`filename`),
    CONSTRAINT `fk_attachments_email_id` FOREIGN KEY (`email_id`) REFERENCES `emails` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='邮件附件表';

-- 邮件解析失败记录表
DROP TABLE IF EXISTS `failed_emails`;
CREATE TABLE `failed_emails` (
    `id` int NOT NULL AUTO_INCREMENT,
    `timestamp` decimal(15,6) NOT NULL COMMENT '时间戳',
    `datetime` varchar(32) NOT NULL COMMENT 'ISO格式时间',
    `sender_ip` varchar(45) DEFAULT NULL COMMENT '发送者IP',
    `mail_from` varchar(255) DEFAULT NULL COMMENT '发件人邮箱',
    `raw_content` longblob COMMENT '原始邮件内容',
    `error_message` text COMMENT '错误信息',
    `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_timestamp` (`timestamp`),
    KEY `idx_mail_from` (`mail_from`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='解析失败邮件记录表';

-- 创建用于快速查询某个邮箱收到的邮件的视图
DROP VIEW IF EXISTS `email_summary`;
CREATE VIEW `email_summary` AS
SELECT 
    e.id,
    e.timestamp,
    e.datetime,
    e.mail_from,
    e.subject,
    e.raw_size,
    GROUP_CONCAT(er.recipient_email SEPARATOR ',') as recipients,
    COUNT(DISTINCT ea.id) as attachment_count
FROM emails e
LEFT JOIN email_recipients er ON e.id = er.email_id
LEFT JOIN email_attachments ea ON e.id = ea.email_id
GROUP BY e.id, e.timestamp, e.datetime, e.mail_from, e.subject, e.raw_size;

SET FOREIGN_KEY_CHECKS = 1;
