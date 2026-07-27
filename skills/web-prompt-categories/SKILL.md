---
name: web-prompt-categories
description: >
  Provide 60+ pre-built web template prompts organized by category (Business, E-commerce,
  Portfolio, Blog, etc.). Users select a category + template, and this skill provides
  a detailed starting prompt that can be used with web-builder-initial for instant,
  professional website generation.

  Trigger conditions:
  - User requests: "show me template categories", "what templates are available", "生成模板"
  - User wants a specific type of site: "create an e-commerce site", "make a restaurant website"
  - Interactive template selection workflow

  Outputs: Detailed prompt for selected template category
---

# Web Prompt Categories

This skill is a **data library**, not a workflow. It provides 60+ pre-built, detailed
website template prompts organized into 14 categories (Business & SaaS, E-commerce & Retail,
Food & Restaurant, Real Estate, Creative & Portfolio, Personal & Blog, Health & Fitness,
Education & Learning, Events & Entertainment, Professional Services, Technology & Apps,
Non-profit & Community, Tools & Utility, Media & Publishing). Each template prompt fully
specifies page structure, sections, content, and design guidelines, ready to hand to
`web-builder-initial` for instant professional website generation.

## When to use

- The user asks what templates/categories are available, or asks to "生成模板".
- The user wants a specific type of site (e.g. "create an e-commerce site", "make a
  restaurant website") and would benefit from a proven starting structure instead of
  a from-scratch prompt.
- Another skill (e.g. `web-builder-initial`, the POC builder) needs a categorized
  template prompt as its starting point.

## How to use — REQUIRED first step

**You MUST read `references/categories.md` (in this skill's directory) BEFORE answering
any template question or selecting/generating a template prompt.** The full template
database lives there; it is intentionally NOT inlined here. Do not guess or reconstruct
template contents from memory — read the file.

Then follow the workflow documented in `references/categories.md`:

1. **Category selection** — present the 14 categories (list in the file's "Usage Workflow"
  section), let the user pick one.
2. **Template selection** — show the templates within the chosen category (each has a
  "Best for" line), let the user pick one.
3. **Prompt generation** — copy the template's complete `Generated prompt` block verbatim,
  optionally appending user customizations (company name, colors, feature toggles).
4. **Hand-off** — pass the final prompt to `web-builder-initial` for generation.

The file also documents advanced options (template customization, section mixing across
templates, industry-keyword injection) — use them only when the user asks.

## For consumer skills

- Reference this data by reading
  `skills/web-prompt-categories/references/categories.md` — never by copying template
  text into your own SKILL.md.
- Each template's `Generated prompt` block is self-contained; concatenate user
  customizations after it and feed the result to `web-builder-initial`.
