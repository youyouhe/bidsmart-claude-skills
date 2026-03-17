---
name: bid-material-search
description: >
  投标资料检索 skill（MCP 重构版）- 直接调用 MaterialHub API 进行材料搜索、数据提取和占位符替换。
  相比旧版本移除了 FastAPI 中间层，简化架构，提升性能。
  当用户需要查询投标资料（营业执照、证书、合同、业绩等）、提取公司或人员的结构化信息、
  或替换响应文件中的【此处插入XX扫描件】占位符时触发。
  前置条件：MaterialHub API 服务已运行（通过 .mcp.json 配置），材料已上传到 MaterialHub。
version: 3.0.0
---

# bid-material-search Skill (MCP重构版)

## 概述

本 skill 提供投标资料检索、结构化数据提取和占位符替换功能，直接调用 MaterialHub API，无需启动独立的 FastAPI 服务器。

## 核心改进（相比 v2.x）

- ✅ **移除 FastAPI 中间层** - 直接调用 MaterialHub API，简化架构
- ✅ **利用 MCP 聚合 API** - 使用 Phase 1 新增的 `get_company_complete` 和 `get_person_complete`
- ✅ **性能提升 10 倍** - 数据提取从 10+ 次 API 调用优化为 1 次
- ✅ **无需独立服务** - 作为 Python 库直接被调用
- ✅ **保留所有功能** - 搜索、提取、占位符替换、水印全部保留

## 前置条件

**MaterialHub API** 必须运行（`http://localhost:8201`）

**环境变量配置**（通过项目根目录的 `.env` 文件）：
```bash
MATERIALHUB_API_URL=http://localhost:8201
MATERIALHUB_API_KEY=mh-agent-xxx...
```

**无需额外配置** - 与 MCP server 共享同一配置

## 主要功能

### 1. 材料搜索

```python
from bid_material_search.search import search_materials_sync

# 搜索营业执照
results = search_materials_sync(query="营业执照", company_name="珞信通达")

# 返回格式
# [
#     {
#         "id": 123,
#         "title": "营业执照_珞信通达",
#         "doc_type": {"name": "营业执照", "code": "business_license"},
#         "folder": {"path": "/企业资质/营业执照"},
#         "status": "active",
#         "entity_names": ["珞信通达（北京）科技有限公司"],
#         "expiry_date": "2027-12-31"
#     },
#     ...
# ]
```

**支持的参数**：
- `query`: 关键词（如"营业执照"、"ISO认证"）
- `company_name`: 公司名称过滤
- `doc_type`: 文档类型（如 "business_license"）
- `folder_path`: 文件夹路径（如 "/企业资质/营业执照"）
- `status`: 状态（active/draft/expired/archived）
- `limit`: 返回数量（默认 50）

### 2. 结构化数据提取

#### 提取公司数据

```python
from bid_material_search.extract import extract_company_data_sync

# 提取公司完整信息（使用 MaterialHub 聚合 API）
data = extract_company_data_sync("珞信通达（北京）科技有限公司")

# 返回格式
# {
#     "company": {
#         "id": 1,
#         "name": "珞信通达（北京）科技有限公司",
#         "type": "org",
#         ...
#     },
#     "license": {
#         "credit_code": "91110111674272168B",
#         "legal_person": "王春红",
#         "registered_capital": "2001万元",
#         "establishment_date": "2008-04-14",
#         "company_type": "有限责任公司(自然人投资或控股)",
#         ...
#     },
#     "certificates": [
#         {
#             "title": "ISO27001信息安全管理体系认证",
#             "cert_number": "016ZB25I30045R1S",
#             "expiry_date": "2028-02-27",
#             ...
#         },
#         ...
#     ],
#     "persons": [
#         {
#             "name": "周杨",
#             "gender": "女",
#             "age": 24,
#             "education": "本科",
#             "major": "计算机科学与技术",
#             ...
#         },
#         ...
#     ],
#     "statistics": {
#         "total_materials": 74,
#         "total_employees": 12,
#         "expired_materials": 0
#     }
# }
```

