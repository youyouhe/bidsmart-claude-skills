---
name: bid-eval-to-json
description: >
  将投标评估报告从 Markdown 格式转换为结构化 JSON 格式。
  解析 `投标评估报告.md` 中的项目信息、客观项、主观项、得分估算等内容，
  生成前端可读的 `投标评估报告.json` 文件。
  当用户要求转换评估报告、生成评估 JSON、格式化评估数据时触发。
  前置条件：需已完成 bid-evaluation 生成 Markdown 报告。
---

# 投标评估报告格式转换

## 核心目标

将人类可读的 Markdown 评估报告转换为机器可读的 JSON 结构，供前端评估页面使用。

## 工作流程

### 1. 读取 Markdown 文件

从工作目录读取 `投标评估报告.md`，验证文件存在性。

### 2. 解析结构化内容

### 2.5 解析 Few-Shot 示例

**示例 1：主观项（带评分表）**

输入 Markdown：
```markdown
#### 3.2.1 功能需求覆盖（8分）

| 评分等级 | 标准 | 得分 |
|---------|------|------|
| 优秀 | 6大模块全部覆盖，有成熟产品，描述准确深入 | 8分 |
| 良好 | 6大模块基本覆盖，部分需定制，描述准确 | 6分 |
| 中等 | 主要模块覆盖，次要模块需开发，整体可行 | 4分 |
| 一般 | 部分模块有偏差，方案需要补充 | 2分 |
| 不足 | 明显缺失重要模块 | 0分 |

**自评得分**：_____ 分
```

期望输出 JSON：
```json
{
  "factor": "功能需求覆盖",
  "score": 8,
  "category": "subjective",
  "parentCategory": "产品和服务方案",
  "scoringRule": "比较打分，根据6大模块覆盖程度评分",
  "assessmentGuide": {
    "question": "我方产品对6大模块的功能覆盖程度如何？",
    "criteria": [
      "房屋土地基础信息模块",
      "公用房管理模块",
      "住宅管理模块",
      "装维修管理模块",
      "系统运行管理模块",
      "综合分析管理模块"
    ],
    "options": [
      { "label": "优秀", "score": 8, "desc": "6大模块全部覆盖，有成熟产品，描述准确深入" },
      { "label": "良好", "score": 6, "desc": "6大模块基本覆盖，部分需定制，描述准确" },
      { "label": "中等", "score": 4, "desc": "主要模块覆盖，次要模块需开发，整体可行" },
      { "label": "一般", "score": 2, "desc": "部分模块有偏差，方案需要补充" },
      { "label": "不足", "score": 0, "desc": "明显缺失重要模块" }
    ]
  },
  "userScore": null,
  "userNotes": null
}
```

**示例 2：客观项（带详细标准）**

输入 Markdown：
```markdown
| **履约能力-认证** | 5分 | ISO9001+ISO20000+ISO27001+CS资质+ITSS | ⚠️ 待定 |
```

期望输出 JSON：
```json
{
  "factor": "履约能力-认证",
  "score": 5,
  "category": "objective",
  "expectedScore": null,
  "confidence": "中",
  "notes": "ISO9001+ISO20000+ISO27001+CS资质+ITSS"
}
```

---

## 正式解析流程

#### 2.1 项目基本信息

从 "一、项目基本信息" 表格中提取：
- **项目名称** (projectName)
- **项目预算** (projectBudget) - 提取金额数字和单位
- **投标截止** (deadline) - 提取日期时间
- **评分总分** (totalScore) - 提取数字

示例 Markdown：
```markdown
| **项目名称** | 清华大学房屋土地数智化管理平台采购项目 |
| **项目预算** | 人民币320万元（含税） |
| **投标截止** | 2026年03月09日 14:00 |
| **评分总分** | 100分 |
```

#### 2.2 客观评分项

**重要**：客观项需要从两个表格中提取信息并合并：

**步骤1：从 "2.3 客观评分项评估" 表格提取基础信息**

| 字段 | 来源列 | 说明 |
|------|--------|------|
| factor | "评分类别" | 评分项名称 |
| score | "分值" | 该项满分，提取数字 |
| category | 固定值 "objective" | 标记为客观项 |
| expectedScore | "预期得分" | 解析得分范围（如 8-12 分取中值 10） |
| confidence | 推断 | "✅" → "高"，"⚠️" → "中"，其他 → "低" |
| notes | "评估依据" | 简短说明 |

**步骤2：从 "4.2 客观-待确认项得分" 表格提取详细依据**

