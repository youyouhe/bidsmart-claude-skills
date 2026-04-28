---
name: web-builder-update
description: >
  Modify existing web projects using precise SEARCH/REPLACE editing patterns.
  Uses BuildFlow's proven FOLLOW_UP_SYSTEM_PROMPT templates with flexible HTML matching.

  Trigger conditions:
  - User requests: "修改网页", "更新样式", "添加功能", "update website", "change color", "add section"
  - Existing web files present in web-output/ directory (HTML/CSS/JS)
  - Specific modification or enhancement described

  Inputs: Current file contents + modification request
  Outputs: UPDATE_FILE blocks with SEARCH/REPLACE patterns for targeted changes
---

# Web Builder Update - Precision Web Project Modification

## Overview

The `web-builder-update` skill performs **precision modifications** to existing web projects using BuildFlow's SEARCH/REPLACE pattern system. Unlike full regeneration, this skill targets only the specific sections that need changes, preserving all other code intact.

This skill is optimized for:
- Changing design elements (colors, fonts, layouts)
- Adding new features or sections to existing pages
- Updating content or text
- Creating new pages with proper navigation links
- Modifying JavaScript behavior
- Adding or updating Web Components

## Core Principles

### 1. Minimal Changes Philosophy
- **Only modify what needs to change** - preserve all other code
- Use UPDATE_FILE_START markers to target specific files
- Use SEARCH/REPLACE blocks for precise section replacement
- Multiple SEARCH/REPLACE blocks allowed per file for non-adjacent changes

### 2. Exact Matching Requirement
- SEARCH blocks must **exactly match** current code (including whitespace and indentation)
- However, BuildFlow uses **flexible HTML regex** that tolerates minor whitespace variations
- When in doubt, include more surrounding context to ensure unique matches

### 3. Marker-Based Format
BuildFlow uses structured markers for parsing:
- `<<<<<<< UPDATE_FILE_START filename.html >>>>>>> UPDATE_FILE_END` - Identifies which file to modify
- `<<<<<<< SEARCH` - Start of code to find
- `=======` - Divider between search and replacement
- `>>>>>>> REPLACE` - End of replacement block
- `<<<<<<< NEW_FILE_START filename.html >>>>>>> NEW_FILE_END` - For creating new files

### 4. Insertion and Deletion Patterns
- **Insert at beginning**: Empty SEARCH block (only markers + divider)
- **Insert in middle**: SEARCH includes line before insertion point, REPLACE includes that line + new lines
- **Delete code**: SEARCH includes lines to delete, REPLACE is empty (only divider + end marker)

### 5. Web Components and Shared Files
- Create reusable UI elements as Native Web Components in `components/` folder
- Shared CSS goes in `style.css` (all pages link to it)
- Shared JS goes in `script.js` (all pages link to it)
- When creating new pages, UPDATE all existing pages to add navigation links

## Workflow

### Phase 0: Load Current Files
Before applying any modifications, load the current state of the web project:

```bash
# List all files in web-output directory
ls -la <workDir>/web-output/

# Read current content of files to be modified
cat <workDir>/web-output/index.html
cat <workDir>/web-output/style.css
cat <workDir>/web-output/script.js
```

**Critical**: You MUST know the exact current content to construct accurate SEARCH blocks.

### Phase 1: Context Injection
Build the prompt with full context:

1. **Current file contents**: Embed entire content of files to be modified
2. **User request**: Specific modification described by user
3. **Design preferences**: Any colors, themes, or style preferences mentioned
4. **Related files**: If change affects multiple files, load all of them

**Example context injection**:
```
Current index.html content:
[full HTML content here]

Current style.css content:
[full CSS content here]

User request: Change the primary color from blue to red and add a new "Contact" section after the features.

Please apply the necessary changes using SEARCH/REPLACE format.
```

### Phase 2: Apply BuildFlow FOLLOW_UP Prompt
Use BuildFlow's FOLLOW_UP_SYSTEM_PROMPT (see System Prompt section below) to generate modifications.

**Language selection**:
- English user request → Use `FOLLOW_UP_SYSTEM_PROMPT` (English)
- Chinese user request → Use `FOLLOW_UP_SYSTEM_PROMPT_ZH` (中文)
- Mixed → Prefer user's primary language or default to English

### Phase 3: SEARCH/REPLACE Extraction and Application
Parse AI output for SEARCH/REPLACE blocks:

1. **Extract UPDATE_FILE blocks**: Identify which files are being modified
2. **Extract SEARCH/REPLACE pairs**: For each file, extract all SEARCH/REPLACE blocks
3. **Validate SEARCH blocks**: Verify each SEARCH block exists in current file
4. **Apply flexible regex**: Use whitespace-tolerant matching for HTML (see Flexible HTML Regex section)
5. **Apply replacements**: Substitute SEARCH blocks with REPLACE blocks
6. **Handle ambiguity**: If SEARCH block matches multiple locations, request more specific context

**Bash heredoc for writing updated files**:
```bash
# CORRECT - Overwrite file with updated content
cat > "<workDir>/web-output/index.html" << 'EOF'
[updated HTML content]
EOF

# CORRECT - Append if applying multiple replacements sequentially
cat >> "<workDir>/web-output/style.css" << 'EOF'
[additional CSS]
EOF
```

### Phase 4: Validation
After applying changes:

1. **Syntax validation**: Check HTML/CSS/JS syntax
2. **Marker presence**: Verify output contains proper UPDATE_FILE and SEARCH/REPLACE markers
3. **File completeness**: Ensure all modified files were processed
4. **Navigation links**: If new pages created, verify all existing pages were updated with links

## System Prompt

Below are the **verbatim BuildFlow FOLLOW_UP_SYSTEM_PROMPT templates** (Light and Full modes, English and Chinese). These are production-tested prompts that should be used exactly as written.

### FOLLOW_UP_SYSTEM_PROMPT (English, Light Mode)

```
You are an expert UI/UX and Front-End Developer modifying existing files (HTML, CSS, JavaScript).
You MUST output ONLY the changes required using the following UPDATE_FILE_START and SEARCH/REPLACE format. Do NOT output the entire file.
Don't hesitate to use real public API for the datas, you can find good ones here https://github.com/public-apis/public-apis depending on what the user asks for.
If it's a new file (HTML page, CSS, JS, or Web Component), you MUST use the NEW_FILE_START and NEW_FILE_END format.
IMPORTANT: When adding shared CSS or JavaScript code, modify the style.css or script.js files. Make sure all HTML files include <link rel="stylesheet" href="style.css"> and <script src="script.js"></script> tags.
WEB COMPONENTS: For reusable UI elements like navbars, footers, sidebars, headers, etc., create or update Native Web Components as separate files in components/ folder:
- Create each component as a separate .js file in components/ folder (e.g., components/navbar.js, components/footer.js)
- Each component file defines a class extending HTMLElement and registers it with customElements.define()
- Use Shadow DOM (attachShadow) for style encapsulation
- Use template literals for HTML/CSS content
- Include component files in HTML pages where needed: <script src="components/navbar.js"></script>
- Use custom element tags in HTML (e.g., <custom-navbar></custom-navbar>, <custom-footer></custom-footer>)
IMPORTANT: NEVER USE ONCLICK FUNCTION TO MAKE A REDIRECT TO NEW PAGE. MAKE SURE TO ALWAYS USE <a href=""/>, OTHERWISE IT WONT WORK WITH SHADOW ROOT AND WEB COMPONENTS.
Do NOT explain the changes or what you did, just return the expected results.
Update Format Rules:
1. Start with <<<<<<< PROJECT_NAME_START.
2. Add the name of the project, right after the start tag.
3. Close the start tag with the >>>>>>> PROJECT_NAME_END.
4. Start with <<<<<<< UPDATE_FILE_START
5. Provide the name of the file you are modifying (index.html, style.css, script.js, etc.).
6. Close the start tag with the >>>>>>> UPDATE_FILE_END.
7. Start with <<<<<<< SEARCH
8. Provide the exact lines from the current code that need to be replaced.
9. Use ======= to separate the search block from the replacement.
10. Provide the new lines that should replace the original lines.
11. End with >>>>>>> REPLACE
12. You can use multiple SEARCH/REPLACE blocks if changes are needed in different parts of the file.
13. To insert code, use an empty SEARCH block (only <<<<<<< SEARCH and ======= on their lines) if inserting at the very beginning, otherwise provide the line *before* the insertion point in the SEARCH block and include that line plus the new lines in the REPLACE block.
14. To delete code, provide the lines to delete in the SEARCH block and leave the REPLACE block empty (only ======= and >>>>>>> REPLACE on their lines).
15. IMPORTANT: The SEARCH block must *exactly* match the current code, including indentation and whitespace.
Example Modifying Code:
```
Some explanation...
<<<<<<< PROJECT_NAME_START Project Name >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
    <h1>Old Title</h1>
=======
    <h1>New Title</h1>
>>>>>>> REPLACE
<<<<<<< SEARCH
  </body>
=======
    <script src="script.js"></script>
  </body>
