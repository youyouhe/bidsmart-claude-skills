# 公司过滤功能说明

## 功能概述

bid-material-search v2.1 新增公司过滤功能，支持多公司场景下的精确材料检索。

**版本**: v2.1.0
**发布日期**: 2026-02-20
**解决问题**: MaterialHub 存储多个公司材料时，需要明确指定查询哪个公司的资料

---

## 业务场景

### 问题描述

当 MaterialHub 中存储多个公司的材料时：

```
公司A（珞信通达）：营业执照、ISO认证、合同...
公司B（海云捷迅）：营业执照、资质证书、合同...
公司C（其他公司）：营业执照、许可证...
```

如果直接搜索"营业执照"，无法确定是哪个公司的，可能返回：
- ❌ 所有公司的营业执照（不符合需求）
- ❌ 第一个匹配的公司（不确定性）

### 解决方案

通过公司过滤参数，明确指定目标公司：

```bash
# 查询公司A的营业执照
GET /api/search?q=营业执照&company_id=1

# 查询公司B的营业执照
GET /api/search?q=营业执照&company_name=海云捷迅
```

---

## API 更新

### 1. 新增端点：列出所有公司

**请求**:
```
GET /api/companies
```

**响应**:
```json
{
  "companies": [
    {
      "id": 1,
      "name": "珞信通达（北京）科技有限公司",
      "legal_person": "王春红",
      "credit_code": "91110111674272168B",
      "address": "北京市海淀区...",
      "material_count": 74,
      "document_count": 1
    },
    {
      "id": 2,
      "name": "王春红",
      "material_count": 2,
      "document_count": 0
    },
    {
      "id": 3,
      "name": "北京海云捷迅科技股份有限公司",
      "material_count": 0,
      "document_count": 0
    }
  ]
}
```

**用途**:
- 查询系统中有哪些公司
- 获取每个公司的材料统计
- 为后续搜索提供 company_id

---

### 2. 扩展端点：搜索材料（新增公司参数）

**请求**:
```
GET /api/search?q=关键词&company_id=1&company_name=公司名
```

**新增参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `company_id` | int | 否 | 公司ID（精确匹配，优先级最高） |
| `company_name` | string | 否 | 公司名称（模糊匹配，优先级低于company_id） |

**参数优先级**:
1. **company_id** - 如果提供，直接使用
2. **company_name** - 如果未提供company_id，通过名称查找公司
3. **无公司参数** - 搜索所有公司的材料

**示例**:

```bash
# 1. 按公司ID过滤（精确）
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"
# 返回：公司1的营业执照

# 2. 按公司名称过滤（模糊匹配）
curl "http://localhost:9000/api/search?q=营业执照&company_name=琪信通达"
# 自动匹配到"珞信通达（北京）科技有限公司"

# 3. 组合过滤
curl "http://localhost:9000/api/search?company_id=1&category=资质证明"
# 返回：公司1的所有资质证明类材料

# 4. 不带关键词，列出公司所有材料
curl "http://localhost:9000/api/search?company_id=1"
# 返回：公司1的所有74个材料
```

---

## 使用场景

### 场景1：投标前确定公司

```bash
# 1. 列出所有公司
curl "http://localhost:9000/api/companies"

# 2. 选择目标公司（如：珞信通达，ID=1）

# 3. 查询该公司的营业执照
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"
```

### 场景2：通过公司名称搜索

```bash
# 不知道公司ID，但知道公司名称
curl "http://localhost:9000/api/search?q=ISO认证&company_name=琪信"

# 自动匹配：琪信 → 珞信通达（北京）科技有限公司
```

### 场景3：批量获取公司材料

```bash
# 获取公司1的所有资质证明
curl "http://localhost:9000/api/search?company_id=1&category=资质证明"

# 获取公司1的所有业绩证明
curl "http://localhost:9000/api/search?company_id=1&category=业绩证明"
```

### 场景4：占位符替换（自动适配）

```bash
# 替换时如果有多个公司的同名材料，建议先搜索确认
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"
# 获取 doc_id: mat_11

# 使用 doc_id 精确替换
curl -X POST "http://localhost:9000/api/replace" \
  -H 'Content-Type: application/json' \
  -d '{
    "target_file": "/path/to/file.md",
    "placeholder": "【此处插入营业执照扫描件】",
    "doc_id": "mat_11"
  }'
```

---

## 技术实现

### MaterialHub API 集成

```python
# materialhub_client.py

def get_companies(self) -> list[dict]:
    """获取公司列表"""
    resp = self._request("GET", "/api/companies")
    return resp.json().get("companies", [])

def get_company_materials(self, company_id: int) -> list[dict]:
    """获取指定公司的所有材料"""
    resp = self._request("GET", f"/api/companies/{company_id}/materials")
    return resp.json().get("materials", [])

def search_materials(self, q=None, company_id=None):
    """搜索材料（支持公司过滤）"""
    if company_id:
        # 使用公司材料端点
        materials = self.get_company_materials(company_id)
        # 客户端过滤关键词
        if q:
            materials = [m for m in materials if q in m["title"]]
        return materials
    else:
        # 使用通用搜索端点
        return self._request("GET", "/api/materials", params={"q": q})
```

### 公司名称模糊匹配

