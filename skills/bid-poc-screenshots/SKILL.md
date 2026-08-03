---
name: bid-poc-screenshots
description: >
  将系统原型页面（poc/ 目录）截取为 PNG 截图，并按 placeholders.json 对照表替换技术标书中的【此处插入:截图:<id>】占位符。
  纯机械步骤，无 LLM 推理。id 查表精确定位，不做文字/前缀/label 猜测（对照表机制见 packages/bidsmart-skills/CLAUDE.md "Placeholder registry" 段）。
  当用户要求"插入原型截图"、"替换功能截图占位符"、"poc截图"时触发。
  前置条件：响应文件/ 目录下已存在技术标书 .md 文件，工作目录根有 placeholders.json，且系统原型已生成（workDir/poc/ 下有子目录）。
tools: [read, write, bash, poc_screenshot]
requires: [puppeteer]
---

# 系统原型截图占位符替换

## 工作模式

**纯机械操作** —— 不需要 LLM 编写任何内容，只做对照表查表 + 文本查找替换 + 调用截图脚本。**id 是唯一连接键，不做文字/前缀/label 猜测**（参见 `packages/bidsmart-skills/CLAUDE.md` "Placeholder registry" 段）。

## 前置检查

1. 确认 POC 目录存在：
   ```bash
   ls -d <workDir>/poc/*/index.html 2>/dev/null | wc -l
   ```
   如果返回 0，则没有 POC 可截图，输出状态 `SKIPPED` 并结束。

2. 确认技术标书文件与对照表存在，并归一化旧表路径：
   ```bash
   ls 响应文件/*.md 2>/dev/null
   python3 $SKILLS_BASE_PATH/bid-manager/scripts/placeholder_registry.py normalize 2>/dev/null
   python3 $SKILLS_BASE_PATH/bid-manager/scripts/placeholder_registry.py stats
   ```
   - 没有 .md 文件 → 状态 `SKIPPED` 并结束。
   - 没有 placeholders.json → 走 §3 legacy 兜底路径（仅扫旧式无 id 占位符）。
   - `source_file` 一律为**工作目录根相对路径**（normalize 已保证），直接打开，禁止自行拼接 `响应文件/` 前缀。

3. 探活浏览器运行时（避免 Puppeteer 在沙箱外启动失败后空等超时，详见 gotchas.md）：
   ```bash
   curl -s /api/v1/health/preflight 2>/dev/null | grep -o '"puppeteer":"[^"]*"' || true
   ```
   不可用时直接 `状态: SKIPPED, 原因: 浏览器运行时不可用`，不徒劳调用。

## 工作流程

### 1. 运行截图工具（多视图自动发现）

调用 `poc_screenshot` 工具（注册为 agent extension，在沙箱外执行 Puppeteer）：

```
poc_screenshot({ pocDir: "<workDir>/poc", outputDir: "<workDir>/响应文件" })
```

工具会**自动发现每个 POC 页面中的 Tab/功能按钮**，加载页面后先截取默认视图，再逐一点击发现的 Tab 按钮截取各功能视图，并为每个视图记录所属功能点 id（`functionPointId`）。返回 JSON 截图清单，并把 **functionPointId → file 映射**写入 `<workDir>/响应文件/screenshots-map.json`（含跨视图去重复用，供本 skill 查表）。

**核对返回的截图数量**：若截图为 0 张或工具报错，完成状态块必须标 `FAILED` 并写明原因（参见 gotchas.md，禁止用"待手动生成"掩盖失败）。

screenshots-map.json 示例：
```json
{
  "version": 1,
  "views": [
    {"functionPointId": "S04-001", "file": "poc-S04-性能预报系统-实时预报.png"},
    {"functionPointId": "S04-002", "file": "poc-S04-性能预报系统-方案比选.png"},
    {"functionPointId": "S05-001", "file": "poc-S05-系统管理平台-S05-001.png"}
  ]
}
```

### 2. 查表替换（主路径：对照表 id 精确定位）

读工作目录根的 `placeholders.json`，filter `type == "screenshot" && status == "pending"`。对每个 item：

**(a) 用 item.id 在 item.source_file 精确定位占位符** —— 正则匹配 `【此处插入:截图:<item.id>】`，id 取 item.id 原值（= `system_decomposition.json` 中该功能点的 FP-id）。**不做文字/前缀/label 猜测，id 是唯一连接键。**

**(b) 解析 id → png 文件**：
- 首选：读 `响应文件/screenshots-map.json`，构建 `{functionPointId: file}` 映射，取 `item.id` 对应的 file（含跨视图去重复用）。
- 兜底（screenshots-map.json 缺失或该 id 未命中）：回退命名约定 `poc-<subdir>-<id>.png`，其中 `<subdir>` 由 `system_decomposition.json` 的 `code+name`（经文件系统不安全字符 `/ \ : * ? " < > |` 及空格归一化为 `-`）得到。
- 仍无匹配 → **保留占位符不动**，item 维持 `pending` 供 bid-assembly 标红（不伪造 done）。

**(c) 替换占位符**为 Markdown 图片引用：

