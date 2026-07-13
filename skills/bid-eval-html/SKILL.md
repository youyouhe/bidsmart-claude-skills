---
name: bid-eval-html
description: >
  将投标评估报告 JSON 数据渲染为单文件自包含 HTML 打分页面（内嵌 JS，浏览器本地打分求和，无需后端）。
  当用户要求生成评估报告的可视化打分页面、HTML 版评估报告时触发。
  前置条件：需已有 `投标评估报告.json`（由 bid-evaluation 生成）或等价的评估数据结构。
  仅负责渲染，不负责生成评估内容本身——数据生成属于 bid-evaluation 的职责。
---

# 投标评估报告 HTML 打分页面生成

## 核心策略

**读取 JSON 数据 → 直接输出一个完整的单文件 HTML。不拆前端资源，不引入外部依赖，不写后端接口。**

输出文件本质是一份"数据可视化+本地打分工具"，用户在浏览器里打开即可查看客观项评估结果、对主观项逐项打分，页面自动求和给出预期总分。**不做持久化**——打分结果只存在于当前页面的内存/DOM 中，刷新页面即丢失，这是本 skill 明确的设计边界，不是缺陷。

## 输入

### 前置检查（必须先执行）

- 优先读取工作目录下的 `投标评估报告.json`。
- 如果该文件不存在，但上下文中已有 bid-evaluation 刚生成的评估数据（同一次对话内直接产出，未落盘），直接使用该数据，不强制要求先落盘再读取。
- **两者都没有** → 停止，告知用户："未找到 `投标评估报告.json`，且当前对话中没有可用的评估数据。HTML 打分页面依赖 `bid-evaluation` 的产出，是否现在运行 bid-evaluation？"
  - 用户同意 → 调用 `bid-evaluation` 后继续
  - 用户不同意 → 暂停本次渲染任务
- 数据结构须符合以下字段（与 bid-evaluation 输出的字段一致）：

```json
{
  "projectName": "string",
  "projectBudget": "string",
  "deadline": "string",
  "totalScore": "number",
  "objectiveItems": [
    { "factor": "string", "score": "number", "expectedScore": "number|null",
      "canProvide": "boolean|string", "confidence": "string",
      "scoringRule": "string", "notes": "string" }
  ],
  "subjectiveItems": [
    { "factor": "string", "score": "number", "category": "string",
      "parentCategory": "string|null", "scoringRule": "string",
      "assessmentGuide": {
        "question": "string", "criteria": ["string"],
        "options": [{ "label": "string", "score": "number", "desc": "string" }]
      }, "userScore": null, "userNotes": null }
  ],
  "autoEstimation": {
    "objectiveScoreMax": "number", "objectiveScoreExpected": "number|null",
    "subjectiveScoreMax": "number", "subjectiveScoreExpected": null,
    "totalScoreMax": "number", "totalScoreExpected": null
  }
}
```

- 若字段缺失或不完整，按缺失处理（如客观项没有 `notes` 就留空显示），**不编造数据**——本 skill 只负责渲染已有数据，不负责补全评估内容（补全评估内容是 bid-evaluation 的职责，如需要更完整的数据应回到 bid-evaluation 重新生成）。

## 视觉风格要求

参考 `bid-ppt` skill 的设计质量基准，但简化为**简洁商务风格**（不是 PPT 幻灯片视觉）：

- **配色**：蓝色系为主色调（如 `#1e40af`/`#2563eb` 类深/中蓝），辅以浅灰背景与白色卡片，避免高饱和度、多色渐变。
- **布局**：表格/卡片布局为主——客观项用表格展示（一行一项），主观项用卡片展示（一卡一项，卡片内含选项按钮组）。
- **禁止**：无动画效果（不要 `transition`/`animation` 类的视觉过场）、无渐变背景、无插画或装饰性图形、无需要外部字体/图标库（如 Font Awesome CDN）——所有样式内联在同一个 `<style>` 块中。
- **必须自包含**：整个页面是唯一一个 `.html` 文件，`<style>` 和 `<script>` 都内嵌在文件内，不引用任何外部 CSS/JS 文件或 CDN 资源（离线也要能正常打开和使用）。

## 页面结构

