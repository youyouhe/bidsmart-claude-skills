---
name: bid-md2doc
description: >
  将 响应文件/ 目录下的 Markdown 文件转换为格式化的 Word (.docx) 文档。
  自动从分析报告和商务文件中读取项目名称、公司名称等信息，
  通过命令行参数调用 generate_docx.js 脚本生成 Word 文件。
  当用户要求生成Word文档、转换MD为docx、导出响应文件时触发。
  前置条件：响应文件/ 目录下已有编写完成的 .md 文件。
---

# MD 转 Word 文档

你是排版师——流水线的最后一道工序，把所有Markdown变成客户拿到手的Word文档。标题层级乱 = 目录生成错，图片路径断 = 正文留白，分页不对 = 整本标书散架。所以：**配置精确、路径正确、转换零损耗**。

## 核心功能

将 `响应文件/` 目录下的 Markdown 文件转换为格式化的 Word (.docx) 文档，
支持标题层级、表格、图片嵌入、页眉页脚、分页等。
支持单册输出（合并为一个文件）和多册输出（按册别生成多个文件）。

## 工作流程

### 0. 前置检查（必须先执行）

检查 `响应文件/` 目录下是否存在编写完成的 `.md` 文件：

```bash
ls 响应文件/*.md 2>/dev/null
```

- **存在** → 继续第 1 步
- **不存在或目录为空** → 停止，告知用户："`响应文件/` 目录下未找到 `.md` 文件，生成 Word 文档需要先完成 `bid-tech-proposal`/`bid-commercial-proposal` 的编写（如需图表和扫描件，还需先跑 `bid-mermaid-diagrams`/`bid-material-search`）。是否现在运行？"
  - 用户同意 → 调用对应 skill 后继续
  - 用户不同意 → 暂停本次任务
- **AUTO_MODE=true** 时：不可交互等待，直接在完成状态摘要中标注 `FAILED`，说明"响应文件/ 为空，无法生成 Word"，交由 bid-manager 处理

### 1. 读取项目信息（仅读取文本文件，不要读取图片）

**⚠️ 重要：只读取 .md 文本文件，不要使用 Read 工具读取 .png 或 .jpg 图片文件**

#### 1.1 从分析报告读取项目名称和册别结构

分析报告（`分析报告.md`）由 bid-analysis 生成，有固定章节结构。**精确提取位置**：

| 字段 | 来源章节 | 提取方式 |
|------|---------|---------|
| **项目全称** | `## 项目概况` → 表格中"项目名称"行 | 读取表格第二列的值 |
| **采购编号** | `## 项目概况` → 表格中"采购编号"或"项目编号"行 | 同上 |
| **采购人** | `## 项目概况` → 表格中"采购人"或"采购单位"行 | 同上 |
| **册别结构** | `## 投标文件册别结构`（如存在） | 读取册别数量和每册文件列表 |

如果分析报告中找不到上述章节或字段：
- 交互模式 → 询问用户补充项目名称
- AUTO_MODE → 从文件名或工作目录名推断，标注"项目名称来自推断"

#### 1.2 从商务文件读取公司名称

公司名称从**权威文件**提取（仅以下位置，避免误提取采购人或案例客户名）：

1. **报价函**（如 `01-报价函.md`）→ "投标人名称："或"单位名称："后的名称
2. **封面**（如 `00-封面.md` 或类似编号）→ 投标人/供应商名称区域
3. **授权委托书** → 授权单位名称

提取到的名称应取**全称**（用于页脚），**简称**的生成规则见 1.3。

如果上述文件均不存在或找不到公司名称：
- 交互模式 → 询问用户："未在报价函/封面中找到公司全称，请提供。"
- AUTO_MODE → 标注 `FAILED`，说明"无法确定公司名称"

#### 1.3 判定输出模式与命名规则

根据册别结构判定输出模式：
- **单册模式**：分析报告未提及册别结构或标注"单册" → 生成一个 Word 文件
- **多册模式**：分析报告指定了多册结构 → 每册生成一个独立 Word 文件

**简称生成规则**（用于拼接输出文件名如 `响应文件-{公司简称}-{项目简称}.docx`）：

