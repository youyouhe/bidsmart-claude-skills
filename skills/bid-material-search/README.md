# bid-material-search Skill v3.0.0

投标资料检索 skill - MCP 重构版

## 概述

本 skill 从 FastAPI 架构重构为直接调用 MaterialHub API 的纯 Python 库，消除了中间层，提升了性能和可维护性。

## 目录结构

```
bid-material-search/
├── SKILL.md                # Skill 定义和使用文档
├── README.md               # 本文件
├── INTEGRATION.md          # 与 bid-manager 的集成指南
├── test_skill.py           # 测试脚本
├── scripts/
│   ├── __init__.py        # 包初始化
│   ├── search.py          # 材料搜索功能
│   ├── extract.py         # 结构化数据提取
│   ├── replace.py         # 占位符替换
│   └── watermark.py       # 水印工具
```

## 快速开始

### 1. 环境准备

确保 MaterialHub API 正在运行：
```bash
curl http://localhost:8201/health
```

确保环境变量已配置（项目根目录 `.env` 文件）：
```
MATERIALHUB_API_URL=http://localhost:8201
MATERIALHUB_API_KEY=mh-agent-xxx...
```

### 2. 安装依赖

```bash
pip install httpx python-dotenv Pillow
```

### 3. 基本使用

```python
import sys
sys.path.insert(0, "c:/material-hub/.claude/skills/bid-material-search/scripts")

# 搜索材料
from search import search_materials_sync
results = search_materials_sync(query="营业执照", company_name="珞信通达")

# 提取公司数据
from extract import extract_company_data_sync
data = extract_company_data_sync("珞信通达（北京）科技有限公司")

# 替换占位符
from replace import replace_all_placeholders_sync
result = replace_all_placeholders_sync("响应文件", "项目名称")
```

### 4. 运行测试

```bash
cd c:/material-hub/.claude/skills/bid-material-search
python test_skill.py
```

## 架构变化

### 旧架构 (v2.x)

```
用户请求
  ↓
Skill 调用
  ↓
HTTP POST → FastAPI Server (localhost:9000)
  ↓
MaterialHubClient (REST API wrapper)
  ↓
HTTP requests → MaterialHub API (localhost:8201)
  ↓
响应
```

**问题**：
- 需要启动 FastAPI 服务（耗时 ~3秒）
- 增加了一层 HTTP 开销
- 需要独立的认证和连接管理
- 服务可能启动失败或崩溃

### 新架构 (v3.0)

```
用户请求
  ↓
Skill 函数调用 (Python import)
  ↓
直接 HTTP requests → MaterialHub API (localhost:8201)
  ↓
响应
```

**优势**：
- 无需启动服务（0秒）
- 减少一层抽象
- 共享 MCP 配置
- 更简单的错误处理

## 性能对比

| 操作 | v2.x (FastAPI) | v3.0 (Direct API) | 提升 |
|------|---------------|-------------------|------|
| 启动时间 | ~3秒 | 0秒 | 无限 |
| 提取公司数据 | ~2秒 (10+ API 调用) | ~200ms (1 API 调用) | **10x** |
| 搜索材料 | ~50ms | ~50ms | 相当 |
| 替换占位符 | ~100ms/个 | ~100ms/个 | 相当 |
| 批量替换10个 | ~4秒 (含启动) | ~1秒 | **4x** |

## 核心功能

### 1. 材料搜索 (search.py)

提供灵活的材料搜索功能：

**函数**：
- `search_materials(query, company_name, doc_type, folder_path, status, limit)` - 异步
- `search_materials_sync(...)` - 同步版本
- `get_document_detail(document_id)` - 获取文档详情
- `get_document_detail_sync(document_id)` - 同步版本

**示例**：
```python
# 按关键词搜索
results = search_materials_sync(query="营业执照")

# 按公司名称搜索
results = search_materials_sync(company_name="珞信通达")

# 组合搜索
results = search_materials_sync(
    query="ISO认证",
    company_name="珞信通达",
    status="active",
    limit=10
)
```

### 2. 数据提取 (extract.py)

使用 MaterialHub 聚合 API 高效提取数据：

**函数**：
- `extract_company_data(company_name)` - 异步
- `extract_company_data_sync(company_name)` - 同步
- `extract_person_data(person_name)` - 异步
- `extract_person_data_sync(person_name)` - 同步

**示例**：
```python
# 提取公司数据（1次API调用获取所有信息）
data = extract_company_data_sync("珞信通达（北京）科技有限公司")

# 访问数据
print(data['company']['name'])              # 公司名称
print(data['license']['credit_code'])       # 统一社会信用代码
print(data['license']['registered_capital']) # 注册资本
print(data['statistics']['total_employees']) # 员工总数
print(len(data['persons']))                  # 员工列表
print(len(data['certificates']))             # 证书列表
```

### 3. 占位符替换 (replace.py)

自动扫描 Markdown 文件并替换占位符：

**函数**：
- `replace_placeholder(target_file, placeholder, query, project_name, output_dir)` - 异步
- `replace_placeholder_sync(...)` - 同步
- `replace_all_placeholders(directory, project_name)` - 异步
- `replace_all_placeholders_sync(...)` - 同步

**占位符格式**：
- `【此处插入营业执照扫描件】`
- `【此处插入ISO认证】`
- `【此处插入XX】`

**示例**：
```python
# 批量替换（自动扫描所有 .md 文件）
result = replace_all_placeholders_sync("响应文件", "项目名称")

print(f"成功: {result['replaced_count']}")
print(f"失败: {result['failed_count']}")
```

**自动功能**：
- 自动从 `分析报告.md` 提取项目名称
- 自动下载图片
- 自动添加水印（50%透明度，右下角）
- 自动更新 Markdown 引用

