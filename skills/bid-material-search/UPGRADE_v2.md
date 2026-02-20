# bid-material-search v2.0 升级说明

## 升级概述

bid-material-search skill 已从本地文件系统模式升级为 MaterialHub API 集成模式（v2.0）。

### 主要变更

**之前 (v1.0)**：
- 基于本地 `pages/` 目录和 `index.json` 文件
- 需要手动维护索引和图片文件
- 静态文件服务

**现在 (v2.0)**：
- 基于 MaterialHub API（集中化材料管理）
- 自动 OCR 识别和数据提取
- 内部/外部双访问模式
- 图片自动缓存
- 保持向后兼容（现有 skills 无需修改）

## 新增功能

1. **智能连接**：内部 URL 优先，外部 URL 兜底
2. **自动认证**：Session-based 认证，自动 token 刷新
3. **图片缓存**：首次下载后本地缓存，提升性能
4. **容错机制**：MaterialHub 不可用时返回空结果，服务继续运行
5. **健康检查**：新增 `/health` 端点，实时监控连接状态

## 环境配置

### 认证方式

服务支持两种认证方式：

**方式 1：交互式输入（推荐）**

启动服务时会提示输入用户名和密码：

```bash
cd skills/bid-material-search/scripts
uvicorn app:app --host 0.0.0.0 --port 9000

# 启动时会提示：
# ============================================================
# MaterialHub 认证
# ============================================================
# 用户名 [默认: admin]: admin
# 密码: ********
# ============================================================
```

**方式 2：环境变量（适合自动化）**

预先设置环境变量，跳过交互式输入：

```bash
# MaterialHub API 地址（可选，有默认值）
export MATERIALHUB_INTERNAL_URL=http://localhost:8201
export MATERIALHUB_EXTERNAL_URL=http://senseflow.club:3100

# MaterialHub 认证
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123

# 图片缓存目录（可选）
export MATERIALHUB_CACHE_DIR=.cache
```

### 配置文件（可选）

对于自动化场景，可以创建 `.env` 文件：

```bash
MATERIALHUB_INTERNAL_URL=http://localhost:8201
MATERIALHUB_EXTERNAL_URL=http://senseflow.club:3100
MATERIALHUB_USERNAME=admin
MATERIALHUB_PASSWORD=admin123
MATERIALHUB_CACHE_DIR=.cache
```

加载配置：

```bash
source .env
```

## 启动服务

### 前置条件

1. 确保 MaterialHub API 服务运行：
   ```bash
   curl http://localhost:8201/health
   # 期望: {"status":"healthy","service":"MaterialHub"}
   ```

2. 已上传材料到 MaterialHub（通过 Web UI）

### 启动步骤

**交互式启动**：

```bash
# 1. 进入 scripts 目录
cd skills/bid-material-search/scripts

# 2. 启动服务（会提示输入用户名密码）
uvicorn app:app --host 0.0.0.0 --port 9000
```

**或使用环境变量启动**：

```bash
# 1. 进入 scripts 目录
cd skills/bid-material-search/scripts

# 2. 设置环境变量
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123

# 3. 启动服务
uvicorn app:app --host 0.0.0.0 --port 9000
```

### 验证运行

```bash
# 健康检查
curl http://localhost:9000/health

# 期望返回:
# {
#   "status": "healthy",
#   "materialhub_connected": true,
#   "materialhub_url": "http://localhost:8201"
# }
```

## 快速测试

运行集成测试脚本：

```bash
cd skills/bid-material-search/scripts

# 设置环境变量
export MATERIALHUB_INTERNAL_URL=http://localhost:8201
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123

# 运行测试
python3 test_integration.py
```

测试脚本会验证：
- MaterialHub API 连接
- 登录认证
- 材料搜索
- bid-material-search 服务状态

## API 端点变更

### 保持兼容的端点

以下端点接口不变，其他 skills 无需修改：

- `GET /api/search?q=关键词` - 搜索材料
- `POST /api/replace` - 替换占位符
- `GET /api/documents` - 列出所有材料
- `GET /api/documents/{doc_id}` - 获取单个材料

### 新增端点

- `GET /health` - 服务健康检查

### 数据格式变更

