# Contributing to BidSmart Claude Skills

Thank you for your interest in contributing! This document provides guidelines for contributing to the BidSmart Claude Skills project.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/youyouhe/bidsmart-claude-skills.git
   cd bidsmart-claude-skills
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Creating or Modifying Skills

### Skill Structure

Each skill should be in its own directory under `skills/` with:

```
skills/your-skill-name/
├── SKILL.md           # Required: Skill definition with frontmatter
└── scripts/           # Optional: Helper scripts
    ├── script1.py
    └── script2.sh
```

### Skill Definition Format

The `SKILL.md` file must start with YAML frontmatter:

```markdown
---
name: skill-name
description: >
  Brief description of what the skill does and when it should be triggered.
  Include use cases and trigger conditions.
---

# Skill Title

## Overview
Detailed explanation of the skill...

## Workflow
Step-by-step process...

## Usage Examples
...
```

### Best Practices

1. **Clear Trigger Conditions**: Specify exactly when the skill should be invoked
2. **Structured Workflows**: Break down complex processes into numbered steps
3. **Error Handling**: Include fallback strategies for common failure cases
4. **Documentation**: Provide clear examples and usage instructions
5. **Chinese Language**: Ensure proper Chinese language support for government procurement context

## 🧪 Testing Your Changes

Before submitting:

1. **Test locally**:
   - Add your fork to `.claude/settings.local.json`
   - Restart Claude Code
   - Test the skill with real or sample data

2. **Verify skill loading**:
   ```bash
   # In Claude Code
   /skills
   ```
   Your skill should appear in the list

3. **Test workflows**:
   - Test individual skill invocation
   - Test integration with other skills
   - Test error cases

## 📋 Commit Guidelines

### Commit Message Format

```
type(scope): brief description

Detailed explanation of changes (optional)

Fixes #issue-number (if applicable)
```

### Types

- `feat`: New feature or skill
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(bid-analysis): add support for Excel-based tender documents

docs(readme): update installation instructions for Windows users

fix(bid-verification): handle missing sections in analysis report
```

## 🔄 Pull Request Process

1. **Update documentation**: Ensure README.md reflects your changes
2. **Test thoroughly**: Verify your changes work as expected
3. **Create PR**: Submit a pull request with:
   - Clear title describing the change
   - Detailed description of what was changed and why
   - Any relevant issue numbers
   - Screenshots or examples if applicable

4. **PR Template**:
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Refactoring

   ## Testing
   - How was this tested?
   - What scenarios were covered?

   ## Checklist
   - [ ] Code follows project style
   - [ ] Documentation updated
   - [ ] Tested locally
   - [ ] No breaking changes (or documented)
   ```

## 🐛 Reporting Issues

When reporting issues, include:

1. **Skill name** that has the issue
2. **Expected behavior** vs **actual behavior**
3. **Steps to reproduce**
4. **Error messages** or logs
5. **Environment**: OS, Claude Code version, etc.

## 💡 Suggesting Enhancements

For feature requests:

1. **Use case**: Describe the problem you're trying to solve
2. **Proposed solution**: How should it work?
3. **Alternatives**: What alternatives have you considered?
4. **Additional context**: Screenshots, examples, etc.

## 🌟 Areas for Contribution

We especially welcome contributions in:

- **New Skills**: Additional bid management workflows
- **Enhanced OCR**: Better handling of scanned documents
- **Multilingual Support**: Support for other languages/regions
- **Testing**: Test cases and validation scripts
- **Documentation**: Tutorials, examples, guides
- **Integration**: Integration with other tools/services

## 📞 Questions?

If you have questions about contributing:

1. Check existing [issues](https://github.com/youyouhe/bidsmart-claude-skills/issues)
2. Open a new issue with the `question` label
3. Join discussions in pull requests

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to BidSmart Claude Skills! 🎉
