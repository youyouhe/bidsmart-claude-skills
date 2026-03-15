#!/usr/bin/env python3
"""
BigModel OCR - 智谱 OCR API 客户端

对 PDF 页面和图片文件进行文字识别，支持中英文混排、手写体、印刷体。
内置内容级缓存，避免重复 API 调用。

环境变量:
    BIGMODEL_API_KEY: 智谱 API 密钥（必需）

Usage:
    # OCR PDF 指定页面
    python bigmodel_ocr.py document.pdf --pages 1-3 --output result.json

    # OCR 单张图片
    python bigmodel_ocr.py cert.jpg --output result.json

    # 批量处理多个文件
    python bigmodel_ocr.py doc.pdf cert.jpg --pages 1-3 --output result.json
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import Optional

import requests

BIGMODEL_API_URL = "https://open.bigmodel.cn/api/paas/v4/files/ocr"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}
PDF_EXTENSIONS = {".pdf"}


class BigModelOCR:
    """Client for the BigModel (智谱) OCR API with content-based caching."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: str = ".ocr_cache",
        tool_type: str = "hand_write",
        language_type: str = "CHN_ENG",
        timeout: int = 120,
    ):
        self.api_key = api_key or os.getenv("BIGMODEL_API_KEY", "")
        if not self.api_key:
            print("[BigModel OCR] WARNING: BIGMODEL_API_KEY not set", file=sys.stderr)

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.tool_type = tool_type
        self.language_type = language_type
        self.timeout = timeout

    def ocr_image_bytes(self, image_bytes: bytes, filename: str = "image.png", page: int = 1) -> dict:
        """OCR image bytes. Returns dict with text, tokens, has_table, cached."""
        # Check cache
        content_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
        cache_key = f"img_{content_hash}"
        cached_text = self._get_cached(cache_key)
        if cached_text is not None:
            tokens = self._estimate_tokens(cached_text)
            has_table = self._detect_table(cached_text)
            return {"page": page, "text": cached_text, "tokens": tokens, "has_table": has_table, "cached": True}

        # Call API
        text = self._call_api(image_bytes, filename)
        if text:
            self._set_cached(cache_key, text)

        tokens = self._estimate_tokens(text or "")
        has_table = self._detect_table(text or "")
        return {"page": page, "text": text or "", "tokens": tokens, "has_table": has_table, "cached": False}

    def ocr_image_file(self, image_path: str) -> dict:
        """OCR an image file. Returns dict with text, tokens, has_table, cached."""
        path = Path(image_path)
        if not path.exists():
            print(f"[BigModel OCR] File not found: {image_path}", file=sys.stderr)
            return {"page": 1, "text": "", "tokens": 0, "has_table": False, "cached": False}

        with open(path, "rb") as f:
            image_bytes = f.read()

        return self.ocr_image_bytes(image_bytes, filename=path.name, page=1)

    def ocr_pdf_page(self, pdf_path: str, page_number: int, dpi: int = 300) -> dict:
        """OCR a single PDF page. Renders to image at given DPI, then calls API."""
        # Check cache (based on PDF content + page number)
        cache_key = self._pdf_cache_key(pdf_path, page_number)
        cached_text = self._get_cached(cache_key)
        if cached_text is not None:
            tokens = self._estimate_tokens(cached_text)
            has_table = self._detect_table(cached_text)
            return {"page": page_number, "text": cached_text, "tokens": tokens, "has_table": has_table, "cached": True}

        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("[BigModel OCR] PyMuPDF not installed. Run: pip install PyMuPDF", file=sys.stderr)
            return {"page": page_number, "text": "", "tokens": 0, "has_table": False, "cached": False}

        try:
            doc = fitz.open(pdf_path)
            if page_number < 1 or page_number > len(doc):
                print(f"[BigModel OCR] Page {page_number} out of range (1-{len(doc)})", file=sys.stderr)
                doc.close()
                return {"page": page_number, "text": "", "tokens": 0, "has_table": False, "cached": False}

            page = doc.load_page(page_number - 1)
            pix = page.get_pixmap(dpi=dpi)
            image_bytes = pix.tobytes("png")
            doc.close()
        except Exception as e:
            print(f"[BigModel OCR] PDF render error page {page_number}: {e}", file=sys.stderr)
            return {"page": page_number, "text": "", "tokens": 0, "has_table": False, "cached": False}

        # Call API
        text = self._call_api(image_bytes, f"page_{page_number}.png")
        if text:
            self._set_cached(cache_key, text)

        tokens = self._estimate_tokens(text or "")
        has_table = self._detect_table(text or "")
        return {"page": page_number, "text": text or "", "tokens": tokens, "has_table": has_table, "cached": False}

    # ------------------------------------------------------------------
    # BigModel API call
    # ------------------------------------------------------------------

    def _call_api(self, image_bytes: bytes, filename: str) -> Optional[str]:
        """Call BigModel OCR API. Returns extracted text or None."""
        if not self.api_key:
            print("[BigModel OCR] API key not configured", file=sys.stderr)
            return None

        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = [("file", (filename, image_bytes, "image/png"))]
        data = {
            "tool_type": self.tool_type,
            "language_type": self.language_type,
            "probability": "false",
        }

        try:
            resp = requests.post(
                BIGMODEL_API_URL,
                headers=headers,
                files=files,
                data=data,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout:
            print(f"[BigModel OCR] Timeout for {filename}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"[BigModel OCR] Request error for {filename}: {e}", file=sys.stderr)
            return None

        if resp.status_code != 200:
            print(f"[BigModel OCR] HTTP {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            return None

        result = resp.json()

        # Check success: status=="succeeded" or code==200 or has "data"
        is_success = (
            result.get("status") == "succeeded"
            or result.get("code") == 200
            or "data" in result
        )

        if not is_success:
            error = result.get("message", result.get("msg", "Unknown error"))
            print(f"[BigModel OCR] API error for {filename}: {error}", file=sys.stderr)
            return None

        # Parse text from response (multiple possible formats)
        text = ""

        # Format 1: words_result array
        words_result = result.get("words_result")
        if isinstance(words_result, list) and words_result:
            text = "\n".join(item.get("words", "") for item in words_result if item.get("words"))

        # Format 2: data.content / data.text / data.markdown
        if not text:
            data_obj = result.get("data") or result.get("result") or {}
            if isinstance(data_obj, dict):
                text = data_obj.get("content", "") or data_obj.get("text", "") or data_obj.get("markdown", "")
            elif isinstance(data_obj, str):
                text = data_obj

        if text:
            print(f"[BigModel OCR] Success for {filename}: {len(text)} chars", file=sys.stderr)
        else:
            print(f"[BigModel OCR] Empty result for {filename}", file=sys.stderr)

        return text if text else None

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def _pdf_cache_key(self, pdf_path: str, page_number: int) -> str:
        """Generate cache key from PDF content + page number."""
        stat = os.stat(pdf_path)
        with open(pdf_path, "rb") as f:
            head = f.read(8192)
        content_hash = hashlib.sha256(head).hexdigest()[:16]
        return f"pdf_{stat.st_size}_{content_hash}_p{page_number}"

    def _get_cached(self, key: str) -> Optional[str]:
        cache_file = self.cache_dir / f"{key}.txt"
        if cache_file.exists():
            return cache_file.read_text(encoding="utf-8")
        return None

    def _set_cached(self, key: str, text: str):
        cache_file = self.cache_dir / f"{key}.txt"
        cache_file.write_text(text, encoding="utf-8")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count (Chinese-aware)."""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return (chinese_chars // 2) + (other_chars // 4)

    @staticmethod
    def _detect_table(text: str) -> bool:
        """Detect if text likely contains a table."""
        return bool(text and "|" in text and "---" in text)


def parse_page_range(spec: str, total: int) -> list:
    """Parse page range like '1-3' or '1,3,5-8' into sorted list of page numbers."""
    pages = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            start = max(1, int(start))
            end = min(total, int(end))
            pages.extend(range(start, end + 1))
        else:
            p = int(part)
            if 1 <= p <= total:
                pages.append(p)
    return sorted(set(pages))


def get_pdf_page_count(pdf_path: str) -> int:
    """Get total page count of a PDF."""
    import fitz
    doc = fitz.open(pdf_path)
    count = len(doc)
    doc.close()
    return count


def process_file(client: BigModelOCR, file_path: str, pages_spec: str, dpi: int) -> dict:
    """Process a single file (PDF or image). Returns result dict."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in PDF_EXTENSIONS:
        total = get_pdf_page_count(file_path)
        if pages_spec:
            page_list = parse_page_range(pages_spec, total)
        else:
            # Default: first 3 pages
            page_list = list(range(1, min(4, total + 1)))

        pages = []
        for pn in page_list:
            print(f"[BigModel OCR] {path.name} page {pn}/{page_list[-1]}...", file=sys.stderr)
            result = client.ocr_pdf_page(file_path, pn, dpi=dpi)
            pages.append(result)

        return {"source": path.name, "type": "pdf", "total_pages": total, "pages": pages}

    elif ext in IMAGE_EXTENSIONS:
        print(f"[BigModel OCR] {path.name}...", file=sys.stderr)
        result = client.ocr_image_file(file_path)
        return {"source": path.name, "type": "image", "pages": [result]}

    else:
        print(f"[BigModel OCR] Unsupported file type: {ext}", file=sys.stderr)
        return {"source": path.name, "type": "unknown", "error": f"Unsupported: {ext}", "pages": []}


def main():
    parser = argparse.ArgumentParser(
        description="BigModel (智谱) OCR - 对 PDF 页面和图片进行文字识别",
        epilog="Example: python bigmodel_ocr.py doc.pdf --pages 1-3 --output result.json",
    )
    parser.add_argument("files", nargs="+", help="PDF 或图片文件路径（支持多个）")
    parser.add_argument("--pages", default="", help="PDF 页码范围，如 '1-3' 或 '1,3,5-8'（默认前3页）")
    parser.add_argument("--output", "-o", help="输出 JSON 文件路径（不指定则输出到 stdout）")
    parser.add_argument("--cache-dir", default=".ocr_cache", help="缓存目录（默认 .ocr_cache）")
    parser.add_argument("--dpi", type=int, default=300, help="PDF 渲染 DPI（默认 300）")
    parser.add_argument("--tool-type", default="hand_write",
                        choices=["hand_write", "ocr"],
                        help="OCR 模式: hand_write=手写+印刷混合（默认）, ocr=纯印刷体")
    args = parser.parse_args()

    api_key = os.getenv("BIGMODEL_API_KEY", "")
    if not api_key:
        print("ERROR: BIGMODEL_API_KEY environment variable not set.", file=sys.stderr)
        print("Get your API key at https://open.bigmodel.cn/", file=sys.stderr)
        sys.exit(1)

    # Validate files exist
    for fp in args.files:
        if not Path(fp).exists():
            print(f"ERROR: File not found: {fp}", file=sys.stderr)
            sys.exit(1)

    client = BigModelOCR(
        api_key=api_key,
        cache_dir=args.cache_dir,
        tool_type=args.tool_type,
    )

    results = []
    for fp in args.files:
        result = process_file(client, fp, args.pages, args.dpi)
        results.append(result)

    # Build summary
    total_pages = sum(len(r["pages"]) for r in results)
    success_pages = sum(1 for r in results for p in r["pages"] if p.get("text"))
    total_tokens = sum(p.get("tokens", 0) for r in results for p in r["pages"])

    output = {
        "results": results,
        "summary": {
            "total_files": len(results),
            "total_pages": total_pages,
            "success_pages": success_pages,
            "failed_pages": total_pages - success_pages,
            "total_tokens": total_tokens,
        },
    }

    output_json = json.dumps(output, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
