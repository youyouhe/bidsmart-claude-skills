# MaterialHub API 文档

MaterialHub 后端API文档，基于FastAPI构建。

## 基础信息

- **默认端口**: 8201
- **基础URL**: `http://localhost:8201`
- **文档地址**:
  - Swagger UI: `http://localhost:8201/docs`
  - ReDoc: `http://localhost:8201/redoc`

## 认证

MaterialHub 使用 **Session-based Authentication** 进行身份验证。

### 认证流程

1. **登录**: POST `/api/auth/login` 获取访问令牌
2. **请求**: 在所有 API 请求的 `Authorization` header 中携带令牌
3. **登出**: POST `/api/auth/logout` 清除会话

### Authorization Header 格式

```
Authorization: Bearer <your_token_here>
```

### 豁免端点

以下端点无需认证：
- `/health` - 健康检查
- `/api/auth/login` - 登录
- `/api/files/*` - 静态图片文件（需登录才能访问 Web UI 获取 URL）

### 默认管理员账户

首次启动时自动创建：
- 用户名: `admin`
- 密码: `admin123`

可通过环境变量配置（见下文）。

## 环境变量

```bash
# 数据库
DB_PATH=data/materials.db

# 服务器
HOST=0.0.0.0
PORT=8201

# OCR服务
OCR_SERVICE_URL=http://localhost:8010
OCR_TIMEOUT=120

# LLM配置
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 认证配置
AUTH_SESSION_HOURS=24                  # 会话有效期（小时）
AUTH_DEFAULT_USERNAME=admin            # 默认管理员用户名
AUTH_DEFAULT_PASSWORD=admin123         # 默认管理员密码
```

---

## 健康检查

### GET /health

检查服务健康状态（无需认证）。

**响应**:
```json
{
  "status": "healthy",
  "service": "MaterialHub"
}
```

---

## 认证管理 (/api/auth)

### 1. 登录

**POST** `/api/auth/login`

用户登录，获取访问令牌（无需认证）。

**请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "token": "a1b2c3d4e5f6...",
  "user": {
    "id": 1,
    "username": "admin",
    "created_at": "2026-02-18T10:00:00",
    "last_login": "2026-02-20T14:30:00"
  },
  "expires_at": "2026-02-21T14:30:00"
}
```

**错误响应**:
```json
{
  "detail": "Invalid username or password"
}
```

---

### 2. 登出

**POST** `/api/auth/logout`

用户登出，清除会话（需要认证）。

**请求 Headers**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true
}
```

---

### 3. 检查会话

**GET** `/api/auth/check`

检查当前会话是否有效（需要认证）。

**请求 Headers**:
```
Authorization: Bearer <token>
```

**响应**:
```json
{
  "valid": true,
  "user": {
    "id": 1,
    "username": "admin",
    "created_at": "2026-02-18T10:00:00",
    "last_login": "2026-02-20T14:30:00"
  }
}
```

**会话无效时**:
```json
{
  "valid": false
}
```

---

## 文档管理 (/api/documents)

**所有端点均需要认证。**

### 1. 上传文档

**POST** `/api/documents`

上传DOCX文档，自动提取图片并创建材料记录。

**请求**:
- Content-Type: `multipart/form-data`
- Body: `file` (DOCX文件)

**响应**:
```json
{
  "document_id": 1,
  "filename": "响应文件.docx",
  "section_count": 15,
  "image_count": 185,
  "materials": [
    {
      "id": 1,
      "document_id": 1,
      "source_filename": "响应文件.docx",
      "section": "资质材料",
      "title": "营业执照",
      "heading_level": 2,
      "image_filename": "营业执照.png",
      "image_url": "/api/materials/1/image",
      "file_size": 123456,
      "expiry_date": null,
      "is_expired": null,
      "created_at": "2026-02-18T10:00:00"
    }
  ]
}
```

**说明**:
- 自动提取DOCX中的图片
- 根据标题层级自动分类
- 支持自动检测有效期
- 上传后触发后台OCR处理

---

### 2. 列出文档

**GET** `/api/documents`

获取所有上传的文档列表。

**响应**:
```json
{
  "documents": [
    {
      "id": 1,
      "filename": "响应文件.docx",
      "upload_time": "2026-02-18T10:00:00",
      "section_count": 15,
      "image_count": 185
    }
  ]
}
```

---

### 3. 删除文档

**DELETE** `/api/documents/{document_id}`

删除指定文档及其所有材料。

