# 结构化数据提取功能

## 功能概述

bid-material-search v2.2 新增**结构化数据提取**功能，为标书编写提供完整的公司、人员、证书等信息。

**版本**: v2.2.0
**发布日期**: 2026-02-21
**解决问题**: 标书编写时需要营业执照的注册资本、法人的性别年龄、ISO证书编号等结构化数据

---

## 业务场景

### 问题描述

编写标书时，AI需要填写大量结构化信息：

```
方案A：您直接提供关键信息（推荐）

最快最准确的方式。请提供以下信息：

1. 王春红（法定代表人）
   - 性别：
   - 职务：
   - 身份证号：
   - 联系电话：

2. 公司信息（从营业执照）
   - 注册资本：
   - 成立日期：
   - 营业期限：

3. ISO证书（5个）
   每个证书需要：
   - 证书编号：
   - 有效期：
   - 认证机构：
```

**问题**：MaterialHub中存储了这些数据（通过OCR+LLM提取），但之前只能获取图片，无法直接获取结构化字段。

### 解决方案

通过新增的API端点，一次性获取公司的所有结构化数据：

```bash
GET /api/extract?company_id=1
```

返回完整的投标数据包：公司信息、法人信息、证书列表、人员列表等。

---

## 数据存储结构

MaterialHub采用三层数据存储架构：

### 1️⃣ Material.extracted_data（完整OCR结果）

存储LLM提取的完整JSON结构：

```json
{
  "material_type": "license",
  "confidence": 0.98,
  "extracted_data": {
    "company_name": "珞信通达（北京）科技有限公司",
    "registered_capital": "2001万元",
    "establishment_date": "2008-04-14",
    "company_type": "有限责任公司(自然人投资或控股)",
    "credit_code": "91110111674272168B"
  },
  "summary": "..."
}
```

### 2️⃣ Company表（核心字段）

从extracted_data自动提取到结构化字段：
- `name` ← company_name
- `legal_person` ← legal_person
- `credit_code` ← credit_code
- `address` ← address

### 3️⃣ Person表（核心字段）

从extracted_data自动提取到结构化字段：
- `name` ← name
- `id_number` ← id_number
- `education` ← education/degree
- `position` （需手动填写）

---

## 新增API端点

### 1. 获取公司详细信息

**端点**: `GET /api/companies/{company_id}/details`

**功能**: 获取公司及其所有材料的完整信息

**响应示例**:

```json
{
  "company": {
    "id": 1,
    "name": "珞信通达（北京）科技有限公司",
    "legal_person": "王春红",
    "credit_code": "91110111674272168B",
    "address": "北京市海淀区..."
  },
  "materials": [
    {
      "id": 11,
      "title": "营业执照",
      "material_type": "license",
      "extracted_data": {
        "material_type": "license",
        "extracted_data": {
          "registered_capital": "2001万元",
          "establishment_date": "2008-04-14",
          "company_type": "有限责任公司(自然人投资或控股)"
        }
      }
    }
  ]
}
```

**使用示例**:

```bash
curl "http://localhost:9000/api/companies/1/details"
```

---

### 2. 列出所有人员

**端点**: `GET /api/persons?company_id={company_id}`

**功能**: 列出公司的所有人员

**响应示例**:

```json
{
  "persons": [
    {
      "id": 11,
      "name": "周杨",
      "id_number": "411023200112043047",
      "education": null,
      "position": null
    }
  ]
}
```

**使用示例**:

```bash
# 列出所有人员
curl "http://localhost:9000/api/persons"

# 列出公司1的人员
curl "http://localhost:9000/api/persons?company_id=1"
```

---

### 3. 获取人员详细信息

**端点**: `GET /api/persons/{person_id}/details`

**功能**: 获取人员及其所有材料的完整信息

**响应示例**:

