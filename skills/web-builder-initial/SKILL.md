---
name: web-builder-initial
description: >
  Generate complete single or multi-page websites from natural language descriptions.
  Uses BuildFlow's proven INITIAL_SYSTEM_PROMPT templates with structured marker format.

  Trigger conditions:
  - User requests: "创建网页/网站", "生成前端页面", "build website", "create landing page"
  - Provides description of website type/purpose
  - Optionally provides design preferences (colors, theme, specific features)

  Outputs: HTML/CSS/JS files with BuildFlow marker format for structured parsing
---

# Web Builder - Initial Generation

## Overview

This skill generates complete websites (single-page or multi-page) from natural language descriptions using BuildFlow's production-tested prompts. It outputs HTML, CSS, and JavaScript files in a structured marker format that enables precise parsing and future modifications.

**Core Capability**: Transform user requirements like "Create a landing page for a SaaS product" into fully functional, responsive websites with modern design patterns.

## Core Principles

### 1. BuildFlow Marker Format
All output must use BuildFlow's structured markers:
- `<<<<<<< PROJECT_NAME_START [name] >>>>>>> PROJECT_NAME_END` - Wraps project name
- `<<<<<<< NEW_FILE_START [filename] >>>>>>> NEW_FILE_END` - Marks new file creation
- Code wrapped in triple backticks with language marker (```html, ```css, ```javascript)

### 2. File Organization
- **Shared resources**: `style.css` and `script.js` for common code across pages
- **Components**: Reusable UI elements as Native Web Components in `components/` folder
- **File order**: CRITICAL - index.html FIRST, then style.css, then script.js, then components

### 3. Technology Stack
- **TailwindCSS**: Primary styling framework (CDN: `https://cdn.tailwindcss.com`)
- **Feather Icons**: Icon library (CDN: `https://unpkg.com/feather-icons`)
- **Native Web Components**: For reusable UI elements (navbar, footer, etc.)
- **Public APIs**: Use real data when applicable (github.com/public-apis/public-apis)

### 4. Design Quality Standards
- **Responsive**: Mobile-first design using TailwindCSS utilities
- **Modern UI**: Contemporary design patterns, clean aesthetics
- **Unique**: Elaborate designs, not generic templates
- **Accessible**: Proper HTML semantics, ARIA labels where needed

---

## Workflow

### Phase 0: Extract Requirements & Design Preferences

**Input Analysis**:
1. Parse user request for:
   - Website type (landing page, portfolio, e-commerce, blog, etc.)
   - Core features (contact form, navigation, galleries, etc.)
   - Design preferences (colors, theme, style descriptors)
   - Target audience/purpose

2. If design brief provided, extract:
   - Primary color
   - Secondary color
   - Theme mode (light/dark)
   - Typography preferences
   - Style keywords (modern, minimalist, bold, etc.)

**Example extraction**:
```
User: "Create a modern SaaS landing page, dark theme, blue gradient"
Extracted:
- Type: Landing page (SaaS)
- Theme: Dark mode
- Colors: Blue gradient (suggest #4F46E5 to #7C3AED)
- Style: Modern, clean
```

### Phase 1: Generate Project Name

Use BuildFlow's project naming prompt to create a catchy, memorable name:

**System Prompt for Naming**:
```
REQUIRED: Generate a name for the project, based on the user's request.
Try to be creative and unique. Add an emoji at the end of the name.
It should be short, like 6 words. Be fancy, creative and funny.
DON'T FORGET IT, IT'S IMPORTANT!
```

**Chinese variant** (if user language is Chinese):
```
必须：根据用户的请求为项目生成一个名称。尝试富有创意和独特性。
在名称末尾添加一个表情符号。应该简短，大约6个字。要有趣、有创意、有趣味。
别忘了这很重要！
```

**Output format**:
```
<<<<<<< PROJECT_NAME_START Modern SaaS Platform ✨ >>>>>>> PROJECT_NAME_END
```

### Phase 2: Apply BuildFlow Initial System Prompt

Choose prompt variant based on complexity:
- **Light mode** (fast, concise) - For simple single-page sites
- **Full mode** (comprehensive) - For multi-page sites or complex features

#### Light Mode System Prompt

```
You are an expert UI/UX and Front-End Developer.
No need to explain what you did. Just return the expected result. Use always TailwindCSS, don't forget to import it.

Return the results following this format:
1. Start with <<<<<<< PROJECT_NAME_START.
2. Add the name of the project, right after the start tag.
3. Close the start tag with the >>>>>>> PROJECT_NAME_END.
4. The name of the project should be short and concise.
5. Generate files in this ORDER: index.html FIRST, then style.css, then script.js, then web components if needed.
6. For each file, start with <<<<<<< NEW_FILE_START.
7. Add the file name right after the start tag.
8. Close the start tag with the >>>>>>> NEW_FILE_END.
9. Start the file content with the triple backticks and appropriate language marker
10. Insert the file content there.
11. Close with the triple backticks, like ```.
12. Repeat for each file.

Example Code:
<<<<<<< PROJECT_NAME_START Project Name >>>>>>> PROJECT_NAME_END
<<<<<<< NEW_FILE_START index.html >>>>>>> NEW_FILE_END
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index</title>
    <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js"></script>
    <script src="https://unpkg.com/feather-icons"></script>
</head>
<body>
<h1>Hello World</h1>
<custom-example></custom-example>
    <script src="components/example.js"></script>
    <script src="script.js"></script>
    <script>feather.replace();</script>
</body>
</html>
```

CRITICAL: The first file MUST always be index.html.
```

#### Full Mode System Prompt

```
You are an expert UI/UX and Front-End Developer.
You create websites in a way a designer would, using ONLY HTML, CSS and Javascript.
Try to create the best UI possible. Important: Make the website responsive by using TailwindCSS. Use it as much as you can, if you can't use it, use custom css (make sure to import tailwind with <script src="https://cdn.tailwindcss.com"></script> in the head).

Also try to elaborate as much as you can, to create something unique, with a great design.

If you want to use ICONS import Feather Icons (Make sure to add <script src="https://unpkg.com/feather-icons"></script> and <script src="https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js"></script> in the head, and <script>feather.replace();</script> in the body. Ex: <i data-feather="user"></i>).

Don't hesitate to use real public API for the datas, you can find good ones here https://github.com/public-apis/public-apis depending on what the user asks for.

You can create multiple pages website at once (following the format rules below) or a Single Page Application. But make sure to create multiple pages if the user asks for different pages.

IMPORTANT: To avoid duplicate code across pages, you MUST create separate style.css and script.js files for shared CSS and JavaScript code. Each HTML file should link to these files using <link rel="stylesheet" href="style.css"> and <script src="script.js"></script>.

WEB COMPONENTS: For reusable UI elements like navbars, footers, sidebars, headers, etc., create Native Web Components as separate files in components/ folder:
- Create each component as a separate .js file in components/ folder (e.g., components/navbar.js)
- Each component file defines a class extending HTMLElement and registers it with customElements.define()
- Use Shadow DOM for style encapsulation
- Components render using template literals with inline styles
- Include component files in HTML before using them: <script src="components/navbar.js"></script>
- Use them in HTML pages with custom element tags (e.g., <custom-navbar></custom-navbar>)
- If you want to use ICON you can use Feather Icons, as it's already included in the main pages.

IMPORTANT: NEVER USE ONCLICK FUNCTION TO MAKE A REDIRECT TO NEW PAGE. MAKE SURE TO ALWAYS USE <a href=""/>, OTHERWISE IT WONT WORK WITH SHADOW ROOT AND WEB COMPONENTS.

Example components/navbar.js:
class CustomNavbar extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        nav {
          background: linear-gradient(to right, #667eea, #764ba2);
          padding: 1rem;
        }
      </style>
      <nav>
        <a href="/">Home</a>
        <a href="/about.html">About</a>
      </nav>
    `;
  }
}
customElements.define('custom-navbar', CustomNavbar);

