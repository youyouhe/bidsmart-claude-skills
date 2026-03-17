# 网络配置指南

## 架构说明

bid-material-search skill 采用客户端-服务器架构：

```
┌─────────────────┐           网络          ┌──────────────────┐
│  客户端（投标）  │ ──────────────────────> │  服务器（资料库） │
│                 │                         │                  │
│  • Skill 脚本   │   HTTP/HTTPS 请求       │  • MaterialHub   │
│  • 响应文件编写 │   API Token 认证        │  • 材料数据库    │
│  • 图片下载     │                         │  • 图片存储      │
└─────────────────┘                         └──────────────────┘
```

**关键点**：
- MaterialHub API 运行在服务器上（通常是 `http://server-ip:8201`）
- Skill 运行在客户端（投标文件编写的机器上）
- 客户端通过 HTTP/HTTPS + API Token 访问服务器

## 配置步骤

### 1. 服务器端配置

在运行 MaterialHub 的服务器上：

```bash
# 确保 MaterialHub API 已启动
cd /path/to/material-hub
python backend/main.py

# 确认服务运行
curl http://localhost:8201/health
# 应返回：{"status": "healthy"}

# 查看 API Key（从服务器的 .env 文件）
cat .env | grep MATERIALHUB_API_KEY
# 输出：MATERIALHUB_API_KEY=mh-mcp-xxx...
```

**网络配置**：
- 确保防火墙允许端口 8201
- 如果使用云服务器，配置安全组规则
- 推荐使用 HTTPS（通过 Nginx/Caddy 反向代理）

### 2. 客户端配置

在运行 bid skills 的客户端机器上：

#### 方法 A：在 bidsmart-claude-skills 目录配置

```bash
cd /path/to/bidsmart-claude-skills
cp skills/bid-material-search/.env.example .env

# 编辑 .env 文件
vim .env
```

填写：
```bash
MATERIALHUB_API_URL=http://your-server-ip:8201  # 或 https://your-domain.com
MATERIALHUB_API_KEY=mh-mcp-xxx...                # 从服务器复制
```

#### 方法 B：在每个项目目录配置

如果每个投标项目都是独立目录：

```bash
cd /path/to/bid-project
cp /path/to/bidsmart-claude-skills/skills/bid-material-search/.env.example .env

# 编辑配置
vim .env
```

**优先级**：
1. 当前项目目录的 `.env`
2. bidsmart-claude-skills 根目录的 `.env`
3. 环境变量

### 3. 测试连接

```bash
cd /path/to/bidsmart-claude-skills/skills/bid-material-search

# 运行测试
python test_skill.py

# 或直接测试 API
python -c "
import os
from dotenv import load_dotenv
import httpx

load_dotenv()
api_url = os.getenv('MATERIALHUB_API_URL')
api_key = os.getenv('MATERIALHUB_API_KEY')

print(f'API URL: {api_url}')
print(f'API Key: {api_key[:20]}...')

# 测试连接
resp = httpx.get(
    f'{api_url}/health',
    headers={'Authorization': f'Bearer {api_key}'}
)
print(f'Status: {resp.status_code}')
print(f'Response: {resp.json()}')
"
```

## 安全建议

### 1. 使用 HTTPS

在生产环境，建议使用 HTTPS：

```nginx
# Nginx 反向代理配置示例
server {
    listen 443 ssl;
    server_name materials.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8201;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

客户端配置：
```bash
MATERIALHUB_API_URL=https://materials.example.com
```

### 2. 保护 API Key

- **不要**提交 `.env` 文件到 Git
- **不要**在代码中硬编码 API Key
- 使用环境变量或加密的配置管理工具
- 定期轮换 API Key

### 3. 网络隔离

如果可能，使用 VPN 或专用网络：

```bash
# 客户端通过 VPN 连接
# 服务器只监听内网 IP
uvicorn main:app --host 192.168.1.100 --port 8201
```

## 故障排查

### 问题 1：连接超时

```
httpx.ConnectTimeout: ...
```

**原因**：
- 服务器未运行
- 防火墙阻止
- IP/端口错误

**解决**：
```bash
# 在服务器上
netstat -tlnp | grep 8201  # 确认监听
firewall-cmd --list-ports  # 检查防火墙

# 在客户端
ping your-server-ip        # 测试网络
telnet your-server-ip 8201 # 测试端口
```

### 问题 2：401 Unauthorized

```
httpx.HTTPStatusError: 401 Unauthorized
```

**原因**：
- API Key 错误或过期
- 请求头格式错误

**解决**：
```bash
# 检查 API Key
echo $MATERIALHUB_API_KEY

# 手动测试
curl -H "Authorization: Bearer $MATERIALHUB_API_KEY" \
     http://your-server-ip:8201/api/v2/search?q=营业执照
```

### 问题 3：下载图片失败

**原因**：
- 图片 URL 仍然指向 localhost
- 防火墙阻止图片下载

**解决**：
检查 MaterialHub API 返回的图片 URL 格式：
```python
# 应返回完整 URL（而非相对路径）
{
    "thumbnail_url": "http://server-ip:8201/media/thumbnails/xxx.jpg"
}
```

如果返回相对路径，修改 `scripts/replace.py`：
```python
# 自动补全 URL
if image_url.startswith('/'):
    image_url = f"{API_BASE}{image_url}"
```

### 问题 4：代理环境

如果需要通过代理访问：

```bash
# .env 文件
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
NO_PROXY=localhost,127.0.0.1
```

Python 代码会自动使用环境变量中的代理。

## 性能优化

### 1. 图片缓存

客户端下载的图片会保存到本地，避免重复下载：

```python
# scripts/replace.py 自动缓存逻辑
output_image_path = os.path.join(output_dir, f"{safe_title}.png")
if os.path.exists(output_image_path):
    print(f"图片已存在，跳过下载: {output_image_path}")
    return output_image_path
```

### 2. 批量操作

使用批量 API 减少请求次数：

```python
# 推荐：批量搜索
results = search_materials_sync(query="", limit=100)

# 避免：循环单次搜索
for keyword in keywords:
    search_materials_sync(query=keyword)
```

### 3. 超时配置

针对慢速网络，增加超时时间：

```python
# scripts/search.py
async with httpx.AsyncClient(base_url=API_BASE, timeout=60) as client:
    # 增加到 60 秒
```

## 多环境配置

使用不同的配置文件管理多个环境：

```bash
# .env.dev - 开发环境（本地）
MATERIALHUB_API_URL=http://localhost:8201
MATERIALHUB_API_KEY=mh-mcp-dev-key

# .env.prod - 生产环境（远程服务器）
MATERIALHUB_API_URL=https://materials.company.com
MATERIALHUB_API_KEY=mh-mcp-prod-key
```

加载指定环境：
```python
from dotenv import load_dotenv
load_dotenv('.env.prod')
```

## 相关文档

- [SKILL.md](SKILL.md) - Skill 使用文档
- [INTEGRATION.md](INTEGRATION.md) - 与其他 Skills 集成
- [MaterialHub API 文档](../../../backend/README.md)