```json
{
  "person": {
    "id": 11,
    "name": "周杨",
    "id_number": "411023200112043047",
    "education": null
  },
  "materials": [
    {
      "id": 123,
      "title": "身份证",
      "material_type": "id_card",
      "extracted_data": {
        "extracted_data": {
          "gender": "女",
          "birth_date": "2001-12-04",
          "nation": "汉"
        }
      }
    }
  ]
}
```

**使用示例**:

```bash
curl "http://localhost:9000/api/persons/11/details"
```

---

### 4. 获取材料详细信息

**端点**: `GET /api/materials/{material_id}/details`

**功能**: 获取单个材料的完整信息（包含extracted_data和ocr_text）

**响应示例**:

```json
{
  "id": 11,
  "title": "营业执照",
  "material_type": "license",
  "extracted_data": {
    "material_type": "license",
    "confidence": 0.98,
    "extracted_data": {
      "company_name": "珞信通达（北京）科技有限公司",
      "registered_capital": "2001万元",
      "establishment_date": "2008-04-14",
      "company_type": "有限责任公司(自然人投资或控股)"
    },
    "summary": "这是珞信通达公司的营业执照..."
  },
  "ocr_text": "统一社会信用代码\n91110111674272168B\n...",
  "image_url": "/api/files/营业执照.png"
}
```

**使用示例**:

```bash
curl "http://localhost:9000/api/materials/11/details"
```

---

### 5. 批量提取结构化数据（⭐ 核心功能）

**端点**: `GET /api/extract?company_id={company_id}`

**功能**: 一次性获取公司的所有结构化数据，专为标书编写设计

**查询参数**:
- `company_id` (必需) - 公司ID
- `material_types` (可选) - 材料类型过滤（逗号分隔）

**响应结构**:

```json
{
  "company": {
    "id": 1,
    "name": "珞信通达（北京）科技有限公司",
    "legal_person": "王春红",
    "credit_code": "91110111674272168B",
    "address": "北京市海淀区..."
  },
  "license": {
    "material_id": 11,
    "title": "营业执照",
    "registered_capital": "2001万元",
    "establishment_date": "2008-04-14",
    "company_type": "有限责任公司(自然人投资或控股)",
    "business_scope": "...",
    "ocr_text": "原始OCR文本（如extracted_data为空时使用）"
  },
  "certificates": [
    {
      "material_id": 22,
      "title": "ISO27001信息安全管理体系认证",
      "cert_type": "iso_cert",
      "cert_number": "016ZB25I30045R1S",
      "expiry_date": "2028-02-27",
      "issue_authority": "BCC Inc.",
      "scope": "计算机应用软件设计开发、系统集成及销售服务...",
      "ocr_text": "Certificate No: 016ZB25I30045R1S\nDate of Expiration: Feb. 27, 2028..."
    }
  ],
  "persons": [
    {
      "person_id": 11,
      "name": "周杨",
      "id_number": "411023200112043047",
      "education": null,
      "position": null,
      "materials": {
        "id_card": [
          {
            "material_id": 123,
            "title": "身份证",
            "extracted_data": {
              "gender": "女",
              "birth_date": "2001-12-04",
              "nation": "汉",
              "address": "河南省..."
            },
            "ocr_text": "姓名 周杨\n性别 女\n民族 汉\n..."
          }
        ],
        "education": [],
        "certificate": []
      }
    }
  ],
  "contracts": []
}
```

**使用示例**:

```bash
# 获取公司1的所有数据
curl "http://localhost:9000/api/extract?company_id=1"

# 只获取营业执照和ISO证书
curl "http://localhost:9000/api/extract?company_id=1&material_types=license,iso_cert"
```

---

## 字段提取对照表

### 营业执照信息

