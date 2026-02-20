---
name: bid-material-search
description: >
  基于 MaterialHub API 构建投标资料检索服务（FastAPI），
  支持关键词搜索、分类过滤、文档类型查询，
  并支持自动替换响应文件中的占位符为实际图片引用。
  内部/外部双访问模式（内部优先，外部兜底），图片自动缓存。
  当用户需要查询投标资料（营业执照、证书、合同、业绩等）、
  启动资料检索服务、或替换响应文件中的【此处插入XX扫描件】占位符时触发。
  前置条件：需 MaterialHub API 服务已运行，材料已通过 MaterialHub 上传。
---

# 投标资料检索服务

## 前置条件

**MaterialHub API 服务**：

- **内部访问（优先）**：`http://localhost:8201`
- **外部访问（兜底）**：`http://senseflow.club:3100`

**认证凭据**：通过环境变量配置管理员账户。

**材料数据**：需已通过 MaterialHub Web UI 上传 DOCX 文档并提取材料。

不再需要手动维护 `pages/` 目录和 `index.json` 文件。

## 依赖

- Python: FastAPI, uvicorn, requests

## 环境变量配置

在启动服务前可以设置以下环境变量（可选）：

```bash
# MaterialHub API 地址（可选，有默认值）
export MATERIALHUB_INTERNAL_URL=http://localhost:8201
export MATERIALHUB_EXTERNAL_URL=http://senseflow.club:3100

# MaterialHub 认证（可选，未设置时会提示输入）
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123

# 图片缓存目录（可选，默认 .cache）
export MATERIALHUB_CACHE_DIR=.cache
```

**注意**：如果未设置 `MATERIALHUB_USERNAME` 或 `MATERIALHUB_PASSWORD`，
服务启动时会提示用户输入用户名和密码。

## 启动服务

核心脚本：`scripts/app.py`（依赖 `scripts/materialhub_client.py`）

确保 MaterialHub API 服务已运行，然后启动本服务：

### 方式 1：交互式启动（推荐）

直接启动，服务会提示输入用户名和密码：

```bash
cd skills/bid-material-search/scripts
uvicorn app:app --host 0.0.0.0 --port 9000
```

启动时会看到提示：

```
============================================================
MaterialHub 认证
============================================================
用户名 [默认: admin]: admin
密码: ********
============================================================
```

### 方式 2：环境变量（适合自动化）

预先设置环境变量，跳过交互式输入：

```bash
# 设置环境变量
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123

# 启动服务
cd skills/bid-material-search/scripts
uvicorn app:app --host 0.0.0.0 --port 9000
```

服务启动后会自动尝试连接 MaterialHub API（内部优先，外部兜底）。
连接失败会记录警告，但服务仍会启动（返回空结果）。

## API 端点

### 图片检索与替换

| 端点 | 说明 |
|------|------|
| `GET /api/search?q=关键词` | 关键词搜索（匹配 type+label+section+ocr_text） |
| `GET /api/search?company_id=1` | 按公司ID过滤（v2.1） |
| `GET /api/search?company_name=公司名` | 按公司名称过滤（v2.1，模糊匹配） |
| `GET /api/search?category=分类` | 按分类过滤（资质证明/业绩证明/基本文件等） |
| `GET /api/search?type=类型` | 按文档类型过滤 |
| `GET /api/documents` | 列出所有文档 |
| `GET /api/documents/{id}` | 单个文档详情 |
| `POST /api/replace` | 占位符替换（搜索+复制图片+替换markdown） |

### 结构化数据提取（v2.2）⭐

| 端点 | 说明 |
|------|------|
| `GET /api/companies` | 列出所有公司 |
| `GET /api/companies/{id}/details` | 获取公司详情（包含所有材料和extracted_data） |
| `GET /api/persons?company_id=1` | 列出人员（可按公司过滤） |
| `GET /api/persons/{id}/details` | 获取人员详情（包含身份证、学历证书等） |
| `GET /api/materials/{id}/details` | 获取材料详情（包含完整extracted_data和ocr_text） |
| `GET /api/extract?company_id=1` | **批量提取结构化数据**（标书编写核心功能） |

### 其他

| 端点 | 说明 |
|------|------|
| `GET /health` | 服务健康检查 |

返回格式：

```json
{
  "results": [
    {
      "id": "mat_11",
      "section": "",
      "type": "营业执照",
      "category": "资质证明",
      "label": "营业执照",
      "page_range": [],
      "source": "materialhub",
      "images": [
        {"filename": "营业执照.png", "url": "/api/materials/11/image"}
      ],
      "_material_id": 11
    }
  ]
}
```

## 多公司场景（v2.1）

当 MaterialHub 中存储多个公司的材料时，需要明确指定查询哪个公司的资料。

### 查询可用公司

```bash
curl "http://localhost:9000/api/companies"
```

**响应示例**：
```json
{
  "companies": [
    {
      "id": 1,
      "name": "珞信通达（北京）科技有限公司",
      "material_count": 74
    },
    {
      "id": 2,
      "name": "王春红",
      "material_count": 2
    }
  ]
}
```

### 按公司搜索材料

