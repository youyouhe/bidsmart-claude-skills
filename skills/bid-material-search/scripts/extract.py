"""结构化数据提取功能

使用 MaterialHub 聚合 API 提取公司和人员的完整信息。
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


async def extract_company_data(company_name: str) -> dict:
    """提取公司完整数据

    使用聚合 API 一次性获取公司的所有信息，适用于投标文件编写。

    Args:
        company_name: 公司名称

    Returns:
        {
            "company": {"name": "...", "id": ..., ...},
            "license": {"credit_code": "...", "legal_person": "...", ...},
            "certificates": [{"title": "...", "cert_number": "...", ...}],
            "persons": [{"name": "...", "gender": "...", ...}],
            "statistics": {"total_materials": 74, "total_employees": 12, ...}
        }
    """
    # 1. 查找公司实体
    try:
        ent_data = await _get("/api/v2/entities/", {"q": company_name, "entity_type": "org", "limit": 5})
        entities = ent_data.get("results", [])

        if not entities:
            return {"error": f"未找到公司: {company_name}"}

        if len(entities) > 1:
            # 返回多个匹配，让调用方选择
            return {
                "error": "找到多个匹配的公司",
                "matches": [
                    {"id": e["id"], "name": e["name"]}
                    for e in entities
                ]
            }

        company_id = entities[0]["id"]
    except Exception as e:
        return {"error": f"查询公司失败: {e}"}

    # 2. 获取公司完整信息（聚合 API）
    try:
        data = await _get(f"/api/v2/companies/{company_id}/complete")
    except httpx.HTTPStatusError as e:
        return {"error": f"获取公司信息失败: {e.response.status_code} {e.response.text}"}
    except Exception as e:
        return {"error": f"获取公司信息失败: {e}"}

    # 3. 提取和格式化数据
    company = data.get("company", {})
    license_info = data.get("license", {})
    employees = data.get("employees", [])
    materials = data.get("materials", [])
    aggregated = data.get("aggregated_info", {})
    stats = data.get("statistics", {})

    # 提取证书（从材料中筛选）
    certificates = []
    for mat in materials:
        doc_type = mat.get("doc_type", {})
        doc_type_code = doc_type.get("code", "")

        # 识别为证书类型的材料
        if "cert" in doc_type_code or "qualification" in doc_type_code:
            cert_data = mat.get("metadata", {}).get("extracted_data", {})
            certificates.append({
                "title": mat.get("title", ""),
                "cert_name": cert_data.get("cert_name", ""),
                "cert_number": cert_data.get("cert_number", ""),
                "expiry_date": mat.get("expiry_date", ""),
                "issue_date": cert_data.get("issue_date", ""),
                "issue_authority": cert_data.get("issue_authority", ""),
                "scope": cert_data.get("scope", ""),
            })

    # 提取人员信息
    persons = []
    for emp in employees:
        emp_attrs = emp.get("attributes", {})
        persons.append({
            "id": emp.get("id"),
            "name": emp.get("name", ""),
            "gender": emp_attrs.get("gender", ""),
            "age": emp_attrs.get("age", ""),
            "birth_date": emp_attrs.get("birth_date", ""),
            "education": emp_attrs.get("education", ""),
            "major": emp_attrs.get("major", ""),
            "position": emp_attrs.get("position", ""),
            "phone": emp_attrs.get("phone", ""),
            "email": emp_attrs.get("email", ""),
        })

    result = {
        "company": {
            "id": company.get("id"),
            "name": company.get("name", ""),
            "type": company.get("entity_type", "org"),
            **company.get("attributes", {}),
        },
        "license": license_info,
        "certificates": certificates,
        "persons": persons,
        "aggregated_info": aggregated,
        "statistics": stats,
    }

    return result


async def extract_person_data(person_name: str) -> dict:
    """提取人员完整数据

    使用聚合 API 一次性获取人员的所有信息。

    Args:
        person_name: 人员姓名

    Returns:
        {
            "person": {"name": "...", "gender": "...", ...},
            "company": {"name": "...", "id": ...,},
            "certificates": [{"cert_name": "...", ...}],
            "materials": [...]
        }
    """
    # 1. 查找人员实体
    try:
        ent_data = await _get("/api/v2/entities/", {"q": person_name, "entity_type": "person", "limit": 5})
        entities = ent_data.get("results", [])

        if not entities:
            return {"error": f"未找到人员: {person_name}"}

        if len(entities) > 1:
            # 返回多个匹配，让调用方选择
            return {
                "error": "找到多个匹配的人员",
                "matches": [
                    {
                        "id": e["id"],
                        "name": e["name"],
                        "company": e.get("attributes", {}).get("company", ""),
                    }
                    for e in entities
                ]
            }

        person_id = entities[0]["id"]
    except Exception as e:
        return {"error": f"查询人员失败: {e}"}

    # 2. 获取人员完整信息（聚合 API）
    try:
        data = await _get(f"/api/v2/persons/{person_id}/complete")
    except httpx.HTTPStatusError as e:
        return {"error": f"获取人员信息失败: {e.response.status_code} {e.response.text}"}
    except Exception as e:
        return {"error": f"获取人员信息失败: {e}"}

    # 3. 提取和格式化数据
    person = data.get("person", {})
    company = data.get("company")
    certificates = data.get("certificates", [])
    materials = data.get("materials", [])
    aggregated = data.get("aggregated_info", {})

    result = {
        "person": {
            "id": person.get("id"),
            "name": person.get("name", ""),
            **person.get("attributes", {}),
        },
        "company": company if company else None,
        "certificates": certificates,
        "materials": materials,
        "aggregated_info": aggregated,
    }

    return result


# Sync wrappers for easier use
def extract_company_data_sync(company_name: str) -> dict:
    """同步版本的 extract_company_data"""
    import asyncio
    return asyncio.run(extract_company_data(company_name))


def extract_person_data_sync(person_name: str) -> dict:
    """同步版本的 extract_person_data"""
    import asyncio
    return asyncio.run(extract_person_data(person_name))
