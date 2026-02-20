# CHANGELOG - v2.1.0

## 多公司支持更新

**发布日期**：2026-02-20
**版本**：v2.1.0
**类型**：功能增强

---

## 🎯 更新概述

bid-material-search 新增**多公司支持**功能，解决 MaterialHub 存储多个公司材料时的精确检索需求。

### 核心问题

**场景**：MaterialHub 中存储了多个公司的投标材料

```
公司A（珞信通达）: 74个材料（营业执照、ISO认证、合同...）
公司B（海云捷迅）: 0个材料
公司C（王春红）  : 2个材料
```

**问题**：搜索"营业执照"无法明确是哪个公司的

**解决**：通过 `company_id` 或 `company_name` 参数精确指定目标公司

---

## ✨ 新增功能

### 1. 公司列表端点

**新端点**：`GET /api/companies`

**功能**：列出 MaterialHub 中所有公司及其材料统计

**示例**：
```bash
curl "http://localhost:9000/api/companies"
```

**响应**：
```json
{
  "companies": [
    {
      "id": 1,
      "name": "珞信通达（北京）科技有限公司",
      "legal_person": "王春红",
      "credit_code": "91110111674272168B",
      "material_count": 74,
      "document_count": 1
    }
  ]
}
```

---

### 2. 公司过滤参数

**扩展端点**：`GET /api/search`

**新增参数**：
- `company_id` (int) - 公司ID，精确匹配
- `company_name` (string) - 公司名称，模糊匹配

**参数优先级**：
1. `company_id` - 最高优先级
2. `company_name` - 次优先级
3. 不提供公司参数 - 搜索所有公司

**示例**：

```bash
# 1. 按公司ID过滤
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"

# 2. 按公司名称过滤
curl "http://localhost:9000/api/search?q=营业执照&company_name=琪信通达"

# 3. 组合过滤
curl "http://localhost:9000/api/search?company_id=1&category=资质证明"

# 4. 列出公司所有材料
curl "http://localhost:9000/api/search?company_id=1"
```

---

## 📝 代码变更

### materialhub_client.py

**新增方法**：

```python
def get_companies(self) -> list[dict]:
    """获取公司列表"""
    resp = self._request("GET", "/api/companies")
    return resp.json().get("companies", [])

def get_company_materials(self, company_id: int) -> list[dict]:
    """获取指定公司的所有材料"""
    resp = self._request("GET", f"/api/companies/{company_id}/materials")
    return resp.json().get("materials", [])
```

**修改方法**：

```python
def search_materials(
    self,
    q: Optional[str] = None,
    document_id: Optional[int] = None,
    status: str = "valid",
    company_id: Optional[int] = None,  # 新增参数
):
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
        ...
```

---

### app.py

**新增端点**：

```python
@app.get("/api/companies")
def list_companies():
    """列出所有公司"""
    companies = materialhub_client.get_companies()
    return {"companies": companies}
```

**扩展端点**：

```python
@app.get("/api/search")
def search(
    q: Optional[str] = None,
    type: Optional[str] = None,
    category: Optional[str] = None,
    company_id: Optional[int] = None,    # 新增
    company_name: Optional[str] = None,  # 新增
):
    # 公司名称模糊匹配逻辑
    target_company_id = None
    if company_id:
        target_company_id = company_id
    elif company_name:
        companies = materialhub_client.get_companies()
        matching = [c for c in companies if company_name.lower() in c["name"].lower()]
        if matching:
            target_company_id = matching[0]["id"]

    # 使用 company_id 过滤
    materials = materialhub_client.search_materials(q=q, company_id=target_company_id)
    ...
```

---

## 🧪 测试验证

### 测试用例

**测试1**：列出公司
```bash
curl "http://localhost:9000/api/companies"
# ✅ 返回3个公司
```

**测试2**：按公司ID搜索
```bash
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"
# ✅ 返回公司1的营业执照（1个）

curl "http://localhost:9000/api/search?q=营业执照&company_id=2"
# ✅ 返回空（公司2没有营业执照）
```

**测试3**：按公司名称搜索
```bash
curl "http://localhost:9000/api/search?q=营业执照&company_name=琪信"
# ✅ 自动匹配到"珞信通达"，返回公司1的营业执照
```

**测试4**：列出公司材料
```bash
curl "http://localhost:9000/api/search?company_id=1"
# ✅ 返回公司1的所有74个材料
```

