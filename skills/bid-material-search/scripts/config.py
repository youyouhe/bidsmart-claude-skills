"""配置加载模块

支持多种配置文件位置的优先级加载：
1. 当前工作目录的 .env
2. bidsmart-claude-skills 根目录的 .env
3. material-hub 根目录的 .env（向后兼容）
4. 系统环境变量
"""

import os
from dotenv import load_dotenv


def load_config():
    """Load configuration from multiple possible locations"""
    # Try current working directory first (highest priority)
    if os.path.exists(".env"):
        load_dotenv(".env", override=True)
        return "current_dir"

    # Try bidsmart-claude-skills root (assuming skill is in skills/bid-material-search/)
    skill_dir = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(skill_dir, "..", ".."))
    repo_env = os.path.join(repo_root, ".env")
    if os.path.exists(repo_env):
        load_dotenv(repo_env, override=True)
        return "repo_root"

    # Try material-hub root (for backward compatibility)
    material_hub_env = os.path.abspath(os.path.join(skill_dir, "..", "..", "..", ".env"))
    if os.path.exists(material_hub_env):
        load_dotenv(material_hub_env, override=True)
        return "material_hub"

    # Fallback to environment variables
    load_dotenv()
    return "env_vars"


# Load on import
_config_source = load_config()

# Configuration
API_BASE = os.getenv("MATERIALHUB_API_URL", "http://localhost:8201")
API_TOKEN = os.getenv("MATERIALHUB_API_KEY", "")

# Debug info (can be disabled in production)
if os.getenv("DEBUG"):
    print(f"[bid-material-search] Config loaded from: {_config_source}")
    print(f"[bid-material-search] API_BASE: {API_BASE}")
    print(f"[bid-material-search] API_TOKEN: {API_TOKEN[:20]}..." if API_TOKEN else "[bid-material-search] API_TOKEN: <not set>")
