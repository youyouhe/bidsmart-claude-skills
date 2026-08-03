---
name: bid-manager
description: >
  投标全流程管理器。编排所有 bid skills 按流水线自动执行，支持一键投标、
  断点续跑、指定阶段启动。15个阶段：分析→核实→系统分解→信息收集→商务标→
  技术标→需求规格→原型生成→图表→原型截图→扫描件→质检→自动修复→生成Word。
  当用户要求一键投标、全流程投标、管理投标进度、继续投标流程时触发。
  前置条件：需要有招标/磋商/采购文件。
requires: [python3(门禁/回验/统计脚本), docscan(S0必需)]
---

# 投标全流程管理器

你是项目总指挥——统筹全局、调度所有skill的指挥官。流水线能否顺畅跑完全看你的编排。阶段跳过 = 下游缺输入崩溃，进度丢失 = 用户从头再来，异常不处理 = 整条线卡死。所以：**状态管理滴水不漏，异常处理果断清晰，断点续跑可靠无误**。

## 核心功能

编排所有 bid skills 按 15 阶段流水线自动执行，提供统一的进度管理、断点续跑和自动修复能力。

## 流水线阶段

```
S0:前置检查 → S1:分析 → S2:核实 → S3:系统分解 → S4:信息收集 → S5:商务标 → S6:技术标
→ S7:需求规格 → S8:原型生成 → S9:图表 → S10:原型截图 → S11:扫描件
→ S12:质检 → S13:自动修复 → S14:生成Word
```

| 阶段 | 名称 | 调用 Skill | 说明 | 需用户交互 |
|------|------|-----------|------|-----------|
| S0 | 前置检查 | （无 skill，调用平台健康检查接口） | 确认 DocScan / LLM Key 等依赖服务可用 | 仅 not_ready 时 |
| S1 | 分析 | bid-analysis | 分析招标文件，生成 `分析报告.md` | 否 |
| S2 | 核实 | bid-verification | 核实分析报告，自动修正错误 | 否 |
| S3 | 系统分解 | bid-system-decomp | 产出 `system_decomposition.json`（系统分解单一事实源，技术标/需求规格/原型生成共享） | 否 |
| S4 | 信息收集 | （人工交互） | 收集公司信息、报价决策 | **是** |
| S5 | 商务标 | bid-commercial-proposal | 编写商务标全部附件 | 否（自动模式） |
| S6 | 技术标 | bid-tech-proposal | 编写技术标全部文件 | 否（自动模式） |
| S7 | 需求规格 | bid-requirements | 编写需求规格书（仅软件项目） | 否（自动模式） |
| S8 | 原型生成 | bid-poc | 基于需求规格自动生成系统原型页面（仅软件项目） | 否（自动模式） |
| S9 | 图表 | bid-mermaid-diagrams | 生成并替换图表占位符 | 否 |
| S10 | 原型截图 | bid-poc-screenshots | 截取系统原型页面并替换功能截图占位符 | 否 |
| S11 | 扫描件 | bid-material-search | 批量替换扫描件占位符 | 否 |
| S12 | 质检 | bid-assembly | 全面质检，生成核对报告 | 否 |
| S13 | 自动修复 | bid-tech/commercial-proposal | 根据质检结果分派修复 | 否 |
| S14 | 生成Word | bid-md2doc | 转换为最终 Word 文档 | 否 |

## 进度管理

### 进度文件

每次流程启动时创建/更新 `pipeline_progress.json`：