**响应**:
```json
{
  "message": "Document 1 deleted"
}
```

---

## 材料管理 (/api/materials)

**所有端点均需要认证。**

### 1. 搜索材料

**GET** `/api/materials`

搜索和筛选材料。

**查询参数**:
- `q` (可选): 搜索关键词
- `document_id` (可选): 文档ID
- `status` (可选): 过期状态
  - `valid`: 有效期内
  - `expired`: 已过期
  - `all`: 全部

**响应**:
```json
{
  "results": [
    {
      "id": 1,
      "document_id": 1,
      "company_id": 1,
      "person_id": null,
      "source_filename": "响应文件.docx",
      "section": "资质材料",
      "title": "营业执照",
      "heading_level": 2,
      "image_filename": "营业执照.png",
      "image_url": "/api/materials/1/image",
      "file_size": 123456,
      "expiry_date": "2025-12-31",
      "is_expired": false,
      "material_type": "license",
      "ocr_text": "营业执照OCR文本...",
      "extracted_data": {
        "company_name": "XXX公司",
        "credit_code": "91110000...",
        "legal_person": "张三"
      },
      "ocr_status": "completed",
      "ocr_error": null,
      "ocr_processed_at": "2026-02-18T10:05:00",
      "created_at": "2026-02-18T10:00:00"
    }
  ]
}
```

---

### 2. 获取材料详情

**GET** `/api/materials/{material_id}`

获取单个材料的详细信息。

**响应**: 同上materials对象

---

### 3. 更新材料

**PATCH** `/api/materials/{material_id}`

更新材料信息。

**请求体**:
```json
{
  "title": "新标题",
  "section": "新分类",
  "expiry_date": "2025-12-31",
  "company_id": 1,
  "person_id": null
}
```

**响应**: 更新后的材料对象

---

### 4. 删除材料

**DELETE** `/api/materials/{material_id}`

删除指定材料。

**响应**:
```json
{
  "message": "Material 1 deleted"
}
```

---

### 5. 获取材料图片

**GET** `/api/materials/{material_id}/image`

获取材料的原始图片文件。

**响应**: 图片文件 (image/png 或 image/jpeg)

---

### 6. 触发OCR识别

**POST** `/api/materials/{material_id}/ocr`

手动触发材料的OCR识别。

**响应**:
```json
{
  "status": "processing",
  "message": "OCR processing started in background",
  "material_id": 1
}
```

**OCR状态**:
- `pending`: 等待处理
- `processing`: 处理中
- `completed`: 已完成
- `failed`: 失败

---

### 7. 获取OCR结果

**GET** `/api/materials/{material_id}/ocr`

获取材料的OCR识别结果。

**响应**:
```json
{
  "status": "completed",
  "ocr_text": "识别的文本内容...",
  "extracted_data": {
    "material_type": "license",
    "confidence": 0.95,
    "extracted_data": {
      "company_name": "XXX公司",
      "credit_code": "91110000..."
    }
  },
  "material_type": "license",
  "error": null,
  "processed_at": "2026-02-18T10:05:00"
}
```

---

## 静态文件 (/api/files)

### 获取图片文件

**GET** `/api/files/{filename}`

获取上传的材料图片文件（无需 Authorization header，但需登录 Web UI 才能获取 URL）。

**响应**: 图片文件 (image/png 或 image/jpeg)

**说明**:
- 图片 URL 在材料对象的 `image_url` 字段中
- 虽然此端点不验证 Authorization header，但用户必须登录 Web UI 才能看到图片 URL
- 图片文件名包含随机哈希，不易被猜测

---

## 公司管理 (/api/companies)

**所有端点均需要认证。**

### 1. 列出公司

**GET** `/api/companies`

获取所有公司列表（含材料统计）。

**响应**:
```json
{
  "companies": [
    {
      "id": 1,
      "name": "XXX科技有限公司",
      "legal_person": "张三",
      "credit_code": "91110000...",
      "address": "北京市海淀区...",
      "created_at": "2026-02-18T10:00:00",
      "updated_at": "2026-02-18T10:00:00",
      "document_count": 2,
      "material_count": 15
    }
  ]
}
```

---

### 2. 获取公司详情

**GET** `/api/companies/{company_id}`

获取单个公司的详细信息。

**响应**: 同上company对象

---

### 3. 获取公司材料

**GET** `/api/companies/{company_id}/materials`

获取公司关联的所有材料。