**doc_id 格式**：
- 之前：`sec_10_1_营业执照`（基于章节编号）
- 现在：`mat_123`（基于 MaterialHub material_id）

**图片引用**：
- 之前：`/pages/10_1_营业执照.jpeg`
- 现在：`/api/materials/123/image`（MaterialHub 端点）

## 迁移指南

### 从 v1.0 迁移到 v2.0

1. **保留旧版本**（可选）：
   ```bash
   cp scripts/app.py scripts/app.py.v1.backup
   ```

2. **更新代码**：
   - 新增 `scripts/materialhub_client.py`
   - 更新 `scripts/app.py`
   - 更新 `SKILL.md`

3. **配置环境变量**：
   ```bash
   export MATERIALHUB_INTERNAL_URL=http://localhost:8201
   export MATERIALHUB_USERNAME=admin
   export MATERIALHUB_PASSWORD=admin123
   ```

4. **上传材料到 MaterialHub**：
   - 访问 MaterialHub Web UI
   - 上传 DOCX 文档
   - 等待 OCR 处理完成

5. **启动服务并测试**：
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 9000
   python3 test_integration.py
   ```

### 回滚到 v1.0

如果遇到问题需要回滚：

```bash
cd skills/bid-material-search/scripts

# 恢复旧版本
cp app.py.v1.backup app.py

# 删除新模块
rm materialhub_client.py

# 重启服务
uvicorn app:app --host 0.0.0.0 --port 9000
```

## 故障排查

### 问题 1: 服务启动报错 "No module named 'requests'"

**解决**：
```bash
pip install requests
```

### 问题 2: 日志显示 "MaterialHub API unavailable"

**原因**：MaterialHub 服务未运行或不可访问

**解决**：
1. 检查 MaterialHub 服务：
   ```bash
   curl http://localhost:8201/health
   ```
2. 检查防火墙/网络
3. 验证环境变量配置

### 问题 3: 搜索返回空结果

**可能原因**：
1. MaterialHub 中没有上传材料
2. 认证失败
3. 搜索关键词不匹配

**解决**：
```bash
# 1. 检查连接状态
curl http://localhost:9000/health

# 2. 手动测试 MaterialHub 搜索
TOKEN=$(curl -s -X POST http://localhost:8201/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.token')

curl -s http://localhost:8201/api/materials \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.results | length'
```

### 问题 4: 图片下载失败

**原因**：MaterialHub 图片不存在或损坏

**解决**：
1. 检查 MaterialHub 中的材料：
   ```bash
   curl -s http://localhost:8201/api/materials/{material_id} \
     -H "Authorization: Bearer $TOKEN"
   ```
2. 清空缓存重试：
   ```bash
   rm -rf .cache/
   ```

## 性能优化

### 缓存策略

图片首次下载后缓存到本地 `.cache/` 目录：

```
.cache/
├── material_1.png
├── material_2.png
└── ...
```

**缓存命中率**：通常 80%+ （同一材料重复使用）

**缓存清理**：

```bash
# 清空所有缓存
rm -rf skills/bid-material-search/scripts/.cache/

# 清空特定材料缓存
rm skills/bid-material-search/scripts/.cache/material_123.png
```

### 连接复用

客户端使用 `requests.Session()`，自动复用 TCP 连接，减少握手开销。

## 后续计划

v2.1 可能增强：

1. **请求重试**：MaterialHub API 调用失败时自动重试
2. **缓存 TTL**：添加缓存过期时间
3. **批量下载**：实现 `/api/batch-replace` 端点
4. **高级搜索**：按材料类型、有效期、公司 ID 过滤

## 技术支持

- 项目文档：`SKILL.md`
- API 文档：`MATERIALHUB_API.md`
- 问题反馈：GitHub Issues

## 版本历史

### v2.0.0 (2026-02-20)

- ✨ 集成 MaterialHub API
- 🔄 内部/外部双访问模式
- 💾 图片自动缓存
- 🔐 Session-based 认证
- 🏥 健康检查端点
- 🛡️ 容错机制
- 📖 向后兼容

### v1.0.0 (2026-01-15)

- 🎉 初始版本
- 📁 本地文件系统模式
- 🔍 关键词搜索
- 📝 占位符替换
