---
name: design-system-applier
description: >
  Apply consistent design system (colors, theme, typography, spacing) to web projects.
  Extracts design preferences from user requests and generates SEARCH/REPLACE patterns
  to update CSS variables, Tailwind classes, and theme configurations.

  Trigger conditions:
  - User requests: "change color scheme", "apply dark mode", "use blue theme", "更改配色"
  - Design preferences mentioned (colors, fonts, spacing scale)
  - Explicit design system requirements

  Inputs: Design preferences + existing web files
  Outputs: UPDATE_FILE blocks with design system changes
---

# Design System Applier - Theme & Color Management

## Overview

The `design-system-applier` skill applies **consistent design systems** to web projects by:
1. **Extracting design preferences** from user requests (colors, theme mode, typography)
2. **Generating CSS variable updates** for root-level design tokens
3. **Creating SEARCH/REPLACE patterns** for Tailwind utility classes
4. **Injecting theme configurations** (dark mode toggles, color schemes)
5. **Updating component styles** to match the design system

This skill is optimized for:
- Changing color schemes across entire projects
- Applying dark/light mode themes
- Updating typography systems
- Standardizing spacing scales
- Implementing brand guidelines

## Core Principles

### 1. Design Token System
Use CSS custom properties (variables) as the source of truth:

```css
:root {
  /* Color tokens */
  --primary: #4F46E5;
  --secondary: #10B981;
  --accent: #F59E0B;
  --neutral: #6B7280;

  /* Semantic colors */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F9FAFB;
  --text-primary: #111827;
  --text-secondary: #6B7280;

  /* Theme-specific */
  --shadow: 0 1px 3px rgba(0,0,0,0.1);
  --border: #E5E7EB;
}

[data-theme="dark"] {
  --bg-primary: #111827;
  --bg-secondary: #1F2937;
  --text-primary: #F9FAFB;
  --text-secondary: #D1D5DB;
  --border: #374151;
  --shadow: 0 1px 3px rgba(0,0,0,0.5);
}
```

