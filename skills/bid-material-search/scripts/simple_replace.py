"""简化的占位符替换 - 让Claude Code做智能判断

架构：
1. 从MaterialHub获取所有材料列表
2. Claude Code查看列表，判断最佳匹配
3. 通过API下载和提取图片
"""

import os
import re
import httpx
from pathlib import Path
from typing import List, Dict, Optional

from config import API_BASE, API_TOKEN
import watermark


def _headers() -> dict:
    """构建请求头"""
    h = {"Content-Type": "application/json"}
    if API_TOKEN:
        h["Authorization"] = f"Bearer {API_TOKEN}"
    return h


async def get_all_materials(limit: int = 100) -> List[Dict]:
    """获取MaterialHub中的所有材料列表

    Returns:
        材料列表，每个包含：id, title, doc_type, status等
    """
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30) as client:
        resp = await client.get("/api/v2/documents/", params={"limit": limit}, headers=_headers())
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])


async def get_material_detail(material_id: int) -> Optional[Dict]:
    """获取材料详情

    Returns:
        材料详情，包含files等信息
    """
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30) as client:
        resp = await client.get(f"/api/v2/documents/{material_id}", headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def download_image(url: str, output_path: str) -> bool:
    """下载图片"""
    try:
        if url.startswith("/"):
            url = f"{API_BASE}{url}"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url, headers=_headers())
            resp.raise_for_status()

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(resp.content)

            return True
    except Exception as e:
        print(f"下载图片失败: {e}")
        return False


async def extract_and_insert_material(
    material_id: int,
    placeholder: str,
    target_file: str,
    output_dir: str,
    project_name: str = ""
) -> Dict:
    """提取材料图片并插入到文件

    Args:
        material_id: MaterialHub材料ID
        placeholder: 占位符文本
        target_file: 目标Markdown文件
        output_dir: 图片输出目录
        project_name: 项目名称（用于水印）

    Returns:
        操作结果
    """
    # 1. 获取材料详情
    detail = await get_material_detail(material_id)
    if not detail:
        return {"success": False, "message": "获取材料详情失败"}

    material_title = detail.get("title", f"material_{material_id}")

    # 2. 找到图片文件
    current_revision = detail.get("current_revision")
    if not current_revision:
        return {"success": False, "message": "材料没有附件"}

    files = current_revision.get("files", [])

    # 优先查找原始图片
    image_file = None
    for f in files:
        if f.get("file_type") == "original" and f.get("mime_type", "").startswith("image/"):
            image_file = f
            break

    # 如果没有原始图片，使用PDF提取的页面
    if not image_file:
        extracted_pages = [f for f in files if f.get("file_type") == "extracted_page"]
        if extracted_pages:
            image_file = extracted_pages[0]  # 使用第一页
            print(f"    使用PDF提取的页面图片")

    if not image_file:
        return {"success": False, "message": "没有可用的图片"}

    # 3. 下载图片
    image_url = image_file.get("url")
    filename = image_file.get("filename", f"material_{material_id}.png")
    output_path = os.path.join(output_dir, filename)

    success = await download_image(image_url, output_path)
    if not success:
        return {"success": False, "message": "下载图片失败"}

    # 4. 添加水印
    if project_name:
        try:
            watermark.add_watermark(
                output_path,
                output_path,
                watermark_text=project_name,
                position="bottom_right",
                opacity=128,
                font_size=20,
            )
        except Exception as e:
            print(f"添加水印失败: {e}")

    # 5. 更新Markdown文件
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = content.replace(placeholder, f"![{material_title}]({filename})")

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {
            "success": True,
            "message": "成功替换占位符",
            "image_path": output_path,
            "material_title": material_title,
        }
    except Exception as e:
        return {"success": False, "message": f"更新文件失败: {e}"}


def find_placeholders(directory: str) -> List[Dict]:
    """扫描目录，找出所有占位符

    Returns:
        [
            {
                "file": "文件路径",
                "placeholder": "占位符文本",
                "context": "上下文"
            },
            ...
        ]
    """
    placeholder_pattern = r"【此处插入(.+?)】"
    results = []

    md_files = list(Path(directory).glob("**/*.md"))

    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 找到所有占位符
            for match in re.finditer(placeholder_pattern, content):
                full_placeholder = match.group(0)
                material_desc = match.group(1)

                # 获取上下文（占位符前后100个字符）
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end]

                results.append({
                    "file": str(md_file),
                    "placeholder": full_placeholder,
                    "material_desc": material_desc,
                    "context": context.replace("\n", " ").strip()
                })
        except Exception as e:
            print(f"处理文件 {md_file} 失败: {e}")

    return results


# 同步包装器
def get_all_materials_sync(*args, **kwargs):
    import asyncio
    return asyncio.run(get_all_materials(*args, **kwargs))


def get_material_detail_sync(*args, **kwargs):
    import asyncio
    return asyncio.run(get_material_detail(*args, **kwargs))


def extract_and_insert_material_sync(*args, **kwargs):
    import asyncio
    return asyncio.run(extract_and_insert_material(*args, **kwargs))