**方式1：通过公司ID（精确）**

```bash
# 查询公司1的营业执照
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"
```

**方式2：通过公司名称（模糊匹配）**

```bash
# 通过名称关键词查询
curl "http://localhost:9000/api/search?q=营业执照&company_name=琪信通达"
```

系统会自动模糊匹配公司名称。

**方式3：列出公司所有材料**

```bash
# 不带关键词，列出公司1的所有材料
curl "http://localhost:9000/api/search?company_id=1"
```

**组合过滤示例**：

```bash
# 查询公司1的所有资质证明
curl "http://localhost:9000/api/search?company_id=1&category=资质证明"

# 查询公司1的ISO认证
curl "http://localhost:9000/api/search?q=ISO&company_id=1&category=资质证明"
```

详见：`COMPANY_FILTER.md`

## 结构化数据提取（v2.2）⭐

MaterialHub 通过 OCR + LLM 从材料图片中提取了结构化数据，存储在 `extracted_data` 字段中。

### 用途

为标书编写提供结构化信息，无需手动输入：

- **营业执照**：注册资本、成立日期、公司类型、经营范围
- **身份证**：性别、出生日期、民族、住址
- **ISO证书**：证书编号、有效期、认证机构、认证范围
- **学历证书**：学历、专业、毕业时间
- **合同业绩**：合同金额、合同日期、客户名称

### 核心端点：批量提取

`GET /api/extract?company_id=1`

一次性获取公司的所有结构化数据：

**响应结构**：

```json
{
  "company": {
    "name": "珞信通达（北京）科技有限公司",
    "legal_person": "王春红",
    "credit_code": "91110111674272168B"
  },
  "license": {
    "registered_capital": "2001万元",
    "establishment_date": "2008-04-14",
    "company_type": "有限责任公司(自然人投资或控股)",
    "ocr_text": "原始OCR文本（备用）"
  },
  "certificates": [
    {
      "title": "ISO27001信息安全管理体系认证",
      "cert_number": "016ZB25I30045R1S",
      "expiry_date": "2028-02-27",
      "issue_authority": "BCC Inc."
    }
  ],
  "persons": [
    {
      "name": "周杨",
      "id_number": "411023200112043047",
      "materials": {
        "id_card": [{
          "extracted_data": {
            "gender": "女",
            "birth_date": "2001-12-04",
            "nation": "汉"
          }
        }]
      }
    }
  ]
}
```

### 使用示例

```bash
# 获取公司1的所有结构化数据
curl "http://localhost:9000/api/extract?company_id=1"

# 只获取营业执照和ISO证书
curl "http://localhost:9000/api/extract?company_id=1&material_types=license,iso_cert"
```

### Python示例

```python
import requests

# 获取数据
response = requests.get(
    "http://localhost:9000/api/extract",
    params={"company_id": 1}
)
data = response.json()

# 提取需要的字段
print(f"公司名称: {data['company']['name']}")
print(f"注册资本: {data['license']['registered_capital']}")
print(f"成立日期: {data['license']['establishment_date']}")

# ISO证书信息
for cert in data['certificates']:
    if 'ISO' in cert['title']:
        print(f"证书名称: {cert['title']}")
        print(f"证书编号: {cert['cert_number']}")
        print(f"有效期: {cert['expiry_date']}")

# 法人信息
legal_person = data['company']['legal_person']
for person in data['persons']:
    if person['name'] == legal_person:
        id_card = person['materials']['id_card'][0]['extracted_data']
        print(f"法人性别: {id_card['gender']}")
        print(f"法人出生日期: {id_card['birth_date']}")
        break
```

### 数据完整性

- ✅ **extracted_data存在**：直接使用提取的字段
- ⚠️ **extracted_data为null**：使用 `ocr_text` 字段（包含原始OCR文本）

详见：`DATA_EXTRACTION.md`

## 材料管理

### 上传新材料

通过 MaterialHub Web UI 上传 DOCX 文档，系统自动提取图片并创建材料记录。

### 更新材料信息

通过 MaterialHub Web UI 编辑材料元数据（标题、分类、有效期等）。

### 搜索能力

搜索由 MaterialHub API 提供，支持：
- 全文搜索（OCR 识别文本）
- 标题/章节关键词匹配
- 分类过滤
- 有效期过滤

## 占位符替换

`POST /api/replace` 端点可自动将响应文件中的 `【此处插入XX扫描件】` 占位符替换为实际图片引用。

### 参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `target_file` | string | 是 | markdown 文件绝对路径 |
| `placeholder` | string | 是 | 要替换的占位符文本 |
| `doc_id` | string | 否 | 精确文档 ID（优先使用） |
| `query` | string | 否 | 模糊搜索关键词（doc_id 未提供时使用，取第一个匹配） |

`doc_id` 和 `query` 至少提供一个。

### 替换流程

1. 根据 `doc_id` 或 `query` 查找匹配文档
2. 读取目标文件，确认占位符存在
3. 将 `pages/` 下的图片复制到目标文件所在目录
4. 将占位符替换为 `![label](filename)` 格式的 markdown 图片引用
5. 写回文件

### 调用示例

