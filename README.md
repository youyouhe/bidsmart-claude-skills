# BidSmart Claude Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Comprehensive Claude Code skills for Chinese government procurement and bid management workflows. This collection provides end-to-end automation for analyzing tender documents, writing proposals, and assembling bid packages.

## 🎯 Features

### Complete Bid Management Workflow

1. **📋 Bid Analysis** (`/bid-analysis`) - Analyze tender documents (PDF/Word), extract scoring criteria, technical requirements, budget constraints, and generate structured outlines
2. **✅ Bid Verification** (`/bid-verification`) - Automatically verify analysis reports and correct errors
3. **📝 Requirements Extraction** (`/bid-requirements`) - Extract detailed requirements from tender documents
4. **🏗️ Software Design** (`/bid-software-design`) - Generate software high-level and detailed design documents from requirement specifications
5. **💼 Commercial Proposal** (`/bid-commercial-proposal`) - Write complete commercial bid documents with all required attachments
6. **🔧 Technical Proposal** (`/bid-tech-proposal`) - Write complete technical bid documents
7. **📊 Mermaid Diagrams** (`/bid-mermaid-diagrams`) - Generate and replace diagram placeholders with rendered images
8. **🔍 Material Search** - ⚠️ **Migrated to [material-hub](https://github.com/youyouhe/material-hub)** (v3.0+ uses MCP architecture for 10x performance)
9. **📦 Material Extraction** (`/bid-material-extraction`) - Extract materials from company resource library
10. **🎯 Bid Assembly** (`/bid-assembly`) - Comprehensive quality check and generate verification report
11. **📄 MD to DOCX** (`/bid-md2doc`) - Convert markdown proposals to final Word documents
12. **🎭 Bid Manager** (`/bid-manager`) - Orchestrate the complete bid workflow end-to-end

## 📦 Installation

### Method 1: Command Line (Recommended - Easiest)

In Claude Code, run these commands:

```bash
# Add the marketplace
/plugin marketplace add youyouhe/bidsmart-claude-skills

# Install the plugin
/plugin install bidsmart-skills@bidsmart-skills
```

That's it! Restart Claude Code and all 12 skills will be available.

### Method 2: Manual Configuration

Add to your project's `.claude/settings.local.json`:

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

### Method 3: Local Development

Clone this repository and use local path:

```bash
git clone https://github.com/youyouhe/bidsmart-claude-skills.git
```

Add to `.claude/settings.local.json`:

```json
{
  "extraKnownMarketplaces": {
    "bidsmart-local": {
      "source": {
        "source": "directory",
        "path": "/path/to/bidsmart-claude-skills"
      }
    }
  },
  "enabledPlugins": {
    "bidsmart-skills@bidsmart-local": true
  }
}
```

Restart Claude Code to load the skills.

## 🚀 Usage

### Quick Start

```bash
# Start the complete workflow
/bid-manager

# Or use individual skills
/bid-analysis path/to/tender.pdf
/bid-requirements path/to/tender.docx
/bid-commercial-proposal
```

### Typical Workflow

13. **Analyze Tender Document**
   ```bash
   /bid-analysis tender.pdf
   ```
   - Extracts all requirements and scoring criteria
   - Generates structured outline

14. **Extract Requirements**
   ```bash
   /bid-requirements tender.pdf
   ```
   - Detailed technical and commercial requirements

15. **Write Proposals**
   ```bash
   /bid-tech-proposal
   /bid-commercial-proposal
   ```
   - Generates complete proposal documents based on analysis

16. **Generate Diagrams**
   ```bash
   /bid-mermaid-diagrams
   ```
   - Renders all mermaid diagram placeholders

17. **Assemble & Convert**
   ```bash
   /bid-assembly
   /bid-md2doc
   ```
   - Final quality check and Word document generation

## 📚 Skill Details

### Bid Analysis

Analyzes government procurement tender documents (competitive negotiation, public bidding, invitation to bid) and extracts:
- Scoring criteria and evaluation standards
- Technical requirements and specifications
- Commercial requirements and payment terms
- Qualification conditions
- Budget constraints
- Generates response document directory structure

**Triggers**: User provides tender/procurement document and requests analysis, requirement extraction, or bid outline generation.

### Bid Manager

Orchestrates the complete bid workflow by coordinating all other skills. Manages the end-to-end process from document analysis to final assembly.

**Triggers**: User wants complete bid management workflow or needs help coordinating multiple bid skills.

### ⚠️ Bid Material Search - Migrated

**bid-material-search** skill has been migrated to the [material-hub](https://github.com/youyouhe/material-hub) repository (v3.0+).

**Why migrated?**
- Tightly coupled with MaterialHub API and MCP server
- v3.0 uses MCP architecture (no FastAPI middleware) for 10x performance improvement
- Better maintained alongside MaterialHub infrastructure

**New location**: https://github.com/youyouhe/material-hub/tree/main/.claude/skills/bid-material-search

**For users**: The skill still works seamlessly in bid workflows when MaterialHub is available.

## 🛠️ Technical Details

### Dependencies

Some skills require additional services:
- **OCR Service**: For scanned PDF documents (optional, configurable via `OCR_SERVICE_URL`)
- **Python**: For PDF parsing and material extraction scripts
- **Node.js**: For Mermaid diagram rendering

### Directory Structure

```
bidsmart-claude-skills/
├── .claude-plugin/
│   └── marketplace.json          # Plugin marketplace definition
├── skills/
│   ├── bid-analysis/
│   │   ├── SKILL.md             # Skill definition
│   │   └── scripts/             # Helper scripts
│   ├── bid-verification/
│   ├── bid-requirements/
│   ├── bid-software-design/
│   ├── bid-commercial-proposal/
│   ├── bid-tech-proposal/
│   ├── bid-mermaid-diagrams/
│   ├── bid-material-extraction/
│   ├── bid-assembly/
│   ├── bid-md2doc/
│   ├── bid-manager/
│   └── bigmodel-ocr/
├── README.md
└── LICENSE

Note: bid-material-search migrated to material-hub repository
```

## 🌏 Language Support

All skills are designed for **Chinese government procurement** with:
- Chinese language support in prompts and outputs
- Understanding of Chinese tender document formats
- Compliance with Chinese procurement regulations
- Support for common Chinese document structures (Word, PDF)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by [everything-claude-code](https://github.com/affaan-m/everything-claude-code)
- Built for Claude Code by Anthropic

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Note**: These skills are optimized for Chinese government procurement workflows. For other use cases, you may need to adapt the prompts and workflows accordingly.