| 要素 | 规则 | 示例 |
|------|------|------|
| **公司简称** | 从全称中提取核心名称：去掉"有限公司""股份有限公司"等后缀 + 去掉地名前缀（如"北京""深圳"） | "珞信通达（北京）科技有限公司" → "珞信通达" |
| **项目简称** | 从项目全称中提取关键词：取前 15-20 字，去掉"采购项目""竞争性磋商"等通用词 | "XX单位被装仓储无纸化办公建设项目" → "被装仓储无纸化办公建设" |

**输出文件名**（默认格式）：
```
响应文件-{公司简称}-{项目简称}.docx
```

多册模式文件名需注明册别：
```
投标文件（{册别名称}）-{投标人简称}.docx
```

### 2. 运行生成脚本

**⚠️ 重要：不要复制脚本到工作目录！直接通过命令行参数调用原始脚本。**

**脚本路径**（按优先级尝试）：

```
# 主路径（smartbid-platform monorepo）
/mnt/oldroot/home/bird/xyy/smartbid-platform/packages/bidsmart-skills/skills/bid-md2doc/scripts/generate_docx.js

# 备选路径（独立 checkout 的 skills 仓库）
/path/to/bidsmart-claude-skills/skills/bid-md2doc/scripts/generate_docx.js
```

先用 `test -f` 检查主路径是否存在，不存在则让用户提供备选路径。AUTO_MODE 下主路径不存在 → 标注 `FAILED`。

通过 JSON 参数传入配置：

```bash
node {脚本路径} '{
  "inputDir": "{工作目录}/响应文件",
  "outputFile": "响应文件-{公司简称}-{项目简称}.docx",
  "headerText": "{项目全称} 响应文件",
  "footerCompany": "{公司全称}"
}'
```

**⚠️ npm 依赖检查**：运行前确认 `docx` npm 包已安装：

```bash
test -d "$(dirname {脚本路径})/node_modules/docx" || echo "ERROR: docx npm 包未安装"
```

#### 2.1 单册模式

一次调用。**必须指定 `excludeFiles`** 排除 S8 和 S10 自身产出的内部文件：

```bash
node {脚本路径} '{"inputDir":"{workDir}/响应文件","outputFile":"{workDir}/响应文件-{公司简称}-{项目简称}.docx","headerText":"{项目全称} 响应文件","footerCompany":"{公司全称}","excludeFiles":["核对报告.md","装订指南.md","00-目录.md","crossref_mapping.json","扫描件资料清单.md","扫描件替换完成报告.md","信息填写进度报告.md","Word文档待完善清单.md"]}'
```

#### 2.2 多册模式

多次调用，每次传不同参数。每册都需排除内部文件：

```bash
# 第一册：资格证明文件
node {脚本路径} '{"inputDir":"{workDir}/响应文件","outputFile":"{workDir}/投标文件（资格证明文件）-{投标人简称}.docx","headerText":"{采购编号} 投标文件（资格证明文件）","footerCompany":"{公司全称}","includeFiles":["00-资格证明文件.md"]}'

# 第二册：商务技术文件
node {脚本路径} '{"inputDir":"{workDir}/响应文件","outputFile":"{workDir}/投标文件（商务技术文件）-{投标人简称}.docx","headerText":"{采购编号} 投标文件（商务技术文件）","footerCompany":"{公司全称}","excludeFiles":["核对报告.md","装订指南.md","00-目录.md","crossref_mapping.json","00-资格证明文件.md"]}'
```

字段说明：
- `inputDir`：`响应文件/` 的绝对路径
- `outputFile`：输出文件路径（建议写绝对路径或相对于 inputDir）
- `headerText`：页眉文字
- `footerCompany`：页脚公司名
- `excludeFiles`：排除的文件列表。**始终包含 S8/S10 内部文件**（核对报告、装订指南、00-目录、crossref_mapping 等）
- `includeFiles`：仅包含的文件列表（优先于 excludeFiles）

**执行失败处理**（见下方"异常处理"表）：

