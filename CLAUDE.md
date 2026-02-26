# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

BidSmart Claude Skills is a comprehensive Claude Code skills plugin for Chinese government procurement bid management. It provides 11 specialized skills that automate the end-to-end workflow from analyzing tender documents to generating final Word proposal documents.

## Architecture

### Skills Plugin Structure

All skills are located in `skills/` directory. Each skill directory contains:
- `SKILL.md` - Skill definition with YAML frontmatter (name, description, trigger conditions) followed by detailed workflow documentation
- `scripts/` (optional) - Helper Python/JavaScript scripts for that skill

The plugin is registered via `.claude-plugin/marketplace.json` which defines the plugin metadata for Claude Code's marketplace system.

### Workflow Pipeline

The 11 skills form a 10-stage bidding pipeline orchestrated by `bid-manager`:

```
S1: Analysis → S2: Verification → S3: Info Collection → S4: Commercial → S5: Technical
→ S6: Diagrams → S7: Material → S8: Quality Check → S9: Auto-fix → S10: Generate Word
```

**Key Skills:**
- **bid-manager** - Orchestrates complete workflow, tracks progress in `pipeline_progress.json`
- **bid-analysis** - Parses tender documents (PDF/Word/Excel), extracts scoring criteria and requirements, supports multi-file input
- **bid-verification** - Validates analysis report against source documents
- **bid-tech-proposal** - Writes technical proposal markdown files
- **bid-commercial-proposal** - Writes commercial proposal markdown files
- **bid-mermaid-diagrams** - Generates Mermaid diagrams and renders to PNG
- **bid-material-search** - FastAPI service for searching and inserting company materials
- **bid-assembly** - Quality checks all outputs, generates verification report
- **bid-md2doc** - Converts markdown to formatted Word documents

### Data Flow

1. **Input**: Tender/procurement documents (supports multiple files)
   - **Word (.docx)** - Preferred format (accurate text and table extraction)
   - **PDF** - Supported with TOC extraction and OCR
   - **Excel (.xlsx, .xls)** - NEW: Technical specifications, quotation lists, parameter tables
   - Multiple files supported: tender documents + technical specs + contract templates
2. **Analysis**: Outputs `分析报告.md` (fixed filename, required by downstream skills)
3. **Proposals**: Markdown files in `响应文件/` directory, numbered sequentially (e.g., `01-报价函.md`)
4. **Final Output**: Word document in `响应文件/` directory

### AUTO_MODE

Skills can run in two modes:
- **Interactive**: Prompts user for information and confirmations
- **AUTO_MODE**: Used by bid-manager, skips prompts, uses pre-collected data from `pipeline_progress.json`

Skills check for AUTO_MODE in context and adjust behavior accordingly.

### Status Summaries

Skills output structured status blocks at completion for parsing by orchestrators:

```
--- SKILL-NAME COMPLETE ---
Key: Value
...
状态: SUCCESS
--- END ---
```

## Development Commands

### Testing Skills Locally

```bash
# Clone repository
git clone https://github.com/youyouhe/bidsmart-claude-skills.git
cd bidsmart-claude-skills

# Configure Claude Code to use local skills
# Edit .claude/settings.local.json in your test project:
{
  "extraKnownMarketplaces": {
    "bidsmart-local": {
      "source": {
        "source": "directory",
        "path": "/absolute/path/to/bidsmart-claude-skills"
      }
    }
  },
  "enabledPlugins": {
    "bidsmart-skills@bidsmart-local": true
  }
}

# Restart Claude Code to load skills
```

### Testing Individual Scripts

```bash
# PDF parsing
python skills/bid-analysis/scripts/parse_pdf.py <pdf_path> --output output.json

# PDF TOC extraction
python skills/bid-analysis/scripts/extract_pdf_toc.py <pdf_path> --pages-json pages.json --output toc.json

# OCR (requires OCR_SERVICE_URL environment variable)
python skills/bid-analysis/scripts/ocr_pages.py <pdf_path> --pages 1-10 --output ocr.json

# Material search service
cd skills/bid-material-search/scripts
python app.py  # Starts FastAPI service on port 8000
```

### Version Control

```bash
# Tag releases
git tag -a v1.0.0 -m "Release message"
git push origin v1.0.0

# Follow conventional commits for CHANGELOG
# feat: New feature
# fix: Bug fix
# docs: Documentation
# refactor: Code refactoring
# chore: Maintenance
```

## Key Implementation Details

### File Naming Conventions

- **Analysis report**: MUST be named `分析报告.md` (hardcoded dependency)
- **Response files**: Numbered like `01-报价函.md`, `02-授权书.md` in `响应文件/` directory
- **Progress tracking**: `pipeline_progress.json` tracks pipeline state
- **Quality report**: `核对报告.md` in `响应文件/`, excluded from final Word output
- **Diagrams**: Named `diagram-N.png` where N is sequential

### PDF Processing Strategy

**Priority**: Always prefer Word (.docx) over PDF when both available. Word provides:
- Exact text extraction
- Structured table data
- No OCR errors

**PDF Workflow**:
1. Run `parse_pdf.py` to extract pages and detect if scanned
2. Run `extract_pdf_toc.py` to get table of contents structure
3. If scanned and OCR_SERVICE_URL configured, run `ocr_pages.py`
4. Skills read from generated JSON files for structured access
5. Fallback: Use Read tool to read PDF directly in 15-20 page chunks

