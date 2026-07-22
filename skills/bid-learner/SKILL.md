---
name: bid-learner
description: >
  投标业务专用经验学习与缺陷诊断器。从对话中提取投标相关的错误、问题和经验教训，
  判断问题性质是"一次性失误"还是"skill 设计缺陷"：一次性失误记录为轻量 gotcha，
  设计缺陷则生成结构化诊断报告（精确定位 SKILL.md 章节、根因分析、建议修改文本），
  供人工审阅决定是否修改 skill 本身。本 skill 从不自动修改 SKILL.md。
  严格限定范围：仅处理投标业务（招标分析、响应文件编写、质检等），
  不学习通用编程、其他领域知识。
  触发条件：用户说"记住这个错误"/"记住这次教训"/"总结经验"/"学习这个案例"；
  用户明确要求"更新 bid-XXX 的 gotchas"；用户说"投标经验记录"/"标书问题记录"；
  用户说"分析一下这个问题的根因"/"这是不是 skill 的设计缺陷"。
  前置条件：当前对话必须在投标项目上下文中（有招标文件、分析报告、响应文件等），
  且最近调用过至少一个 bid-* skill。
  不触发：非投标相关对话；用户只是抱怨但没明确要求记录；问题与 bid 业务无关（如通用代码错误）。
---

# 投标业务经验学习与缺陷诊断器

## 核心原则

### 1. 目标是找到根因，不是记流水账

记录错误本身不是目的。**目标是判断这个错误的根源在哪里**：是一次性的偶然（环境问题、原文本身矛盾、执行时的偶然疏漏），还是 skill 的设计本身有缺陷（规则缺失、规则模糊、缺少校验机制），导致同类问题会反复发生。

只有分类判断做对了，产出才有意义：
- **一次性失误** → 轻量记录到 `{skill}-gotchas.md`，供下次参考（可能有用，也可能没用）
- **设计缺陷** → 生成结构化诊断报告到 `{skill}-defect-reports.md`，精确定位到 SKILL.md 哪一节该改、给出建议修改文本，供人工审阅

**⚠️ 本 skill 从不自动修改任何 SKILL.md。** 诊断报告只是建议，是否采纳、何时修改，始终是人工决定。

### 2. 严格的范围限定

**仅学习以下类型的经验：**

✅ 招标文件分析错误（评分表提取、资格条件理解偏差、金额/时间解析错误）
✅ 响应文件编写问题（技术方案遗漏、商务附件错误、报价不一致、占位符残留）
✅ 质检和验证问题（验证逻辑遗漏、合规检查不全、文件编号错误）
✅ 流程编排问题（Pipeline 阶段失败、断点续跑异常、自动修复失效）

❌ **不学习**：通用编程错误、非投标领域业务、系统配置/网络问题、非 bid-* skills 的问题

### 3. 沙箱安全约束

**⚠️ 重要：skills 目录在沙箱中是只读的。**

所有产出（gotcha 和缺陷报告）必须写入工作目录（workDir），不能直接写入 skills 目录。
脚本通过 `--output-dir` 参数指定写入位置。

## 脚本调用规范

**⚠️ 重要：不要复制脚本到工作目录！直接通过绝对路径调用。**

脚本基础路径（固定）：
```
SCRIPTS=/mnt/oldroot/home/bird/xyy/smartbid-platform/packages/bidsmart-skills/skills/bid-learner/scripts
```

如该路径不存在（非该特定 host/checkout），改用本仓库自带的路径：
```
SCRIPTS={本仓库路径}/skills/bid-learner/scripts
```

### 可用脚本

| 脚本 | 功能 | 关键参数 |
|------|------|---------|
| `validate_context.py` | 验证对话是否在投标上下文 | `--text "对话文本"` |
| `identify_skill.py` | 识别问题归属的 skill | `--problem "描述" [--context "上下文"]` |
| `check_gotcha_history.py` | 检查该 skill 是否有同类历史问题 | `--skill X --title Y [--gotcha-dir DIR] [--skills-root DIR]` |
| `inject_gotcha.py` | 注入轻量 gotcha（一次性失误分支） | `--skill X --title Y --problem Z --solution W --output-dir DIR` |
| `generate_defect_report.py` | 生成缺陷诊断报告（设计缺陷分支） | 见下方 Phase 4B |
| `self_check.py` | 扫描 gotchas 检测作用域漂移 | `[--skills-root DIR]` |

## 工作流程

```
Phase 1: 上下文验证
Phase 2: 识别目标 Skill
Phase 2.5: 历史同类问题检查   ← 新增
Phase 3: 从对话中提取问题要素（含根因）
Phase 3.5: 分类判断 —— 一次性失误 vs 设计缺陷   ← 新增，核心分支点
Phase 4A: 一次性失误 → 注入轻量 gotcha
Phase 4B: 设计缺陷 → 生成结构化诊断报告   ← 新增
Phase 5: 确认与输出
```

