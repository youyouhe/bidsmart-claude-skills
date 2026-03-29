#!/usr/bin/env python3
"""
上下文验证脚本

验证当前对话是否在投标业务上下文中，决定是否允许学习。

调用方式：
  python3 validate_context.py --text "对话文本内容..."
"""

import argparse
import json
import sys
from typing import Dict, List


BID_FILES = [
    '招标文件', '磋商文件', '采购文件', '分析报告.md', '响应文件/',
    '核对报告.md', '核实报告.md', 'pipeline_progress.json'
]

BID_SKILLS = [
    'bid-analysis', 'bid-verification', 'bid-commercial-proposal',
    'bid-tech-proposal', 'bid-assembly', 'bid-manager', 'bid-requirements',
    'bid-mermaid-diagrams', 'bid-material-search', 'bid-md2doc'
]

BID_KEYWORDS = [
    '投标', '招标', '标书', '响应文件', '技术标', '商务标',
    '评分', '资格', '报价', '磋商', '采购', '供应商', '附件'
]


def validate_bid_context(conversation_text: str) -> Dict:
    """验证当前对话是否在投标业务上下文中"""
    reasons = []
    score = 0

    # 检查1：是否涉及投标文件
    matched_files = [f for f in BID_FILES if f in conversation_text]
    if matched_files:
        score += 1
        reasons.append(f"✅ 涉及投标文件：{', '.join(matched_files[:3])}")

    # 检查2：是否调用了 bid-* skills
    matched_skills = [s for s in BID_SKILLS if s in conversation_text]
    if matched_skills:
        score += 1
        reasons.append(f"✅ 调用了 bid skills：{', '.join(matched_skills[:3])}")

    # 检查3：话题是否相关
    keyword_count = sum(1 for kw in BID_KEYWORDS if kw in conversation_text)
    if keyword_count >= 3:
        score += 1
        reasons.append(f"✅ 投标关键词出现 {keyword_count} 次")

    is_valid = score >= 2
    if not is_valid:
        reasons.append("❌ 不满足至少2项条件，拒绝学习")

    return {
        "is_valid": is_valid,
        "score": score,
        "reasons": reasons
    }


def parse_args():
    parser = argparse.ArgumentParser(description='验证投标业务上下文')
    parser.add_argument('--text', required=True, help='对话上下文文本')
    return parser.parse_args()


def main():
    args = parse_args()

    result = validate_bid_context(args.text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["is_valid"] else 1)


if __name__ == '__main__':
    main()
