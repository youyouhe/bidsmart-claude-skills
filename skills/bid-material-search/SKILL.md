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

你是资料管家——企业资质库的搜索引擎。营业执照、证书、合同、业绩，用户需要什么你就精准找到什么。搜不到 = 占位符留在标书里，搜错了 = 放了别人的证书进去。所以：**关键词精准、结果匹配、替换到位**。

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

### 🚨 服务可用性检测（每次触发本 skill 时必须先执行，不可跳过）

本 skill 与 bid-analysis 依赖的 DocScan 不同：**没有可用的本地回退方案**——材料搜索、扫描件替换等能力完全依赖 MaterialHub API 提供的实际数据（企业资质、证书扫描件），这些数据不存在于工作目录本地文件中，无法像 DocScan 离线时那样"改用 python-docx 本地解析"。因此 MaterialHub 不可用时，本 skill 唯一正确的做法是**明确告知用户当前无法提供该服务**，而不是尝试降级、编造、或跳过检测直接报错。

**检测方法**（在执行任何搜索/提取/替换操作前）：
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8201/health
```
或直接调用一次任意 MCP tool（如 `list_doc_types`），若返回连接错误即视为不可用。

**检测结果的处理**：
- **返回 HTTP 200** → 服务在线，正常执行用户请求的搜索/提取/替换操作
- **连接失败/超时/非 200**（包括本 skill 早期版本文档中提到的 `ImportError`、认证失败等根本无法访问服务的情况）→ **立即停止，明确告知用户**：

  > MaterialHub 服务（`http://localhost:8201`）当前无法访问，本 skill 依赖该服务提供的实际资质材料数据，无法在离线状态下生成或猜测扫描件内容。当前无法完成您要求的材料检索/占位符替换操作。请确认 MaterialHub 服务已启动，或检查 `MATERIALHUB_API_URL`/`MATERIALHUB_API_KEY` 配置后重试。

  **不可**：编造材料数据、留空处理后假装已完成、或在未告知用户的情况下静默跳过占位符替换。占位符留空是可以接受的结果（用户知情后可后续手动处理），但"看起来完成了但其实没有真实数据支撑"是不可接受的。

- **AUTO_MODE（bid-manager S7 阶段调用）下的处理**：不能停下来等待用户交互，但仍必须在完成状态摘要的 `状态` 字段标注 `FAILED`（而非 `SUCCESS`），并在摘要中写明"MaterialHub 服务不可用，本阶段未执行任何替换"，供 bid-manager 决定是否跳过本阶段继续流程（参考 CLAUDE.md"Graceful degradation"原则：可选服务不可用时应跳过并警告，不是静默视为成功）。

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

**🚨 关键原则：搜索命中多个候选材料时，不静默取第一个。**

**前置检查（替换类操作执行前，必须先执行）**：在批量/单个替换占位符前，先确认 `响应文件/` 目录下确实存在待替换的占位符（由 `bid-tech-proposal`/`bid-commercial-proposal` 生成）：

```bash
grep -rl "【此处插入.*扫描件】" 响应文件/*.md 2>/dev/null
```

- **无匹配文件或 `响应文件/` 不存在** → 停止，告知用户："未在 `响应文件/` 下找到扫描件占位符，通常需要先由 `bid-tech-proposal`/`bid-commercial-proposal` 完成编写。是否现在运行对应 skill？"
  - 用户同意 → 调用相应 skill 后继续
  - 用户不同意 → 暂停本次任务
- **AUTO_MODE=true** 时：不可交互等待，直接在完成状态摘要中标注 `FAILED`，说明"未找到扫描件占位符"，交由 bid-manager 处理

`smart_search` 的多级回退策略（同义词、去后缀、关键词展开）越"智能"，越容易在词义模糊时匹配到不止一份材料（如公司改过名、同类证书有多个版本）。放错扫描件到最终投标文件是本 skill 最严重的失败模式（比"没找到"更糟——"没找到"至少占位符还留在文档里提醒有遗漏，放错则是悄悄插入了错误内容）。

#### 替换单个占位符（交互模式，非 AUTO_MODE 时优先使用）

