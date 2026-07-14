---
name: bid-mermaid-diagrams
description: >
  为投标文件中的图表占位符渲染 Mermaid 图为 PNG 图片。
  扫描 markdown 文件中的【此处插入XX图】占位符，优先提取占位符后已有的
  Mermaid 代码块直接渲染（上游 bid-tech-proposal 已按规范编写好代码），
  兼容处理旧格式的 ASCII 图转换，渲染为高清 PNG，
  然后替换占位符为 markdown 图片引用。
  架构图/流程图/时序图/数据流图/状态机默认改用内置的 archify 渲染引擎，
  效果更专业；甘特图和 ER 图 archify 不支持，仍走 Mermaid+mmdc 路径。
  当用户要求画图、生成图表、替换图表占位符、为技术方案/实施方案画架构图时触发。
---

# Mermaid 图表生成与渲染

你是视觉设计师——把方案变成专业图表的角色。架构图、流程图、拓扑图，每张图都直接影响评委对技术方案的直观印象。图表语法错误 = 渲染失败留白，图文不符 = 扣印象分。所以：**优先使用上游已给出的 Mermaid 代码，不重新设计图表结构；确保语法正确、一次渲染成功**。

## 依赖

- Node.js（已预装）
- @mermaid-js/mermaid-cli（已预装，禁止自行安装）
- mermaid_render 工具（系统内置扩展，优先使用）
- archify（`scripts/archify/`，已随本 skill 内置，无需安装，架构图/流程图/时序图/数据流图/状态机的渲染引擎）
- archify render server（`scripts/archify-server.mjs`，需在沙盒外预先启动，端口 18800）

## 核心工具

- **mermaid_render**：系统内置工具，直接传入 Mermaid 代码和输出路径即可渲染，优先使用（流程图/组织架构图/甘特图/ER图走这条路径）
- 渲染脚本：`scripts/render.sh`（甘特图/ER 图专用，Mermaid+mmdc 路径）
- 主题配置：`scripts/mermaid.json`（蓝色专业主题，支持中文）
- **archify 渲染脚本**：`scripts/render_archify.mjs`（架构图/流程图/时序图/数据流图/状态机走这条路径，优先通过 HTTP 调用沙盒外的 archify-server，服务不在线才尝试本地 Puppeteer）

## Archify Server 启动方式

archify render server 需在**沙盒外**单独启动（Chrome/Puppeteer 需要完整系统权限），类似 DocScan（8800）和 MaterialHub（8201）的模式：

```bash
# 启动（默认端口 18800，后台运行，日志写到 /tmp/archify-server-18800.log）
bash skills/bid-mermaid-diagrams/scripts/start-archify-server.sh

# 停止
bash skills/bid-mermaid-diagrams/scripts/stop-archify-server.sh

# 健康检查
curl http://127.0.0.1:18800/health
```

服务在线时，`render_archify.mjs` 内部会自动通过 HTTP POST 发给服务端渲染，Chrome/Puppeteer 完全跑在沙盒外；服务不在线时退为本地 Puppeteer（仅在沙盒外环境有效）。

## 工作流程

### 0. 前置检查（必须先执行）

检查 `响应文件/` 目录下是否存在包含图表占位符的 `.md` 文件（由 `bid-tech-proposal`/`bid-commercial-proposal` 生成）：

```bash
grep -rl "【此处插入.*图】" 响应文件/*.md 2>/dev/null
```

- **有匹配文件** → 继续第 1 步
- **无匹配文件或 `响应文件/` 不存在** → 停止，告知用户："未在 `响应文件/` 下找到图表占位符，图表渲染需要先由 `bid-tech-proposal`/`bid-commercial-proposal` 写好占位符及 Mermaid 代码块。是否现在运行对应 skill？"
  - 用户同意 → 调用相应 skill 后继续
  - 用户不同意 → 暂停本次任务
- **AUTO_MODE=true** 时：不可交互等待，直接在完成状态摘要中标注 `FAILED`，说明"未找到图表占位符"，交由 bid-manager 处理

### 0.1 水印决策（询问用户）

