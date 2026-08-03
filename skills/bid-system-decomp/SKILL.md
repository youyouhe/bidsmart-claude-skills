---
name: bid-system-decomp
description: >
  从分析报告中提取技术需求，进行系统分解，产出全流水线唯一的 system_decomposition.json 契约。
  这是 tech-proposal / requirements / poc / poc-screenshots 共享的系统分解单一事实源——
  任何下游 skill 的系统编号、系统名称、截图占位符一律消费本 json，禁止各自重新划分。
  当 bid-manager 在"分析/核实"之后编排系统分解阶段时触发；也可用户单独要求"系统分解/
  划分子系统/建立系统清单"时触发。
  前置条件：工作目录根存在 分析报告.md。
tools: [read, write, bash]
---

# 系统分解契约生成（全流水线单一事实源）

你是系统分解架构师。你的唯一产物 `system_decomposition.json` 是**整条投标流水线的系统分解契约**——
tech-proposal 拿它填截图占位符，requirements 拿它镜像进 `_metadata.md`，poc 拿它决定生成哪些原型，
poc-screenshots 拿它对齐系统编号。**两套坐标系（招标原文编号 vs S 编号）在这里、且仅在这里被对齐**。

## 核心原则

**单一事实源** — 系统编号（S01/S02/…）在本 skill 首次且唯一地产生。下游任何 skill 不得自造、
重排或跳号 S 编号；要拿系统清单，读 `system_decomposition.json`。

**反幻觉锚点** — 系统分解是一种"聚类推断"，必须可校验。每个 system 必须带 `original_refs`，
回溯到 `分析报告.md#技术需求` 的原文章节号或原文编号（如 `(五)过程管理`、`4.2.1.1`）。
**任何 system 若列不出 original_refs，不得写入 json**——这说明它是凭空捏造的。

**如实计数** — `totals` 里的 ▲/★ 计数必须与分析报告"技术需求"章节逐条核对一致。
若与分析报告完成摘要里的 `▲功能条目` 计数不符，以本 skill 重新清点为准并在状态块标注差异。

## 前置检查（Step 0）

```bash
ls 分析报告.md
```
- 存在 → 继续。
- 不存在 + 交互模式 → 提示用户先运行 `bid-analysis`。
- 不存在 + `AUTO_MODE=true` → 输出状态 `FAILED`，缺失件 `分析报告.md`，绝不伪造 SUCCESS。

## 工作流程

### Step 1：提取技术需求条目

Read `分析报告.md` 的 `## 技术需求` 章节，逐条提取功能条目，记录每条的：
- **原文编号**（4.x.y.z，沿用招标原文体系，不自造）
- **▲/★ 标注**（原样转抄原文标记；无标注记为普通条目）

只到"功能条目"粒度，**不在此步分系统**（分系统是 Step 2 的事）。统计：
- 功能条目总数 `FP`
- ▲ 标注条目数 `▲N`
- ★ 标注条目数 `★N`

### Step 2：分域与系统划分

把 Step 1 的条目按业务领域聚合成系统，分配 S 编号。**分域原则（沿用 bid-requirements 既有规则）**：
- 按业务流程的上下游关系分组
- 同一业务域的功能放在同一系统
- 基础设施/平台/合规类可单独成系统
- 每个系统 3 个以上功能点为宜；过小则合并，过大（>20 功能点）考虑拆分

**编号规则**：`S{序号:02d}`，从 `S01` 起**连续递增，不得跳号**（S01、S02、S03…，禁止 S01、S03、S04）。

每个 system 记录：
- `code`：S01
- `name`：系统名（取自原文业务术语，不自造）
- `original_refs`：该系统覆盖的原文章节号/编号列表（**必填，反幻觉锚点**）
- `function_point_count`：该系统功能点数
- `functionPoints`：该系统功能点明细数组（**必填，见 Step 4**）

**判定 `has_system_structure`**：若本标的是纯硬件采购/纯服务采购，技术需求里没有可聚合成"系统/平台/模块"的软件功能 → `has_system_structure: false`，`systems: []`，直接写 json 并结束（下游各自退化为沿用原文编号）。

### Step 3：规模分级与原型标记

按功能点数分级（阈值沿用 bid-requirements）：
- **小型**（≤6）
- **中型**（7-20）
- **大型**（>20）

为每个 system 标记 `ui_prototype`（bool）：该系统的功能是否属于"数据录入/统计报表/管理配置/流程审批/移动端扫码"等**有 UI 界面**的类别。纯集成/同步/对接类、纯文书报告类 → `ui_prototype: false`（poc 阶段跳过）。

### Step 4：形成功能点明细 `functionPoints[]`（下游截图/需求规格的连接键）

把 Step 1 提取的每一条功能条目归属到 Step 2 划分的系统后，为每条形成功能点对象，
写入所属 system 的 `functionPoints` 数组：