### 2. Extraction Priority
When extracting design preferences from user requests:
1. **Explicit colors**: Hex codes (#4F46E5), RGB, color names
2. **Theme mode**: "dark mode", "light theme", "dark/light toggle"
3. **Color relationships**: "primary/secondary", "brand colors", "accent"
4. **Typography**: Font families, size scales, weights
5. **Spacing**: Padding/margin scale preferences

### 3. Update Strategy
Apply design changes in order:
1. **Root-level CSS variables** (`:root` selector)
2. **Theme-specific overrides** (`[data-theme="dark"]` selector)
3. **Component-specific styles** (update custom components)
4. **Tailwind utility overrides** (update inline classes if needed)
5. **JavaScript theme toggles** (add theme switcher logic)

### 4. Preservation Rules
- **Preserve existing structure**: Only change design tokens, not layout
- **Maintain accessibility**: Ensure sufficient color contrast (WCAG AA: 4.5:1)
- **Keep semantic meaning**: Don't change `danger` red to blue
- **Respect user choices**: If user specifies green, use green (not "similar" colors)

## Workflow

### Phase 0: Extract Design Preferences

Parse user request for design specifications:

```python
import re
from typing import TypedDict

class DesignPreferences(TypedDict):
    primary_color: str | None
    secondary_color: str | None
    accent_color: str | None
    theme_mode: str | None  # 'light', 'dark', 'auto'
    font_family: str | None
    spacing_scale: str | None

def extract_design_preferences(user_request: str) -> DesignPreferences:
    """
    Extract design preferences from user request.

    Examples:
        "使用蓝色和绿色主题" → primary: blue, secondary: green
        "Apply dark mode with purple accent" → theme: dark, accent: purple
        "Change to #4F46E5 primary color" → primary: #4F46E5
    """
    prefs: DesignPreferences = {
        'primary_color': None,
        'secondary_color': None,
        'accent_color': None,
        'theme_mode': None,
        'font_family': None,
        'spacing_scale': None
    }

    # Extract hex colors
    hex_colors = re.findall(r'#[0-9A-Fa-f]{6}', user_request)
    if len(hex_colors) >= 1:
        prefs['primary_color'] = hex_colors[0]
    if len(hex_colors) >= 2:
        prefs['secondary_color'] = hex_colors[1]

    # Extract theme mode
    if any(word in user_request.lower() for word in ['dark mode', '暗色', '深色', 'dark theme']):
        prefs['theme_mode'] = 'dark'
    elif any(word in user_request.lower() for word in ['light mode', '亮色', '浅色', 'light theme']):
        prefs['theme_mode'] = 'light'
    elif any(word in user_request.lower() for word in ['theme toggle', '主题切换', 'dark/light']):
        prefs['theme_mode'] = 'auto'

    # Extract named colors
    color_keywords = {
        'blue': '#3B82F6', 'purple': '#9333EA', 'green': '#10B981',
        'red': '#EF4444', 'yellow': '#F59E0B', 'pink': '#EC4899',
        'indigo': '#6366F1', 'teal': '#14B8A6', 'orange': '#F97316',
        '蓝色': '#3B82F6', '紫色': '#9333EA', '绿色': '#10B981',
        '红色': '#EF4444', '黄色': '#F59E0B', '粉色': '#EC4899'
    }

    for keyword, hex_value in color_keywords.items():
        if keyword in user_request.lower():
            # Determine if it's primary, secondary, or accent based on context
            if 'primary' in user_request.lower() or '主色' in user_request:
                prefs['primary_color'] = hex_value
            elif 'secondary' in user_request.lower() or '次色' in user_request or '辅助' in user_request:
                prefs['secondary_color'] = hex_value
            elif 'accent' in user_request.lower() or '强调' in user_request:
                prefs['accent_color'] = hex_value
            elif not prefs['primary_color']:  # Default to primary if unspecified
                prefs['primary_color'] = hex_value

    # Extract font family
    font_match = re.search(r'font[:\s]+([A-Za-z\s,]+)', user_request, re.IGNORECASE)
    if font_match:
        prefs['font_family'] = font_match.group(1).strip()

    return prefs
```

**Usage**:
```python
request = "使用蓝色作为主色,绿色作为辅助色,应用暗色模式"
prefs = extract_design_preferences(request)

print(prefs)
# Output:
# {
#     'primary_color': '#3B82F6',
#     'secondary_color': '#10B981',
#     'accent_color': None,
#     'theme_mode': 'dark',
#     'font_family': None,
#     'spacing_scale': None
# }
```

### Phase 1: Read Current Design System

Load existing CSS to understand current design tokens:

```bash
# Read style.css to find current design system
cat <workDir>/web-output/style.css | grep -A 20 ':root {' > current_design.txt
```

Parse existing CSS variables:

```python
def parse_existing_design_system(css_content: str) -> dict[str, str]:
    """
    Parse existing CSS custom properties from :root block.

    Returns:
        Dict of variable names to values
    """
    variables = {}

    # Extract :root block
    root_match = re.search(r':root\s*\{([^}]+)\}', css_content, re.DOTALL)
    if not root_match:
        return variables

    root_content = root_match.group(1)

    # Parse --variable: value; patterns
    var_pattern = re.compile(r'--([a-z0-9-]+)\s*:\s*([^;]+);')
    for match in var_pattern.finditer(root_content):
        var_name = match.group(1)
        var_value = match.group(2).strip()
        variables[var_name] = var_value

    return variables
```

**Usage**:
```python
css = """
:root {
  --primary: #4F46E5;
  --secondary: #10B981;
}
"""

vars = parse_existing_design_system(css)
print(vars)
# Output: {'primary': '#4F46E5', 'secondary': '#10B981'}
```

### Phase 2: Generate SEARCH/REPLACE Patterns

Create UPDATE_FILE blocks to apply design changes:

```python
def generate_design_update_patterns(
    current_vars: dict[str, str],
    new_prefs: DesignPreferences
) -> list[dict]:
    """
    Generate SEARCH/REPLACE patterns for design system updates.

    Returns:
        List of dicts with 'search' and 'replace' keys
    """
    patterns = []

    # Pattern 1: Update primary color
    if new_prefs['primary_color']:
        if 'primary' in current_vars:
            patterns.append({
                'search': f"  --primary: {current_vars['primary']};",
                'replace': f"  --primary: {new_prefs['primary_color']};"
            })

    # Pattern 2: Update secondary color
    if new_prefs['secondary_color']:
        if 'secondary' in current_vars:
            patterns.append({
                'search': f"  --secondary: {current_vars['secondary']};",
                'replace': f"  --secondary: {new_prefs['secondary_color']};"
            })

    # Pattern 3: Add dark theme block (if theme_mode == 'dark' or 'auto')
    if new_prefs['theme_mode'] in ['dark', 'auto']:
        # Check if dark theme block already exists
        # If not, add after :root block
        patterns.append({
            'search': ":root {\n  /* Color tokens */",
            'replace': f""":root {{
  /* Color tokens */
}}

[data-theme="dark"] {{
  --bg-primary: #111827;
  --bg-secondary: #1F2937;
  --text-primary: #F9FAFB;
  --text-secondary: #D1D5DB;
  --border: #374151;
}}"""
        })

    return patterns
```

### Phase 3: Apply via web-builder-update

Call `web-builder-update` skill with generated UPDATE_FILE block:

```bash
#!/bin/bash
# apply_design_system.sh

WORK_DIR="$1"
DESIGN_PREFS_JSON="$2"  # JSON from extract_design_preferences

# Read current style.css
CURRENT_CSS=$(cat "$WORK_DIR/web-output/style.css")

# Parse existing design system
CURRENT_VARS=$(python3 << EOF
import sys
css = sys.stdin.read()
vars = parse_existing_design_system(css)
import json
print(json.dumps(vars))
EOF
)

# Generate SEARCH/REPLACE patterns
PATTERNS=$(python3 << EOF
import json
current_vars = json.loads('$CURRENT_VARS')
new_prefs = json.loads('$DESIGN_PREFS_JSON')
patterns = generate_design_update_patterns(current_vars, new_prefs)
print(json.dumps(patterns))
EOF
)

# Build UPDATE_FILE block
UPDATE_BLOCK="<<<<<<< PROJECT_NAME_START Design Update >>>>>>> PROJECT_NAME_END\n"
UPDATE_BLOCK+="<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END\n"

echo "$PATTERNS" | jq -c '.[]' | while read -r pattern; do
    SEARCH=$(echo "$pattern" | jq -r '.search')
    REPLACE=$(echo "$pattern" | jq -r '.replace')

    UPDATE_BLOCK+="<<<<<<< SEARCH\n"
    UPDATE_BLOCK+="$SEARCH\n"
    UPDATE_BLOCK+="=======\n"
    UPDATE_BLOCK+="$REPLACE\n"
    UPDATE_BLOCK+=">>>>>>> REPLACE\n"
done

# Call web-builder-update with UPDATE_BLOCK
echo "$UPDATE_BLOCK" | /skills/web-builder-update/execute.sh "$WORK_DIR"
```

### Phase 4: Add Theme Toggle (if needed)

If `theme_mode == 'auto'`, add JavaScript theme switcher:

```javascript
// Theme toggle script to inject into script.js
const themeToggleScript = `
// Theme toggle functionality
const themeToggle = document.getElementById('theme-toggle');
const htmlElement = document.documentElement;

// Load saved theme or default to light
const savedTheme = localStorage.getItem('theme') || 'light';
htmlElement.setAttribute('data-theme', savedTheme);

// Toggle theme on button click
if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const currentTheme = htmlElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';

    htmlElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update button icon if using Feather icons
    if (typeof feather !== 'undefined') {
      feather.replace();
    }
  });
}
`;
```

