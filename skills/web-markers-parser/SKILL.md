---
name: web-markers-parser
description: >
  Parse AI responses containing BuildFlow markers (NEW_FILE_START, UPDATE_FILE_START,
  SEARCH/REPLACE, PROJECT_NAME_START) into structured file operations. This is a utility
  skill called by web-builder-initial and web-builder-update, not directly user-invoked.

  Inputs: AI response text with BuildFlow markers
  Outputs: Structured data (files array, project name, SEARCH/REPLACE operations, errors)
---

# Web Markers Parser - BuildFlow Marker Extraction Utility

## Overview

The `web-markers-parser` skill is a **helper utility** that parses AI responses containing BuildFlow's structured markers into actionable file operations. This skill is NOT directly user-invoked — it's called by `web-builder-initial` and `web-builder-update` skills to extract:

1. **Project name** from `PROJECT_NAME_START/END` markers
2. **New files** from `NEW_FILE_START/END` blocks
3. **File updates** from `UPDATE_FILE_START/END` blocks
4. **SEARCH/REPLACE operations** for precision editing
5. **Validation errors** for malformed markers

## Core Functionality

### 1. Marker Types

BuildFlow uses 5 marker types:

| Marker | Purpose | Example |
|--------|---------|---------|
| `PROJECT_NAME_START` / `_END` | Project name extraction | `<<<<<<< PROJECT_NAME_START My App >>>>>>> PROJECT_NAME_END` |
| `NEW_FILE_START` / `_END` | New file creation | `<<<<<<< NEW_FILE_START index.html >>>>>>> NEW_FILE_END` |
| `UPDATE_FILE_START` / `_END` | File modification target | `<<<<<<< UPDATE_FILE_START style.css >>>>>>> UPDATE_FILE_END` |
| `SEARCH` + `DIVIDER` + `REPLACE` | Precision replacement | See SEARCH/REPLACE section below |

### 2. Marker Constants

```python
# Marker definitions (from BuildFlow prompts.ts)
PROJECT_NAME_START = "<<<<<<< PROJECT_NAME_START"
PROJECT_NAME_END = ">>>>>>> PROJECT_NAME_END"

NEW_FILE_START = "<<<<<<< NEW_FILE_START"
NEW_FILE_END = ">>>>>>> NEW_FILE_END"

UPDATE_FILE_START = "<<<<<<< UPDATE_FILE_START"
UPDATE_FILE_END = ">>>>>>> UPDATE_FILE_END"

SEARCH_START = "<<<<<<< SEARCH"
DIVIDER = "======="
REPLACE_END = ">>>>>>> REPLACE"
```

### 3. Parsing Flow

```
AI Response
    ↓
Extract Project Name (PROJECT_NAME markers)
    ↓
Extract New Files (NEW_FILE markers + code blocks)
    ↓
Extract Update Operations (UPDATE_FILE markers)
    ↓
For each UPDATE_FILE:
    Extract SEARCH/REPLACE blocks
    Apply flexible HTML regex matching
    Validate SEARCH exists in current file
    Apply replacement
    ↓
Return structured result
```

## Parsing Logic

### Function 1: Extract Project Name

```python
import re

def extract_project_name(ai_response: str) -> str | None:
    """
    Extract project name from PROJECT_NAME_START/END markers.

    Args:
        ai_response: Full AI response text

    Returns:
        Project name string, or None if not found

    Example:
        Input: "<<<<<<< PROJECT_NAME_START My Portfolio ✨ >>>>>>> PROJECT_NAME_END"
        Output: "My Portfolio ✨"
    """
    pattern = re.compile(
        r'<<<<<<< PROJECT_NAME_START\s*([\s\S]*?)\s*>>>>>>> PROJECT_NAME_END'
    )
    match = pattern.search(ai_response)

    if match:
        return match.group(1).strip()

    return None
```

**Usage**:
```python
project_name = extract_project_name(ai_output)
print(f"Project: {project_name}")
# Output: Project: My Portfolio ✨
```

