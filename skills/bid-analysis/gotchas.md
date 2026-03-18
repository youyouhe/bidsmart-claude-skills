# bid-analysis - Gotchas

这些是从实践中学到的反直觉知识和常见陷阱。

## Gotchas

### 特定资格条件为"无"被当作可省略

**问题**：磋商邀请中特定资格条件明确写"无"，分析时误认为"既然无要求就不写"，导致分析报告遗漏此字段，后续响应文件缺少资格声明。

**解决**：特定资格条件为"无"仍需在分析报告中显式标注`特定资格条件：无`，并说明这意味着所有符合一般资格的供应商均可参加。

**示例**：
```markdown
### 特定资格条件
**无**

> 本项目无特定资格条件要求，所有满足一般资格条件的供应商均可参加。
```

*（来自 bidsmart-skills-review.md，注入时间：2026-03-18）*

---

### 评分表子项分值未验算导致不一致

**问题**：评分标准表中"技术方案 20分"，但子项合计 5+8+7+5=25分，逐行提取时未发现矛盾，直接输出，导致后续编写时得分目标错误。

**解决**：提取评分标准后**必须执行分值验算**：
1. 计算每个大类的子项分值之和
2. 与大类总分对比
3. 发现不一致时标注 ⚠️ 并在分析报告中提示核查原文

**示例**：
```python
def validate_scoring_table(sections: list) -> list:
    """验证评分表分值一致性"""
    issues = []
    for section in sections:
        declared = section['total_score']
        calculated = sum(item['score'] for item in section['items'])
        if declared != calculated:
            issues.append({
                'section': section['name'],
                'declared': declared,
                'calculated': calculated,
                'diff': calculated - declared
            })
    return issues
```

*（来自 bidsmart-skills-review.md，注入时间：2026-03-18）*

---

### Word 表格中的合并单元格导致提取错位

**问题**：使用 python-docx 提取评分表时，遇到合并单元格（如大类名称跨多行），直接 `row.cells[0].text` 会重复读取或错位。

**解决**：检测合并单元格并跳过重复读取：
```python
from docx.table import _Cell

def extract_table_with_merged_cells(table):
    """处理合并单元格的表格提取"""
    seen_cells = set()
    rows_data = []

    for row in table.rows:
        row_data = []
        for cell in row.cells:
            # 检查是否已处理（合并单元格会重复出现）
            cell_id = id(cell._element)
            if cell_id not in seen_cells:
                seen_cells.add(cell_id)
                row_data.append(cell.text.strip())
            else:
                row_data.append('')  # 已合并，用空字符串占位
        rows_data.append(row_data)

    return rows_data
```

*（来自实践经验，注入时间：2026-03-18）*

---

### 预算金额单位混淆（万元 vs 元）

**问题**：磋商邀请中预算写"230万元"，但提取时只记录数字 230，后续生成报价函时误写为"230元"，导致严重错误。

**解决**：
1. 提取金额时必须同时提取单位
2. 在分析报告中统一标注单位：`预算金额：230万元（2,300,000.00元）`
3. 生成报价时从分析报告读取完整金额字段

**示例**：
```python
import re

def extract_budget(text: str) -> dict:
    """提取预算金额及单位"""
    pattern = r'(\d+(?:\.\d+)?)\s*(万元|元)'
    match = re.search(pattern, text)

    if match:
        amount = float(match.group(1))
        unit = match.group(2)

        # 统一转换为元
        if unit == '万元':
            amount_yuan = amount * 10000
        else:
            amount_yuan = amount

        return {
            'original': match.group(0),
            'amount': amount,
            'unit': unit,
            'amount_yuan': amount_yuan,
            'formatted': f"{amount_yuan:,.2f}元"
        }
```

*（来自 bidsmart-skills-review.md，注入时间：2026-03-18）*

---

### 附件清单遗漏带星号的必须项

**问题**：响应文件组成中有 15 个附件，其中 8 个标注★必须，但提取时只记录附件名称，未标注是否必须，导致响应文件目录规划时无法区分优先级。

**解决**：
1. 提取附件清单时必须标注★标记
2. 在分析报告中明确区分必须/可选
3. 生成响应文件目录时必须附件优先

**示例**：
```markdown
## 响应文件组成

| 序号 | 附件名称 | 是否必须 |
|------|---------|---------|
| 1 | ★报价函 | 必须 |
| 2 | ★营业执照 | 必须 |
| 3 | 类似业绩证明 | 可选 |
| 4 | ★技术方案 | 必须 |
```

*（来自 bidsmart-skills-review.md，注入时间：2026-03-18）*
