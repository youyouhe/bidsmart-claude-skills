# bid-material-search 使用示例和最佳实践

本文档提供 bid-material-search skill 的实际使用示例和最佳实践。

---

## 快速开始

### 1. 启动服务

```bash
# 设置环境变量（可选）
export MATERIALHUB_USERNAME=admin
export MATERIALHUB_PASSWORD=admin123

# 启动服务
cd skills/bid-material-search/scripts
uvicorn app:app --host 0.0.0.0 --port 9000
```

### 2. 验证连接

```bash
curl http://localhost:9000/health

# 预期响应
{
  "status": "healthy",
  "materialhub_connected": true,
  "materialhub_url": "http://localhost:8201"
}
```

---

## 常见场景

### 场景 1：获取公司完整信息（推荐）⭐

```python
import requests

# 使用聚合 API 一次性获取所有信息
data = requests.get(
    "http://localhost:9000/api/extract",
    params={"company_id": 1}
).json()

# 直接使用聚合后的字段
print(f"公司名称: {data['company']['name']}")
print(f"注册资本: {data['license']['registered_capital']}")
print(f"成立日期: {data['license']['establishment_date']}")

# ISO证书信息
for cert in data['certificates']:
    if 'ISO' in cert['title']:
        print(f"证书: {cert['title']}")
        print(f"证书编号: {cert['cert_number']}")

# 人员信息（扩展字段已聚合）
for person in data['persons']:
    print(f"{person['name']}: {person['gender']}, {person['age']}岁")
```

### 场景 2：查找营业执照

```bash
# 方法 1：关键词搜索
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"

# 方法 2：使用 extract API（推荐）⭐
curl "http://localhost:9000/api/extract?company_id=1" | jq '.license'
```

### 场景 3：替换占位符

```bash
curl -X POST http://localhost:9000/api/replace \
  -H 'Content-Type: application/json' \
  -d '{
    "target_file": "/path/to/响应文件/15-营业执照.md",
    "placeholder": "【此处插入营业执照扫描件】",
    "query": "营业执照"
  }'
```

---

## 投标文件编写集成

### 完整工作流示例

```python
#!/usr/bin/env python3
"""投标文件编写：自动获取公司信息和证书"""
import requests

BASE_URL = "http://localhost:9000"
COMPANY_ID = 1

def get_bid_data():
    """获取投标所需的所有数据（一次API调用）"""
    response = requests.get(
        f"{BASE_URL}/api/extract",
        params={"company_id": COMPANY_ID}
    )
    response.raise_for_status()
    return response.json()

def generate_company_section(data):
    """生成公司信息章节"""
    company = data["company"]
    license_info = data["license"]

    return f"""
## 公司基本信息

| 项目 | 内容 |
|------|------|
| 公司名称 | {company['name']} |
| 统一社会信用代码 | {company['credit_code']} |
| 法定代表人 | {company['legal_person']} |
| 注册资本 | {license_info['registered_capital']} |
| 成立日期 | {license_info['establishment_date']} |
| 公司类型 | {license_info['company_type']} |
"""

def main():
    print("正在获取投标数据...")
    data = get_bid_data()

    print(f"✅ 获取成功！")
    print(f"  - 公司: {data['company']['name']}")
    print(f"  - 证书: {len(data['certificates'])} 个")
    print(f"  - 人员: {len(data['persons'])} 人")

    # 生成markdown内容
    content = generate_company_section(data)

    # 保存到文件
    with open("响应文件/公司信息.md", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ 已生成: 响应文件/公司信息.md")

if __name__ == "__main__":
    main()
```

---

## 性能优化技巧

### 技巧 1：使用聚合 API（而非多次调用）⭐⭐⭐

**❌ 不推荐：多次API调用**

```python
# 需要 3+ 次 HTTP 请求
company = requests.get(f"{BASE_URL}/api/companies/{company_id}").json()
materials = requests.get(f"{BASE_URL}/api/companies/{company_id}/materials").json()
persons = requests.get(f"{BASE_URL}/api/persons?company_id={company_id}").json()
```

**✅ 推荐：使用聚合 API**

```python
# 仅 1 次 HTTP 请求！
data = requests.get(f"{BASE_URL}/api/extract?company_id={company_id}").json()
```

**性能对比**：

| 方式 | HTTP 请求次数 | 响应时间 |
|------|--------------|---------|
| 多次调用 | 3 + N（N=人员数） | ~2000ms（N=10） |
| 聚合 API ⭐ | 1 | ~200ms |

**提速**：~10倍 ⚡

### 技巧 2：利用图片缓存

```python
# 第一次下载（慢）
img1 = requests.get(f"{BASE_URL}/api/materials/11/image").content  # ~500ms

# 第二次获取（快！）
img2 = requests.get(f"{BASE_URL}/api/materials/11/image").content  # ~5ms（缓存命中）
```

---

## 最佳实践

### ✅ DO（推荐做法）

1. **使用聚合 API**
   ```python
   # ✅ 好：一次调用获取所有信息
   data = requests.get(f"{BASE_URL}/api/extract?company_id=1").json()
   ```

2. **指定公司 ID 过滤**
   ```bash
   # ✅ 好：精确过滤
   curl "http://localhost:9000/api/search?q=营业执照&company_id=1"
   ```

3. **检查服务健康状态**
   ```python
   # ✅ 好：启动时检查连接
   health = requests.get(f"{BASE_URL}/health").json()
   if not health["materialhub_connected"]:
       raise RuntimeError("MaterialHub 未连接")
   ```

### ❌ DON'T（不推荐做法）

1. **多次 API 调用获取相同数据**
   ```python
   # ❌ 坏：多次调用
   company = requests.get(f"{BASE_URL}/api/companies/1").json()
   materials = requests.get(f"{BASE_URL}/api/companies/1/materials").json()
   ```

2. **不指定公司过滤（多公司场景）**
   ```bash
   # ❌ 坏：可能返回错误公司的材料
   curl "http://localhost:9000/api/search?q=营业执照"
   ```

---

## 常用命令速查

```bash
# 健康检查
curl http://localhost:9000/health

# 列出公司
curl http://localhost:9000/api/companies

# 获取完整数据（推荐）⭐
curl "http://localhost:9000/api/extract?company_id=1"

# 搜索材料
curl "http://localhost:9000/api/search?q=营业执照&company_id=1"

# 替换占位符
curl -X POST http://localhost:9000/api/replace \
  -H 'Content-Type: application/json' \
  -d '{"target_file":"/path/to/file.md","placeholder":"【占位符】","query":"关键词"}'
```

---

## 相关文档

- [SKILL.md](SKILL.md) - 完整功能说明
- [OPTIMIZATION_RECOMMENDATIONS.md](OPTIMIZATION_RECOMMENDATIONS.md) - 优化建议
- [MaterialHub API 文档](../../MATERIALHUB_API.md) - MaterialHub 完整 API 文档
