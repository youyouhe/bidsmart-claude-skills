# Changelog

All notable changes to bid-material-search skill.

## [3.0.0] - 2026-03-16

### 🎉 Major Refactoring - MCP Integration

**Breaking Changes:**
- Removed FastAPI server completely
- Changed from HTTP-based to direct Python function calls
- Removed `app.py` and `materialhub_client.py`

**Added:**
- Direct MaterialHub API integration via httpx
- Sync wrappers for all async functions (`*_sync`)
- Comprehensive test suite (`test_skill.py`)
- Integration guide (`INTEGRATION.md`)
- Technical documentation (`README.md`)

**Improved:**
- 10x faster company data extraction (1 API call vs 10+)
- Zero startup time (no FastAPI service needed)
- Simpler error handling
- Better integration with bid-manager

**MCP Server Extensions:**
- Added `get_company_complete` tool to MCP server
- Added `get_person_complete` tool to MCP server

### Migration Guide

**Before (v2.x):**
```python
# Start FastAPI
subprocess.Popen(["uvicorn", "app:app", "--port", "9000"])
time.sleep(3)

# HTTP call
response = requests.post("http://localhost:9000/api/replace", json={...})
```

**After (v3.0):**
```python
# Direct import
from bid_material_search.replace import replace_all_placeholders_sync

# Function call
result = replace_all_placeholders_sync("响应文件", project_name)
```

## [2.3.2] - 2026-02-21

### Added
- Word document watermarking support
- Batch processing for .docx files

## [2.3.1] - 2026-02-21

### Added
- Automatic watermark with project name extraction from analysis report
- Configurable watermark position, opacity, and style

## [2.3.0] - 2026-02-21

### Added
- MaterialHub aggregation API integration
- `/api/companies/{id}/complete` endpoint usage
- `/api/persons/{id}/complete` endpoint usage

### Improved
- Data extraction performance (~10x faster)
- Single API call for complete company info

## [2.2.0] - 2026-02-20

### Added
- Structured data extraction endpoint (`/api/extract`)
- Automatic aggregation of company information
- Certificate extraction
- Employee information parsing

## [2.1.0] - 2026-02-19

### Added
- Multi-company filtering
- Company ID filter (`?company_id=1`)
- Company name filter (`?company_name=公司名`, fuzzy search)

### Fixed
- Search accuracy improvements

## [2.0.0] - 2026-02-20

### Changed
- **Breaking:** Removed local `pages/` and `index.json`
- Integrated with MaterialHub API
- Added Session-based authentication
- Image caching in `.cache` directory

### Added
- Dual URL mode (internal + external fallback)
- Automatic connection switching
- MaterialHub client library

### Removed
- Local file storage dependency
- Manual index management

## [1.x] - Legacy

Legacy versions used local file storage and index.json.
Details not documented.

---

[3.0.0]: https://github.com/youyouhe/material-hub/compare/v2.3.2...v3.0.0
[2.3.2]: https://github.com/youyouhe/material-hub/compare/v2.3.1...v2.3.2
[2.3.1]: https://github.com/youyouhe/material-hub/compare/v2.3.0...v2.3.1
[2.3.0]: https://github.com/youyouhe/material-hub/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/youyouhe/material-hub/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/youyouhe/material-hub/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/youyouhe/material-hub/releases/tag/v2.0.0