```python
from bid_material_search.replace import replace_placeholder_sync

result = replace_placeholder_sync(
    target_file="响应文件/01-报价函.md",
    placeholder="【此处插入营业执照扫描件】",
    query="营业执照",
    project_name="清华房屋土地数智化平台",  # 可选，用于水印
    output_dir="响应文件",
    auto_mode=False,  # 非 AUTO_MODE 时设为 False，遇到歧义会返回候选列表而非静默替换
)

# 情况1：唯一匹配，直接替换成功
# {
#     "success": True,
#     "message": "成功替换占位符",
#     "image_path": "响应文件/营业执照_珞信通达.png",
#     "document_title": "营业执照_珞信通达（北京）科技有限公司",
#     "ambiguous": False,
#     "expiry_warning": None  # 或过期/临期提示文字
# }

# 情况2：多个匹配，需人工确认——此时向用户展示 candidates，
# 询问用哪一个，再用 replace_placeholder_by_id_sync 传入用户选定的 id 完成替换
# {
#     "success": False,
#     "ambiguous": True,
#     "message": "'营业执照' 匹配到 2 个材料，需人工确认使用哪一个",
#     "candidates": [
#         {"id": 5, "title": "营业执照_珞信通达", "folder": "/企业资质/营业执照", ...},
#         {"id": 12, "title": "营业执照_旧名称", "folder": "/企业资质/营业执照(历史)", ...}
#     ]
# }
```

**遇到 `ambiguous: True` 时的处理方法**：
1. 将 `candidates` 列表（含 title、folder、entity_names、expiry_date）展示给用户
2. 如果候选之间差异明显（如文件夹路径提示一个是"历史"版本），可先用 `browse_folder` MCP tool 查看该文件夹结构辅助判断，但**不得替用户做最终选择**
3. 用户确认后，调用 `replace_placeholder_by_id_sync(target_file=..., placeholder=..., doc_id=用户选定的id, ...)` 完成替换

**过期检查（`expiry_warning` 字段）**：只要材料 `is_expired=True` 或 30 天内到期，返回结果会带上 `expiry_warning` 提示。即使替换本身成功（图片已插入），也必须把这条提示展示给用户，不可因为"success: True"就忽略——过期证书插入投标文件可能导致废标，这是比格式问题更严重的风险。

#### 批量替换所有占位符（AUTO_MODE，由 bid-manager 在 S7 阶段调用）

```python
from bid_material_search.replace import replace_all_placeholders_sync

result = replace_all_placeholders_sync(
    directory="响应文件",
    project_name="清华房屋土地数智化平台",  # 可选，留空则自动从分析报告提取
    auto_mode=True,  # 批量场景不能阻塞等待用户输入，遇到歧义取第一个但标注存疑
)

# 返回格式
# {
#     "success": True,
#     "replaced_count": 12,
#     "failed_count": 2,
#     "ambiguous_count": 3,       # 存疑替换数量（AUTO_MODE下自动选取但未经确认）
#     "expiry_warning_count": 1,  # 过期/临期材料数量
#     "total_files": 10,
#     "details": [...]
# }
```

**⚠️ AUTO_MODE 下的歧义和过期材料不是"已解决"，而是"延后到质检环节"**：`ambiguous_count > 0` 或 `expiry_warning_count > 0` 时，必须在完成状态摘要中明确列出，供 S8 质检（bid-assembly）复核这些存疑替换是否正确、过期材料是否需要更新。不可因为 `replaced_count` 达标就视为完全成功。

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

## 可用的 MaterialHub MCP Tools（Claude 直接调用，不经过 Python 脚本层）

除了上述 Python 函数（供脚本化调用），Claude 在会话中还可以直接调用 MaterialHub 提供的 MCP tools。这些工具与 Python 脚本走的是同一个 MaterialHub 后端，但接口形式不同（MCP tool 返回格式化文本，适合直接阅读；Python 函数返回结构化 dict，适合程序处理）。**遇到 Python 脚本函数无法满足的场景（如需要浏览文件夹结构、查过期清单）时，应优先直接调用对应的 MCP tool，而非在 Python 脚本里重新实现一套。**

