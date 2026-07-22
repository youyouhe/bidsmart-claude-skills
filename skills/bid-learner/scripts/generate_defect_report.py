#!/usr/bin/env python3
"""
缺陷报告生成脚本 - 带严格作用域控制

核心功能：当问题被判定为"skill 设计缺陷"（而非一次性失误）时，生成结构化
诊断报告，精确定位到 SKILL.md 的具体章节，给出建议修改文本。

⚠️ 本脚本只生成报告，从不修改 SKILL.md 本身。是否采纳由人工审阅决定。

调用方式：
  python3 generate_defect_report.py \
    --skill bid-analysis \
    --title "特定资格条件判断缺少显式规则" \
    --defect-type "缺失规则" \
    --location "SKILL.md《资格要求提取》章节" \
    --current-text "(无对应规则，该章节未提及\"无\"值的处理方式)" \
    --root-cause "SKILL.md 未说明特定资格条件为\"无\"时如何处理，LLM 按常识推断为\"可省略\"" \
    --trigger-scenario "招标文件特定资格条件字段明确写\"无\"" \
    --historical-count 2 \
    --suggested-fix "在《资格要求提取》章节补充：特定资格条件为\"无\"时仍需显式标注" \
    --impact-assessment "仅影响资格要求提取环节，不影响其他章节" \
    --output-dir /path/to/workDir
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============ 作用域验证（与 inject_gotcha.py 保持一致） ============

BID_KEYWORDS = [
    '招标', '投标', '标书', '响应文件', '评分', '资格', '报价', '磋商', '采购',
    '技术标', '商务标', '质检', '分析报告', '核对报告', '附件', '供应商'
]

NON_BID_KEYWORDS = [
    'react', 'vue', 'api', 'database', 'server', 'bug', 'debug',
    'npm', 'git', 'docker', 'kubernetes', 'frontend', 'backend'
]

DEFECT_TYPES = ['缺失规则', '规则模糊', '规则矛盾', '缺少校验', '示例错误', '路径失效', '其他']


def validate_bid_scope(content: str) -> bool:
    content_lower = content.lower()
    has_bid_context = any(kw in content for kw in BID_KEYWORDS)
    has_non_bid = any(kw in content_lower for kw in NON_BID_KEYWORDS)
    if has_non_bid and not has_bid_context:
        return False
    return has_bid_context


def validate_skill_name(skill_name: str) -> bool:
    return skill_name.startswith('bid-')


def get_default_skills_root() -> str:
    script_dir = Path(__file__).resolve().parent
    return str(script_dir.parent.parent)


# ============ 缺陷报告编号 ============

def next_defect_id(report_file: Path) -> int:
    """扫描已有报告，返回下一个可用编号（已有最大编号+1，无报告则从1开始）。"""
    if not report_file.exists():
        return 1
    content = report_file.read_text(encoding='utf-8')
    ids = [int(m) for m in re.findall(r'\[DEFECT-(\d+)\]', content)]
    return max(ids, default=0) + 1


def load_existing_titles(report_file: Path) -> List[str]:
    if not report_file.exists():
        return []
    content = report_file.read_text(encoding='utf-8')
    return re.findall(r'### \[DEFECT-\d+\]\s*(.+)', content)


def check_duplicate(new_title: str, existing_titles: List[str]) -> bool:
    new_title_lower = new_title.lower()
    for existing in existing_titles:
        existing_lower = existing.strip().lower()
        if new_title_lower in existing_lower or existing_lower in new_title_lower:
            return True
    return False


# ============ 报告生成 ============

def generate_defect_report(
    skill_name: str,
    title: str,
    defect_type: str,
    location: str,
    current_text: str,
    root_cause: str,
    trigger_scenario: str,
    historical_count: int,
    suggested_fix: str,
    impact_assessment: str,
    skills_root: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict:
    if not validate_skill_name(skill_name):
        return {"success": False, "message": f"❌ 拒绝生成：{skill_name} 不是 bid-* skill", "file": None}

    full_content = f"{title} {root_cause} {trigger_scenario} {suggested_fix}"
    if not validate_bid_scope(full_content):
        return {"success": False, "message": "❌ 作用域错误：内容不属于投标业务领域", "file": None}

    if defect_type not in DEFECT_TYPES:
        return {
            "success": False,
            "message": f"❌ defect_type 必须是以下之一：{DEFECT_TYPES}",
            "file": None,
        }

    if not skills_root:
        skills_root = get_default_skills_root()
    skills_root = Path(skills_root)

    skill_path = skills_root / skill_name
    if not skill_path.exists():
        return {"success": False, "message": f"❌ Skill 不存在：{skill_path}", "file": None}

    if not output_dir:
        return {"success": False, "message": "❌ 缺陷报告必须指定 --output-dir（写入 workDir，不直接改 skill 目录）", "file": None}

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    report_file = output_path / f"{skill_name}-defect-reports.md"

    existing_titles = load_existing_titles(report_file)
    if check_duplicate(title, existing_titles):
        return {"success": False, "message": "⚠️ 类似缺陷报告已存在，跳过（请检查是否需要更新历史频次而非新建）", "file": str(report_file)}

    defect_id = next_defect_id(report_file)

    severity = "🔴 高" if historical_count >= 2 else ("🟡 中" if historical_count == 1 else "🔵 待观察")

    entry = f"### [DEFECT-{defect_id}] {title}\n\n"
    entry += f"| 项目 | 内容 |\n"
    entry += f"|------|------|\n"
    entry += f"| 缺陷类型 | {defect_type} |\n"
    entry += f"| 严重程度 | {severity}（历史出现 {historical_count} 次） |\n"
    entry += f"| 定位 | {location} |\n\n"
    entry += f"**当前文本引用：**\n> {current_text}\n\n"
    entry += f"**根因分析：**\n{root_cause}\n\n"
    entry += f"**触发场景：**\n{trigger_scenario}\n\n"
    entry += f"**建议修改：**\n{suggested_fix}\n\n"
    entry += f"**影响评估：**\n{impact_assessment}\n\n"
    entry += f"*（诊断时间：{datetime.now().strftime('%Y-%m-%d')}，⚠️ 本报告仅供参考，SKILL.md 未被自动修改）*\n\n---\n\n"

    if not report_file.exists():
        content = f"# {skill_name} - 设计缺陷诊断报告\n\n"
        content += "这些是从实践失败中诊断出的 skill 设计缺陷，需人工审阅后决定是否修改 SKILL.md。\n"
        content += "本文件不会被自动应用到 SKILL.md。\n\n"
        content += entry
    else:
        content = report_file.read_text(encoding='utf-8')
        content += entry

    report_file.write_text(content, encoding='utf-8')

    return {
        "success": True,
        "message": f"✅ 已生成缺陷报告 [DEFECT-{defect_id}]（写入 workDir，未修改 SKILL.md）",
        "file": str(report_file),
        "defect_id": defect_id,
    }


# ============ CLI ============

def parse_args():
    parser = argparse.ArgumentParser(description='投标 skill 设计缺陷诊断报告生成工具')
    parser.add_argument('--skill', required=True, help='目标 skill 名称（如 bid-analysis）')
    parser.add_argument('--title', required=True, help='缺陷标题')
    parser.add_argument('--defect-type', required=True, choices=DEFECT_TYPES, help='缺陷类型')
    parser.add_argument('--location', required=True, help='SKILL.md 中的定位（章节名/大致行号）')
    parser.add_argument('--current-text', required=True, help='SKILL.md 当前文本引用（无对应规则时填写说明）')
    parser.add_argument('--root-cause', required=True, help='根因分析')
    parser.add_argument('--trigger-scenario', required=True, help='触发场景')
    parser.add_argument('--historical-count', type=int, default=0, help='该类问题历史出现次数（不含本次）')
    parser.add_argument('--suggested-fix', required=True, help='建议修改文本')
    parser.add_argument('--impact-assessment', required=True, help='改动影响范围评估')
    parser.add_argument('--skills-root', default=None, help='skills 根目录（默认从脚本位置推算）')
    parser.add_argument('--output-dir', required=True, help='输出目录（workDir，必须指定）')
    return parser.parse_args()


def main():
    args = parse_args()

    result = generate_defect_report(
        skill_name=args.skill,
        title=args.title,
        defect_type=args.defect_type,
        location=args.location,
        current_text=args.current_text,
        root_cause=args.root_cause,
        trigger_scenario=args.trigger_scenario,
        historical_count=args.historical_count,
        suggested_fix=args.suggested_fix,
        impact_assessment=args.impact_assessment,
        skills_root=args.skills_root,
        output_dir=args.output_dir,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == '__main__':
    main()
