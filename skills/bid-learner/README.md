# Bid-Learner - 投标业务经验学习工具

## 概述

Bid-Learner 是一个**自我改进的 Skill**，从投标业务实践中自动学习经验教训，并将其注入到相应的 bid-* skills 的 gotchas.md 文件中。

**严格作用域限制**：仅适用于投标业务（招标、磋商、标书、响应文件等），拒绝学习非投标领域的经验，防止作用域漂移和技能异化。

## 核心功能

1. **上下文验证**：三层验证确保学习发生在投标业务上下文中
2. **问题识别**：从失败案例中提取可复用的经验教训
3. **Skill 定位**：自动识别应将经验注入到哪个 bid-* skill
4. **Gotcha 生成**：结构化生成 gotcha 条目（问题-解决-示例）
5. **自动注入**：将 gotcha 追加到目标 skill 的 gotchas.md
6. **作用域自检**：定期扫描检测是否有非投标经验混入

## 文件结构

```
bid-learner/
├── SKILL.md                    # Skill 定义和工作流程
├── README.md                   # 本文件
├── scripts/                    # 核心脚本
│   ├── inject_gotcha.py       # Gotcha 注入（带作用域验证）
│   ├── validate_context.py    # 上下文验证
│   ├── identify_skill.py      # Skill 识别
│   └── self_check.py          # 作用域自检
├── templates/                  # 模板
│   └── gotcha_template.md     # Gotcha 编写模板
└── initial-gotchas/           # 初始 Gotchas 文件
    ├── bid-analysis-gotchas.md
    ├── bid-verification-gotchas.md
    └── bid-assembly-gotchas.md
```

## 使用方法

### 触发学习

当用户在投标业务对话中说：
- "记住这个错误"
- "记住这次教训"
- "总结经验"
- "学习这个案例"

### 工作流程

1. **验证上下文**（自动）
   ```bash
   python scripts/validate_context.py "对话历史文本"
   ```

2. **识别问题**（LLM）
   - 从对话中提取：问题描述、失败原因、解决方案、示例代码

3. **定位 Skill**（自动）
   ```bash
   python scripts/identify_skill.py "问题描述" "上下文"
   ```

4. **生成 Gotcha**（LLM）
   - 使用 gotcha_template.md 生成结构化条目

5. **注入**（自动）
   ```bash
   python scripts/inject_gotcha.py \
     bid-analysis \
     "特定资格条件为无被当作可省略" \
     "磋商邀请中特定资格条件明确写无..." \
     "特定资格条件为无仍需在分析报告中显式标注..." \
     "示例代码..."
   ```

6. **确认**（展示给用户）
   ```
   ✅ 已将经验注入到 bid-analysis/gotchas.md
   ```

### 定期自检

每周运行一次作用域自检：
```bash
python scripts/self_check.py ~/.claude/skills
```

## 作用域控制机制

### 三层验证

1. **文件检查**：是否涉及投标文件（招标文件、分析报告.md、响应文件/）
2. **Skill 检查**：是否调用了 bid-* skills
3. **关键词检查**：是否包含投标业务关键词（投标、招标、标书、评分、资格、报价等）

**通过条件**：至少满足 2 项 → 允许学习

### 拒绝条件

- 非 bid-* skill 的问题 → 拒绝
- 内容包含大量非投标技术关键词（React、API、Database等）且缺乏投标上下文 → 拒绝
- 上下文验证得分 < 2 → 拒绝

### 自检机制

定期扫描所有 bid-* skills 的 gotchas.md，检测可疑条目：
- 有非投标关键词（React、Vue、API、Database等）
- 且缺乏投标上下文关键词（招标、投标、标书等）
- → 标注为⚠️可疑，建议人工审查

## 初始 Gotchas

已为核心 skills 准备初始 gotchas（来自 bidsmart-skills-review.md）：

### bid-analysis（5条）
- 特定资格条件为"无"被当作可省略
- 评分表子项分值未验算导致不一致
- Word 表格中的合并单元格导致提取错位
- 预算金额单位混淆（万元 vs 元）
- 附件清单遗漏带星号的必须项