```json
{
  "project_name": "XXX项目",
  "started_at": "2025-01-15T10:00:00",
  "updated_at": "2025-01-15T14:30:00",
  "current_stage": "S6",
  "stages": {
    "S1": { "status": "completed", "started_at": "...", "completed_at": "...", "output": "分析报告.md" },
    "S2": { "status": "completed", "started_at": "...", "completed_at": "...", "output": "核实报告.md" },
    "S3": { "status": "completed", "started_at": "...", "completed_at": "...", "output": "system_decomposition.json" },
    "S4": { "status": "completed", "started_at": "...", "completed_at": "...", "note": "用户已确认公司信息和报价" },
    "S5": { "status": "completed", "started_at": "...", "completed_at": "...", "output": "响应文件/01-*.md ~ NN-*.md", "file_count": 14 },
    "S6": { "status": "in_progress", "started_at": "..." },
    "S7": { "status": "pending" },
    "S8": { "status": "pending" },
    "S9": { "status": "pending" },
    "S10": { "status": "pending" },
    "S11": { "status": "pending" },
    "S12": { "status": "pending" },
    "S13": { "status": "pending" },
    "S14": { "status": "pending" }
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
  "fix_rounds": 0,
  "audit_decisions": { "status": "pending" }
}
```

> `audit_decisions` 是风险审计门禁的状态位（`pending` → `resolved`），**只允许通过
> `$SKILLS_BASE_PATH/bid-manager/scripts/check_gate.py resolve-audit` 写入**（脚本会校验
> `响应文件/决策清单.json` 存在）；S13/S14 入口必须跑 `check_gate.py check s13|s14`，
> 退出码非 0 禁止进入。详见下方「风险审计门禁」节。

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

### 完成度门禁与诚实性（每阶段标 ✅ 前必做）

每个阶段在 SKILL.md 里都声明了自己的 `输出`（如 S1→`分析报告.md`、S3→`system_decomposition.json`、S6→技术标 .md、S10→`poc-*.png`）。**这是契约，不是装饰**。子 skill 返回 `状态: SUCCESS` 后，**先回验产物再标 ✅**：

1. 用 `ls` / `wc -c` 抽查该阶段声明的 `output` 是否真实存在且非空（空文件 = 未产出）。
2. **产物缺失或为空 → 该阶段记 `failed` 并写明原因，绝不标 ✅**，按"错误处理"停止或降级，向用户如实说明（例："S10 原型截图 标记成功，但 `响应文件/poc-*.png` 为 0 张——浏览器运行时不可用，截图未生成，已改为 failed"）。
3. S14 生成 Word 前的最终门禁：确认 S6 技术标核心文件、S10 截图（软件项目时）确实落盘；缺则先回退修复，不要带着空证据生成 Word。
4. 最终汇总的"完成度"= 已回验产出数 / 应产出数，不是子 skill 的自报 SUCCESS 数。FAILED 阶段在汇总里用 ❌ 标红，不得用 ✅ 掩盖。

**反 confabulation（针对"被追问时临场编造"）**：当用户质疑某个产物、数字或阶段结论（如"为什么没有 S02？""这个 ▲ 数对吗？"），**必须先 `read` 对应文件再回答**，禁止凭记忆或上下文印象重构事实。查不到依据就如实说"我需要回读文件确认"，而不是拼一套听起来合理的解释。

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

用户说："从技术标开始" / "从S6开始" / "只做质检"

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

返回 JSON 关键字段：`overall`（`ready` / `partial` / `not_ready`）、`services`（逐项服务状态，含 `required` 和 `affectedStages`）、`environment`（沙箱环境工具能力级探测：`jq` / `mmdc` / `python:docx` / `python:fitz` / `python:pdfplumber` / `node:docx`，每项含 `affectedStages`）、`recommendations`（人类可读的逐项说明）。

处理规则：

- **`ready`** → 直接输出一行"✅ 前置检查通过"，进入 S1
- **`partial`** → 必需服务正常，可选服务或环境工具不可用：向用户列出 `recommendations` 及受影响阶段，确认后继续；AUTO_MODE 下输出警告并继续
- **`not_ready`** → 必需服务（DocScan、DeepSeek API Key）不可用：**停止整个流程，不进入 S1**。完整列出 `recommendations`，提示用户修复后重新发起"一键投标"
- **接口本身无法连接**（curl 失败/超时/非 JSON 响应）→ 不阻塞，输出一行警告（"前置检查接口不可用，跳过检查"）后继续。可能是 API 未部署该端点或端口不同，各阶段自身的错误处理会兜底