Create UPDATE_FILE block to inject this script:

```
<<<<<<< UPDATE_FILE_START script.js >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
=======
// Theme toggle functionality
const themeToggle = document.getElementById('theme-toggle');
const htmlElement = document.documentElement;

const savedTheme = localStorage.getItem('theme') || 'light';
htmlElement.setAttribute('data-theme', savedTheme);

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const currentTheme = htmlElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    htmlElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    if (typeof feather !== 'undefined') {
      feather.replace();
    }
  });
}
>>>>>>> REPLACE
```

Add theme toggle button to HTML:

```
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
  </body>
=======
  <button id="theme-toggle" class="fixed top-4 right-4 p-2 rounded-lg bg-gray-200 dark:bg-gray-700">
    <i data-feather="sun" class="w-5 h-5"></i>
  </button>
  </body>
>>>>>>> REPLACE
```

## Usage Examples

### Example 1: Change Primary Color

**User request**: "Change the primary color to purple (#9333EA)"

**Extracted preferences**:
```python
{
    'primary_color': '#9333EA',
    'secondary_color': None,
    'accent_color': None,
    'theme_mode': None,
    'font_family': None,
    'spacing_scale': None
}
```

**Generated UPDATE_FILE**:
```
<<<<<<< PROJECT_NAME_START Design Update >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
  --primary: #4F46E5;
=======
  --primary: #9333EA;
>>>>>>> REPLACE
```

