"""占位符替换功能

扫描 Markdown 文件，替换【此处插入XX扫描件】占位符为实际图片引用。
"""

import os
import re
import httpx
from pathlib import Path
from typing import Any, List, Dict

import search
import watermark

# Load configuration
from config import API_BASE, API_TOKEN


# 智能搜索策略
def remove_common_suffixes(text: str) -> str:
    """去除常见后缀和描述词

    Args:
        text: 原始文本

    Returns:
        去除后缀后的文本
    """
    # 阶段1：去除描述性短语
    descriptive_phrases = [
        '正反面', '扫描件', '复印件', '副本', '原件', '电子件',
        '（如需要）', '(如需要)', '近三个月内', '有效期内',
    ]
    result = text
    for phrase in descriptive_phrases:
        result = result.replace(phrase, '')

    # 阶段2：去除常见后缀
    suffixes = [
        '认证证书', '证书', '认证', '证明', '文件', '材料', '附件'
    ]
    for suffix in suffixes:
        if result.endswith(suffix):
            result = result[:-len(suffix)]

    return result.strip()


def extract_keywords(query: str) -> List[str]:
    """提取关键词

    提取查询词中的核心识别特征，如标准号、数字、关键名词等。

    Args:
        query: 查询词

    Returns:
        关键词列表
    """
    keywords = []

    # ISO 标准号（如 ISO 27001, ISO/IEC 27001）
    iso_match = re.search(r'ISO[/\s]?(?:IEC)?[\s]?(\d+)', query, re.IGNORECASE)
    if iso_match:
        keywords.append(iso_match.group(1))  # 只提取数字
        keywords.append(f'ISO {iso_match.group(1)}')

    # CMMI 等级
    cmmi_match = re.search(r'CMMI[\s]?(\d+)', query, re.IGNORECASE)
    if cmmi_match:
        keywords.append(f'CMMI{cmmi_match.group(1)}')
        keywords.append(f'CMMI {cmmi_match.group(1)}')

    # 去掉数字、括号等，提取主要名词
    clean = re.sub(r'[（）()【】\[\]0-9一二三四五六七八九十]+', '', query)
    if clean.strip():
        keywords.append(clean.strip())

    return keywords


def expand_abbreviation(query: str) -> str:
    """展开简称

    将常见简称扩展为全称。

    Args:
        query: 查询词

    Returns:
        扩展后的查询词
    """
    abbreviations = {
        '财审': '财务审计报告',
        '营执': '营业执照',
        '等保': '信息系统安全等级保护',
        '软著': '软件著作权',
        '社保': '社会保险',
        '高企': '高新技术企业',
    }

    for abbr, full in abbreviations.items():
        if abbr in query:
            query = query.replace(abbr, full)

    return query


def apply_synonyms(query: str) -> List[str]:
    """应用同义词映射

    生成同义词变体，扩大匹配范围。

    Args:
        query: 查询词

    Returns:
        包含原词和同义词的列表
    """
    result = [query]

    synonyms = {
        '委托代理人': ['委托人', '代理人'],
        '法定代表人': ['法人', '法人代表', '法定代表'],
        '项目经理': ['项目负责人', '经理'],
        '团队成员': ['成员', '人员'],
    }

    for key, syn_list in synonyms.items():
        if key in query:
            for syn in syn_list:
                result.append(query.replace(key, syn))

    return result


