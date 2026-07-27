# CLAUDE.md

BidSmart Claude Skills is a Claude Code skills plugin for Chinese government procurement bid management, plus an unrelated set of web-site-building skills bundled in the same plugin. Skill directories live under `skills/`; the plugin is registered via `.claude-plugin/marketplace.json`.

## Architecture

### Skills plugin structure

Each directory under `skills/` contains `SKILL.md` (required: YAML frontmatter with `name`, `description` incl. trigger conditions, then the workflow docs) and optionally `scripts/` (self-contained helper Python/Node scripts).

### Bid pipeline

`bid-manager` orchestrates a 13-stage pipeline tracked in `pipeline_progress.json`. The authoritative stage list and sequencing live in `skills/bid-manager/SKILL.md` — do not duplicate it here. Only S3 (info collection) requires user interaction; all other stages run with `AUTO_MODE=true`, skipping prompts and reading pre-collected data from `pipeline_progress.json`.

Skills outside the numbered pipeline (standalone, never called by bid-manager as a stage):
- `bid-evaluation` / `bid-eval-html` — pre-bid feasibility assessment: evaluation writes `.md` + `.json`, then calls eval-html to render a self-contained browser-local scoring page.
- `bid-requirements` → `bid-software-design` — separate deeper "systems engineering" sub-pipeline for large software-heavy bids.
- `bid-learner` — extracts lessons from the conversation and injects them into other bid-* skills' `gotchas.md`, strictly scoped to bidding-domain issues.
- `bid-ppt` — optional add-on bid-manager may invoke in AUTO_MODE, not a numbered stage.
- `bid-material-extraction` — one-off ingestion building the materials library that `bid-material-search` searches; `bigmodel-ocr`, `generate-placeholder-toolkit` — ad hoc utilities.

Web-building skills (unrelated to bidding): `web-builder-initial`, `web-builder-update`, `web-markers-parser`, `design-system-applier`, `project-namer`, `web-prompt-categories`, `image-placeholder-guide`.

### Data flow

1. Input: tender documents (Word preferred, PDF with OCR fallback, Excel spec/quotation tables).
2. `分析报告.md` — fixed filename, hardcoded dependency of every downstream skill.
3. Proposals: numbered Markdown files in `响应文件/` (`01-报价函.md`, ...).
4. Final output: Word document(s) via bid-md2doc. `核对报告.md` is excluded from Word output.

### Status summaries

Skills emit structured completion blocks for orchestrators to parse:

```
--- SKILL-NAME COMPLETE ---
Key: Value
状态: SUCCESS
--- END ---
```

## Testing

No build, lint, or test runner in this repo. Two ways to exercise code:

**Local plugin test**: clone the repo, then in your test project's `.claude/settings.local.json`:
```json
{
  "extraKnownMarketplaces": {
    "bidsmart-local": { "source": { "source": "directory", "path": "/absolute/path/to/bidsmart-claude-skills" } }
  },
  "enabledPlugins": { "bidsmart-skills@bidsmart-local": true }
}
```
Restart Claude Code, run `/skills` to confirm loading.

**Direct script testing**:
```bash
python skills/bid-analysis/scripts/parse_pdf.py <pdf> --output out.json
python skills/bid-analysis/scripts/extract_pdf_toc.py <pdf> --pages-json pages.json --output toc.json
python skills/bid-analysis/scripts/ocr_pages.py <pdf> --pages 1-10 --output ocr.json   # needs OCR_SERVICE_URL
python skills/bid-analysis/scripts/parse_excel.py 技术规范.xlsx --format both
cd skills/bid-material-search && python test_skill.py   # needs MaterialHub API running
```

Versioning: conventional commits + git tags. CHANGELOG.md has two conflicting `[1.1.0]` entries — trust git log, not CHANGELOG version numbers.

## Key implementation details

### File naming (hardcoded dependencies)
- `分析报告.md` — exact name required; every downstream skill reads it. Also fixed: `响应文件/` numbered files, `pipeline_progress.json`, `diagram-N.png` (sequential).