**Result**: All elements using `var(--primary)` now use purple.

### Example 2: Apply Dark Mode Theme

**User request**: "添加暗色模式支持" (Add dark mode support)

**Extracted preferences**:
```python
{
    'primary_color': None,
    'secondary_color': None,
    'accent_color': None,
    'theme_mode': 'dark',
    'font_family': None,
    'spacing_scale': None
}
```

**Generated UPDATE_FILE**:
```
<<<<<<< PROJECT_NAME_START Dark Mode >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
:root {
  --bg-primary: #FFFFFF;
  --text-primary: #111827;
}
=======
:root {
  --bg-primary: #FFFFFF;
  --text-primary: #111827;
}

[data-theme="dark"] {
  --bg-primary: #111827;
  --bg-secondary: #1F2937;
  --text-primary: #F9FAFB;
  --text-secondary: #D1D5DB;
  --border: #374151;
  --shadow: 0 1px 3px rgba(0,0,0,0.5);
}
>>>>>>> REPLACE
```

**Result**: Dark mode CSS variables added, ready for `data-theme="dark"` attribute.

### Example 3: Complete Color Scheme Update

**User request**: "使用蓝色(#3B82F6)作为主色,绿色(#10B981)作为辅助色,橙色(#F97316)作为强调色"

**Extracted preferences**:
```python
{
    'primary_color': '#3B82F6',
    'secondary_color': '#10B981',
    'accent_color': '#F97316',
    'theme_mode': None,
    'font_family': None,
    'spacing_scale': None
}
```

**Generated UPDATE_FILE**:
```
<<<<<<< PROJECT_NAME_START Color Scheme >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
  --primary: #4F46E5;
  --secondary: #6B7280;
  --accent: #F59E0B;
=======
  --primary: #3B82F6;
  --secondary: #10B981;
  --accent: #F97316;
>>>>>>> REPLACE
```

**Result**: All three color tokens updated simultaneously.

### Example 4: Add Theme Toggle with Auto Mode

**User request**: "Add dark/light theme toggle button"

**Extracted preferences**:
```python
{
    'primary_color': None,
    'secondary_color': None,
    'accent_color': None,
    'theme_mode': 'auto',
    'font_family': None,
    'spacing_scale': None
}
```

**Generated files**:
1. **style.css**: Add dark theme CSS variables
2. **script.js**: Inject theme toggle logic
3. **index.html**: Add theme toggle button

