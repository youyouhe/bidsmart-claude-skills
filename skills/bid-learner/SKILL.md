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

✅ **招标文件分析错误**
- 评分表提取错误
- 资格条件理解偏差
- 金额/时间解析错误
- 附件清单遗漏

✅ **响应文件编写问题**
- 技术方案章节遗漏
- 商务附件生成错误
- 报价不一致
- 占位符残留

✅ **质检和验证问题**
- 验证逻辑遗漏
- 合规检查不全
- 文件编号错误

✅ **流程编排问题**
- Pipeline 阶段失败
- 断点续跑异常
- 自动修复失效

❌ **不学习以下内容：**
- 通用 Python/JavaScript 编程错误
- 非投标领域的业务逻辑
- 系统配置、网络问题
- 其他 skills（非 bid-*）的问题

### 2. 上下文验证机制

每次触发时，必须先验证上下文：

```python
def validate_bid_context(conversation_history: list) -> bool:
    """验证当前对话是否在投标业务上下文中"""

    # 检查1：是否有投标相关文件
    bid_files = [
        '招标文件', '磋商文件', '采购文件',
        '分析报告.md', '响应文件/', '核对报告.md'
    ]
    has_bid_files = any(f in str(conversation_history) for f in bid_files)

    # 检查2：最近是否调用过 bid-* skills
    recent_skills = extract_skill_calls(conversation_history, limit=10)
    has_bid_skills = any(s.startswith('bid-') for s in recent_skills)

    # 检查3：对话主题是否与投标相关
    bid_keywords = [
        '投标', '招标', '标书', '响应文件', '技术标', '商务标',
        '评分', '资格', '报价', '磋商', '采购'
    ]
    topic_relevant = any(kw in str(conversation_history) for kw in bid_keywords)

    # 至少满足2个条件
    score = sum([has_bid_files, has_bid_skills, topic_relevant])
    return score >= 2

# 如果验证失败，拒绝学习
if not validate_bid_context(context):
    print("⚠️ 当前上下文不在投标业务范围内，无法记录经验。")
    print("bid-learner 仅用于投标相关问题的学习。")
    exit(1)
```

## 工作流程

### Phase 1: 上下文验证与范围检查

```
1. 读取最近 20 轮对话历史
2. 运行 validate_bid_context()
3. 如果不通过 → 拒绝并说明原因
4. 如果通过 → 继续到 Phase 2
```

### Phase 2: 问题分析

从对话中提取：

#### 2.1 识别问题所属的 Skill

```python
def identify_target_skill(context: dict) -> str:
    """识别问题归属的 bid skill"""

    # 优先级1：用户明确指定
    if match := re.search(r'(bid-\w+)', context['user_message']):
        return match.group(1)

    # 优先级2：从最近的 skill 调用推断
    recent_calls = context['recent_skill_calls']
    bid_skills = [s for s in recent_calls if s.startswith('bid-')]
    if bid_skills:
        return bid_skills[-1]  # 最近的 bid skill

    # 优先级3：从错误堆栈推断
    if context.get('error_trace'):
        for skill in ['bid-analysis', 'bid-verification', 'bid-tech-proposal',
                      'bid-commercial-proposal', 'bid-assembly', 'bid-manager']:
            if skill in context['error_trace']:
                return skill

    # 优先级4：从问题描述推断
    problem_desc = context['problem_description']
    mappings = {
        '分析报告': 'bid-analysis',
        '核实': 'bid-verification',
        '技术标': 'bid-tech-proposal',
        '商务标': 'bid-commercial-proposal',
        '质检': 'bid-assembly',
        '流程': 'bid-manager',
        '图表': 'bid-mermaid-diagrams',
        '扫描件': 'bid-material-search',
        'Word': 'bid-md2doc',
    }

    for keyword, skill in mappings.items():
        if keyword in problem_desc:
            return skill

    return None  # 无法确定，询问用户
```

#### 2.2 提取问题要素