| 错误类型 | 症状 | 处理 |
|---------|------|------|
| Node.js 未安装 | `node: command not found` | 标注 `FAILED`，建议 `apt install nodejs` |
| npm 包缺失 | `Cannot find module 'docx'` | 标注 `FAILED`，建议 `cd {脚本目录} && npm install` |
| 输出文件被占用 | `EBUSY` 错误 | 标注 `FAILED`，建议"关闭 Word 后重试" |
| JSON 解析异常 | 脚本报错但非上述原因 | 检查特殊字符（引号、反斜杠）是否被 shell 错误转义 |

### 3. DocScan 后期增强（可选，需 DocScan 服务在线）

**⚠️ DocScan 是一个可选的外部服务。** 此步骤在 DocScan 在线时自动执行，离线时优雅跳过——不影响 generate_docx.js 已产出的 .docx 文件。

**多册模式处理**：步骤 3.1-3.4 对每个 docx 文件逐个执行完整循环（上传→清扫→交叉引用→下载）。每个 docx 独立处理，一个失败不影响其他。

#### 3.0 检查 DocScan 可用性

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8800/api/health
```

- **返回 200** → 继续 3.1
- **连接失败/超时** → 跳过整个步骤 3，输出提示：
  > DocScan 服务（`http://localhost:8800`）当前不可用，跳过后期增强（交叉引用、占位符清扫）。已生成的 docx 文件不受影响，可正常使用。
  
  然后直接跳到步骤 4（报告生成结果）
- **AUTO_MODE=true** 时 DocScan 不可用 → 同上跳过，在完成状态中标注"DocScan 离线，跳过后期增强"

#### 3.1 上传 docx 到 DocScan

将 generate_docx.js 生成的 docx 上传到 DocScan，使其可被编辑：

```bash
FID=$(curl -s -X POST http://localhost:8800/api/docx/upload \
  -F "file=@{outputFile路径}" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "DocScan FID: $FID"
```

**多册模式**：
```bash
# 对每个 docx 执行
for docx in "{workDir}/投标文件（资格证明文件）-{投标人简称}.docx" "{workDir}/投标文件（商务技术文件）-{投标人简称}.docx"; do
  FID=$(curl -s -X POST http://localhost:8800/api/docx/upload -F "file=@$docx" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
  echo "DocScan FID for $docx: $FID"
  # 记录 FID → 文件映射，供 3.2-3.4 循环使用
done
```

#### 3.2 占位符最终清扫

```bash
curl -s http://localhost:8800/api/docx/$FID/placeholders | python3 -c "
import json, sys
data = json.load(sys.stdin)
phs = data.get('placeholders', [])
print(f'占位符总数: {data[\"count\"]}')
for ph in phs:
    print(f'  {ph[\"id\"]}: {ph[\"text\"]}  [{ph[\"location\"]}]  {ph[\"path\"]}')
"
```

**分类判断**（LLM 分析 placeholders 输出）：
- **预期存在的占位符**：如 `【此处插入营业执照扫描件】`、`【此处插入XX图】` — 这些是扫描件/图表的正常占位，需用户后续手动替换为实际扫描件
- **应已替换但遗漏的占位符**：如 `【公司名称】`、`【项目名称】`、`【待填写】` — 这些应在编写阶段已被替换
- **信息待确认占位符**：如 `【此处插入截图】` — 需标注提醒

**处理**：
- 仅做检测和报告，不做自动替换（占位符替换在 markdown 级别由 `bid-material-search` 和 `bid-mermaid-diagrams` 完成）
- 发现遗漏占位符时 → 在完成状态中列出数量和类型
- AUTO_MODE=true → 在完成状态中标注"发现 N 个未替换占位符"

#### 3.3 交叉引用：为索引表填入页码

这是 DocScan 提供的**独有核心能力**——在正文中标记章节位置，在索引表中插入自动页码字段，经 ONLYOFFICE 重算后填入真实页码。

**前置条件**：文档中存在索引表（如 `00-目录.md` 转换后的表格）。

**页码列的两种策略**：

| 策略 | 适用场景 | 操作 |
|------|---------|------|
| **A: 专用页码列** | 索引表有"页码"列（推荐） | 直接以"页码"列的 cellPath 为目标 |
| **B: 追加到附件名称列** | 索引表无"页码"列（回退） | 以"附件名称"列的 cellPath 为目标，crossref 会自动在文本后追加"第X页" |