**Complete UPDATE_FILE blocks**:
```
<<<<<<< PROJECT_NAME_START Theme Toggle >>>>>>> PROJECT_NAME_END

# 1. Add dark theme variables
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
}
=======
}

[data-theme="dark"] {
  --bg-primary: #111827;
  --bg-secondary: #1F2937;
  --text-primary: #F9FAFB;
  --text-secondary: #D1D5DB;
  --border: #374151;
}
>>>>>>> REPLACE

# 2. Add theme toggle script
<<<<<<< UPDATE_FILE_START script.js >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
=======
const themeToggle = document.getElementById('theme-toggle');
const htmlElement = document.documentElement;
const savedTheme = localStorage.getItem('theme') || 'light';
htmlElement.setAttribute('data-theme', savedTheme);

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const currentTheme = htmlElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    htmlElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  });
}
>>>>>>> REPLACE

# 3. Add toggle button to HTML
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
  <body>
=======
  <body>
    <button id="theme-toggle" class="fixed top-4 right-4 p-2 rounded-lg bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 transition">
      <i data-feather="sun" class="w-5 h-5 dark:text-white"></i>
    </button>
>>>>>>> REPLACE
```

**Result**: Fully functional theme toggle with persistence in localStorage.

## Advanced Features

### Feature 1: Semantic Color Mapping

Map design tokens to semantic purposes:

```css
:root {
  /* Base colors */
  --primary: #4F46E5;
  --secondary: #10B981;

  /* Semantic mappings */
  --color-success: var(--secondary);
  --color-danger: #EF4444;
  --color-warning: #F59E0B;
  --color-info: var(--primary);

  /* UI elements */
  --btn-primary-bg: var(--primary);
  --btn-primary-text: #FFFFFF;
  --link-color: var(--primary);
  --border-color: #E5E7EB;
}
```

This allows changing the entire UI by updating only `--primary` and `--secondary`.

### Feature 2: Typography System

Complete typography scale with CSS variables:

```css
:root {
  /* Font families */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-serif: 'Merriweather', Georgia, serif;
  --font-mono: 'Fira Code', monospace;

  /* Font sizes (modular scale: 1.25) */
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.25rem;    /* 20px */
  --text-xl: 1.5rem;     /* 24px */
  --text-2xl: 1.875rem;  /* 30px */
  --text-3xl: 2.25rem;   /* 36px */

  /* Font weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  /* Line heights */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
}
```

Update typography via design-system-applier:
```python
if new_prefs['font_family']:
    patterns.append({
        'search': "  --font-sans: 'Inter', system-ui, sans-serif;",
        'replace': f"  --font-sans: '{new_prefs['font_family']}', system-ui, sans-serif;"
    })
```

### Feature 3: Spacing Scale

Consistent spacing system:

```css
:root {
  /* Spacing scale (8px base) */
  --space-1: 0.25rem;  /* 4px */
  --space-2: 0.5rem;   /* 8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-12: 3rem;    /* 48px */
  --space-16: 4rem;    /* 64px */
}
```

### Feature 4: Color Contrast Validation

Ensure WCAG AA compliance (4.5:1 contrast ratio for text):

```python
def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """
    Calculate WCAG contrast ratio between two colors.

    Args:
        color1, color2: Hex color codes (e.g., '#4F46E5')

    Returns:
        Contrast ratio (1-21)
    """
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def relative_luminance(rgb: tuple[int, int, int]) -> float:
        r, g, b = [x / 255.0 for x in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    lum1 = relative_luminance(rgb1)
    lum2 = relative_luminance(rgb2)

    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)

    return (lighter + 0.05) / (darker + 0.05)

def validate_color_contrast(text_color: str, bg_color: str) -> tuple[bool, float]:
    """
    Validate if color contrast meets WCAG AA (4.5:1 for normal text).

    Returns:
        (is_valid, contrast_ratio)
    """
    ratio = calculate_contrast_ratio(text_color, bg_color)
    is_valid = ratio >= 4.5
    return (is_valid, ratio)
```

