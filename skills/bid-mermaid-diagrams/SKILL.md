---
name: bid-mermaid-diagrams
description: >
  为投标文件中的图表占位符渲染 Mermaid 图为 PNG 图片。
  扫描 markdown 文件中的【此处插入XX图】占位符，优先提取占位符后已有的
  Mermaid 代码块直接渲染（上游 bid-tech-proposal 已按规范编写好代码），
  兼容处理旧格式的 ASCII 图转换，渲染为高清 PNG，
  然后替换占位符为 markdown 图片引用。
  架构类图表（系统架构图/总体架构图/部署架构图/拓扑图）默认改用内置的 archify 渲染引擎，
  效果更专业；流程图/组织架构图/甘特图/ER图仍走 Mermaid+mmdc 路径。
  当用户要求画图、生成图表、替换图表占位符、为技术方案/实施方案画架构图时触发。
---

# Mermaid 图表生成与渲染

你是视觉设计师——把方案变成专业图表的角色。架构图、流程图、拓扑图，每张图都直接影响评委对技术方案的直观印象。图表语法错误 = 渲染失败留白，图文不符 = 扣印象分。所以：**优先使用上游已给出的 Mermaid 代码，不重新设计图表结构；确保语法正确、一次渲染成功**。

## 依赖

- Node.js（已预装）
- @mermaid-js/mermaid-cli（已预装，禁止自行安装）
- mermaid_render 工具（系统内置扩展，优先使用）
- archify（`scripts/archify/`，已随本 skill 内置，无需安装，架构类图表的渲染引擎）
- archify render server（`scripts/archify-server.mjs`，需在沙盒外预先启动，端口 18800）

## 核心工具

- **mermaid_render**：系统内置工具，直接传入 Mermaid 代码和输出路径即可渲染，优先使用（流程图/组织架构图/甘特图/ER图走这条路径）
- 渲染脚本：`scripts/render.sh`（备用方案，Mermaid+mmdc 路径）
- 主题配置：`scripts/mermaid.json`（蓝色专业主题，支持中文）
- **archify 渲染脚本**：`scripts/render_archify.mjs`（架构类图表走这条路径，优先通过 HTTP 调用沙盒外的 archify-server，服务不在线才尝试本地 Puppeteer）

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

### 3. 编写/校验 Mermaid 代码

若走方式A（已有代码块）：仅做语法校验和明显错误修正，见下方注意事项，不重新设计结构。
若走方式B/C（需要新写代码）：根据步骤2确定的内容编写 `.mmd` 文件。Mermaid 代码要求：

- **中文标签**：所有节点文字使用中文
- **层次清晰**：用 subgraph 表达分层/分组关系
- **配色通过主题控制**：不在 mmd 文件中硬编码颜色（除非特别需要区分）

#### 图表类型对照

| 占位符内容 | Mermaid 图类型 | 说明 |
|-----------|---------------|------|
| XX架构图 | `graph TD` | 分层架构，用 subgraph 表达层 |
| XX拓扑图 | `graph TD` | 网络拓扑，用 subgraph 表达区域 |
| XX流程图 | `graph TD` | 流程图，用菱形表达判断 |
| ER图 | `erDiagram` | 实体关系图 |
| 甘特图 | `gantt` | 项目进度甘特图 |
| 组织架构图 | `graph TD` | 树形组织结构 |
| 对接/集成架构图 | `graph LR` | 左右布局，表达系统间关系 |
| 方法论/示意图 | `graph LR` | 流程或阶段示意 |

#### Mermaid 编写注意事项

1. **节点 ID 用英文**，显示标签用中文括号包裹：`A[系统总体架构]`
2. **subgraph 标题用中文**：`subgraph 基础设施层`
3. **避免特殊字符**：标签中避免 `()` `{}` `[]` 等 mermaid 语法字符，用全角替代
4. **连接线标签简短**：`A -->|数据同步| B`
5. **gantt 图日期格式**：`YYYY-MM-DD` 或相对周数
6. **erDiagram 关系**：`PATIENT ||--o{ NURSING_RECORD : has`
7. **节点文字过长时换行**：在引号标签中换行无效，应缩短文字或拆分节点

