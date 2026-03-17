"""bid-material-search skill - MCP-based implementation

搜索和查询投标材料，直接使用 MaterialHub MCP tools。
"""

__version__ = "3.0.0"  # MCP-based version

from .search import search_materials
from .extract import extract_company_data, extract_person_data
from .replace import replace_placeholder, replace_all_placeholders
from .watermark import add_watermark, get_project_name_from_analysis

__all__ = [
    "search_materials",
    "extract_company_data",
    "extract_person_data",
    "replace_placeholder",
    "replace_all_placeholders",
    "add_watermark",
    "get_project_name_from_analysis",
]
