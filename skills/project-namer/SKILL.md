---
name: project-namer
description: >
  Generate creative, catchy project names with emojis for web projects.
  Uses BuildFlow's PROMPT_FOR_PROJECT_NAME template to create short (≤6 words),
  unique, and memorable names that reflect the project's purpose.

  Trigger conditions:
  - Called by web-builder-initial during project creation
  - User explicitly requests: "give this project a name", "命名这个项目"
  - Auto-generated when creating new web projects

  Inputs: Project description or user request
  Outputs: Project name (≤6 words) + emoji
---

# Project Namer - Creative Project Name Generation

## Overview

The `project-namer` skill generates **creative, memorable project names** for web projects using BuildFlow's proven naming prompt. This skill produces:
- **Short names**: ≤6 words for easy recall
- **Emoji suffix**: One emoji that represents the project theme
- **Creative flair**: Fancy, unique, and sometimes humorous names
- **Bilingual support**: Works for both English and Chinese project descriptions

## Core Principles

### 1. Name Characteristics
A good project name should be:
- **Short**: Maximum 6 words, ideally 2-4 words
- **Memorable**: Easy to remember and pronounce
- **Descriptive**: Reflects the project's purpose or theme
- **Unique**: Stands out from generic names
- **Emoji-enhanced**: One emoji that captures the essence

### 2. Naming Patterns

Common patterns that work well:

| Pattern | Example | When to Use |
|---------|---------|-------------|
| Adjective + Noun | Modern Dashboard 📊 | Professional projects |
| Action + Subject | Build Anywhere 🚀 | Tools and platforms |
| Metaphor | Pixel Perfect 🎨 | Creative projects |
| Compound Word | CodeCraft ⚡ | Tech projects |
| Alliteration | Portfolio Paradise 🌟 | Playful projects |

### 3. Emoji Selection Guidelines

Choose emojis that match the project theme:

| Project Type | Suitable Emojis | Examples |
|--------------|-----------------|----------|
| Portfolio/Personal | ✨ 🌟 🎨 🎯 | Creative Portfolio ✨ |
| Business/SaaS | 🚀 💼 📊 ⚡ | Smart Analytics 📊 |
| E-commerce | 🛍️ 🛒 💳 🏪 | Shop Haven 🛍️ |
| Blog/Content | 📝 📚 ✍️ 📖 | Write Away 📝 |
| Food/Restaurant | 🍕 🍔 🍜 🍰 | Tasty Bites 🍕 |
| Education | 📚 🎓 🧠 📖 | Learn Hub 🎓 |
| Health/Fitness | 💪 🏃 🧘 ❤️ | Fit Journey 💪 |
| Real Estate | 🏡 🏘️ 🏢 🔑 | Dream Homes 🏡 |
| Technology | ⚡ 🔧 💻 🤖 | Tech Sphere ⚡ |
| Finance | 💰 💳 📈 🏦 | Money Matters 💰 |

### 4. Multilingual Naming

**English projects**:
- Use English words, international terms
- Emoji at the end
- Example: "Creative Studio ✨"

**Chinese projects**:
- Use Chinese characters (usually 4-8 characters for ≤6 "words" concept)
- Emoji at the end
- Example: "智能作文批改系统 📝" (Smart Essay Grading System)

## System Prompts

### English Version (PROMPT_FOR_PROJECT_NAME)

```
REQUIRED: Generate a name for the project, based on the user's request.
Try to be creative and unique. Add a emoji at the end of the name.
It should be short, like 6 words. Be fancy, creative and funny.
DON'T FORGET IT, IT'S IMPORTANT!
```

### Chinese Version (PROMPT_FOR_PROJECT_NAME_ZH)

```
必需: 根据用户的请求为项目生成一个名称。
尽量富有创意和独特性。在名称末尾添加一个 emoji。
名称应该简短,大约6个词。要时尚、有创意且有趣味。
不要忘记,这很重要!
```

## Workflow

### Phase 1: Analyze Project Description

Extract key themes from project description:

```python
import re
from typing import TypedDict

class ProjectThemes(TypedDict):
    project_type: str | None    # 'portfolio', 'e-commerce', 'blog', etc.
    industry: str | None         # 'food', 'tech', 'health', etc.
    key_features: list[str]      # ['modern', 'responsive', 'fast']
    language: str                # 'en' or 'zh'

def analyze_project_description(description: str) -> ProjectThemes:
    """
    Analyze project description to extract themes for naming.

    Args:
        description: User's project description

    Returns:
        ProjectThemes dict with extracted information
    """
    themes: ProjectThemes = {
        'project_type': None,
        'industry': None,
        'key_features': [],
        'language': 'en' if re.search(r'[a-zA-Z]', description) else 'zh'
    }

    # Detect project type
    type_keywords = {
        'portfolio': ['portfolio', 'personal site', '作品集', '个人网站'],
        'e-commerce': ['shop', 'store', 'e-commerce', '商城', '购物'],
        'blog': ['blog', 'articles', 'writing', '博客', '文章'],
        'dashboard': ['dashboard', 'admin', 'analytics', '仪表盘', '控制台'],
        'landing': ['landing page', 'product page', '落地页', '产品页'],
        'restaurant': ['restaurant', 'menu', 'food', '餐厅', '菜单'],
        'education': ['education', 'learning', 'course', '教育', '学习', '课程']
    }

    for ptype, keywords in type_keywords.items():
        if any(keyword in description.lower() for keyword in keywords):
            themes['project_type'] = ptype
            break

    # Detect industry
    industry_keywords = {
        'tech': ['technology', 'software', 'app', '科技', '软件', '应用'],
        'food': ['food', 'restaurant', 'cafe', '美食', '餐厅', '咖啡'],
        'health': ['health', 'fitness', 'wellness', '健康', '健身'],
        'finance': ['finance', 'banking', 'investment', '金融', '银行', '投资'],
        'real-estate': ['real estate', 'property', 'housing', '房地产', '房产']
    }

    for industry, keywords in industry_keywords.items():
        if any(keyword in description.lower() for keyword in keywords):
            themes['industry'] = industry
            break

    # Extract key features (adjectives)
    feature_keywords = ['modern', 'simple', 'clean', 'elegant', 'fast', 'smart',
                       'innovative', 'creative', 'professional', 'minimal',
                       '现代', '简洁', '优雅', '快速', '智能', '创新', '专业']

    for keyword in feature_keywords:
        if keyword in description.lower():
            themes['key_features'].append(keyword)

    return themes
```

### Phase 2: Build Naming Context

Combine project description with naming prompt:

```python
def build_naming_prompt(description: str, themes: ProjectThemes) -> str:
    """
    Build complete prompt for LLM to generate project name.

    Args:
        description: Original project description
        themes: Extracted themes

    Returns:
        Complete prompt string
    """
    # Choose language-specific prompt
    if themes['language'] == 'zh':
        naming_instruction = """
必需: 根据用户的请求为项目生成一个名称。
尽量富有创意和独特性。在名称末尾添加一个 emoji。
名称应该简短,大约6个词。要时尚、有创意且有趣味。
不要忘记,这很重要!
"""
    else:
        naming_instruction = """
REQUIRED: Generate a name for the project, based on the user's request.
Try to be creative and unique. Add a emoji at the end of the name.
It should be short, like 6 words. Be fancy, creative and funny.
DON'T FORGET IT, IT'S IMPORTANT!
"""

    # Build context
    context = f"""
Project Description: {description}

Project Type: {themes['project_type'] or 'general web project'}
Industry: {themes['industry'] or 'general'}
Key Features: {', '.join(themes['key_features']) if themes['key_features'] else 'not specified'}

{naming_instruction}

Project Name:"""

    return context
```

### Phase 3: Generate Name

Call LLM with naming prompt:

```bash
#!/bin/bash
# generate_name.sh

PROJECT_DESC="$1"

# Analyze themes
THEMES=$(python3 << EOF
import sys
description = sys.stdin.read()
themes = analyze_project_description(description)
import json
print(json.dumps(themes))
EOF
)

# Build prompt
NAMING_PROMPT=$(python3 << EOF
import json
description = "$PROJECT_DESC"
themes = json.loads('$THEMES')
prompt = build_naming_prompt(description, themes)
print(prompt)
EOF
)

# Call LLM
PROJECT_NAME=$(call_llm "$NAMING_PROMPT")

# Extract name (remove any leading/trailing text)
# Expected format: "Project Name 🚀"
echo "$PROJECT_NAME" | sed 's/^.*: //' | head -n 1
```

### Phase 4: Validate and Refine

Ensure name meets criteria:

```python
import re

def validate_project_name(name: str) -> tuple[bool, list[str]]:
    """
    Validate that project name meets criteria.

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Check length (≤6 words)
    # For English: split by spaces
    # For Chinese: count characters (each character ~ 1 word)
    if re.search(r'[a-zA-Z]', name):  # English
        word_count = len(name.split())
        if word_count > 6:
            errors.append(f"Name too long: {word_count} words (max 6)")
    else:  # Chinese
        # Remove emoji and spaces for counting
        clean_name = re.sub(r'[\U00010000-\U0010ffff\s]+', '', name)
        if len(clean_name) > 12:  # ~6 words = ~12 chars in Chinese
            errors.append(f"Name too long: {len(clean_name)} characters (max ~12)")

    # Check for emoji
    has_emoji = bool(re.search(r'[\U00010000-\U0010ffff]', name))
    if not has_emoji:
        errors.append("Missing emoji at the end")

    # Check if empty
    if not name.strip():
        errors.append("Name is empty")

    return (len(errors) == 0, errors)


def extract_name_from_response(llm_response: str) -> str:
    """
    Extract clean project name from LLM response.

    Handles cases where LLM adds extra text like:
    - "Here's a name: My Project 🚀"
    - "Project Name: My Project 🚀"
    - "My Project 🚀 (This name reflects...)"
    """
    # Remove common prefixes
    response = re.sub(r'^.*(Project Name|Name|Here\'s|How about):\s*', '', llm_response, flags=re.IGNORECASE)

    # Take first line
    response = response.split('\n')[0].strip()

    # Remove trailing explanations in parentheses
    response = re.sub(r'\s*\([^)]+\)\s*$', '', response)

    # Remove quotes
    response = response.strip('"\'')

    return response.strip()
```

## Usage Examples

### Example 1: Simple Portfolio

**Input**:
```
Project description: "Create a personal portfolio website to showcase my design work"
```

**Themes extracted**:
```python
{
    'project_type': 'portfolio',
    'industry': None,
    'key_features': [],
    'language': 'en'
}
```

**Generated names** (examples):
- "Creative Portfolio ✨"
- "Design Showcase 🎨"
- "Pixel Perfect 🎯"
- "Work & Wonder 🌟"

### Example 2: E-commerce Platform

**Input**:
```
Project description: "Modern online store for selling handmade crafts"
```

**Themes extracted**:
```python
{
    'project_type': 'e-commerce',
    'industry': None,
    'key_features': ['modern'],
    'language': 'en'
}
```

**Generated names**:
- "Craft Haven 🛍️"
- "Modern Market 🏪"
- "Handmade Hub 🎁"
- "Artisan Alley ✨"

### Example 3: Chinese Educational Platform

**Input**:
```
Project description: "智能作文批改系统,帮助学生提高写作能力"
```

**Themes extracted**:
```python
{
    'project_type': 'education',
    'industry': None,
    'key_features': ['智能'],
    'language': 'zh'
}
```

**Generated names**:
- "智能作文批改系统 📝"
- "写作小助手 ✍️"
- "文章优化师 📖"
- "作文智库 🎓"

### Example 4: Restaurant Website

**Input**:
```
Project description: "Website for Italian restaurant with menu and reservations"
```

**Themes extracted**:
```python
{
    'project_type': 'restaurant',
    'industry': 'food',
    'key_features': [],
    'language': 'en'
}
```

**Generated names**:
- "Bella Tavola 🍝"
- "Pasta Paradise 🍕"
- "Trattoria Delight 🍷"
- "Italian Table 🇮🇹"

### Example 5: Tech Dashboard

**Input**:
```
Project description: "Analytics dashboard with real-time data visualization"
```

**Themes extracted**:
```python
{
    'project_type': 'dashboard',
    'industry': 'tech',
    'key_features': [],
    'language': 'en'
}
```

**Generated names**:
- "Data Pulse 📊"
- "Insight Engine ⚡"
- "Metrics Hub 📈"
- "Dashboard Pro 💻"

## Integration with web-builder-initial

The `web-builder-initial` skill calls `project-namer` during Phase 1:

```bash
# In web-builder-initial workflow (Phase 1)

# Generate project name
PROJECT_NAME=$(/skills/project-namer/generate.sh "$USER_REQUEST")

echo "📦 Generated project name: $PROJECT_NAME"

# Validate
VALIDATION=$(python3 << EOF
name = "$PROJECT_NAME"
is_valid, errors = validate_project_name(name)
import json
print(json.dumps({'valid': is_valid, 'errors': errors}))
EOF
)

IS_VALID=$(echo "$VALIDATION" | jq -r '.valid')

if [ "$IS_VALID" = "false" ]; then
    echo "⚠️  Name validation failed:"
    echo "$VALIDATION" | jq -r '.errors[]'

    # Retry with explicit reminder
    PROJECT_NAME=$(/skills/project-namer/generate.sh "$USER_REQUEST" --retry)
fi

# Use in PROJECT_NAME markers
echo "<<<<<<< PROJECT_NAME_START $PROJECT_NAME >>>>>>> PROJECT_NAME_END"
```

## Advanced Features

### Feature 1: Name Variations

Generate multiple name options and let user choose:

```python
def generate_name_variations(description: str, count: int = 5) -> list[str]:
    """
    Generate multiple name options for the same project.

    Args:
        description: Project description
        count: Number of variations to generate

    Returns:
        List of unique project names
    """
    names = []
    themes = analyze_project_description(description)

    for i in range(count):
        # Add variation hint to prompt
        variation_hint = f"(Variation {i+1}/{count} - be creative and different)"
        prompt = build_naming_prompt(description, themes) + variation_hint

        name = call_llm(prompt)
        name = extract_name_from_response(name)

        # Ensure uniqueness
        if name not in names:
            names.append(name)

    return names
```

**Usage**:
```python
description = "Modern SaaS platform for project management"
variations = generate_name_variations(description, count=5)

print("📋 Name Options:")
for i, name in enumerate(variations, 1):
    print(f"  {i}. {name}")

# Output:
# 📋 Name Options:
#   1. Project Pulse 🚀
#   2. Task Flow ⚡
#   3. Work Wave 📊
#   4. Synced Up 🔄
#   5. Team Nexus 💼
```

### Feature 2: Domain Name Check

Validate if .com domain is available:

```python
import socket

def check_domain_availability(project_name: str) -> tuple[bool, str]:
    """
    Check if .com domain is available for project name.

    Args:
        project_name: Project name with emoji (e.g., "My Project 🚀")

    Returns:
        (is_available, domain_name)
    """
    # Remove emoji and special chars
    clean_name = re.sub(r'[^\w\s-]', '', project_name)
    clean_name = clean_name.lower().strip()

    # Convert spaces to hyphens
    domain_name = clean_name.replace(' ', '-')
    domain_full = f"{domain_name}.com"

    try:
        # Try to resolve domain
        socket.gethostbyname(domain_full)
        # If successful, domain exists (not available)
        return (False, domain_full)
    except socket.gaierror:
        # Domain doesn't exist (available)
        return (True, domain_full)
```

**Usage**:
```python
project_name = "Creative Portfolio ✨"
is_available, domain = check_domain_availability(project_name)

if is_available:
    print(f"✅ Domain available: {domain}")
else:
    print(f"❌ Domain taken: {domain}")
    print(f"   Try: {domain.replace('.com', '-app.com')}")
```

### Feature 3: SEO-Friendly Name Suggestions

Optimize names for search engines:

```python
def generate_seo_friendly_name(description: str, keywords: list[str]) -> str:
    """
    Generate SEO-optimized project name that includes target keywords.

    Args:
        description: Project description
        keywords: Target SEO keywords (e.g., ['restaurant', 'italian', 'nyc'])

    Returns:
        SEO-friendly project name
    """
    themes = analyze_project_description(description)

    # Build SEO-focused prompt
    seo_prompt = f"""
{build_naming_prompt(description, themes)}

IMPORTANT: Include these keywords naturally in the name: {', '.join(keywords)}

SEO Guidelines:
- Use keywords early in the name
- Keep it descriptive
- Avoid generic terms
- Still be creative and memorable

Project Name:"""

    name = call_llm(seo_prompt)
    return extract_name_from_response(name)
```

**Usage**:
```python
description = "Restaurant website for Italian cuisine in New York"
keywords = ['italian', 'restaurant', 'nyc']

seo_name = generate_seo_friendly_name(description, keywords)
print(f"SEO Name: {seo_name}")
# Output: "Italian NYC Bistro 🍝"
```

### Feature 4: Brand Name Generator

Generate brand-style names (compound words, portmanteaus):