### 3.5 架构类图表：改用 archify 渲染（默认路径）

当占位符内容属于**架构类**（系统总体架构图、总体架构图、部署架构图、拓扑图、对接/集成架构图——即上表中判定为 `graph TD`/`graph LR` 且描述的是组件/服务/基础设施关系而非流程步骤的图）时，默认改用内置的 archify 渲染引擎代替 mmdc，效果更专业（原生 4× 高清栅格化、CJK 文字宽度自动测量、深浅色主题一致）。

**判定规则**：
- 占位符文字含"架构""拓扑""部署图""集成架构"→ 走 archify
- 占位符文字含"流程""组织架构""甘特""ER图""方法论示意"→ 仍走 3./4. 的 Mermaid+mmdc 路径，不受本节影响
- 拿不准时，看图表描述的是"静态组件关系"（archify）还是"动作/时序/层级隶属"（Mermaid）

**步骤（替代步骤3/4，仅用于架构类图表）：**

1. **不编写 `.mmd` 文件**，改为编写 archify 的 JSON IR 文件 `{描述}.architecture.json`。

   **⚠️ 必须使用 grid 布局模式（不要手算 `pos`/`size` 坐标）**：手算像素坐标极易导致标签与组件重叠、组件超出画布，archify 校验器会直接拒绝渲染。使用 grid 模式时，只需给每个组件写 `row`/`col` 整数，渲染器自动计算位置：

   ```json
   {
     "schema_version": 1,
     "diagram_type": "architecture",
     "meta": { "title": "系统总体架构", "subtitle": "..." },
     "layout": {
       "mode": "grid",
       "cols": 4,
       "cellW": 160,
       "cellH": 70,
       "gapX": 40,
       "gapY": 40,
       "origin": [60, 60]
     },
     "components": [
       { "id": "web",  "type": "frontend", "label": "Web前端",  "sublabel": "Vue3",       "row": 0, "col": 0 },
       { "id": "gw",   "type": "backend",  "label": "API网关",  "sublabel": "鉴权/限流",   "row": 0, "col": 1 },
       { "id": "svc",  "type": "backend",  "label": "业务服务", "sublabel": "SpringBoot", "row": 0, "col": 2 },
       { "id": "db",   "type": "database", "label": "数据库",   "sublabel": "MySQL",      "row": 0, "col": 3 }
     ],
     "connections": [
       { "from": "web", "to": "gw",  "label": "HTTPS" },
       { "from": "gw",  "to": "svc" },
       { "from": "svc", "to": "db",  "label": "SQL" }
     ],
     "boundaries": [],
     "cards": []
   }
   ```

   **grid 参数说明**：
   - `cols`：总列数（决定画布宽度，按最大 col+1 取值，通常 3–6）
   - `cellW` / `cellH`：每格宽高（px），中文标签建议 `cellW ≥ 150`
   - `gapX` / `gapY`：格间距，建议 30–50
   - `origin`：左上角起始坐标，默认 `[60, 60]` 留出边距即可
   - 组件只写 `row`/`col`，**不写 `pos`/`size`**——两者并存时 `pos` 优先，混用会产生坐标冲突

   **其他字段规则**：
   - `type` 只能是 `frontend`/`backend`/`database`/`cloud`/`security`/`messagebus`/`external`
   - `id` 必须英文（Schema 约束），`label`/`sublabel` 用中文
   - **忠实原则**依然适用：节点集合、层级归属、连接关系来自原始 Mermaid/ASCII 图/文字描述，不得凭空编造；grid 的 `row`/`col` 是视觉排布，由你决定，但不能增删节点
   - `connections` 中的 `label` 若文字较长容易与组件重叠，改成空（省略 `label` 字段）或用 `cards` 说明，比强行塞标签更稳
