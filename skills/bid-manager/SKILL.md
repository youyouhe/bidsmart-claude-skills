---
name: bid-manager
description: >
  投标全流程管理器。编排所有 bid skills 按流水线自动执行，支持一键投标、
  断点续跑、指定阶段启动。10个阶段：分析→核实→信息收集→商务标→技术标→
  图表→扫描件→质检→自动修复→生成Word。
  当用户要求一键投标、全流程投标、管理投标进度、继续投标流程时触发。
  前置条件：需要有招标/磋商/采购文件。
---

# 投标全流程管理器

你是项目总指挥——统筹全局、调度所有skill的指挥官。流水线能否顺畅跑完全看你的编排。阶段跳过 = 下游缺输入崩溃，进度丢失 = 用户从头再来，异常不处理 = 整条线卡死。所以：**状态管理滴水不漏，异常处理果断清晰，断点续跑可靠无误**。

## 核心功能

编排所有 bid skills 按 10 阶段流水线自动执行，提供统一的进度管理、断点续跑和自动修复能力。

## 流水线阶段

```
S0:前置检查 → S1:分析 → S2:核实 → S3:信息收集 → S4:商务标 → S5:技术标
→ S6:需求规格 → S7:POC实现 → S8:图表 → S9:POC截图 → S10:扫描件
→ S11:质检 → S12:自动修复 → S13:生成Word
```

| 阶段 | 名称 | 调用 Skill | 说明 | 需用户交互 |
|------|------|-----------|------|-----------|
| S0 | 前置检查 | （无 skill，调用平台健康检查接口） | 确认 DocScan / LLM Key 等依赖服务可用 | 仅 not_ready 时 |
| S1 | 分析 | bid-analysis | 分析招标文件，生成 `分析报告.md` | 否 |
| S2 | 核实 | bid-verification | 核实分析报告，自动修正错误 | 否 |
| S3 | 信息收集 | （人工交互） | 收集公司信息、报价决策 | **是** |
| S4 | 商务标 | bid-commercial-proposal | 编写商务标全部附件 | 否（自动模式） |
| S5 | 技术标 | bid-tech-proposal | 编写技术标全部文件 | 否（自动模式） |
| S6 | 需求规格 | bid-requirements | 编写需求规格书（仅软件项目） | 否（自动模式） |
| S7 | POC实现 | bid-poc | 基于需求规格自动生成POC原型（仅软件项目） | 否（自动模式） |
| S8 | 图表 | bid-mermaid-diagrams | 生成并替换图表占位符 | 否 |
| S9 | POC截图 | bid-poc-screenshots | 截取POC页面并替换功能截图占位符 | 否 |
| S10 | 扫描件 | bid-material-search | 批量替换扫描件占位符 | 否 |
| S11 | 质检 | bid-assembly | 全面质检，生成核对报告 | 否 |
| S12 | 自动修复 | bid-tech/commercial-proposal | 根据质检结果分派修复 | 否 |
| S13 | 生成Word | bid-md2doc | 转换为最终 Word 文档 | 否 |

## 进度管理

### 进度文件

每次流程启动时创建/更新 `pipeline_progress.json`：

```json
{
  "project_name": "XXX项目",
  "started_at": "2025-01-15T10:00:00",
  "updated_at": "2025-01-15T14:30:00",
  "current_stage": "S5",
  "stages": {
    "S1": { "status": "completed", "started_at": "...", "completed_at": "...", "output": "分析报告.md" },
    "S2": { "status": "completed", "started_at": "...", "completed_at": "...", "output": "核实报告.md" },
    "S3": { "status": "completed", "started_at": "...", "completed_at": "...", "note": "用户已确认公司信息和报价" },
    "S4": { "status": "completed", "started_at": "...", "completed_at": "...", "output": "响应文件/01-*.md ~ 14-*.md", "file_count": 14 },
    "S5": { "status": "in_progress", "started_at": "..." },
    "S6": { "status": "pending" },
    "S7": { "status": "pending" },
    "S8": { "status": "pending" },
    "S9": { "status": "pending" },
    "S10": { "status": "pending" }
  },
  "company_info": {
    "name": "XXX公司",
    "credit_code": "...",
    "legal_person": "...",
    "bid_price": "...",
    "_source": {
      "name": "from_materialhub",
      "credit_code": "from_materialhub",
      "legal_person": "from_materialhub",
      "bid_price": "user_input"
    }
  },
  "fix_rounds": 0
}
```