### Function 2: Extract New Files

```python
from typing import TypedDict

class FileData(TypedDict):
    path: str
    content: str
    language: str  # 'html', 'css', 'javascript', 'unknown'

def extract_new_files(ai_response: str) -> list[FileData]:
    """
    Extract NEW_FILE blocks and their code content.

    Args:
        ai_response: Full AI response text

    Returns:
        List of FileData dicts with path, content, language

    Example:
        Input: "<<<<<<< NEW_FILE_START index.html >>>>>>> NEW_FILE_END\n```html\n<html>...</html>\n```"
        Output: [{'path': 'index.html', 'content': '<html>...</html>', 'language': 'html'}]
    """
    files = []

    # Regex for NEW_FILE blocks
    new_file_pattern = re.compile(
        r'<<<<<<< NEW_FILE_START\s*([\s\S]*?)\s*>>>>>>> NEW_FILE_END\s*([\s\S]*?)(?=<<<<<<< NEW_FILE_START|<<<<<<< UPDATE_FILE_START|$)',
        re.DOTALL
    )

    for match in new_file_pattern.finditer(ai_response):
        file_path = match.group(1).strip()
        file_content_raw = match.group(2).strip()

        # Try to extract from code blocks (```html, ```css, ```javascript)
        html_match = re.search(r'```html\s*([\s\S]*?)\s*```', file_content_raw)
        css_match = re.search(r'```css\s*([\s\S]*?)\s*```', file_content_raw)
        js_match = re.search(r'```javascript\s*([\s\S]*?)\s*```', file_content_raw)

        if html_match:
            content = html_match.group(1).strip()
            language = 'html'
        elif css_match:
            content = css_match.group(1).strip()
            language = 'css'
        elif js_match:
            content = js_match.group(1).strip()
            language = 'javascript'
        else:
            # No code block, use raw content
            content = file_content_raw
            language = 'unknown'

        files.append({
            'path': file_path,
            'content': content,
            'language': language
        })

    return files
```

**Usage**:
```python
new_files = extract_new_files(ai_output)
for file in new_files:
    print(f"New file: {file['path']} ({file['language']}, {len(file['content'])} chars)")
# Output:
# New file: index.html (html, 1234 chars)
# New file: style.css (css, 567 chars)
# New file: script.js (javascript, 234 chars)
```

### Function 3: Extract Update Operations

```python
class SearchReplaceBlock(TypedDict):
    search: str
    replace: str

class UpdateOperation(TypedDict):
    file_path: str
    operations: list[SearchReplaceBlock]

def extract_update_operations(ai_response: str) -> list[UpdateOperation]:
    """
    Extract UPDATE_FILE blocks and their SEARCH/REPLACE operations.

    Args:
        ai_response: Full AI response text

    Returns:
        List of UpdateOperation dicts with file_path and operations

    Example:
        Input: UPDATE_FILE block with 2 SEARCH/REPLACE pairs
        Output: [{'file_path': 'index.html', 'operations': [{'search': '...', 'replace': '...'}, ...]}]
    """
    updates = []

    # Regex for UPDATE_FILE blocks
    update_file_pattern = re.compile(
        r'<<<<<<< UPDATE_FILE_START\s*([\s\S]*?)\s*>>>>>>> UPDATE_FILE_END\s*([\s\S]*?)(?=<<<<<<< UPDATE_FILE_START|<<<<<<< NEW_FILE_START|$)',
        re.DOTALL
    )

    for match in update_file_pattern.finditer(ai_response):
        file_path = match.group(1).strip()
        file_content = match.group(2).strip()

        # Extract all SEARCH/REPLACE blocks within this UPDATE_FILE
        operations = []
        position = 0

        while True:
            search_start_index = file_content.find('<<<<<<< SEARCH', position)
            if search_start_index == -1:
                break

            divider_index = file_content.find('=======', search_start_index)
            if divider_index == -1:
                break

            replace_end_index = file_content.find('>>>>>>> REPLACE', divider_index)
            if replace_end_index == -1:
                break

            # Extract SEARCH and REPLACE blocks
            search_block = file_content[
                search_start_index + len('<<<<<<< SEARCH'):divider_index
            ].strip()

            replace_block = file_content[
                divider_index + len('======='):replace_end_index
            ].strip()

            operations.append({
                'search': search_block,
                'replace': replace_block
            })

            position = replace_end_index + len('>>>>>>> REPLACE')

        if operations:
            updates.append({
                'file_path': file_path,
                'operations': operations
            })

    return updates