```python
def extract_problem_elements(context: dict) -> dict:
    """从对话中提取问题的关键要素"""

    return {
        'symptom': extract_symptom(context),      # 用户看到的现象
        'cause': infer_root_cause(context),       # 根因分析
        'solution': extract_solution(context),    # 解决方法
        'trigger': infer_trigger_condition(context),  # 触发条件
        'severity': assess_severity(context),     # 严重性
        'frequency': check_if_recurring(context), # 是否重复问题
    }

def extract_symptom(context: dict) -> str:
    """提取症状描述"""
    # 从用户的描述中提取"观察到的现象"
    user_complaints = [
        msg for msg in context['messages']
        if msg['role'] == 'user' and any(kw in msg['content']
            for kw in ['错误', '问题', '不对', '不一致', '遗漏'])
    ]

    if user_complaints:
        # 取最详细的一条描述
        return max(user_complaints, key=lambda m: len(m['content']))['content']

    return "（需手动补充症状描述）"

def infer_root_cause(context: dict) -> str:
    """推断根本原因"""
    # 从 Claude 的回复中提取根因分析
    # 或基于问题类型推断常见原因

    problem_type = classify_problem(context)

    common_causes = {
        'hallucination': 'AI 基于常识推测，未严格遵循原文',
        'parsing_error': 'PDF/Word 解析时表格识别错误',
        'inconsistency': '多个文件独立生成，未维护数据一致性',
        'missing_content': '生成时跳过了某些必需内容',
        'validation_gap': '验证逻辑不完整，未检测到此类问题',
    }

    return common_causes.get(problem_type, "（需分析根本原因）")

def extract_solution(context: dict) -> str:
    """提取解决方案"""
    # 从后续对话中提取"最终如何解决"
    solution_keywords = ['解决', '修复', '改成', '应该', '正确的是']

    solutions = [
        msg['content'] for msg in context['messages']
        if any(kw in msg['content'] for kw in solution_keywords)
    ]

    if solutions:
        return solutions[-1]  # 最终的解决方案

    return "（需补充解决方案）"
```

### Phase 3: 生成 Gotcha 条目

使用标准模板：

```markdown
### {编号}. {问题简短标题}

**症状：**
{用户观察到的现象}

**原因：**
{根本原因分析}

**解决：**
```{language}
{具体代码或步骤}
```

**触发条件：**
{什么情况下会遇到}

**频率：** {低/中/高}
**严重性：** {低/中/高/致命}
**业务阶段：** {分析/编写/质检/流程}
**记录时间：** {YYYY-MM-DD}
**项目背景：** {简要描述当时场景}

**防御策略：**
{如何在代码/流程中预防此问题}
```

### Phase 4: 注入到目标 Skill

```bash
python scripts/inject_gotcha.py \
  --skill {target_skill} \
  --gotcha gotcha_draft.json \
  --validate-scope  # 强制验证是否属于 bid 范围
```

### Phase 5: 确认与输出

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 投标经验已学习并注入到 {skill}/gotchas.md

新增条目（第{N}条）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### {N}. {标题}

**症状：** {症状简述}
**原因：** {原因简述}
**严重性：** {严重性}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

统计信息：
• 该 skill 当前共有 {总数} 个已知问题
• 本次记录的问题严重性：{严重性}
• 下次使用该 skill 时会自动读取此经验

{如果是高频问题（>=3次）}
⚠️ 这是高频问题（第{N}次记录），建议：
  1. 考虑添加自动验证脚本
  2. 或重构相关逻辑以根治问题
```

## 高级功能

### 1. 模式识别（跨 Skill 分析）

当积累一定数量 gotchas 后，自动分析模式：

```python
def analyze_patterns_across_skills():
    """跨 skill 分析问题模式"""

    all_gotchas = []
    for skill in get_all_bid_skills():
        gotchas = load_gotchas(skill)
        all_gotchas.extend([(skill, g) for g in gotchas])

    # 模式1：相同根因的问题
    causes = {}
    for skill, gotcha in all_gotchas:
        cause = gotcha['cause']
        causes.setdefault(cause, []).append((skill, gotcha))

    # 找出影响多个 skills 的根因
    systemic_issues = {
        cause: skills
        for cause, skills in causes.items()
        if len(set(s for s, _ in skills)) >= 2  # 至少影响2个skills
    }

    # 模式2：高频问题
    high_freq = [
        (skill, g) for skill, g in all_gotchas
        if g.get('frequency') == '高'
    ]

    # 模式3：致命问题
    critical = [
        (skill, g) for skill, g in all_gotchas
        if g.get('severity') == '致命'
    ]

    return {
        'systemic_issues': systemic_issues,
        'high_frequency': high_freq,
        'critical_issues': critical,
    }
```

### 2. 自动生成改进建议

基于积累的 gotchas，生成系统性改进建议：

```python
def generate_improvement_suggestions(patterns: dict) -> list:
    """生成改进建议"""

    suggestions = []

    # 建议1：针对系统性问题
    for cause, affected_skills in patterns['systemic_issues'].items():
        skill_names = [s for s, _ in affected_skills]
        suggestions.append({
            'priority': 'high',
            'type': 'architectural',
            'title': f'系统性问题：{cause}',
            'affected_skills': skill_names,
            'suggestion': f'考虑在架构层面解决，避免在每个 skill 中重复修复'
        })

    # 建议2：针对高频问题
    if len(patterns['high_frequency']) >= 3:
        suggestions.append({
            'priority': 'high',
            'type': 'automation',
            'title': '高频问题需要自动化防御',
            'suggestion': '为这些高频问题创建自动验证脚本'
        })

    # 建议3：针对致命问题
    if patterns['critical_issues']:
        suggestions.append({
            'priority': 'critical',
            'type': 'immediate_action',
            'title': '存在致命问题需立即修复',
            'issues': patterns['critical_issues'],
            'suggestion': '优先处理致命问题，避免导致废标'
        })

    return suggestions
