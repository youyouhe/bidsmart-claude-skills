# Bid-Learner - 投标业务经验学习与缺陷诊断工具

## 概述

Bid-Learner 是一个**自我改进的 Skill**，从投标业务实践中提取问题，并判断问题性质——是**一次性失误**还是**skill 设计缺陷**：

- **一次性失误**（环境问题、原文数据错误、偶然疏漏且首次出现）→ 记录为轻量 gotcha，追加到 `{skill}-gotchas.md`
- **设计缺陷**（SKILL.md 规则缺失/模糊/矛盾、缺少校验机制、或同类问题已复发）→ 生成结构化诊断报告，追加到 `{skill}-defect-reports.md`，精确定位到 SKILL.md 哪一节该改，给出建议修改文本

**⚠️ 关键约束：本 skill 从不自动修改任何 SKILL.md。** 无论哪个分支，产出都只是建议/记录，是否采纳、何时修改，始终由人工决定。

**严格作用域限制**：仅适用于投标业务（招标、磋商、标书、响应文件等），拒绝学习非投标领域的经验，防止作用域漂移和技能异化。

## 核心功能

1. **上下文验证**：三层验证确保学习发生在投标业务上下文中
2. **问题识别**：从失败案例中提取症状、根因、触发条件
3. **Skill 定位**：自动识别问题归属的 bid-* skill
4. **历史检查**：扫描该 skill 是否已有相似的历史 gotcha/缺陷记录
5. **分类判断**：一次性失误走轻量记录，设计缺陷走结构化诊断报告
6. **Gotcha 生成**：结构化生成 gotcha 条目（问题-解决-示例）
7. **缺陷报告生成**：结构化生成缺陷诊断报告（定位-根因-建议修改-影响评估）
8. **自动注入**：将 gotcha/缺陷报告追加到目标 skill 对应的输出文件
9. **作用域自检**：定期扫描检测是否有非投标经验混入

## 文件结构

```
bid-learner/
├── SKILL.md                       # Skill 定义和工作流程
├── README.md                      # 本文件
├── scripts/                       # 核心脚本
│   ├── validate_context.py       # 上下文验证
│   ├── identify_skill.py         # Skill 识别
│   ├── check_gotcha_history.py   # 历史同类问题检查（驱动分类判断）
│   ├── inject_gotcha.py          # 轻量 Gotcha 注入（一次性失误分支）
│   ├── generate_defect_report.py # 缺陷诊断报告生成（设计缺陷分支）
│   └── self_check.py             # 作用域自检
├── templates/                     # 模板
│   ├── gotcha_template.md        # Gotcha 编写模板
│   └── defect_report_template.md # 缺陷诊断报告模板（含何时该用哪个模板的判断标准）
└── initial-gotchas/               # 初始 Gotchas 文件
    ├── bid-analysis-gotchas.md
    ├── bid-verification-gotchas.md
    └── bid-assembly-gotchas.md
```

## 使用方法

### 触发学习

当用户在投标业务对话中说：
- "记住这个错误" / "记住这次教训" / "总结经验" / "学习这个案例"
- "分析一下这个问题的根因" / "这是不是 skill 的设计缺陷"

### 工作流程

1. **验证上下文**（自动）
   ```bash
   python scripts/validate_context.py --text "对话历史文本"
   ```

2. **识别问题归属 Skill**（自动）
   ```bash
   python scripts/identify_skill.py --problem "问题描述" --context "上下文"
   ```

3. **历史检查**（自动，新增）
   ```bash
   python scripts/check_gotcha_history.py --skill bid-analysis --title "问题标题" --gotcha-dir {workDir}
   ```
   返回 `similar_count`——同类问题历史出现次数，是分类判断的重要依据。

4. **提取问题要素**（LLM）
   - 从对话中提取：症状、**根因**（因果链，不是症状复述）、解决方案、触发条件、严重性

5. **分类判断**（LLM，核心分支点，新增）

   判定为"设计缺陷"需满足以下任一条件：
   - SKILL.md 对应章节确实模糊/缺失/矛盾（**必须实际读取 SKILL.md 核实**，不能凭对话推测）
   - 同类问题历史 ≥1 次（`check_gotcha_history.py` 证据）
   - 根源是缺少校验/门控机制

   否则判定为"一次性失误"。

6A. **一次性失误 → 注入 Gotcha**（自动）
   ```bash
   python scripts/inject_gotcha.py \
     --skill bid-analysis \
     --title "标题" --problem "问题" --solution "解决方案" \
     --output-dir {workDir}
   ```

6B. **设计缺陷 → 生成诊断报告**（自动，新增）
   ```bash
   python scripts/generate_defect_report.py \
     --skill bid-analysis \
     --title "缺陷标题" --defect-type "缺失规则" \
     --location "SKILL.md《XX章节》" --current-text "原文引用" \
     --root-cause "根因分析" --trigger-scenario "触发场景" \
     --historical-count 2 --suggested-fix "建议修改文本" \
     --impact-assessment "影响评估" \
     --output-dir {workDir}
   ```

