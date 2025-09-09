#!/usr/bin/env python3
"""
测试数据库功能
"""

import os
import sys
from email_database import EmailDatabase
from datetime import datetime
import time

def test_database():
    """测试数据库基本功能"""
    print("🧪 开始测试数据库功能...")
    
    # 使用测试数据库文件
    test_db_path = "./test_emails.db"
    
    # 如果测试数据库存在，删除它
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # 初始化数据库
        print("1. 初始化数据库...")
        db = EmailDatabase(test_db_path)
        print("✅ 数据库初始化成功")
        
        # 测试保存邮件
        print("\n2. 测试保存邮件...")
        test_email_data = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'sender_ip': '192.168.1.100',
            'from': 'test@example.com',
            'to': ['user@test.com', 'admin@test.com'],
            'subject': '测试邮件主题',
            'plaintext_body': '这是一封测试邮件的纯文本内容。\n包含多行文本。',
            'html_body': '<p>这是一封<strong>测试邮件</strong>的HTML内容。</p>',
            'attachments': [
                {'filename': 'test.txt', 'content_type': 'text/plain', 'size': 1234},
                {'filename': 'image.jpg', 'content_type': 'image/jpeg', 'size': 5678}
            ],
            'raw_size': 10000,
            'raw_content': b'This is raw email content for testing purposes'
        }
        
        email_id = db.save_email(test_email_data)
        if email_id:
            print(f"✅ 邮件保存成功，ID: {email_id}")
        else:
            print("❌ 邮件保存失败")
            return False
        
        # 测试查询邮件
        print("\n3. 测试查询邮件...")
        email = db.get_email_by_id(email_id)
        if email:
            print(f"✅ 邮件查询成功")
            print(f"   主题: {email['subject']}")
            print(f"   发件人: {email['mail_from']}")
            print(f"   收件人数量: {len(email.get('recipients', []))}")
            print(f"   附件数量: {len(email.get('attachments', []))}")
        else:
            print("❌ 邮件查询失败")
            return False
        
        # 测试按收件人查询
        print("\n4. 测试按收件人查询...")
        emails = db.get_emails_by_recipient('user@test.com')
        if emails:
            print(f"✅ 收件人查询成功，找到 {len(emails)} 封邮件")
        else:
            print("❌ 收件人查询失败")
            return False
        
        # 测试统计信息
        print("\n5. 测试统计信息...")
        stats = db.get_stats()
        print(f"✅ 统计信息获取成功:")
        print(f"   总邮件数: {stats.get('total_emails', 0)}")
        print(f"   失败邮件数: {stats.get('failed_emails', 0)}")
        print(f"   总附件数: {stats.get('total_attachments', 0)}")
        print(f"   唯一收件人数: {stats.get('unique_recipients', 0)}")
        
        # 测试保存失败邮件
        print("\n6. 测试保存失败邮件...")
        failed_id = db.save_failed_email(
            '192.168.1.200',
            'failed@example.com',
            b'Raw content that failed to parse',
            'Email parsing error: invalid format'
        )
        if failed_id:
            print(f"✅ 失败邮件保存成功，ID: {failed_id}")
        else:
            print("❌ 失败邮件保存失败")
            return False
        
        # 测试删除邮件
        print("\n7. 测试删除邮件...")
        if db.delete_email(email_id):
            print("✅ 邮件删除成功")
        else:
            print("❌ 邮件删除失败")
            return False
        
        print("\n🎉 所有数据库测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    finally:
        # 清理测试数据库
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("🧹 测试数据库已清理")

if __name__ == '__main__':
    success = test_database()
    sys.exit(0 if success else 1)