判断方法：读取 `GET /api/docx/{fid}/tables`，检查索引表的表头行是否含"页码"列。有 → 策略 A；无 → 策略 B。

**优先读取 S8 生成的映射**：如果 `响应文件/crossref_mapping.json` 存在（由 `bid-assembly` 步骤 5.5 生成），优先使用其中的 keyword → row 映射——S8 拥有分析报告+全部响应文件的完整上下文，其映射比 S10 事后猜测更准确。若无此文件，则按下方工作流自行发现。

**工作流**（LLM 驱动，不写脚本）：

**3.3.1 列出所有表格，定位索引表**

```bash
curl -s http://localhost:8800/api/docx/$FID/tables
```

LLM 分析返回的表格列表，找到索引表（特征：含有"序号"/"附件名称"/"文件"/"页码"等列头）。记录索引表的 `table[N]` 路径。

**3.3.2 获取正文段落，匹配索引项**

```bash
curl -s http://localhost:8800/api/docx/$FID/preview
```

LLM 分析返回的段落列表，为索引表中的每个附件找到正文中对应的首次出现位置：
- 从索引表"附件名称"列读取条目（如"报价函"、"法定代表人授权委托书"）
- 在 preview 段落中搜索包含该附件名称的段落
- 提取该段落中一段**在正文中唯一**的关键文本作为 keyword（建议 15-30 字，避免太短产生歧义）

**⚠️ pandoc 文本变化容错**：pandoc 转换后 docx 中的文本可能与 markdown 原文不完全一致（全角/半角标点转换、多余空格、特殊字符转义等）。选取 keyword 时应遵循：
1. **优先选中文汉字序列**（如"法定代表人授权委托书"），不受标点变化影响
2. **避免选取含特殊标点的片段**（如 `"` `—` `·`），这些在 pandoc 中可能被转义
3. **如精确匹配失败（HTTP 400）**，尝试缩短 keyword（取前 10 字）或选用附件名称本身作为 keyword 重试
4. **keyword 必须出现在 body 段落中**，不能出现在表格单元格内。如果附件名称只在表格中出现，跳过该项

**3.3.3 逐个插入交叉引用**

对索引表中需要页码的每一行：

```bash
curl -s -X POST http://localhost:8800/api/docx/$FID/crossref \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "{正文中唯一的关键文本}",
    "cellPath": "table[{N}].row[{R}].cell[{C}]",
    "paragraphPath": "paragraph[{P}]"
  }'
```

参数说明：
- `keyword`：正文中要打书签的精确文本（必须在 body 段落中，不能在表格内）
- `cellPath`：目标单元格路径，从 3.3.1 的 tables 输出中获取
- `paragraphPath`：**当 keyword 在多个段落中出现时必须提供**，从 3.3.2 的 preview 输出中获取段落路径以消歧；如果 keyword 全文唯一则可省略

DocScan 内部自动完成：
1. 在正文 keyword 处打书签
2. 在目标单元格插入 PAGEREF 字段（自动识别"第……页"模式拼接）
3. 调用 ONLYOFFICE 重算真实页码并写回

**错误恢复**：
| HTTP 状态 | 含义 | 处理 |
|-----------|------|------|
| 200 | 成功 | 记录 `✅` |
| 400 "keyword not found" | 文本不在正文中 | 尝试缩短 keyword 重试一次；仍失败则记录 `⚠️ 跳过：keyword未找到` |
| 400 "matches N paragraphs" | keyword 歧义 | 添加 `paragraphPath` 重试；无法确定时记录 `⚠️ 跳过：歧义` |
| 500 | 字段重算失败 | 记录 `⚠️ 跳过：ONLYOFFICE重算失败`，通常为 Docker 容器问题 |

**注意**：
- crossref 每次调用都会触发 ONLYOFFICE 字段重算（涉及 Docker 容器通信），单次耗时约 3-8 秒
- 索引表有多行时需逐个调用，总耗时与行数成正比

#### 3.4 下载增强后的 docx

```bash
curl -s http://localhost:8800/api/docx/$FID -o "{outputFile路径}"
```