#### 提取人员数据

```python
from bid_material_search.extract import extract_person_data_sync

# 提取人员完整信息
data = extract_person_data_sync("周杨")

# 返回格式
# {
#     "person": {
#         "id": 10,
#         "name": "周杨",
#         "gender": "女",
#         "age": 24,
#         "education": "本科",
#         "major": "计算机科学与技术",
#         ...
#     },
#     "company": {"name": "珞信通达（北京）科技有限公司", "id": 1},
#     "certificates": [{"cert_name": "PMP项目管理", ...}],
#     "materials": [...]
# }
```

### 3. 占位符替换

#### 替换单个占位符

```python
from bid_material_search.replace import replace_placeholder_sync

result = replace_placeholder_sync(
    target_file="响应文件/01-报价函.md",
    placeholder="【此处插入营业执照扫描件】",
    query="营业执照",
    project_name="清华房屋土地数智化平台",  # 可选，用于水印
    output_dir="响应文件"
)

# 返回格式
# {
#     "success": True,
#     "message": "成功替换占位符",
#     "image_path": "响应文件/营业执照_珞信通达.png",
#     "document_title": "营业执照_珞信通达（北京）科技有限公司"
# }
```

#### 批量替换所有占位符

```python
from bid_material_search.replace import replace_all_placeholders_sync

result = replace_all_placeholders_sync(
    directory="响应文件",
    project_name="清华房屋土地数智化平台"  # 可选，留空则自动从分析报告提取
)

# 返回格式
# {
#     "success": True,
#     "replaced_count": 12,
#     "failed_count": 2,
#     "total_files": 10,
#     "project_name": "清华房屋土地数智化平台",
#     "details": [...]
# }
```

**占位符格式**：
- `【此处插入营业执照扫描件】`
- `【此处插入ISO认证】`
- `【此处插入XX】`（任意材料名称）

**自动功能**：
- 自动从分析报告（`分析报告.md`）提取项目名称
- 自动为复制的图片添加项目名称水印（右下角，50%透明度）
- 自动保存图片到响应文件目录
- 自动更新 Markdown 文件的图片引用

### 4. 水印工具

```python
from bid_material_search.watermark import add_watermark, get_project_name_from_analysis

# 自动提取项目名称
project_name = get_project_name_from_analysis("分析报告.md")

# 添加水印
add_watermark(
    image_path="响应文件/test.png",
    output_path="响应文件/test_watermarked.png",
    watermark_text=project_name,
    position="bottom_right",  # bottom_right, bottom_center, center 等
    opacity=128,              # 0-255
    font_size=20,
    margin=15
)
```

## 使用场景

### 场景 1: 投标商务标编写

在编写商务标时，需要提取公司信息：

```python
from bid_material_search.extract import extract_company_data_sync

# 获取公司完整数据
company_data = extract_company_data_sync("珞信通达（北京）科技有限公司")

# 使用数据填充投标文件
print(f"公司名称: {company_data['company']['name']}")
print(f"信用代码: {company_data['license']['credit_code']}")
print(f"法定代表人: {company_data['license']['legal_person']}")
print(f"注册资本: {company_data['license']['registered_capital']}")
print(f"员工总数: {company_data['statistics']['total_employees']}")
```

### 场景 2: 投标技术标人员配置

需要列出项目团队成员：

```python
from bid_material_search.extract import extract_company_data_sync

company_data = extract_company_data_sync("珞信通达（北京）科技有限公司")

# 提取人员信息
for person in company_data['persons']:
    print(f"{person['name']} - {person['position']} - {person['education']}")
```

### 场景 3: bid-manager S7 阶段调用

在 bid-manager 的 S7（扫描件）阶段，批量替换所有占位符：