```
【此处插入:截图:S04-001】
→
![<item.label 或 系统名 - 功能点>](<file>)
```

label 优先取 item.label；缺失时取 `system_decomposition.json` 里该功能点的 name。**label/图注中禁止出现 "POC"、"概念验证"、"Demo" 字样**——这些文字会进入标书正文，评委可见，一律用"系统原型"口径（与 bid-tech-proposal §4.2.1 措辞规则一致）。

**(d) 回填 placeholders.json（用权威脚本，禁止手改 JSON）**：
```bash
python3 $SKILLS_BASE_PATH/bid-manager/scripts/placeholder_registry.py mark-done --id <item.id> --asset <file 路径>
```

### 2.5 孤儿截图兜底插入（确保每张 POC 截图都进标书）

§2 只替换**已登记占位符**的截图。常见缺陷：上游 `bid-tech-proposal` 漏给某些系统/功能点建截图占位符，但 `bid-poc` 仍生成了对应原型视图 → 这些**孤儿截图**若无兜底会全部丢失（标书缺图）。本步强制让每张捕获的截图都落到正文。

读 `响应文件/screenshots-map.json`，**展开**其 `screenshots[].screenshots[]` 全部视图（含 `functionPointId` 与 `file`），与 placeholders.json 的 screenshot item.id 集合比对：

1. **识别孤儿**：视图的 `functionPointId` ∉ 任何 screenshot item.id；以及 `functionPointId=null` 的"默认视图"（文件名形如 `poc-<系统>.png`）。
2. **逐张补插**（纯机械，不写论述文字）：
   - **定位系统**：由 `functionPointId` 前缀（`S01-005`→`S01`）或文件名（`poc-S01-…`→`S01`）。
   - **定位小节**：在技术方案文件中（通常 `响应文件/05-总体技术方案.md`；找不到则 `grep -rl <系统名> 响应文件/*.md`）找到该系统的小节标题（`##`/`###` 含系统编号 S01 或系统名）。
   - **插入点**：优先该功能点小节末尾（`#### S01-005 …` 之后、下一个 `####`/`###` 之前）；功能点小节不存在则插到系统小节末尾。
   - **插入内容**：一行 `![系统原型 - <功能点名|系统名>](<file>)`（**裸文件名，不加 `响应文件/` 前缀**——md 文件与截图同在 `响应文件/` 下，generate_docx.js 的 baseDir 已是该目录，加前缀会变成 `响应文件/响应文件/...` 导致 Word 找不到图）。措辞用"系统原型"，**禁 POC/概念验证/Demo**。
3. **默认视图去重**：同一系统只要已有任意截图落位，其 `functionPointId=null` 默认视图**不再补插**；仅当某系统**零张落位**时，用默认视图兜底插一张，确保每个有 POC 的系统至少出现一张原型截图。
4. **回填对照表**：每张补插的截图用权威脚本登记（脚本幂等 upsert，已存在则跳过 status/asset 之外的字段——对补插项需先 register 再 mark-done）：
   ```bash
   python3 $SKILLS_BASE_PATH/bid-manager/scripts/placeholder_registry.py register \
     --id <functionPointId 或 S0N-prototype> --type screenshot --source-file <落位的 md 文件>
   python3 $SKILLS_BASE_PATH/bid-manager/scripts/placeholder_registry.py mark-done \
     --id <functionPointId 或 S0N-prototype> --asset <file>
   ```
   使 bid-assembly 闭环校验通过。

> 本步是"截图不进 Word"的最终兜底：即使上游占位符缺失/命名不一致，只要生成了原型视图，就保证它进入标书。

### 3. legacy 兜底扫描（无 id 的旧占位符）

`placeholders.json` 缺失、或正文残留旧式无 id 占位符时，扫描 `响应文件/` 下所有 .md 文件：

```bash
grep -n '【此处插入.*功能截图】' 响应文件/*.md
```

对命中的 legacy 占位符（如 `【此处插入S04性能预报系统功能截图】`），沿用旧的**系统编号 `S\d{2}` 匹配 subDir** 方式分配默认视图截图（多截图时按视图 label 关键词匹配功能小节末尾插入）。**此为兜底，新项目一律走 §2 对照表主路径；legacy 占位符不写回 placeholders.json。**

### 4. 自检

所有 `type == "screenshot"` 的 item 处理完后：

```bash
grep -c '【此处插入:截图:' 响应文件/*.md
```

source_file 中**不得残留** `【此处插入:截图:...】`；残留则对应 item 维持 `pending`（不伪造 done），供 bid-assembly 闭环标红。

### 5. 输出结果

```markdown
--- BID-POC-SCREENSHOTS COMPLETE ---
状态: SUCCESS | SKIPPED | FAILED
截图总数: N
替换成功(id 匹配): M
补插孤儿截图(§2.5 兜底): K2
未匹配占位符(仍 pending): K
截图清单:
  - poc-S04-性能预报系统.png (462 KB)
  - poc-S05-系统管理平台.png (319 KB)
--- END ---
```

如果无 POC 或无占位符，状态为 `SKIPPED`。