async def smart_search(query: str, limit: int = 5) -> List[Dict]:
    """智能搜索材料

    实现多级回退搜索策略：
    1. 尝试完整查询词
    2. 尝试同义词变体
    3. 尝试去除后缀
    4. 尝试关键词
    5. 展开简称后重试

    Args:
        query: 原始查询词
        limit: 返回数量上限

    Returns:
        搜索结果列表
    """
    # 策略1: 展开简称
    expanded_query = expand_abbreviation(query)

    # 策略2: 生成多个查询词（从具体到模糊）
    queries_to_try = [
        expanded_query,                          # 完整词（展开简称后）
    ]

    # 策略3: 添加同义词变体
    synonym_variants = apply_synonyms(expanded_query)
    queries_to_try.extend(synonym_variants)

    # 策略4: 去除后缀和描述词
    queries_to_try.append(remove_common_suffixes(expanded_query))

    # 策略5: 添加关键词
    keywords = extract_keywords(expanded_query)
    queries_to_try.extend(keywords)

    # 去重并保持顺序
    seen = set()
    unique_queries = []
    for q in queries_to_try:
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            unique_queries.append(q)

    # 逐个尝试
    for i, q in enumerate(unique_queries):
        results = await search.search_materials(query=q, limit=limit)
        if results:
            if i > 0:
                # 记录使用了哪个查询词成功
                print(f"    [回退搜索] 使用查询词 \"{q}\" 找到 {len(results)} 个结果")
            return results

    # 所有策略都失败
    return []


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
    auto_mode: bool = False,
) -> dict:
    """替换单个占位符

    Args:
        target_file: 目标 Markdown 文件路径
        placeholder: 占位符文本（如"【此处插入营业执照扫描件】"）
        query: 搜索关键词（如"营业执照"）
        project_name: 项目名称（用于水印）
        output_dir: 图片输出目录
        auto_mode: 是否为自动模式（bid-manager 调度时为 True，此时不能等待用户交互，
            多个匹配结果时按相关度取第一个但在返回结果中明确标注 ambiguous=True，
            供上游质检环节（bid-assembly）复核；非自动模式下应返回候选列表交由
            调用方（Claude）向用户提问后再次调用并指定 doc_id）

    Returns:
        {
            "success": bool,
            "message": str,
            "image_path": str,  # 如果成功
            "ambiguous": bool,  # 如果搜索命中多个结果
            "candidates": [...],  # ambiguous=True 时的候选列表
        }
    """
    # 1. 智能搜索文档（使用多级回退策略）
    results = await smart_search(query=query, limit=5)
    if not results:
        return {"success": False, "message": f"未找到匹配 '{query}' 的材料"}

    # 多个结果时的歧义处理：不静默取第一个
    if len(results) > 1:
        candidates = [
            {
                "id": r["id"],
                "title": r["title"],
                "folder": r.get("folder", {}).get("path", ""),
                "entity_names": r.get("entity_names", []),
                "expiry_date": r.get("expiry_date", ""),
            }
            for r in results
        ]
        if not auto_mode:
            # 交互模式：不猜测，返回候选列表，调用方应向用户展示后
            # 用 doc_id 参数重新调用 replace_placeholder_by_id 完成替换
            return {
                "success": False,
                "ambiguous": True,
                "message": f"'{query}' 匹配到 {len(results)} 个材料，需人工确认使用哪一个",
                "candidates": candidates,
            }
        # AUTO_MODE：不能阻塞等待用户输入，取第一个但显式标注存疑，
        # 供 bid-assembly 质检阶段复核，不当作确定无误的结果静默处理
        doc = results[0]
        ambiguous_flag = True
        ambiguous_note = f"AUTO_MODE 下从 {len(results)} 个匹配中自动选取第一个，未经人工确认，需质检复核"
    else:
        doc = results[0]
        ambiguous_flag = False
        ambiguous_note = None

    doc_id = doc["id"]
    doc_title = doc["title"]

    return await _replace_with_document(
        target_file, placeholder, doc_id, doc_title, project_name, output_dir,
        ambiguous=ambiguous_flag, ambiguous_note=ambiguous_note,
    )


async def replace_placeholder_by_id(
    target_file: str,
    placeholder: str,
    doc_id: int,
    project_name: str = "",
    output_dir: str = "响应文件",
) -> dict:
    """使用用户已确认的 doc_id 完成占位符替换（消歧后的第二次调用）

    当 replace_placeholder 返回 ambiguous=True 后，应将 candidates 展示给用户，
    用户选定具体材料后，用其 id 调用本函数完成实际替换。
    """
    detail = await search.get_document_detail(doc_id)
    if not detail:
        return {"success": False, "message": f"获取文档详情失败: {doc_id}"}
    doc_title = detail.get("title", f"material_{doc_id}")
    return await _replace_with_document(
        target_file, placeholder, doc_id, doc_title, project_name, output_dir,
        ambiguous=False, ambiguous_note=None, detail=detail,
    )