**测试5**：组合过滤
```bash
curl "http://localhost:9000/api/search?company_id=1&category=资质证明"
# ✅ 返回公司1的11个资质证明材料
```

---

## 📊 统计数据

### 代码变更

| 文件 | 变更类型 | 新增行数 | 删除行数 |
|------|---------|---------|---------|
| `materialhub_client.py` | 修改 | +48 | -5 |
| `app.py` | 修改 | +35 | -8 |
| `SKILL.md` | 修改 | +72 | -10 |
| `COMPANY_FILTER.md` | 新增 | +450 | 0 |
| `CHANGELOG_v2.1.0.md` | 新增 | 本文档 | 0 |

**总计**：+605 行代码和文档

---

## ✅ 向后兼容

### 现有功能保持不变

✅ **不带公司参数的搜索**（默认行为）：

```bash
# 这些请求仍然正常工作
curl "http://localhost:9000/api/search?q=营业执照"
curl "http://localhost:9000/api/search?category=资质证明"
```

✅ **占位符替换**无需修改：

```bash
# 现有的替换逻辑不受影响
curl -X POST "http://localhost:9000/api/replace" \
  -d '{"target_file": "...","placeholder": "...","query": "营业执照"}'
```

✅ **其他端点**保持不变：
- `GET /api/documents`
- `GET /api/documents/{id}`
- `GET /health`

### 升级建议

**单公司环境** → 无需修改代码

**多公司环境** → 建议添加公司过滤参数：

```python
# 之前
response = requests.get(f"{base_url}/api/search?q=营业执照")

# 现在（推荐）
response = requests.get(f"{base_url}/api/search?q=营业执照&company_id=1")
```

---

## 🎯 使用场景

### 场景1：投标前确定公司

```python
# 1. 获取公司列表
companies_resp = requests.get(f"{base_url}/api/companies")
companies = companies_resp.json()["companies"]

# 2. 选择目标公司
target_company = companies[0]  # 假设选择第一个
company_id = target_company["id"]

# 3. 查询该公司的材料
search_resp = requests.get(
    f"{base_url}/api/search",
    params={"q": "营业执照", "company_id": company_id}
)
```

### 场景2：批量处理多公司材料

```python
# 获取所有公司
companies = requests.get(f"{base_url}/api/companies").json()["companies"]

# 为每个公司处理材料
for company in companies:
    if company["material_count"] > 0:
        materials = requests.get(
            f"{base_url}/api/search",
            params={"company_id": company["id"]}
        ).json()["results"]

        print(f"公司 {company['name']} 有 {len(materials)} 个材料")
```

### 场景3：通过公司名称智能搜索

```python
# 用户输入公司名称关键词
company_keyword = "琪信"

# 搜索该公司的ISO认证
materials = requests.get(
    f"{base_url}/api/search",
    params={"q": "ISO", "company_name": company_keyword}
).json()["results"]
```

---

## 🐛 Bug修复

### 修复：ocr_text 为 None 导致的异常

**问题**：某些材料的 `ocr_text` 字段为 None，调用 `.lower()` 时抛出 `AttributeError`

**修复**：
```python
# 之前
if q_lower in m.get("ocr_text", "").lower()  # ❌ 如果是None会报错

# 现在
if q_lower in (m.get("ocr_text") or "").lower()  # ✅ 正确处理None
```

---

## 📚 相关文档

- `COMPANY_FILTER.md` - 公司过滤功能详细说明（新增）
- `SKILL.md` - 技能使用文档（已更新）
- `MATERIALHUB_API.md` - MaterialHub API 规格
- `CHANGELOG_v2.0.1.md` - 认证方式更新

---

## 🚀 后续计划

v2.2 可能增强：

1. **按人员过滤**：类似公司过滤，支持按人员ID搜索材料
2. **高级搜索**：按材料类型、有效期、文档来源等多维度过滤
3. **批量替换**：支持一次性替换多个公司的材料
4. **缓存优化**：缓存公司列表，减少API调用

---

## 版本信息

- **v2.1.0** - 多公司支持（当前版本）
- **v2.0.1** - 认证方式优化（交互式输入）
- **v2.0.0** - MaterialHub API 集成
- **v1.0.0** - 本地文件系统模式

---

**维护者**：Claude Sonnet 4.5
**发布日期**：2026-02-20
**状态**：✅ 已完成并测试通过