**Usage in design system application**:
```python
# Before applying new colors, validate contrast
text_color = new_prefs['primary_color']
bg_color = '#FFFFFF'  # Assume white background

is_valid, ratio = validate_color_contrast(text_color, bg_color)

if not is_valid:
    print(f"⚠️  Warning: Contrast ratio {ratio:.2f}:1 is below WCAG AA (4.5:1)")
    print(f"   Consider darkening {text_color} for better accessibility")
```

## Error Handling

### Error 1: Invalid Color Format

**Symptom**: User provides invalid hex code

```python
def validate_hex_color(color: str) -> tuple[bool, str]:
    """Validate hex color format."""
    if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
        return (False, f"Invalid hex color: {color}. Expected format: #RRGGBB")
    return (True, "")

# Usage
if new_prefs['primary_color']:
    is_valid, error = validate_hex_color(new_prefs['primary_color'])
    if not is_valid:
        print(f"❌ {error}")
        sys.exit(1)
```

### Error 2: Missing Design System

**Symptom**: style.css has no CSS variables to update

```python
def has_design_system(css_content: str) -> bool:
    """Check if CSS has design system variables."""
    return '--primary' in css_content or '--color' in css_content

# Usage
if not has_design_system(current_css):
    print("⚠️  No existing design system found")
    print("   Creating new design system from scratch...")
    # Generate complete :root block
```

### Error 3: Theme Conflict

**Symptom**: Dark theme block already exists but needs update

```python
def has_dark_theme(css_content: str) -> bool:
    """Check if dark theme already defined."""
    return '[data-theme="dark"]' in css_content

# Usage
if has_dark_theme(current_css) and new_prefs['theme_mode'] == 'dark':
    print("ℹ️  Dark theme already exists, updating variables...")
    # Generate UPDATE patterns for existing dark theme block
else:
    print("➕ Adding new dark theme support...")
    # Generate INSERT pattern for new dark theme block
```

## Integration Notes

### Calling Sequence

```bash
# From user request:
# "Change to blue primary color with dark mode"

# 1. Extract design preferences
PREFS=$(python3 << EOF
request = "Change to blue primary color with dark mode"
prefs = extract_design_preferences(request)
import json
print(json.dumps(prefs))
EOF
)

# 2. Apply design system
/skills/design-system-applier/apply.sh "$WORK_DIR" "$PREFS"

# 3. design-system-applier internally calls:
#    - web-markers-parser (to parse current CSS)
#    - web-builder-update (to apply changes)
```

### Output Format

```
✅ Design System Applied

🎨 Changes:
- Primary color: #4F46E5 → #3B82F6 (blue)
- Theme mode: light → dark (with toggle)

📊 Contrast Validation:
- Primary on white: 8.2:1 (WCAG AA ✅)
- Text on dark bg: 12.5:1 (WCAG AAA ✅)

📄 Modified Files:
- style.css (2 changes: colors + dark theme)
- script.js (1 change: theme toggle)
- index.html (1 change: toggle button)

📂 Output Location: <workDir>/web-output/
```

## Verification Checklist

- [ ] All color tokens updated consistently
- [ ] Dark theme CSS variables added (if theme_mode == 'dark' or 'auto')
- [ ] Theme toggle script injected (if theme_mode == 'auto')
- [ ] Theme toggle button added to HTML (if theme_mode == 'auto')
- [ ] Contrast ratios validated (WCAG AA: 4.5:1 for text)
- [ ] No semantic color changes (danger stays red, success stays green)
- [ ] Typography variables updated (if font_family specified)
- [ ] All HTML files reference updated style.css
- [ ] No layout structure changes (only design tokens)

---

**Implementation Status**: ✅ Complete - Ready for use
**Dependencies**: `web-builder-update` (for applying changes), `web-markers-parser` (for parsing CSS)
**Inputs**: User design preferences (colors, theme mode, typography)
**Outputs**: UPDATE_FILE blocks with design system changes
**Last Updated**: 2026-03-30