```

**Usage**:
```python
updates = extract_update_operations(ai_output)
for update in updates:
    print(f"Update {update['file_path']}: {len(update['operations'])} operations")
    for i, op in enumerate(update['operations'], 1):
        print(f"  Operation {i}: Replace {len(op['search'])} chars with {len(op['replace'])} chars")

# Output:
# Update index.html: 2 operations
#   Operation 1: Replace 45 chars with 52 chars
#   Operation 2: Replace 23 chars with 67 chars
```

### Function 4: Flexible HTML Regex Matching

This is the **critical function** that makes SEARCH/REPLACE work reliably despite whitespace variations:

```python
def escape_regex(text: str) -> str:
    """Escape special regex characters."""
    return re.escape(text)

def create_flexible_html_regex(search_block: str) -> re.Pattern:
    """
    Create whitespace-tolerant regex for HTML matching.

    This function transforms a SEARCH block into a regex pattern that tolerates:
    - Any amount of whitespace (spaces, tabs, newlines)
    - Whitespace between HTML tags
    - Leading/trailing whitespace around tags

    Args:
        search_block: The SEARCH block content from SEARCH/REPLACE pattern

    Returns:
        Compiled regex pattern that tolerates whitespace variations

    Example:
        Input: "<h1>Title</h1>"
        Output: Pattern that matches "<h1>Title</h1>", "<h1> Title </h1>", "<h1>\n  Title\n</h1>", etc.
    """
    # Step 1: Escape regex special characters
    search_regex = escape_regex(search_block)

    # Step 2: Replace escaped whitespace with flexible whitespace
    search_regex = re.sub(r'\\s+', r'\\s*', search_regex)

    # Step 3: Handle whitespace between tags
    search_regex = re.sub(r'>\s*<', r'>\\s*<', search_regex)

    # Step 4: Handle whitespace around closing tags
    search_regex = re.sub(r'\s*>', r'\\s*>', search_regex)

    # Step 5: Compile with DOTALL for multiline matching
    return re.compile(search_regex, re.DOTALL)


def apply_search_replace(
    file_content: str,
    search_block: str,
    replace_block: str
) -> tuple[str, int, int]:
    """
    Apply SEARCH/REPLACE with flexible HTML matching.

    Args:
        file_content: Current file content
        search_block: Text to search for
        replace_block: Text to replace with

    Returns:
        Tuple of (updated_content, start_line, end_line)

    Raises:
        ValueError: If SEARCH block not found or matches multiple times
    """
    # Handle empty SEARCH block (insert at beginning)
    if search_block.strip() == "":
        updated_content = f"{replace_block}\n{file_content}"
        return (updated_content, 1, replace_block.count('\n') + 1)

    # Create flexible regex
    pattern = create_flexible_html_regex(search_block)

    # Find all matches
    matches = list(pattern.finditer(file_content))

    if len(matches) == 0:
        raise ValueError(f"SEARCH block not found in file:\n{search_block[:100]}...")

    if len(matches) > 1:
        raise ValueError(
            f"SEARCH block matches {len(matches)} times (must be unique):\n{search_block[:100]}..."
        )

    # Apply replacement
    match = matches[0]
    before_text = file_content[:match.start()]
    after_text = file_content[match.end():]

    # Calculate line numbers
    start_line = before_text.count('\n') + 1
    end_line = start_line + replace_block.count('\n')

    updated_content = before_text + replace_block + after_text

    return (updated_content, start_line, end_line)