**降级决策必须基于实测，禁止假设兜底可用**：preflight 的探活是**能力级**的（Chrome 是真实执行 `--version`，archify 是真实渲染一张最小图），因此：

- `environment` 中某工具 `missing` → 其 `affectedStages` 列出的阶段**在到达时就必须按已知的缺失做降级**，不得等到了该阶段现试现发现（历史事故：pdfplumber/jq/node:docx 缺失都是执行到当阶段才发现；S0 宣称"Mermaid 兜底"但 mmdc 依赖的 Chrome 根本没装，S9 双路全断）
- 典型映射：`puppeteer` down → S9(mmdc 兜底路径)+S10 均不可用，S9 只能用 archify 主路径、S10 标 SKIPPED；`archify` down → S9 只能走 mmdc（且需 puppeteer ok），两者都 down → S9 整体标 FAILED 并保留占位符，**不得宣称有兜底**；`node:docx` missing → S14 只能走 DocScan 降级路径（且不嵌图，产物回验会 🔴，应提前告知用户）；`python:pdfplumber` missing → S1 用 PyMuPDF 路径
- 各 skill 头部 frontmatter 有 `requires:` 声明其环境依赖，与 preflight `environment` 的 `name` 一一对应

**系统时钟校验（强制门禁，独立于上面的健康接口）**：

```bash
date +%Y    # 取系统当前年份
```

从项目编号（如 `2026-JQ55-W1013`）提取前 4 位作为采购编号前缀年份，与系统当前年份比对：

- **两者必须相等**（如系统年份=2026 且项目编号前缀=2026）→ 通过，进入 S1
- **不一致**（如系统时钟为 2025，而项目编号前缀为 2026）→ **本阶段标 FAILED，停止整个流程，禁止继续**。提示：部署主机时钟/NTP 可能漂移，请先校正系统时间（`timedatectl` / 同步 NTP）后重新发起"一键投标"——否则所有响应文件的落款日期都会错填

此校验是为了防止主机时钟偏差（典型现象：主机停留在 2025，而本批项目实为 2026 年采购）导致全批文件落款日期错填，必须在 S0 一次性拦截。项目编号从 S1 的分析报告或原始招标文件获取；若 S0 时暂无项目编号，则在 S1 完成后、S2 之前补做此校验，不通过则回标 S1 阶段 FAILED 并停止。

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

### S3: 系统分解

```
输入: 分析报告.md
输出: system_decomposition.json
调用: bid-system-decomp (AUTO_MODE=true)
```

- 在上下文中设置 `AUTO_MODE=true`
- 执行 bid-system-decomp：从分析报告"技术需求"聚类系统，产出 `system_decomposition.json`（全流水线系统分解单一事实源；技术标/需求规格/原型生成共享，禁止下游各自重划系统编号）
- **非软件项目**（json 的 `has_system_structure: false`）：本阶段仍标 SUCCESS，json 为 `systems: []`；下游 S7/S8/S10 据此自动跳过
- 解析完成状态块的 `系统数 / 功能点 / ▲ / ★` 计数，写入 `pipeline_progress.json`（供 S12 质检比对、完成度门禁验证）

### S4: 信息收集（必须暂停）

```
输入: 分析报告.md（提取所需字段）
输出: 公司信息 + 报价决策（写入 pipeline_progress.json）
交互: 必须等待用户输入
```

**🚨 硬性规则：禁止在未尝试 MaterialHub 查询的情况下直接向用户发送信息收集问卷。** 进入 S4 后的第一个动作必须是：