| 字段 | 是否提取 | 存储位置 | API获取方式 |
|------|---------|---------|------------|
| 公司名称 | ✅ | Company.name + JSON | `/api/companies/{id}/details` |
| 法定代表人 | ✅ | Company.legal_person + JSON | `/api/companies/{id}/details` |
| 统一社会信用代码 | ✅ | Company.credit_code + JSON | `/api/companies/{id}/details` |
| 地址 | ✅ | Company.address + JSON | `/api/companies/{id}/details` |
| 注册资本 | ✅ | 仅在JSON | `/api/extract?company_id=1` → `license.registered_capital` |
| 公司类型 | ✅ | 仅在JSON | `/api/extract?company_id=1` → `license.company_type` |
| 成立日期 | ✅ | 仅在JSON | `/api/extract?company_id=1` → `license.establishment_date` |
| 营业期限 | ⚠️ | OCR文本中 | `/api/materials/{id}/details` → `ocr_text`（需自行解析） |
| 经营范围 | ⚠️ | OCR文本中 | `/api/materials/{id}/details` → `ocr_text`（需自行解析） |

### 人员信息（身份证）

| 字段 | 是否提取 | 存储位置 | API获取方式 |
|------|---------|---------|------------|
| 姓名 | ✅ | Person.name + JSON | `/api/persons/{id}/details` |
| 身份证号 | ✅ | Person.id_number + JSON | `/api/persons/{id}/details` |
| 性别 | ✅ | 仅在JSON | `/api/extract?company_id=1` → `persons[].materials.id_card[].extracted_data.gender` |
| 出生日期 | ✅ | 仅在JSON | `/api/extract?company_id=1` → `persons[].materials.id_card[].extracted_data.birth_date` |
| 年龄 | ✅ | 计算得出 | 前端根据birth_date计算 |
| 民族 | ✅ | 仅在JSON | `/api/extract?company_id=1` → `persons[].materials.id_card[].extracted_data.nation` |
| 住址 | ✅ | 仅在JSON | `/api/extract?company_id=1` → `persons[].materials.id_card[].extracted_data.address` |
| 学历 | ✅ | Person.education | `/api/persons/{id}/details` |
| 职位 | ✅ | Person.position | `/api/persons/{id}/details`（需手动填写） |
| 专业 | ⚠️ | 学历证书OCR可提取 | `/api/persons/{id}/details` → 查找education类型材料的extracted_data.major |
| 职称/证书 | ⚠️ | 证书类OCR可提取 | `/api/extract?company_id=1` → 查找persons[].materials.certificate |
| 从业年限 | ❌ | - | 需手动录入 |
| 联系电话 | ❌ | - | 需手动录入 |
| 电子邮箱 | ❌ | - | 需手动录入 |

### ISO证书信息

| 字段 | 是否提取 | 存储位置 | API获取方式 |
|------|---------|---------|------------|
| 证书名称 | ✅ | Material.title + JSON | `/api/extract?company_id=1` → `certificates[].title` |
| 证书编号 | ✅ | 仅在JSON | `/api/extract?company_id=1` → `certificates[].cert_number` |
| 有效期 | ✅ | Material.expiry_date + JSON | `/api/extract?company_id=1` → `certificates[].expiry_date` |
| 认证机构 | ✅ | 仅在JSON | `/api/extract?company_id=1` → `certificates[].issue_authority` |
| 认证范围 | ✅ | 仅在JSON | `/api/extract?company_id=1` → `certificates[].scope` |

---

## 使用场景

### 场景1：标书编写 - 获取完整公司数据

