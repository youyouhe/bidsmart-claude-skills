# 🚀 Quick Start Guide

Get started with BidSmart Claude Skills in 5 minutes.

## Prerequisites

- [Claude Code](https://claude.ai/claude-code) installed
- Git (for GitHub installation method)
- Python 3.8+ (for some advanced features)

## Installation

### Step 1: Install the Plugin

Choose one of these methods:

#### Option A: Command Line (Easiest - Recommended)

In Claude Code, run:

```bash
# Add marketplace
/plugin marketplace add youyouhe/bidsmart-claude-skills

# Install plugin
/plugin install bidsmart-skills@bidsmart-skills
```

Done! Skip to Step 2.

#### Option B: Manual Configuration

1. In your project directory, edit `.claude/settings.local.json`:

```json
{
  "extraKnownMarketplaces": {
    "bidsmart": {
      "source": {
        "source": "github",
        "repo": "youyouhe/bidsmart-claude-skills"
      }
    }
  },
  "enabledPlugins": {
    "bidsmart-skills@bidsmart": true
  }
}
```

#### Option C: Local Development

```bash
# Clone the repository
git clone https://github.com/youyouhe/bidsmart-claude-skills.git ~/bidsmart-claude-skills

# Add to .claude/settings.local.json
{
  "extraKnownMarketplaces": {
    "bidsmart-local": {
      "source": {
        "source": "directory",
        "path": "~/bidsmart-claude-skills"
      }
    }
  },
  "enabledPlugins": {
    "bidsmart-skills@bidsmart-local": true
  }
}
```

### Step 2: Restart Claude Code

```bash
# Exit current session
exit

# Start new session
claude
```

### Step 3: Verify Installation

```bash
# Check available skills
/skills

# You should see all 11 bid skills listed
```

## Your First Bid Analysis

### Example 1: Complete Workflow

Let's analyze a tender document and create a proposal.

```bash
# Start Claude Code in your project directory
claude

# Run the complete workflow
/bid-manager

# Follow the interactive prompts to:
# 1. Upload your tender document
# 2. Review the analysis
# 3. Generate proposals
# 4. Create final Word documents
```

### Example 2: Manual Step-by-Step

If you prefer more control:

```bash
# 1. Analyze the tender document
/bid-analysis path/to/tender.pdf

# Review the generated analysis.md file

# 2. Extract detailed requirements
/bid-requirements path/to/tender.pdf

# 3. Write technical proposal
/bid-tech-proposal

# 4. Write commercial proposal
/bid-commercial-proposal

# 5. Generate diagrams
/bid-mermaid-diagrams

# 6. Final assembly and conversion
/bid-assembly
/bid-md2doc
```

## Common Use Cases

### Use Case 1: Quick Analysis

Just need to understand a tender document?

```bash
/bid-analysis tender.pdf
```

This will:
- Extract all requirements
- Identify scoring criteria
- Generate a structured outline
- Create a response template

### Use Case 2: Proposal Writing

Already analyzed the document and ready to write?

```bash
# For technical bid
/bid-tech-proposal

# For commercial bid
/bid-commercial-proposal
```

### Use Case 3: Material Management

Need to find and insert company materials?

```bash
# Search for matching materials
/bid-material-search

# Extract from resource library
/bid-material-extraction
```

## Project Structure

After running the skills, your project will have:

```
your-bid-project/
├── analysis/
│   ├── analysis.md              # Main analysis report
│   ├── requirements.json        # Extracted requirements
│   └── scoring_criteria.json    # Scoring breakdown
├── proposals/
│   ├── technical/
│   │   ├── technical_proposal.md
│   │   └── diagrams/
│   └── commercial/
│       └── commercial_proposal.md
├── materials/
│   └── extracted/               # Company materials
└── output/
    ├── technical_proposal.docx  # Final Word doc
    └── commercial_proposal.docx # Final Word doc
```

## Configuration

### Optional: OCR Service

For scanned PDF documents, configure OCR:

```bash
# In .env file or environment
export OCR_SERVICE_URL="http://your-ocr-service:8000"
```

### Optional: Custom Templates

Create custom templates in your project:

```
templates/
├── technical_template.md
└── commercial_template.md
```

The skills will use your templates if present.

## Troubleshooting

### Skills not showing up?

1. Check `.claude/settings.local.json` syntax
2. Ensure marketplace path is correct
3. Restart Claude Code completely
4. Check `/plugin` command for errors

### PDF parsing issues?

1. Try providing Word version if available (preferred)
2. Check if PDF is scanned (configure OCR service)
3. Verify PDF is not password-protected

### Chinese characters not displaying?

Ensure your terminal supports UTF-8:
```bash
export LANG=zh_CN.UTF-8
```

## Next Steps

- **Customize workflows**: Edit SKILL.md files to match your process
- **Add templates**: Create custom proposal templates
- **Contribute**: Share improvements back to the project

## Getting Help

- 📖 Read the full [README](README.md)
- 🐛 Report issues on [GitHub](https://github.com/youyouhe/bidsmart-claude-skills/issues)
- 💬 Check [Discussions](https://github.com/youyouhe/bidsmart-claude-skills/discussions)

## Pro Tips

1. **Use Word documents when possible** - More accurate than PDF parsing
2. **Keep materials organized** - Maintain a good resource library structure
3. **Review before final export** - Always check the markdown proposals before converting to Word
4. **Save templates** - Reuse successful proposal structures
5. **Version control** - Commit proposals to git for tracking changes

---

Happy bidding! 🎯