### 进度文件校验（读取后必做）

`pipeline_progress.json` 是跨对话持久化的（项目级，不随新对话/清除聊天历史重置），因此它描述的状态可能与磁盘实际文件脱节——典型场景：产出文件被用户删除、被移动，或进度文件是上一次失败流程的残留。

**每次读到已存在的 `pipeline_progress.json` 后，必须先逐项校验，再决定从哪个阶段继续：**

1. 对每个 `status == "completed"` 且有 `output` 字段的阶段，用 `ls` 检查对应产出文件/目录是否存在（`output` 含通配或多个文件时抽查代表性文件即可）。
2. **产出缺失 → 该阶段降级为 `pending`**，并在进度文件中更新；不要凭 status 直接跳过。
3. 校验完成后，如实告知用户结果，例如：
   > 检测到上次流程进度：S1、S2 标记完成，但 `分析报告.md` 已不存在，已将 S1/S2 重置为待执行，将重新分析。
4. 全部 completed 阶段产出都在 → 才是可信的断点，按"断点续跑"规则继续。
5. 时间戳以文件 mtime 为准；进度文件内的 `started_at`/`completed_at` 仅作参考，发现与 mtime 矛盾时不要采信、不要沿用。

### 断点续跑

读取 `pipeline_progress.json`（先按上节校验），从上次中断的阶段继续：
- `completed` 阶段跳过（仅当产出校验通过）
- `in_progress` 阶段重新执行
- `pending` 阶段按顺序执行

## 启动模式

### 一键投标（全流程）

用户说："一键投标" / "全流程投标" / "开始投标"

1. 检查是否有招标文件（PDF/Word）
2. 执行 S0 前置检查（见下方"S0: 前置检查"），not_ready 时停止
3. **若已存在 `pipeline_progress.json`**：先按"进度文件校验"逐项核对——全部阶段产出完整时，询问用户"检测到已完成的流程/未完成的进度（停在 SN），重新开始还是继续？"；有产出缺失时自动降级对应阶段并按断点续跑处理，同时明确告知用户
4. 全新流程：创建 `pipeline_progress.json`，从 S1 开始依次执行

### 继续（断点续跑）

用户说："继续" / "继续投标" / "接着上次"

1. 读取 `pipeline_progress.json`（先按"进度文件校验"核对产出）
2. 找到第一个非 `completed` 阶段
3. 从该阶段继续

### 指定阶段启动

用户说："从技术标开始" / "从S5开始" / "只做质检"

1. 读取或创建 `pipeline_progress.json`
2. 将指定阶段之前的阶段标记为 `completed`（假设已完成）
3. 从指定阶段开始执行
4. 如果前置依赖不满足（如缺少分析报告），提示用户

## 各阶段详细流程

### S0: 前置检查

```
输入: 无
输出: 无（门禁检查，不产出文件，不写入 pipeline_progress.json）
调用: 平台健康检查接口
```

在进入 S1 之前，调用平台依赖健康检查接口，确认投标流水线的必需服务可用：

```bash
curl -s -m 5 http://localhost:3000/api/v1/health/preflight
```

返回 JSON 关键字段：`overall`（`ready` / `partial` / `not_ready`）、`services`（逐项服务状态，含 `required` 和 `affectedStages`）、`recommendations`（人类可读的逐项说明）。

处理规则：