```

**Usage**:
```python
current_html = """
<body>
    <h1>Old Title</h1>
    <p>Content</p>
</body>
"""

search = "    <h1>Old Title</h1>"
replace = "    <h1>New Title</h1>"

try:
    updated_html, start, end = apply_search_replace(current_html, search, replace)
    print(f"✅ Replaced lines {start}-{end}")
    print(updated_html)
except ValueError as e:
    print(f"❌ Error: {e}")

# Output:
# ✅ Replaced lines 3-3
# <body>
#     <h1>New Title</h1>
#     <p>Content</p>
# </body>
```

### Function 5: Validate Markers

```python
def validate_markers(ai_response: str) -> tuple[bool, list[str]]:
    """
    Validate that AI output contains proper BuildFlow markers.

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Check PROJECT_NAME markers
    if '<<<<<<< PROJECT_NAME_START' not in ai_response:
        errors.append("Missing PROJECT_NAME_START marker")
    if '>>>>>>> PROJECT_NAME_END' not in ai_response:
        errors.append("Missing PROJECT_NAME_END marker")

    # Check UPDATE_FILE pairs
    update_starts = ai_response.count('<<<<<<< UPDATE_FILE_START')
    update_ends = ai_response.count('>>>>>>> UPDATE_FILE_END')
    if update_starts != update_ends:
        errors.append(
            f"Mismatched UPDATE_FILE markers: {update_starts} starts, {update_ends} ends"
        )

    # Check NEW_FILE pairs
    new_starts = ai_response.count('<<<<<<< NEW_FILE_START')
    new_ends = ai_response.count('>>>>>>> NEW_FILE_END')
    if new_starts != new_ends:
        errors.append(
            f"Mismatched NEW_FILE markers: {new_starts} starts, {new_ends} ends"
        )

    # Check SEARCH/REPLACE pairs
    search_starts = ai_response.count('<<<<<<< SEARCH')
    replace_ends = ai_response.count('>>>>>>> REPLACE')
    dividers = ai_response.count('=======')

    if search_starts != replace_ends:
        errors.append(
            f"Mismatched SEARCH/REPLACE: {search_starts} SEARCH, {replace_ends} REPLACE"
        )

    if dividers < search_starts:
        errors.append(
            f"Missing dividers: {dividers} dividers for {search_starts} SEARCH blocks"
        )

    # Check if at least one operation type exists
    has_new_files = new_starts > 0
    has_updates = update_starts > 0

    if not has_new_files and not has_updates:
        errors.append("No NEW_FILE or UPDATE_FILE operations found")

    return (len(errors) == 0, errors)
```

**Usage**:
```python
is_valid, errors = validate_markers(ai_output)

if is_valid:
    print("✅ All markers valid")
else:
    print("❌ Marker validation errors:")
    for error in errors:
        print(f"  - {error}")

# Example output:
# ❌ Marker validation errors:
#   - Mismatched SEARCH/REPLACE: 3 SEARCH, 2 REPLACE
#   - Missing dividers: 2 dividers for 3 SEARCH blocks
```

## Main Parsing Function

The complete parser combines all extraction functions:

```python
from typing import TypedDict

class ParseResult(TypedDict):
    success: bool
    project_name: str | None
    new_files: list[FileData]
    update_operations: list[UpdateOperation]
    errors: list[str]

def parse_buildflow_markers(ai_response: str) -> ParseResult:
    """
    Main parsing function that extracts all BuildFlow markers.

    Args:
        ai_response: Full AI response text with BuildFlow markers

    Returns:
        ParseResult dict with all extracted data and validation errors
    """
    # Validate markers first
    is_valid, errors = validate_markers(ai_response)

    if not is_valid:
        return {
            'success': False,
            'project_name': None,
            'new_files': [],
            'update_operations': [],
            'errors': errors
        }

    # Extract all data
    try:
        project_name = extract_project_name(ai_response)
        new_files = extract_new_files(ai_response)
        update_operations = extract_update_operations(ai_response)

        return {
            'success': True,
            'project_name': project_name,
            'new_files': new_files,
            'update_operations': update_operations,
            'errors': []
        }
    except Exception as e:
        return {
            'success': False,
            'project_name': None,
            'new_files': [],
            'update_operations': [],
            'errors': [f"Parsing exception: {str(e)}"]
        }
```

**Full usage example**:
```python
# Parse AI output
result = parse_buildflow_markers(ai_response)

if result['success']:
    print(f"✅ Parsing successful")
    print(f"📦 Project: {result['project_name']}")
    print(f"📄 New files: {len(result['new_files'])}")
    print(f"✏️  Update operations: {len(result['update_operations'])}")

    # Process new files
    for file in result['new_files']:
        print(f"\n📝 Creating: {file['path']}")
        with open(f"web-output/{file['path']}", 'w') as f:
            f.write(file['content'])

    # Process updates
    for update in result['update_operations']:
        print(f"\n✏️  Updating: {update['file_path']}")
        with open(f"web-output/{update['file_path']}", 'r') as f:
            current_content = f.read()

        updated_content = current_content
        for op in update['operations']:
            updated_content, start, end = apply_search_replace(
                updated_content,
                op['search'],
                op['replace']
            )
            print(f"  ✓ Replaced lines {start}-{end}")

        with open(f"web-output/{update['file_path']}", 'w') as f:
            f.write(updated_content)
else:
    print(f"❌ Parsing failed:")
    for error in result['errors']:
        print(f"  - {error}")
```

## File Operations

### Writing New Files

```bash
#!/bin/bash
# write_new_files.sh - Write NEW_FILE blocks to disk

WORK_DIR="$1"
NEW_FILES_JSON="$2"  # JSON array from parse_buildflow_markers

# Create web-output directory
mkdir -p "$WORK_DIR/web-output"
mkdir -p "$WORK_DIR/web-output/components"

# Parse JSON and write files
echo "$NEW_FILES_JSON" | jq -c '.[]' | while read -r file; do
    FILE_PATH=$(echo "$file" | jq -r '.path')
    FILE_CONTENT=$(echo "$file" | jq -r '.content')

    # Create parent directories if needed
    PARENT_DIR=$(dirname "$WORK_DIR/web-output/$FILE_PATH")
    mkdir -p "$PARENT_DIR"

    # Write file using heredoc
    cat > "$WORK_DIR/web-output/$FILE_PATH" << 'EOF'
$FILE_CONTENT
EOF

    echo "✅ Created: $FILE_PATH"
done
```

### Applying Update Operations

```bash
#!/bin/bash
# apply_updates.sh - Apply SEARCH/REPLACE operations

WORK_DIR="$1"
UPDATE_OPS_JSON="$2"  # JSON array from parse_buildflow_markers

# Python script to apply updates (uses apply_search_replace function)
python3 << 'PYTHON_SCRIPT'
import json
import sys
import os

def apply_updates(work_dir, updates_json):
    updates = json.loads(updates_json)

    for update in updates:
        file_path = update['file_path']
        full_path = os.path.join(work_dir, 'web-output', file_path)

        # Read current content
        with open(full_path, 'r') as f:
            content = f.read()

        # Apply each operation
        for i, op in enumerate(update['operations'], 1):
            try:
                content, start, end = apply_search_replace(
                    content,
                    op['search'],
                    op['replace']
                )
                print(f"  ✓ Operation {i}: Lines {start}-{end}")
            except ValueError as e:
                print(f"  ❌ Operation {i} failed: {e}", file=sys.stderr)
                sys.exit(1)

        # Write updated content
        with open(full_path, 'w') as f:
            f.write(content)

        print(f"✅ Updated: {file_path}")

if __name__ == '__main__':
    work_dir = os.environ['WORK_DIR']
    updates_json = sys.stdin.read()
    apply_updates(work_dir, updates_json)
PYTHON_SCRIPT
```

## Error Detection

### Error 1: Missing Markers

```python
def detect_missing_markers(ai_response: str) -> list[str]:
    """Detect if critical markers are missing."""
    warnings = []

    if '<<<<<<< PROJECT_NAME_START' not in ai_response:
        warnings.append("No project name provided (missing PROJECT_NAME markers)")

    if '<<<<<<< NEW_FILE_START' not in ai_response and '<<<<<<< UPDATE_FILE_START' not in ai_response:
        warnings.append("No file operations found (missing NEW_FILE and UPDATE_FILE markers)")

    return warnings
```

### Error 2: Malformed SEARCH/REPLACE

```python
def detect_malformed_search_replace(file_content: str) -> list[str]:
    """Detect common SEARCH/REPLACE formatting errors."""
    errors = []

    # Check for SEARCH without matching REPLACE
    search_count = file_content.count('<<<<<<< SEARCH')
    replace_count = file_content.count('>>>>>>> REPLACE')

    if search_count > replace_count:
        errors.append(f"Incomplete SEARCH/REPLACE: {search_count - replace_count} missing REPLACE blocks")

    # Check for divider mismatches
    divider_count = file_content.count('=======')
    if divider_count < search_count:
        errors.append(f"Missing dividers: Expected {search_count}, found {divider_count}")

    return errors
```

### Error 3: Code Block Extraction Failures

```python
def detect_code_block_issues(new_file_block: str) -> list[str]:
    """Detect issues with code block formatting."""
    warnings = []

    # Check for code blocks
    has_html = '```html' in new_file_block
    has_css = '```css' in new_file_block
    has_js = '```javascript' in new_file_block

    if not (has_html or has_css or has_js):
        warnings.append("No code block markers (```html, ```css, ```javascript) found")

    # Check for unclosed code blocks
    triple_backticks = new_file_block.count('```')
    if triple_backticks % 2 != 0:
        warnings.append(f"Unclosed code block (odd number of triple backticks: {triple_backticks})")

    return warnings
```

## Integration with web-builder Skills

### Called by web-builder-initial

```bash
# In web-builder-initial workflow (Phase 3)

# Step 1: Get AI output with markers
AI_OUTPUT=$(call_llm_with_prompt "$INITIAL_PROMPT")

# Step 2: Call parser
PARSE_RESULT=$(parse_buildflow_markers "$AI_OUTPUT")

# Step 3: Check success
SUCCESS=$(echo "$PARSE_RESULT" | jq -r '.success')

if [ "$SUCCESS" = "true" ]; then
    # Extract data
    PROJECT_NAME=$(echo "$PARSE_RESULT" | jq -r '.project_name')
    NEW_FILES=$(echo "$PARSE_RESULT" | jq -c '.new_files')

    # Write files
    bash write_new_files.sh "$WORK_DIR" "$NEW_FILES"

    echo "✅ Project created: $PROJECT_NAME"
else
    # Show errors
    ERRORS=$(echo "$PARSE_RESULT" | jq -r '.errors[]')
    echo "❌ Parsing failed:"
    echo "$ERRORS"
fi
```

### Called by web-builder-update

```bash
# In web-builder-update workflow (Phase 3)

# Step 1: Get AI output with UPDATE_FILE and SEARCH/REPLACE
AI_OUTPUT=$(call_llm_with_prompt "$UPDATE_PROMPT")

# Step 2: Call parser
PARSE_RESULT=$(parse_buildflow_markers "$AI_OUTPUT")

# Step 3: Check success
SUCCESS=$(echo "$PARSE_RESULT" | jq -r '.success')

if [ "$SUCCESS" = "true" ]; then
    # Extract data
    NEW_FILES=$(echo "$PARSE_RESULT" | jq -c '.new_files')
    UPDATES=$(echo "$PARSE_RESULT" | jq -c '.update_operations')

    # Write new files (if any)
    if [ "$(echo "$NEW_FILES" | jq 'length')" -gt 0 ]; then
        bash write_new_files.sh "$WORK_DIR" "$NEW_FILES"
    fi

    # Apply updates
    echo "$UPDATES" | bash apply_updates.sh "$WORK_DIR"

    echo "✅ Project updated"
else
    # Show errors
    ERRORS=$(echo "$PARSE_RESULT" | jq -r '.errors[]')
    echo "❌ Parsing failed:"
    echo "$ERRORS"
fi
```

## Scripts to Create

### scripts/parse_markers.py

Main parsing script (~250 lines):

```python
#!/usr/bin/env python3
"""
parse_markers.py - Parse BuildFlow markers from AI response