```
┌─────────────────────────────────────┐
│ 顶部：项目名称 / 预算 / 截止时间 / 总分 │
├─────────────────────────────────────┤
│ 一、客观项评估（表格，多数只读，"需确认/待定"项可自评）│
│   评分因素 | 满分 | 预期得分(只读数字 或 可编辑输入框) | 能否提供 | 置信度 | 说明 │
│   底部一行：客观项小计（满分 / 预期得分求和，含用户自评部分） │
├─────────────────────────────────────┤
│ 二、主观项打分（卡片，逐项可交互）       │
│   每卡：评分因素 | 满分 | 评分规则 | 打分选项(radio按钮组) | 备注(textarea) │
├─────────────────────────────────────┤
│ 三、汇总（随打分实时更新）              │
│   客观项预期得分 + 主观项已打分合计 = 当前预期总分 / 满分总分 │
│   未打分主观项数量提示（如"还有 3 项未打分，当前为部分预估"）│
└─────────────────────────────────────┘
```

## 交互逻辑（内嵌 JS）

1. 页面加载时，把 JSON 数据内嵌为 JS 变量（`const evalData = {...}`），不通过 `fetch` 异步加载（避免 `file://` 协议下的跨域限制）。
2. **客观项部分——区分只读展示与可自评两种行**：
   - `expectedScore` 有确定数值（非 `null`）→ 该行"预期得分"列纯文本展示，不可编辑（说明已有确定依据，不应被用户随手改掉）。
   - `expectedScore` 为 `null`（通常对应 `canProvide` 为 `"需确认"` 或服务不可用场景）→ 该行"预期得分"列渲染一个数字输入框（`<input type="number" min="0" max="{该项满分}">`），允许用户根据自己对该项实际情况的判断填入一个估算分数，页面记录到 `state.objectiveUserScores[itemIndex]`，实时计入客观项小计。**未填写时视为 0 分**，不是自动假设满分或原 `expectedScore` 空值，避免过于乐观。
   - 每个可编辑行旁需有一个小的提示图标/文字（如"⚠️ 需确认，可自行估算"），避免用户误以为这是系统给出的确定结论。
3. 主观项每项渲染一组单选按钮（对应 `options` 数组），用户点击某个选项即记录该项当前得分到内存中的状态对象（如 `state.subjectiveScores[factorIndex] = score`）。
4. 每次打分/自评状态变化后，实时重新计算并更新汇总区域：
   - 客观项预期得分 = 有确定值的 `expectedScore` 之和 + 用户对"需确认"项填写的自评分之和（未填写按 0 计）
   - 主观项合计 = 已打分项的 score 之和（未打分的不计入，但要在 UI 上明确提示"N 项未打分"）
   - 预期总分 = 客观项预期得分（含自评部分）+ 主观项已打分合计
   - 同时展示"满分总分"（`autoEstimation.totalScoreMax`）用于对比
5. 备注 `textarea` 的内容只保留在页面内存中，用于用户当场查看/复制，不做保存。
6. 明确不提供任何"保存/导出/提交"按钮或逻辑——如需要保留结果，页面顶部展示一行提示文字："此页面为本地浏览器交互工具，打分结果不会自动保存，请在决策后手动记录到评估报告或截图留存"。

## 工作流程

### Step 1: 读取数据

读取 `投标评估报告.json`（或使用同一对话内 bid-evaluation 刚产出的内存数据）。

### Step 2: 生成单文件 HTML

用 `write` 工具一次性写出 `投标评估报告.html`，包含完整 `<style>` 和 `<script>`。

**不要**：拆分成多个文件、引入构建步骤、依赖 npm 包渲染。
**要**：一次 `write` 完成整个 HTML 文件。

### Step 3: 校验

用 `bash` 简单检查文件是否生成、非空、包含 `<script>` 标签：

```bash
test -s 投标评估报告.html && grep -q "<script>" 投标评估报告.html && echo OK
```

（无浏览器环境时不强制做无头渲染验证，语法上肉眼检查 JS 是否有明显的引号/括号不匹配即可。）

## 输出文件

- `投标评估报告.html` - 单文件自包含 HTML 打分页面（工作目录根目录，不建子目录）

## 完成状态

```
--- BID-EVAL-HTML COMPLETE ---
输入数据: 投标评估报告.json（或内存数据）
客观项: {N}个
主观项: {N}个
输出文件: 投标评估报告.html
状态: SUCCESS
--- END ---
```
