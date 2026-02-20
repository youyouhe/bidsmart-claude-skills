"""FastAPI backend for bid material search - MaterialHub API integration."""

import getpass
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from materialhub_client import MaterialHubClient

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# MaterialHub material_type 到旧分类的映射
MATERIAL_TYPE_MAP = {
    "license": "资质证明",
    "qualification": "资质证明",
    "certificate": "资质证明",
    "iso_cert": "资质证明",
    "legal_person_cert": "资质证明",
    "id_card": "人员资料",
    "education": "人员资料",
    "degree": "人员资料",
    "contract": "业绩证明",
    "performance": "业绩证明",
    "other": "基本文件",
}

app = FastAPI(title="投标文件检索系统 (MaterialHub)", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局客户端
materialhub_client: Optional[MaterialHubClient] = None


def _get_credentials():
    """获取认证凭据（优先环境变量，否则交互式输入）

    Returns:
        tuple: (username, password)
    """
    username = os.getenv("MATERIALHUB_USERNAME")
    password = os.getenv("MATERIALHUB_PASSWORD")

    # 如果环境变量未设置，提示用户输入
    if not username or not password:
        logger.info("MaterialHub 认证信息未在环境变量中找到，请输入：")
        print("\n" + "=" * 60)
        print("MaterialHub 认证")
        print("=" * 60)

        if not username:
            try:
                username = input("用户名 [默认: admin]: ").strip()
                if not username:
                    username = "admin"
            except (EOFError, KeyboardInterrupt):
                logger.error("\n用户取消输入，使用默认值: admin")
                username = "admin"

        if not password:
            try:
                password = getpass.getpass("密码: ")
                if not password:
                    logger.warning("密码为空，使用默认值")
                    password = "admin123"
            except (EOFError, KeyboardInterrupt):
                logger.error("\n用户取消输入，使用默认值")
                password = "admin123"

        print("=" * 60 + "\n")

    return username, password


@app.on_event("startup")
def initialize():
    """初始化 MaterialHub 客户端"""
    global materialhub_client

    internal_url = os.getenv("MATERIALHUB_INTERNAL_URL", "http://localhost:8201")
    external_url = os.getenv("MATERIALHUB_EXTERNAL_URL", "http://senseflow.club:3100")
    cache_dir = os.getenv("MATERIALHUB_CACHE_DIR", ".cache")

    # 获取认证凭据（环境变量或交互式输入）
    username, password = _get_credentials()

    materialhub_client = MaterialHubClient(
        internal_url=internal_url,
        external_url=external_url,
        username=username,
        password=password,
        cache_dir=cache_dir,
    )

    # 尝试连接
    if materialhub_client.connect():
        logger.info(f"Connected to MaterialHub: {materialhub_client.base_url}")
    else:
        logger.warning("MaterialHub API unavailable - service will return empty results")


def _transform_material(material: dict) -> dict:
    """将 MaterialHub material 转换为旧格式

    Args:
        material: MaterialHub API 返回的 material 对象

    Returns:
        旧格式的文档对象
    """
    material_id = material["id"]
    title = material.get("title", "")
    section = material.get("section", "")
    material_type = material.get("material_type", "other")

    return {
        "id": f"mat_{material_id}",
        "section": section,
        "type": title,
        "category": MATERIAL_TYPE_MAP.get(material_type, "基本文件"),
        "label": f"{section} {title}".strip() if section else title,
        "page_range": [],
        "source": "materialhub",
        "images": [
            {
                "filename": material.get("image_filename", f"material_{material_id}.png"),
                "url": f"/api/materials/{material_id}/image",
            }
        ],
        "_material_id": material_id,  # 用于下载图片
    }


@app.get("/health")
def health_check():
    """服务健康检查"""
    materialhub_connected = bool(materialhub_client and materialhub_client.token)
    return {
        "status": "healthy",
        "materialhub_connected": materialhub_connected,
        "materialhub_url": materialhub_client.base_url if materialhub_client else None,
    }


@app.get("/api/search")
def search(
    q: Optional[str] = Query(None, description="搜索关键词"),
    type: Optional[str] = Query(None, description="文档类型匹配"),
    category: Optional[str] = Query(None, description="分类过滤"),
    company_id: Optional[int] = Query(None, description="公司ID过滤"),
    company_name: Optional[str] = Query(None, description="公司名称过滤（模糊匹配）"),
):
    """搜索材料（从 MaterialHub API）

    Args:
        q: 搜索关键词
        type: 文档类型过滤（模糊匹配）
        category: 分类过滤（模糊匹配）
        company_id: 公司ID过滤（精确匹配）
        company_name: 公司名称过滤（模糊匹配，优先级低于company_id）

    Returns:
        搜索结果列表
    """
    if not materialhub_client or not materialhub_client.token:
        logger.warning("MaterialHub client not available")
        return {"results": []}

    # 解析公司ID（优先级：company_id > company_name）
    target_company_id = None
    if company_id:
        target_company_id = company_id
    elif company_name:
        # 通过公司名称模糊匹配查找公司ID
        companies = materialhub_client.get_companies()
        matching_companies = [
            c for c in companies
            if company_name.lower() in c.get("name", "").lower()
        ]
        if matching_companies:
            target_company_id = matching_companies[0]["id"]
            logger.info(f"Matched company '{company_name}' to ID {target_company_id}: {matching_companies[0]['name']}")
        else:
            logger.warning(f"No company matched for name: {company_name}")

    # 调用 MaterialHub API 搜索
    materials = materialhub_client.search_materials(q=q, company_id=target_company_id)

    # 转换为旧格式
    results = [_transform_material(m) for m in materials]

    # 客户端过滤（type 和 category）
    if type:
        results = [r for r in results if type in r.get("type", "")]

    if category:
        results = [r for r in results if category in r.get("category", "")]

    logger.info(
        f"Search results: {len(results)} materials "
        f"(q={q}, type={type}, category={category}, company_id={target_company_id})"
    )
    return {"results": results}


@app.get("/api/documents")
def list_documents():
    """列出所有材料（兼容旧端点）"""
    if not materialhub_client or not materialhub_client.token:
        logger.warning("MaterialHub client not available")
        return {"documents": []}

    materials = materialhub_client.search_materials()
    results = [_transform_material(m) for m in materials]
    return {"documents": results}


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str):
    """获取单个材料详情（兼容旧端点）"""
    if not materialhub_client or not materialhub_client.token:
        raise HTTPException(status_code=503, detail="MaterialHub API unavailable")

    # 从 doc_id 提取 material_id
    if not doc_id.startswith("mat_"):
        raise HTTPException(status_code=400, detail="Invalid doc_id format")

    try:
        material_id = int(doc_id.split("_")[1])
    except (IndexError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid doc_id format")

    # 搜索该材料
    materials = materialhub_client.search_materials()
    for m in materials:
        if m["id"] == material_id:
            return _transform_material(m)

    raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")


@app.get("/api/companies")
def list_companies():
    """列出所有公司（新增端点）

    Returns:
        公司列表，包含材料统计
    """
    if not materialhub_client or not materialhub_client.token:
        raise HTTPException(status_code=503, detail="MaterialHub API unavailable")

    companies = materialhub_client.get_companies()
    logger.info(f"Listed {len(companies)} companies")
    return {"companies": companies}


class ReplaceRequest(BaseModel):
    target_file: str
    placeholder: str
    doc_id: str | None = None
    query: str | None = None


@app.post("/api/replace")
def replace_placeholder(req: ReplaceRequest):
    """替换占位符为材料图片

    Args:
        req: 替换请求参数

    Returns:
        替换结果
    """
    if not materialhub_client or not materialhub_client.token:
        raise HTTPException(status_code=503, detail="MaterialHub API unavailable")

    # 1. 搜索材料
    if req.doc_id and req.doc_id.startswith("mat_"):
        # 从 doc_id 提取 material_id
        try:
            material_id = int(req.doc_id.split("_")[1])
            # 验证材料存在
            materials = materialhub_client.search_materials()
            material = next((m for m in materials if m["id"] == material_id), None)
            if not material:
                raise HTTPException(status_code=404, detail=f"Material not found: {req.doc_id}")
        except (IndexError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid doc_id format")

    elif req.query:
        materials = materialhub_client.search_materials(q=req.query)
        if not materials:
            raise HTTPException(status_code=404, detail=f"No material matching '{req.query}'")
        material = materials[0]
        material_id = material["id"]

    else:
        raise HTTPException(status_code=400, detail="Must provide doc_id or query")

    # 2. 读取目标文件并验证占位符
    target = Path(req.target_file)
    if not target.is_file():
        raise HTTPException(status_code=404, detail=f"Target file not found: {req.target_file}")

    content = target.read_text(encoding="utf-8")
    if req.placeholder not in content:
        raise HTTPException(
            status_code=404,
            detail=f"Placeholder not found in file: {req.placeholder}",
        )

    # 3. 下载图片到目标目录（带缓存）
    image_bytes = materialhub_client.get_material_image(material_id)
    if not image_bytes:
        raise HTTPException(status_code=500, detail="Failed to download image from MaterialHub")

    target_dir = target.parent
    image_filename = f"material_{material_id}.png"
    image_path = target_dir / image_filename

    try:
        image_path.write_bytes(image_bytes)
        logger.info(f"Saved image to {image_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")

    # 4. 替换占位符
    title = material.get("title", f"material_{material_id}")
    md_image = f"![{title}]({image_filename})"
    content = content.replace(req.placeholder, md_image, 1)

    # 5. 写回文件
    try:
        target.write_text(content, encoding="utf-8")
        logger.info(f"Replaced placeholder in {target}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {e}")

    return {
        "success": True,
        "replaced": req.placeholder,
        "doc_id": f"mat_{material_id}",
        "doc_label": f"{material.get('section', '')} {material.get('title', '')}".strip(),
        "images_copied": [image_filename],
        "target_file": str(target),
    }
