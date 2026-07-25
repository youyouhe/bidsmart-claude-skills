---
name: bid-poc-screenshots
description: >
  将 POC 原型页面截取为 PNG 截图，并替换技术标书中的【此处插入XX功能截图】占位符。
  纯机械步骤，无 LLM 推理。运行时自动识别已有的占位符和 POC 子目录的对应关系。
  当用户要求"插入POC截图"、"替换功能截图占位符"、"poc截图"时触发。
  前置条件：响应文件/ 目录下已存在技术标书 .md 文件，且 POC 已生成（workDir/poc/ 下有子目录）。
tools: [read, write, bash]
---

# POC 截图占位符替换

## 工作模式

**纯机械操作** —— 不需要 LLM 编写任何内容，只做文本查找替换 + 调用截图脚本。

## 前置检查

1. 确认 POC 目录存在：
   ```bash
   ls -d <workDir>/poc/*/index.html 2>/dev/null | wc -l
   ```
   如果返回 0，则没有 POC 可截图，输出状态 `SKIPPED` 并结束。

2. 确认技术标书文件存在：
   ```bash
   ls 响应文件/*.md 2>/dev/null
   ```
   如果没有 .md 文件，输出状态 `SKIPPED` 并结束。

## 工作流程

### 1. 统计占位符

扫描 `响应文件/` 下所有 .md 文件，找出所有 `【此处插入XX功能截图】` 占位符：

```bash
grep -n '【此处插入.*功能截图】' 响应文件/*.md
```

将结果列出，供后续步骤参考匹配关系。

如果没有任何占位符，说明技术标书还未编写，输出状态 `SKIPPED`。

### 2. 运行截图脚本

```bash
node /mnt/oldroot/home/bird/xyy/smartbid-platform/tools/pptx-converter/screenshot-poc.js <workDir>/poc/ 响应文件/
```

脚本输出 JSON 格式的截图清单，如：
```json
{
  "screenshots": [
    { "subDir": "S04-性能预报系统", "screenshot": "poc-S04-性能预报系统.png", "sizeBytes": 473449 },
    { "subDir": "S05-系统管理平台", "screenshot": "poc-S05-系统管理平台.png", "sizeBytes": 319454 }
  ]
}
```

### 3. 建立映射并替换

将步骤 1 找到的每个占位符与步骤 2 的截图匹配。匹配规则：**占位符中的功能名称与 POC 子目录名包含相同的关键词（如系统编号 S04、系统名 性能预报）**。

对每个匹配上的占位符：
1. 确定其所在的文件路径和行号
2. 用 `read` 工具读取该行附近的内容确认上下文
3. 用 `edit` 工具将占位符文本替换为 Markdown 图片引用：

   ```
   【此处插入S04性能预报系统功能截图】（截图需加盖公章）
   →
   ![S04 性能预报系统 POC 原型](poc-S04-性能预报系统.png)
   ```

对于无法匹配的占位符，保留原文不动（可能是手工截图需求或其他非 POC 场景）。

### 4. 输出结果

```markdown
--- BID-POC-SCREENSHOTS COMPLETE ---
状态: SUCCESS
截图总数: N
替换成功: M
未匹配占位符: K
截图清单:
  - poc-S04-性能预报系统.png (462 KB)
  - poc-S05-系统管理平台.png (319 KB)
--- END ---
```

如果无 POC 或无占位符，状态为 `SKIPPED`。