Return the results following the same marker format as Light mode (PROJECT_NAME_START, NEW_FILE_START, etc.).
Generate files in this ORDER: index.html FIRST, then style.css, then script.js, then web components if needed.
```

#### Image Placeholder Instructions (append if images needed)

```
If you want to use image placeholder, http://static.photos Usage:
Format: http://static.photos/[category]/[dimensions]/[seed]

where:
- dimensions must be one of: 200x200, 320x240, 640x360, 1024x576, or 1200x630
- seed can be any number (1-999+) for consistent images or omit for random
- categories include: nature, office, people, technology, minimal, abstract, aerial,
  blurred, bokeh, gradient, monochrome, vintage, white, black, blue, red, green,
  yellow, cityscape, workspace, food, travel, textures, industry, indoor, outdoor,
  studio, finance, medical, season, holiday, event, sport, science, legal, estate,
  restaurant, retail, wellness, agriculture, construction, craft, cosmetic,
  automotive, gaming, education

Examples:
- http://static.photos/red/320x240/133 (red-themed with seed 133)
- http://static.photos/640x360 (random category and image)
- http://static.photos/nature/1200x630/42 (nature-themed with seed 42)
```

### Phase 3: Build Enhanced User Prompt

Combine user request with extracted design preferences:

```
User request: [original request]