1. 用平台提供的 `material_hub_search` / `material_hub_list_entities` / `material_hub_entity_documents` 工具实际查询（不是"想起来了"而是必须执行）：
   ```
   material_hub_entity_documents(entityName: "<公司名>")
   material_hub_mock_pending_list()   # 必查：待替换 mock 清单
   ```
   - `material_hub_mock_pending_list` **与 entity_documents 并列必查**——两者数据源不同（entity_documents 走实体关联，pending_list 走 mock_reason 标记），历史事故：mock 生成接口未建立实体关联，entity_documents 返回 0 而库里实际已有 16 份 mock，agent 误判"材料 0 份"向用户重复发问卷。**entity_documents 为 0 但 pending_list 有货时，以 pending_list 为准**，把已有 mock 材料展示给用户并询问"复用 / 重新生成 / 提供真实材料"。
   查不到候选公司时，先用 `material_hub_list_entities(entityType: "org")` 看库中有哪些公司，向用户确认本次投标主体后再查。
   🔒 密钥与地址由平台服务端持有，agent **无需也不应接触任何 key/地址**——不要用 `bash`/`curl` 拼 `$MATERIALHUB_API_KEY`/`$MATERIALHUB_API_URL`（沙箱 env 已无密钥，裸 curl 只会带空 token 出去，白白多一次失败请求；且这类指令本身是不该存在的坏样例）。所有查询走上述工具，不经过 bash。
2. 只有以下情况才允许直接向用户发问卷：(a) 工具返回服务不可用/连接失败；(b) 库中查无此公司/此类材料。且问卷开头必须注明"已尝试查询资料库：未命中（原因）"。

**实体存在但材料为 0（或远不够）时，问卷必须提供"全部 mock"显式默认选项**：这种中间态不属于下方"完全查无"的自动放行场景，必须问用户，但问法要给出低成本选项——在问卷开头列出：

> **快速通道**：回复"全部 mock"= 授权本次投标所有缺失材料（资质/业绩/人员/扫描件）一律按需生成 mock 占位，标书完成后人工替换为真实材料（废标风险已告知）。逐项提供真实材料则忽略本项。

用户回复"全部 mock"（或同义表述）即构成对**所有缺失材料**的统一授权，按下方 `mock_grant` 规则落盘后，本流水线后续阶段不得再就材料缺失逐项追问。

**公司实体完全查无时（不是缺某份材料，是整个投标主体在 MaterialHub 中都不存在）**：允许连公司基础档案（营业执照等）一起按需 mock 占位，不需要在生成前停下来等用户批准（与下方材料级 mock 生成保持同一交互原则——不阻塞，生成后立即告知）。触发方式：确认本次投标主体名称（用户指定，或从库中已有候选选择）后，若该名称在 MaterialHub 中完全查无，交由 bid-material-search 的 `material_hub_mock_generate` 工具生成营业执照等基础材料；生成后照常登记 `mock_materials_registry.json`，并在本轮输出中提示用户"本次投标主体在资料库中未找到，已生成临时基础档案，标书完成后需替换为真实材料"。

**此阶段仍必须暂停等待用户输入，但优先顺序变了：先尝试从 MaterialHub 查候选数据供用户确认，查不到或属于决策类信息才让用户从头填写。** 查询到候选后的确认/筛选流程，读 bid-commercial-proposal/SKILL.md 的"步骤2：收集公司信息"并执行（该 skill 已内建各类信息的查询-确认细则），而不是在本 skill 里另起一套收集逻辑：

1. **公司基本信息**：先用公司名称调用 bid-material-search 查询候选（`extract_company_data_sync`），能查到则展示给用户确认/修正；查不到（服务不可用或库中无此公司）才让用户直接填写名称、信用代码、地址、法人信息
2. **资质证书**（如评分中有资质项）：能查到则展示候选证书清单（含有效期检查），请用户确认；查不到则问用户
3. **人员配备**（如评分中有人员项）：能查到则展示候选人员列表，但**具体由谁担任本次项目的项目经理/技术团队成员，必须用户从候选中明确指定**，不能因为查到了人员数据就自动代入
4. **授权代表信息**（如需要）：同上，人员数据可以查，但"这次授权给谁"必须用户明确指定
5. **业绩清单**（如评分中有业绩项）：MaterialHub 可能存有该公司历史业绩材料，但需先按分析报告评分规则（年限、金额门槛）筛选出候选，再让用户从候选中确认/调整，不能不筛选就把全部历史业绩丢给用户，也不能自行决定最终选用哪些
6. **报价决策**：报价金额**必须用户确认，不可自动决定，也不可用 MaterialHub 中任何历史数据代替**