```python
# app.py

if company_name:
    # 获取所有公司
    companies = materialhub_client.get_companies()

    # 模糊匹配
    matching = [
        c for c in companies
        if company_name.lower() in c["name"].lower()
    ]

    if matching:
        target_company_id = matching[0]["id"]
        logger.info(f"Matched '{company_name}' to company {target_company_id}")
```

---

## 测试验证

### 测试1：列出公司

```bash
curl "http://localhost:9000/api/companies"
```

**期望结果**:
```json
{
  "companies": [
    {"id": 1, "name": "珞信通达...", "material_count": 74},
    {"id": 2, "name": "王春红", "material_count": 2},
    {"id": 3, "name": "北京海云捷迅...", "material_count": 0}
  ]
}
```

### 测试2：按公司ID搜索

```bash
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"
```

**期望结果**:
- ✅ 返回公司1的营业执照（1个）

```bash
curl "http://localhost:9000/api/search?q=营业执照&company_id=2"
```

**期望结果**:
- ✅ 返回空（公司2没有营业执照）

### 测试3：按公司名称搜索

```bash
curl "http://localhost:9000/api/search?q=营业执照&company_name=琪信"
```

**期望结果**:
- ✅ 自动匹配到"珞信通达"
- ✅ 返回公司1的营业执照

### 测试4：无关键词列出公司材料

```bash
curl "http://localhost:9000/api/search?company_id=1"
```

**期望结果**:
- ✅ 返回公司1的所有74个材料

### 测试5：组合过滤

```bash
curl "http://localhost:9000/api/search?company_id=1&category=资质证明"
```

**期望结果**:
- ✅ 返回公司1的资质证明类材料（11个）

---

## 向后兼容

### 现有功能保持不变

✅ **不带公司参数的搜索**仍然正常工作：

```bash
# 这个仍然有效（搜索所有公司）
curl "http://localhost:9000/api/search?q=营业执照"
```

✅ **占位符替换**无需修改：

```bash
# 现有的替换逻辑不受影响
curl -X POST "http://localhost:9000/api/replace" \
  -d '{"target_file": "...","placeholder": "...","query": "营业执照"}'
```

### 升级建议

**场景1：单公司环境** → 无需修改代码

**场景2：多公司环境** → 建议添加公司过滤：

```python
# 之前
response = requests.get(f"{base_url}/api/search?q=营业执照")

# 现在（推荐）
response = requests.get(f"{base_url}/api/search?q=营业执照&company_id=1")
```

---

## 常见问题

### Q1: 如果不知道公司ID怎么办？

**A**: 使用 `company_name` 参数：

```bash
curl "http://localhost:9000/api/search?q=营业执照&company_name=琪信"
```

系统会自动模糊匹配公司名称。

---

### Q2: 多个公司有同名材料，如何确保获取正确的？

**A**: 始终使用 `company_id` 或 `company_name` 参数：

```bash
# 方式1：通过ID（推荐）
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"

# 方式2：通过名称
curl "http://localhost:9000/api/search?q=营业执照&company_name=珞信通达"
```

---

### Q3: 占位符替换时如何指定公司？

**A**: 两种方式：

**方式1**：先搜索获取精确的 `doc_id`

```bash
# 1. 搜索并获取 doc_id
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"
# 返回: {"id": "mat_11", ...}

# 2. 使用 doc_id 替换
curl -X POST "http://localhost:9000/api/replace" \
  -d '{"doc_id": "mat_11", ...}'
```

**方式2**：使用 `query` 参数（单公司场景）

```bash
curl -X POST "http://localhost:9000/api/replace" \
  -d '{"query": "营业执照", ...}'
```

---

### Q4: 如何列出某个公司的所有材料？

**A**: 不带 `q` 参数，只提供 `company_id`：

```bash
curl "http://localhost:9000/api/search?company_id=1"
```

返回该公司的所有材料（不过滤关键词）。

---

### Q5: 公司名称匹配规则是什么？

**A**: **部分匹配（不区分大小写）**

```bash
company_name=琪信   → 匹配 "珞信通达（北京）科技有限公司"
company_name=海云   → 匹配 "北京海云捷迅科技股份有限公司"
company_name=北京   → 匹配第一个包含"北京"的公司
```

建议使用公司名称中**最具特征的部分**。

---

## 版本历史

### v2.1.0 (2026-02-20)

**新功能**:
- ✨ 新增 `GET /api/companies` 端点
- ✨ 搜索端点支持 `company_id` 参数
- ✨ 搜索端点支持 `company_name` 参数（模糊匹配）
- ✨ 公司材料端点集成

**代码变更**:
- `materialhub_client.py`: 添加 `get_companies()` 和 `get_company_materials()`
- `app.py`: 扩展 `/api/search` 端点，添加 `/api/companies` 端点

**向后兼容**:
- ✅ 所有现有 API 保持不变
- ✅ 不带公司参数的搜索仍然有效

---

## 相关文档

- `MATERIALHUB_API.md` - MaterialHub API 完整规格
- `SKILL.md` - bid-material-search 使用文档
- `UPGRADE_v2.md` - v2.0 升级指南
- `AUTH_UPDATE.md` - 认证方式说明

---

**维护者**: Claude Sonnet 4.5
**最后更新**: 2026-02-20