Usage:
    python parse_markers.py < ai_response.txt > result.json

Output JSON format:
{
    "success": true,
    "project_name": "My App",
    "new_files": [...],
    "update_operations": [...],
    "errors": []
}
"""

import sys
import json
import re
from typing import TypedDict

# [Include all parsing functions here: extract_project_name, extract_new_files,
#  extract_update_operations, validate_markers, parse_buildflow_markers]

def main():
    # Read AI response from stdin
    ai_response = sys.stdin.read()

    # Parse markers
    result = parse_buildflow_markers(ai_response)

    # Output JSON to stdout
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
```

### scripts/apply_search_replace.py

SEARCH/REPLACE application script (~200 lines):

```python
#!/usr/bin/env python3
"""
apply_search_replace.py - Apply SEARCH/REPLACE operations to files

Usage:
    python apply_search_replace.py <work_dir> < update_operations.json

Input JSON format:
[
    {
        "file_path": "index.html",
        "operations": [
            {"search": "...", "replace": "..."},
            ...
        ]
    },
    ...
]
"""

import sys
import json
import os
from typing import TypedDict

# [Include: escape_regex, create_flexible_html_regex, apply_search_replace]

def main():
    if len(sys.argv) != 2:
        print("Usage: apply_search_replace.py <work_dir>", file=sys.stderr)
        sys.exit(1)

    work_dir = sys.argv[1]

    # Read update operations from stdin
    updates = json.load(sys.stdin)

    for update in updates:
        file_path = update['file_path']
        full_path = os.path.join(work_dir, 'web-output', file_path)

        # Read current content
        with open(full_path, 'r') as f:
            content = f.read()

        # Apply each operation
        for i, op in enumerate(update['operations'], 1):
            try:
                content, start, end = apply_search_replace(
                    content,
                    op['search'],
                    op['replace']
                )
                print(f"  ✓ Operation {i}: Lines {start}-{end}")
            except ValueError as e:
                print(f"  ❌ Operation {i} failed: {e}", file=sys.stderr)
                sys.exit(1)

        # Write updated content
        with open(full_path, 'w') as f:
            f.write(content)

        print(f"✅ Updated: {file_path}")

if __name__ == '__main__':
    main()
```

### scripts/validate_markers.py

Standalone validation script (~100 lines):

```python
#!/usr/bin/env python3
"""
validate_markers.py - Validate BuildFlow markers in AI response

