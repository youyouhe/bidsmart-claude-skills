#!/usr/bin/env python3
"""
自检脚本 - 检测作用域漂移

扫描所有 bid-* skills 的 gotchas.md，检测是否有非投标业务的经验混入。

调用方式：
  python3 self_check.py --skills-root /path/to/skills
  python3 self_check.py  （默认从脚本位置推算 skills 根目录）
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List


BID_KEYWORDS = [
    '招标', '投标', '标书', '响应文件', '评分', '资格', '报价', '磋商', '采购',
    '技术标', '商务标', '质检', '分析报告', '核对报告', '附件', '供应商'
]

NON_BID_KEYWORDS = [
    'react', 'vue', 'angular', 'svelte', 'api', 'rest', 'graphql',
    'database', 'mysql', 'postgres', 'mongodb', 'redis',
    'server', 'nginx', 'apache', 'kubernetes', 'docker',
    'bug', 'debug', 'testing', 'jest', 'pytest',
    'npm', 'yarn', 'pip', 'git', 'github', 'gitlab',
    'frontend', 'backend', 'fullstack', 'deployment'
]


def get_default_skills_root() -> str:
    """从脚本自身位置推算 skills 根目录：scripts/ -> bid-learner/ -> skills/"""
    script_dir = Path(__file__).resolve().parent
    return str(script_dir.parent.parent)


def scan_gotchas(skills_root: str) -> Dict:
    """
    扫描所有 bid-* skills 的 gotchas.md，检测作用域漂移
    """
    skills_root = Path(skills_root)
    if not skills_root.exists():
        return {"suspicious": [], "clean": 0, "total_skills": 0, "error": f"目录不存在: {skills_root}"}

    bid_skills = [d for d in skills_root.iterdir() if d.is_dir() and d.name.startswith('bid-')]

    suspicious_items = []
    clean_count = 0

    for skill_path in bid_skills:
        gotcha_file = skill_path / 'gotchas.md'

        if not gotcha_file.exists():
            continue

        with open(gotcha_file, 'r', encoding='utf-8') as f:
            content = f.read()

        sections = content.split('### ')

        for i, section in enumerate(sections[1:], start=1):
            section_lower = section.lower()

            has_bid_context = any(kw in section for kw in BID_KEYWORDS)
            non_bid_matches = [kw for kw in NON_BID_KEYWORDS if kw in section_lower]

            if non_bid_matches and not has_bid_context:
                title = section.split('\n')[0].strip()
                suspicious_items.append({
                    "skill": skill_path.name,
                    "file": str(gotcha_file),
                    "section": i,
                    "title": title,
                    "non_bid_keywords": non_bid_matches,
                    "preview": section[:200].replace('\n', ' ')
                })
            else:
                clean_count += 1

    return {
        "suspicious": suspicious_items,
        "clean": clean_count,
        "total_skills": len(bid_skills)
    }


def format_report(result: Dict) -> str:
    """格式化自检报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("Bid-Learner 作用域自检报告")
    lines.append("=" * 60)
    lines.append(f"扫描 Skills: {result['total_skills']} 个")
    lines.append(f"正常条目: {result['clean']} 条")
    lines.append(f"可疑条目: {len(result['suspicious'])} 条")
    lines.append("")

    if result['suspicious']:
        lines.append("⚠️ 检测到可疑条目（可能存在作用域漂移）：")
        lines.append("")

        for item in result['suspicious']:
            lines.append(f"【{item['skill']}】第 {item['section']} 条")
            lines.append(f"  标题: {item['title']}")
            lines.append(f"  非投标关键词: {', '.join(item['non_bid_keywords'])}")
            lines.append(f"  预览: {item['preview']}")
            lines.append(f"  文件: {item['file']}")
            lines.append("")

        lines.append("建议：检查以上条目是否真正属于投标业务，考虑移除或修改")
    else:
        lines.append("✅ 未检测到作用域漂移，所有 gotchas 均属于投标业务范畴")

    lines.append("=" * 60)
    return '\n'.join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description='Bid-Learner 作用域自检')
    parser.add_argument('--skills-root', default=None,
                        help='skills 根目录（默认从脚本位置推算）')
    return parser.parse_args()


def main():
    args = parse_args()
    skills_root = args.skills_root or get_default_skills_root()

    result = scan_gotchas(skills_root)

    # JSON 输出到 stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 可读报告输出到 stderr
    print("\n", file=sys.stderr)
    print(format_report(result), file=sys.stderr)

    sys.exit(0 if not result['suspicious'] else 1)


if __name__ == '__main__':
    main()