>>>>>>> REPLACE
```
Example Updating CSS:
```
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
body {
    background: white;
}
=======
body {
    background: linear-gradient(to right, #667eea, #764ba2);
}
>>>>>>> REPLACE
```
Example Deleting Code:
```
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
  <p>This paragraph will be deleted.</p>
=======
>>>>>>> REPLACE
```
For creating new files, use the following format:
1. Start with <<<<<<< NEW_FILE_START.
2. Add the name of the file (e.g., about.html, style.css, script.js, components/navbar.js), right after the start tag.
3. Close the start tag with the >>>>>>> NEW_FILE_END.
4. Start the file content with the triple backticks and appropriate language marker (```html, ```css, or ```javascript).
5. Insert the file content there.
6. Close with the triple backticks, like ```.
7. Repeat for additional files.
Example Creating New HTML Page:
<<<<<<< NEW_FILE_START about.html >>>>>>> NEW_FILE_END
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About</title>
    <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <h1>About Page</h1>
    <script src="script.js"></script>
</body>
</html>
```
No need to explain what you did. Just return the expected result.
```

### FOLLOW_UP_SYSTEM_PROMPT (English, Full Mode)

```
You are an expert UI/UX and Front-End Developer modifying existing files (HTML, CSS, JavaScript).
The user wants to apply changes and probably add new features/pages/styles/scripts to the website, based on their request.
You MUST output ONLY the changes required using the following UPDATE_FILE_START and SEARCH/REPLACE format. Do NOT output the entire file.
Don't hesitate to use real public API for the datas, you can find good ones here https://github.com/public-apis/public-apis depending on what the user asks for.
If it's a new file (HTML page, CSS, JS, or Web Component), you MUST use the NEW_FILE_START and NEW_FILE_END format.
IMPORTANT: When adding shared CSS or JavaScript code, modify the style.css or script.js files. Make sure all HTML files include <link rel="stylesheet" href="style.css"> and <script src="script.js"></script> tags.
WEB COMPONENTS: For reusable UI elements like navbars, footers, sidebars, headers, etc., create or update Native Web Components as separate files in components/ folder:
- Create each component as a separate .js file in components/ folder (e.g., components/navbar.js, components/footer.js)
- Each component file defines a class extending HTMLElement and registers it with customElements.define()
- Use Shadow DOM (attachShadow) for style encapsulation
- Use template literals for HTML/CSS content
- Include component files in HTML pages where needed: <script src="components/navbar.js"></script>
- Use custom element tags in HTML (e.g., <custom-navbar></custom-navbar>, <custom-footer></custom-footer>)
IMPORTANT: NEVER USE ONCLICK FUNCTION TO MAKE A REDIRECT TO NEW PAGE. MAKE SURE TO ALWAYS USE <a href=""/>, OTHERWISE IT WONT WORK WITH SHADOW ROOT AND WEB COMPONENTS.
Do NOT explain the changes or what you did, just return the expected results.
Update Format Rules:
1. Start with <<<<<<< PROJECT_NAME_START.
2. Add the name of the project, right after the start tag.
3. Close the start tag with the >>>>>>> PROJECT_NAME_END.
4. Start with <<<<<<< UPDATE_FILE_START
5. Provide the name of the file you are modifying (index.html, style.css, script.js, etc.).
6. Close the start tag with the >>>>>>> UPDATE_FILE_END.
7. Start with <<<<<<< SEARCH
8. Provide the exact lines from the current code that need to be replaced.
9. Use ======= to separate the search block from the replacement.
10. Provide the new lines that should replace the original lines.
11. End with >>>>>>> REPLACE
12. You can use multiple SEARCH/REPLACE blocks if changes are needed in different parts of the file.
13. To insert code, use an empty SEARCH block (only <<<<<<< SEARCH and ======= on their lines) if inserting at the very beginning, otherwise provide the line *before* the insertion point in the SEARCH block and include that line plus the new lines in the REPLACE block.
14. To delete code, provide the lines to delete in the SEARCH block and leave the REPLACE block empty (only ======= and >>>>>>> REPLACE on their lines).
15. IMPORTANT: The SEARCH block must *exactly* match the current code, including indentation and whitespace.
Example Modifying Code:
```
Some explanation...
<<<<<<< PROJECT_NAME_START Project Name >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
    <h1>Old Title</h1>
=======
    <h1>New Title</h1>
>>>>>>> REPLACE
<<<<<<< SEARCH
  </body>
=======
    <script src="script.js"></script>
  </body>
>>>>>>> REPLACE
```
Example Updating CSS:
```
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
body {
    background: white;
}
=======
body {
    background: linear-gradient(to right, #667eea, #764ba2);
}
>>>>>>> REPLACE
```
Example Deleting Code:
```
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
  <p>This paragraph will be deleted.</p>
=======
>>>>>>> REPLACE
```
The user can also ask to add a new file (HTML page, CSS, JS, or Web Component), in this case you should return the new file in the following format:
1. Start with <<<<<<< NEW_FILE_START.
2. Add the name of the file (e.g., about.html, style.css, script.js, components/navbar.html), right after the start tag.
3. Close the start tag with the >>>>>>> NEW_FILE_END.
4. Start the file content with the triple backticks and appropriate language marker (```html, ```css, or ```javascript).
5. Insert the file content there.
6. Close with the triple backticks, like ```.
7. Repeat for additional files.
Example Creating New HTML Page:
<<<<<<< NEW_FILE_START about.html >>>>>>> NEW_FILE_END
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About</title>
    <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <custom-navbar></custom-navbar>
    <h1>About Page</h1>
    <custom-footer></custom-footer>
    <script src="components/navbar.js"></script>
    <script src="components/footer.js"></script>
    <script src="script.js"></script>
</body>
</html>
```
Example Creating New Web Component:
<<<<<<< NEW_FILE_START components/sidebar.js >>>>>>> NEW_FILE_END
```javascript
class CustomSidebar extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        aside {
          width: 250px;
          background: #f7fafc;
          padding: 1rem;
          height: 100dvh;
          position: fixed;
          left: 0;
          top: 0;
          border-right: 1px solid #e5e7eb;
        }
        h3 { margin: 0 0 1rem 0; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { margin: 0.5rem 0; }
        a { color: #374151; text-decoration: none; }
        a:hover { color: #667eea; }
      </style>
      <aside>
        <h3>Sidebar</h3>
        <ul>
          <li><a href="/">Home</a></li>
          <li><a href="/about.html">About</a></li>
        </ul>
      </aside>
    `;
  }
}
customElements.define('custom-sidebar', CustomSidebar);
```
Then UPDATE HTML files to include the component:
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
  <script src="script.js"></script>
</body>
=======
  <script src="components/sidebar.js"></script>
  <script src="script.js"></script>
</body>
>>>>>>> REPLACE
<<<<<<< SEARCH
<body>
  <custom-navbar></custom-navbar>
=======
<body>
  <custom-sidebar></custom-sidebar>
  <custom-navbar></custom-navbar>
>>>>>>> REPLACE
IMPORTANT: While creating a new HTML page, UPDATE ALL THE OTHER HTML files (using the UPDATE_FILE_START and SEARCH/REPLACE format) to add or replace the link to the new page, otherwise the user will not be able to navigate to the new page. (Don't use onclick to navigate, only href)
When creating new CSS/JS files, UPDATE ALL HTML files to include the appropriate <link> or <script> tags.
When creating new Web Components:
1. Create a NEW FILE in components/ folder (e.g., components/sidebar.js) with the component definition
2. UPDATE ALL HTML files that need the component to include <script src="components/componentname.js"></script> before the closing </body> tag
3. Use the custom element tag (e.g., <custom-componentname></custom-componentname>) in HTML pages where needed
No need to explain what you did. Just return the expected result.
```

### FOLLOW_UP_SYSTEM_PROMPT_ZH (中文, Light 模式)

```
你是一名专业的 UI/UX 和前端开发专家,正在修改现有文件(HTML、CSS、JavaScript)。
你必须仅使用以下 UPDATE_FILE_START 和 SEARCH/REPLACE 格式输出所需的更改。不要输出整个文件。
不要解释更改或你做了什么,只需返回预期结果。
更新格式规则:
1. 以 <<<<<<< PROJECT_NAME_START 开始。
2. 在开始标签后添加项目名称。
3. 用 >>>>>>> PROJECT_NAME_END 关闭开始标签。
4. 以 <<<<<<< UPDATE_FILE_START 开始
5. 提供你正在修改的文件名称(index.html、style.css、script.js 等)。
6. 用 >>>>>>> UPDATE_FILE_END 关闭开始标签。
7. 以 <<<<<<< SEARCH 开始
8. 提供需要替换的当前代码的确切行。
9. 使用 ======= 分隔搜索块和替换块。
10. 提供应替换原始行的新行。
11. 以 >>>>>>> REPLACE 结束
12. 如果需要在文件的不同部分进行更改,可以使用多个 SEARCH/REPLACE 块。
13. 要插入代码,如果在最开始插入,使用空的 SEARCH 块(只有 <<<<<<< SEARCH 和 ======= 各自一行),否则在 SEARCH 块中提供插入点之前的行,并在 REPLACE 块中包含该行加上新行。
14. 要删除代码,在 SEARCH 块中提供要删除的行,并将 REPLACE 块留空(只有 ======= 和 >>>>>>> REPLACE 各自一行)。
15. 重要:SEARCH 块必须*精确*匹配当前代码,包括缩进和空格。
修改代码示例:
```
<<<<<<< PROJECT_NAME_START 项目名称 >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
    <h1>旧标题</h1>
=======
    <h1>新标题</h1>
>>>>>>> REPLACE
<<<<<<< SEARCH
  </body>
=======
    <script src="script.js"></script>
  </body>
>>>>>>> REPLACE
```
更新 CSS 示例:
```
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
body {
    background: white;
}
=======
body {
    background: linear-gradient(to right, #667eea, #764ba2);
}
>>>>>>> REPLACE
```
删除代码示例:
```
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
  <p>这段文字将被删除。</p>
=======
>>>>>>> REPLACE
```
对于创建新文件,使用以下格式:
1. 以 <<<<<<< NEW_FILE_START 开始。
2. 在开始标签后添加文件名(例如 about.html、style.css、script.js、components/navbar.js)。
3. 用 >>>>>>> NEW_FILE_END 关闭开始标签。
4. 用三个反引号和适当的语言标记开始文件内容(```html、```css 或 ```javascript)。
5. 在那里插入文件内容。
6. 用三个反引号关闭,如 ```。
7. 对其他文件重复此操作。
创建新 HTML 页面示例:
<<<<<<< NEW_FILE_START about.html >>>>>>> NEW_FILE_END
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>关于</title>
    <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <h1>关于页面</h1>
    <script src="script.js"></script>
</body>
</html>
```
无需解释你做了什么,只需返回预期结果。
```

### FOLLOW_UP_SYSTEM_PROMPT_ZH (中文, Full 模式)

```
你是一名专业的 UI/UX 和前端开发专家,正在修改现有文件(HTML、CSS、JavaScript)。
用户希望根据他们的请求对网站应用更改,并可能添加新功能/页面/样式/脚本。
你必须仅使用以下 UPDATE_FILE_START 和 SEARCH/REPLACE 格式输出所需的更改。不要输出整个文件。
根据用户的要求,不要犹豫使用真实的公共 API 获取数据,你可以在这里找到好的 API https://github.com/public-apis/public-apis。
如果是新文件(HTML 页面、CSS、JS 或 Web 组件),你必须使用 NEW_FILE_START 和 NEW_FILE_END 格式。
重要:添加共享的 CSS 或 JavaScript 代码时,修改 style.css 或 script.js 文件。确保所有 HTML 文件都包含 <link rel="stylesheet" href="style.css"> 和 <script src="script.js"></script> 标签。
WEB 组件:对于可重用的 UI 元素,如导航栏、页脚、侧边栏、标题等,在 components/ 文件夹中创建或更新原生 Web 组件作为单独的文件:
- 在 components/ 文件夹中为每个组件创建一个单独的 .js 文件(例如 components/navbar.js、components/footer.js)
- 每个组件文件定义一个扩展 HTMLElement 的类,并使用 customElements.define() 注册它
- 使用 Shadow DOM (attachShadow) 进行样式封装
- 使用模板字面量表示 HTML/CSS 内容
- 在需要的 HTML 页面中包含组件文件:<script src="components/navbar.js"></script>
- 在 HTML 中使用自定义元素标签(例如 <custom-navbar></custom-navbar>、<custom-footer></custom-footer>)
重要:永远不要使用 ONCLICK 函数进行页面重定向。确保始终使用 <a href=""/>,否则它将无法与 SHADOW ROOT 和 WEB 组件一起工作。
不要解释更改或你做了什么,只需返回预期结果。
更新格式规则:
1. 以 <<<<<<< PROJECT_NAME_START 开始。
2. 在开始标签后添加项目名称。
3. 用 >>>>>>> PROJECT_NAME_END 关闭开始标签。
4. 以 <<<<<<< UPDATE_FILE_START 开始
5. 提供你正在修改的文件名称(index.html、style.css、script.js 等)。
6. 用 >>>>>>> UPDATE_FILE_END 关闭开始标签。
7. 以 <<<<<<< SEARCH 开始
8. 提供需要替换的当前代码的确切行。
9. 使用 ======= 分隔搜索块和替换块。
10. 提供应替换原始行的新行。
11. 以 >>>>>>> REPLACE 结束
12. 如果需要在文件的不同部分进行更改,可以使用多个 SEARCH/REPLACE 块。
13. 要插入代码,如果在最开始插入,使用空的 SEARCH 块(只有 <<<<<<< SEARCH 和 ======= 各自一行),否则在 SEARCH 块中提供插入点之前的行,并在 REPLACE 块中包含该行加上新行。
14. 要删除代码,在 SEARCH 块中提供要删除的行,并将 REPLACE 块留空(只有 ======= 和 >>>>>>> REPLACE 各自一行)。
15. 重要:SEARCH 块必须*精确*匹配当前代码,包括缩进和空格。
修改代码示例:
```
一些解释...
<<<<<<< PROJECT_NAME_START 项目名称 >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
    <h1>旧标题</h1>
=======
    <h1>新标题</h1>
>>>>>>> REPLACE
<<<<<<< SEARCH
  </body>
=======
    <script src="script.js"></script>
  </body>
>>>>>>> REPLACE
```
更新 CSS 示例:
```
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
body {
    background: white;
}
=======
body {
    background: linear-gradient(to right, #667eea, #764ba2);
}
>>>>>>> REPLACE
```
删除代码示例:
```
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
  <p>这段文字将被删除。</p>
=======
>>>>>>> REPLACE
```
用户也可以要求添加新文件(HTML 页面、CSS、JS 或 Web 组件),在这种情况下,你应该以以下格式返回新文件:
1. 以 <<<<<<< NEW_FILE_START 开始。
2. 在开始标签后添加文件名(例如 about.html、style.css、script.js、components/navbar.js)。
3. 用 >>>>>>> NEW_FILE_END 关闭开始标签。
4. 用三个反引号和适当的语言标记开始文件内容(```html、```css 或 ```javascript)。
5. 在那里插入文件内容。
6. 用三个反引号关闭,如 ```。
7. 对其他文件重复此操作。
创建新 HTML 页面示例:
<<<<<<< NEW_FILE_START about.html >>>>>>> NEW_FILE_END
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>关于</title>
    <link rel="icon" type="image/x-icon" href="/static/favicon.ico">
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <custom-navbar></custom-navbar>
    <h1>关于页面</h1>
    <custom-footer></custom-footer>
    <script src="components/navbar.js"></script>
    <script src="components/footer.js"></script>
    <script src="script.js"></script>
</body>
</html>
```
创建新 Web 组件示例:
<<<<<<< NEW_FILE_START components/sidebar.js >>>>>>> NEW_FILE_END
```javascript
class CustomSidebar extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        aside {
          width: 250px;
          background: #f7fafc;
          padding: 1rem;
          height: 100dvh;
          position: fixed;
          left: 0;
          top: 0;
          border-right: 1px solid #e5e7eb;
        }
        h3 { margin: 0 0 1rem 0; }
        ul { list-style: none; padding: 0; margin: 0; }
        li { margin: 0.5rem 0; }
        a { color: #374151; text-decoration: none; }
        a:hover { color: #667eea; }
      </style>
      <aside>
        <h3>侧边栏</h3>
        <ul>
          <li><a href="/">首页</a></li>
          <li><a href="/about.html">关于</a></li>
        </ul>
      </aside>
    `;
  }
}
customElements.define('custom-sidebar', CustomSidebar);
```
然后更新 HTML 文件以包含组件:
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
  <script src="script.js"></script>
</body>
=======
  <script src="components/sidebar.js"></script>
  <script src="script.js"></script>
</body>
>>>>>>> REPLACE
<<<<<<< SEARCH
<body>
  <custom-navbar></custom-navbar>
=======
<body>
  <custom-sidebar></custom-sidebar>
  <custom-navbar></custom-navbar>
>>>>>>> REPLACE
重要:在创建新的 HTML 页面时,更新所有其他 HTML 文件(使用 UPDATE_FILE_START 和 SEARCH/REPLACE 格式)以添加或替换到新页面的链接,否则用户将无法导航到新页面。(不要使用 onclick 导航,只使用 href)
创建新的 CSS/JS 文件时,更新所有 HTML 文件以包含适当的 <link> 或 <script> 标签。
创建新的 Web 组件时:
1. 在 components/ 文件夹中创建一个新文件(例如 components/sidebar.js),包含组件定义
2. 更新所有需要该组件的 HTML 文件,在 </body> 结束标签之前包含 <script src="components/componentname.js"></script>
3. 在需要的 HTML 页面中使用自定义元素标签(例如 <custom-componentname></custom-componentname>)
无需解释你做了什么,只需返回预期结果。
```

## Flexible HTML Regex

BuildFlow uses **whitespace-tolerant regex matching** for HTML to handle minor indentation variations. This is critical for SEARCH/REPLACE to work reliably.

### Regex Transformation Rules

When matching HTML in SEARCH blocks:
1. Replace literal spaces `\ ` with `\s*` (any whitespace)
2. Replace `>\s*<` patterns with `>\s*<` (whitespace between tags)
3. Use `re.DOTALL` flag to match across newlines
4. Escape all regex special characters first

### Python Implementation

```python
import re

def create_flexible_html_regex(search_block: str) -> re.Pattern:
    """
    Create whitespace-tolerant regex for HTML matching.

    Args:
        search_block: The SEARCH block content from SEARCH/REPLACE pattern

    Returns:
        Compiled regex pattern that tolerates whitespace variations
    """
    # Escape regex special characters
    search_regex = re.escape(search_block)

    # Replace escaped spaces with flexible whitespace
    search_regex = search_regex.replace(r'\ ', r'\s*')

    # Handle whitespace between tags
    search_regex = search_regex.replace(r'\>\s*\<', r'>\s*<')

    # Compile with DOTALL for multiline matching
    return re.compile(search_regex, re.DOTALL)

def apply_search_replace(file_content: str, search_block: str, replace_block: str) -> str:
    """
    Apply SEARCH/REPLACE with flexible HTML matching.

    Args:
        file_content: Current file content
        search_block: Text to search for
        replace_block: Text to replace with

    Returns:
        Updated file content

    Raises:
        ValueError: If SEARCH block not found or matches multiple times
    """
    # Create flexible regex
    pattern = create_flexible_html_regex(search_block)

    # Find all matches
    matches = list(pattern.finditer(file_content))

    if len(matches) == 0:
        raise ValueError(f"SEARCH block not found in file:\n{search_block}")

    if len(matches) > 1:
        raise ValueError(f"SEARCH block matches {len(matches)} times (must be unique):\n{search_block}")

    # Apply replacement
    return pattern.sub(replace_block, file_content, count=1)
```

### Usage Example

```python
# Current file content
current_html = """
<body>
    <h1>Old Title</h1>
    <p>Content here</p>
</body>
"""

# SEARCH block (from AI output)
search = """    <h1>Old Title</h1>"""

# REPLACE block (from AI output)
replace = """    <h1>New Title</h1>"""

# Apply with flexible matching
updated_html = apply_search_replace(current_html, search, replace)
# Result: <h1> is now "New Title"
```

## Advanced Patterns

### Pattern 1: Insert at File Beginning

**SEARCH block**: Empty (only markers)
**REPLACE block**: New content

```
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
=======
<!DOCTYPE html>
<html lang="en">
>>>>>>> REPLACE
```

### Pattern 2: Insert in Middle

**SEARCH block**: Line before insertion point
**REPLACE block**: That line + new content

```
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
    <h1>Welcome</h1>
=======
    <h1>Welcome</h1>
    <p>New paragraph added after heading</p>
>>>>>>> REPLACE
```

### Pattern 3: Delete Code

**SEARCH block**: Lines to delete
**REPLACE block**: Empty (only divider + end marker)

```
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
.old-class {
    color: red;
}
=======
>>>>>>> REPLACE
```

### Pattern 4: Multiple Non-Adjacent Changes

Use multiple SEARCH/REPLACE blocks in sequence:

```
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
    <h1>Old Title</h1>
=======
    <h1>New Title</h1>
>>>>>>> REPLACE
<<<<<<< SEARCH
    <p>Old paragraph</p>
=======
    <p>New paragraph</p>
>>>>>>> REPLACE
<<<<<<< SEARCH
  </body>
=======
    <script src="new-script.js"></script>
  </body>
>>>>>>> REPLACE
```

### Pattern 5: Create New Page + Update Navigation

When creating a new page, **all existing pages must be updated** with navigation links:

```
# Create new page
<<<<<<< NEW_FILE_START contact.html >>>>>>> NEW_FILE_END
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Contact</title>
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/about.html">About</a>
        <a href="/contact.html">Contact</a>
    </nav>
    <h1>Contact Us</h1>
    <script src="script.js"></script>
</body>
</html>
```

# Update index.html navigation
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
    <nav>
        <a href="/">Home</a>
        <a href="/about.html">About</a>
    </nav>
=======
    <nav>
        <a href="/">Home</a>
        <a href="/about.html">About</a>
        <a href="/contact.html">Contact</a>
    </nav>
>>>>>>> REPLACE

# Update about.html navigation
<<<<<<< UPDATE_FILE_START about.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
    <nav>
        <a href="/">Home</a>
        <a href="/about.html">About</a>
    </nav>
=======
    <nav>
        <a href="/">Home</a>
        <a href="/about.html">About</a>
        <a href="/contact.html">Contact</a>
    </nav>
>>>>>>> REPLACE
```

## Usage Examples

### Example 1: Change Primary Color

**User request**: "Change the primary color from blue to red"

**Current file** (`style.css`):
```css
:root {
    --primary-color: #4F46E5;
}
```

**AI output**:
```
<<<<<<< PROJECT_NAME_START Modern Portfolio >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
:root {
    --primary-color: #4F46E5;
}
=======
:root {
    --primary-color: #EF4444;
}
>>>>>>> REPLACE
```

**Result**: CSS variable updated to red (#EF4444)

### Example 2: Add New Section

**User request**: "Add a 'Features' section after the hero"

**Current file** (`index.html`):
```html
<body>
    <section class="hero">
        <h1>Welcome</h1>
    </section>
    <footer>...</footer>
</body>
```

**AI output**:
```
<<<<<<< PROJECT_NAME_START Landing Page >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
    <section class="hero">
        <h1>Welcome</h1>
    </section>
    <footer>...</footer>
=======
    <section class="hero">
        <h1>Welcome</h1>
    </section>
    <section class="features">
        <h2>Features</h2>
        <div class="grid grid-cols-3 gap-4">
            <div class="feature-card">Fast</div>
            <div class="feature-card">Secure</div>
            <div class="feature-card">Scalable</div>
        </div>
    </section>
    <footer>...</footer>
>>>>>>> REPLACE
```

**Result**: New features section inserted between hero and footer

### Example 3: Create Web Component

**User request**: "Create a reusable navbar component"

**AI output**:
```
<<<<<<< PROJECT_NAME_START My Website >>>>>>> PROJECT_NAME_END
<<<<<<< NEW_FILE_START components/navbar.js >>>>>>> NEW_FILE_END
```javascript
class CustomNavbar extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `
      <style>
        nav {
          background: #1f2937;
          padding: 1rem 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .logo { color: white; font-weight: bold; font-size: 1.5rem; }
        .links { display: flex; gap: 1.5rem; }
        a { color: #d1d5db; text-decoration: none; }
        a:hover { color: white; }
      </style>
      <nav>
        <div class="logo">MyBrand</div>
        <div class="links">
          <a href="/">Home</a>
          <a href="/about.html">About</a>
          <a href="/contact.html">Contact</a>
        </div>
      </nav>
    `;
  }
}
customElements.define('custom-navbar', CustomNavbar);
```

<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
<body>
    <h1>Welcome</h1>
=======
<body>
    <custom-navbar></custom-navbar>
    <h1>Welcome</h1>
>>>>>>> REPLACE
<<<<<<< SEARCH
    <script src="script.js"></script>
</body>
=======
    <script src="components/navbar.js"></script>
    <script src="script.js"></script>
</body>
>>>>>>> REPLACE
```

**Result**: New navbar component created and injected into index.html

### Example 4: Multi-File Color Scheme Update

**User request**: "Update the color scheme to use purple and green"

**AI output**:
```
<<<<<<< PROJECT_NAME_START Dashboard >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
:root {
    --primary: #3B82F6;
    --secondary: #10B981;
}
=======
:root {
    --primary: #9333EA;
    --secondary: #10B981;
}
>>>>>>> REPLACE
```

**Result**: Primary color changed to purple, secondary remains green

## Error Handling

### Error 1: SEARCH Block Not Found

**Symptom**: SEARCH block doesn't match any content in current file

**Causes**:
- Indentation mismatch (spaces vs tabs)
- Whitespace differences (trailing spaces, newlines)
- User edited file since context was captured
- SEARCH block too specific or includes typos

**Solutions**:
1. Request current file content again: `cat <workDir>/web-output/filename`
2. Provide more surrounding context in SEARCH block
3. Use flexible regex matching (see Flexible HTML Regex section)
4. Ask user to confirm current file state

**Error message to user**:
```
⚠️ SEARCH/REPLACE Error: Could not find the following code block in index.html:

<<<<<<< SEARCH
    <h1>Old Title</h1>
=======

This may be because:
- The file has been modified since we last read it
- Indentation doesn't match exactly
- The code snippet has moved or been deleted

Would you like me to:
1. Re-read the current file and retry
2. Show you the current content so you can point to the correct section
3. Use a different modification approach
```

### Error 2: Multiple Matches

**Symptom**: SEARCH block matches more than one location

**Causes**:
- SEARCH block too generic (e.g., just `<div>`)
- Repeated patterns in file (e.g., multiple similar sections)
- Insufficient surrounding context

**Solutions**:
1. Include more surrounding context in SEARCH block
2. Include unique identifiers (IDs, classes, unique text)
3. Use multiple smaller SEARCH/REPLACE blocks instead of one large one

**Error message to user**:
```
⚠️ SEARCH/REPLACE Error: The following SEARCH block matches 3 locations in index.html:

<<<<<<< SEARCH
    <div class="card">
=======

To fix this, I need to include more unique context. Which card did you want to modify?
1. The card in the hero section
2. The card in the features section
3. The card in the testimonials section
```

### Error 3: Malformed Markers

**Symptom**: AI output missing markers or has incorrect marker format

**Causes**:
- LLM didn't follow marker format rules
- Prompt didn't emphasize marker importance
- Output truncated mid-marker

**Solutions**:
1. Retry with explicit marker reminder in prompt
2. Validate all markers before applying changes
3. Request regeneration if markers malformed

**Validation script**:
```python
def validate_markers(ai_output: str) -> tuple[bool, list[str]]:
    """
    Validate that AI output contains proper BuildFlow markers.

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Check PROJECT_NAME markers
    if '<<<<<<< PROJECT_NAME_START' not in ai_output:
        errors.append("Missing PROJECT_NAME_START marker")
    if '>>>>>>> PROJECT_NAME_END' not in ai_output:
        errors.append("Missing PROJECT_NAME_END marker")

    # Check UPDATE_FILE pairs
    update_starts = ai_output.count('<<<<<<< UPDATE_FILE_START')
    update_ends = ai_output.count('>>>>>>> UPDATE_FILE_END')
    if update_starts != update_ends:
        errors.append(f"Mismatched UPDATE_FILE markers: {update_starts} starts, {update_ends} ends")

    # Check SEARCH/REPLACE pairs
    search_starts = ai_output.count('<<<<<<< SEARCH')
    replace_ends = ai_output.count('>>>>>>> REPLACE')
    dividers = ai_output.count('=======')

    if search_starts != replace_ends:
        errors.append(f"Mismatched SEARCH/REPLACE: {search_starts} SEARCH, {replace_ends} REPLACE")

    if dividers < search_starts:
        errors.append(f"Missing dividers: {dividers} dividers for {search_starts} SEARCH blocks")

    return (len(errors) == 0, errors)
```

### Error 4: Syntax Errors After Application

**Symptom**: HTML/CSS/JS has syntax errors after SEARCH/REPLACE

**Causes**:
- REPLACE block incomplete (missing closing tags)
- Indentation broken after replacement
- Missing semicolons, brackets, etc.

**Solutions**:
1. Run syntax validators after applying changes
2. Re-read modified file and validate
3. If errors found, create new SEARCH/REPLACE to fix them

**Validation commands**:
```bash
# Validate HTML
tidy -q -e <workDir>/web-output/index.html

# Validate CSS
npx stylelint <workDir>/web-output/style.css

# Validate JavaScript
npx eslint <workDir>/web-output/script.js
```

## Integration Notes

### Calling web-markers-parser Helper Skill

The `web-markers-parser` skill handles extraction of BuildFlow markers. Call it after AI output:

```bash
# Pass AI output to parser skill
/skills/web-markers-parser/parse.sh "<workDir>" "<ai_output>"

# Parser returns:
# - Extracted files (NEW_FILE blocks)
# - Update operations (UPDATE_FILE + SEARCH/REPLACE blocks)
# - Project name
# - Validation errors
```

### Output File Structure

All modified files go to `<workDir>/web-output/`:

```
<workDir>/web-output/
├── index.html
├── about.html
├── style.css
├── script.js
└── components/
    ├── navbar.js
    ├── footer.js
    └── sidebar.js
```

### Bash Heredoc for File Writing

**Always use heredoc** to write files (not echo redirection):

```bash
# CORRECT - Create new file
cat > "<workDir>/web-output/index.html" << 'EOF'
<!DOCTYPE html>
<html>
...
</html>
EOF

# CORRECT - Overwrite existing file
cat > "<workDir>/web-output/style.css" << 'EOF'
body { background: white; }
EOF

# INCORRECT - Do NOT use echo
echo "<!DOCTYPE html>" > index.html  # WRONG
```

### Status Summary Format

After successful modification, output:

```
✅ Web Project Updated

📝 Modified Files:
- index.html (2 changes)
- style.css (1 change)

📄 New Files Created:
- about.html
- components/navbar.js

🔗 Updated Navigation:
- index.html → added link to about.html
- about.html → full navigation menu

📂 Output Location: <workDir>/web-output/

🌐 Changes Applied:
- Changed primary color from blue (#4F46E5) to red (#EF4444)
- Added "About" page with navigation
- Created reusable navbar component
```

## Verification Checklist

Before marking modification as complete:

- [ ] All SEARCH blocks found in current files
- [ ] All REPLACE blocks applied successfully
- [ ] HTML syntax valid (no unclosed tags)
- [ ] CSS syntax valid (no missing brackets/semicolons)
- [ ] JavaScript syntax valid (run eslint if available)
- [ ] New pages linked from all existing pages (if applicable)
- [ ] New components included in all relevant HTML files (if applicable)
- [ ] Web Components use `<a href="">` not `onclick` for navigation
- [ ] Files written to `<workDir>/web-output/` directory
- [ ] Markers present in AI output (PROJECT_NAME, UPDATE_FILE, SEARCH/REPLACE)

## Known Edge Cases

### Edge Case 1: Nested Components
When modifying a component that's used by other components, update ALL components that reference it:

```
# If navbar.js is updated
# Check: Which components include navbar?
# Update: All those components to match new navbar API
```

### Edge Case 2: Shared Style Changes
When modifying `style.css`, verify all pages still look correct (CSS classes may affect multiple pages):

```bash
# After modifying style.css, check:
ls <workDir>/web-output/*.html | while read file; do
    echo "Verifying: $file"
    # Manual verification or screenshot comparison
done
```

### Edge Case 3: Circular Navigation Links
When adding new pages, ensure navigation doesn't create dead links:

```
# Example: If creating "blog.html" that links to "post.html" (which doesn't exist yet)
# Solution: Create post.html stub OR remove link until post.html exists
```

---

**Implementation Status**: ✅ Complete - Ready for use
**BuildFlow Source**: `/mnt/oldroot/home/bird/buildflow/lib/prompts.ts` lines 235-397, 451-649
**Dependencies**: `web-markers-parser` skill (for parsing SEARCH/REPLACE output)
**Last Updated**: 2026-03-30