Usage:
    python validate_markers.py < ai_response.txt

Exit codes:
    0 - All markers valid
    1 - Validation errors found
"""

import sys

# [Include: validate_markers, detect_missing_markers, detect_malformed_search_replace]

def main():
    ai_response = sys.stdin.read()

    is_valid, errors = validate_markers(ai_response)

    if is_valid:
        print("✅ All markers valid")
        sys.exit(0)
    else:
        print("❌ Marker validation errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

## Testing

### Test 1: Parse Simple NEW_FILE

```python
def test_parse_new_file():
    ai_response = """
<<<<<<< PROJECT_NAME_START Test App >>>>>>> PROJECT_NAME_END
<<<<<<< NEW_FILE_START index.html >>>>>>> NEW_FILE_END
```html
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body><h1>Hello</h1></body>
</html>
```
"""

    result = parse_buildflow_markers(ai_response)

    assert result['success'] == True
    assert result['project_name'] == 'Test App'
    assert len(result['new_files']) == 1
    assert result['new_files'][0]['path'] == 'index.html'
    assert '<!DOCTYPE html>' in result['new_files'][0]['content']

    print("✅ Test passed: Parse simple NEW_FILE")
```

### Test 2: Parse UPDATE_FILE with SEARCH/REPLACE

```python
def test_parse_update_file():
    ai_response = """