```python
import requests

# 1. 获取公司的所有结构化数据
response = requests.get(
    "http://localhost:9000/api/extract",
    params={"company_id": 1}
)
data = response.json()

# 2. 提取需要的字段
company_name = data["company"]["name"]
legal_person = data["company"]["legal_person"]
registered_capital = data["license"]["registered_capital"]
establishment_date = data["license"]["establishment_date"]

# 3. 提取ISO证书信息
iso_certs = data["certificates"]
for cert in iso_certs:
    if "ISO" in cert["title"]:
        print(f"证书名称: {cert['title']}")
        print(f"证书编号: {cert['cert_number']}")
        print(f"有效期: {cert['expiry_date']}")

# 4. 提取法人信息
legal_person_data = None
for person in data["persons"]:
    if person["name"] == legal_person:
        legal_person_data = person
        break

if legal_person_data:
    id_card_materials = legal_person_data["materials"].get("id_card", [])
    if id_card_materials:
        id_card_data = id_card_materials[0]["extracted_data"]
        gender = id_card_data.get("gender")
        birth_date = id_card_data.get("birth_date")
        print(f"法人性别: {gender}")
        print(f"法人出生日期: {birth_date}")
```

### 场景2：人员表生成

```python
import requests

# 获取数据
response = requests.get(
    "http://localhost:9000/api/extract",
    params={"company_id": 1}
)
data = response.json()

# 生成人员表
print("| 姓名 | 性别 | 出生日期 | 民族 | 学历 | 职位 |")
print("|------|------|---------|------|------|------|")

for person in data["persons"]:
    name = person["name"]
    education = person.get("education") or "N/A"
    position = person.get("position") or "N/A"

    # 从身份证材料提取性别、出生日期
    id_card_data = {}
    if "id_card" in person["materials"] and person["materials"]["id_card"]:
        id_card_data = person["materials"]["id_card"][0].get("extracted_data", {})

    gender = id_card_data.get("gender", "N/A")
    birth_date = id_card_data.get("birth_date", "N/A")
    nation = id_card_data.get("nation", "N/A")

    print(f"| {name} | {gender} | {birth_date} | {nation} | {education} | {position} |")
```

### 场景3：证书清单生成

```python
import requests

response = requests.get(
    "http://localhost:9000/api/extract",
    params={"company_id": 1, "material_types": "iso_cert,qualification,certificate"}
)
data = response.json()

print("# 公司资质证书清单\n")
for i, cert in enumerate(data["certificates"], 1):
    print(f"## {i}. {cert['title']}")
    print(f"- **证书编号**: {cert.get('cert_number', 'N/A')}")
    print(f"- **有效期**: {cert.get('expiry_date', 'N/A')}")
    print(f"- **认证机构**: {cert.get('issue_authority', 'N/A')}")
    print(f"- **认证范围**: {cert.get('scope', 'N/A')}")
    print()
```

---

## 数据完整性处理

### extracted_data 为空时的处理

某些材料可能OCR识别完成，但LLM提取尚未执行，此时 `extracted_data` 为 `null`。

**解决方案**：API返回中包含 `ocr_text` 字段，可以：

1. **使用ocr_text**: 将原始OCR文本传给标书编写AI，让它自己提取
2. **触发OCR提取**: 调用MaterialHub的 `/api/materials/{id}/ocr` 端点手动触发
3. **等待后台处理**: MaterialHub会自动批量处理

**示例**:

```python
# 获取证书信息
cert = data["certificates"][0]

if cert.get("cert_number"):
    # extracted_data存在，直接使用
    print(f"证书编号: {cert['cert_number']}")
else:
    # extracted_data为空，使用ocr_text
    ocr_text = cert.get("ocr_text", "")
    print(f"原始OCR文本:\n{ocr_text}")
    # 让标书编写AI从OCR文本中提取证书编号
```

---

## 与其他功能的关系

### 1. 图片检索（v2.0）

**功能**: 搜索材料、获取图片URL、替换占位符

**端点**:
- `GET /api/search` - 搜索材料
- `POST /api/replace` - 替换占位符

**用途**: 在标书中插入图片（营业执照扫描件、证书扫描件等）

### 2. 公司过滤（v2.1）

**功能**: 按公司过滤材料

**端点**:
- `GET /api/companies` - 列出公司
- `GET /api/search?company_id=1` - 按公司搜索

**用途**: 多公司场景下精确定位目标公司

