# 简单SMTP邮件监听器使用说明

## 功能特性

- ✅ 监听SMTP端口接收邮件
- ✅ 域名验证（支持通配符）
- ✅ 邮件内容解析（纯文本/HTML）
- ✅ 附件信息提取
- ✅ 邮件数据保存为JSON
- ✅ 实时日志记录
- ✅ 控制台邮件摘要显示

## 部署步骤

### 1. 安装依赖
```bash
pip3 install aiosmtpd
```

### 2. 修改配置
编辑 `simple_mail_listener.py` 文件开头的配置：

```python
SMTP_PORT = 25                    # SMTP端口，需要root权限
ALLOWED_DOMAINS = [               # 允许接收的域名
    "example.com", 
    "test.com", 
    "*.yourdomain.com"           # 支持通配符
]
DATA_DIR = "./mail_data"         # 邮件保存目录
```

### 3. 启动服务

**方式一：使用root权限（推荐用于生产环境）**
```bash
sudo python3 simple_mail_listener.py
```

**方式二：使用非特权端口（测试用）**
```python
# 修改脚本中的端口
SMTP_PORT = 2525  # 或其他大于1024的端口
```
```bash
python3 simple_mail_listener.py
```

## DNS配置

要让外部邮件发送到您的服务器，需要配置DNS MX记录：

```
# 示例DNS记录
example.com.        IN  MX  10  mail.example.com.
mail.example.com.   IN  A       YOUR_SERVER_IP
```

## 测试方法

### 1. 本地测试
使用telnet模拟SMTP客户端：

```bash
telnet localhost 25
```

然后输入SMTP命令：
```
HELO test.com
MAIL FROM: sender@test.com
RCPT TO: recipient@example.com
DATA
Subject: Test Email

This is a test message.
.
QUIT
```

### 2. 使用Python发送测试邮件
```python
import smtplib
from email.mime.text import MIMEText

# 创建邮件
msg = MIMEText("这是一封测试邮件")
msg['Subject'] = "测试邮件"
msg['From'] = "sender@test.com"
msg['To'] = "recipient@example.com"

# 发送邮件
with smtplib.SMTP('localhost', 25) as server:
    server.send_message(msg)
```

### 3. 使用外部邮件客户端
配置邮件客户端SMTP服务器为您的服务器IP和端口。

## 输出说明

### 控制台输出
```
📬 新邮件摘要
============================================================
时间: 2024-01-01T12:00:00.000000
来源IP: 192.168.1.100
发送方: sender@test.com
收件方: recipient@example.com
主题: 测试邮件
正文预览: 这是一封测试邮件...
附件数量: 0
邮件大小: 256 bytes
============================================================
```

### 保存的JSON文件
```json
{
  "timestamp": 1704096000.0,
  "datetime": "2024-01-01T12:00:00.000000",
  "sender_ip": "192.168.1.100",
  "from": "sender@test.com",
  "to": ["recipient@example.com"],
  "subject": "测试邮件",
  "plaintext_body": "这是一封测试邮件",
  "html_body": "",
  "attachments": [],
  "raw_size": 256
}
```

## 常见问题

### Q: 端口25被占用或权限不足
**A:** 
- 使用 `sudo` 运行脚本
- 或修改端口为 > 1024 的端口
- 检查防火墙设置

### Q: 收不到外部邮件
**A:** 
1. 检查DNS MX记录是否正确
2. 确认防火墙开放了SMTP端口
3. 检查域名是否在 `ALLOWED_DOMAINS` 列表中

### Q: 邮件内容乱码
**A:** 脚本已处理UTF-8和Latin1编码，如仍有问题请检查原始邮件编码

## 日志文件

- **控制台日志**: 实时显示运行状态
- **文件日志**: `mail_listener.log` 保存详细日志
- **邮件数据**: `./mail_data/` 目录下的JSON文件

## 安全注意事项

1. **生产环境**建议添加更多安全检查
2. **限制接收邮件大小**防止磁盘空间耗尽
3. **定期清理**旧邮件文件
4. **防火墙配置**只开放必要端口

## 扩展功能

可以基于此脚本添加：
- Webhook通知
- 邮件转发
- 垃圾邮件过滤
- Web界面查看
- 数据库存储

---

**提示**: 这是一个简化的测试工具，生产环境使用请参考完整的opentrashmail项目。