7. **确认**（展示给用户）
   ```
   ✅ 已记录一次性失误到 bid-analysis-gotchas.md
   ```
   或
   ```
   🔍 检测到 Skill 设计缺陷 [DEFECT-N]，已生成诊断报告
   ⚠️ 报告仅供参考，SKILL.md 未被自动修改
   ```

### 定期自检

每周运行一次作用域自检：
```bash
python scripts/self_check.py ~/.claude/skills
```

## 作用域控制机制

### 三层验证（沿用不变）

1. **文件检查**：是否涉及投标文件（招标文件、分析报告.md、响应文件/）
2. **Skill 检查**：是否调用了 bid-* skills
3. **关键词检查**：是否包含投标业务关键词（投标、招标、标书、评分、资格、报价等）

**通过条件**：至少满足 2 项 → 允许学习

### 拒绝条件

- 非 bid-* skill 的问题 → 拒绝
- 内容包含大量非投标技术关键词（React、API、Database等）且缺乏投标上下文 → 拒绝
- 上下文验证得分 < 2 → 拒绝

### 缺陷报告的额外安全约束

- `generate_defect_report.py` 必须指定 `--output-dir`（写入 workDir），从不直接写入 skills 目录
- 标题重复时拒绝写入，避免同一缺陷重复建档
- 严重程度自动按历史频次计算，不由 LLM 主观判断

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
  --text "我在处理招标文件，调用了 bid-analysis，生成了分析报告.md"

# 测试 Skill 识别
python ~/.claude/skills/bid-learner/scripts/identify_skill.py \
  --problem "评分表子项分值验算错误"

# 测试历史检查
python ~/.claude/skills/bid-learner/scripts/check_gotcha_history.py \
  --skill bid-analysis --title "特定资格条件为无被当作可省略" \
  --skills-root ~/.claude/skills

# 测试自检
python ~/.claude/skills/bid-learner/scripts/self_check.py --skills-root ~/.claude/skills
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

### 何时该升级为设计缺陷诊断（而非普通 gotcha）

详见 `templates/defect_report_template.md` 的判断标准。核心信号：
1. 翻查 SKILL.md 对应章节，规则确实缺失/模糊/矛盾
2. 同类问题历史 ≥1 次（`check_gotcha_history.py` 可查）
3. 缺少本该有的校验/门控机制

### 定期审查

每月审查一次 gotchas 和缺陷报告：
1. 运行 `self_check.py` 检测作用域漂移
2. 检查是否有重复的 gotchas
3. 合并相似的经验
4. 审阅缺陷报告，决定是否采纳并手动修改对应 SKILL.md
5. 采纳后的缺陷报告可以标注"已修复"或归档

### 质量标准

好的 Gotcha：
- ✅ 标题简洁（5-10字）
- ✅ 问题描述具体（真实场景）
- ✅ 解决方案可执行（明确步骤或代码）
- ✅ 有示例（代码或配置）
- ✅ 与投标业务直接相关

好的缺陷报告：
- ✅ 标题描述缺陷本质，不是症状
- ✅ 定位精确到 SKILL.md 具体章节
- ✅ 根因解释因果链，不是复述症状
- ✅ 建议修改直接可用，不是空话
- ✅ 诚实评估影响面

## 预期效果

### 短期（1-2周）
- 核心 bid-* skills 质量从 90% → 95%
- 常见错误（分值验算、特定资格条件、占位符）显著减少

### 中期（1-2月）
- 积累 30-50 条实践经验，若干条升级为缺陷报告并被采纳修复
- 自动修复率从 60% → 80%
- 人工干预需求降低

### 长期（3月+）
- 形成完整的投标业务知识库
- SKILL.md 本身的规则覆盖率持续提升（通过采纳缺陷报告的建议修改）
- 新类型的招标文件自动适应能力增强
- 达到 95%+ 自主完成率

## 限制和风险

### 限制
- 仅适用于投标业务，不能学习其他领域
- 依赖用户主动触发"记住这个错误"/"分析根因"
- 无法自动发现潜在问题，只能从失败中学习
- **不会自动修改 SKILL.md**——缺陷报告需要人工审阅并手动应用，这是有意的设计约束（避免未经审阅的改动破坏 skill）

### 风险
- **作用域漂移**：如果验证机制失效，可能混入非投标经验 → 通过 self_check.py 定期检测
- **Gotcha/缺陷报告膨胀**：随时间积累过多记录 → 定期审查和合并
- **过拟合**：针对特定项目的经验可能不通用 → 注入时抽象化问题
- **误判分类**：把设计缺陷误判为一次性失误会导致问题持续复发 → 分类判断时"不确定则倾向缺陷"的约束可缓解，但仍需人工复核

## 支持

如有问题或改进建议，请在投标业务对话中提出，bid-learner 会持续学习和改进。
