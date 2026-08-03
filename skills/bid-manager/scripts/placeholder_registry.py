#!/usr/bin/env python3
"""placeholder_registry.py — 占位符对照表（placeholders.json）唯一权威读写工具。

契约背景：packages/bidsmart-skills/CLAUDE.md "Placeholder registry" 段。
本脚本把契约里的写入/校验规则固化为机器校验，替代各 skill 手写 jq/grep 自检：

  register   登记/更新一条 item（幂等 upsert，source_file 强制归一化为工作目录根相对路径）
  validate   闭环校验（表↔正文双向核对 + asset 存在性），发现问题退出码 1
  stats      输出按 type/status 分组的计数 JSON
  normalize  一次性迁移：把表内所有 source_file 归一化为根相对路径

路径约定（本脚本强制）：source_file 一律为**工作目录根相对路径**
（如 `响应文件/00-资格证明文件合集.md`、`项目文档/01-需求分析/S01-xxx.md`），
禁止裸文件名——历史上裸文件名导致 S9/S11/S12 各自临时拼接目录前缀，同一 bug 修三次。

用法：
  python3 placeholder_registry.py register --id business-license --type scan \
      --material-type business-license --source-file 00-资格证明文件合集.md
  python3 placeholder_registry.py validate            # 闭环校验，🔴 时退出码 1
  python3 placeholder_registry.py stats               # 计数 JSON
  python3 placeholder_registry.py normalize           # 迁移旧表路径
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

REGISTRY_NAME = "placeholders.json"
# 占位符可能出现的目录（相对工作目录根）
SEARCH_DIRS = ["响应文件", "项目文档"]
PLACEHOLDER_RE = re.compile(r"【此处插入:(截图|图表|扫描件):([A-Za-z0-9_-]+)】")
TYPE2CN = {"screenshot": "截图", "diagram": "图表", "scan": "扫描件"}


def find_registry(root: Path) -> Path:
    return root / REGISTRY_NAME


def load(root: Path) -> dict:
    p = find_registry(root)
    if not p.exists():
        return {"version": 1, "items": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"🔴 {REGISTRY_NAME} 不是合法 JSON: {e}", file=sys.stderr)
        sys.exit(2)
    data.setdefault("version", 1)
    data.setdefault("items", [])
    return data


def save(root: Path, data: dict) -> None:
    find_registry(root).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def normalize_source_file(root: Path, raw: str) -> tuple[str, list[str]]:
    """归一化为工作目录根相对路径；返回 (normalized, warnings)。"""
    warns: list[str] = []
    raw = raw.strip().lstrip("./")
    if not raw:
        return raw, ["source_file 为空"]
    # 1) 已是合法的根相对路径
    if (root / raw).is_file():
        return raw, warns
    # 2) 裸文件名 → 到已知目录里找
    base = os.path.basename(raw)
    for d in SEARCH_DIRS:
        cand = root / d / base
        if cand.is_file():
            warns.append(f"source_file 裸文件名已归一化: {raw} → {d}/{base}")
            return f"{d}/{base}", warns
    # 3) 递归搜（项目文档有子目录结构）
    for d in SEARCH_DIRS:
        dd = root / d
        if dd.is_dir():
            hits = sorted(p for p in dd.rglob(base) if p.is_file())
            if hits:
                rel = hits[0].relative_to(root).as_posix()
                warns.append(f"source_file 已归一化: {raw} → {rel}")
                return rel, warns
    warns.append(f"⚠️ source_file 不存在（保持原值）: {raw}")
    return raw, warns


def cmd_register(root: Path, args) -> int:
    data = load(root)
    src, warns = normalize_source_file(root, args.source_file)
    for w in warns:
        print(f"  [register] {w}", file=sys.stderr)
    for it in data["items"]:
        if it.get("id") == args.id:
            # 幂等 upsert：已存在则只更新允许漂移的字段，不动 status/asset（替换方所有）
            it["type"] = args.type
            it["source_file"] = src
            if args.material_type:
                it["material_type"] = args.material_type
            print(f"[register] upsert(更新) id={args.id} → {src}")
            save(root, data)
            return 0
    item = {
        "id": args.id,
        "type": args.type,
        "source_file": src,
        "status": "pending",
        "asset": None,
    }
    if args.material_type:
        item["material_type"] = args.material_type
    if args.system:
        item["system"] = args.system
    if args.function_point:
        item["function_point"] = args.function_point
    if args.label:
        item["label"] = args.label
    if args.title:
        item["title"] = args.title
    data["items"].append(item)
    save(root, data)
    print(f"[register] upsert(新增) id={args.id} type={args.type} → {src}")
    return 0


def iter_md_files(root: Path):
    for d in SEARCH_DIRS:
        dd = root / d
        if dd.is_dir():
            yield from sorted(dd.rglob("*.md"))


def cmd_mark_done(root: Path, args) -> int:
    data = load(root)
    for it in data["items"]:
        if it.get("id") == args.id:
            asset = args.asset.strip().lstrip("./")
            if not (root / asset).is_file():
                # asset 也允许相对 source_file 目录（替换方常写同目录文件名）
                cand = (root / it.get("source_file", "")).parent / asset
                if cand.is_file():
                    asset = cand.relative_to(root).as_posix()
                else:
                    print(f"🔴 asset 文件不存在: {args.asset}", file=sys.stderr)
                    return 1
            it["status"] = "done"
            it["asset"] = asset
            if args.mock:
                it["is_mock_pending_replacement"] = True
            save(root, data)
            print(f"[mark-done] id={args.id} asset={asset}" + ("（mock 待替换）" if args.mock else ""))
            return 0
    print(f"🔴 对照表中不存在 id: {args.id}", file=sys.stderr)
    return 1


def cmd_validate(root: Path, _args) -> int:
    data = load(root)
    items = data["items"]
    reds: list[str] = []
    yellows: list[str] = []

    # 0) 表内 id 唯一性
    seen: dict[str, int] = {}
    for it in items:
        seen[it.get("id", "?")] = seen.get(it.get("id", "?"), 0) + 1
    for iid, n in seen.items():
        if n > 1:
            reds.append(f"对照表 id 重复 ×{n}: {iid}")

    # 1) 表 → 正文：每个 item 的占位符在其 source_file 中存在且唯一；done 的 asset 存在
    for it in items:
        iid, typ, st = it.get("id"), it.get("type"), it.get("status")
        src, warns = normalize_source_file(root, it.get("source_file", ""))
        if src != it.get("source_file"):
            yellows.append(f"{iid}: source_file 未归一化（{it.get('source_file')} → {src}），运行 normalize 修复")
        f = root / src
        cn = TYPE2CN.get(typ, "")
        if not f.is_file():
            reds.append(f"{iid}: source_file 不存在: {src}")
        elif cn:
            n = len(re.findall(re.escape(f"【此处插入:{cn}:{iid}】"), f.read_text(encoding="utf-8")))
            if st == "pending" and n == 0:
                reds.append(f"{iid}: 表内 pending 但 {src} 中无对应占位符（表与正文漂移）")
            elif st == "done" and n > 0:
                yellows.append(f"{iid}: 已标 done 但 {src} 中占位符仍残留 ×{n}（标 done 前未替换正文？）")
            elif n > 1:
                yellows.append(f"{iid}: {src} 中同 id 占位符 ×{n}（应唯一；同文件多处引用需人工确认）")
        if st == "done":
            asset = it.get("asset")
            if not asset:
                yellows.append(f"{iid}: status=done 但 asset 为空")
            elif not (root / asset).is_file() and not (f.parent / asset).is_file():
                reds.append(f"{iid}: asset 文件不存在: {asset}")

    # 2) 正文 → 表：每个正文占位符的 id 都必须在表里（捕获漏登记）
    known = {it.get("id") for it in items}
    for md in iter_md_files(root):
        for m in PLACEHOLDER_RE.finditer(md.read_text(encoding="utf-8")):
            if m.group(2) not in known:
                reds.append(f"正文占位符未登记: 【此处插入:{m.group(1)}:{m.group(2)}】 in {md.relative_to(root)}")

    # 3) 汇总
    pending = [it["id"] for it in items if it.get("status") == "pending"]
    report = {
        "total_items": len(items),
        "pending": len(pending),
        "done": sum(1 for it in items if it.get("status") == "done"),
        "red": reds,
        "yellow": yellows,
        "pending_ids": pending,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if reds:
        print(f"\n🔴 闭环校验失败（{len(reds)} 项）", file=sys.stderr)
        return 1
    if yellows:
        print(f"\n🟡 校验通过（{len(yellows)} 项警告）", file=sys.stderr)
    else:
        print("\n✅ 闭环校验通过", file=sys.stderr)
    return 0


def cmd_stats(root: Path, _args) -> int:
    data = load(root)
    out: dict[str, dict[str, int]] = {}
    for it in data["items"]:
        t = out.setdefault(it.get("type", "?"), {"pending": 0, "done": 0, "other": 0})
        t[it.get("status", "other") if it.get("status") in ("pending", "done") else "other"] += 1
    print(json.dumps({"total": len(data["items"]), "by_type": out}, ensure_ascii=False, indent=2))
    return 0


def cmd_normalize(root: Path, _args) -> int:
    data = load(root)
    changed = 0
    for it in data["items"]:
        src, _ = normalize_source_file(root, it.get("source_file", ""))
        if src != it.get("source_file"):
            print(f"  {it.get('id')}: {it.get('source_file')} → {src}")
            it["source_file"] = src
            changed += 1
    save(root, data)
    print(f"[normalize] {changed}/{len(data['items'])} 条 source_file 已归一化")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="占位符对照表权威读写工具")
    ap.add_argument("--root", default=".", help="工作目录根（默认 CWD）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("register", help="幂等 upsert 一条 item")
    r.add_argument("--id", required=True)
    r.add_argument("--type", required=True, choices=list(TYPE2CN))
    r.add_argument("--source-file", required=True)
    r.add_argument("--material-type")
    r.add_argument("--system")
    r.add_argument("--function-point")
    r.add_argument("--label")
    r.add_argument("--title")

    sub.add_parser("validate", help="闭环校验（🔴 退出码 1）")
    sub.add_parser("stats", help="计数 JSON")
    sub.add_parser("normalize", help="迁移旧表 source_file 为根相对路径")

    m = sub.add_parser("mark-done", help="替换方回填 status=done + asset")
    m.add_argument("--id", required=True)
    m.add_argument("--asset", required=True, help="产物路径（根相对或相对 source_file 目录）")
    m.add_argument("--mock", action="store_true", help="标记 is_mock_pending_replacement")

    args = ap.parse_args()
    root = Path(args.root).resolve()
    return {
        "register": cmd_register,
        "validate": cmd_validate,
        "stats": cmd_stats,
        "normalize": cmd_normalize,
        "mark-done": cmd_mark_done,
    }[args.cmd](root, args)


if __name__ == "__main__":
    sys.exit(main())
