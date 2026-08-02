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

### Placeholder registry (占位符对照表机制 v1)

Image/screenshot/scan placeholders use a **unique-id + JSON registry** pattern so replacement is **lookup-based, not text/prefix guessing** (the old text-match approach caused mis-replacement, missed variant placeholders like `【此处展示…】`, and duplicate-image confusion).

**Placeholder format** (regex): `【此处插入:(截图|图表|扫描件):<id>】`，其中 `<id>` 为 `[A-Za-z0-9_-]+`。
- `截图` id = `system_decomposition.json` 里该功能点的 id（如 `S01-001`）——已唯一，**直接复用**，不要为截图新造 id。
- `图表` id = 语义 slug（如 `sys-arch`）；`扫描件` id = 材料类型码（如 `business-license`）。仅当无自然唯一键时用 `uuid-<短码>`（用 helper 脚本生成，**禁止让 LLM 凭空造 UUID**）。

**对照表文件**：项目工作目录根的 `placeholders.json`（与 `分析报告.md` 同级）。

**Schema**：
```json
{ "version": 1, "items": [
  { "id": "S01-001", "type": "screenshot", "system": "S01", "function_point": "S01-001",
    "label": "系统架构与多终端支持", "source_file": "15-技术要求响应材料.md",
    "status": "pending", "asset": null },
  { "id": "sys-arch", "type": "diagram", "title": "系统总体架构图",
    "source_file": "16-技术方案.md", "status": "pending", "asset": null },
  { "id": "business-license", "type": "scan", "material_type": "business_license",
    "source_file": "00-资格证明文件合集.md", "status": "pending", "asset": null }
]}
```
- `type` ∈ `screenshot` | `diagram` | `scan`。
- `status` ∈ `pending`（写入方登记）| `done`（替换方替换后回填 `asset`）。
- `asset` = 产物相对路径（png / 扫描件图），由替换方填写。

**写入方**（`bid-tech-proposal` 写 截图/图表，`bid-commercial-proposal` 写 扫描件）：每在正文写一个占位符，就向 `placeholders.json` upsert 对应 item（按 `id` 幂等去重）。

**替换方**（`bid-poc-screenshots` / `bid-mermaid-diagrams` / `bid-material-search`）：读 `placeholders.json`，filter `type` = 自己的领域 且 `status` = `pending`，用 `id` 在 `source_file` 里精确定位 `【此处插入:<type>:<id>】`，替换为产物，回填 `status` = `done` + `asset`。**不做文字/前缀/label 猜测——id 是唯一连接键。**

**校验方**（`bid-assembly`）：闭环核对——(a) 每个表内 `id` 在其 `source_file` 中有且仅有 1 个占位符；(b) 正文中每个占位符的 `id` 都在表里；(c) 每个 `done` item 的 `asset` 文件确实存在；(d) 所有替换器跑完后仍 `pending` 的 item → 🔴。以此捕获"表与正文漂移"。

老项目里的 legacy 占位符 `【此处插入XX图/截图/扫描件】`（无 id）仍由 `bid-assembly` §5.3 兜底清扫；**新项目一律用对照表**。

### Mock materials registry (mock_materials_registry.json)

MaterialHub 目前配置为 mock 数据（出于用户隐私考虑，暂未接入真实资质库）。招标要求的某类材料在 MaterialHub 中零命中时，`bid-material-search` 可调用 `material_hub_mock_generate` 工具按需生成一份贴合该要求的临时材料（见其 SKILL.md "Mock 生成兜底路径"），而不是直接留空占位符——但生成的是**假材料**，必须被显式追踪、最终提醒用户替换。

**对照表文件**：项目工作目录根的 `mock_materials_registry.json`（与 `placeholders.json` 同级）。

**Schema**：
```json
{ "items": [
  { "document_id": 42, "doc_type_code": "iso-cert", "entity_name": "星辰科技有限公司",
    "requirement_text": "投标人须具备ISO27001信息安全管理体系认证",
    "placeholder_id": "iso27001-cert", "generated_at": "2026-08-02T10:00:00Z" }
]}
```

**写入方**（`bid-material-search`）：每次调用 `material_hub_mock_generate` 成功生成一份材料，就向本文件 append 对应 item（`document_id` 幂等去重）。同时在对应的 `placeholders.json` item 上追加 `is_mock_pending_replacement: true` 标记（而非直接标 `done`——材料确实已替换进正文，但来源是假的，需要这个标记与"真实材料替换完成"区分）。

