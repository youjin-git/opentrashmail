#!/usr/bin/env python3
"""
简单的SMTP邮件监听器 - 用于测试邮件接收功能
基于opentrashmail的核心逻辑简化而来
"""

import asyncio
import logging
import json
import time
import os
from datetime import datetime
from aiosmtpd.controller import Controller
from email.parser import BytesParser
from email.header import decode_header, make_header
from email import policy

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mail_listener.log')
    ]
)
logger = logging.getLogger(__name__)

# 配置参数
SMTP_PORT = 25
ALLOWED_DOMAINS = ["example.com", "test.com", "*.yourdomain.com"]  # 修改为您的域名
ACCEPT_ALL_DOMAINS = False  # 设置为True可接收所有域名的邮件
DATA_DIR = "./mail_data"

class SimpleMailHandler:
    """简化的邮件处理器"""
    
    def __init__(self):
        # 确保数据目录存在
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
            logger.info(f"创建数据目录: {DATA_DIR}")
    
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        """处理收件人验证"""
        logger.info(f"收件人验证: {address}")
        
        # 如果设置为接受所有域名，直接通过
        if ACCEPT_ALL_DOMAINS:
            logger.info(f"✅ 接受所有域名: {address}")
            return '250 OK'
        
        # 检查域名是否被允许
        domain = address.split('@')[1].lower()
        allowed = False
        
        for allowed_domain in ALLOWED_DOMAINS:
            if allowed_domain.startswith("*"):
                # 通配符域名匹配
                suffix = allowed_domain[1:]  # 去掉*
                if domain.endswith(suffix):
                    allowed = True
                    break
            elif domain == allowed_domain:
                allowed = True
                break
        
        if allowed:
            logger.info(f"✅ 接受域名: {domain}")
            return '250 OK'
        else:
            logger.warning(f"❌ 拒绝域名: {domain}")
            return '550 Domain not allowed'
    
    async def handle_DATA(self, server, session, envelope):
        """处理邮件数据"""
        try:
            peer_ip = session.peer[0] if session.peer else "unknown"
            logger.info(f"📧 接收到新邮件 - 来源IP: {peer_ip}")
            logger.info(f"   发送方: {envelope.mail_from}")
            logger.info(f"   收件方: {envelope.rcpt_tos}")
            
            # 解析邮件
            message = BytesParser(policy=policy.default).parsebytes(envelope.content)
            
            # 提取邮件信息
            subject = str(make_header(decode_header(message['subject']))) if message['subject'] else "(无主题)"
            from_addr = message['from'] or envelope.mail_from
            to_addrs = envelope.rcpt_tos
            
            logger.info(f"   主题: {subject}")
            
            # 提取邮件内容
            plaintext_body = ""
            html_body = ""
            attachments = []
            
            for part in message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                
                content_type = part.get_content_type()
                
                if content_type == 'text/plain':
                    try:
                        plaintext_body += part.get_payload(decode=True).decode('utf-8')
                    except UnicodeDecodeError:
                        plaintext_body += part.get_payload(decode=True).decode('latin1', errors='ignore')
                    except Exception as e:
                        logger.warning(f"解码纯文本内容失败: {e}")
                
                elif content_type == 'text/html':
                    try:
                        html_body += part.get_payload(decode=True).decode('utf-8')
                    except UnicodeDecodeError:
                        html_body += part.get_payload(decode=True).decode('latin1', errors='ignore')
                    except Exception as e:
                        logger.warning(f"解码HTML内容失败: {e}")
                
                else:
                    # 处理附件
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': filename,
                            'content_type': content_type,
                            'size': len(part.get_payload(decode=True)) if part.get_payload(decode=True) else 0
                        })
            
            # 构建邮件数据
            email_data = {
                'timestamp': time.time(),
                'datetime': datetime.now().isoformat(),
                'sender_ip': peer_ip,
                'from': from_addr,
                'to': to_addrs,
                'subject': subject,
                'plaintext_body': plaintext_body[:1000] + "..." if len(plaintext_body) > 1000 else plaintext_body,
                'html_body': html_body[:1000] + "..." if len(html_body) > 1000 else html_body,
                'attachments': attachments,
                'raw_size': len(envelope.content)
            }
            
            # 保存邮件数据
            self.save_email_data(email_data)
            
            # 在控制台显示邮件摘要
            self.print_email_summary(email_data)
            
            logger.info("✅ 邮件处理完成")
            return '250 Message accepted for delivery'
            
        except Exception as e:
            logger.error(f"❌ 处理邮件时出错: {e}")
            return '451 Requested action aborted: local error in processing'
    
    def save_email_data(self, email_data):
        """保存邮件数据到文件"""
        try:
            filename = f"email_{int(email_data['timestamp'])}.json"
            filepath = os.path.join(DATA_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(email_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 邮件已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"保存邮件数据失败: {e}")
    
    def print_email_summary(self, email_data):
        """在控制台打印邮件摘要"""
        print("\n" + "="*60)
        print("📬 新邮件摘要")
        print("="*60)
        print(f"时间: {email_data['datetime']}")
        print(f"来源IP: {email_data['sender_ip']}")
        print(f"发送方: {email_data['from']}")
        print(f"收件方: {', '.join(email_data['to'])}")
        print(f"主题: {email_data['subject']}")
        print(f"正文预览: {email_data['plaintext_body'][:100]}...")
        if email_data['attachments']:
            print(f"附件数量: {len(email_data['attachments'])}")
            for att in email_data['attachments']:
                print(f"  - {att['filename']} ({att['size']} bytes)")
        print(f"邮件大小: {email_data['raw_size']} bytes")
        print("="*60 + "\n")

def main():
    """主函数"""
    print("🚀 启动简单SMTP邮件监听器")
    print(f"📂 数据保存目录: {DATA_DIR}")
    print(f"🌐 监听端口: {SMTP_PORT}")
    print(f"🏷️  允许的域名: {ALLOWED_DOMAINS}")
    print("💡 修改脚本开头的配置参数来适配您的需求")
    print("\n" + "="*60)
    
    # 创建邮件处理器
    handler = SimpleMailHandler()
    
    # 创建SMTP控制器
    try:
        controller = Controller(
            handler, 
            hostname='0.0.0.0',  # 监听所有接口
            port=SMTP_PORT
        )
        
        logger.info(f"🎯 启动SMTP服务器，监听 0.0.0.0:{SMTP_PORT}")
        controller.start()
        
        print(f"✅ SMTP服务器已启动")
        print(f"   监听地址: 0.0.0.0:{SMTP_PORT}")
        print(f"   日志文件: mail_listener.log")
        print(f"   按 Ctrl+C 停止服务")
        print("\n🔍 等待邮件...")
        
        # 保持运行
        try:
            while True:
                asyncio.get_event_loop().run_until_complete(asyncio.sleep(1))
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号")
            controller.stop()
            logger.info("SMTP服务器已停止")
            print("✅ 服务已停止")
            
    except PermissionError:
        print(f"❌ 权限不足，无法绑定端口 {SMTP_PORT}")
        print("💡 解决方案:")
        print(f"   1. 使用 sudo 运行: sudo python3 {__file__}")
        print("   2. 或修改 SMTP_PORT 为大于1024的端口")
        
    except Exception as e:
        logger.error(f"启动服务器失败: {e}")
        print(f"❌ 启动失败: {e}")

if __name__ == '__main__':
    main()
