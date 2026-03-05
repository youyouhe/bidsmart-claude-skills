---
name: bid-material-search
description: >
  基于 MaterialHub API 构建投标资料检索服务（FastAPI），
  支持关键词搜索、分类过滤、文档类型查询，
  并支持自动替换响应文件中的占位符为实际图片引用。
  内部/外部双访问模式（内部优先，外部兜底），图片自动缓存。
  ✨ v2.3+ 使用 MaterialHub 聚合 API，一次性获取公司/人员完整信息（含扩展字段）。
  当用户需要查询投标资料（营业执照、证书、合同、业绩等）、
  启动资料检索服务、或替换响应文件中的【此处插入XX扫描件】占位符时触发。
  前置条件：需 MaterialHub API 服务已运行，材料已通过 MaterialHub 上传。
---

# 投标资料检索服务 (MaterialHub 集成)

## 核心特性 ⭐ v2.3+

### 🚀 MaterialHub 聚合 API 集成

- **公司完整信息** (`/api/companies/{id}/complete`)：
  - 一次性获取公司基本信息、员工列表、所有材料
  - 自动聚合扩展字段：注册资本、成立日期、公司类型、经营范围
  - 包含统计信息（材料数、员工数、过期材料数）

- **人员完整信息** (`/api/persons/{id}/complete`)：
  - 一次性获取人员信息、所属公司、所有材料、证书列表
  - 自动聚合扩展字段：性别、年龄、出生日期、学历、专业、毕业院校
  - 自动提取证书信息（证书编号、有效期、发证机构）

### 📊 结构化数据提取 (`/api/extract`)

为标书编写提供一站式数据获取：
```json
{
  "company": { "name": "...", "credit_code": "..." },
  "license": { "registered_capital": "2001万元", "establishment_date": "2008-04-14" },
  "certificates": [{ "title": "ISO27001", "cert_number": "...", "expiry_date": "..." }],
  "persons": [{
    "name": "张三",
    "gender": "男",
    "age": 35,
    "education": "本科",
    "major": "计算机科学与技术",
    "certificates": [...]
  }]
}
```

### 🔐 认证与连接管理

- **Session-based 认证**：自动 token 管理和过期刷新
- **双地址兜底**：内部 URL 优先，外部 URL 兜底
- **图片缓存**：本地缓存减少重复下载

### 🖼️ 自动水印 (v2.3.1)

- 从 `分析报告.md` 自动提取项目名称
- 为复制的图片自动添加水印（防止材料滥用）
- 支持 Word 文档批量水印处理

## 🚀 使用聚合 API 的优势

### 传统方式 vs 聚合 API

**传统方式**（多次请求）：
```python
# 需要多次API调用
company = client.get("/api/companies/1")
materials = client.get("/api/companies/1/materials")
employees = client.get("/api/persons?company_id=1")

# 手动从materials中提取数据
for material in materials:
    if material["material_type"] == "license":
        # 手动解析 extracted_data...
        registered_capital = material["extracted_data"]["registered_capital"]
```

**聚合 API 方式**（一次请求）⭐：
```python
# 一次调用，获取所有信息！
data = client.get("/api/companies/1/complete")

# 扩展字段已经聚合好
print(data["aggregated_info"]["registered_capital"])  # "2001万元"
print(data["aggregated_info"]["establishment_date"])  # "2008-04-14"
print(data["statistics"]["total_materials"])  # 74
```

**性能对比**：

| 方式 | HTTP 请求 | 响应时间 | 代码行数 | 性能 |
|------|----------|---------|---------|------|
| 传统方式 | 3 + N 次 | ~2000ms | ~50行 | - |
| 聚合 API ⭐ | 1 次 | ~200ms | ~10行 | **~10倍提速** ⚡ |

## 前置条件

**MaterialHub API 服务**：

- **内部访问（优先）**：`http://localhost:8201`
- **外部访问（兜底）**：`http://senseflow.club:3100`

**认证凭据**：通过环境变量配置管理员账户。

**材料数据**：需已通过 MaterialHub Web UI 上传 DOCX 文档并提取材料。

## 启动服务

```bash
# 设置环境变量（可选）
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123

# 启动服务
cd skills/bid-material-search/scripts
uvicorn app:app --host 0.0.0.0 --port 9000
```