async def _replace_with_document(
    target_file: str,
    placeholder: str,
    doc_id: int,
    doc_title: str,
    project_name: str,
    output_dir: str,
    ambiguous: bool = False,
    ambiguous_note: str | None = None,
    detail: dict | None = None,
) -> dict:
    """内部函数：给定确定的 doc_id，完成图片下载、水印、占位符替换"""
    # 2. 获取文档详情
    if detail is None:
        detail = await search.get_document_detail(doc_id)
        if not detail:
            return {"success": False, "message": f"获取文档详情失败: {doc_id}"}

    # 2.1 有效期检查：过期/临期材料不静默插入，标注供人工确认
    expiry_warning = None
    expiry_date = detail.get("expiry_date")
    is_expired = detail.get("is_expired")
    if is_expired:
        expiry_warning = f"⚠️ 该材料已过期（有效期至 {expiry_date}），插入投标文件前需人工确认是否更新材料或说明情况"
    elif expiry_date:
        try:
            from datetime import date, datetime
            exp = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            days_left = (exp - date.today()).days
            if 0 <= days_left <= 30:
                expiry_warning = f"⚠️ 该材料将于 {days_left} 天内过期（{expiry_date}），建议确认投标截止日前仍在有效期内"
        except (ValueError, TypeError):
            pass

    # 3. 找到图片附件
    current_revision = detail.get("current_revision")
    if not current_revision:
        return {"success": False, "message": "文档没有附件"}

    files = current_revision.get("files", [])
    image_file = None

    # 优先查找原始图片文件
    for f in files:
        if f.get("file_type") == "original" and f.get("mime_type", "").startswith("image/"):
            image_file = f
            break

    # 如果没有原始图片，查找从PDF提取的页面图片
    if not image_file:
        extracted_pages = [f for f in files if f.get("file_type") == "extracted_page"]
        if extracted_pages:
            # 使用第一页（通常是最重要的）
            image_file = extracted_pages[0]
            print(f"    [PDF提取] 使用提取的第1页图片")

    if not image_file:
        return {"success": False, "message": "文档没有图片附件（无原始图片或提取页面）"}

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
            "ambiguous": ambiguous,
            "ambiguous_note": ambiguous_note,
            "expiry_warning": expiry_warning,
        }
    except Exception as e:
        return {"success": False, "message": f"更新文件失败: {e}"}


async def replace_all_placeholders(
    directory: str = "响应文件",
    project_name: str = "",
    auto_mode: bool = True,
) -> dict:
    """批量替换所有占位符

    扫描目录下所有 .md 文件，查找【此处插入XX扫描件】或【此处插入XX】占位符并替换。

    Args:
        directory: 扫描目录
        project_name: 项目名称（用于水印，如果为空则自动从分析报告提取）
        auto_mode: 批量模式默认按自动模式处理歧义（不阻塞等待用户输入），
            遇到多个匹配时取第一个但在 details 中标注 ambiguous=True，
            汇总到 ambiguous_count，供质检环节（bid-assembly）复核；
            如需交互式逐一确认，调用方应改用 replace_placeholder（auto_mode=False）
            单独处理每个占位符

    Returns:
        {
            "success": bool,
            "replaced_count": int,
            "failed_count": int,
            "ambiguous_count": int,  # 存疑替换数量，需人工复核
            "expiry_warning_count": int,  # 过期/临期材料数量，需人工复核
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
    ambiguous_count = 0
    expiry_warning_count = 0
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
                    auto_mode=auto_mode,
                )

                if result["success"]:
                    replaced_count += 1
                    if result.get("ambiguous"):
                        ambiguous_count += 1
                    if result.get("expiry_warning"):
                        expiry_warning_count += 1
                    details.append({
                        "file": str(md_file),
                        "placeholder": full_placeholder,
                        "query": material_name,
                        "status": "success",
                        "image": result.get("image_path"),
                        "ambiguous": result.get("ambiguous", False),
                        "ambiguous_note": result.get("ambiguous_note"),
                        "expiry_warning": result.get("expiry_warning"),
                    })
                    print(f"    ✓ 成功")
                    if result.get("ambiguous_note"):
                        print(f"    ⚠️ {result['ambiguous_note']}")
                    if result.get("expiry_warning"):
                        print(f"    {result['expiry_warning']}")
                else:
                    failed_count += 1
                    details.append({
                        "file": str(md_file),
                        "placeholder": full_placeholder,
                        "query": material_name,
                        "status": "failed",
                        "error": result.get("message"),
                        "ambiguous": result.get("ambiguous", False),
                        "candidates": result.get("candidates"),
                    })
                    print(f"    ✗ 失败: {result.get('message')}")

        except Exception as e:
            print(f"处理文件 {md_file} 失败: {e}")
            failed_count += 1

    return {
        "success": True,
        "replaced_count": replaced_count,
        "failed_count": failed_count,
        "ambiguous_count": ambiguous_count,
        "expiry_warning_count": expiry_warning_count,
        "total_files": len(md_files),
        "details": details,
        "project_name": project_name,
    }


# Sync wrappers
def replace_placeholder_sync(*args, **kwargs) -> dict:
    """同步版本的 replace_placeholder"""
    import asyncio
    return asyncio.run(replace_placeholder(*args, **kwargs))


def replace_placeholder_by_id_sync(*args, **kwargs) -> dict:
    """同步版本的 replace_placeholder_by_id"""
    import asyncio
    return asyncio.run(replace_placeholder_by_id(*args, **kwargs))


def replace_all_placeholders_sync(*args, **kwargs) -> dict:
    """同步版本的 replace_all_placeholders"""
    import asyncio
    return asyncio.run(replace_all_placeholders(*args, **kwargs))