### 4. 水印工具 (watermark.py)

为图片添加项目名称水印：

**函数**：
- `add_watermark(image_path, output_path, watermark_text, ...)`
- `get_project_name_from_analysis(analysis_path)`
- `add_watermark_batch(image_dir, ...)`

**示例**：
```python
# 添加水印
add_watermark(
    "test.png",
    "test_watermarked.png",
    watermark_text="清华房屋土地数智化平台",
    position="bottom_right",
    opacity=128
)
```

## 与 MCP Server 的关系

本 skill 利用了 Phase 1 中扩展的 MCP tools：

### 新增的 MCP Tools

1. **`get_company_complete`** ([mcp-server/server.py:645-738](c:\material-hub\mcp-server\server.py#L645))
   - 一次性获取公司的完整信息
   - 包含：基本信息、营业执照、员工、材料、统计
   - 替代了原来的 10+ 次 API 调用

2. **`get_person_complete`** ([mcp-server/server.py:745-848](c:\material-hub\mcp-server\server.py#L745))
   - 一次性获取人员的完整信息
   - 包含：基本信息、所属公司、材料、证书

### Skill vs MCP Tool

| 功能 | MCP Tool | Skill 实现 | 说明 |
|------|----------|-----------|------|
| 搜索材料 | ✓ `search_documents` | ✓ `search.py` | Skill 封装为 Python 函数 |
| 获取详情 | ✓ `get_document_detail` | ✓ `search.py` | Skill 封装为 Python 函数 |
| 提取公司数据 | ✓ `get_company_complete` | ✓ `extract.py` | Skill 解析和格式化 |
| 提取人员数据 | ✓ `get_person_complete` | ✓ `extract.py` | Skill 解析和格式化 |
| 占位符替换 | ✗ | ✓ `replace.py` | Skill 独有（复杂操作） |
| 水印 | ✗ | ✓ `watermark.py` | Skill 独有（图像处理） |

**为什么不全部用 MCP？**

- MCP tools 返回格式化文本（适合 LLM 阅读）
- Skill 返回结构化数据（适合编程使用）
- 占位符替换涉及文件操作、图像处理，不适合 MCP

## 集成到 bid-manager

详见 [INTEGRATION.md](INTEGRATION.md)

简要步骤：

```python
# 在 bid-manager 的 S7 阶段
import sys
sys.path.insert(0, "c:/material-hub/.claude/skills/bid-material-search/scripts")
from replace import replace_all_placeholders_sync

result = replace_all_placeholders_sync("响应文件", project_name)
```

## 测试

### 运行完整测试套件

```bash
cd c:/material-hub/.claude/skills/bid-material-search
python test_skill.py
```

测试包括：
1. ✓ 材料搜索
2. ✓ 文档详情获取
3. ✓ 公司数据提取
4. ✓ 占位符替换
5. ✓ 水印提取

### 单独测试某个功能

```python
# 测试搜索
python -c "
import sys
sys.path.insert(0, 'scripts')
from search import search_materials_sync
results = search_materials_sync(query='营业执照', limit=3)
for r in results:
    print(f'- {r[\"title\"]}')
"

# 测试数据提取
python -c "
import sys
sys.path.insert(0, 'scripts')
from extract import extract_company_data_sync
data = extract_company_data_sync('珞信通达')
print(f'公司: {data[\"company\"][\"name\"]}')
print(f'员工: {len(data.get(\"persons\", []))}')
"
```

## 故障排查

### MaterialHub API 连接失败

```bash
# 检查服务状态
curl http://localhost:8201/health

# 检查环境变量
cat c:/material-hub/.env | grep MATERIALHUB

# 重启 MaterialHub
cd c:/material-hub
bash start.sh
```

### 未找到材料

```bash
# 使用 MCP tool 检查
# 在 Claude Code 中：搜索 "营业执照"

# 或使用 Python
python -c "
import sys
sys.path.insert(0, 'scripts')
from search import search_materials_sync
results = search_materials_sync(query='', limit=10)  # 列出所有材料
for r in results:
    print(f'{r[\"id\"]}: {r[\"title\"]}')
"
```

### ImportError

确保 Python 路径正确：
```python
import sys
import os

# 方法 1: 相对路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

# 方法 2: 绝对路径
sys.path.insert(0, "c:/material-hub/.claude/skills/bid-material-search/scripts")
```

## 版本历史

### v3.0.0 (2026-03-16) - MCP 重构版

**重大变更**：
- 移除 FastAPI 服务器
- 直接调用 MaterialHub API
- 利用新的 MCP 聚合 tools
- 性能提升 10 倍（数据提取）

**新功能**：
- 同步版本的所有函数（`*_sync`）
- 完整的测试套件
- 集成指南

**迁移指南**：
- 旧版本：`requests.post("http://localhost:9000/api/replace", ...)`
- 新版本：`replace_all_placeholders_sync("响应文件", project_name)`

### v2.3.2 - Word 文档水印

- 添加 Word 文档水印支持

### v2.3.1 - 自动水印

- 自动从分析报告提取项目名称
- 自动添加水印到复制的图片

### v2.3 - MaterialHub 聚合 API

- 使用 `/api/companies/{id}/complete`
- 使用 `/api/persons/{id}/complete`

### v2.0 - MaterialHub 集成

- 移除本地 `pages/` 和 `index.json`
- 使用 MaterialHub REST API
- Session 认证

## 相关文档

- [SKILL.md](SKILL.md) - 使用文档
- [INTEGRATION.md](INTEGRATION.md) - 集成指南
- [实施计划](../../plans/goofy-wiggling-thacker.md)
- [MCP Server](../../mcp-server/server.py)

## 贡献

本 skill 是 MaterialHub 项目的一部分。

## License

与 MaterialHub 项目保持一致。