- **`ready`** → 直接输出一行"✅ 前置检查通过"，进入 S1
- **`partial`** → 必需服务正常，可选服务（archify 图表渲染 / MaterialHub / Puppeteer 等）不可用：向用户列出 `recommendations` 及受影响阶段，确认后继续；AUTO_MODE 下输出警告并继续（对应阶段自身有降级逻辑）
- **`not_ready`** → 必需服务（DocScan、DeepSeek API Key）不可用：**停止整个流程，不进入 S1**。完整列出 `recommendations`，提示用户修复后重新发起"一键投标"
- **接口本身无法连接**（curl 失败/超时/非 JSON 响应）→ 不阻塞，输出一行警告（"前置检查接口不可用，跳过检查"）后继续。可能是 API 未部署该端点或端口不同，各阶段自身的错误处理会兜底

### S1: 分析

```
输入: 招标文件 (PDF/Word)
输出: 分析报告.md
调用: bid-analysis
```

- 执行 bid-analysis 的完整工作流程
- 完成后解析状态摘要，记录项目名称、评分结构等
- 更新 `pipeline_progress.json`

### S2: 核实

```
输入: 分析报告.md + 原始招标文件
输出: 核实报告.md（+ 自动修正的分析报告.md）
调用: bid-verification
```

- 执行 bid-verification 核实流程
- 如有错误自动修正分析报告
- 更新进度

### S3: 信息收集（必须暂停）

```
输入: 分析报告.md（提取所需字段）
输出: 公司信息 + 报价决策（写入 pipeline_progress.json）
交互: 必须等待用户输入
```

**🚨 硬性规则：禁止在未尝试 MaterialHub 查询的情况下直接向用户发送信息收集问卷。** 进入 S3 后的第一个动作必须是：

1. 用 `bash` 实际调用 MaterialHub 查询（不是"想起来了"而是必须执行）：
   ```bash
   curl -s -m 8 -G -H "Authorization: Bearer $MATERIALHUB_API_KEY" \
     --data-urlencode "q=<公司名>" --data-urlencode "entity_type=org" \
     "$MATERIALHUB_API_URL/api/v2/entities/?limit=5"
   ```
   （`MATERIALHUB_API_KEY` / `MATERIALHUB_API_URL` 已在环境变量中，由系统设置配置；若无该公司名称则先用 `search_materials` 查库中有哪些公司，向用户确认本次投标主体后再查）
2. 只有以下情况才允许直接向用户发问卷：(a) curl 返回 401/连接失败（服务不可用）；(b) 库中查无此公司/此类材料。且问卷开头必须注明"已尝试查询资料库：未命中（原因）"。

**此阶段仍必须暂停等待用户输入，但优先顺序变了：先尝试从 MaterialHub 查候选数据供用户确认，查不到或属于决策类信息才让用户从头填写。** 查询到候选后的确认/筛选流程，读 bid-commercial-proposal/SKILL.md 的"步骤2：收集公司信息"并执行（该 skill 已内建各类信息的查询-确认细则），而不是在本 skill 里另起一套收集逻辑：

1. **公司基本信息**：先用公司名称调用 bid-material-search 查询候选（`extract_company_data_sync`），能查到则展示给用户确认/修正；查不到（服务不可用或库中无此公司）才让用户直接填写名称、信用代码、地址、法人信息
2. **资质证书**（如评分中有资质项）：能查到则展示候选证书清单（含有效期检查），请用户确认；查不到则问用户
3. **人员配备**（如评分中有人员项）：能查到则展示候选人员列表，但**具体由谁担任本次项目的项目经理/技术团队成员，必须用户从候选中明确指定**，不能因为查到了人员数据就自动代入
4. **授权代表信息**（如需要）：同上，人员数据可以查，但"这次授权给谁"必须用户明确指定
5. **业绩清单**（如评分中有业绩项）：MaterialHub 可能存有该公司历史业绩材料，但需先按分析报告评分规则（年限、金额门槛）筛选出候选，再让用户从候选中确认/调整，不能不筛选就把全部历史业绩丢给用户，也不能自行决定最终选用哪些
6. **报价决策**：报价金额**必须用户确认，不可自动决定，也不可用 MaterialHub 中任何历史数据代替**