### 3. 数据提取（v2.2）⭐ 新增

**功能**: 提取结构化数据

**端点**:
- `GET /api/companies/{id}/details` - 公司详情
- `GET /api/persons/{id}/details` - 人员详情
- `GET /api/materials/{id}/details` - 材料详情
- `GET /api/extract` - 批量提取

**用途**: 为标书编写提供结构化数据（注册资本、性别年龄、证书编号等）

### 完整工作流

```
1. 选择公司
   GET /api/companies
   → 获取公司列表，选择目标公司（company_id=1）

2. 获取结构化数据
   GET /api/extract?company_id=1
   → 获取所有结构化信息（注册资本、证书、人员等）

3. 搜索并插入图片
   GET /api/search?q=营业执照&company_id=1
   POST /api/replace
   → 在标书中插入营业执照扫描件
```

---

## 测试示例

### 测试1：获取公司完整数据

```bash
curl -s "http://localhost:9000/api/companies/1/details" | jq '
{
  company: .company.name,
  legal_person: .company.legal_person,
  license: (.materials[] | select(.title == "营业执照") | {
    registered_capital: .extracted_data.extracted_data.registered_capital,
    establishment_date: .extracted_data.extracted_data.establishment_date
  })
}'
```

### 测试2：获取人员性别年龄

```bash
curl -s "http://localhost:9000/api/persons/11/details" | jq '
{
  name: .person.name,
  id_number: .person.id_number,
  id_card: (.materials[] | select(.material_type == "id_card") | {
    gender: .extracted_data.extracted_data.gender,
    birth_date: .extracted_data.extracted_data.birth_date,
    nation: .extracted_data.extracted_data.nation
  })
}'
```

### 测试3：批量提取所有数据

```bash
curl -s "http://localhost:9000/api/extract?company_id=1" | jq '
{
  company: .company.name,
  registered_capital: .license.registered_capital,
  establishment_date: .license.establishment_date,
  certificates_count: (.certificates | length),
  persons_count: (.persons | length)
}'
```

---

## 故障排查

### 问题1：extracted_data为null

**原因**：MaterialHub的LLM提取尚未执行

**解决**：
1. 使用 `ocr_text` 字段（包含原始OCR文本）
2. 等待MaterialHub后台处理
3. 手动触发OCR提取（如果MaterialHub支持）

### 问题2：某些字段缺失

**原因**：OCR识别不完整或LLM提取失败

**解决**：
1. 查看 `ocr_text` 确认OCR是否识别到该字段
2. 如果OCR有但extracted_data没有，考虑重新触发LLM提取
3. 如果OCR也没有，需要检查原始图片质量

### 问题3：人员信息不完整

**原因**：部分字段（如从业年限、联系方式）MaterialHub未提取

**解决**：这些字段需要：
1. 手动录入到MaterialHub
2. 或者在标书编写时提示用户提供

---

## 版本历史

### v2.2.0 (2026-02-21)

**新功能**:
- ✨ 新增 `GET /api/companies/{id}/details` 端点
- ✨ 新增 `GET /api/persons` 端点
- ✨ 新增 `GET /api/persons/{id}/details` 端点
- ✨ 新增 `GET /api/materials/{id}/details` 端点
- ✨ 新增 `GET /api/extract` 批量提取端点（核心功能）

**代码变更**:
- `materialhub_client.py`: 添加详情获取方法
- `app.py`: 添加5个新端点

**向后兼容**:
- ✅ 所有现有API保持不变
- ✅ 图片检索功能不受影响
- ✅ 公司过滤功能不受影响

---

## 相关文档

- `SKILL.md` - 主文档
- `COMPANY_FILTER.md` - 公司过滤功能
- `MATERIALHUB_API.md` - MaterialHub API规格
- `DATA_EXTRACTION.md` - 本文档

---

**维护者**: Claude Sonnet 4.5
**最后更新**: 2026-02-21