2. **渲染**：
   ```bash
   node scripts/render_archify.mjs architecture input.architecture.json output.png
   ```
   脚本内部会：调用 archify 渲染出 HTML → 用 archify 自带的 `check` 做 schema/布局校验（校验失败会打印具体错误路径并退出，此时修正 JSON 后重跑，不要跳过校验直接使用）→ 用无头 Chrome 截图导出高清 PNG → 自动尝试添加水印（同 render.sh 逻辑，从 `分析报告.md` 提取项目名称）。
   - 可选第4个参数指定截图缩放倍数（默认 3）：`node scripts/render_archify.mjs architecture input.json output.png 4`
3. **产物同步**：与步骤5相同，只是被删除的源代码块换成了 `.architecture.json` 对应的说明块（如果占位符后确实写了 JSON 代码块作为草稿，也要一并清理），最终替换为图片引用。

### 4. 渲染为 PNG（Mermaid+mmdc 路径，非架构类图表）

将 `.mmd` 文件渲染为 PNG：

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

## 批量处理

当用户要求处理某个文件的所有图表占位符时：

1. 读取文件，提取所有 `【此处插入XX图】` 占位符列表
2. 逐个处理：提取内容（优先用已有Mermaid代码块）→ 编写/校验 mmd → 渲染 → 替换
3. 汇报处理结果

当用户要求处理所有文件时：

1. 扫描 `响应文件/` 目录下所有 md 文件中的占位符
2. 按文件分组，逐文件处理
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
1. 识别为架构类图表 → 走 archify 路径（步骤3.5）
2. 编写 XX.architecture.json（components/connections，忠实于占位符前后已有的结构依据）
3. node scripts/render_archify.mjs architecture XX.architecture.json diagram-系统总体架构图.png
4. 替换占位符，删除源 JSON 说明块
```

## 渲染失败排查

1. **中文乱码**：检查 mermaid.json 中 fontFamily 是否包含中文字体
2. **图表溢出**：减少节点数量或增加 width 参数
3. **语法错误**：先用 `npx @mermaid-js/mermaid-cli -i file.mmd -o /dev/null` 验证语法
4. **节点 ID 冲突**：不同 subgraph 中的节点 ID 不能重复
5. **archify 布局校验失败**（最常见）：报错形如 `Label "XX" overlaps component "YY"` 或 `Component "ZZ" falls outside the viewBox`。**不要切回 Mermaid 路径**——这是 JSON 写法问题，切 Mermaid 只是逃避。正确做法：
   - 若使用了手算 `pos`/`size`：改用 grid 模式（`layout.mode: "grid"` + 每个组件写 `row`/`col`），彻底消灭坐标类错误
   - 若 grid 模式下 boundary 超出画布：增大 `cols` 或 `cellW`/`cellH`，或把 boundary 成员改到更靠中间的 `row`/`col`
   - 若 connection label 压节点：删掉该 label（省略 `label` 字段），或把说明移到 `cards`
   - 修正后重跑 `node scripts/render_archify.mjs`，直到命令输出 `OK: ...` 为止
6. **archify schema 校验失败**：报错形如 `/components/2 must NOT have additional properties`。按提示修正 JSON 字段（通常是 `type` 用了 schema 之外的值，或混写了 `pos` 和 `row`/`col`），修正后重跑
7. **archify-server 未启动**：`render_archify.mjs` 会打印 `archify-server not running, using local Puppeteer`，退为本地模式。在沙盒内运行时本地 Puppeteer 同样不可用，此时应先在沙盒外执行 `bash scripts/start-archify-server.sh` 再重试

## 完成状态

图表生成完成后，输出以下结构化状态摘要：

```
--- BID-MERMAID-DIAGRAMS COMPLETE ---
处理文件数: {N}
生成图表数: {N}
  其中直接使用上游Mermaid代码: {N}
  其中由ASCII图转换: {N}
  其中使用archify渲染（架构类）: {N}
跳过占位符（非图表类）: {N}
跳过占位符（缺少结构化依据，需补充正文）: {N}，清单：{占位符位置1, 占位符位置2, ...}
图表清单: {diagram-XX.png, diagram-YY.png, ...}
输出目录: 响应文件/
状态: SUCCESS
--- END ---
```