渲染前询问用户是否为图表添加项目名称水印（右下角半透明项目名，防投标材料被滥用）：

```
📋 图表水印设置
本次生成的图表是否需要添加项目名称水印？
1️⃣ 添加水印（推荐，项目名自动从 分析报告.md 提取）
2️⃣ 不添加水印
```

- 用户选择**添加**（或默认）→ 正常渲染，脚本自动打水印
- 用户选择**不添加** → 后续所有渲染命令前缀环境变量 `NO_WATERMARK=1`，例如：
  ```bash
  NO_WATERMARK=1 node scripts/render_archify.mjs architecture input.json output.png
  NO_WATERMARK=1 bash scripts/render.sh input.mmd output.png
  ```
- **AUTO_MODE=true**（bid-manager 调度，无法交互）→ 默认**添加水印**（保持防滥用），并在完成状态摘要中注明

### 1. 扫描占位符

在目标 markdown 文件中查找 `【此处插入XX图】` 格式的占位符。
每个占位符对应一张需要生成的图表。

### 2. 提取图表内容

对每个占位符，按以下优先级确定图表内容：

**方式 A（主路径）：占位符后紧跟的 Mermaid 代码块**

上游 bid-tech-proposal 等 skill 按规范编写时，占位符后面直接跟着一个 ` ```mermaid ` 代码块（见 bid-tech-proposal「图表生成规范」），这个代码块本身就是待渲染的最终内容，不需要再"分析上下文重新设计图表"：

- 若占位符后紧邻 ` ```mermaid ` 代码块 → **直接提取该代码块作为 `.mmd` 文件内容**，跳过步骤3的编写环节，仅按步骤3的语法规范检查/修正明显的语法错误（如节点ID冲突、特殊字符），不改变图表的结构、节点、层级——上游已经根据方案内容确定了这些，本 skill 只负责渲染，不重新设计图表内容
- 若该 Mermaid 代码块与其前后文字描述的模块/层级数量明显不一致（如代码画了3层但文字提到4个子系统）→ 以 Mermaid 代码块为准渲染，同时在处理汇报中提示这处不一致，供人工核实是否代码块本身遗漏了内容

**方式 B（兼容旧格式）：占位符后紧跟 ASCII 字符图**