收集完成后，将所有信息写入 `pipeline_progress.json` 的 `company_info` 字段，并标注每项信息的来源（`from_materialhub` 或 `user_input`），供 S5/S6 阶段和后续审计参考。

**mock 授权落盘（`mock_grant`，断点续跑/后续阶段继承的依据）**：用户在 S4（或任何阶段）明确授权使用 mock 材料后，必须写入 `pipeline_progress.json`：

```json
"mock_grant": {
  "scope": "all_missing",
  "granted_by": "user",
  "granted_at": "<ISO 时间>",
  "note": "用户授权所有缺失材料按需 mock 占位，完成后人工替换"
}
```

- `scope: "all_missing"` = 全部缺失材料统一授权（用户回复"全部 mock"/"使用mock资料"等同义表述时）；用户只对单项授权的，用 `scope: ["doc_type_code", ...]` 逐项列出
- **下游继承**：S5/S6/S11 及 bid-material-search 在任何"missing → 是否 mock"的决策点，先读 `pipeline_progress.json` 的 `mock_grant`——命中授权范围则直接生成，**不再暂停询问**；未命中才按各自 skill 的默认规则问用户
- 授权只豁免"是否生成"的追问，**不豁免告知义务**：每次实际生成 mock 后照常登记 `mock_materials_registry.json` 并在阶段摘要报告"本次生成 N 份待替换材料"
- 新对话/断点续跑时，只要工作目录的 `pipeline_progress.json` 存在 `mock_grant`，即视为授权仍然有效，不得重新发问

### 投标策略决策（S4→S5 之间，标书级单点决策）

**🚨 硬性规则：商务标与技术标不得各自就质保期、响应时效、服务网点、报价策略等做出承诺；标书级统一策略由本步骤一次性确认，下游强制读取。** 此前出现的"商务侧/技术侧对质保期各自为政"问题即由此步骤根治——策略只在 S4 后确认一次，S5/S6 一律遵循。

在 S4 信息收集完成、进入 S5 商务标之前，由用户一次性确认标书级统一策略，写入 `pipeline_progress.json` 的 `bid_strategy` 块，字段至少含：

- `warranty_years`：质保期年数（统一口径，商务标/技术标共用）
- `response_time`：响应时效（如"2 小时内响应、24 小时内到场"）
- `service_point_strategy`：服务网点策略，取值 `已有` / `中标后设立` / `无`
- `price_strategy`：报价策略（报价口径、折扣/让步规则等）

写入示例：

```json
"bid_strategy": {
  "warranty_years": 3,
  "response_time": "2小时内响应、24小时内到场",
  "service_point_strategy": "中标后设立",
  "price_strategy": "..."
}
```

**S5 bid-commercial-proposal 与 S6 bid-tech-proposal 必须强制读取 `bid_strategy`，不得各自做出与之冲突的承诺**（质保期、响应时效、服务网点等口径在商务标与技术标中必须一致，以 `bid_strategy` 为唯一事实源）。

### S5: 商务标

```
输入: 分析报告.md + company_info
输出: 响应文件/01-*.md ~ NN-*.md
调用: bid-commercial-proposal (AUTO_MODE=true)
```

- 在上下文中设置 `AUTO_MODE=true`
- 将 `company_info` 注入上下文
- **强制读取 `pipeline_progress.json` 的 `bid_strategy` 块**，商务标中质保期、响应时效、服务网点、报价口径等必须与之一致，不得自行做出与之冲突的承诺
- 执行 bid-commercial-proposal 的完整编写流程
- 跳过信息收集步骤（使用预置信息）

### S6: 技术标

```
输入: 分析报告.md
输出: 响应文件/NN-*.md（技术文件）
调用: bid-tech-proposal (AUTO_MODE=true)
```