### Phase 1: 上下文验证

```bash
python3 $SCRIPTS/validate_context.py --text "最近20轮对话的关键内容摘要"
```

输出 JSON：`{"is_valid": true/false, "score": 0-3, "reasons": [...]}`

如果 `is_valid` 为 false → 拒绝学习，告知用户原因。

### Phase 2: 识别目标 Skill

```bash
python3 $SCRIPTS/identify_skill.py --problem "问题描述" --context "对话上下文"
```

输出 JSON：`{"skill": "bid-analysis", "confidence": 0.67, "matched_patterns": [...]}`

如果 `skill` 为 null → 询问用户手动指定。

### Phase 2.5: 历史同类问题检查（新增）

在做分类判断之前，先看这个 skill 是否已经出现过类似问题——这是判断"一次性 vs 设计缺陷"最有力的证据来源之一。

```bash
python3 $SCRIPTS/check_gotcha_history.py \
  --skill {target_skill} \
  --title "本次问题的初步标题" \
  --gotcha-dir "{workDir}" \
  --skills-root {skills根目录}
```

输出 JSON：`{"similar_count": N, "matches": [...], "recommendation": "..."}`

`similar_count >= 1` 是 Phase 3.5 判定为"设计缺陷"的直接证据之一（见下）。

### Phase 3: 从对话中提取问题要素

由 LLM 完成（不需要脚本），提取：
- **症状**：用户观察到的现象
- **根因**：**不是复述症状，而是解释因果链**——为什么会发生这个症状？是外部因素（环境、原文数据）导致，还是 SKILL.md 的规则本身有问题（缺失/模糊/矛盾），或是缺少一步校验/门控？
- **解决**：具体解决方法（针对本次问题的临时修复）
- **触发条件**：什么情况下会遇到
- **严重性**：低/中/高/致命
- **业务阶段**：分析/编写/质检/流程

**根因提取是整个工作流程的关键步骤**——如果只停留在"症状"层面（如"漏了一个字段"），无法做出 Phase 3.5 的分类判断。必须往下追问一层："为什么会漏？是 LLM 没读到位置，还是 SKILL.md 从未要求读这个位置？"

### Phase 3.5: 分类判断 —— 一次性失误 vs 设计缺陷（核心分支点）

**判定为"设计缺陷"，需满足以下任一条件：**

| 条件 | 判断方法 |
|------|---------|
| (a) SKILL.md 对应章节确实模糊/缺失/矛盾 | **必须实际读取该 skill 的 SKILL.md 对应章节**，引用原文核实——不能凭对话推测，必须看到实际文本才能下结论 |
| (b) 同类问题历史 ≥1 次 | Phase 2.5 的 `check_gotcha_history.py` 返回 `similar_count >= 1` |
| (c) 根源是缺少校验/门控机制 | 该环节本该有自检步骤、异常处理路径、前置检查，但 SKILL.md 里没有 |

**判定为"一次性失误"，适用于：**
- 环境问题（网络超时、外部服务离线、Docker 未启动等）
- 外部数据本身有问题（招标文件原文自相矛盾、格式损坏）
- SKILL.md 已经写得清楚，只是执行时的偶然疏漏，且是**首次**出现（没有 (a)(b)(c) 任一证据）

**⚠️ 关键约束**：条件 (a) 要求真实读取 SKILL.md，不可跳过。如果不确定，优先假设是"设计缺陷"并读取核实——漏判一次性失误的代价（多写一份报告）远小于漏判设计缺陷的代价（问题继续复发）。

### Phase 4A: 一次性失误 → 注入轻量 gotcha

```bash
python3 $SCRIPTS/inject_gotcha.py \
  --skill {target_skill} \
  --title "问题简短标题" \
  --problem "问题描述" \
  --solution "解决方案" \
  --output-dir "{workDir}"
```

**注意**：`--output-dir` 必须指定为当前工作目录，确保写入可写区域。
输出文件为 `{workDir}/{skill}-gotchas.md`。

### Phase 4B: 设计缺陷 → 生成结构化诊断报告（新增）

**前置：必须先读取该 skill 的 SKILL.md 对应章节**，确认定位准确、引用原文无误，再调用脚本。

```bash
python3 $SCRIPTS/generate_defect_report.py \
  --skill {target_skill} \
  --title "缺陷标题（描述缺陷本质，不是症状）" \
  --defect-type "缺失规则|规则模糊|规则矛盾|缺少校验|示例错误|路径失效|其他" \
  --location "{skill}/SKILL.md 的具体章节名" \
  --current-text "SKILL.md 中相关章节的原文引用；规则完全缺失时填 (无对应规则，说明该章节未提及此场景)" \
  --root-cause "为什么这段文字/这处空白会导致观察到的错误" \
  --trigger-scenario "什么样的输入/上下文会触发" \
  --historical-count {Phase 2.5 返回的 similar_count} \
  --suggested-fix "具体的替换/新增文本，直接可用于修改 SKILL.md" \
  --impact-assessment "这个改动会影响哪些其他章节/流程" \
  --output-dir "{workDir}"
```

