#!/usr/bin/env python3
"""
历史同类问题检查脚本

在生成 gotcha 或缺陷报告之前，检查该 skill 是否已有相似标题/关键词的
历史记录（gotchas 或缺陷报告）。用于驱动"一次性失误 vs 设计缺陷"的分类
判断——同类问题反复出现，说明轻量记录没有生效，必须升级为缺陷诊断。

调用方式：
  python3 check_gotcha_history.py --skill bid-analysis --title "特定资格条件误判"
  python3 check_gotcha_history.py --skill bid-analysis --title "..." \
    --gotcha-dir /path/to/workDir --skills-root /path/to/skills
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


def get_default_skills_root() -> str:
    """从脚本自身位置推算 skills 根目录：scripts/ -> bid-learner/ -> skills/"""
    script_dir = Path(__file__).resolve().parent
    return str(script_dir.parent.parent)


def _tokenize(text: str) -> set:
    """粗粒度分词，兼容中文和英文：
    - 英文/数字片段按 \\w+ 切分为单词
    - 连续中文片段按 2-gram 字符切分（中文没有空格分词，整句切分会导致重叠永远为0）
    """
    text = text.lower()
    tokens = set()
    for run in re.findall(r'[a-z0-9]+|[一-鿿]+', text):
        if re.match(r'^[a-z0-9]+$', run):
            if len(run) >= 2:
                tokens.add(run)
        else:
            # 中文片段：2-gram 字符切分
            for i in range(len(run) - 1):
                tokens.add(run[i:i + 2])
            if len(run) == 1:
                tokens.add(run)
    return tokens


def _extract_entries(content: str, heading_prefix: str = '### ') -> List[Dict]:
    """从 markdown 内容中提取 (标题, 日期) 条目列表。"""
    entries = []
    sections = content.split(heading_prefix)
    for section in sections[1:]:
        lines = section.split('\n')
        title = lines[0].strip()
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', section)
        date = date_match.group(1) if date_match else None
        entries.append({"title": title, "date": date})
    return entries


def check_history(
    skill_name: str,
    title: str,
    gotcha_dir: str = None,
    skills_root: str = None,
) -> Dict:
    """
    检查该 skill 的历史 gotchas 和缺陷报告中，是否有与 title 相似的条目。

    匹配策略：标题分词后计算重叠度，重叠 >= 2 个有效词或重叠率 >= 50% 视为相似。
    """
    if not skills_root:
        skills_root = get_default_skills_root()
    skills_root = Path(skills_root)

    candidate_files = []
    # 初始 gotchas（skill 目录下，通常随 skill 一起提交）
    candidate_files.append(skills_root / skill_name / 'gotchas.md')
    # workDir 中的实践 gotchas 和缺陷报告
    if gotcha_dir:
        gd = Path(gotcha_dir)
        candidate_files.append(gd / f'{skill_name}-gotchas.md')
        candidate_files.append(gd / f'{skill_name}-defect-reports.md')

    new_tokens = _tokenize(title)
    matches = []

    for f in candidate_files:
        if not f.exists():
            continue
        content = f.read_text(encoding='utf-8')
        heading_prefix = '### [DEFECT-' if 'defect-reports' in f.name else '### '
        # 缺陷报告的标题格式为 "### [DEFECT-N] 标题"，用更宽松的前缀匹配
        entries = _extract_entries(content, '### ')
        for entry in entries:
            existing_tokens = _tokenize(entry['title'])
            if not existing_tokens:
                continue
            overlap = new_tokens & existing_tokens
            overlap_rate = len(overlap) / max(len(new_tokens), 1)
            if len(overlap) >= 2 or overlap_rate >= 0.5:
                matches.append({
                    "title": entry['title'],
                    "date": entry['date'],
                    "source_file": str(f),
                    "overlap_tokens": sorted(overlap),
                })

    return {
        "similar_count": len(matches),
        "matches": matches,
        "recommendation": (
            "建议按设计缺陷处理：同类问题已出现过，轻量记录未能防止复发"
            if len(matches) >= 1 else
            "可能是首次出现，暂无历史依据升级为设计缺陷（仍需结合 SKILL.md 章节核查判断）"
        ),
    }


def parse_args():
    parser = argparse.ArgumentParser(description='检查同类问题历史出现次数')
    parser.add_argument('--skill', required=True, help='目标 skill 名称（如 bid-analysis）')
    parser.add_argument('--title', required=True, help='本次问题标题')
    parser.add_argument('--gotcha-dir', default=None, help='workDir 中存放 gotchas/缺陷报告的目录')
    parser.add_argument('--skills-root', default=None, help='skills 根目录（默认从脚本位置推算）')
    return parser.parse_args()


def main():
    args = parse_args()
    result = check_history(
        skill_name=args.skill,
        title=args.title,
        gotcha_dir=args.gotcha_dir,
        skills_root=args.skills_root,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == '__main__':
    main()