```json
{ "id": "S01-001", "name": "住院医师信息管理", "original_ref": "4.2.1.1" }
```

- `id`：`{code}-{序号:03d}`，**每个系统内从 001 起连续递增、不得跳号**（S01-001、S01-002…，禁止 S01-001、S01-003）
- `name`：功能点名称（取自原文条目文字，可截短，不自造）
- `original_ref`：该功能点的原文编号（反幻觉锚点，必填）

**功能点 id 是全流水线唯一连接键**：bid-tech-proposal 的截图占位符（`【此处插入:截图:<FP-id>】`）、
bid-requirements 的功能点编号、bid-poc 的 manifest 一律消费这里的 `functionPoints[].id`，
禁止下游各自重新枚举。本字段缺失 = 下游截图占位符体系整体失效（历史事故：S3 未产出
functionPoints，S6 运行时由 manager 手工补 json，id 与需求规格枚举结果存在漂移风险）。

> 旧的系统级 `screenshot_placeholder` 字段（`【此处插入{系统标识}功能截图】`）**已废弃，不再生成**——
> 截图占位符已改为功能点粒度，由 bid-tech-proposal 按 `functionPoints[].id` 自行放置。


### Step 5：汇总 totals

```json
"totals": {
  "systems": <系统数>,
  "function_points": <FP>,
  "▲": <▲N>,
  "★": <★N>
}
```
`function_points` 必须等于各 system `function_point_count` 之和；`▲`/`★` 必须与 Step 1 清点一致。

### Step 6：写出契约

写 `system_decomposition.json` 到**工作目录根**（与 `分析报告.md` 并列）：

```json
{
  "schema_version": 2,
  "source": "分析报告.md#技术需求",
  "has_system_structure": true,
  "systems": [
    {
      "code": "S01",
      "name": "住院医师过程管理系统",
      "original_refs": ["(五)过程管理", "4.2.1", "4.2.1.1"],
      "size_grade": "中",
      "function_point_count": 18,
      "ui_prototype": true,
      "functionPoints": [
        { "id": "S01-001", "name": "住院医师信息管理", "original_ref": "4.2.1.1" },
        { "id": "S01-002", "name": "过程记录与跟踪", "original_ref": "4.2.1.2" }
      ]
    }
  ],
  "totals": { "systems": 7, "function_points": 61, "▲": 9, "★": 3 }
}
```

用 `bash` 的 heredoc 或 `write` 工具一次性写出；json 必须合法（写后用 `python -m json.tool` 或 `node -e` 校验一次）。

## 自检（写 json 前必做）

1. **编号连续**：`S01, S02, …, S0N` 无跳号、无重复。
2. **锚点可回溯**：每个 system 的 `original_refs` 都能在 `分析报告.md#技术需求` 找到对应文字。抽 2 个 system 回读原文核对。
3. **计数自洽**：`totals.function_points` == 各 `function_point_count` 之和 == 全部 system 的 `functionPoints[]` 长度之和；`totals.▲` == Step 1 清点；`totals.★` == Step 1 清点。
4. **功能点 id 自洽（强制）**：每个 system 内 `functionPoints[].id` 从 `{code}-001` 起连续无跳号、无重复；每条都有 `name` 与 `original_ref`；每个 system 的 `function_point_count` == 其 `functionPoints.length`。可用一条命令核验：
   ```bash
   node -e "const j=require('./system_decomposition.json');let bad=0;for(const s of j.systems){const fps=s.functionPoints||[];fps.forEach((f,i)=>{const want=s.code+'-'+String(i+1).padStart(3,'0');if(f.id!==want){console.error('id不连续:',f.id,'应为',want);bad=1}});if(fps.length!==s.function_point_count){console.error(s.code,'count不符');bad=1}};const sum=j.systems.reduce((a,s)=>a+(s.functionPoints||[]).length,0);if(sum!==j.totals.function_points){console.error('totals不符',sum);bad=1}process.exit(bad)"
   ```
5. 与分析报告完成摘要里的 `▲功能条目` 计数比对——若不一致，以本 skill 逐条清点结果为准。

## 完成状态块

```
--- BID-SYSTEM-DECOMP COMPLETE ---
状态: SUCCESS
系统数: {totals.systems}
功能点: {totals.function_points}
▲ 标注: {totals.▲}
★ 标注: {totals.★}
has_system_structure: {true|false}
输出: system_decomposition.json
--- END ---
```

`has_system_structure: false` 时也输出 SUCCESS（这是合法状态，非软件标的），下游据此跳过系统相关环节。

`AUTO_MODE=true` 下若 `分析报告.md` 缺失或自检失败 → `状态: FAILED`，标注缺失件/失败原因，绝不伪造 SUCCESS。