**响应**:
```json
{
  "company": {
    "id": 1,
    "name": "XXX科技有限公司",
    ...
  },
  "materials": [
    {
      "id": 1,
      "title": "营业执照",
      ...
    }
  ]
}
```

---

### 4. 获取公司完整信息（聚合API）

**GET** `/api/companies/{company_id}/complete`

获取公司的完整信息，包括基本信息、员工列表、所有材料及聚合的扩展信息（一次性获取所有关联数据）。

**响应**:
```json
{
  "company": {
    "id": 1,
    "name": "琪信通达（北京）科技有限公司",
    "legal_person": "王春红",
    "credit_code": "91110111674272168B",
    "address": "北京市海淀区中关村大街17号10号楼3层301室-2040",
    "created_at": "2026-02-17T16:16:37.020279",
    "updated_at": "2026-02-17T16:16:37.020284"
  },
  "employees": [
    {
      "id": 1,
      "name": "张三",
      "id_number": "110101199001011234",
      "education": "本科",
      "position": "项目经理",
      "company_id": 1,
      "created_at": "2026-02-18T10:00:00",
      "updated_at": "2026-02-18T10:00:00",
      "material_count": 5
    }
  ],
  "materials": [
    {
      "id": 11,
      "document_id": 1,
      "company_id": 1,
      "person_id": null,
      "title": "营业执照",
      "material_type": "license",
      "image_url": "/api/files/营业执照.png",
      "expiry_date": "2025-12-31",
      "is_expired": false,
      "extracted_data": {
        "company_name": "琪信通达（北京）科技有限公司",
        "legal_person": "王春红",
        "credit_code": "91110111674272168B",
        "address": "北京市海淀区...",
        "registered_capital": "2001万元",
        "company_type": "有限责任公司(自然人投资或控股)",
        "establishment_date": "2008-04-14"
      },
      "ocr_status": "completed",
      "created_at": "2026-02-17T15:58:10"
    }
  ],
  "aggregated_info": {
    "registered_capital": "2001万元",
    "establishment_date": "2008-04-14",
    "company_type": "有限责任公司(自然人投资或控股)",
    "business_scope": "技术开发、技术咨询...",
    "operating_period": "2008-04-14至长期"
  },
  "statistics": {
    "total_materials": 74,
    "total_employees": 12,
    "expired_materials": 2,
    "valid_materials": 72
  }
}
```

**说明**:
- 一次性返回公司的所有关联数据
- `aggregated_info` 从营业执照材料的 OCR 结果中自动提取扩展字段
- 包含注册资本、成立日期、公司类型等数据库表中未存储的字段
- 适合用于投标文件生成等需要完整公司信息的场景

---

## 人员管理 (/api/persons)

**所有端点均需要认证。**

### 1. 列出人员

**GET** `/api/persons`

获取所有人员列表（含材料统计）。

**查询参数**:
- `company_id` (可选): 按公司筛选

**响应**:
```json
{
  "persons": [
    {
      "id": 1,
      "name": "张三",
      "id_number": "110101199001011234",
      "education": "本科",
      "position": "项目经理",
      "company_id": 1,
      "created_at": "2026-02-18T10:00:00",
      "updated_at": "2026-02-18T10:00:00",
      "material_count": 6
    }
  ]
}
```

---

### 2. 获取人员详情

**GET** `/api/persons/{person_id}`

获取单个人员的详细信息。

**响应**: 同上person对象

---

### 3. 获取人员材料

**GET** `/api/persons/{person_id}/materials`

获取人员关联的所有材料。

**响应**:
```json
{
  "person": {
    "id": 1,
    "name": "张三",
    ...
  },
  "materials": [
    {
      "id": 1,
      "title": "身份证",
      ...
    }
  ]
}
```

---

### 4. 获取人员完整信息（聚合API）

**GET** `/api/persons/{person_id}/complete`

获取人员的完整信息，包括基本信息、所属公司、所有材料、聚合的扩展信息及证书列表（一次性获取所有关联数据）。

