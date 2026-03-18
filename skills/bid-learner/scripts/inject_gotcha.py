#!/usr/bin/env python3
"""
Gotcha 注入脚本 - 带严格作用域控制

核心功能：将经验教训（gotcha）注入到指定 bid-* skill 的 gotchas.md 文件
安全机制：严格验证投标业务上下文，拒绝非投标领域的经验注入
"""

import os
import sys
import json
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

    # 检查投标关键词
    has_bid_context = any(kw in content for kw in BID_KEYWORDS)

    # 检查非投标关键词
    has_non_bid = any(kw in content_lower for kw in NON_BID_KEYWORDS)

    # 必须有投标上下文，且不能有过多非投标技术关键词
    if has_non_bid and not has_bid_context:
        return False

    return has_bid_context


def validate_skill_name(skill_name: str) -> bool:
    """验证 skill 名称是否为 bid-* 系列"""
    return skill_name.startswith('bid-')


# ============ Gotcha 注入 ============

def load_existing_gotchas(skill_path: Path) -> List[str]:
    """加载已有的 gotchas"""
    gotcha_file = skill_path / 'gotchas.md'
    if not gotcha_file.exists():
        return []

    with open(gotcha_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 提取 ## Gotchas 后的内容
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


def check_duplicate(new_gotcha: str, existing_gotchas: List[str]) -> bool:
    """检查是否重复（简单的相似度检查）"""
    new_title = new_gotcha.split('\n')[0].lower()

    for existing in existing_gotchas:
        existing_title = existing.split('\n')[0].lower()
        if new_title in existing_title or existing_title in new_title:
            return True

    return False


def inject_gotcha(
    skill_name: str,
    title: str,
    problem: str,
    solution: str,
    example: Optional[str] = None,
    skills_root: str = '~/.claude/skills'
) -> Dict[str, any]:
    """
    注入 gotcha 到指定 skill

    返回: {"success": bool, "message": str, "file": str}
    """

    # 验证 skill 名称
    if not validate_skill_name(skill_name):
        return {
            "success": False,
            "message": f"❌ 拒绝注入：{skill_name} 不是 bid-* skill",
            "file": None
        }

    # 验证内容属于投标业务
    full_content = f"{title} {problem} {solution} {example or ''}"
    if not validate_bid_scope(full_content):
        return {
            "success": False,
            "message": f"❌ 作用域错误：内容不属于投标业务领域",
            "file": None
        }

    # 定位 skill 目录
    skills_root = Path(skills_root).expanduser()
    skill_path = skills_root / skill_name

    if not skill_path.exists():
        return {
            "success": False,
            "message": f"❌ Skill 不存在：{skill_path}",
            "file": None
        }

    # 加载已有 gotchas
    existing_gotchas = load_existing_gotchas(skill_path)

    # 构建新 gotcha
    new_gotcha = f"### {title}\n\n"
    new_gotcha += f"**问题**：{problem}\n\n"
    new_gotcha += f"**解决**：{solution}\n\n"
    if example:
        new_gotcha += f"**示例**：\n{example}\n\n"
    new_gotcha += f"*（学习自实践，注入时间：{datetime.now().strftime('%Y-%m-%d')}）*\n\n"

    # 检查重复
    if check_duplicate(new_gotcha, existing_gotchas):
        return {
            "success": False,
            "message": f"⚠️ 类似经验已存在，跳过",
            "file": str(skill_path / 'gotchas.md')
        }

    # 写入或追加
    gotcha_file = skill_path / 'gotchas.md'

    if not gotcha_file.exists():
        # 创建新文件
        content = f"# {skill_name} - Gotchas\n\n"
        content += "这些是从实践中学到的反直觉知识和常见陷阱。\n\n"
        content += "## Gotchas\n\n"
        content += new_gotcha
    else:
        # 追加到现有文件
        with open(gotcha_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if '## Gotchas' not in content:
            content += "\n## Gotchas\n\n"

        content += new_gotcha

    with open(gotcha_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return {
        "success": True,
        "message": f"✅ 已注入到 {skill_name}/gotchas.md",
        "file": str(gotcha_file)
    }


# ============ CLI ============

def main():
    if len(sys.argv) < 5:
        print("用法: inject_gotcha.py <skill_name> <title> <problem> <solution> [example]")
        sys.exit(1)

    skill_name = sys.argv[1]
    title = sys.argv[2]
    problem = sys.argv[3]
    solution = sys.argv[4]
    example = sys.argv[5] if len(sys.argv) > 5 else None

    result = inject_gotcha(skill_name, title, problem, solution, example)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == '__main__':
    main()