```

### 3. 防止经验异化的自我检查

定期检查 gotchas.md 的内容，确保不偏离投标业务：

```python
def self_check_for_scope_drift():
    """检查是否有非投标业务的经验混入"""

    bid_keywords = [
        '招标', '投标', '标书', '响应文件', '评分', '资格',
        '报价', '磋商', '采购', '技术标', '商务标', '质检'
    ]

    non_bid_keywords = [
        'React', 'Vue', 'API', 'Database', 'Server',
        'Bug', 'Debug', 'npm', 'git', 'Docker'
    ]

    for skill in get_all_bid_skills():
        gotchas = load_gotchas(skill)

        for i, gotcha in enumerate(gotchas):
            content = str(gotcha).lower()

            # 检查是否包含投标关键词
            has_bid_context = any(kw in content for kw in bid_keywords)

            # 检查是否包含非投标关键词
            has_non_bid = any(kw.lower() in content for kw in non_bid_keywords)

            # 标记可疑条目
            if has_non_bid and not has_bid_context:
                print(f"⚠️ 可疑条目：{skill}/gotchas.md 第{i+1}条")
                print(f"   内容：{gotcha['title']}")
                print(f"   可能偏离了投标业务范围")
```

## 使用示例

### 场景 1：分析阶段错误（有效）

```
[对话上下文]
• 文件：某某项目磋商文件.pdf
• 已调用：bid-analysis
• 问题：特定资格条件幻觉

User: 等等，特定资格条件不对，原文写的"无"，你写了"须具有资质"
Claude: 抱歉...
User: 记住这个错误

[触发 bid-learner]
Claude:
✅ 上下文验证通过（投标业务）
🔍 分析中...
  - 涉及 Skill: bid-analysis
  - 问题类型: 幻觉（hallucination）
  - 严重性: 高

✅ 已注入到 bid-analysis/gotchas.md（第8条）
```

### 场景 2：通用编程问题（拒绝）

```
[对话上下文]
• 文件：test.py
• 问题：Python 语法错误

User: 这个 Python 代码报错了
Claude: 让我看看... 是缩进问题
User: 记住这个错误

[尝试触发 bid-learner]
Claude:
❌ 上下文验证失败
   - 无投标相关文件
   - 未调用 bid-* skills
   - 对话主题非投标业务

⚠️ bid-learner 仅用于投标业务相关问题的学习。
   当前问题属于通用编程错误，不在学习范围内。
```

### 场景 3：跨 Skill 系统性问题（高级）

```
[对话上下文]
• 报价不一致问题（第3次）
• 涉及：bid-commercial-proposal, bid-assembly

User: 又是报价不一致！这已经第三次了
Claude: 确实需要系统性解决...
User: 总结经验，彻底解决

[触发 bid-learner - 深度分析模式]
Claude:
✅ 上下文验证通过
🔍 深度模式分析（高频问题）

问题模式识别：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 系统性问题：数据一致性
  - 影响 skills: bid-commercial-proposal, bid-assembly
  - 出现频率: 第3次（高频）
  - 根本原因: 缺乏单一数据源
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 已注入到：
  • bid-commercial-proposal/gotchas.md（第6条）
  • bid-assembly/gotchas.md（第9条）

💡 系统性改进建议：
  1. 架构改进：引入 company_info 作为唯一数据源
  2. 验证脚本：创建 verify_price_consistency.py
  3. Pipeline 增强：在 S3 阶段锁定报价，后续只读

我可以帮你实现这些改进吗？
```

## 完成状态

每次学习完成后，输出结构化摘要：

```
--- BID-LEARNER COMPLETE ---
目标 Skill: {skill_name}
条目编号: 第{N}条
问题类型: {问题类型}
严重性: {严重性}
频率: {频率}
是否高频: {yes/no}
改进建议: {建议数量}条
状态: SUCCESS
--- END ---
```

## 注意事项

### 范围控制

1. **始终验证上下文** - 不在投标业务范围内的对话拒绝学习
2. **定期自检** - 每月运行 `self_check_for_scope_drift()`
3. **用户提示** - 当拒绝学习时，友好说明原因

### 数据质量

1. **人工确认** - 生成 gotcha 草稿后，让用户确认再注入
2. **避免冗余** - 注入前检查是否已有类似问题
3. **保持简洁** - 每个 gotcha 控制在 10 行内（不含代码示例）

### 维护策略

1. **定期清理** - 半年一次，清理已解决或过时的 gotchas
2. **版本标记** - 记录每个 gotcha 适用的 skill 版本
3. **优先级排序** - 按严重性和频率排序，高优先级靠前