**响应**:
```json
{
  "person": {
    "id": 11,
    "name": "周杨",
    "id_number": "411023200112043047",
    "education": "本科",
    "position": "高级工程师",
    "company_id": 1,
    "created_at": "2026-02-17T16:33:18",
    "updated_at": "2026-02-17T16:33:18"
  },
  "company": {
    "id": 1,
    "name": "琪信通达（北京）科技有限公司",
    "legal_person": "王春红",
    "credit_code": "91110111674272168B",
    "address": "北京市海淀区..."
  },
  "materials": [
    {
      "id": 5,
      "document_id": 1,
      "company_id": null,
      "person_id": 11,
      "title": "身份证",
      "material_type": "id_card",
      "image_url": "/api/files/身份证.png",
      "extracted_data": {
        "name": "周杨",
        "gender": "女",
        "nation": "汉",
        "birth_date": "2001-12-04",
        "id_number": "411023200112043047",
        "address": "河南省许昌县小召乡唐庄"
      },
      "ocr_status": "completed",
      "created_at": "2026-02-17T15:58:10"
    },
    {
      "id": 23,
      "title": "学历证书",
      "material_type": "education",
      "extracted_data": {
        "name": "周杨",
        "degree": "本科",
        "major": "计算机科学与技术",
        "university": "北京大学",
        "graduation_date": "2023-06-30"
      }
    }
  ],
  "aggregated_info": {
    "gender": "女",
    "birth_date": "2001-12-04",
    "age": 24,
    "nation": "汉",
    "address": "河南省许昌县小召乡唐庄",
    "major": "计算机科学与技术",
    "degree": "本科",
    "university": "北京大学",
    "graduation_date": "2023-06-30"
  },
  "certificates": [
    {
      "material_id": 45,
      "title": "软件设计师证书",
      "type": "certificate",
      "cert_number": "12345678",
      "issue_date": "2022-05-20",
      "expiry_date": null,
      "issue_authority": "工业和信息化部",
      "is_expired": false
    },
    {
      "material_id": 46,
      "title": "PMP项目管理专业人士认证",
      "type": "certificate",
      "cert_number": "PMI98765",
      "issue_date": "2023-03-15",
      "expiry_date": "2026-03-15",
      "issue_authority": "Project Management Institute",
      "is_expired": false
    }
  ],
  "statistics": {
    "total_materials": 8,
    "total_certificates": 2,
    "expired_certificates": 0,
    "valid_certificates": 2
  }
}
```

**说明**:
- 一次性返回人员的所有关联数据
- `aggregated_info` 从身份证、学历证书等材料的 OCR 结果中自动提取扩展字段
- 包含性别、出生日期、年龄（自动计算）、民族、住址、专业、学历等数据库表中未存储的字段
- `certificates` 列表汇总了该人员的所有证书材料（含证书编号、有效期等）
- 适合用于投标文件生成、人员信息填报等需要完整人员信息的场景

**聚合字段来源**:
- **身份证 (id_card)**: gender, birth_date, age, nation, address
- **学历证书 (education)**: major, degree, university, graduation_date
- **证书 (certificate)**: 自动汇总所有证书信息到 certificates 列表

---

## 材料关联

### 关联到公司

**PATCH** `/api/materials/{material_id}`
```json
{
  "company_id": 1
}
```

### 关联到人员

**PATCH** `/api/materials/{material_id}`
```json
{
  "person_id": 1
}
```

### 取消关联

**PATCH** `/api/materials/{material_id}`
```json
{
  "company_id": null,
  "person_id": null
}
```

---

## 材料类型

系统自动识别的材料类型：

### 公司材料
- `license`: 营业执照
- `legal_person_cert`: 法定代表人证明
- `qualification`: 资质证书
- `iso_cert`: ISO认证证书
- `certificate`: 其他证书

### 个人材料
- `id_card`: 身份证
- `education`: 学历证书
- `degree`: 学位证书
- `certificate`: 职业证书
- `qualification`: 资格证书

### 其他
- `other`: 其他材料

---

## 错误响应

所有端点可能返回的错误：

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未认证或会话过期 |
| 404 | 资源不存在 |
| 413 | 文件过大 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |

**错误响应示例**:

**401 未认证**:
```json
{
  "detail": "Not authenticated"
}
```

**401 会话过期**:
```json
{
  "detail": "Invalid or expired session"
}
```

**404 资源不存在**:
```json
{
  "detail": "Material not found"
}
```

**400 参数错误**:
```json
{
  "detail": "Invalid request parameters"
}
```

---

## OCR自动处理流程

1. **上传文档** → 自动提取图片并创建材料
2. **后台OCR处理** → 自动触发OCR识别（可配置）
3. **信息提取** → 使用LLM提取结构化信息
4. **智能关联** → 自动创建公司/人员并关联材料
5. **有效期提醒** → 自动检测和标记过期状态

---

## 批量操作示例

**注意**: 所有操作均需要先获取访问令牌。

