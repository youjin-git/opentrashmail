#!/usr/bin/env python3
"""
邮件发送测试脚本 - 用于测试simple_mail_listener.py
"""

import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_test_email(smtp_host='localhost', smtp_port=25):
    """发送测试邮件"""
    
    print(f"🚀 开始发送测试邮件到 {smtp_host}:{smtp_port}")
    
    try:
        # 创建邮件内容
        msg = MIMEMultipart()
        msg['From'] = 'test@sender.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = f'测试邮件 - {time.strftime("%Y-%m-%d %H:%M:%S")}'
        
        # 添加邮件正文
        body = """
这是一封测试邮件！

邮件内容包括：
- 纯文本内容
- 时间戳：{timestamp}
- 测试目的：验证SMTP监听器功能

如果您看到这封邮件，说明邮件监听器工作正常！
        """.format(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 连接SMTP服务器并发送
        print("📡 连接SMTP服务器...")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.set_debuglevel(1)  # 显示SMTP调试信息
            print("📤 发送邮件...")
            server.send_message(msg)
            print("✅ 邮件发送成功！")
            
    except ConnectionRefusedError:
        print("❌ 连接被拒绝 - 请确保SMTP监听器正在运行")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

def send_html_email(smtp_host='localhost', smtp_port=25):
    """发送HTML格式测试邮件"""
    
    print(f"🚀 发送HTML测试邮件到 {smtp_host}:{smtp_port}")
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = 'html-test@sender.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = f'HTML测试邮件 - {time.strftime("%Y-%m-%d %H:%M:%S")}'
        
        # 纯文本版本
        text = """
HTML测试邮件
============

这是纯文本版本的邮件内容。
时间：{timestamp}
        """.format(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # HTML版本
        html = """
<html>
<head></head>
<body>
    <h2 style="color: #2E86AB;">HTML测试邮件</h2>
    <p>这是一封 <strong>HTML格式</strong> 的测试邮件。</p>
    <ul>
        <li>包含HTML标签</li>
        <li>彩色文字</li>
        <li>格式化内容</li>
    </ul>
    <p style="color: #666;">发送时间：{timestamp}</p>
    <hr>
    <p><em>如果您看到这封邮件，说明HTML邮件解析正常！</em></p>
</body>
</html>
        """.format(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # 添加纯文本和HTML部分
        part1 = MIMEText(text, 'plain', 'utf-8')
        part2 = MIMEText(html, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # 发送邮件
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.send_message(msg)
            print("✅ HTML邮件发送成功！")
            
    except Exception as e:
        print(f"❌ HTML邮件发送失败: {e}")

def test_multiple_recipients(smtp_host='localhost', smtp_port=25):
    """测试多收件人邮件"""
    
    print(f"🚀 发送多收件人测试邮件")
    
    try:
        msg = MIMEText("这是发送给多个收件人的测试邮件", 'plain', 'utf-8')
        msg['From'] = 'multi-test@sender.com'
        msg['To'] = 'user1@example.com, user2@test.com'
        msg['Subject'] = f'多收件人测试 - {time.strftime("%Y-%m-%d %H:%M:%S")}'
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            # 发送给多个收件人
            server.send_message(msg, to_addrs=['user1@example.com', 'user2@test.com'])
            print("✅ 多收件人邮件发送成功！")
            
    except Exception as e:
        print(f"❌ 多收件人邮件发送失败: {e}")

def main():
    """主测试函数"""
    print("📧 SMTP邮件监听器测试工具")
    print("=" * 50)
    
    # 配置SMTP服务器
    smtp_host = input("SMTP服务器地址 (默认: localhost): ").strip() or 'localhost'
    smtp_port_input = input("SMTP端口 (默认: 25): ").strip()
    smtp_port = int(smtp_port_input) if smtp_port_input else 25
    
    print(f"\n🎯 目标服务器: {smtp_host}:{smtp_port}")
    print("=" * 50)
    
    # 运行测试
    tests = [
        ("基础文本邮件", lambda: send_test_email(smtp_host, smtp_port)),
        ("HTML格式邮件", lambda: send_html_email(smtp_host, smtp_port)),
        ("多收件人邮件", lambda: test_multiple_recipients(smtp_host, smtp_port))
    ]
    
    for test_name, test_func in tests:
        print(f"\n🧪 测试: {test_name}")
        print("-" * 30)
        try:
            test_func()
            print("✅ 测试完成")
        except Exception as e:
            print(f"❌ 测试失败: {e}")
        
        # 等待一下再进行下一个测试
        time.sleep(2)
    
    print("\n" + "=" * 50)
    print("🏁 所有测试完成！")
    print("💡 检查邮件监听器的控制台输出和 mail_data/ 目录")

if __name__ == '__main__':
    main()
