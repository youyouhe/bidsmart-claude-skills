# 安装和配置指南

## 快速安装

### 1. 克隆仓库

```bash
git clone https://github.com/youyouhe/bidsmart-claude-skills.git
cd bidsmart-claude-skills
```

### 2. 安装依赖

```bash
pip install httpx python-dotenv Pillow
```

### 3. 配置 MaterialHub 连接

创建 `.env` 文件在项目根目录：

```bash
# 本地开发（MaterialHub 在本机）
MATERIALHUB_API_URL=http://localhost:8201
MATERIALHUB_API_KEY=mh-mcp-xxx...

# 远程服务器（MaterialHub 在远程机器）
MATERIALHUB_API_URL=http://192.168.1.100:8201
MATERIALHUB_API_KEY=mh-mcp-xxx...

# 或使用 HTTPS
MATERIALHUB_API_URL=https://materials.company.com
MATERIALHUB_API_KEY=mh-mcp-xxx...
```

**获取 API Key**：从运行 MaterialHub 的服务器上的 `.env` 文件中复制 `MATERIALHUB_API_KEY`。

### 4. 测试连接

```bash
cd skills/bid-material-search
python test_skill.py
```

## 服务器端配置

如果你还没有运行 MaterialHub API，需要先在服务器上配置：

### 1. 克隆 MaterialHub

```bash
git clone https://github.com/youyouhe/material-hub.git
cd material-hub
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动 API

```bash
python backend/main.py
```

API 将运行在 `http://localhost:8201`。

### 4. 配置防火墙（如需远程访问）

```bash
# Ubuntu/Debian
sudo ufw allow 8201/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8201/tcp
sudo firewall-cmd --reload
```

### 5. 配置 HTTPS（推荐生产环境）

使用 Nginx 作为反向代理：

```nginx
server {
    listen 443 ssl;
    server_name materials.company.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8201;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 增加超时时间（处理大文件上传）
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

## 使用场景

### 场景 1: 本地开发

MaterialHub 和 bid skills 都在同一台机器上：

```bash
# .env
MATERIALHUB_API_URL=http://localhost:8201
MATERIALHUB_API_KEY=mh-mcp-dev-key
```

### 场景 2: 团队协作（局域网）

MaterialHub 在服务器上，多个团队成员的机器访问：

```bash
# 服务器 IP: 192.168.1.100
# 客户端 .env
MATERIALHUB_API_URL=http://192.168.1.100:8201
MATERIALHUB_API_KEY=mh-mcp-shared-key
```

### 场景 3: 生产环境（公网）

MaterialHub 部署在云服务器，使用域名 + HTTPS：

```bash
# 客户端 .env
MATERIALHUB_API_URL=https://materials.company.com
MATERIALHUB_API_KEY=mh-mcp-prod-key
```

## 与其他 Skills 集成

### bid-manager

bid-manager 会在 S7 阶段自动调用 bid-material-search：

```python
# bid-manager/scripts/stage_07_scans.py
from bid_material_search.replace import replace_all_placeholders_sync

result = replace_all_placeholders_sync("响应文件", project_name)
```

### bid-commercial-proposal

编写商务标时提取公司数据：

```python
# bid-commercial-proposal/scripts/write_commercial.py
from bid_material_search.extract import extract_company_data_sync

company_data = extract_company_data_sync("珞信通达（北京）科技有限公司")
```

## 故障排查

### 问题 1: ImportError: No module named 'config'

**原因**：Python 路径配置问题

**解决**：
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
```

### 问题 2: 连接超时

```
httpx.ConnectTimeout: ...
```

**检查清单**：
1. ✅ MaterialHub API 是否运行
   ```bash
   curl http://server-ip:8201/health
   ```

2. ✅ 防火墙是否开放端口
   ```bash
   # 服务器端
   sudo ufw status | grep 8201
   ```

3. ✅ 网络连通性
   ```bash
   # 客户端
   ping server-ip
   telnet server-ip 8201
   ```