### DocScan (docx → per-page Markdown, `docscan/` submodule)
Two-stage startup: `docscan/start.sh [port]` first brings up an ONLYOFFICE Docker container (port 8079, JWT disabled, mounts `docscan/fonts/` for CJK) via `docker compose up -d`, then starts the FastAPI service on port 8800. There is no env var for the URL — callers assume `http://localhost:8800`. The call workflow (health → convert → md/{fid}) and the python-docx fallback are documented in `skills/bid-analysis/SKILL.md` §1.2 — read that, not here.

### Document parsing strategy (Word/PDF/Excel)
Fully specified in `skills/bid-analysis/SKILL.md` §0–1: Word-first priority, parse_pdf/extract_pdf_toc/ocr_pages flow, parse_excel outputs, tables extracted fully and never summarized. Do not restate it here.

### bid-md2doc Word generation
`generate_docx.js` takes all config as **one JSON string CLI argument** (`process.argv[2]`: `inputDir`, `outputFile`, `headerText`, `footerCompany`, `excludeFiles`, `includeFiles`, `fileOrder`) — it never edits a CONFIG block in the script. Multi-book output = multiple invocations with different include/exclude lists.

**⚠️ Portability**: `bid-md2doc`'s, `bid-assembly`'s and `bid-learner`'s SKILL.md hardcode absolute script paths into a *different sibling checkout* (`/mnt/oldroot/home/bird/xyy/smartbid-platform/packages/bidsmart-skills/...`) that only resolve on that specific host. From a plugin install or any other clone, use this repo's own `skills/bid-md2doc/scripts/generate_docx.js` and fix the SKILL.md path. Do not confuse the near-empty `smartbid-platform/` placeholder dir inside this repo with that external platform repo.

### MaterialHub (bid-material-search)
- No standalone server to start — plain Python functions call the MaterialHub REST API directly (usage details in `skills/bid-material-search/SKILL.md`).
- `config.py` looks for `.env` in cwd → repo root → material-hub root, in that order; only `skills/bid-material-search/.env.example` exists.

### Optional external services (all fail gracefully with a warning)
DocScan `localhost:8800` (needs Docker for ONLYOFFICE) · MaterialHub API `localhost:8201` (`MATERIALHUB_API_URL`/`MATERIALHUB_API_KEY`, separate repo) · OCR via `OCR_SERVICE_URL`. archify-server (port 18800, used by bid-mermaid-diagrams) runs OUTSIDE the bwrap sandbox because Chrome/Puppeteer needs full system access; only gantt/ER diagrams still go through Mermaid+mmdc.

## Skill development guidelines

New skill: `skills/<name>/SKILL.md` with frontmatter (`name`, `description` with trigger keywords + preconditions), numbered workflow steps, the status-summary block if bid-manager-orchestrated, self-contained `scripts/` (avoid hardcoded external paths — see portability caveat above).

Cross-skill communication: fixed filenames (`分析报告.md`), `pipeline_progress.json` for cross-session state, status-summary blocks for bid-manager, context flags like `AUTO_MODE`.

Error handling conventions:
- Every skill with upstream artifacts has a "Step 0: 前置检查": present → proceed; missing + interactive → ask the user whether to run the upstream skill; missing + `AUTO_MODE=true` → mark the stage `FAILED` in the status block (never fake `SUCCESS`), naming the missing artifact so bid-manager halts there.
- Validate extracted data (e.g. scoring sub-items sum to category totals).
- Optional services (OCR, MaterialHub) degrade with a warning, never silently.
- bid-assembly + bid-manager auto-fix loop: 2-round limit.

All prompts, outputs, and file/dir names are Simplified Chinese — ensure UTF-8 throughout.

## Common issues

- Skills not loading → validate `.claude/settings.local.json` JSON, absolute marketplace path, full Claude Code restart.
- PDF parse errors → prefer Word source; check password protection; scanned PDFs need `OCR_SERVICE_URL`.
- Word generation fails → run `npm install` beside `generate_docx.js` (its own `package.json`); check image paths in markdown; if using a hardcoded absolute script path, confirm it exists on this host.