如果 Markdown 中存在"4.2 客观-待确认项得分"或类似章节，需要提取"需确认内容"列的详细信息：

示例表格：
```markdown
| 评分项 | 满分 | 状态 | 需确认内容 |
|--------|------|------|-----------|
| 项目团队-证书 | 4分 | ⚠️ 待确认 | 项目经理高项、产品经理架构师、安全经理CISP、服务经理证书 |
| 项目团队-人数 | 3分 | ⚠️ 待确认 | 12名工程师（得3分）或仅8名（得1分） |
```

**步骤3：合并信息**

根据 `factor` 名称匹配，将详细依据补充到 `notes` 字段：
- 如果"需确认内容"列有详细信息，则 `notes = 简短说明 + " | 详细要求：" + 需确认内容`
- 否则保持原 `notes`

**解析规则**：
- 预期得分格式 "8-12分" → 取中值 10
- 预期得分格式 "7-9分" → 取中值 8
- 预期得分格式 "⚠️ 待定" → expectedScore: null, confidence: "中"
- 预期得分格式 "2分" → expectedScore: 2, confidence: "高"

示例输出（合并后）：
```json
{
  "factor": "项目团队-证书",
  "score": 4,
  "category": "objective",
  "expectedScore": null,
  "confidence": "中",
  "notes": "项目经理1+产品经理1+安全经理1+服务经理1 | 详细要求：项目经理高项、产品经理架构师、安全经理CISP、服务经理证书"
}
```

#### 2.3 主观评分项

从 "三、主观评分项自评表" 各个小节中提取：

**识别规则**：
- 每个 `### 3.X 标题（N分）` 是一个主观项
- 标题格式：`### 3.1 需求理解（15分）`
- 提取：项名称 = "需求理解"，满分 = 15

**二级拆分**（如果存在）：
- `#### 3.1.1 以图管房（5分）` → 子项，满分 5 分
- 如果有二级项，则按二级项拆分（每个二级项是独立的 subjectiveItem）
- 如果无二级项，则整个大项作为一个 subjectiveItem

**评分标准表**：
- 解析表格，提取评分等级、标准描述、得分
- 生成 `assessmentGuide.options` 数组

示例 Markdown：
```markdown
### 3.1 需求理解（15分）

#### 3.1.1 以图管房（5分）

| 评分等级 | 标准 | 得分 |
|---------|------|------|
| 优秀 | 深入理解GIS+房产业务 | 5分 |
| 良好 | 理解需求，有GIS开发能力 | 4分 |
| 中等 | 基本理解需求 | 3分 |

**自评得分**：_____ 分
```

示例输出：
```json
{
  "factor": "以图管房",
  "score": 5,
  "category": "subjective",
  "parentCategory": "需求理解",
  "scoringRule": "比较打分，根据GIS和房产业务理解深度评分",
  "assessmentGuide": {
    "question": "我方对以图管房需求的理解和技术方案质量如何？",
    "criteria": [
      "GIS技术能力",
      "房产业务理解",
      "一张图解决方案成熟度"
    ],
    "options": [
      { "label": "优秀", "score": 5, "desc": "深入理解GIS+房产业务" },
      { "label": "良好", "score": 4, "desc": "理解需求，有GIS开发能力" },
      { "label": "中等", "score": 3, "desc": "基本理解需求" }
    ]
  },
  "userScore": null,
  "userNotes": null
}
```

#### 2.4 得分估算

从客观项和主观项数据中计算：

```json
"autoEstimation": {
  "objectiveScoreMax": <客观项 score 总和>,
  "objectiveScoreExpected": <客观项 expectedScore 总和（排除 null）>,
  "subjectiveScoreMax": <主观项 score 总和>,
  "subjectiveScoreExpected": null,  // 待用户打分
  "totalScoreMax": <objectiveScoreMax + subjectiveScoreMax>,
  "totalScoreExpected": null
}
```

### 3. 生成 JSON 文件

**关键要求**：
1. ✅ **必须提取评分表中的所有选项**（优秀/良好/中等等）
2. ✅ `options` 数组不能为空（除非是父级分类项）
3. ✅ 每个 option 必须包含 `label`（等级名称）、`score`（分数）、`desc`（标准描述）
4. ✅ `scoringRule` 必须描述具体的评分方式，不能是泛泛的描述

使用 `write` 工具输出 `投标评估报告.json`，格式：

