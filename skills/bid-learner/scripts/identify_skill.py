#!/usr/bin/env python3
"""
Skill 识别脚本

根据问题描述和上下文，识别应该将 gotcha 注入到哪个 bid-* skill。

调用方式：
  python3 identify_skill.py --problem "评分标准提取错误"
  python3 identify_skill.py --problem "评分标准提取错误" --context "分析报告中遗漏了..."
"""

import argparse
import json
import sys
from typing import Dict, List

# Skill 映射规则
SKILL_PATTERNS = {
    'bid-analysis': [
        '分析报告', '提取评分', '识别要求', '解析招标文件', '理解需求',
        '结构化输出', '遗漏字段', '评分标准', '资格条件'
    ],
    'bid-verification': [
        '核实', '校验', '交叉验证', '幻觉', '数据错误', '分值验算',
        '原文对比', '差异检查'
    ],
    'bid-commercial-proposal': [
        '商务标', '报价函', '资格证明', '营业执照', '业绩材料',
        '声明函', '授权书', '附件编写', '商务文件'
    ],
    'bid-tech-proposal': [
        '技术标', '技术方案', '实施方案', '培训方案', '服务方案',
        '技术响应', '章节设计', '技术文件'
    ],
    'bid-requirements': [
        '需求分析', '需求规格', '需求细化', '功能需求', '非功能需求',
        '用户故事', '需求文档'
    ],
    'bid-assembly': [
        '质检', '核对', '完整性检查', '一致性', '占位符残留',
        '装订指南', '目录生成', '自查自纠'
    ],
    'bid-manager': [
        '流程编排', '断点续跑', '阶段管理', 'pipeline', '自动修复',
        '进度管理', '一键投标'
    ],
    'bid-mermaid-diagrams': [
        '图表', 'mermaid', '架构图', '流程图', '时序图',
        '图表占位符', '渲染PNG'
    ],
    'bid-material-search': [
        '资料检索', '扫描件', '证书查找', '营业执照', '资质证书',
        '检索服务', 'MaterialHub'
    ],
    'bid-md2doc': [
        'Word生成', 'docx转换', 'markdown转换', '文档格式',
        '样式设置', 'generate_docx'
    ]
}


def identify_target_skill(problem: str, context: str = '') -> Dict:
    """识别问题应归属的 skill"""
    full_text = f"{problem} {context}".lower()

    scores = {}
    matched_patterns = {}

    for skill, patterns in SKILL_PATTERNS.items():
        score = 0
        matches = []
        for pattern in patterns:
            if pattern in full_text:
                score += 1
                matches.append(pattern)
        if score > 0:
            scores[skill] = score
            matched_patterns[skill] = matches

    if not scores:
        return {
            "skill": None,
            "confidence": 0.0,
            "matched_patterns": [],
            "message": "❌ 无法识别目标 skill，请手动指定"
        }

    best_skill = max(scores, key=scores.get)
    max_score = scores[best_skill]
    total_patterns = len(SKILL_PATTERNS[best_skill])
    confidence = max_score / total_patterns

    return {
        "skill": best_skill,
        "confidence": round(confidence, 2),
        "matched_patterns": matched_patterns[best_skill],
        "message": f"✅ 识别为 {best_skill}（置信度 {confidence:.0%}）"
    }


def parse_args():
    parser = argparse.ArgumentParser(description='识别问题归属的 bid skill')
    parser.add_argument('--problem', required=True, help='问题描述')
    parser.add_argument('--context', default='', help='额外上下文（可选）')
    return parser.parse_args()


def main():
    args = parse_args()

    result = identify_target_skill(args.problem, args.context)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    sys.exit(0 if result["skill"] else 1)


if __name__ == '__main__':
    main()