## API 端点概览

### 📊 结构化数据提取（推荐）⭐

| 端点 | 说明 |
|------|------|
| `GET /api/extract?company_id=1` ⭐⭐ | **批量提取结构化数据**（标书编写核心功能） |
| `GET /api/companies/{id}/complete` ⭐ | **公司完整信息**（聚合 API，含扩展字段） |
| `GET /api/persons/{id}/complete` ⭐ | **人员完整信息**（聚合 API，含扩展字段和证书） |

### 🔍 图片检索与替换

| 端点 | 说明 |
|------|------|
| `GET /api/search?q=关键词&company_id=1` | 关键词搜索 |
| `POST /api/replace` | 占位符替换 |

### 其他

| 端点 | 说明 |
|------|------|
| `GET /health` | 服务健康检查 |
| `GET /api/companies` | 列出所有公司 |
| `GET /api/persons?company_id=1` | 列出人员 |

## 聚合 API 提供的扩展字段

### 公司扩展字段（从营业执照提取）
- `registered_capital`: 注册资本
- `establishment_date`: 成立日期
- `company_type`: 公司类型
- `business_scope`: 经营范围
- `operating_period`: 营业期限

### 人员扩展字段（从身份证、学历证书提取）
- `gender`: 性别
- `birth_date`: 出生日期
- `age`: 年龄（自动计算）
- `nation`: 民族
- `address`: 住址
- `major`: 专业
- `degree`: 学历
- `university`: 毕业院校
- `graduation_date`: 毕业日期

## 使用示例

### 快速开始

```python
import requests

BASE_URL = "http://localhost:9000"
COMPANY_ID = 1

# 获取公司所有数据（一次API调用）⭐
data = requests.get(
    f"{BASE_URL}/api/extract",
    params={"company_id": COMPANY_ID}
).json()

# 直接使用聚合后的字段
company = data["company"]
license_info = data["license"]

print(f"公司名称: {company['name']}")
print(f"注册资本: {license_info['registered_capital']}")
print(f"成立日期: {license_info['establishment_date']}")

# ISO证书信息
for cert in data['certificates']:
    if 'ISO' in cert['title']:
        print(f"证书: {cert['title']}")
        print(f"证书编号: {cert['cert_number']}")
        print(f"有效期: {cert['expiry_date']}")

# 人员信息（扩展字段已聚合）
for person in data['persons']:
    print(f"{person['name']}: {person['gender']}, {person['age']}岁, {person['education']}")
    for cert in person.get('certificates', []):
        print(f"  - {cert['title']}")
```

### 替换占位符

```bash
curl -X POST http://localhost:9000/api/replace \
  -H 'Content-Type: application/json' \
  -d '{
    "target_file": "/path/to/响应文件/15-营业执照.md",
    "placeholder": "【此处插入营业执照扫描件】",
    "query": "营业执照"
  }'
```

## 版本历史

### v2.3+ ⭐ MaterialHub 聚合 API 集成
- ✨ 使用 MaterialHub 聚合 API (`/complete` 端点)
- 🚀 一次性获取公司/人员完整信息（含扩展字段）
- 📊 自动聚合：注册资本、成立日期、性别、年龄、学历等
- 🎯 优化 `/api/extract` 端点，减少 API 调用次数
- 📈 提升性能：从多次请求优化为单次请求（~10倍提速）

### v2.3.2 - Word文档水印支持
- ✨ 支持为 Word 文档中的图片批量添加水印

### v2.3.1 - 自动水印功能
- ✨ 从分析报告自动提取项目名称
- 🖼️ 图片复制时自动添加水印

### v2.0 - MaterialHub API 集成
- 🔄 完全迁移到 MaterialHub API
- 🔐 Session-based 认证
- 🔄 内部/外部双URL兜底
- 💾 图片本地缓存

## 相关文档

- [OPTIMIZATION_RECOMMENDATIONS.md](OPTIMIZATION_RECOMMENDATIONS.md) - 优化建议和代码质量评估
- [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - 使用示例和最佳实践
- [DATA_EXTRACTION.md](DATA_EXTRACTION.md) - 结构化数据提取详解
- [MaterialHub API 文档](../../MATERIALHUB_API.md) - MaterialHub 完整 API 文档