### 1. 获取访问令牌
```bash
TOKEN=$(curl -s -X POST http://localhost:8201/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.token')

echo "Token: $TOKEN"
```

### 2. 批量触发OCR
```bash
# 为所有材料触发OCR（需要令牌）
for i in {1..185}; do
  curl -X POST http://localhost:8201/api/materials/$i/ocr \
    -H "Authorization: Bearer $TOKEN"
  sleep 1
done
```

### 3. 批量更新有效期
```bash
curl -X PATCH http://localhost:8201/api/materials/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"expiry_date": "2025-12-31"}'
```

### 4. 批量查询材料
```bash
# 获取所有材料
curl -s http://localhost:8201/api/materials \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.results[] | {id, title, ocr_status}'
```

---

## 快速开始

### 1. 启动服务
```bash
# 宿主机环境
./start.sh

# Docker环境
docker-compose up -d
```

### 2. 登录获取令牌
```bash
# 使用默认账户登录
curl -X POST http://localhost:8201/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 保存令牌到环境变量
export TOKEN="<your_token_here>"
```

### 3. 测试 API
```bash
# 测试健康检查（无需认证）
curl http://localhost:8201/health

# 获取材料列表（需要认证）
curl http://localhost:8201/api/materials \
  -H "Authorization: Bearer $TOKEN"

# 上传文档（需要认证）
curl -X POST http://localhost:8201/api/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@your_document.docx"
```

### 4. 使用 Web UI
访问 http://localhost:3100，使用 `admin` / `admin123` 登录。

### 5. 使用聚合API获取完整信息

```bash
# 获取公司完整信息（包含员工、材料、扩展字段）
curl http://localhost:8201/api/companies/1/complete \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{
      company: .company.name,
      registered_capital: .aggregated_info.registered_capital,
      employees: .statistics.total_employees,
      materials: .statistics.total_materials
    }'

# 获取人员完整信息（包含公司、材料、证书、扩展字段）
curl http://localhost:8201/api/persons/1/complete \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{
      name: .person.name,
      age: .aggregated_info.age,
      gender: .aggregated_info.gender,
      education: .aggregated_info.degree,
      major: .aggregated_info.major,
      certificates: [.certificates[] | .title]
    }'
```

---

## 开发指南

### 查看日志
```bash
# 宿主机
tail -f backend.log

# Docker
docker-compose logs -f backend
```

### 调试技巧
```bash
# 访问 Swagger UI 交互式文档
open http://localhost:8201/docs

# 在 Swagger UI 中认证：
# 1. 点击右上角 "Authorize" 按钮
# 2. 输入: Bearer <your_token>
# 3. 点击 "Authorize"，然后就可以测试所有 API 了

# 检查会话状态
curl http://localhost:8201/api/auth/check \
  -H "Authorization: Bearer $TOKEN"

# 查看数据库
cd backend
source venv/bin/activate
python
>>> from database import *
>>> with get_session() as db:
...     users = db.query(User).all()
...     print(f"Total users: {len(users)}")
```

### 修改密码
```bash
cd backend
python set_password.py admin your_new_password
```

---

## 性能优化

1. **批量处理**: OCR处理使用后台线程，不阻塞API响应
2. **缓存策略**: OCR结果存储在数据库中，避免重复处理
3. **智能筛选**: LLM预筛选减少不必要的OCR调用
4. **图片优化**: 自动调整图片大小以提高处理速度

---

## 安全注意事项

### 已实现的安全措施

1. **认证授权**: ✅ Session-based authentication
   - 密码使用 bcrypt 哈希存储
   - 会话令牌使用 UUID（随机且不可预测）
   - 会话 24 小时自动过期
   - 所有 API 端点（除登录和健康检查）均需认证

2. **文件安全**: ✅ 上传文件验证
   - 文件类型限制（DOCX、PNG、JPG）
   - 文件大小限制
   - 防止路径遍历攻击

3. **SQL注入防护**: ✅ 使用 SQLAlchemy ORM
   - 参数化查询
   - 自动转义

4. **CORS配置**: ✅ 跨域资源共享
   - 当前配置为允许所有源（适合内部使用）
   - 生产环境建议限制为特定域名

### 生产环境建议

1. **API限流**: 建议添加限流中间件（如 slowapi）
2. **HTTPS**: 使用 HTTPS 加密传输（在 Nginx/Caddy 层配置）
3. **密码策略**: 修改默认管理员密码
4. **会话管理**:
   - 定期清理过期会话
   - 考虑添加刷新令牌机制
