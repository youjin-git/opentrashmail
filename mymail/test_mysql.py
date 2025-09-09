#!/usr/bin/env python3
"""
测试MySQL数据库连接和功能
"""

import sys
from email_database import EmailDatabase
from datetime import datetime
import time

def test_mysql_connection():
    """测试MySQL数据库连接和基本功能"""
    print("🧪 开始测试MySQL数据库功能...")
    
    # MySQL连接配置
    mysql_config = {
        'host': '120.27.238.180',
        'port': 3306,
        'database': 'tempmail',
        'user': 'tempmail',
        'password': 'tempmail'
    }
    
    try:
        # 初始化数据库连接
        print("1. 测试数据库连接...")
        db = EmailDatabase(**mysql_config)
        print("✅ 数据库连接和初始化成功")
        
        # 测试基本连接
        print("\n2. 测试数据库操作...")
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == 1:
            print("✅ 数据库查询测试成功")
        else:
            print("❌ 数据库查询测试失败")
            return False
        
        # 测试保存邮件
        print("\n3. 测试保存邮件功能...")
        test_email_data = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'sender_ip': '192.168.1.100',
            'from': 'test@example.com',
            'to': ['user@test.com', 'admin@test.com'],
            'subject': 'MySQL测试邮件',
            'plaintext_body': '这是一封MySQL测试邮件的纯文本内容。\n用于验证数据库存储功能。',
            'html_body': '<p>这是一封<strong>MySQL测试邮件</strong>的HTML内容。</p>',
            'attachments': [
                {'filename': 'test.txt', 'content_type': 'text/plain', 'size': 1234}
            ],
            'raw_size': 5000,
            'raw_content': b'This is raw email content for MySQL testing'
        }
        
        email_id = db.save_email(test_email_data)
        if email_id:
            print(f"✅ 邮件保存成功，ID: {email_id}")
        else:
            print("❌ 邮件保存失败")
            return False
        
        # 测试查询邮件
        print("\n4. 测试查询邮件...")
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
        
        # 测试统计信息
        print("\n5. 测试统计信息...")
        stats = db.get_stats()
        print(f"✅ 统计信息获取成功:")
        print(f"   总邮件数: {stats.get('total_emails', 0)}")
        print(f"   失败邮件数: {stats.get('failed_emails', 0)}")
        print(f"   总附件数: {stats.get('total_attachments', 0)}")
        print(f"   唯一收件人数: {stats.get('unique_recipients', 0)}")
        
        # 测试按收件人查询
        print("\n6. 测试按收件人查询...")
        emails = db.get_emails_by_recipient('user@test.com')
        if emails:
            print(f"✅ 收件人查询成功，找到 {len(emails)} 封邮件")
        else:
            print("❌ 收件人查询失败")
            return False
        
        # 清理测试数据
        print("\n7. 清理测试数据...")
        if db.delete_email(email_id):
            print("✅ 测试邮件删除成功")
        else:
            print("❌ 测试邮件删除失败")
        
        print("\n🎉 所有MySQL数据库测试通过!")
        print(f"🔗 数据库连接信息: {mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}")
        return True
        
    except Exception as e:
        print(f"❌ MySQL测试失败: {e}")
        print("请检查:")
        print("1. MySQL服务器是否可访问")
        print("2. 数据库连接信息是否正确") 
        print("3. 是否安装了mysql-connector-python: pip install mysql-connector-python")
        print("4. 数据库是否已经创建并初始化了表结构")
        return False

def check_mysql_requirements():
    """检查MySQL相关依赖"""
    print("🔍 检查MySQL依赖...")
    
    try:
        import mysql.connector
        print("✅ mysql-connector-python 已安装")
        return True
    except ImportError:
        print("❌ mysql-connector-python 未安装")
        print("请运行: pip install mysql-connector-python")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("MySQL数据库连接测试")
    print("=" * 60)
    
    # 检查依赖
    if not check_mysql_requirements():
        sys.exit(1)
    
    # 运行测试
    success = test_mysql_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试完成 - 所有功能正常")
        print("现在可以启动邮件监听器:")
        print("python3 simple_mail_listener.py")
    else:
        print("❌ 测试失败 - 请检查配置和依赖")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
