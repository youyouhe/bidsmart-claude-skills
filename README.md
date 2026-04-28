# BidSmart Claude Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Skills Count](https://img.shields.io/badge/skills-26-blue)
![Version](https://img.shields.io/badge/version-1.1.0-green)

Comprehensive Claude Code skills for Chinese government procurement bid management **and web development**. This collection provides end-to-end automation for analyzing tender documents, writing proposals, assembling bid packages, and building complete websites from natural language descriptions.

## 🎯 Features

### Complete Bid Management Workflow (19 Skills)

1. **📋 Bid Analysis** (`/bid-analysis`) - Analyze tender documents (PDF/Word/Excel), extract scoring criteria, technical requirements, budget constraints
2. **🎯 Bid Evaluation** (`/bid-evaluation`) - Evaluate bid feasibility, auto-assess objective items, generate scoring sheets
3. **✅ Bid Verification** (`/bid-verification`) - Automatically verify analysis reports and correct errors
4. **📝 Requirements Extraction** (`/bid-requirements`) - Extract detailed requirements from tender documents
5. **🏗️ Software Design** (`/bid-software-design`) - Generate software high-level and detailed design documents
6. **💼 Commercial Proposal** (`/bid-commercial-proposal`) - Write complete commercial bid documents
7. **🔧 Technical Proposal** (`/bid-tech-proposal`) - Write complete technical bid documents
8. **📊 Mermaid Diagrams** (`/bid-mermaid-diagrams`) - Generate and render diagram placeholders to PNG
9. **🔍 Material Search** (`/bid-material-search`) - Search and retrieve materials from MaterialHub (v3.0: MCP架构，远程服务器，10x性能)
10. **📦 Material Extraction** (`/bid-material-extraction`) - Extract materials from company resource library
11. **🎯 Bid Assembly** (`/bid-assembly`) - Comprehensive quality check and verification report
12. **📄 MD to DOCX** (`/bid-md2doc`) - Convert markdown proposals to final Word documents
13. **🎭 Bid Manager** (`/bid-manager`) - Orchestrate the complete bid workflow end-to-end

### 🌐 Web Development Workflow (7 Skills) - NEW in v1.1.0

14. **🏗️ Web Builder Initial** (`/web-builder-initial`) - Generate complete single or multi-page websites from natural language descriptions
15. **🔄 Web Builder Update** (`/web-builder-update`) - Precision modifications and updates to existing web projects
16. **🎨 Design System Applier** (`/design-system-applier`) - Theme and color management with preset styles and gradients
17. **🖼️ Image Placeholder Guide** (`/image-placeholder-guide`) - Documentation for static.photos placeholder service
18. **✨ Project Namer** (`/project-namer`) - Creative project name generation with multiple style options
19. **🔖 Web Markers Parser** (`/web-markers-parser`) - BuildFlow marker extraction and data flow parsing
20. **📚 Web Prompt Categories** (`/web-prompt-categories`) - 60+ website template database with categorized prompts

## 📦 Installation

### Method 1: Command Line (Recommended - Easiest)

In Claude Code, run these commands:

```bash
# Add the marketplace
/plugin marketplace add youyouhe/bidsmart-claude-skills

# Install the plugin
/plugin install bidsmart-skills@bidsmart-skills
```

That's it! Restart Claude Code and all 26 skills will be available.

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

## 🔧 MaterialHub Configuration (Required for Material Search)

The `bid-material-search` skill requires a running MaterialHub API server. MaterialHub can run on the same machine (local) or on a remote server (client-server architecture).

### Server Setup

1. Clone and run MaterialHub:
   ```bash
   git clone https://github.com/youyouhe/material-hub.git
   cd material-hub
   pip install -r requirements.txt
   python backend/main.py
   ```

2. MaterialHub API will run on `http://localhost:8201`

### Client Configuration

Create a `.env` file in the `bidsmart-claude-skills` root directory:

**Local Development** (MaterialHub on the same machine):
```bash
MATERIALHUB_API_URL=http://localhost:8201
MATERIALHUB_API_KEY=mh-mcp-xxx...  # Copy from material-hub/.env
```

**Remote Server** (MaterialHub on a different machine):
```bash
MATERIALHUB_API_URL=http://192.168.1.100:8201  # Server IP
MATERIALHUB_API_KEY=mh-mcp-xxx...              # Copy from server
```

**Production (HTTPS)**:
```bash
MATERIALHUB_API_URL=https://materials.company.com
MATERIALHUB_API_KEY=mh-mcp-prod-key
```

### Test Connection

```bash
cd skills/bid-material-search
python test_skill.py
```

For detailed network configuration, see [NETWORK_CONFIG.md](skills/bid-material-search/NETWORK_CONFIG.md).

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

### Bid Management Workflow

1. **Analyze Tender Document**
   ```bash
   /bid-analysis tender.pdf
   ```
   - Extracts all requirements and scoring criteria
   - Generates structured outline

2. **Extract Requirements**
   ```bash
   /bid-requirements tender.pdf
   ```
   - Detailed technical and commercial requirements

3. **Write Proposals**
   ```bash
   /bid-tech-proposal
   /bid-commercial-proposal
   ```
   - Generates complete proposal documents based on analysis

4. **Generate Diagrams**
   ```bash
   /bid-mermaid-diagrams
   ```
   - Renders all mermaid diagram placeholders

5. **Assemble & Convert**
   ```bash
   /bid-assembly
   /bid-md2doc
   ```
   - Final quality check and Word document generation

### Web Development Workflow

1. **Create a New Website**
   ```bash
   /web-builder-initial "Build a modern portfolio website with hero section, 
   about page, and contact form. Use blue gradient theme."
   ```
   - Generates complete HTML structure
   - Applies design system automatically
   - Creates responsive layout

2. **Update Existing Website**
   ```bash
   /web-builder-update "Change the hero section background to purple gradient 
   and add a testimonials section"
   ```
   - Precision modifications without rebuilding
   - Preserves existing code structure

3. **Apply Design System**
   ```bash
   /design-system-applier blue-gradient
   ```
   - Apply preset themes (blue-gradient, purple-dream, sunset-glow, etc.)
   - Consistent color palette across entire site

4. **Browse Template Library**
   ```bash
   /web-prompt-categories
   ```
   - 60+ categorized website templates
   - Copy-paste ready prompts for common website types

## 📚 Skill Details

### Bid Management Skills

#### Bid Analysis
Analyzes government procurement tender documents (competitive negotiation, public bidding, invitation to bid) and extracts:
- Scoring criteria and evaluation standards
- Technical requirements and specifications
- Commercial requirements and payment terms
- Qualification conditions
- Budget constraints
- Generates response document directory structure

**Triggers**: User provides tender/procurement document and requests analysis, requirement extraction, or bid outline generation.

#### Bid Manager
Orchestrates the complete bid workflow by coordinating all other skills. Manages the end-to-end process from document analysis to final assembly.

**Triggers**: User wants complete bid management workflow or needs help coordinating multiple bid skills.

### Web Development Skills

#### Web Builder Initial
Generates complete single or multi-page websites from natural language descriptions. Supports various website types including portfolio, business, landing pages, e-commerce, documentation sites, and more.

**Triggers**: User requests to build/create a new website with specific requirements.

#### Web Builder Update
Precision modifications and updates to existing web projects. Maintains code structure while applying targeted changes.

**Triggers**: User requests to modify/update an existing website project.

#### Design System Applier
Theme and color management with 10+ preset styles (blue-gradient, purple-dream, sunset-glow, forest-green, ocean-breeze, etc.). Provides consistent design tokens across the entire project.

**Triggers**: User requests to apply a theme or change website colors.

#### Project Namer
Creative project name generation with multiple style options (professional, creative, tech-focused, playful). Generates meaningful names based on project description.

**Triggers**: User needs help naming a web project.

#### Web Prompt Categories
Database of 60+ categorized website template prompts across 10 categories (business, portfolio, e-commerce, SaaS, education, health, entertainment, community, utility, creative). Each category includes 6 ready-to-use prompts.

**Triggers**: User asks for website examples, templates, or inspiration.

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
