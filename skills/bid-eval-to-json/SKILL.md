---
name: bid-eval-to-json
description: >
  将投标评估报告从 Markdown 格式转换为结构化 JSON 格式。
  读取 `投标评估报告.md` 全文，直接提取为前端可读的 `投标评估报告.json`。
  当用户要求转换评估报告、生成评估 JSON、格式化评估数据时触发。
  前置条件：需已完成 bid-evaluation 生成 Markdown 报告。
---

# 投标评估报告格式转换

## 核心策略

**直接读取 → 直接输出 JSON。不写脚本，不用正则，不分步解析。**

评估报告 Markdown 通常 200-400 行，完全在上下文窗口内。你直接阅读全文，理解语义，一次性输出完整 JSON。

## 工作流程

### Step 1: 读取 Markdown

用 `read` 工具读取工作目录下的 `投标评估报告.md` 全文。

### Step 2: 直接输出 JSON

阅读完 Markdown 后，用 `write` 工具直接写出 `投标评估报告.json`。

**不要**：
- 写 Python/JS 解析脚本
- 用 grep/sed/awk 提取内容
- 分多步读取文件的不同部分
- 先写中间文件再转换

**要**：一步到位，读完 MD 直接 write JSON。

### Step 3: 验证

用 `bash` 执行 `python3 -c "import json; json.load(open('投标评估报告.json'))"` 验证 JSON 语法正确。

## JSON 输出格式

```json
{
  "projectName": "项目名称",
  "projectBudget": "498.68万元",
  "deadline": "2026年4月20日9时",
  "totalScore": 100,

  "objectiveItems": [
    {
      "factor": "价格评分",
      "score": 10,
      "category": "objective",
      "expectedScore": 8,
      "confidence": "高",
      "notes": "最低价法，假设非最低价",
      "scoringRule": "满足招标文件要求且投标价格最低的投标报价为评标基准价..."
    }
  ],

  "subjectiveItems": [
    {
      "factor": "需求理解",
      "score": 12,
      "category": "subjective",
      "parentCategory": null,
      "scoringRule": "原文评分规则摘要",
      "assessmentGuide": {
        "question": "评估问题原文",
        "criteria": ["标准1", "标准2"],
        "options": [
          { "label": "优秀", "score": 12, "desc": "理解深入、分析全面" },
          { "label": "良好", "score": 7, "desc": "理解较好、符合需求" },
          { "label": "一般", "score": 1, "desc": "理解较浅、欠佳" },
          { "label": "未提供", "score": 0, "desc": "" }
        ]
      },
      "userScore": null,
      "userNotes": null
    }
  ],

  "autoEstimation": {
    "objectiveScoreMax": 30,
    "objectiveScoreExpected": 18,
    "subjectiveScoreMax": 70,
    "subjectiveScoreExpected": null,
    "totalScoreMax": 100,
    "totalScoreExpected": null
  }
}
```

## 字段提取规则

### 项目基本信息
- 从"一、项目基本信息"表格中提取 projectName, projectBudget, deadline, totalScore
- totalScore 提取纯数字（如 "100分" → 100）

### 客观项 (objectiveItems)
- 来源：二、客观条件评估 下各小节 + 2.3 客观项小计表格
- `factor`: 评分项名称
- `score`: 满分分值（纯数字）
- `expectedScore`: 预期得分（纯数字，"⚠️ 待定" → null）
  - 范围格式 "8-12分" → 取中值 10
- `confidence`: 根据标记推断 —— ✅→"高"，⚠️→"中"，❌→"低"
- `notes`: 评估说明的简短摘要
- `scoringRule`: 评分规则原文（精简版）
- 如果存在"4.2 客观-待确认项得分"表格，将"需确认内容"合并到 notes

### 主观项 (subjectiveItems)
- 来源：三、主观条件评估 下各小节
- 识别模式：`### 3.X 标题（N分）`
- 如果有 `#### 3.X.Y 子标题（M分）` 二级拆分，每个子项独立，parentCategory = 大项名称
- 如果无二级拆分，parentCategory = null
- `assessmentGuide.question`: 来自"评估问题"
- `assessmentGuide.criteria`: 来自"评估标准"下的列表项
- `assessmentGuide.options`: 来自"打分选项"，每项提取 label（等级名）、score（分数）、desc（描述）
  - 格式：`- [ ] 优秀（12分）：描述` → `{"label":"优秀","score":12,"desc":"描述"}`
- `userScore`: null（待用户填写）
- `userNotes`: null

### 得分估算 (autoEstimation)
- objectiveScoreMax: 客观项 score 之和
- objectiveScoreExpected: 客观项 expectedScore 之和（跳过 null）
- subjectiveScoreMax: 主观项 score 之和
- subjectiveScoreExpected: null（待用户打分）
- totalScoreMax: objectiveScoreMax + subjectiveScoreMax
- totalScoreExpected: null

## 质量要求

1. **所有主观项必须有 options 数组**，且每个 option 必须有 label、score、desc
2. **数值一致性**：autoEstimation 中的 Max 值必须等于对应 items 的 score 之和
3. **不要编造内容**：所有字段都从 MD 原文提取，不要补充额外信息
4. **JSON 必须合法**：无尾逗号，注意中文引号 `\u201c\u201d` 需要用 Unicode 转义（`\u201c` `\u201d`），否则会被误认为 JSON 字符串结束符

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