模板和更详细的编写指南见 `templates/defect_report_template.md`。

输出文件为 `{workDir}/{skill}-defect-reports.md`。

**脚本内建的安全约束**：
- 仅接受 `bid-*` skill
- 内容必须落在投标业务范围内
- 标题重复时拒绝写入（提示"请检查是否需要更新历史频次而非新建"）
- 严重程度自动按历史频次计算：≥2次🔴高，1次🟡中，0次但规则确实缺失🔵待观察

### Phase 5: 确认与输出

**一次性失误分支：**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 投标经验已记录（一次性失误）

新增条目：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### {标题}

**症状：** {症状简述}
**根因：** {根因简述}
**严重性：** {严重性}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

输出文件：{workDir}/{skill}-gotchas.md
下次使用该 skill 时可参考此经验
```

**设计缺陷分支：**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 检测到 Skill 设计缺陷 [DEFECT-{N}]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
定位：{skill}/SKILL.md 《{章节名}》
缺陷类型：{类型}
严重程度：{严重程度}（历史出现 {N} 次）

根因：{根因简述}
建议修改：{建议修改摘要}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

输出文件：{workDir}/{skill}-defect-reports.md
⚠️ 本报告仅供参考，SKILL.md 未被自动修改，需人工审阅后决定是否采纳该建议
```

## 高级功能

### 自检（检测作用域漂移）

```bash
python3 $SCRIPTS/self_check.py --skills-root /mnt/oldroot/home/bird/xyy/smartbid-platform/packages/bidsmart-skills/skills
```

扫描所有 bid-* skills 的 gotchas.md，检测是否有非投标业务内容混入。

## 使用示例

### 场景 1：一次性失误（首次出现，规则本身没问题）

```
User: 这次 DocScan 服务超时了，导致占位符检测失败
User: 记住这个问题

→ validate_context.py → ✅ 通过
→ identify_skill.py → bid-md2doc（置信度 55%）
→ check_gotcha_history.py → similar_count=0
→ Phase 3.5 判断：环境问题（DocScan 离线），SKILL.md 已有优雅降级规则 → 一次性失误
→ inject_gotcha.py → 写入 {workDir}/bid-md2doc-gotchas.md
```

### 场景 2：设计缺陷（同类问题复发）

```
User: 又是特定资格条件的问题，跟上次一样，写"无"的时候又被漏掉了
User: 分析一下根因

→ validate_context.py → ✅ 通过
→ identify_skill.py → bid-analysis（置信度 67%）
→ check_gotcha_history.py → similar_count=1（匹配到上次的 gotcha 记录）
→ Phase 3.5 判断：满足条件(b) 历史复发 → 设计缺陷
→ 读取 bid-analysis/SKILL.md《资格要求提取》章节，确认无对应规则
→ generate_defect_report.py → 写入 {workDir}/bid-analysis-defect-reports.md [DEFECT-1]
```

### 场景 3：通用编程问题（拒绝）

```
User: 这个 Python 代码报错了
User: 记住这个错误

→ validate_context.py → ❌ 不满足2项条件
→ "bid-learner 仅用于投标业务相关问题的学习"
```

## 完成状态

```
--- BID-LEARNER COMPLETE ---
分类: {一次性失误/设计缺陷}
目标 Skill: {skill_name}
```

一次性失误分支追加：
```
问题类型: {问题类型}
严重性: {严重性}
输出文件: {workDir}/{skill}-gotchas.md
```

设计缺陷分支追加：
```
缺陷编号: DEFECT-{N}
缺陷类型: {类型}
定位: {skill}/SKILL.md 《{章节名}》
历史频次: 第{N}次
输出文件: {workDir}/{skill}-defect-reports.md
⚠️ 本报告仅供参考，SKILL.md 未被自动修改
```

统一收尾：
```
状态: SUCCESS
--- END ---
```

## 注意事项

### 范围控制
1. **始终验证上下文** — 不在投标业务范围内的对话拒绝学习
2. **定期自检** — 运行 `self_check.py` 检测作用域漂移

### 分类判断质量
1. **根因不能停留在症状层面** — Phase 3 必须往下追问一层因果
2. **条件 (a) 必须实际读取 SKILL.md** — 不可凭对话内容推测 SKILL.md 是否有对应规则
3. **不确定时优先假设是设计缺陷** — 漏判一次性失误的代价远小于放过一个真实缺陷

### 数据质量
1. **人工确认** — 生成 gotcha 或缺陷报告草稿后，让用户确认再写入
2. **避免冗余** — 两个脚本都内建重复检测
3. **保持简洁** — gotcha 每条控制在 10 行内；缺陷报告可以更详细，但建议修改必须具体可执行
4. **诚实评估影响面** — 缺陷报告的"建议修改"如果会牵连其他章节，必须在"影响评估"中写明
