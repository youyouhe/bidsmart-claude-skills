# bid-verification - Gotchas

这些是从实践中学到的反直觉知识和常见陷阱。

## Gotchas

### 只核对分析报告未回查原始文件

**问题**：核实时直接读取分析报告中的数据与分析报告自身对比（循环论证），没有真正读取原始招标文件（Word/PDF），导致幻觉数据被当作正确值。

**解决**：核实流程必须：
1. 加载分析报告提取待核实数据点
2. **独立加载原始招标文件**（Word 优先，PDF 次之）
3. 逐项在原文中查找并对比
4. 标注差异和出处

**示例**：
```python
# ❌ 错误做法
report_budget = extract_from_report('预算金额')
verified_budget = extract_from_report('预算金额')  # 循环论证！

# ✅ 正确做法
report_budget = extract_from_report('预算金额')
source_budget = extract_from_word_doc('采购文件.docx', field='预算金额')
is_match = (report_budget == source_budget)
```

*（来自 bidsmart-skills-review.md，注入时间：2026-03-18）*

---

### Word 表格优先级低于 PDF 导致精度损失

**问题**：同时提供 Word 和 PDF 时，先读 PDF 提取数据，但 PDF 中的表格可能因格式转换产生错位或乱码，导致核实结果不准确。

**解决**：严格遵守数据源优先级：
1. **Word (.docx)** — 最高优先级，文本精确、表格结构化
2. **PDF** — 次优先级，仅用于补充或交叉对比
3. 如两种格式内容不一致，以 Word 为准并在核实报告中标注差异

**示例**：
```python
def load_source_document(word_path: str, pdf_path: str):
    """按优先级加载原始文件"""
    if os.path.exists(word_path):
        print("✅ 使用 Word 作为主数据源")
        return load_word_document(word_path)
    elif os.path.exists(pdf_path):
        print("⚠️ 仅有 PDF，精度可能受限")
        return load_pdf_document(pdf_path)
    else:
        raise FileNotFoundError("未找到原始招标文件")
```

*（来自 SKILL.md，注入时间：2026-03-18）*

---

### 分值验算只检查总分未检查子项

**问题**：核实时只验证"技术 40 + 商务 40 + 价格 20 = 100"，但未验证技术大类下的子项是否合计为 40，导致子项错误（如 10+12+15+5=42）未被发现。

**解决**：分值验算必须三层检查：
1. 总分 = 所有大类之和（100分制）
2. 每个大类总分 = 该大类子项之和
3. 每个子项分值 ≥ 0 且为合理数值

**示例**：
```python
def validate_all_scores(scoring_data: dict) -> list:
    """三层分值验算"""
    issues = []

    # 第一层：总分检查
    total_declared = 100
    total_calculated = sum(cat['total'] for cat in scoring_data['categories'])
    if total_declared != total_calculated:
        issues.append(f"总分不一致：声明100分，计算{total_calculated}分")

    # 第二层：大类子项检查
    for category in scoring_data['categories']:
        cat_total = category['total']
        sub_sum = sum(item['score'] for item in category['items'])
        if cat_total != sub_sum:
            issues.append(f"{category['name']} 分值不一致：声明{cat_total}分，子项合计{sub_sum}分")

    # 第三层：子项合理性检查
    for category in scoring_data['categories']:
        for item in category['items']:
            if item['score'] <= 0 or item['score'] > 50:
                issues.append(f"异常分值：{item['name']} = {item['score']}分")

    return issues
```

*（来自 bidsmart-skills-review.md，注入时间：2026-03-18）*

---

### 采购编号位数错误未被检测

**问题**：招标文件封面采购编号为 "SDGP370000000000000000"（20位），分析报告写成 "SDGP3700000000000000"（18位），核实时只检查了前缀 "SDGP" 一致就通过，未检查完整编号。

**解决**：关键数据核实必须**逐字符精确对比**，不能只检查前缀或模糊匹配：
```python
def verify_exact_match(field_name: str, report_value: str, source_value: str) -> dict:
    """精确匹配验证"""
    if report_value == source_value:
        return {"status": "✅", "match": True}
    else:
        return {
            "status": "❌",
            "match": False,
            "report": report_value,
            "source": source_value,
            "issue": f"字符不一致（长度：{len(report_value)} vs {len(source_value)}）"
        }
```

*（来自 bidsmart-skills-review.md，注入时间：2026-03-18）*

---

### 核实完成后未自动修正分析报告

**问题**：核实报告中标注了 5 个❌错误项，但分析报告未被更新，后续 bid-commercial-proposal 仍然读取错误的分析报告，导致响应文件错误传播。

**解决**：核实完成后必须自动修正分析报告：
1. 解析核实报告中的所有❌错误项
2. 定位分析报告中的对应位置
3. 用原文正确值替换
4. 在修正处添加注释说明修正原因

**示例**：
```python
def auto_fix_analysis_report(verification_errors: list, report_path: str):
    """根据核实结果自动修正分析报告"""
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    for error in verification_errors:
        # 定位错误位置
        wrong_value = error['report_value']
        correct_value = error['source_value']
        field_name = error['field']

        # 替换并添加注释
        old_line = f"{field_name}：{wrong_value}"
        new_line = f"{field_name}：{correct_value}  <!-- 已修正（原值：{wrong_value}，核实时间：{datetime.now().date()}） -->"

        content = content.replace(old_line, new_line)

    # 写回文件
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 已自动修正 {len(verification_errors)} 处错误")
```

*（来自 SKILL.md，注入时间：2026-03-18）*