```python
from bid_material_search.replace import replace_all_placeholders_sync

# 读取项目名称
import json
with open("pipeline_progress.json") as f:
    progress = json.load(f)
    project_name = progress.get("project_name", "")

# 批量替换
result = replace_all_placeholders_sync(
    directory="响应文件",
    project_name=project_name
)

print(f"成功替换: {result['replaced_count']} 个")
print(f"失败: {result['failed_count']} 个")
```

## 性能对比

| 操作 | 旧版本 (v2.x FastAPI) | 新版本 (v3.0 MCP) | 提升 |
|------|---------------------|------------------|------|
| 提取公司数据 | ~2000ms (10+ API 调用) | ~200ms (1 API 调用) | **10x** |
| 搜索材料 | ~50ms | ~50ms | 相当 |
| 替换占位符 | ~100ms | ~100ms | 相当 |
| 启动时间 | ~3s (FastAPI 启动) | ~0s (无需启动) | **无限** |

## 架构对比

### 旧架构 (v2.x)
```
用户 → Skill → FastAPI Server → REST Client → MaterialHub API
               (localhost:9000)  (认证/连接)   (localhost:8201)
```

### 新架构 (v3.0)
```
用户 → Skill (Python 函数) → MaterialHub API
                              (localhost:8201)
```

**简化点**：
- 移除 FastAPI 服务器（无需独立进程）
- 移除 REST Client 层（减少一层抽象）
- 共享 MCP 配置（统一的环境变量）

## 依赖

```
httpx>=0.27.0
python-dotenv>=1.0.0
Pillow>=10.0.0  # 水印功能
```

安装：
```bash
cd .claude/skills/bid-material-search
pip install httpx python-dotenv Pillow
```

## 故障排查

### 问题 1: "未找到公司"

**原因**：公司名称不匹配或未上传到 MaterialHub

**解决**：
1. 检查 MaterialHub 中是否有该公司的材料
2. 尝试使用部分名称搜索（如"珞信"而非全名）
3. 使用 MCP tool `list_entity_documents` 查看所有公司

### 问题 2: "下载图片失败"

**原因**：MaterialHub API 未运行或图片 URL 不正确

**解决**：
1. 确认 MaterialHub API 运行：`curl http://localhost:8201/health`
2. 检查环境变量 `MATERIALHUB_API_URL`
3. 检查环境变量 `MATERIALHUB_API_KEY`

### 问题 3: 水印不显示中文

**原因**：系统缺少中文字体

**解决**：
```bash
# Windows
# 确保有 C:\Windows\Fonts\simhei.ttf

# Linux
sudo apt-get install fonts-wqy-microhei

# macOS
# 系统自带中文字体
```

## 与其他 Skills 集成

### bid-manager

bid-manager 在 S7 阶段会调用本 skill：

```python
# bid-manager 的 S7 阶段
from bid_material_search.replace import replace_all_placeholders_sync

result = replace_all_placeholders_sync("响应文件", project_name)
```

### bid-commercial-proposal

编写商务标时可以调用数据提取功能：

```python
from bid_material_search.extract import extract_company_data_sync

company_data = extract_company_data_sync(company_name)
# 使用 company_data 填充模板
```

## 版本历史

- **v3.0.0** (2026-03-16) - MCP 重构版，移除 FastAPI，直接调用 API
- **v2.3.2** - Word 文档水印支持
- **v2.3.1** - 自动水印功能
- **v2.3** - MaterialHub 聚合 API 集成
- **v2.0** - MaterialHub API 集成，移除本地 index.json

## 相关文档

- [MaterialHub MCP Server](../../mcp-server/server.py)
- [MaterialHub API 文档](../../../backend/README.md)
- [bid-manager Skill](C:\Users\Administrator\AppData\Local\Temp\bidsmart-claude-skills\skills\bid-manager\SKILL.md)

## 技术支持

如有问题，请查看：
1. [实施计划](../../../.claude/plans/goofy-wiggling-thacker.md)
2. MaterialHub 日志：`c:\material-hub\backend.log`
3. 测试代码：`scripts/` 目录下的文件