<<<<<<< PROJECT_NAME_START Test App >>>>>>> PROJECT_NAME_END
<<<<<<< UPDATE_FILE_START index.html >>>>>>> UPDATE_FILE_END
<<<<<<< SEARCH
<h1>Old Title</h1>
=======
<h1>New Title</h1>
>>>>>>> REPLACE
"""

    result = parse_buildflow_markers(ai_response)

    assert result['success'] == True
    assert len(result['update_operations']) == 1
    assert result['update_operations'][0]['file_path'] == 'index.html'
    assert len(result['update_operations'][0]['operations']) == 1
    assert 'Old Title' in result['update_operations'][0]['operations'][0]['search']
    assert 'New Title' in result['update_operations'][0]['operations'][0]['replace']

    print("✅ Test passed: Parse UPDATE_FILE with SEARCH/REPLACE")
```

### Test 3: Flexible HTML Regex Matching

```python
def test_flexible_html_regex():
    # Test whitespace tolerance
    html = "<body>\n    <h1>Title</h1>\n</body>"
    search = "<body><h1>Title</h1></body>"  # No whitespace

    pattern = create_flexible_html_regex(search)
    match = pattern.search(html)

    assert match is not None, "Should match despite whitespace differences"
    print("✅ Test passed: Flexible HTML regex matching")
```

### Test 4: Apply SEARCH/REPLACE

```python
def test_apply_search_replace():
    current = """
