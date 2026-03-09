---
name: bid-md2doc
description: >
  将 响应文件/ 目录下的 Markdown 文件转换为格式化的 Word (.docx) 文档。
  自动从分析报告和商务文件中读取项目名称、公司名称等信息，
  编辑 generate_docx.js 的 CONFIG 区域，然后运行脚本生成 Word 文件。
  当用户要求生成Word文档、转换MD为docx、导出响应文件时触发。
  前置条件：响应文件/ 目录下已有编写完成的 .md 文件。
---

# MD 转 Word 文档

## 核心功能

将 `响应文件/` 目录下的 Markdown 文件转换为格式化的 Word (.docx) 文档，
支持标题层级、表格、图片嵌入、页眉页脚、分页等。
支持单册输出（合并为一个文件）和多册输出（按册别生成多个文件）。

## 工作流程

### 1. 读取项目信息

#### 1.1 从分析报告读取项目名称和册别结构

```python
# 读取 分析报告.md，提取项目名称
# 通常在 "## 项目概况" 章节的 "项目名称" 行
```

提取字段：
- **项目名称**：用于页眉文字和输出文件名
- **采购编号**：可选，用于页眉补充信息
- **册别结构**：从"投标文件册别结构"章节提取册别数量和每册包含的文件列表

#### 1.2 从商务文件读取公司名称

扫描 `响应文件/` 目录下的文件（如报价函、封面等），提取公司全称：

```python
# 在已编写的商务文件中搜索公司名称
# 通常在报价函或封面文件的签章区域
```

提取字段：
- **公司全称**：用于页脚

#### 1.3 判定输出模式

根据册别结构判定输出模式：
- **单册模式**：分析报告未提及册别结构或标注"单册" → 生成一个 Word 文件
- **多册模式**：分析报告指定了多册结构 → 每册生成一个独立 Word 文件

### 2. 编辑 generate_docx.js 配置

编辑工作目录下 `generate_docx.js` 顶部的 CONFIG 区域（位于 `// === CONFIG START ===` 和 `// === CONFIG END ===` 之间）。

#### 2.1 单册模式

```javascript
const CONFIG = {
  inputDir: '{工作目录}/响应文件',
  outputFile: '响应文件-{公司简称}-{项目简称}.docx',
  headerText: '{项目全称} 响应文件',
  footerCompany: '{公司全称}',
  excludeFiles: ['核对报告.md', '装订指南.md'],
};
```

#### 2.2 多册模式

多册模式需要**多次运行** generate_docx.js，每次使用不同的 CONFIG：
- 每册通过 `excludeFiles` 排除不属于该册的文件，或通过 `includeFiles` 仅包含该册的文件
- 每册的 `outputFile` 和 `headerText` 使用该册的名称

推荐方式：创建 `generate_both.js`（或 `generate_all.js`）包装脚本，自动修改 CONFIG 并多次调用 generate_docx.js：

```javascript
// 第一册：资格证明文件
const config1 = {
  inputDir: '{工作目录}/响应文件',
  outputFile: '投标文件（资格证明文件）-{公司简称}.docx',
  headerText: '{采购编号} 投标文件（资格证明文件）',
  footerCompany: '{公司全称}',
  excludeFiles: ['核对报告.md', '装订指南.md', /* 第二册的文件 */],
  includeFiles: ['00-资格证明文件.md'],  // 仅包含第一册文件
};

// 第二册：商务技术文件
const config2 = {
  inputDir: '{工作目录}/响应文件',
  outputFile: '投标文件（商务技术文件）-{公司简称}.docx',
  headerText: '{采购编号} 投标文件（商务技术文件）',
  footerCompany: '{公司全称}',
  excludeFiles: ['核对报告.md', '装订指南.md', '00-资格证明文件.md'],
};
```

字段填写规则：
- `inputDir`：保持为 `响应文件/` 的绝对路径
- `outputFile`：单册时为 `响应文件-{公司简称}-{项目简称}.docx`；多册时为 `投标文件（{册别名称}）-{公司简称}.docx`
- `headerText`：单册时为 `{项目全称} 响应文件`；多册时为 `{采购编号} 投标文件（{册别名称}）`
- `footerCompany`：公司全称
- `excludeFiles`：固定排除 `核对报告.md` 和 `装订指南.md`，多册时还需排除其他册的文件
- `includeFiles`：可选，如指定则仅处理列出的文件（优先于 excludeFiles）

### 3. 运行生成脚本

```bash
# 单册模式
cd {工作目录} && node generate_docx.js

# 多册模式
cd {工作目录} && node generate_both.js
```

### 4. 报告生成结果

输出以下信息：
- 生成的 .docx 文件路径和大小
- 处理的 Markdown 文件数量
- 嵌入的图片数量
- 排除的文件列表

## 排除规则

以下文件不转换为 Word：
- `核对报告.md` — 内部质检文件，不进入最终文档
- `装订指南.md` — 内部参考文件，不进入最终文档
- 用户指定的其他排除文件

## 图片处理

generate_docx.js 支持 Markdown 图片语法 `![alt](file.png)`：
- 自动读取图片文件并嵌入 Word
- 图片宽度不超过页面内容区（约15cm），高度按比例缩放
- 支持 PNG 和 JPEG 格式
- 图片不存在时插入红色 `[图片缺失: filename]` 占位文字

## 注意事项

- 运行前确认 `响应文件/` 目录存在且有 .md 文件
- 确认 `docx` npm 包已安装（`node_modules/docx`）
- CONFIG 编辑仅修改 `CONFIG START` 和 `CONFIG END` 之间的内容，不改动其他代码
- 如果生成失败，检查控制台错误信息并修复（常见：图片路径错误、特殊字符导致表格解析失败）

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
状态: SUCCESS
--- END ---
```
