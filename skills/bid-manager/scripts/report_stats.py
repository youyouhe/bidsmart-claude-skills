#!/usr/bin/env python3
"""report_stats.py — 分析报告/核实报告的权威计数工具（禁止 LLM 手写统计数字）。

历史事故：S1 分析报告"编写归属统计"手写 20/7（实际表格 19/9）；S2 核实报告摘要
手写 31 项（明细实际 63 项）。根因都是 LLM 凭印象/fragile grep 手写统计段落。
本脚本提供两条权威路径：

  tables <file.docx>            权威表格行数/★/▲ 计数（替代 grep -c 与目测数行）
  check-report <report.md>      校验报告末尾统计 JSON 块与正文实际计数一致

统计 JSON 块格式（必须是报告中最后一个 ```json 围栏块，且含 "_stats": true）：

  分析报告 分析报告.md:
    <!-- report-stats -->
    ```json
    { "_stats": true, "kind": "analysis",
      "business_files": 19, "tech_files": 9, "total_files": 28 }
    ```
    business_files/tech_files = "投标文件组成"表中 `| 商务标 |` / `| 技术标 |` 的行数
    （由本脚本计数填入，禁止手写）

  核实报告 核实报告.md:
    <!-- report-stats -->
    ```json
    { "_stats": true, "kind": "verification",
      "correct": 50, "wrong": 3, "suspect": 2, "notfound": 8, "total_items": 63 }
    ```
    correct/wrong/suspect/notfound = "逐项核实明细"表中各行状态标记数
    （✅/❌/⚠️/🔍，由本脚本计数填入，禁止手写）
"""
import argparse
import glob as globmod
import json
import re
import sys
from pathlib import Path

STATS_MARKER = "<!-- report-stats -->"


def cmd_tables(args) -> int:
    """对 docx 直接读表格结构（python-docx），输出每个表的行/列/★/▲ 权威计数。"""
    try:
        import docx
    except ImportError:
        print("🔴 需要 python-docx（pip install python-docx）", file=sys.stderr)
        return 2
    doc = docx.Document(args.docx)
    out = []
    for i, t in enumerate(doc.tables):
        rows = len(t.rows)
        cols = len(t.columns) if rows else 0
        stars = triangles = 0
        header = ""
        for r_i, row in enumerate(t.rows):
            for cell in row.cells:
                stars += cell.text.count("★")
                triangles += cell.text.count("▲")
            if r_i == 0:
                header = " | ".join(c.text.strip().replace("\n", " ")[:20] for c in row.cells)[:80]
        out.append({"table": i, "rows": rows, "cols": cols, "star": stars,
                    "triangle": triangles, "header": header})
    print(json.dumps({"file": args.docx, "tables": out,
                      "total_tables": len(out)}, ensure_ascii=False, indent=2))
    return 0


def find_stats_block(text: str) -> dict | None:
    """取最后一个 <!-- report-stats --> 后的 ```json 块。"""
    idx = text.rfind(STATS_MARKER)
    if idx < 0:
        return None
    m = re.search(r"```json\s*(\{.*?\})\s*```", text[idx:], re.S)
    if not m:
        return None
    try:
        block = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    return block if block.get("_stats") else None


def body_without_stats(text: str) -> str:
    idx = text.rfind(STATS_MARKER)
    return text[:idx] if idx >= 0 else text


def count_analysis(body: str) -> dict:
    return {
        "business_files": len(re.findall(r"\|\s*商务标\s*\|", body)),
        "tech_files": len(re.findall(r"\|\s*技术标\s*\|", body)),
    }


def count_verification(body: str) -> dict:
    # 明细表格单元格中的状态标记：| ✅ | 或 | ✅正确 |
    def n(mark: str) -> int:
        return len(re.findall(r"\|\s*" + re.escape(mark), body))
    return {"correct": n("✅"), "wrong": n("❌"), "suspect": n("⚠️"), "notfound": n("🔍")}


def cmd_check_report(args) -> int:
    p = Path(args.report)
    if not p.is_file():
        print(f"🔴 报告不存在: {p}", file=sys.stderr)
        return 2
    text = p.read_text(encoding="utf-8")
    block = find_stats_block(text)
    if block is None:
        print(f"🔴 缺少统计 JSON 块（{STATS_MARKER} + ```json，含 \"_stats\": true）——"
              "统计数字必须由脚本计数填入，禁止手写", file=sys.stderr)
        return 1
    body = body_without_stats(text)
    kind = block.get("kind")
    fails: list[str] = []

    if kind == "analysis":
        actual = count_analysis(body)
        for k, v in actual.items():
            if block.get(k) is not None and block[k] != v:
                fails.append(f"{k}: 统计块={block[k]} vs 正文实际={v}")
        if block.get("total_files") is not None:
            s = actual["business_files"] + actual["tech_files"]
            if block["total_files"] != s:
                fails.append(f"total_files: 统计块={block['total_files']} vs 商务+技术={s}")
    elif kind == "verification":
        actual = count_verification(body)
        for k, v in actual.items():
            if block.get(k) is not None and block[k] != v:
                fails.append(f"{k}: 统计块={block[k]} vs 明细实际={v}")
        if block.get("total_items") is not None:
            s = sum(actual.values())
            if block["total_items"] != s:
                fails.append(f"total_items: 统计块={block['total_items']} vs 四类状态之和={s}")
    else:
        fails.append(f"未知 kind: {kind!r}（应 analysis|verification）")

    report = {"report": str(p), "kind": kind, "stats_block": block,
              "actual": actual if kind in ("analysis", "verification") else None,
              "mismatches": fails}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if fails:
        print(f"\n🔴 统计块与正文不一致（{len(fails)} 项）——用 actual 值修正统计块", file=sys.stderr)
        return 1
    print("\n✅ 统计块与正文一致", file=sys.stderr)
    return 0


def cmd_fill(args) -> int:
    """计算正文实际计数并输出应填入的统计 JSON 块（agent 粘贴到报告末尾）。"""
    p = Path(args.report)
    text = p.read_text(encoding="utf-8")
    body = body_without_stats(text)
    if args.kind == "analysis":
        a = count_analysis(body)
        block = {"_stats": True, "kind": "analysis",
                 **a, "total_files": a["business_files"] + a["tech_files"]}
    else:
        v = count_verification(body)
        block = {"_stats": True, "kind": "verification",
                 **v, "total_items": sum(v.values())}
    print(f"{STATS_MARKER}\n```json\n{json.dumps(block, ensure_ascii=False, indent=2)}\n```")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="报告权威计数工具")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("tables", help="docx 表格权威行数/★/▲ 计数")
    t.add_argument("docx")

    c = sub.add_parser("check-report", help="校验统计块与正文一致（不一致退出码 1）")
    c.add_argument("report")

    f = sub.add_parser("fill", help="计算正文计数并输出应填入的统计块")
    f.add_argument("report")
    f.add_argument("--kind", required=True, choices=["analysis", "verification"])

    args = ap.parse_args()
    return {"tables": cmd_tables, "check-report": cmd_check_report, "fill": cmd_fill}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