```python
def generate_brand_name(description: str) -> str:
    """
    Generate brand-style name using compound words or portmanteaus.

    Examples:
        - "creative" + "flow" → "CreativeFlow"
        - "smart" + "hub" → "SmartHub"
        - "pixel" + "forge" → "PixelForge"
    """
    themes = analyze_project_description(description)

    brand_prompt = f"""
{build_naming_prompt(description, themes)}

BRAND STYLE GUIDELINES:
- Create a single compound word (e.g., CodeCraft, PixelForge, DataPulse)
- OR use a short 2-word brand (e.g., Blue Ocean, Swift Lane)
- Use CamelCase for compound words
- Add ONE emoji that represents the brand

Examples:
- SaaS platform → CloudSync ☁️
- Design tool → PixelCraft 🎨
- Analytics → DataFlow 📊

Brand Name:"""

    name = call_llm(brand_prompt)
    return extract_name_from_response(name)
```

## Error Handling

### Error 1: Name Too Long

**Symptom**: Generated name exceeds 6 words

```python
def handle_name_too_long(name: str, description: str) -> str:
    """Retry with explicit length constraint."""
    retry_prompt = f"""
{build_naming_prompt(description, analyze_project_description(description))}

CRITICAL: The previous name "{name}" was TOO LONG.
Generate a SHORTER name with MAXIMUM 4 words.
Still add emoji at the end.

Shorter Project Name:"""

    new_name = call_llm(retry_prompt)
    return extract_name_from_response(new_name)
```

### Error 2: Missing Emoji

**Symptom**: Name doesn't include emoji

```python
def add_emoji_to_name(name: str, project_type: str) -> str:
    """Add appropriate emoji if missing."""
    emoji_map = {
        'portfolio': '✨',
        'e-commerce': '🛍️',
        'blog': '📝',
        'dashboard': '📊',
        'restaurant': '🍕',
        'education': '🎓',
        'default': '🚀'
    }

    emoji = emoji_map.get(project_type, emoji_map['default'])
    return f"{name.strip()} {emoji}"
```

### Error 3: Generic Name

**Symptom**: Name is too generic ("My Website", "Web App")

```python
def is_generic_name(name: str) -> bool:
    """Check if name is too generic."""
    generic_patterns = [
        r'\bmy\s+\w+\b',  # "My Website", "My App"
        r'\bweb\s*(site|app|page)\b',  # "Website", "Web App"
        r'\bproject\s+\d+\b',  # "Project 1"
        r'\b(test|demo|sample)\b',  # "Test Site", "Demo"
    ]

    name_lower = name.lower()
    return any(re.search(pattern, name_lower) for pattern in generic_patterns)


def regenerate_if_generic(name: str, description: str) -> str:
    """Regenerate if name is generic."""
    if is_generic_name(name):
        print(f"⚠️  Name too generic: {name}")
        print("   Regenerating with more creativity...")

        creative_prompt = f"""
{build_naming_prompt(description, analyze_project_description(description))}

AVOID generic terms like: "My Website", "Web App", "Project", "Test"
BE CREATIVE and UNIQUE. Think of metaphors, compound words, or interesting phrases.

Creative Project Name:"""

        new_name = call_llm(creative_prompt)
        return extract_name_from_response(new_name)

    return name
```

## Output Format

```
✅ Project Name Generated

📦 Name: Creative Portfolio ✨

📊 Analysis:
- Type: portfolio
- Industry: general
- Features: creative
- Language: English

📏 Validation:
- Length: 2 words ✅
- Emoji: ✅ (✨)
- Uniqueness: High
- SEO Score: 7/10

💡 Domain Suggestions:
- creative-portfolio.com (available ✅)
- creativepf.com (available ✅)
- getportfolio.com (taken ❌)
```

## Verification Checklist

- [ ] Name is ≤6 words (or ≤12 chars for Chinese)
- [ ] Emoji present at the end
- [ ] Name is unique (not generic like "My Website")
- [ ] Name reflects project purpose
- [ ] Language matches project description (EN/ZH)
- [ ] No special characters except emoji
- [ ] Easy to pronounce and remember
- [ ] Not overly similar to existing brands

---

**Implementation Status**: ✅ Complete - Ready for use
**BuildFlow Source**: `/mnt/oldroot/home/bird/buildflow/lib/prompts.ts` line 27, 407
**Dependencies**: LLM API for name generation
**Called By**: `web-builder-initial` (Phase 1)
**Last Updated**: 2026-03-30
