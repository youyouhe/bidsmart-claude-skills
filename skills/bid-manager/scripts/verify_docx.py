#!/usr/bin/env python3
"""verify_docx.py — S14 最终 Word 产物的机器回验（生成后必跑）。

背景：历史事故——S14 走降级路径（DocScan 在线转换合并单文件）产出 39KB docx，
没有任何一步验证产物：14 张已下载扫描件未嵌入、占位符可能残留、三册结构丢失，
流程却自报 SUCCESS。本脚本把"产物 sanity check"固化：

  python3 verify_docx.py <docx路径> [--source-glob "响应文件/*.md"]

检查项：
  1. docx 可解包、word/document.xml 存在（格式合法）
  2. 占位符残留：document.xml 中检索 【此处插入 / 【待人工补充 → 🔴
  3. 图片嵌入：word/media/ 文件数 vs 源 md 中的图片引用数（docx 图片数 < md 引用数 → 🔴）
  4. 文本量比对：docx 提取文本字符数 vs 源 md 总字符数（低于 50% → 🟡 疑似内容丢失）
  5. 体量下限：提取文本 < 2000 字符 → 🟡（整本标书不应只有几千字）

退出码：🔴 > 0 → 1；仅 🟡 → 0（警告不阻塞，但必须写进最终汇总）。
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

PLACEHOLDER_RESIDUE = ["【此处插入", "【待人工补充", "【待补充】"]
IMG_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
TAG_RE = re.compile(r"<[^>]+>")


def extract_docx_text(z: zipfile.ZipFile) -> str:
    parts = []
    for name in z.namelist():
        if name.startswith("word/") and name.endswith(".xml") and (
            name == "word/document.xml" or name.startswith("word/header") or name.startswith("word/footer")
        ):
            xml = z.read(name).decode("utf-8", errors="ignore")
            parts.append(TAG_RE.sub("", xml))
    return "".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description="S14 最终 Word 产物回验")
    ap.add_argument("docx", help="生成的 .docx 路径")
    ap.add_argument("--source-glob", default="响应文件/*.md", help="源 md 文件 glob（相对 --root）")
    ap.add_argument("--root", default=".", help="工作目录根（默认 CWD）")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    docx = (root / args.docx).resolve() if not Path(args.docx).is_absolute() else Path(args.docx)

    reds: list[str] = []
    yellows: list[str] = []

    # 1. 格式合法
    if not docx.is_file():
        print(f"🔴 docx 不存在: {docx}", file=sys.stderr)
        return 1
    try:
        z = zipfile.ZipFile(docx)
        names = z.namelist()
        if "word/document.xml" not in names:
            reds.append("docx 内无 word/document.xml（非法 docx）")
    except zipfile.BadZipFile:
        print(f"🔴 不是合法 docx（zip 解包失败）: {docx}", file=sys.stderr)
        return 1

    text = extract_docx_text(z) if not reds else ""
    media = [n for n in z.namelist() if n.startswith("word/media/")]

    # 2. 占位符残留
    for ph in PLACEHOLDER_RESIDUE:
        n = text.count(ph)
        if n:
            reds.append(f"占位符残留: {ph} ×{n}")

    # 3/4. 与源 md 比对。图片数按 basename 去重——同一图片在多 md 或同 md 多处引用
    # 都只算 1 张（Word media 也只存 1 份），否则引用次数 > media 文件数必然误报红。
    md_files = sorted(root.glob(args.source_glob))
    md_img_set = set()
    md_chars = 0
    for md in md_files:
        content = md.read_text(encoding="utf-8", errors="ignore")
        md_chars += len(content)
        for ref in IMG_REF_RE.findall(content):
            md_img_set.add(ref.split("/")[-1])
    md_imgs = len(md_img_set)

    if md_files:
        if md_imgs > 0 and len(media) < md_imgs:
            reds.append(
                f"图片未全部嵌入: 源 md 引用 {md_imgs} 张（去重后唯一），docx word/media/ 仅 {len(media)} 个文件"
                "（疑似走了不嵌图的降级转换路径）。若此 docx 是多册中的单本，须用 --source-glob 指定"
                "本册源 md 重校验——用全目录比对单册会因其他册的图算进分母而误报"
            )
        ratio = (len(text) / md_chars) if md_chars else 0
        if ratio < 0.5:
            yellows.append(
                f"文本量偏低: docx 提取 {len(text)} 字符 vs 源 md {md_chars} 字符（{ratio:.0%}），疑似内容丢失"
            )
    else:
        yellows.append(f"未找到源 md（glob: {args.source_glob}），跳过图片/文本比对")

    # 5. 体量下限
    if text and len(text) < 2000:
        yellows.append(f"docx 提取文本仅 {len(text)} 字符，整本标书不应只有几千字")

    report = {
        "docx": str(docx.relative_to(root)) if docx.is_relative_to(root) else str(docx),
        "size_kb": round(docx.stat().st_size / 1024, 1),
        "text_chars": len(text),
        "media_files": len(media),
        "md_image_refs": md_imgs,
        "md_chars": md_chars,
        "red": reds,
        "yellow": yellows,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if reds:
        print(f"\n🔴 产物回验失败（{len(reds)} 项）——不得宣称 S14 完成，先回退修复转换路径", file=sys.stderr)
        return 1
    if yellows:
        print(f"\n🟡 产物回验通过（{len(yellows)} 项警告，须写入最终汇总）", file=sys.stderr)
    else:
        print("\n✅ 产物回验通过", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