部分历史文件或非规范渠道生成的文件，占位符后跟着 ``` 代码块包裹的 ASCII art 而非 Mermaid 代码。此时才需要"转换"：

- 应将 ASCII 图内容忠实转换为 Mermaid 语法，ASCII 图定义了图表的结构和层次关系
- **忠实原则**：不添加 ASCII 图中没有的元素，不遗漏已有的元素——转换是格式转换，不是重新设计
- 若 ASCII 图与周边文字描述冲突（结构/数量不一致），以 ASCII 图为准（它是更明确的结构化输入），并在处理汇报中提示这处不一致

**方式 C（无结构化输入时）：仅有章节标题和文字描述**

如果占位符前后既没有 Mermaid 代码块也没有 ASCII 图，只有章节标题和自然语言描述，此时**不得凭标题和常识自行设计图表的具体结构**（如凭空编出层级数量、模块名称、连接关系、人员编制等具体数字）：

- 图表中出现的每一个节点、每一层分组、每一条连线所代表的关系，都必须能在占位符前后的文字描述中找到对应依据——文字描述提到了什么就画什么，没提到的模块/层级/数字不得添加
- 如果文字描述过于简略（如只有一句话），生成的图表也应保持简单（只画文字描述中明确提到的元素），不得为了"图表看起来更专业"而虚构额外的分层、人员数量、技术选型等细节
- 如果连简单的图表都无法从上下文中获得依据（完全没有相关描述），应跳过该占位符并在处理汇报中列出，提示需要先在正文补充相关描述，而不是直接生成一张凭空想象的图

### 3. 判定图表类型与渲染路径

先根据占位符内容判定走哪条渲染路径。**除甘特图和 ER 图外，其余全部走 archify**（出图质量优于 Mermaid）：

| 占位符内容 | 渲染路径 | archify type |
|-----------|---------|-------------|
| 系统架构图 / 总体架构图 / 分层架构 | archify | `architecture` |
| 部署架构图 / 网络拓扑图 | archify | `architecture` |
| 对接 / 集成架构图 | archify | `architecture` |
| 组织架构图 / 三员管理架构 | archify | `architecture` |
| 流程图 / 审批流 / 故障处理 / 运维流程 | archify | `workflow` |
| 时序图 / 服务流程时序 / 请求生命周期 | archify | `sequence` |
| 数据流图 / 数据流向 / ETL 流向 | archify | `dataflow` |
| 状态机 / 生命周期图 / 状态转换 | archify | `lifecycle` |
| 方法论 / 阶段示意图 | archify | `workflow`（或 `lifecycle`） |
| **甘特图（项目实施进度）** | **Mermaid** | — `gantt` |
| **ER 图（数据库实体关系）** | **Mermaid** | — `erDiagram` |

判定补充：
- 描述"静态组件/服务关系"→ `architecture`；"动作/步骤/时序"→ `workflow`/`sequence`；"数据流向"→ `dataflow`；"状态转换"→ `lifecycle`
- 拿不准时，优先 `architecture`（布局最稳）或 `workflow`（覆盖面最广）

### 3a. archify 编写与渲染（主路径）

走 archify 的图，**不编写 `.mmd` 文件**，改为编写 archify JSON IR 文件 `{描述}.{type}.json`（type 见步骤3表）。每种 type 用不同字段定位节点——**理解各自的 layout budget 是写对的关键**。

#### architecture（架构图）—— 用 grid 布局，不手算坐标
```json
{
  "schema_version": 1, "diagram_type": "architecture",
  "meta": { "title": "系统总体架构", "subtitle": "分层架构" },
  "layout": { "mode": "grid", "cols": 4, "cellW": 160, "cellH": 70, "gapX": 40, "gapY": 40, "origin": [60, 60] },
  "components": [
    { "id": "web", "type": "frontend", "label": "Web前端", "row": 0, "col": 0 },
    { "id": "db",  "type": "database", "label": "数据库",  "row": 0, "col": 3 }
  ],
  "connections": [{ "from": "web", "to": "db", "label": "读写" }],
  "boundaries": [], "cards": []
}
```
- 组件用 `row`/`col` 定位，**不写 `pos`/`size`**（grid 自动算）；`cols` 按最大 col+1 取值（3–6），`cellW ≥ 150`
- `type`：`frontend`/`backend`/`database`/`cloud`/`security`/`messagebus`/`external`

#### workflow（流程图）—— 用 lane 泳道 + col，⚠️ 列间距不均
```json
{
  "schema_version": 1, "diagram_type": "workflow",
  "meta": { "title": "故障处理流程" },
  "lanes": [{ "id": "onsite", "label": "现场团队" }, { "id": "expert", "label": "专家团队", "variant": "exception" }],
  "mainPath": ["receive", "handle", "resolve"],
  "nodes": [
    { "id": "receive", "lane": "onsite", "col": 1, "type": "backend", "label": "接收告警" },
    { "id": "handle",  "lane": "onsite", "col": 3, "type": "backend", "label": "现场处理" },
    { "id": "resolve", "lane": "onsite", "col": 5, "type": "security", "label": "问题解决" }
  ],
  "edges": [{ "from": "receive", "to": "handle" }, { "from": "handle", "to": "resolve" }],
  "cards": []
}
```
- 节点用 `lane` + `col`（0–5）定位，省略 viewBox（高度自动算）
- **⚠️ 6 列 x 间距不均**：col 0→1(132)、2→3(130)、4→5(125) 宽松；**col 1↔2(80)、3↔4(70) 太窄**。同一 lane 的连续节点必须用宽松列（如 1,3,5 或 0,2,4），否则 92px 默认节点重叠
- 默认节点 92×52（有 `tag` 时高 68）；跨 lane 连线用 `route: "drop"`；标签压节点就删 `label`
- `lane.variant: "exception"` 用于异常/重试/失败泳道

#### sequence（时序图）—— participants 顶部排列，message 按 y 递增
```json
{
  "schema_version": 1, "diagram_type": "sequence",
  "meta": { "title": "请求生命周期", "viewBox": [920, 760] },
  "participants": [
    { "id": "web", "type": "frontend", "label": "前端" },
    { "id": "api", "type": "backend", "label": "API" }
  ],
  "messages": [
    { "from": "web", "to": "api", "y": 200, "label": "GET /data", "variant": "emphasis" },
    { "from": "api", "to": "web", "y": 280, "label": "200 JSON", "variant": "return" }
  ],
  "segments": [], "activations": [], "cards": []
}
```
- participants 最多 8 个；超过就拆图或合并角色
- message 的 `y` ∈ [160, height−83]，共享水平空间的两条间隔 ≥28px，箭头水平跨度 ≥60px
- message 太密 → 加大 `meta.viewBox` 高度（默认 [920,760]）
- `variant`：`emphasis` 主路径 / `return` 响应 / `dashed` 异步 / `security` 鉴权

#### dataflow（数据流图）—— 用 stage 阶段 + row 行
```json
{
  "schema_version": 1, "diagram_type": "dataflow",
  "meta": { "title": "数据流向", "viewBox": [940, 720] },
  "stages": [{ "label": "采集" }, { "label": "处理" }, { "label": "存储" }],
  "nodes": [
    { "id": "src", "type": "frontend", "label": "数据源",   "stage": 0, "row": 0 },
    { "id": "etl", "type": "backend",  "label": "ETL",      "stage": 1, "row": 0 },
    { "id": "wh",  "type": "database", "label": "数据仓库",  "stage": 2, "row": 0 }
  ],
  "flows": [{ "from": "src", "to": "etl", "label": "原始数据" }, { "from": "etl", "to": "wh", "label": "清洗结果" }],
  "cards": []
}
```
- stages 只能 2–5 个；rows 5 个；节点用 `stage` + `row` 定位，默认 112×58
- **flow 的 `label` 必填**（命名数据资产，如"原始数据"）；`classification` 标敏感度（如"PII"）

#### lifecycle（状态机/生命周期）—— lane id 固定语义
```json
{
  "schema_version": 1, "diagram_type": "lifecycle",
  "meta": { "title": "工单生命周期", "viewBox": [980, 660] },
  "lanes": [
    { "id": "main", "label": "主流程" },
    { "id": "event", "label": "中断处理" },
    { "id": "terminal", "label": "终态" }
  ],
  "states": [
    { "id": "created",  "type": "start",   "label": "已创建",   "lane": "main",     "col": 0, "step": "01" },
    { "id": "handling", "type": "active",  "label": "处理中",   "lane": "main",     "col": 2, "step": "02" },
    { "id": "paused",   "type": "waiting", "label": "挂起待补", "lane": "event",    "col": 1 },
    { "id": "done",     "type": "success", "label": "完成",     "lane": "terminal", "col": 1 }
  ],
  "transitions": [
    { "from": "created", "to": "handling" },
    { "from": "handling", "to": "paused", "variant": "dashed" },
    { "from": "handling", "to": "done", "variant": "emphasis" }
  ],
  "cards": []
}
```
- lane id 固定语义：`main`（必需，顶部相位带）、`terminal`（底部结果带）、其他任意 id（中间事件带，总 lane ≤4）
- main 带 col 0–4；event/terminal 带 col 0–2；状态用 `lane` + `col` 定位
- 状态用 **`type`**（不是 variant）取值：`start`/`active`/`waiting`/`success`/`failure`；`step`（如 "01"）给 main 带状态标序号
- 主生命周期沿 main 带水平铺设；transition 才用 `variant`（`emphasis`/`dashed`/`security`）

#### 共通规则（所有 archify 类型）
- `id` 必须英文，`label`/`title` 用中文
- **忠实原则**：节点/连接/状态来自原始 Mermaid 代码块/ASCII 图/文字描述，不得凭空编造；`row`/`col`/`stage`/`y` 等排布由你定，但不能增删元素
- 渲染命令统一（第1参数是步骤3表中的 type）：
  ```bash
  node scripts/render_archify.mjs <type> input.{type}.json output.png
  # 可选第4参数指定截图缩放（默认 3）
  node scripts/render_archify.mjs <type> input.{type}.json output.png 4
  ```
  脚本会：archify render → check 校验 → 沙盒外 Chrome 截图 → 自动水印
- **校验失败不许跳过、不许切回 Mermaid**：报错会给具体建议（如 `Suggested fix: labelDy +58` 或 `skip a column`），按提示修 JSON 重跑

#### 从已有 Mermaid 代码块转译
占位符后若已有上游写的 Mermaid 代码块（步骤2 方式A），**不要直接用它渲染**，而是读懂其结构后转译成对应 archify type 的 JSON IR：
- Mermaid `graph TD/LR`（组件关系）→ `architecture`；`graph TD`（流程步骤）→ `workflow`
- Mermaid `sequenceDiagram` → `sequence`；`stateDiagram` → `lifecycle`
- 转译时保留原图的节点集合和连接关系，按各 type 的 layout budget 重新排布位置（不改变节点/连接本身）

### 3b. Mermaid 编写（仅甘特图 / ER 图）

只有甘特图和 ER 图走 Mermaid（archify 无此类型），编写 `.mmd` 文件：
- **甘特图**：`gantt`，日期格式 `YYYY-MM-DD`
- **ER 图**：`erDiagram`，关系 `PATIENT ||--o{ NURSING_RECORD : has`
- 节点 ID 用英文、标签用中文；避免 `(){}[]` 等语法字符

### 4. 渲染为 PNG（Mermaid+mmdc 路径，仅甘特图/ER 图）

archify 图表已在步骤 3a 渲染。本步只渲染步骤 3b 编写的甘特图/ER 图 `.mmd` 文件：

```bash
# 单个文件
bash scripts/render.sh input.mmd output.png

# 自定义宽度和缩放
bash scripts/render.sh input.mmd output.png 1400 2
```

参数说明：
- `width`：图片宽度像素（默认 1200，复杂图可设 1400-1800）
- `scale`：缩放因子（默认 2，适合打印；屏幕查看可设 1）

渲染输出的 PNG 保存到目标 markdown 文件的同目录。

**⭐ 自动水印功能**：
`render.sh` 脚本在渲染完成后会自动尝试添加项目名称水印：
- 从当前目录的 `分析报告.md` 中自动提取项目名称
- 在图片右下角添加半透明灰色水印
- 如果未找到项目名称，跳过水印功能（不影响渲染）

水印参数：
- 位置：右下角
- 透明度：50%
- 字体大小：20px
- 边距：15px

**手动添加水印**：
```bash
# 使用 watermark.py 手动添加水印
python3 scripts/watermark.py --auto-project-name diagram.png -o diagram.png
```

### 5. 替换占位符并清理源代码块

将 markdown 中的占位符行替换为图片引用，**同时删除关联的源代码块（Mermaid 代码块或 ASCII 代码块，取决于步骤2走的是哪条路径）**：

**替换前（方式A：Mermaid 代码块，主路径）：**
```
【此处插入系统总体架构图】

​```mermaid
graph TD
    A[系统A] --> B[系统B]
​```
（后续将自动渲染为 PNG 图片）
```

**替换前（方式B：ASCII 图，兼容旧格式）：**
```
​```
┌──────────┐
│  系统A   │──→│  系统B   │
└──────────┘
​```

【此处插入系统总体架构图】
```

**替换后（两种情况都一样，源代码块已删除）：**
```
![系统总体架构图](diagram-系统总体架构图.png)
```

**操作步骤：**
1. 用 edit 工具将 `【此处插入XX图】` 替换为 `![XX图](diagram-XX.png)`（与 PNG 实际保存位置一致：目标 markdown 文件同目录下，文件名带 `diagram-` 前缀，不放入子目录）
2. 找到占位符上方或下方紧邻的源代码块（Mermaid 代码块或 ASCII 文本图），用 edit 工具将整个代码块删除
3. 确认替换后文件中不存在重复的图表表达（一个源代码块 + 一个 PNG）

**重要：删除源代码块。** 占位符替换为图片引用后，必须同时删除其上方或下方的源代码块（``` 包裹的 Mermaid 代码或 ASCII 文本图）。
源代码块仅用于生成/渲染的输入，PNG 生成后已无用途，保留会导致文档中同时出现两个图（一个源码/文字版、一个图片版），排版混乱。

### 6. 图片文件命名

统一命名格式：`diagram-{描述}.png`

例：
- `diagram-系统总体架构图.png`
- `diagram-项目甘特图.png`
- `diagram-故障处理流程图.png`

**archify 源文件保留**：archify 路径编写的 JSON IR 文件命名 `diagram-{描述}.{type}.json`（如 `diagram-系统总体架构图.architecture.json`），与 PNG 同目录（目标 md 所在的 `响应文件/`）。**渲染替换后保留不删**——它是可复用、可追溯的中间产物：渲染失败时修正 JSON 即可直接重渲、fresh session 断点续渲时可复用跳过编写步骤。`bid-md2doc` 只读 `.md`，JSON 不会被误纳入 Word 文档。

## 批量处理

当用户要求处理某个文件的所有图表占位符，或处理所有文件时。

### 断点续渲（fresh session 续做，不重复已完成的工作）

标书图表多（常 20+ 张），渲染可能中途失败或会话中断。**再次调用本 skill（含 fresh session）时，必须先判断进度、精准续做，不从头重渲**：

1. **扫描已完成项 → 跳过**：grep `响应文件/*.md` 中的 `![XX图](diagram-*.png)` 图片引用——这些占位符已渲染并替换完成，跳过不处理。

2. **扫描待处理项**：grep 还在的 `【此处插入.*图】` 占位符——这些需要处理（含从未处理 + 之前渲染失败的）。

3. **对每个待处理占位符，按优先级检查中间产物可复用**：
   - 已有对应 `diagram-{描述}.png` 但占位符未替换（渲染成功、替换中断）→ 直接执行步骤 5 替换，不重新渲染
   - 已有对应 `diagram-{描述}.{type}.json` 但无 PNG（JSON 编写过、渲染失败/中断）→ 复用该 JSON 直接 `node scripts/render_archify.mjs` 重渲，不重新编写；若仍报布局校验错，按"渲染失败排查"修正 JSON 再渲
   - 无任何中间产物 → 走完整流程（步骤 2 提取 → 3a 编写 JSON → 渲染 → 5 替换）

4. **汇报区分**：本次跳过 {N} 张（已完成）、复用重渲 {M} 张、新建 {K} 张、仍失败 {L} 张（列出占位符和失败原因）。

这样 fresh session 后只补没完成的、复用能复用的，不把已渲染的 20+ 张图重跑一遍。

### 按文件分组

当用户要求处理所有文件时：

1. 扫描 `响应文件/` 目录下所有 md 文件中的占位符
2. 按文件分组，逐文件处理（每个文件内走上面的断点续渲逻辑）
3. 跳过非图表类占位符（如 `【此处插入XX扫描件】`、`【此处插入XX功能截图】`）

## 跳过规则

以下占位符**不处理**（需要真实截图/扫描件，不是可生成的图表）：

- `【此处插入XX扫描件】` — 证书/合同扫描件
- `【此处插入XX功能截图】` — 系统功能截图（需真实系统）
- `【此处插入XX查询截图】` — 网站查询截图
- `【此处插入XX效果示意图】` — 需要 UI mockup（可另行处理）

**另有一种情况需跳过并汇报**：图表类占位符本身，但按步骤2的方式C排查后，占位符前后既无 Mermaid 代码块、无 ASCII 图、也无足够的文字描述支撑画出图表内容——此时不得凭标题和常识编造图表结构，应跳过该占位符，在处理汇报中列出并说明"缺少可参考的结构化内容，需先在正文补充描述"，而不是强行生成一张缺乏依据的图。

## 典型调用示例

```
用户：把技术方案里的图画出来
操作：
1. 读取 07-技术方案.md
2. 找到 8 个图表占位符
3. 逐个生成 mermaid → 渲染 PNG → 替换占位符
4. 汇报：8 张图已生成

用户：画一个项目甘特图
操作：
1. 读取上下文中的进度信息
2. 编写 gantt 类型 mermaid
3. 渲染 PNG
4. 插入到指定位置

用户：把系统总体架构图画出来
操作：
1. 识别为架构类 → archify architecture（步骤3a）
2. 编写 XX.architecture.json（grid 布局，忠实于占位符前后的结构依据）
3. node scripts/render_archify.mjs architecture XX.architecture.json diagram-系统总体架构图.png
4. 替换占位符，删除源代码块

用户：把故障处理流程图画出来
操作：
1. 识别为流程图 → archify workflow（步骤3a）
2. 编写 XX.workflow.json（lane 泳道 + col，同一泳道连续节点跳列）
3. node scripts/render_archify.mjs workflow XX.workflow.json diagram-故障处理流程图.png
4. 替换占位符，删除源代码块
```

## 渲染失败排查

1. **中文乱码**：检查 mermaid.json 中 fontFamily 是否包含中文字体
2. **图表溢出**：减少节点数量或增加 width 参数
3. **语法错误**：先用 `npx @mermaid-js/mermaid-cli -i file.mmd -o /dev/null` 验证语法
4. **节点 ID 冲突**：不同 subgraph 中的节点 ID 不能重复
5. **archify 布局校验失败**（最常见）：报错形如 `Label "XX" overlaps component "YY"`、`Nodes "A" and "B" are less than 8px apart` 或 `falls outside the viewBox`。**不要切回 Mermaid 路径**——这是 JSON 写法问题，切 Mermaid 只是逃避。按 type 对症修：
   - **architecture**：用 grid 模式（`row`/`col`），boundary 超画布就增大 `cols` 或 `cellW`，connection label 压节点就删 label
   - **workflow**：同一 lane 连续节点不能用相邻窄列（col 1↔2、3↔4 只隔 70-80px），改用宽松列（1,3,5 或 0,2,4）；edge 太短就删 label 或换 `route: "drop"`
   - **sequence**：participant 超 8 个要拆图；message 太密（报 `overlap horizontally`）加大 `meta.viewBox` 高度；箭头跨度 <60px 说明两个 participant 太近，减少角色
   - **dataflow**：stage 只能 2–5 个，超出报错就合并阶段；flow 的 `label` 必填，缺失会报错
   - **lifecycle**：必须有 `main` lane；状态重叠（报 `across lanes`）用不同 `col` 或 `yOffset` 分开
   - 通用：修正后重跑 `node scripts/render_archify.mjs`，直到输出 `OK: ...`
6. **archify schema 校验失败**：报错形如 `/nodes/2 must NOT have additional properties`。按提示修正 JSON 字段（通常是 `type` 用了 schema 之外的值，或混写了 `pos` 和 `row`/`col`，或字段拼错），修正后重跑
7. **archify-server 未启动**：`render_archify.mjs` 会打印 `archify-server not running, using local Puppeteer`，退为本地模式。在沙盒内运行时本地 Puppeteer 同样不可用，此时应先在沙盒外执行 `bash scripts/start-archify-server.sh` 再重试

## 完成状态

图表生成完成后，输出以下结构化状态摘要：

```
--- BID-MERMAID-DIAGRAMS COMPLETE ---
处理文件数: {N}
生成图表数: {N}
  其中直接使用上游Mermaid代码: {N}
  其中由ASCII图转换: {N}
  其中使用archify渲染: {N}（按类型分：architecture {N} / workflow {N} / sequence {N} / dataflow {N} / lifecycle {N}）
断点续渲统计（若为续做）:
  跳过（已完成）: {N}
  复用重渲（已有JSON/PNG）: {N}
  新建: {N}
  仍失败: {N}，清单：{占位符 + 失败原因}
跳过占位符（非图表类）: {N}
跳过占位符（缺少结构化依据，需补充正文）: {N}，清单：{占位符位置1, 占位符位置2, ...}
图表清单: {diagram-XX.png, diagram-YY.png, ...}
输出目录: 响应文件/
状态: SUCCESS
--- END ---
```