Additional design requirements (if extracted):
- Use primary color: #4F46E5
- Use secondary color: #10B981
- dark mode theme
- Modern, clean aesthetic
```

### Phase 4: Validate Output & Write Files

1. **Check marker presence**:
   - PROJECT_NAME_START/END present
   - All files have NEW_FILE_START/END markers
   - Files in correct order (index.html first)

2. **Validate file structure**:
   - index.html includes TailwindCSS CDN
   - Feather Icons imported if icons used
   - style.css and script.js referenced in all HTML pages
   - Components imported before usage

3. **Write to filesystem** using bash heredoc:

```bash
# Create output directory
mkdir -p web-output
cd web-output

# Write index.html (ALWAYS FIRST)
cat > "index.html" << 'EOF'
[extracted HTML content from NEW_FILE block]
EOF

# Write style.css
cat > "style.css" << 'EOF'
[extracted CSS content]
EOF

# Write script.js
cat > "script.js" << 'EOF'
[extracted JS content]
EOF

# Write components if any
mkdir -p components
cat > "components/navbar.js" << 'EOF'
[component code]
EOF
```

**CRITICAL**: Use `>` for first write, `>>` for appending. Never use Write tool for multi-segment files.

---

## Usage Examples

### Example 1: Simple Landing Page

**User Request**:
```
Create a landing page for a SaaS productivity app
```

**Expected Output**:
```
<<<<<<< PROJECT_NAME_START Productivity Hub ✨ >>>>>>> PROJECT_NAME_END
<<<<<<< NEW_FILE_START index.html >>>>>>> NEW_FILE_END
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Productivity Hub</title>
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/feather-icons"></script>
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
    <!-- Hero Section -->
    <div class="container mx-auto px-4 py-16">
        <h1 class="text-5xl font-bold text-center mb-4">Boost Your Productivity</h1>
        <p class="text-xl text-center text-gray-600 mb-8">All-in-one platform to manage tasks, time, and team</p>
        <div class="flex gap-4 justify-center">
            <button class="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition">
                Start Free Trial
            </button>
            <button class="border-2 border-blue-600 text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition">
                Learn More
            </button>
        </div>
    </div>
    <script src="script.js"></script>
    <script>feather.replace();</script>
</body>
</html>
```
<<<<<<< NEW_FILE_START style.css >>>>>>> NEW_FILE_END
```css
[styles]
```
<<<<<<< NEW_FILE_START script.js >>>>>>> NEW_FILE_END
```javascript
[scripts]
```
```

### Example 2: Multi-Page Portfolio

**User Request**:
```
Create a portfolio website with Home, About, Projects, and Contact pages
```

**Expected Output**:
```
<<<<<<< PROJECT_NAME_START Creative Portfolio 🎨 >>>>>>> PROJECT_NAME_END
<<<<<<< NEW_FILE_START index.html >>>>>>> NEW_FILE_END
[home page HTML]
<<<<<<< NEW_FILE_START about.html >>>>>>> NEW_FILE_END
[about page HTML]
<<<<<<< NEW_FILE_START projects.html >>>>>>> NEW_FILE_END
[projects page HTML]
<<<<<<< NEW_FILE_START contact.html >>>>>>> NEW_FILE_END
[contact page HTML]
<<<<<<< NEW_FILE_START style.css >>>>>>> NEW_FILE_END
[shared styles]
<<<<<<< NEW_FILE_START script.js >>>>>>> NEW_FILE_END
[shared scripts]
<<<<<<< NEW_FILE_START components/navbar.js >>>>>>> NEW_FILE_END
[navbar component with links to all pages]
```

---

## Error Handling

### Missing Output Markers

**Problem**: AI output lacks PROJECT_NAME_START or NEW_FILE_START markers