**读取方**（`bid-assembly` 质检阶段）：交付前检查本文件是否非空。非空则在最终交付说明中用**最高优先级（🔴）**列出待替换材料清单（材料类型、对应招标要求原文、MaterialHub 文档 id），不得被其他"✅ 已完成"的措辞掩盖。也可调用 `material_hub_mock_pending_list` 工具做一次服务端权威核对（同一份材料若已被用户在 MaterialHub 替换为真实材料，会从该工具的返回结果中消失，即使本地 registry 文件未同步更新，也应以服务端结果为准）。

**不产生本文件**：如果本次投标 MaterialHub 检索全部命中真实材料（未触发任何 mock 生成），本文件不应被创建——它的存在本身就是"本次标书含未替换假材料"的信号，不能因为流程需要就无条件创建空文件。

### File naming (hardcoded dependencies)
- `分析报告.md` — exact name required; every downstream skill reads it. Also fixed: `响应文件/` numbered files, `pipeline_progress.json`, `diagram-N.png` (sequential).

### DocScan (docx → per-page Markdown, `docscan/` submodule)
Two-stage startup: `docscan/start.sh [port]` first brings up an ONLYOFFICE Docker container (port 8079, JWT disabled, mounts `docscan/fonts/` for CJK) via `docker compose up -d`, then starts the FastAPI service on port 8800. `DOCSCAN_URL`/`DOCSCAN_API_KEY` 由平台解析（DB 权威）：Web 会话（BidAgentService 子进程，bwrap 继承 API 进程 env）直接用；CLI/插件会话的 shell 拿不到 API 进程 env，由平台把 DB 配置同步到 `${SMARTBID_CONFIG_DIR:-~/.config/smartbid}/services.env`，skill 在调 DocScan 前用一个引导块 `source` 它（见 `bid-analysis`/`bid-md2doc`/`bid-assembly` 的 DocScan 段；三处逐字节相同，改一处须同步另两处——为可移植性刻意内联，不抽 `_shared/`）。未配置时回退 `http://localhost:8800`。The call workflow (health → convert → md/{fid}) and the python-docx fallback are documented in `skills/bid-analysis/SKILL.md` §1.2 — read that, not here.

### Document parsing strategy (Word/PDF/Excel)
Fully specified in `skills/bid-analysis/SKILL.md` §0–1: Word-first priority, parse_pdf/extract_pdf_toc/ocr_pages flow, parse_excel outputs, tables extracted fully and never summarized. Do not restate it here.

### bid-md2doc Word generation
`generate_docx.js` takes all config as **one JSON string CLI argument** (`process.argv[2]`: `inputDir`, `outputFile`, `headerText`, `footerCompany`, `excludeFiles`, `includeFiles`, `fileOrder`) — it never edits a CONFIG block in the script. Multi-book output = multiple invocations with different include/exclude lists.

**⚠️ Portability**: `bid-md2doc`'s, `bid-assembly`'s and `bid-learner`'s SKILL.md hardcode absolute script paths into a *different sibling checkout* (`/mnt/oldroot/home/bird/xyy/smartbid-platform/packages/bidsmart-skills/...`) that only resolve on that specific host. From a plugin install or any other clone, use this repo's own `skills/bid-md2doc/scripts/generate_docx.js` and fix the SKILL.md path. Do not confuse the near-empty `smartbid-platform/` placeholder dir inside this repo with that external platform repo.

### MaterialHub (bid-material-search)
- No standalone server to start — plain Python functions call the MaterialHub REST API directly (usage details in `skills/bid-material-search/SKILL.md`).
- `config.py` looks for `.env` in cwd → repo root → material-hub root, in that order; only `skills/bid-material-search/.env.example` exists.

### Optional external services (all fail gracefully with a warning)
DocScan `localhost:8800` 默认（可经系统设置 `services.docscanUrl`/`docscanApiKey` 配远程地址；平台同步到 env 与 `services.env`，见上节；needs Docker for ONLYOFFICE） · MaterialHub API `localhost:8201` (`MATERIALHUB_API_URL`/`MATERIALHUB_API_KEY`, separate repo) · OCR via `OCR_SERVICE_URL`. archify-server (port 18800, used by bid-mermaid-diagrams) runs OUTSIDE the bwrap sandbox because Chrome/Puppeteer needs full system access; only gantt/ER diagrams still go through Mermaid+mmdc.

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