5. **审计日志**: 记录关键操作（登录、修改、删除等）
6. **备份策略**: 定期备份数据库和图片文件

### 安全配置示例

修改默认密码：
```bash
cd backend
python set_password.py admin your_strong_password
```

清理过期会话：
```python
from database import get_session
from auth import cleanup_expired_sessions

with get_session() as db:
    deleted = cleanup_expired_sessions(db)
    print(f"Cleaned up {deleted} expired sessions")
```

---

## 相关文档

- [README](README.md) - 项目概述和快速开始
- [宿主机开发指南](HOST_DEVELOPMENT.md) - 宿主机环境配置
- [OCR功能说明](OCR_FEATURE.md) - OCR 识别功能详解
- [OCR服务API](api.md) - DeepSeek-OCR-2 服务 API
- [OCR服务集成](OCR_SERVICE_INTEGRATION.md) - OCR 服务集成说明

---

## 常见问题

### Q: 如何修改默认管理员密码？
A: 使用 `backend/set_password.py` 脚本：
```bash
cd backend
python set_password.py admin your_new_password
```

### Q: 会话过期后如何处理？
A: 前端会自动检测 401 响应并跳转到登录页。手动调用时需重新登录获取新令牌。

### Q: 可以同时在多个设备登录吗？
A: 可以。每次登录会创建独立的会话，互不影响。

### Q: 如何查看当前活跃的会话？
A: 查询数据库：
```bash
cd backend
sqlite3 data/materials.db "SELECT user_id, token, created_at, expires_at FROM sessions WHERE expires_at > datetime('now')"
```

### Q: 图片文件为什么不需要认证？
A: 为了支持浏览器 `<img>` 标签直接加载。虽然图片端点不验证令牌，但：
- 用户必须登录 Web UI 才能看到图片 URL
- 图片文件名包含随机哈希，难以猜测
- 适合内部使用场景

### Q: 如何在生产环境中部署？
A: 建议配置：
1. 修改默认管理员密码
2. 配置 HTTPS（使用 Nginx/Caddy 反向代理）
3. 限制 CORS 允许的源
4. 添加 API 限流
5. 定期备份数据库

### Q: 聚合API和普通API有什么区别？
A:
- **普通API** (`/api/companies/{id}`, `/api/persons/{id}`)：只返回数据库表中的字段
- **聚合API** (`/api/companies/{id}/complete`, `/api/persons/{id}/complete`)：
  - 一次性返回所有关联数据（员工、材料、证书等）
  - 自动从材料的 OCR 结果中提取扩展字段
  - 包含统计信息
  - 适合需要完整信息的场景（如投标文件生成）

**示例**：公司聚合API额外返回：
- `aggregated_info.registered_capital` - 注册资本（从营业执照OCR提取）
- `aggregated_info.establishment_date` - 成立日期
- `aggregated_info.company_type` - 公司类型
- `employees` - 员工列表
- `materials` - 所有材料列表
- `statistics` - 统计信息

### Q: OCR提取的字段存储在哪里？
A:
- **核心字段**：存储在数据库表中（如 Company.name, Person.id_number）
- **扩展字段**：存储在 `Material.extracted_json` 的 `extracted_data` 对象中
- **访问方式**：
  - 直接获取材料：`GET /api/materials/{id}` → `extracted_data` 字段
  - 聚合API：`GET /api/companies/{id}/complete` → `aggregated_info` 字段（自动聚合）

---

## 版本历史

### v1.2.0 (2026-02-21)
- ✨ 添加公司完整信息聚合API (`/api/companies/{id}/complete`)
- ✨ 添加人员完整信息聚合API (`/api/persons/{id}/complete`)
- 📊 自动从OCR结果聚合扩展字段（注册资本、性别、年龄等）
- 📋 证书信息自动汇总功能
- 🎯 优化投标文件生成场景的数据获取

### v1.1.0 (2026-02-20)
- ✨ 添加 Session-based 认证系统
- 🔒 保护所有 API 端点
- 👤 默认管理员账户
- 🔐 密码 bcrypt 哈希
- ⏰ 24小时会话过期
- 🔧 密码管理工具

### v1.0.0 (2026-02-17)
- 🎉 初始版本发布
- 📄 DOCX 文档处理
- 🔍 OCR 识别
- 🤖 LLM 智能提取
- 🏢 公司/人员管理
- 🔗 材料关联