<body>
    <h1>Old</h1>
    <p>Content</p>
</body>
"""

    search = "    <h1>Old</h1>"
    replace = "    <h1>New</h1>"

    updated, start, end = apply_search_replace(current, search, replace)

    assert '<h1>New</h1>' in updated
    assert '<h1>Old</h1>' not in updated
    assert start == 3  # Line 3
    assert end == 3

    print("✅ Test passed: Apply SEARCH/REPLACE")
```

## Known Edge Cases

### Edge Case 1: Multiple Code Blocks in NEW_FILE

If AI returns multiple code blocks in one NEW_FILE:

```
<<<<<<< NEW_FILE_START index.html >>>>>>> NEW_FILE_END
```html
<html>...</html>
```
```css
/* Some inline styles */
```
```

**Solution**: Only extract the first code block (HTML takes precedence over CSS/JS).

### Edge Case 2: Nested Markers (Invalid)

If AI accidentally nests markers:

```
<<<<<<< NEW_FILE_START outer.html >>>>>>> NEW_FILE_END
<<<<<<< NEW_FILE_START inner.html >>>>>>> NEW_FILE_END  // INVALID
```

**Solution**: Parser should detect and report as error (nested markers not allowed).

### Edge Case 3: SEARCH Block with Regex Special Chars

If SEARCH block contains regex special characters:

```
<<<<<<< SEARCH
const regex = /[a-z]+/;
=======
```

**Solution**: `escape_regex()` handles this — all regex chars are escaped before creating pattern.

---

**Implementation Status**: ✅ Complete - Helper skill ready
**BuildFlow Source**: `/mnt/oldroot/home/bird/buildflow/lib/format-ai-response.ts`
**Dependencies**: None (standalone utility)
**Called By**: `web-builder-initial`, `web-builder-update`
**Last Updated**: 2026-03-30
