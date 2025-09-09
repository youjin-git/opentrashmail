#!/usr/bin/env python3
"""
邮件数据库操作类
用于将接收到的邮件存储到SQLite数据库中
"""

import mysql.connector
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailDatabase:
    """邮件数据库操作类"""
    
    def __init__(self, host: str = "localhost", port: int = 3306, 
                 database: str = "tempmail", user: str = "root", password: str = ""):
        """
        初始化数据库连接
        
        Args:
            host: MySQL服务器地址
            port: MySQL端口
            database: 数据库名
            user: 用户名
            password: 密码
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        return mysql.connector.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
    
    def init_database(self):
        """初始化数据库，创建必要的表"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 创建邮件主表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DECIMAL(15,6) NOT NULL,
                    datetime VARCHAR(32) NOT NULL,
                    sender_ip VARCHAR(45),
                    mail_from VARCHAR(255) NOT NULL,
                    subject TEXT,
                    plaintext_body LONGTEXT,
                    html_body LONGTEXT,
                    raw_content LONGBLOB,
                    raw_size INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_datetime (datetime),
                    INDEX idx_mail_from (mail_from(100))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建收件人表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_recipients (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email_id INT NOT NULL,
                    recipient_email VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (email_id) REFERENCES emails (id) ON DELETE CASCADE,
                    INDEX idx_email_id (email_id),
                    INDEX idx_recipient_email (recipient_email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建附件表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_attachments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email_id INT NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    content_type VARCHAR(100),
                    file_size INT DEFAULT 0,
                    file_path VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (email_id) REFERENCES emails (id) ON DELETE CASCADE,
                    INDEX idx_email_id (email_id),
                    INDEX idx_filename (filename)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # 创建失败邮件记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS failed_emails (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DECIMAL(15,6) NOT NULL,
                    datetime VARCHAR(32) NOT NULL,
                    sender_ip VARCHAR(45),
                    mail_from VARCHAR(255),
                    raw_content LONGBLOB,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_mail_from (mail_from(100))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # MySQL表已包含索引定义，无需单独创建
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 数据库初始化成功: {self.host}:{self.port}/{self.database}")
            
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise
    
    def save_email(self, email_data: Dict[str, Any]) -> Optional[int]:
        """
        保存邮件到数据库
        
        Args:
            email_data: 邮件数据字典
            
        Returns:
            保存成功返回邮件ID，失败返回None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 插入邮件主记录
            cursor.execute("""
                INSERT INTO emails (
                    timestamp, datetime, sender_ip, mail_from, subject,
                    plaintext_body, html_body, raw_content, raw_size
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                email_data.get('timestamp'),
                email_data.get('datetime'),
                email_data.get('sender_ip'),
                email_data.get('from'),
                email_data.get('subject'),
                email_data.get('plaintext_body'),
                email_data.get('html_body'),
                email_data.get('raw_content'),  # 原始邮件内容
                email_data.get('raw_size', 0)
            ))
            
            email_id = cursor.lastrowid
            
            # 插入收件人记录
            recipients = email_data.get('to', [])
            if isinstance(recipients, str):
                recipients = [recipients]
            
            for recipient in recipients:
                cursor.execute("""
                    INSERT INTO email_recipients (email_id, recipient_email)
                    VALUES (%s, %s)
                """, (email_id, recipient))
            
            # 插入附件记录
            attachments = email_data.get('attachments', [])
            for attachment in attachments:
                cursor.execute("""
                    INSERT INTO email_attachments (
                        email_id, filename, content_type, file_size
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    email_id,
                    attachment.get('filename'),
                    attachment.get('content_type'),
                    attachment.get('size', 0)
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 邮件已保存到数据库，ID: {email_id}")
            return email_id
            
        except Exception as e:
            logger.error(f"❌ 保存邮件到数据库失败: {e}")
            return None
    
    def save_failed_email(self, sender_ip: str, mail_from: str, 
                         raw_content: bytes, error_message: str) -> Optional[int]:
        """
        保存解析失败的邮件
        
        Args:
            sender_ip: 发送者IP
            mail_from: 发件人
            raw_content: 原始邮件内容
            error_message: 错误信息
            
        Returns:
            保存成功返回记录ID，失败返回None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now()
            timestamp = now.timestamp()
            datetime_str = now.isoformat()
            
            cursor.execute("""
                INSERT INTO failed_emails (
                    timestamp, datetime, sender_ip, mail_from, 
                    raw_content, error_message
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                timestamp,
                datetime_str,
                sender_ip,
                mail_from,
                raw_content,
                error_message
            ))
            
            record_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ 失败邮件已保存到数据库，ID: {record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"❌ 保存失败邮件到数据库失败: {e}")
            return None
    
    def get_emails_by_recipient(self, recipient_email: str, 
                               limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        根据收件人邮箱查询邮件
        
        Args:
            recipient_email: 收件人邮箱
            limit: 限制返回数量
            offset: 偏移量
            
        Returns:
            邮件列表
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)  # 使结果可以按列名访问
            
            cursor.execute("""
                SELECT e.*, GROUP_CONCAT(er.recipient_email) as recipients,
                       COUNT(ea.id) as attachment_count
                FROM emails e
                LEFT JOIN email_recipients er ON e.id = er.email_id
                LEFT JOIN email_attachments ea ON e.id = ea.email_id
                WHERE e.id IN (
                    SELECT DISTINCT email_id FROM email_recipients 
                    WHERE recipient_email = %s
                )
                GROUP BY e.id
                ORDER BY e.timestamp DESC
                LIMIT %s OFFSET %s
            """, (recipient_email, limit, offset))
            
            rows = cursor.fetchall()
            conn.close()
            
            # MySQL connector已返回字典格式
            return rows
            
        except Exception as e:
            logger.error(f"❌ 查询邮件失败: {e}")
            return []
    
    def get_email_by_id(self, email_id: int) -> Optional[Dict]:
        """
        根据ID获取邮件详情
        
        Args:
            email_id: 邮件ID
            
        Returns:
            邮件详情字典，不存在返回None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # 获取邮件基本信息
            cursor.execute("SELECT * FROM emails WHERE id = %s", (email_id,))
            email = cursor.fetchone()
            
            if not email:
                conn.close()
                return None
            
            email_dict = email
            
            # 获取收件人列表
            cursor.execute("""
                SELECT recipient_email FROM email_recipients 
                WHERE email_id = %s
            """, (email_id,))
            recipients = [row[0] for row in cursor.fetchall()]
            email_dict['recipients'] = recipients
            
            # 获取附件列表
            cursor.execute("""
                SELECT filename, content_type, file_size 
                FROM email_attachments 
                WHERE email_id = %s
            """, (email_id,))
            attachments = []
            for row in cursor.fetchall():
                attachments.append({
                    'filename': row[0],
                    'content_type': row[1],
                    'size': row[2]
                })
            email_dict['attachments'] = attachments
            
            conn.close()
            return email_dict
            
        except Exception as e:
            logger.error(f"❌ 获取邮件详情失败: {e}")
            return None
    
    def delete_email(self, email_id: int) -> bool:
        """
        删除邮件（级联删除相关记录）
        
        Args:
            email_id: 邮件ID
            
        Returns:
            删除成功返回True，失败返回False
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM emails WHERE id = %s", (email_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                logger.info(f"✅ 邮件 {email_id} 已删除")
                return True
            else:
                conn.close()
                logger.warning(f"⚠️ 邮件 {email_id} 不存在")
                return False
                
        except Exception as e:
            logger.error(f"❌ 删除邮件失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # 总邮件数
            cursor.execute("SELECT COUNT(*) FROM emails")
            stats['total_emails'] = cursor.fetchone()[0]
            
            # 失败邮件数
            cursor.execute("SELECT COUNT(*) FROM failed_emails")
            stats['failed_emails'] = cursor.fetchone()[0]
            
            # 总附件数
            cursor.execute("SELECT COUNT(*) FROM email_attachments")
            stats['total_attachments'] = cursor.fetchone()[0]
            
            # 唯一收件人数
            cursor.execute("SELECT COUNT(DISTINCT recipient_email) FROM email_recipients")
            stats['unique_recipients'] = cursor.fetchone()[0]
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {}
