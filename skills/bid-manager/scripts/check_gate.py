#!/usr/bin/env python3
"""check_gate.py — 投标流水线阶段门禁的硬校验（bid-manager 强制入口检查）。

背景：风险审计门禁（bid-audit）是流程中第二个用户决策点，要求"全部裁决后方可进入
S13/S14"。历史上该门禁只有 prompt 层约束，曾被 agent 用一句"用户已授权先完成编写"
自行放行。本脚本把门禁固化为状态机硬校验：

  python3 check_gate.py check s13   # 进 S13 前必跑；未裁决 → 退出码 1，禁止进入
  python3 check_gate.py check s14   # 进 S14 前必跑；审计未裁决 / 占位符闭环不过 → 退出码 1
  python3 check_gate.py resolve-audit --note "用户已逐条裁决（见对话）"
                                    # 用户裁决完成后由 agent 调用，落 audit_decisions.status=resolved
  python3 check_gate.py status      # 查看当前门禁状态

状态载体：工作目录根 pipeline_progress.json 的 audit_decisions 字段：
  { "status": "pending" | "resolved", "resolved_at": "...", "note": "..." }
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROGRESS = "pipeline_progress.json"
SCRIPT_DIR = Path(__file__).resolve().parent


def load_progress(root: Path) -> dict:
    p = root / PROGRESS
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"🔴 {PROGRESS} 不是合法 JSON: {e}", file=sys.stderr)
        sys.exit(2)


def save_progress(root: Path, data: dict) -> None:
    (root / PROGRESS).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def audit_state(prog: dict) -> str:
    return (prog.get("audit_decisions") or {}).get("status", "pending")


def cmd_check(root: Path, args) -> int:
    prog = load_progress(root)
    stage = args.stage.lower()
    fails: list[str] = []

    # ── 门禁 1（S13/S14 共同）：风险审计必须已裁决 ──
    if audit_state(prog) != "resolved":
        fails.append(
            "风险审计门禁未裁决（audit_decisions.status != resolved）："
            "必须把 响应文件/决策清单.json 逐条呈现给用户、收到逐条裁决后，"
            "运行 check_gate.py resolve-audit 才能继续。不得以任何笼统授权"
            "（如『先完成编写』）代替逐条裁决。"
        )

    # ── 门禁 2（仅 S14）：S12 质检已执行 + 占位符闭环自洽 ──
    if stage == "s14":
        if not (root / "响应文件" / "核对报告.md").is_file():
            fails.append("S12 质检未执行（响应文件/核对报告.md 不存在），禁止直接生成 Word")
        reg = SCRIPT_DIR / "placeholder_registry.py"
        if (root / "placeholders.json").is_file() and reg.is_file():
            r = subprocess.run(
                [sys.executable, str(reg), "--root", str(root), "validate"],
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                fails.append(
                    "占位符闭环校验未通过（placeholder_registry.py validate 退出码非 0）："
                    "逐项修复后再进 S14。明细见上方 validate 输出。"
                )
                sys.stderr.write(r.stdout + r.stderr)

    if fails:
        print(f"🚫 GATE CHECK FAIL（{stage.upper()} 入口）:", file=sys.stderr)
        for f in fails:
            print(f"  🔴 {f}", file=sys.stderr)
        return 1
    print(f"✅ GATE CHECK PASS（{stage.upper()} 入口）")
    return 0


def cmd_resolve_audit(root: Path, args) -> int:
    prog = load_progress(root)
    decisions_file = root / "响应文件" / "决策清单.json"
    if not decisions_file.is_file():
        print("🔴 响应文件/决策清单.json 不存在——bid-audit 尚未执行，不能标记已裁决", file=sys.stderr)
        return 1
    prog["audit_decisions"] = {
        "status": "resolved",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "note": args.note or "",
    }
    save_progress(root, prog)
    print("[resolve-audit] audit_decisions.status = resolved")
    print("⚠️ 请确认：决策清单已逐条呈现给用户且收到逐条裁决；标『需修复』的条目必须合并进 S13 修复输入。")
    return 0


def cmd_status(root: Path, _args) -> int:
    prog = load_progress(root)
    out = {
        "audit_decisions": prog.get("audit_decisions") or {"status": "pending"},
        "current_stage": prog.get("current_stage"),
        "fix_rounds": prog.get("fix_rounds"),
        "has_decisions_file": (root / "响应文件" / "决策清单.json").is_file(),
        "has_assembly_report": (root / "响应文件" / "核对报告.md").is_file(),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="投标流水线阶段门禁硬校验")
    ap.add_argument("--root", default=".", help="工作目录根（默认 CWD）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="阶段入口检查（FAIL 退出码 1）")
    c.add_argument("stage", choices=["s13", "s14"])

    r = sub.add_parser("resolve-audit", help="用户逐条裁决后标记审计门禁通过")
    r.add_argument("--note", default="")

    sub.add_parser("status", help="查看门禁状态")

    args = ap.parse_args()
    root = Path(args.root).resolve()
    return {
        "check": cmd_check,
        "resolve-audit": cmd_resolve_audit,
        "status": cmd_status,
    }[args.cmd](root, args)


if __name__ == "__main__":
    sys.exit(main())