```bash
# 通过 query 模糊匹配
curl -X POST localhost:9000/api/replace \
  -H 'Content-Type: application/json' \
  -d '{"target_file":"/path/to/响应文件/26-企业营业执照副本.md","placeholder":"【此处插入企业营业执照副本扫描件】","query":"营业执照"}'

# 通过 doc_id 精确指定
curl -X POST localhost:9000/api/replace \
  -H 'Content-Type: application/json' \
  -d '{"target_file":"/path/to/file.md","placeholder":"【此处插入ISO认证扫描件】","doc_id":"sec_10_5_ISO认证"}'
```

### 返回格式

```json
{
  "success": true,
  "replaced": "【此处插入企业营业执照副本扫描件】",
  "doc_id": "sec_10_1_营业执照",
  "doc_label": "10.1 营业执照",
  "images_copied": ["10_1_营业执照.jpeg"],
  "target_file": "/path/to/响应文件/26-企业营业执照副本.md"
}
```

### Claude 工作流中的典型用法

在编写响应文件时，遇到需要插入扫描件的占位符，可直接调用替换端点：

```python
import requests
requests.post("http://localhost:9000/api/replace", json={
    "target_file": "/abs/path/to/响应文件/26-企业营业执照副本.md",
    "placeholder": "【此处插入企业营业执照副本扫描件】",
    "query": "营业执照"
})
```

替换后图片文件会复制到目标 markdown 文件的同级目录，无需手动移动。

## 批量替换模式

当被 bid-manager 调度或用户要求批量替换时，自动扫描 `响应文件/` 目录下所有 `.md` 文件中的扫描件占位符，逐个匹配并替换。

### 工作流程

1. **扫描占位符**：遍历 `响应文件/` 下所有 `.md` 文件，提取所有 `【此处插入XX扫描件】` 格式的占位符
2. **逐个匹配**：对每个占位符，从占位符文字中提取关键词，调用搜索 API 查找匹配文档
3. **自动替换**：找到匹配后调用 `/api/replace` 端点完成替换
4. **记录结果**：
   - ✅ 成功替换：占位符 → 图片引用
   - ⚠️ 多个匹配：列出候选，标记为需人工确认
   - ❌ 无匹配：保留原占位符，列入未匹配清单

### 调用方式

```bash
# 批量替换所有扫描件占位符
curl -X POST localhost:9000/api/batch-replace \
  -H 'Content-Type: application/json' \
  -d '{"target_dir": "/home/tiger/bid/响应文件"}'
```

或由 Claude 直接执行：

```python
import os, requests

resp_dir = "/home/tiger/bid/响应文件"
for fname in os.listdir(resp_dir):
    if not fname.endswith('.md'):
        continue
    fpath = os.path.join(resp_dir, fname)
    content = open(fpath).read()
    import re
    placeholders = re.findall(r'【此处插入(.+?)扫描件】', content)
    for ph in placeholders:
        requests.post("http://localhost:9000/api/replace", json={
            "target_file": fpath,
            "placeholder": f"【此处插入{ph}扫描件】",
            "query": ph.strip()
        })
```

## 典型查询示例

```bash
# 搜索某人相关资料
curl "localhost:9000/api/search?q=张三"

# 查看所有资质证明
curl "localhost:9000/api/search?category=资质证明"

# 查找合同类文件
curl "localhost:9000/api/search?q=合同"

# 查找ISO认证
curl "localhost:9000/api/search?q=ISO"
```

## 故障排查

### 连接失败

**症状**：启动日志显示 "MaterialHub API unavailable"

**解决方法**：
1. 检查 MaterialHub 服务是否运行：
   ```bash
   curl http://localhost:8201/health
   ```
2. 检查网络连接（如使用外部地址）
3. 验证环境变量配置是否正确

### 认证失败

**症状**：搜索返回空结果，日志显示 "Login failed"

**解决方法**：
1. 验证用户名密码：
   ```bash
   curl -X POST http://localhost:8201/api/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"admin","password":"admin123"}'
   ```
2. 检查 MaterialHub 管理员账户是否被禁用
3. 查看 MaterialHub 服务日志

### 图片下载失败

**症状**：替换操作返回 500 错误 "Failed to download image"

**解决方法**：
1. 检查 material_id 是否存在
2. 检查 MaterialHub 图片文件是否损坏
3. 清空缓存目录后重试：
   ```bash
   rm -rf .cache/
   ```

### 服务健康检查

```bash
curl http://localhost:9000/health
```

预期返回：
```json
{
  "status": "healthy",
  "materialhub_connected": true,
  "materialhub_url": "http://localhost:8201"
}
```

## 完成状态

替换完成后，输出以下结构化状态摘要：

```
--- BID-MATERIAL-SEARCH COMPLETE ---
扫描文件数: {N}
发现占位符: {N}
✅成功替换: {N}
⚠️需人工确认: {N}（MaterialHub 返回多个匹配）
❌无匹配: {N}（MaterialHub 中未找到）
复制图片数: {N}
缓存命中率: {N}%
MaterialHub 连接: {internal/external/failed}
输出目录: 响应文件/
状态: SUCCESS
--- END ---
```
