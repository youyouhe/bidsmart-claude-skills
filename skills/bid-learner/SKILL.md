---
name: bid-learner
description: >
  投标业务专用经验学习器。从对话中提取投标相关的错误、问题和经验教训，
  自动注入到 bid-* skills 的 gotchas.md 文件中。

  严格限定范围：仅处理投标业务（招标分析、响应文件编写、质检等），
  不学习通用编程、其他领域知识。

  触发条件：
  1. 用户说"记住这个错误" / "记住这次教训" / "总结经验" / "学习这个案例"
  2. 用户明确要求"更新 bid-XXX 的 gotchas"
  3. 用户说"投标经验记录" / "标书问题记录"

  前置条件：
  - 当前对话必须在投标项目上下文中（有招标文件、分析报告、响应文件等）
  - 最近调用过至少一个 bid-* skill

  不触发条件：
  ❌ 非投标相关对话
  ❌ 用户只是抱怨但没明确要求记录
  ❌ 问题与 bid 业务无关（如通用代码错误）
---

# 投标业务经验学习器

## 核心原则

### 1. 严格的范围限定

**仅学习以下类型的经验：**

✅ 招标文件分析错误（评分表提取、资格条件理解偏差、金额/时间解析错误）
✅ 响应文件编写问题（技术方案遗漏、商务附件错误、报价不一致、占位符残留）
✅ 质检和验证问题（验证逻辑遗漏、合规检查不全、文件编号错误）
✅ 流程编排问题（Pipeline 阶段失败、断点续跑异常、自动修复失效）

❌ **不学习**：通用编程错误、非投标领域业务、系统配置/网络问题、非 bid-* skills 的问题

### 2. 沙箱安全约束

**⚠️ 重要：skills 目录在沙箱中是只读的。**

所有 gotcha 输出必须写入工作目录（workDir），不能直接写入 skills 目录。
脚本通过 `--output-dir` 参数指定写入位置。

## 脚本调用规范

**⚠️ 重要：不要复制脚本到工作目录！直接通过绝对路径调用。**

脚本基础路径（固定）：
```
SCRIPTS=/mnt/oldroot/home/bird/xyy/smartbid-platform/packages/bidsmart-skills/skills/bid-learner/scripts
```

### 可用脚本

| 脚本 | 功能 | 关键参数 |
|------|------|---------|
| `validate_context.py` | 验证对话是否在投标上下文 | `--text "对话文本"` |
| `identify_skill.py` | 识别问题归属的 skill | `--problem "描述" [--context "上下文"]` |
| `inject_gotcha.py` | 注入 gotcha 到指定 skill | `--skill X --title Y --problem Z --solution W --output-dir DIR` |
| `self_check.py` | 扫描 gotchas 检测作用域漂移 | `[--skills-root DIR]` |

## 工作流程

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

### Phase 3: 从对话中提取问题要素

由 LLM 完成（不需要脚本），提取：
- **症状**：用户观察到的现象
- **原因**：根因分析
- **解决**：具体解决方法
- **触发条件**：什么情况下会遇到
- **严重性**：低/中/高/致命
- **业务阶段**：分析/编写/质检/流程

### Phase 4: 注入 Gotcha

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

### Phase 5: 确认与输出

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 投标经验已记录

新增条目：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### {标题}

**症状：** {症状简述}
**原因：** {原因简述}
**严重性：** {严重性}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

输出文件：{workDir}/{skill}-gotchas.md
下次使用该 skill 时可参考此经验
```

## 高级功能

### 自检（检测作用域漂移）

```bash
python3 $SCRIPTS/self_check.py --skills-root /mnt/oldroot/home/bird/xyy/smartbid-platform/packages/bidsmart-skills/skills
```

扫描所有 bid-* skills 的 gotchas.md，检测是否有非投标业务内容混入。

## 使用示例

### 场景 1：分析阶段错误（有效）

```
User: 等等，特定资格条件不对，原文写的"无"，你写了"须具有资质"
User: 记住这个错误

→ validate_context.py → ✅ 通过
→ identify_skill.py → bid-analysis（置信度 67%）
→ inject_gotcha.py → 写入 {workDir}/bid-analysis-gotchas.md
```

### 场景 2：通用编程问题（拒绝）

```
User: 这个 Python 代码报错了
User: 记住这个错误

→ validate_context.py → ❌ 不满足2项条件
→ "bid-learner 仅用于投标业务相关问题的学习"
```

## 完成状态

```
--- BID-LEARNER COMPLETE ---
目标 Skill: {skill_name}
问题类型: {问题类型}
严重性: {严重性}
输出文件: {workDir}/{skill}-gotchas.md
状态: SUCCESS
--- END ---
```

## 注意事项

### 范围控制
1. **始终验证上下文** — 不在投标业务范围内的对话拒绝学习
2. **定期自检** — 运行 `self_check.py` 检测作用域漂移

### 数据质量
1. **人工确认** — 生成 gotcha 草稿后，让用户确认再注入
2. **避免冗余** — 注入前脚本自动检查重复
3. **保持简洁** — 每个 gotcha 控制在 10 行内