| MCP Tool | 用途 | 本 skill 中的适用场景 |
|---|---|---|
| `search_documents` | 全文关键词搜索文档 | 对应 `search.py` 的能力，Python 层已封装 |
| `get_document_detail` | 获取单个文档完整详情 | 对应 `search.py`，Python 层已封装 |
| `get_company_complete` | 一次性获取公司完整信息 | 对应 `extract.py`，Python 层已封装 |
| `get_person_complete` | 一次性获取人员完整信息 | 对应 `extract.py`，Python 层已封装 |
| `list_entity_documents` | 查询某公司/人员关联的全部文档 | 消歧场景：多个候选材料对应不同实体时，用此工具确认哪个实体是当前项目的投标主体 |
| `browse_folder` | 浏览文件夹树/文件夹内文档列表 | 消歧场景：候选材料位于不同文件夹（如"营业执照"与"营业执照(历史版本)"），浏览文件夹结构辅助判断，或不传参数查看整体分类结构 |
| `list_doc_types` | 列出系统所有文档类型分类 | 校验 `search_materials` 的 `doc_type` 参数值是否真实存在，避免凭猜测传入不存在的 code |
| `list_expiring_documents` | 查询即将过期/已过期的文档 | **插入扫描件前的主动检查**：批量替换开始前，先调用一次 `list_expiring_documents(days=30)`，将结果与本次要处理的占位符对应的材料交叉核对，对命中的项在替换时优先提示用户，而不是等 `replace_placeholder` 逐个返回 `expiry_warning` 才发现 |
| `add_document` | 导入文件并创建文档记录 | 不属于本 skill 职责范围——材料入库是 `bid-material-extraction` 的工作，本 skill 只搜索/使用已入库材料，不创建新材料 |

**推荐用法**：批量处理前（`replace_all_placeholders` 调用前），先用 `list_expiring_documents` 做一次全局检查：

```
调用 list_expiring_documents(days=30)
若返回的过期/临期文档标题命中本次待处理的占位符查询词，
在开始批量替换前先向用户展示这批风险材料清单，
询问是否继续使用（可能需要用户先去 MaterialHub 更新材料）或跳过这些占位符。
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

在 bid-manager 的 S7（扫描件）阶段，批量替换所有占位符（AUTO_MODE，不可交互）：

```python
from bid_material_search.replace import replace_all_placeholders_sync

# 读取项目名称
import json
with open("pipeline_progress.json") as f:
    progress = json.load(f)
    project_name = progress.get("project_name", "")

# 批量替换（auto_mode=True：遇到歧义不阻塞，取第一个但标注存疑供质检复核）
result = replace_all_placeholders_sync(
    directory="响应文件",
    project_name=project_name,
    auto_mode=True,
)

print(f"成功替换: {result['replaced_count']} 个")
print(f"失败: {result['failed_count']} 个")
print(f"存疑（歧义未确认）: {result['ambiguous_count']} 个 — 需 S8 质检复核")
print(f"过期/临期材料: {result['expiry_warning_count']} 个 — 需 S8 质检复核")
```

**S7 阶段的完成状态摘要必须包含 `ambiguous_count` 和 `expiry_warning_count`**，供 bid-assembly（S8质检）读取并列入核对报告，不可只汇报 `replaced_count`/`failed_count` 而遗漏这两项存疑指标。

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

## 完成状态

批量替换完成后（bid-manager S7 阶段调用时），输出以下结构化状态摘要：

```
--- BID-MATERIAL-SEARCH COMPLETE ---
处理文件数: {total_files}
成功替换: {replaced_count}
失败: {failed_count}
存疑（AUTO_MODE下歧义未经人工确认）: {ambiguous_count}，需S8质检复核
过期/临期材料: {expiry_warning_count}，需S8质检复核
输出目录: 响应文件/
状态: SUCCESS
--- END ---
```

**若前置的服务可用性检测失败**（MaterialHub 不可访问），改用以下摘要，不可仍标注 `SUCCESS`：

```
--- BID-MATERIAL-SEARCH COMPLETE ---
处理文件数: 0
成功替换: 0
失败: 0
存疑: 0
过期/临期材料: 0
输出目录: 响应文件/
状态: FAILED
失败原因: MaterialHub 服务（http://localhost:8201）不可访问，本阶段未执行任何替换，占位符原样保留
--- END ---
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