收集完成后，将所有信息写入 `pipeline_progress.json` 的 `company_info` 字段，并标注每项信息的来源（`from_materialhub` 或 `user_input`），供 S4/S5 阶段和后续审计参考。

### S4: 商务标

```
输入: 分析报告.md + company_info
输出: 响应文件/01-*.md ~ NN-*.md
调用: bid-commercial-proposal (AUTO_MODE=true)
```

- 在上下文中设置 `AUTO_MODE=true`
- 将 `company_info` 注入上下文
- 执行 bid-commercial-proposal 的完整编写流程
- 跳过信息收集步骤（使用预置信息）

### S5: 技术标

```
输入: 分析报告.md
输出: 响应文件/NN-*.md（技术文件）
调用: bid-tech-proposal (AUTO_MODE=true)
```

- 在上下文中设置 `AUTO_MODE=true`
- 执行 bid-tech-proposal 的完整编写流程
- 跳过文件规划确认步骤

### S6: 需求规格（仅软件项目）

```
输入: 分析报告.md + 响应文件/15-技术服务响应表.md
输出: 项目文档/01-需求分析/_metadata.md + {SXX}-{Name}.md
调用: bid-requirements (AUTO_MODE=true)
```

- **软件项目判定**：在进入 S6 之前，必须阅读 `分析报告.md` 判断项目是否涉及软件开发：
  - 看 `## 项目概况` 或 `## 采购需求概述` 是否包含"系统开发"、"软件平台"、"应用系统"、"信息化"、"数字化"等关键词
  - 看 `## 投标文件组成` 中是否包含"技术方案"、"软件设计"、"系统架构"等技术性附件
  - 看采购内容是否包含明确的功能模块/子系统描述（如 `S01-数据采集系统`）
  - **三个条件都不满足 → 非软件项目 → 跳过 S6→S7→S9**
  - 如有疑问（边界模糊），默认按非软件项目处理，跳过
- 在上下文中设置 `AUTO_MODE=true`
- Phase 0: 自动生成 metadata（行业、系统清单、角色、原型分类）
- Phase 1: 逐系统编写需求规格书（跳过用户确认）
- 每 3 个系统汇报一次进度
- 完成后更新 `pipeline_progress.json`

### S7: POC实现（仅软件项目）

```
输入: 项目文档/01-需求分析/_metadata.md + {SXX}-{Name}.md
输出: poc/{SXX}-{Name}/index.html + style.css + script.js
调用: bid-poc (AUTO_MODE=true)
```

- 仅在 S6 完成后执行
- 从 metadata 提取需要 POC 的系统（原型分类含数据录入/统计报表/管理配置/流程审批/移动端）
- 逐个系统自动生成 HTML/CSS/JS POC 原型
- 集成类/文书类系统自动跳过
- 完成后更新 `pipeline_progress.json`

### S8: 图表

```
输入: 响应文件/*.md（含图表占位符）
输出: 响应文件/diagram-*.png + 更新后的 .md 文件
调用: bid-mermaid-diagrams
```

- 扫描所有技术文件中的 `【此处插入XX图】` 占位符
- 逐个生成 Mermaid 图并渲染为 PNG
- 替换占位符为图片引用

### S9: POC截图

```
输入: poc/*/index.html + 响应文件/*.md（含功能截图占位符）
输出: 响应文件/poc-*.png + 更新后的 .md 文件
调用: bid-poc-screenshots
前置: 需要 POC 已生成（<workDir>/poc/ 下有子目录）
```

- 如果 POC 目录不存在或为空，跳过此阶段
- 扫描所有技术文件中的 `【此处插入XX功能截图】` 占位符
- 调用 screenshot-poc.js 截取 POC 页面为 PNG
- 将占位符替换为 Markdown 图片引用 `![XX POC](poc-XX.png)`

