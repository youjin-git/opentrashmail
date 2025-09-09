-- OpenTrashMail 数据库初始化脚本
-- 创建邮件存储的数据库表结构

-- 邮件主表
CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,                    -- Unix时间戳
    datetime TEXT NOT NULL,                     -- ISO格式时间
    sender_ip TEXT,                             -- 发送者IP
    mail_from TEXT NOT NULL,                    -- 发件人邮箱
    subject TEXT,                               -- 邮件主题
    plaintext_body TEXT,                        -- 纯文本正文
    html_body TEXT,                             -- HTML正文
    raw_content BLOB,                           -- 原始邮件内容
    raw_size INTEGER DEFAULT 0,                 -- 原始邮件大小
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_datetime (datetime),
    INDEX idx_mail_from (mail_from)
);

-- 收件人表（一封邮件可能有多个收件人）
CREATE TABLE IF NOT EXISTS email_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    recipient_email TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails (id) ON DELETE CASCADE,
    INDEX idx_email_id (email_id),
    INDEX idx_recipient_email (recipient_email)
);

-- 附件表
CREATE TABLE IF NOT EXISTS email_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    content_type TEXT,
    file_size INTEGER DEFAULT 0,
    file_path TEXT,                             -- 附件存储路径
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails (id) ON DELETE CASCADE,
    INDEX idx_email_id (email_id),
    INDEX idx_filename (filename)
);

-- 邮件解析失败记录表
CREATE TABLE IF NOT EXISTS failed_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    datetime TEXT NOT NULL,
    sender_ip TEXT,
    mail_from TEXT,
    raw_content BLOB,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_mail_from (mail_from)
);

-- 创建用于快速查询某个邮箱收到的邮件的视图
CREATE VIEW IF NOT EXISTS email_summary AS
SELECT 
    e.id,
    e.timestamp,
    e.datetime,
    e.mail_from,
    e.subject,
    e.raw_size,
    GROUP_CONCAT(er.recipient_email) as recipients,
    COUNT(ea.id) as attachment_count
FROM emails e
LEFT JOIN email_recipients er ON e.id = er.email_id
LEFT JOIN email_attachments ea ON e.id = ea.email_id
GROUP BY e.id, e.timestamp, e.datetime, e.mail_from, e.subject, e.raw_size;