覆盖原始的 generate_docx.js 输出文件，完成增强。

**多册模式**：每个 docx 分别下载覆盖。

### 4. 报告生成结果

输出以下信息：
- 生成的 .docx 文件路径和大小
- 处理的 Markdown 文件数量
- 嵌入的图片数量
- 排除的文件列表
- DocScan 后期增强状态（已执行/跳过）+ 占位符数量 + 交叉引用数量

## 排除规则

以下文件不转换为 Word（S8 内部产出物，不进入最终交付文档）：
- `核对报告.md` — 内部质检文件
- `装订指南.md` — 内部参考文件
- `00-目录.md` — 目录索引（最终 Word 中的页码由 DocScan crossref 生成）
- `crossref_mapping.json` — S8→S10 数据交换文件，非文档内容
- 用户指定的其他排除文件

## 图片处理

generate_docx.js 支持 Markdown 图片语法 `![alt](file.png)`：
- 自动读取图片文件并嵌入 Word
- 图片宽度不超过页面内容区（约15cm），高度按比例缩放
- 支持 PNG 和 JPEG 格式
- 图片不存在时插入红色 `[图片缺失: filename]` 占位文字

**⚠️ 重要：不需要使用 Read 工具读取图片文件**
- `generate_docx.js` 脚本会自动处理所有图片的读取和嵌入
- Claude 只需确保 Markdown 中的图片路径正确（相对于 `响应文件/` 目录）
- 无需验证图片内容或尺寸，脚本会自动处理

## generate_docx.js 渲染行为

编写 Markdown 时必须了解 generate_docx.js 的以下渲染规则，否则 Word 输出会出现排版问题：

### 自动分页规则

generate_docx.js 在以下情况插入分页符：

- **`---` 水平分隔线** → 转换为分页符（用于封面与正文之间、章节之间的分页）
- **文件间分隔**：合并多个 .md 文件时，每个文件之间自动插入分页符

**注意**：`##` 标题（H2）**不会**自动触发分页。如果需要某个章节从新页开始，在该章节前插入 `---`。

封面、签章区可以使用 `#` 或 `##` 标题标记，不会导致异常分页。

### 空白行处理
- **禁止使用 `&nbsp;`**：generate_docx.js 已内置清理逻辑，会自动移除所有 `&nbsp;` 实体
- 使用普通空行（连续两个换行符）即可实现段落间距
- 封面留白、签章区间距通过正常的 Markdown 空行处理

### ImageRun 类型
- 嵌入图片时必须指定 `type` 参数（`'png'` 或 `'jpg'`），否则图片扩展名会变成 `.undefined`，导致 Word 无法显示
- generate_docx.js 已内置自动检测逻辑，基于文件扩展名确定类型

### 行距
- 正文段落和列表项默认使用 **1.5 倍行距**（`spacing.line: 360`）
- 标题行距由标题样式控制（`spacing.before: 240, after: 120`）

### 文件排序
- CONFIG 支持 `fileOrder` 数组，指定文件的合并顺序
- 多册模式下，商务文件（06-）应排在技术文件（01-05）之前

## 注意事项

- 运行前确认 `响应文件/` 目录存在且有 .md 文件
- 确认 `docx` npm 包已安装（`node_modules/docx`）
- CONFIG 通过命令行 JSON 参数传入，不要复制或编辑脚本文件
- 如果生成失败，检查控制台错误信息并修复（常见：图片路径错误、特殊字符导致表格解析失败）
- **Word 文件被占用时写入会失败**（EBUSY 错误）：生成前确保目标 .docx 文件未在 Word 中打开

## 完成状态

生成完成后，输出以下结构化状态摘要：

```
--- BID-MD2DOC COMPLETE ---
输出模式: {单册/多册}
输出文件: {文件路径}（多册时逐个列出）
文件大小: {KB}
MD文件数: {N}
图片数: {N}
排除文件: {核对报告.md, 装订指南.md, ...}
DocScan后期增强: {SUCCESS / SKIPPED_OFFLINE / PARTIAL}
交叉引用: {成功数}/{总数}
占位符残留: {N}个
状态: SUCCESS
--- END ---
```
