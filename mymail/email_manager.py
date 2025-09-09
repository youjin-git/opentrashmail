#!/usr/bin/env python3
"""
邮件数据库管理工具
用于查询、管理和导出存储在数据库中的邮件
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from email_database import EmailDatabase

def format_email_summary(email):
    """格式化邮件摘要显示"""
    timestamp = datetime.fromtimestamp(email['timestamp'])
    
    # 截断长主题和发件人
    subject = email['subject'][:50] + "..." if len(email['subject']) > 50 else email['subject']
    from_addr = email['mail_from'][:30] + "..." if len(email['mail_from']) > 30 else email['mail_from']
    
    return f"{email['id']:>6} | {timestamp.strftime('%Y-%m-%d %H:%M')} | {from_addr:<32} | {subject}"

def list_emails(db, recipient=None, limit=20, offset=0):
    """列出邮件"""
    print("="*100)
    print("邮件列表")
    print("="*100)
    print(f"{'ID':<6} | {'时间':<16} | {'发件人':<32} | 主题")
    print("-"*100)
    
    if recipient:
        emails = db.get_emails_by_recipient(recipient, limit, offset)
        print(f"收件人: {recipient}")
    else:
        # 获取所有邮件
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT e.*, COUNT(ea.id) as attachment_count
            FROM emails e
            LEFT JOIN email_attachments ea ON e.id = ea.email_id
            GROUP BY e.id
            ORDER BY e.timestamp DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        emails = cursor.fetchall()
        conn.close()
    
    if not emails:
        print("没有找到邮件")
        return
    
    for email in emails:
        print(format_email_summary(email))
    
    print(f"\n显示 {len(emails)} 封邮件 (偏移: {offset})")

def show_email(db, email_id):
    """显示邮件详情"""
    email = db.get_email_by_id(email_id)
    
    if not email:
        print(f"❌ 邮件 ID {email_id} 不存在")
        return
    
    timestamp = datetime.fromtimestamp(email['timestamp'])
    
    print("="*80)
    print(f"邮件详情 - ID: {email['id']}")
    print("="*80)
    print(f"时间: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"发件人: {email['mail_from']}")
    print(f"收件人: {', '.join(email.get('recipients', []))}")
    print(f"主题: {email['subject'] or '(无主题)'}")
    print(f"发送IP: {email['sender_ip']}")
    print(f"邮件大小: {email['raw_size']} 字节")
    
    if email.get('attachments'):
        print(f"附件数量: {len(email['attachments'])}")
        for att in email['attachments']:
            print(f"  - {att['filename']} ({att['size']} 字节, {att['content_type']})")
    
    print("\n" + "-"*50)
    print("纯文本内容:")
    print("-"*50)
    if email['plaintext_body']:
        print(email['plaintext_body'][:1000])
        if len(email['plaintext_body']) > 1000:
            print("...(内容已截断)")
    else:
        print("(无纯文本内容)")
    
    if email['html_body']:
        print("\n" + "-"*50)
        print("HTML内容:")
        print("-"*50)
        print(email['html_body'][:500])
        if len(email['html_body']) > 500:
            print("...(内容已截断)")
    
    print("="*80)

def export_email(db, email_id, format='json'):
    """导出邮件"""
    email = db.get_email_by_id(email_id)
    
    if not email:
        print(f"❌ 邮件 ID {email_id} 不存在")
        return
    
    if format.lower() == 'json':
        # 导出为JSON格式
        export_data = {
            'id': email['id'],
            'timestamp': email['timestamp'],
            'datetime': email['datetime'],
            'sender_ip': email['sender_ip'],
            'from': email['mail_from'],
            'to': email.get('recipients', []),
            'subject': email['subject'],
            'plaintext_body': email['plaintext_body'],
            'html_body': email['html_body'],
            'attachments': email.get('attachments', []),
            'raw_size': email['raw_size']
        }
        
        filename = f"email_{email_id}_{int(email['timestamp'])}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 邮件已导出到: {filename}")
    
    elif format.lower() == 'eml':
        # 导出为EML格式（原始邮件）
        if email['raw_content']:
            filename = f"email_{email_id}_{int(email['timestamp'])}.eml"
            with open(filename, 'wb') as f:
                f.write(email['raw_content'])
            print(f"✅ 原始邮件已导出到: {filename}")
        else:
            print("❌ 该邮件没有原始内容数据")

def show_stats(db):
    """显示统计信息"""
    stats = db.get_stats()
    
    print("="*50)
    print("数据库统计信息")
    print("="*50)
    print(f"总邮件数: {stats.get('total_emails', 0)}")
    print(f"失败邮件数: {stats.get('failed_emails', 0)}")
    print(f"总附件数: {stats.get('total_attachments', 0)}")
    print(f"唯一收件人数: {stats.get('unique_recipients', 0)}")
    
    # 获取最近的邮件
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 最近一封邮件时间
        cursor.execute("SELECT MAX(timestamp) FROM emails")
        latest = cursor.fetchone()[0]
        if latest:
            latest_time = datetime.fromtimestamp(latest)
            print(f"最新邮件: {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 今天的邮件数量
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cursor.execute("SELECT COUNT(*) FROM emails WHERE timestamp >= %s", (today_start.timestamp(),))
        today_count = cursor.fetchone()[0]
        print(f"今天收到: {today_count} 封邮件")
        
        conn.close()
    except Exception as e:
        print(f"获取额外统计信息失败: {e}")
    
    print("="*50)

def search_emails(db, query, field='all'):
    """搜索邮件"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        if field == 'all':
            sql = """
                SELECT e.* FROM emails e
                WHERE e.mail_from LIKE %s OR e.subject LIKE %s 
                OR e.plaintext_body LIKE %s OR e.html_body LIKE %s
                ORDER BY e.timestamp DESC
                LIMIT 50
            """
            params = [f"%{query}%"] * 4
        elif field == 'from':
            sql = "SELECT * FROM emails WHERE mail_from LIKE %s ORDER BY timestamp DESC LIMIT 50"
            params = [f"%{query}%"]
        elif field == 'subject':
            sql = "SELECT * FROM emails WHERE subject LIKE %s ORDER BY timestamp DESC LIMIT 50"
            params = [f"%{query}%"]
        elif field == 'recipient':
            sql = """
                SELECT e.* FROM emails e
                JOIN email_recipients er ON e.id = er.email_id
                WHERE er.recipient_email LIKE %s
                ORDER BY e.timestamp DESC LIMIT 50
            """
            params = [f"%{query}%"]
        else:
            print(f"❌ 不支持的搜索字段: {field}")
            return
        
        cursor.execute(sql, params)
        emails = cursor.fetchall()
        conn.close()
        
        if not emails:
            print(f"没有找到匹配 '{query}' 的邮件")
            return
        
        print(f"搜索结果: '{query}' (字段: {field})")
        print("="*100)
        print(f"{'ID':<6} | {'时间':<16} | {'发件人':<32} | 主题")
        print("-"*100)
        
        for email in emails:
            print(format_email_summary(email))
        
        print(f"\n找到 {len(emails)} 封匹配的邮件")
        
    except Exception as e:
        print(f"❌ 搜索失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='邮件数据库管理工具')
    parser.add_argument('--db', default='./emails.db', help='数据库文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出邮件')
    list_parser.add_argument('--recipient', '-r', help='按收件人筛选')
    list_parser.add_argument('--limit', '-l', type=int, default=20, help='显示数量')
    list_parser.add_argument('--offset', '-o', type=int, default=0, help='偏移量')
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='显示邮件详情')
    show_parser.add_argument('id', type=int, help='邮件ID')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出邮件')
    export_parser.add_argument('id', type=int, help='邮件ID')
    export_parser.add_argument('--format', '-f', choices=['json', 'eml'], default='json', help='导出格式')
    
    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索邮件')
    search_parser.add_argument('query', help='搜索关键词')
    search_parser.add_argument('--field', '-f', choices=['all', 'from', 'subject', 'recipient'], 
                              default='all', help='搜索字段')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 初始化数据库连接
    try:
        db = EmailDatabase(args.db)
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)
    
    # 执行命令
    if args.command == 'list':
        list_emails(db, args.recipient, args.limit, args.offset)
    elif args.command == 'show':
        show_email(db, args.id)
    elif args.command == 'export':
        export_email(db, args.id, args.format)
    elif args.command == 'stats':
        show_stats(db)
    elif args.command == 'search':
        search_emails(db, args.query, args.field)

if __name__ == '__main__':
    main()