**Critical**: Chinese government tender documents often have critical data (scoring criteria, payment terms) in tables. Tables must be fully extracted, not summarized.

### Excel Processing Strategy (NEW in v2.4.0)

**Priority**: Excel files contain detailed technical specifications, quotation lists, and parameter tables that complement main tender documents.

**Typical Excel Files**:
- Technical specification tables (功能参数表)
- Quotation/budget lists (报价清单)
- Feature comparison tables (功能对比表)
- Scoring criteria details (评分细则表)

**Excel Workflow**:
1. Run `parse_excel.py` to extract all worksheets and data
2. Generates both JSON (structured) and Markdown (human-readable) outputs
3. Skills read Markdown format for easy table comprehension
4. Supports multi-file processing (batch mode)
5. Fallback: Claude can directly read Excel files

**Usage**:
```bash
# Single file
python skills/bid-analysis/scripts/parse_excel.py 技术规范.xlsx --format both

# Output:
# - 技术规范_data.json (complete data)
# - 技术规范_data.md (formatted tables)
```

**Multi-File Integration**:
- Main file (磋商文件.docx): Scoring criteria, process requirements
- Excel files: Detailed parameters, pricing breakdown
- Contract templates: Payment terms, warranty periods
- All information merged into unified analysis report with source attribution

**See**: `skills/bid-analysis/MULTI_FILE_EXAMPLE.md` for complete workflow examples.

### Word Document Generation

The `bid-md2doc` skill:
1. Reads project name from `分析报告.md`
2. Reads company name from commercial proposal files
3. Edits CONFIG section of `/home/tiger/bid/generate_docx.js`
4. Runs Node.js script to convert all markdown files in `响应文件/` to single Word document
5. Excludes `核对报告.md` and `装订指南.md` from output

### Material Search Service

`bid-material-search` provides FastAPI REST service:
- Serves extracted materials (images of certificates, contracts, etc.)
- Provides keyword search via `/search` endpoint
- Supports batch placeholder replacement in markdown files
- Uses `index.json` for metadata and full-text search

## Skill Development Guidelines

### Creating New Skills

1. Create directory in `skills/new-skill-name/`
2. Write `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: skill-name
   description: >
     Detailed description including when to trigger this skill.
     Include trigger keywords and preconditions.
   ---
   ```
3. Document workflow as numbered steps
4. Include status summary format if skill will be orchestrated
5. Add scripts to `scripts/` subdirectory if needed
6. Update `README.md` to list new skill

### Skill Communication Protocol

Skills in the pipeline communicate via:
1. **Files**: Analysis outputs go to fixed filenames (e.g., `分析报告.md`)
2. **Progress JSON**: `pipeline_progress.json` stores cross-skill state
3. **Status summaries**: Structured text blocks for orchestrators to parse
4. **Context flags**: AUTO_MODE and other flags passed in conversation context

### Error Handling Patterns

- **Missing prerequisites**: Check for required files, return clear error message
- **Data validation**: Verify extracted data (e.g., scoring totals match)
- **Graceful degradation**: If optional services (OCR, material library) unavailable, skip with warning
- **Fix loops**: `bid-assembly` + `bid-manager` implement auto-fix with 2-round limit

## Testing Skills

### Manual Testing Workflow

1. Place sample tender document in test directory
2. Run `/bid-analysis <path>` and verify `分析报告.md` accuracy
3. Run `/bid-tech-proposal` and check markdown quality
4. Run `/bid-mermaid-diagrams` and verify PNG generation
5. Run `/bid-md2doc` and check Word formatting

### Validation Checklist

- [ ] Scoring criteria totals match (sub-items sum to category total)
- [ ] All tables from tender fully extracted
- [ ] Qualification requirements match source exactly (no hallucination)
- [ ] Diagrams render correctly as PNG
- [ ] Word document includes all markdown files except excluded ones
- [ ] Images embedded in Word correctly
- [ ] No placeholder text like 【此处插入XX】 remains in final output

## Chinese Language Considerations

- All prompts, outputs, and file contents use Simplified Chinese
- Tender documents follow Chinese government procurement format
- Compliance requirements reference Chinese regulations
- File and directory names use Chinese characters
- Ensure terminal/editor supports UTF-8

## Dependencies

**Python** (3.8+):
- `pdfplumber` - PDF table extraction
- `PyMuPDF` (fitz) - PDF parsing
- `python-docx` - Word document reading
- `fastapi`, `uvicorn` - Material search service
- `requests` - OCR client (optional)

**Node.js**:
- `docx` package - Word document generation
- Mermaid CLI - Diagram rendering

**Optional Services**:
- OCR service endpoint (configure via `OCR_SERVICE_URL`)

## Common Issues

### Skills Not Loading
- Check `.claude/settings.local.json` syntax is valid JSON
- Verify marketplace path is absolute and correct
- Restart Claude Code completely

### PDF Parsing Errors
- Word format strongly preferred over PDF
- Check if PDF is password-protected
- For scanned PDFs, configure OCR service

### Word Generation Fails
- Verify `docx` npm package installed in `/home/tiger/bid/`
- Check image paths in markdown are correct
- Verify no special characters breaking table parsing