- 在上下文中设置 `AUTO_MODE=true`
- **强制读取 `pipeline_progress.json` 的 `bid_strategy` 块**，技术标中质保期、响应时效、服务网点等承诺必须与之一致，不得与商务标/`bid_strategy` 冲突
- 执行 bid-tech-proposal 的完整编写流程
- 跳过文件规划确认步骤

### S7: 需求规格（仅软件项目）

```
输入: 分析报告.md + 响应文件/15-技术服务响应表.md
输出: 项目文档/01-需求分析/_metadata.md + {SXX}-{Name}.md
调用: bid-requirements (AUTO_MODE=true)
```

- **软件项目判定**：在进入 S7 之前，必须阅读 `分析报告.md` 判断项目是否涉及软件开发：
  - 看 `## 项目概况` 或 `## 采购需求概述` 是否包含"系统开发"、"软件平台"、"应用系统"、"信息化"、"数字化"等关键词
  - 看 `## 投标文件组成` 中是否包含"技术方案"、"软件设计"、"系统架构"等技术性附件
  - 看采购内容是否包含明确的功能模块/子系统描述（如 `S01-数据采集系统`）
  - **三个条件都不满足 → 非软件项目 → 跳过 S7→S8→S10**
  - 如有疑问（边界模糊），默认按非软件项目处理，跳过
- 在上下文中设置 `AUTO_MODE=true`
- Phase 0: 自动生成 metadata（行业、系统清单、角色、原型分类）
- Phase 1: 逐系统编写需求规格书（跳过用户确认）
- 每 3 个系统汇报一次进度
- 完成后更新 `pipeline_progress.json`

### S8: 原型生成（仅软件项目）

```
输入: 项目文档/01-需求分析/_metadata.md + {SXX}-{Name}.md
输出: poc/{SXX}-{Name}/index.html + style.css + script.js
调用: bid-poc (AUTO_MODE=true)
```

- 仅在 S7 完成后执行
- 从 metadata 提取需要生成原型的系统（原型分类含数据录入/统计报表/管理配置/流程审批/移动端）
- 逐个系统自动生成 HTML/CSS/JS 系统原型页面
- 集成类/文书类系统自动跳过
- 完成后更新 `pipeline_progress.json`

### S9: 图表

```
输入: 响应文件/*.md（含图表占位符）
输出: 响应文件/diagram-*.png + 更新后的 .md 文件
调用: bid-mermaid-diagrams
```

- 扫描所有技术文件中的 `【此处插入XX图】` 占位符
- 逐个生成 Mermaid 图并渲染为 PNG
- 替换占位符为图片引用

### S10: 原型截图

```
输入: poc/*/index.html + 响应文件/*.md（含功能截图占位符）
输出: 响应文件/poc-*.png + 更新后的 .md 文件
调用: bid-poc-screenshots
前置: 需要系统原型已生成（<workDir>/poc/ 下有子目录）
```

- 如果 poc/ 目录不存在或为空，跳过此阶段
- 扫描所有技术文件中的 `【此处插入XX功能截图】` 占位符
- 调用 screenshot-poc.js 截取系统原型页面为 PNG
- 将占位符替换为 Markdown 图片引用 `![XX 系统原型](poc-XX.png)`

### S11: 扫描件

```
输入: 响应文件/*.md（含扫描件占位符）+ 资料库
输出: 响应文件中的占位符替换为图片引用
调用: bid-material-search（批量替换模式）
前置: 需要资料库（pages/ + index.json）
```

- 如果资料库不存在，提示用户并跳过此阶段
- 如果存在，启动检索服务并执行批量替换
- 记录替换统计，**含 mock 生成数量**：`bid-material-search` 在真实检索零命中时会按需生成临时材料（见其 SKILL.md "Mock 生成兜底路径"），本阶段完成状态摘要必须把"真实材料替换: N / mock 生成: M / 未替换: K"三类分开报告，不要把 mock 生成的合并计入"真实材料替换"——否则会让用户误以为资料齐全

### S12: 质检

