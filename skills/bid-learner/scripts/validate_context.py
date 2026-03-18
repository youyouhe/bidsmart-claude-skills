#!/usr/bin/env python3
"""
上下文验证脚本

验证当前对话是否在投标业务上下文中，决定是否允许学习
"""

import sys
import json
from typing import List, Dict


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


def validate_bid_context(conversation_text: str) -> Dict[str, any]:
    """
    验证当前对话是否在投标业务上下文中

    返回: {
        "is_valid": bool,
        "score": int,  # 0-3
        "reasons": List[str]
    }
    """
    conversation_lower = conversation_text.lower()
    reasons = []
    score = 0

    # 检查1：是否涉及投标文件
    has_bid_files = any(f in conversation_text for f in BID_FILES)
    if has_bid_files:
        score += 1
        matched = [f for f in BID_FILES if f in conversation_text]
        reasons.append(f"✅ 涉及投标文件：{', '.join(matched[:3])}")

    # 检查2：是否调用了 bid-* skills
    has_bid_skills = any(s in conversation_text for s in BID_SKILLS)
    if has_bid_skills:
        score += 1
        matched = [s for s in BID_SKILLS if s in conversation_text]
        reasons.append(f"✅ 调用了 bid skills：{', '.join(matched[:3])}")

    # 检查3：话题是否相关
    keyword_count = sum(1 for kw in BID_KEYWORDS if kw in conversation_text)
    if keyword_count >= 3:
        score += 1
        reasons.append(f"✅ 投标关键词出现 {keyword_count} 次")

    # 判断
    is_valid = score >= 2

    if not is_valid:
        reasons.append("❌ 不满足至少2项条件，拒绝学习")

    return {
        "is_valid": is_valid,
        "score": score,
        "reasons": reasons
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "is_valid": False,
            "score": 0,
            "reasons": ["❌ 未提供对话上下文"]
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    conversation_text = sys.argv[1]
    result = validate_bid_context(conversation_text)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["is_valid"] else 1)


if __name__ == '__main__':
    main()