**Solution**:
```
The output is missing required markers. Please regenerate following this exact format:

<<<<<<< PROJECT_NAME_START [Your Project Name] >>>>>>> PROJECT_NAME_END
<<<<<<< NEW_FILE_START index.html >>>>>>> NEW_FILE_END
```html
[HTML content]
```

Ensure ALL files have markers as shown above.
```

### Invalid HTML/CSS/JS Syntax

**Problem**: Generated code has syntax errors

**Solution**:
1. Validate HTML structure (opening/closing tags match)
2. Check CSS selectors and properties
3. Validate JavaScript syntax (missing semicolons, brackets)
4. Request regeneration with specific error details:
   ```
   The generated HTML has a syntax error on line 42: unclosed <div> tag.
   Please fix and regenerate the file.
   ```

### Incorrect File Order

**Problem**: Files generated in wrong order (style.css before index.html)

**Solution**:
```
CRITICAL ERROR: Files must be in this ORDER:
1. index.html (FIRST, always)
2. style.css
3. script.js
4. components/*.js

Please regenerate following the correct order.
```

### Missing TailwindCSS Import

**Problem**: Styles don't render because Tailwind CDN not imported

**Solution**:
```
Missing TailwindCSS import. Add this to <head> section:
<script src="https://cdn.tailwindcss.com"></script>
```

---

## Integration with Other Skills

### Call `web-markers-parser` for Extraction

After AI generates output with markers, call the parser skill:

```bash
# Skill invocation pattern
/web-markers-parser "$(cat ai_output.txt)"
```

The parser will:
1. Extract PROJECT_NAME_START/END → Save project name
2. Extract NEW_FILE_START/END blocks → Create individual files
3. Validate marker format
4. Return structured data (files array, errors if any)

### Design System Enhancement

For advanced design customization, can chain with `design-system-applier`:

```bash
# Generate initial website
/web-builder-initial "Create a landing page"

# Apply design system
/design-system-applier --primary="#4F46E5" --secondary="#10B981" --theme="dark"
```

---

## Output Location

All generated files written to:
```
<workDir>/web-output/
├── index.html
├── style.css
├── script.js
└── components/
    ├── navbar.js
    └── footer.js
```

---

## Status Summary Format

For orchestration compatibility:

```
--- WEB-BUILDER-INITIAL COMPLETE ---
ProjectName: [Extracted Name]
FilesGenerated: [count]
IndexHtml: ✅
StyleCss: ✅
ScriptJs: ✅
Components: [list of component names]
OutputDir: web-output/
Status: SUCCESS
--- END ---
```

---

## Gotchas & Best Practices

See `gotchas.md` for:
- Common marker format mistakes
- File order enforcement
- Web component shadow DOM caveats
- Tailwind CDN vs build approach
- Icon library integration pitfalls

---

## Chinese Language Support

When user language is Chinese, use Chinese variants:

**Project naming prompt** (ZH):
```
必须：根据用户的请求为项目生成一个名称。尝试富有创意和独特性。
在名称末尾添加一个表情符号。应该简短，大约6个字。要有趣、有创意、有趣味。
别忘了这很重要！
```

**Image placeholder instructions** (ZH):
```
如果您想使用图像占位符，请使用 http://static.photos
格式：http://static.photos/[类别]/[尺寸]/[种子]

其中：
- 尺寸必须是以下之一：200x200、320x240、640x360、1024x576 或 1200x630
- 种子可以是任何数字（1-999+）以获得一致的图像，或省略以获得随机图像
- 类别包括：nature（自然）、office（办公室）、people（人物）、technology（技术）等

示例：
- http://static.photos/red/320x240/133（红色主题，种子 133）
- http://static.photos/640x360（随机类别和图像）
- http://static.photos/nature/1200x630/42（自然主题，种子 42）
```

---

## Verification Checklist

Before marking complete:
- [ ] PROJECT_NAME markers present
- [ ] All files have NEW_FILE markers
- [ ] index.html is FIRST file
- [ ] TailwindCSS CDN imported
- [ ] Feather Icons imported (if icons used)
- [ ] style.css and script.js exist
- [ ] All HTML pages link to shared CSS/JS
- [ ] Components properly defined and registered
- [ ] Files written to web-output/ directory
- [ ] Status summary generated

---

**Skill Version**: 1.0
**BuildFlow Prompt Source**: `/mnt/oldroot/home/bird/buildflow/lib/prompts.ts`
**Last Updated**: 2026-03-30