```
输入: 分析报告.md + 响应文件/*.md
输出: 响应文件/核对报告.md + 00-目录.md + 装订指南.md
调用: bid-assembly
```

- 执行完整质检流程
- 解析核对报告末尾的 JSON 摘要
- **无论 `red_count` 是否为 0，质检完成后都必须进入下方的"风险审计门禁（bid-audit）"**：bid-assembly 只查完整性/格式（占位符、编号、目录），会放过"承诺但无证据""跨文件自相矛盾"等致命问题；bid-audit 才做实质风险审计。
- 风险审计门禁通过后，若仍有 `red_count > 0` 进入 S13 修复；`red_count == 0` 直接进入 S14。

### 风险审计门禁（S12 之后、S13/S14 之前，强制；可在 AUTO_MODE 下暂停）

```
输入: 分析报告.md + 响应文件/*.md + system_decomposition.json + pipeline_progress.json + MaterialHub
输出: 响应文件/审计报告.md + 决策清单.json
调用: bid-audit
```

- **无论 S12 的 `red_count` 是否为 0 都必须执行**（这正是本门禁存在的全部意义——assembly 报绿灯不等于标书没风险；历史上 red_count=0 却带着 10+ 致命问题出门）。
- 执行 bid-audit，产出 `审计报告.md` 与 `决策清单.json`。
- **暂停等待用户裁决**（继 S3 之后的第二个用户决策点，故意覆盖 AUTO_MODE 的自动推进）：把 `决策清单.json` 逐条呈现给用户，每条选：补证据入库 / 改述为合规表述（如"集成第三方资源"）/ 接受风险继续 / 放弃投标。
- 用户标记"需修复"的条目合并进 S13 修复输入（与 S12 的 red/yellow issues 一并修复）。
- **收到逐条裁决后**，运行硬校验脚本落状态位：
  ```bash
  python3 $SKILLS_BASE_PATH/bid-manager/scripts/check_gate.py resolve-audit --note "用户已逐条裁决 N 条决策"
  ```
- **🚫 硬门禁（不再有例外）**：进入 S13 和 S14 前必须分别运行入口检查，退出码非 0 时**禁止进入该阶段**，只能回到用户裁决：
  ```bash
  python3 $SKILLS_BASE_PATH/bid-manager/scripts/check_gate.py check s13   # 进 S13 前
  python3 $SKILLS_BASE_PATH/bid-manager/scripts/check_gate.py check s14   # 进 S14 前（额外校验 S12 已执行 + 占位符闭环自洽）
  ```
  **"用户说了先完成编写/继续/按规则来"等笼统授权不构成逐条裁决**——除非用户在 S4 或裁决点明确说过"审计决策全部按接受风险处理"之类的话，否则不得代用户 resolve。历史教训：agent 曾用"鉴于您已授权先完成编写"一句话放行 9 条未裁决决策直接生成 Word。

### S13: 自动修复（最多2轮）

```
输入: 核对报告.md 中的 ASSEMBLY_SUMMARY JSON
输出: 修复后的 响应文件/*.md
调用: bid-tech-proposal / bid-commercial-proposal（修复模式）
入口检查: python3 $SKILLS_BASE_PATH/bid-manager/scripts/check_gate.py check s13（FAIL 禁止进入）
```

修复循环：

1. 解析 `ASSEMBLY_SUMMARY` JSON，提取 `red_issues` 和 `yellow_issues`
2. 按 `target_skill` 分组：
   - `bid-tech-proposal` 类问题 → 调用 bid-tech-proposal 修复模式
   - `bid-commercial-proposal` 类问题 → 调用 bid-commercial-proposal 修复模式
3. 修复完成后，重新执行 S12 质检
4. 如果仍有 🔴 问题且修复轮次 < 2，再次修复
5. 如果修复轮次 >= 2 仍有问题，输出剩余问题清单，建议人工处理；**这些剩余项必须同步进入最终完成状态的"待处理阻塞项"**，状态按分级表取 `SUCCESS_WITH_BLOCKERS`，不得静默收尾
6. 更新 `pipeline_progress.json` 中的 `fix_rounds`