### 问题 3: 401 Unauthorized

**原因**：API Key 错误或过期

**解决**：
1. 检查 API Key 是否正确复制
2. 确认服务器的 `.env` 文件中有该 Key
3. 检查请求头格式：`Authorization: Bearer mh-mcp-xxx...`

### 问题 4: 图片下载失败

**原因**：图片 URL 是相对路径，无法从客户端访问

**检查**：
```python
# scripts/replace.py
# 确保图片 URL 是完整的 HTTP(S) URL
if image_url.startswith('/'):
    image_url = f"{API_BASE}{image_url}"
```

## 多环境管理

使用不同的 `.env` 文件管理多个环境：

```bash
# 项目结构
bidsmart-claude-skills/
├── .env.dev          # 开发环境
├── .env.staging      # 测试环境
├── .env.production   # 生产环境
└── skills/
    └── bid-material-search/
```

切换环境：
```bash
# 开发环境
cp .env.dev .env

# 生产环境
cp .env.production .env
```

或使用环境变量：
```bash
# Linux/macOS
export MATERIALHUB_API_URL=http://prod-server:8201
export MATERIALHUB_API_KEY=mh-mcp-prod-key

# Windows
set MATERIALHUB_API_URL=http://prod-server:8201
set MATERIALHUB_API_KEY=mh-mcp-prod-key
```

## 性能优化

### 1. 使用图片缓存

客户端下载的图片会自动缓存，避免重复下载：

```python
# 图片保存到 响应文件/ 目录后，下次直接使用
output_image_path = "响应文件/营业执照_珞信通达.png"
if os.path.exists(output_image_path):
    # 跳过下载
    pass
```

### 2. 批量操作

减少 API 调用次数：

```python
# 推荐：一次获取所有数据
company_data = extract_company_data_sync("珞信通达")
# 包含：company, license, certificates, persons, statistics

# 避免：多次单独调用
# license = get_license()
# certificates = list_certificates()
# persons = list_persons()
```

### 3. 增加超时时间

针对慢速网络：

```python
# scripts/config.py 或各个模块
async with httpx.AsyncClient(base_url=API_BASE, timeout=60) as client:
    # 超时时间增加到 60 秒
```

## 安全建议

1. **不要提交 `.env` 文件到 Git**
   ```bash
   # .gitignore
   .env
   .env.*
   !.env.example
   ```

2. **使用 HTTPS**（生产环境）
   - 通过 Let's Encrypt 获取免费证书
   - 配置 Nginx/Caddy 反向代理

3. **限制 API Key 权限**
   - 为不同用户/团队生成不同的 API Key
   - 定期轮换 API Key

4. **使用 VPN 或专用网络**
   - 避免在公网暴露 MaterialHub API
   - 使用 VPN 连接内网资源

## 升级指南

### 从 v2.x 升级到 v3.0

1. **移除旧的 FastAPI 服务器**
   ```bash
   # 不再需要启动独立服务
   # python -m bid_material_search.server  # ← 删除
   ```

2. **更新导入路径**
   ```python
   # 旧版本
   # import requests
   # resp = requests.get("http://localhost:9000/search")

   # 新版本
   from bid_material_search.search import search_materials_sync
   results = search_materials_sync(query="营业执照")
   ```

3. **更新配置**
   ```bash
   # 旧版本 .env
   # BID_MATERIAL_SEARCH_API=http://localhost:9000  # ← 删除

   # 新版本 .env
   MATERIALHUB_API_URL=http://localhost:8201
   MATERIALHUB_API_KEY=mh-mcp-xxx...
   ```

## 相关文档

- [SKILL.md](SKILL.md) - Skill 使用文档
- [NETWORK_CONFIG.md](NETWORK_CONFIG.md) - 详细网络配置
- [INTEGRATION.md](INTEGRATION.md) - 与其他 Skills 集成
- [MaterialHub API 文档](https://github.com/youyouhe/material-hub)
