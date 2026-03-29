#!/usr/bin/env python3
"""
Gotcha 注入脚本 - 带严格作用域控制

核心功能：将经验教训（gotcha）注入到指定 bid-* skill 的 gotchas.md 文件
安全机制：严格验证投标业务上下文，拒绝非投标领域的经验注入

调用方式：
  python3 inject_gotcha.py --skill bid-analysis --title "标题" --problem "问题" --solution "解决"
  python3 inject_gotcha.py --skill bid-analysis --title "标题" --problem "问题" --solution "解决" \
    --skills-root /path/to/skills --output-dir /path/to/workdir

沙箱兼容：
  - 默认 skills-root 从脚本自身位置推算（向上两级）
  - 如指定 --output-dir，gotcha 写入该目录下的 {skill}-gotchas.md（适用于只读沙箱）
  - 如未指定 --output-dir 且 skills 目录可写，直接写入 {skill}/gotchas.md
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============ 作用域验证 ============

BID_KEYWORDS = [
    '招标', '投标', '标书', '响应文件', '评分', '资格', '报价', '磋商', '采购',
    '技术标', '商务标', '质检', '分析报告', '核对报告', '附件', '供应商'
]

NON_BID_KEYWORDS = [
    'react', 'vue', 'api', 'database', 'server', 'bug', 'debug',
    'npm', 'git', 'docker', 'kubernetes', 'frontend', 'backend'
]


def validate_bid_scope(content: str) -> bool:
    """验证内容是否属于投标业务范畴"""
    content_lower = content.lower()
    has_bid_context = any(kw in content for kw in BID_KEYWORDS)
    has_non_bid = any(kw in content_lower for kw in NON_BID_KEYWORDS)
    if has_non_bid and not has_bid_context:
        return False
    return has_bid_context


def validate_skill_name(skill_name: str) -> bool:
    """验证 skill 名称是否为 bid-* 系列"""
    return skill_name.startswith('bid-')


# ============ 默认路径推算 ============

def get_default_skills_root() -> str:
    """从脚本自身位置推算 skills 根目录：scripts/ -> bid-learner/ -> skills/"""
    script_dir = Path(__file__).resolve().parent
    return str(script_dir.parent.parent)


# ============ Gotcha 注入 ============

def load_existing_gotchas(gotcha_file: Path) -> List[str]:
    """加载已有的 gotchas"""
    if not gotcha_file.exists():
        return []

    with open(gotcha_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_gotcha_section = False
    gotchas = []
    current_gotcha = []

    for line in lines:
        if line.startswith('## Gotchas'):
            in_gotcha_section = True
            continue

        if in_gotcha_section:
            if line.startswith('### '):
                if current_gotcha:
                    gotchas.append(''.join(current_gotcha))
                current_gotcha = [line]
            elif line.strip():
                current_gotcha.append(line)

    if current_gotcha:
        gotchas.append(''.join(current_gotcha))

    return gotchas


def check_duplicate(new_title: str, existing_gotchas: List[str]) -> bool:
    """检查是否重复"""
    new_title_lower = new_title.lower()
    for existing in existing_gotchas:
        existing_title = existing.split('\n')[0].lower()
        if new_title_lower in existing_title or existing_title in new_title_lower:
            return True
    return False


def inject_gotcha(
    skill_name: str,
    title: str,
    problem: str,
    solution: str,
    example: Optional[str] = None,
    skills_root: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> Dict:
    """
    注入 gotcha 到指定 skill

    Args:
        skill_name: 目标 skill 名称（如 bid-analysis）
        title: 问题标题
        problem: 问题描述
        solution: 解决方案
        example: 示例（可选）
        skills_root: skills 根目录（默认从脚本位置推算）
        output_dir: 输出目录（沙箱模式下写入此目录，而非 skills 目录）
    """
    # 验证 skill 名称
    if not validate_skill_name(skill_name):
        return {"success": False, "message": f"❌ 拒绝注入：{skill_name} 不是 bid-* skill", "file": None}

    # 验证内容属于投标业务
    full_content = f"{title} {problem} {solution} {example or ''}"
    if not validate_bid_scope(full_content):
        return {"success": False, "message": "❌ 作用域错误：内容不属于投标业务领域", "file": None}

    # 确定 skills 根目录
    if not skills_root:
        skills_root = get_default_skills_root()
    skills_root = Path(skills_root)

    # 验证 skill 存在
    skill_path = skills_root / skill_name
    if not skill_path.exists():
        return {"success": False, "message": f"❌ Skill 不存在：{skill_path}", "file": None}

    # 确定 gotcha 文件位置
    if output_dir:
        # 沙箱模式：写入 workDir
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        gotcha_file = output_path / f"{skill_name}-gotchas.md"
    else:
        # 直接模式：写入 skill 目录
        gotcha_file = skill_path / 'gotchas.md'

    # 加载已有 gotchas（优先从 skill 目录读取，再从输出目录读取）
    existing_gotchas = load_existing_gotchas(skill_path / 'gotchas.md')
    if output_dir:
        existing_gotchas.extend(load_existing_gotchas(gotcha_file))

    # 构建新 gotcha
    new_gotcha = f"### {title}\n\n"
    new_gotcha += f"**问题**：{problem}\n\n"
    new_gotcha += f"**解决**：{solution}\n\n"
    if example:
        new_gotcha += f"**示例**：\n{example}\n\n"
    new_gotcha += f"*（学习自实践，注入时间：{datetime.now().strftime('%Y-%m-%d')}）*\n\n"

    # 检查重复
    if check_duplicate(title, existing_gotchas):
        return {"success": False, "message": "⚠️ 类似经验已存在，跳过", "file": str(gotcha_file)}

    # 写入或追加
    if not gotcha_file.exists():
        content = f"# {skill_name} - Gotchas\n\n"
        content += "这些是从实践中学到的反直觉知识和常见陷阱。\n\n"
        content += "## Gotchas\n\n"
        content += new_gotcha
    else:
        with open(gotcha_file, 'r', encoding='utf-8') as f:
            content = f.read()
        if '## Gotchas' not in content:
            content += "\n## Gotchas\n\n"
        content += new_gotcha

    with open(gotcha_file, 'w', encoding='utf-8') as f:
        f.write(content)

    location = "workDir" if output_dir else "skills 目录"
    return {
        "success": True,
        "message": f"✅ 已注入到 {gotcha_file.name}（{location}）",
        "file": str(gotcha_file)
    }


# ============ CLI ============

def parse_args():
    parser = argparse.ArgumentParser(description='投标经验注入工具')
    parser.add_argument('--skill', required=True, help='目标 skill 名称（如 bid-analysis）')
    parser.add_argument('--title', required=True, help='问题标题')
    parser.add_argument('--problem', required=True, help='问题描述')
    parser.add_argument('--solution', required=True, help='解决方案')
    parser.add_argument('--example', default=None, help='示例（可选）')
    parser.add_argument('--skills-root', default=None,
                        help='skills 根目录（默认从脚本位置推算）')
    parser.add_argument('--output-dir', default=None,
                        help='输出目录（沙箱模式下写入此目录而非 skills 目录）')
    return parser.parse_args()


def main():
    args = parse_args()

    result = inject_gotcha(
        skill_name=args.skill,
        title=args.title,
        problem=args.problem,
        solution=args.solution,
        example=args.example,
        skills_root=args.skills_root,
        output_dir=args.output_dir,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == '__main__':
    main()