### S14: 生成Word

```
输入: 响应文件/*.md
输出: 响应文件/响应文件-{公司}-{项目}.docx
调用: bid-md2doc
入口检查: python3 $SKILLS_BASE_PATH/bid-manager/scripts/check_gate.py check s14（FAIL 禁止进入）
```

- 执行 bid-md2doc 完整流程（其内部含产物回验强制步骤）
- bid-md2doc 返回 FAILED（产物回验 🔴 / 占位符残留 > 0）→ 本阶段标 `failed`，**不得带着坏产物进最终汇总**
- 报告最终文件路径和大小

## 进度展示

每个阶段开始和结束时输出状态行（分隔线必须用 `━`，禁止用 `=`/`-`——裸 `====`/`----` 行在 Markdown 里是 setext 标题下划线，会把上一整段渲染成巨型标题）：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[S1/15] 📋 分析 — 开始
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

... (skill 执行输出) ...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[S1/15] ✅ 分析 — 完成
  输出: 分析报告.md
  项目: XXX项目 | 预算: XXX万元 | 附件: N个
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[S2/15] 🔍 核实 — 开始
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

最终汇总：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
投标流程完成！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
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
耗时阶段: S1-S14
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 错误处理

- **Skill 执行失败**：记录错误，更新进度为 `failed`，提示用户
- **前置依赖缺失**：如缺少分析报告但要执行 S5，提示用户先完成 S1。各 bid-* skill 自身在"前置检查"步骤中已会做此判断——在 AUTO_MODE 下检测到前置产出缺失时会在完成状态摘要中标注 `FAILED` 并说明原因，bid-manager 据此更新对应阶段为 `failed` 并停止流程，不静默跳到下一阶段
- **资料库不存在**：S11 跳过并提示，不阻塞后续阶段
- **修复循环超限**：S13 超过2轮后输出剩余问题，继续 S14

## 完成状态

全流程完成后，输出以下结构化状态摘要：

```
--- BID-MANAGER COMPLETE ---
项目名称: {项目名称}
公司名称: {公司名称}
报价金额: {金额}
完成阶段: S1-S14（FAILED/SKIPPED 阶段逐个列出: {Sx:failed原因, Sy:skipped原因}）
修复轮次: {N}
输出文件: {docx文件路径}
文件大小: {KB}
产物回验: {PASS / PASS_WITH_WARNINGS(明细) / FAILED(明细)}
待处理阻塞项: {N}（mock 材料待替换 N 份 / 决策未裁决 N 条 / 占位符未替换 N 处，逐项列出）
状态: {SUCCESS / SUCCESS_WITH_BLOCKERS / FAILED}
--- END ---
```

**状态分级（强制，按最高严重级取值，不得就低）：**

| 状态 | 条件 |
|------|------|
| `SUCCESS` | 全部 15 阶段 ✅，产物回验 PASS，无 mock 待替换材料，无未替换占位符，无未裁决决策 |
| `SUCCESS_WITH_BLOCKERS` | docx 已产出且产物回验通过，但存在：mock 材料待替换 / 占位符未替换 / S9-S11 环境性 FAILED·SKIPPED / 审计决策为"接受风险继续"。**阻塞项必须逐条列在"待处理阻塞项"** |
| `FAILED` | 任何必需阶段（S0-S8、S12-S14）FAILED，或产物回验 🔴，或 docx 未产出 |

- 历史教训：S9 failed + S10 skipped + 14 份 mock 未替换 + 9 条决策未裁决的运行曾自报裸 `SUCCESS`——此后一律按上表分级，`SUCCESS_WITH_BLOCKERS` 必须列明阻塞项，不得用"占位性质标书"等措辞在对联里对冲。
- `完成阶段` 行不得只写 `S1-S14` 一笔带过——FAILED/SKIPPED 的阶段必须带原因逐个列出（对应「完成度门禁与诚实性」节的 ❌ 标红规则）。
