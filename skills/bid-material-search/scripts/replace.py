"""占位符替换功能

扫描 Markdown 文件，替换【此处插入XX扫描件】占位符为实际图片引用。
"""

import os
import re
import httpx
from pathlib import Path
from typing import Any

import search
import watermark

# Load configuration
from config import API_BASE, API_TOKEN


async def download_image(url: str, output_path: str) -> bool:
    """下载图片

    Args:
        url: 图片 URL（可以是相对路径或绝对路径）
        output_path: 输出文件路径

    Returns:
        是否成功下载
    """
    try:
        # Handle relative URLs
        if url.startswith("/"):
            url = f"{API_BASE}{url}"

        headers = {}
        if API_TOKEN:
            headers["Authorization"] = f"Bearer {API_TOKEN}"

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(output_path, "wb") as f:
                f.write(resp.content)

            return True
    except Exception as e:
        print(f"下载图片失败: {e}")
        return False


async def replace_placeholder(
    target_file: str,
    placeholder: str,
    query: str,
    project_name: str = "",
    output_dir: str = "响应文件",
) -> dict:
    """替换单个占位符

    Args:
        target_file: 目标 Markdown 文件路径
        placeholder: 占位符文本（如"【此处插入营业执照扫描件】"）
        query: 搜索关键词（如"营业执照"）
        project_name: 项目名称（用于水印）
        output_dir: 图片输出目录

    Returns:
        {
            "success": bool,
            "message": str,
            "image_path": str,  # 如果成功
        }
    """
    # 1. 搜索文档
    results = await search.search_materials(query=query, limit=5)
    if not results:
        return {"success": False, "message": f"未找到匹配 '{query}' 的材料"}

    # 使用第一个结果
    doc = results[0]
    doc_id = doc["id"]
    doc_title = doc["title"]

    # 2. 获取文档详情
    detail = await search.get_document_detail(doc_id)
    if not detail:
        return {"success": False, "message": f"获取文档详情失败: {doc_id}"}

    # 3. 找到图片附件
    current_revision = detail.get("current_revision")
    if not current_revision:
        return {"success": False, "message": "文档没有附件"}

    files = current_revision.get("files", [])
    image_file = None
    for f in files:
        if f.get("file_type") == "original" and f.get("mime_type", "").startswith("image/"):
            image_file = f
            break

    if not image_file:
        return {"success": False, "message": "文档没有图片附件"}

    # 4. 下载图片
    image_url = image_file.get("url")
    filename = image_file.get("filename", f"material_{doc_id}.png")

    # 保存图片
    output_path = os.path.join(output_dir, filename)
    success = await download_image(image_url, output_path)
    if not success:
        return {"success": False, "message": "下载图片失败"}

    # 5. 添加水印（如果有项目名称）
    if project_name:
        try:
            output_path = watermark.add_watermark(
                output_path,
                output_path,  # 覆盖原图
                watermark_text=project_name,
                position="bottom_right",
                opacity=128,
                font_size=20,
            )
        except Exception as e:
            print(f"添加水印失败: {e}")

    # 6. 更新 Markdown 文件
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 替换占位符
        new_content = content.replace(placeholder, f"![{doc_title}]({filename})")

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_content)

        return {
            "success": True,
            "message": f"成功替换占位符",
            "image_path": output_path,
            "document_title": doc_title,
        }
    except Exception as e:
        return {"success": False, "message": f"更新文件失败: {e}"}


async def replace_all_placeholders(
    directory: str = "响应文件",
    project_name: str = "",
) -> dict:
    """批量替换所有占位符

    扫描目录下所有 .md 文件，查找【此处插入XX扫描件】或【此处插入XX】占位符并替换。

    Args:
        directory: 扫描目录
        project_name: 项目名称（用于水印，如果为空则自动从分析报告提取）

    Returns:
        {
            "success": bool,
            "replaced_count": int,
            "failed_count": int,
            "details": [...]
        }
    """
    # 自动提取项目名称
    if not project_name:
        project_name = watermark.get_project_name_from_analysis("分析报告.md")

    # 查找所有 .md 文件
    md_files = list(Path(directory).glob("**/*.md"))
    if not md_files:
        return {"success": False, "message": f"目录 {directory} 下没有 .md 文件"}

    # 占位符正则表达式
    placeholder_pattern = r"【此处插入(.+?)(扫描件)?】"

    replaced_count = 0
    failed_count = 0
    details = []

    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 查找所有占位符
            placeholders = re.findall(placeholder_pattern, content)
            if not placeholders:
                continue

            print(f"\n处理文件: {md_file}")
            print(f"找到 {len(placeholders)} 个占位符")

            for match in placeholders:
                material_name = match[0].strip()
                full_placeholder = f"【此处插入{match[0]}{match[1]}】"

                print(f"  替换: {full_placeholder} (查询: {material_name})")

                result = await replace_placeholder(
                    target_file=str(md_file),
                    placeholder=full_placeholder,
                    query=material_name,
                    project_name=project_name,
                    output_dir=directory,
                )

                if result["success"]:
                    replaced_count += 1
                    details.append({
                        "file": str(md_file),
                        "placeholder": full_placeholder,
                        "query": material_name,
                        "status": "success",
                        "image": result.get("image_path"),
                    })
                    print(f"    ✓ 成功")
                else:
                    failed_count += 1
                    details.append({
                        "file": str(md_file),
                        "placeholder": full_placeholder,
                        "query": material_name,
                        "status": "failed",
                        "error": result.get("message"),
                    })
                    print(f"    ✗ 失败: {result.get('message')}")

        except Exception as e:
            print(f"处理文件 {md_file} 失败: {e}")
            failed_count += 1

    return {
        "success": True,
        "replaced_count": replaced_count,
        "failed_count": failed_count,
        "total_files": len(md_files),
        "details": details,
        "project_name": project_name,
    }


# Sync wrappers
def replace_placeholder_sync(*args, **kwargs) -> dict:
    """同步版本的 replace_placeholder"""
    import asyncio
    return asyncio.run(replace_placeholder(*args, **kwargs))


def replace_all_placeholders_sync(*args, **kwargs) -> dict:
    """同步版本的 replace_all_placeholders"""
    import asyncio
    return asyncio.run(replace_all_placeholders(*args, **kwargs))
