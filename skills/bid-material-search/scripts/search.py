"""材料搜索功能

直接调用 MaterialHub API 进行材料搜索。
"""

import httpx
from typing import Any

# Load configuration
from config import API_BASE, API_TOKEN


def _headers() -> dict:
    """构建请求头"""
    h = {"Content-Type": "application/json"}
    if API_TOKEN:
        h["Authorization"] = f"Bearer {API_TOKEN}"
    return h


async def _get(path: str, params: dict | None = None) -> Any:
    """发送 GET 请求到 MaterialHub API"""
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30) as client:
        resp = await client.get(path, params=params, headers=_headers())
        resp.raise_for_status()
        return resp.json()


async def search_materials(
    query: str = "",
    company_name: str = "",
    doc_type: str = "",
    folder_path: str = "",
    status: str = "",
    limit: int = 50,
) -> list[dict]:
    """搜索材料

    Args:
        query: 搜索关键词
        company_name: 公司名称（关联实体过滤）
        doc_type: 文档类型（code 或名称）
        folder_path: 文件夹路径
        status: 文档状态
        limit: 返回数量上限

    Returns:
        材料列表，每个材料包含：
        {
            "id": 123,
            "title": "营业执照",
            "doc_type": {"id": 1, "name": "营业执照", "code": "business_license"},
            "folder": {"id": 2, "name": "营业执照", "path": "/企业资质/营业执照"},
            "status": "active",
            "entity_names": ["XX公司"],
            "expiry_date": "2027-12-31",
            "metadata": {...}
        }
    """
    params: dict[str, Any] = {"limit": limit, "offset": 0}

    if query:
        params["q"] = query
    if status:
        params["status"] = status

    # Resolve company_name to entity_id
    if company_name:
        try:
            ent_data = await _get("/api/v2/entities/", {"q": company_name, "entity_type": "org", "limit": 1})
            entities = ent_data.get("results", [])
            if entities:
                params["entity_id"] = entities[0]["id"]
        except Exception:
            pass

    # Resolve folder_path to folder_id
    if folder_path:
        try:
            tree_data = await _get("/api/v2/folders/tree")
            tree = tree_data.get("tree", []) if isinstance(tree_data, dict) else tree_data

            def _find_folder(nodes: list, target: str) -> int | None:
                for n in nodes:
                    if n["path"] == target or n["name"] == target:
                        return n["id"]
                    if n.get("children"):
                        found = _find_folder(n["children"], target)
                        if found:
                            return found
                return None

            fid = _find_folder(tree, folder_path)
            if fid:
                params["folder_id"] = fid
        except Exception:
            pass

    # Resolve doc_type to doc_type_id
    if doc_type:
        try:
            dt_data = await _get("/api/v2/doc-types/")
            for cat_types in dt_data.get("doc_types", {}).values():
                for dt in cat_types:
                    if dt["code"] == doc_type or doc_type.lower() in dt["name"].lower():
                        params["doc_type_id"] = dt["id"]
                        break
        except Exception:
            pass

    try:
        data = await _get("/api/v2/search", params)
        results = data.get("results", [])
        return results
    except httpx.HTTPStatusError as e:
        print(f"搜索失败: {e.response.status_code} {e.response.text}")
        return []
    except Exception as e:
        print(f"搜索失败: {e}")
        return []


async def get_document_detail(document_id: int) -> dict | None:
    """获取文档详情

    Args:
        document_id: 文档ID

    Returns:
        文档详情字典，包含完整的元数据、附件信息等
    """
    try:
        doc = await _get(f"/api/v2/documents/{document_id}")
        return doc
    except httpx.HTTPStatusError as e:
        print(f"获取文档失败: {e.response.status_code} {e.response.text}")
        return None
    except Exception as e:
        print(f"获取文档失败: {e}")
        return None


# Sync wrappers for easier use
def search_materials_sync(*args, **kwargs) -> list[dict]:
    """同步版本的 search_materials"""
    import asyncio
    return asyncio.run(search_materials(*args, **kwargs))


def get_document_detail_sync(document_id: int) -> dict | None:
    """同步版本的 get_document_detail"""
    import asyncio
    return asyncio.run(get_document_detail(document_id))