```json
{
  "projectName": "...",
  "projectBudget": "...",
  "deadline": "...",
  "totalScore": 100,

  "objectiveItems": [
    { "factor": "...", "score": 13, "category": "objective", ... }
  ],

  "subjectiveItems": [
    { "factor": "...", "score": 5, "category": "subjective", ... }
  ],

  "autoEstimation": {
    "objectiveScoreMax": 44,
    "objectiveScoreExpected": 30,
    "subjectiveScoreMax": 56,
    "subjectiveScoreExpected": null,
    "totalScoreMax": 100,
    "totalScoreExpected": null
  }
}
```

### 4. 验证输出

**必须执行以下验证**：

1. ✅ **JSON 语法检查**：使用 Python `json.load()` 验证
2. ✅ **必需字段检查**：projectName, totalScore, objectiveItems, subjectiveItems, autoEstimation
3. ✅ **客观项 notes 完整性**：
   ```python
   # 检查客观项是否有详细说明
   for item in objectiveItems:
       assert item['notes'] is not None and len(item['notes']) > 10
       # 如果是"待确认"项，notes 应该包含详细要求
       if item['confidence'] == '中' and item['expectedScore'] is None:
           assert '详细要求' in item['notes'] or len(item['notes']) > 20
   ```
4. ✅ **主观项 options 完整性**：
   ```python
   # 伪代码
   for item in subjectiveItems:
       if item is 子项:  # 有 parentCategory 或不是汇总项
           assert len(item.assessmentGuide.options) > 0
           for opt in item.assessmentGuide.options:
               assert 'label' in opt and 'score' in opt and 'desc' in opt
   ```
4. ✅ **输出统计**：客观项数量、主观项数量、有 options 的主观项数量

**如果验证失败，必须修复并重新生成 JSON。**

## 解析技巧

### Markdown 表格解析

```
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 值1 | 值2 | 值3 |
```

- 按行分割，跳过分隔行（`|-----|`）
- 提取列名（第一行）
- 逐行解析数据行

### 数字提取

- "100分" → 100
- "8-12分" → 中值 10
- "人民币320万元" → "320万元"

### 日期格式

- "2026年03月09日 14:00" → "2026-03-09 14:00"（或保持原格式）

### 符号识别

- ✅ → confidence: "高", canProvide: true
- ⚠️ → confidence: "中", canProvide: false (需确认)
- ❌ → confidence: "低", canProvide: false

## 容错处理

如果某些字段缺失或格式异常：
- 使用默认值（如 expectedScore: null）
- 在 notes 中标注 "解析异常"
- 继续处理其他项，不要中断

## 完成状态

```
--- BID-EVAL-TO-JSON COMPLETE ---
输入文件: 投标评估报告.md
输出文件: 投标评估报告.json
客观项数量: {N}
主观项数量: {N}
预期客观得分: {X}/{Y}
状态: SUCCESS
--- END ---
```

## 示例完整输出

```json
{
  "projectName": "清华大学房屋土地数智化管理平台采购项目",
  "projectBudget": "320万元",
  "deadline": "2026-03-09 14:00",
  "totalScore": 100,

  "objectiveItems": [
    {
      "factor": "投标报价",
      "score": 13,
      "category": "objective",
      "expectedScore": 10,
      "confidence": "中",
      "notes": "最低价法，假设报价300万，基准价280万"
    },
    {
      "factor": "技术性能参数响应",
      "score": 9,
      "category": "objective",
      "expectedScore": 8,
      "confidence": "高",
      "notes": "业务范围3分+服务范围3分+辅助工作3分"
    }
  ],

  "subjectiveItems": [
    {
      "factor": "以图管房",
      "score": 5,
      "category": "subjective",
      "parentCategory": "需求理解",
      "scoringRule": "比较打分",
      "assessmentGuide": {
        "question": "我方对以图管房需求的理解和技术方案质量如何？",
        "criteria": ["GIS技术能力", "房产业务理解"],
        "options": [
          { "label": "优秀", "score": 5, "desc": "深入理解GIS+房产业务" },
          { "label": "良好", "score": 4, "desc": "理解需求，有GIS开发能力" },
          { "label": "中等", "score": 3, "desc": "基本理解需求" }
        ]
      },
      "userScore": null,
      "userNotes": null
    }
  ],

  "autoEstimation": {
    "objectiveScoreMax": 44,
    "objectiveScoreExpected": 30,
    "subjectiveScoreMax": 56,
    "subjectiveScoreExpected": null,
    "totalScoreMax": 100,
    "totalScoreExpected": null
  }
}
```