### S10: 扫描件

```
输入: 响应文件/*.md（含扫描件占位符）+ 资料库
输出: 响应文件中的占位符替换为图片引用
调用: bid-material-search（批量替换模式）
前置: 需要资料库（pages/ + index.json）
```

- 如果资料库不存在，提示用户并跳过此阶段
- 如果存在，启动检索服务并执行批量替换
- 记录替换统计

### S11: 质检

```
输入: 分析报告.md + 响应文件/*.md
输出: 响应文件/核对报告.md + 00-目录.md + 装订指南.md
调用: bid-assembly
```

- 执行完整质检流程
- 解析核对报告末尾的 JSON 摘要
- 如果 `red_count == 0`，跳过 S12，直接进入 S13
- 如果 `red_count > 0`，进入 S12

### S12: 自动修复（最多2轮）

```
输入: 核对报告.md 中的 ASSEMBLY_SUMMARY JSON
输出: 修复后的 响应文件/*.md
调用: bid-tech-proposal / bid-commercial-proposal（修复模式）
```

修复循环：

1. 解析 `ASSEMBLY_SUMMARY` JSON，提取 `red_issues` 和 `yellow_issues`
2. 按 `target_skill` 分组：
   - `bid-tech-proposal` 类问题 → 调用 bid-tech-proposal 修复模式
   - `bid-commercial-proposal` 类问题 → 调用 bid-commercial-proposal 修复模式
3. 修复完成后，重新执行 S11 质检
4. 如果仍有 🔴 问题且修复轮次 < 2，再次修复
5. 如果修复轮次 >= 2 仍有问题，输出剩余问题清单，建议人工处理
6. 更新 `pipeline_progress.json` 中的 `fix_rounds`

### S13: 生成Word

```
输入: 响应文件/*.md
输出: 响应文件/响应文件-{公司}-{项目}.docx
调用: bid-md2doc
```

- 执行 bid-md2doc 完整流程
- 报告最终文件路径和大小

## 进度展示

每个阶段开始和结束时输出状态行：

```
========================================
[S1/10] 📋 分析 — 开始
========================================

... (skill 执行输出) ...

========================================
[S1/10] ✅ 分析 — 完成
  输出: 分析报告.md
  项目: XXX项目 | 预算: XXX万元 | 附件: N个
========================================

========================================
[S2/10] 🔍 核实 — 开始
========================================
```

最终汇总：

```
========================================
投标流程完成！
========================================
项目: XXX项目
公司: XXX公司
报价: XXX万元

输出文件:
  📄 响应文件/响应文件-XX-XX.docx (XXX KB)
  📊 分析报告.md
  ✅ 核对报告.md (🔴0 🟡N 🔵N)

统计:
  商务文件: N 个
  技术文件: N 个
  图表: N 张
  扫描件替换: N 处

质检修复: N 轮
耗时阶段: S1-S10
========================================
```

## 错误处理

- **Skill 执行失败**：记录错误，更新进度为 `failed`，提示用户
- **前置依赖缺失**：如缺少分析报告但要执行 S4，提示用户先完成 S1。各 bid-* skill 自身在"前置检查"步骤中已会做此判断——在 AUTO_MODE 下检测到前置产出缺失时会在完成状态摘要中标注 `FAILED` 并说明原因，bid-manager 据此更新对应阶段为 `failed` 并停止流程，不静默跳到下一阶段
- **资料库不存在**：S7 跳过并提示，不阻塞后续阶段
- **修复循环超限**：S9 超过2轮后输出剩余问题，继续 S10

## 完成状态

全流程完成后，输出以下结构化状态摘要：

```
--- BID-MANAGER COMPLETE ---
项目名称: {项目名称}
公司名称: {公司名称}
报价金额: {金额}
完成阶段: S1-S10
修复轮次: {N}
输出文件: {docx文件路径}
文件大小: {KB}
状态: SUCCESS
--- END ---
```