### bid-verification（5条）
- 只核对分析报告未回查原始文件
- Word 表格优先级低于 PDF 导致精度损失
- 分值验算只检查总分未检查子项
- 采购编号位数错误未被检测
- 核实完成后未自动修正分析报告

### bid-assembly（5条）
- 自查自纠盲区：质检时参考编写记忆
- 占位符检测遗漏非标准格式
- 完整性检查未验证文件编号连续性
- 一致性检查只比对名称未比对具体值
- 核对报告缺少可执行的修复指引

## 部署步骤

### 1. 将初始 Gotchas 注入到现有 Skills

```bash
# 复制到实际 skills 目录
cp initial-gotchas/bid-analysis-gotchas.md ~/.claude/skills/bid-analysis/gotchas.md
cp initial-gotchas/bid-verification-gotchas.md ~/.claude/skills/bid-verification/gotchas.md
cp initial-gotchas/bid-assembly-gotchas.md ~/.claude/skills/bid-assembly/gotchas.md
```

### 2. 安装 bid-learner

```bash
# 复制到 skills 目录
cp -r bid-learner ~/.claude/skills/
chmod +x ~/.claude/skills/bid-learner/scripts/*.py
```

### 3. 验证安装

```bash
# 测试上下文验证
python ~/.claude/skills/bid-learner/scripts/validate_context.py \
  "我在处理招标文件，调用了 bid-analysis，生成了分析报告.md"

# 测试 Skill 识别
python ~/.claude/skills/bid-learner/scripts/identify_skill.py \
  "评分表子项分值验算错误"

# 测试自检
python ~/.claude/skills/bid-learner/scripts/self_check.py ~/.claude/skills
```

## 维护指南

### 何时触发学习

✅ **应该学习**：
- 投标业务中的失败案例（遗漏附件、分值验算错误、格式不符等）
- bid-* skills 执行中的常见陷阱
- 招标文件解析的反直觉问题
- 质检中反复出现的问题

❌ **不应学习**：
- 通用编程错误（npm install 失败、API 调用错误）
- 非投标业务的经验（网站开发、数据分析）
- 一次性的偶然问题（网络超时、文件损坏）

### 定期审查

每月审查一次 gotchas：
1. 运行 `self_check.py` 检测作用域漂移
2. 检查是否有重复的 gotchas
3. 合并相似的经验
4. 删除过时的 gotchas

### 质量标准

好的 Gotcha：
- ✅ 标题简洁（5-10字）
- ✅ 问题描述具体（真实场景）
- ✅ 解决方案可执行（明确步骤或代码）
- ✅ 有示例（代码或配置）
- ✅ 与投标业务直接相关

差的 Gotcha：
- ❌ 标题模糊（"注意某个问题"）
- ❌ 问题泛泛而谈（"可能出错"）
- ❌ 解决方案抽象（"要仔细"）
- ❌ 缺少示例
- ❌ 与投标业务无关

## 预期效果

### 短期（1-2周）
- 核心 bid-* skills 质量从 90% → 95%
- 常见错误（分值验算、特定资格条件、占位符）显著减少

### 中期（1-2月）
- 积累 30-50 条实践经验
- 自动修复率从 60% → 80%
- 人工干预需求降低

### 长期（3月+）
- 形成完整的投标业务知识库
- 新类型的招标文件自动适应能力增强
- 达到 95%+ 自主完成率

## 限制和风险

### 限制
- 仅适用于投标业务，不能学习其他领域
- 依赖用户主动触发"记住这个错误"
- 无法自动发现潜在问题，只能从失败中学习

### 风险
- **作用域漂移**：如果验证机制失效，可能混入非投标经验 → 通过 self_check.py 定期检测
- **Gotcha 膨胀**：随时间积累过多经验 → 定期审查和合并
- **过拟合**：针对特定项目的经验可能不通用 → 注入时抽象化问题

## 支持

如有问题或改进建议，请在投标业务对话中提出，bid-learner 会持续学习和改进。
