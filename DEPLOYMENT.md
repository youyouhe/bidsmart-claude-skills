# 🚀 Deployment Guide

This guide explains how to deploy your BidSmart Claude Skills repository to GitHub and make it available to others.

## Prerequisites

- GitHub account
- Git installed locally
- Repository prepared in `/tmp/bidsmart-claude-skills`

## Step 1: Create GitHub Repository

### Option A: Using GitHub Web Interface

1. Go to [GitHub](https://github.com) and log in
2. Click the **"+"** icon in the top right, select **"New repository"**
3. Fill in the details:
   - **Repository name**: `bidsmart-claude-skills`
   - **Description**: "Comprehensive Claude Code skills for Chinese government procurement"
   - **Visibility**: Public (or Private if you prefer)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Click **"Create repository"**

### Option B: Using GitHub CLI

```bash
# Install GitHub CLI if not already installed
# On Ubuntu/Debian:
# sudo apt install gh

# Login to GitHub
gh auth login

# Create repository
gh repo create bidsmart-claude-skills --public --description "Comprehensive Claude Code skills for Chinese government procurement"
```

## Step 2: Push Your Repository

After creating the GitHub repository, you'll see instructions. Here's what to do:

### Copy Repository to Your Home Directory

```bash
# Copy from /tmp to your home directory for permanent storage
cp -r /tmp/bidsmart-claude-skills ~/bidsmart-claude-skills
cd ~/bidsmart-claude-skills
```

### Connect to GitHub

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/bidsmart-claude-skills.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

### If using SSH (recommended for frequent pushes):

```bash
# Set up SSH key if you haven't
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add SSH key to GitHub (copy the public key)
cat ~/.ssh/id_ed25519.pub
# Go to GitHub → Settings → SSH and GPG keys → New SSH key

# Use SSH remote
git remote set-url origin git@github.com:YOUR_USERNAME/bidsmart-claude-skills.git
git push -u origin main
```

## Step 3: Configure Repository Settings

### Add Repository Description

1. Go to your repository on GitHub
2. Click **"About"** section (gear icon)
3. Add:
   - **Description**: "Comprehensive Claude Code skills for Chinese government procurement"
   - **Topics**: `claude-code`, `skills`, `bid-management`, `government-procurement`, `chinese`
   - **Website**: Your documentation site (optional)

### Set Up Branch Protection (Optional)

For team collaboration:

1. Go to **Settings** → **Branches**
2. Add rule for `main` branch:
   - ✅ Require pull request reviews
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date

### Enable Issues and Discussions

1. Go to **Settings** → **Features**
2. Enable:
   - ✅ Issues (for bug reports)
   - ✅ Discussions (for Q&A)
   - ✅ Projects (for roadmap)

## Step 4: Create a Release

Create your first official release:

```bash
# Tag the release
git tag -a v1.0.0 -m "Initial release: BidSmart Claude Skills v1.0.0"

# Push the tag
git push origin v1.0.0
```

Or use GitHub web interface:
1. Go to **Releases** → **Create a new release**
2. Tag: `v1.0.0`
3. Title: `BidSmart Claude Skills v1.0.0`
4. Description: Copy from CHANGELOG.md
5. Click **Publish release**

## Step 5: Update Documentation

After deploying, update the placeholder URLs in your documentation:

```bash
# Update README.md
sed -i 's/YOUR_USERNAME/your-actual-username/g' README.md

# Update CONTRIBUTING.md
sed -i 's/YOUR_USERNAME/your-actual-username/g' CONTRIBUTING.md

# Update QUICKSTART.md
sed -i 's/YOUR_USERNAME/your-actual-username/g' QUICKSTART.md

# Commit and push
git add .
git commit -m "docs: update GitHub username in documentation"
git push
```

## Step 6: Test Installation

Test that others can install your skills:

### Create a test project

```bash
mkdir /tmp/test-bidsmart
cd /tmp/test-bidsmart
mkdir -p .claude

# Create settings.local.json
cat > .claude/settings.local.json << 'EOF'
{
  "extraKnownMarketplaces": {
    "bidsmart": {
      "source": {
        "source": "github",
        "repo": "YOUR_USERNAME/bidsmart-claude-skills"
      }
    }
  },
  "enabledPlugins": {
    "bidsmart-skills@bidsmart": true
  }
}
EOF

# Start Claude Code
claude

# In Claude Code, check skills are loaded
/skills
```

## Step 7: Promote Your Repository

### Add Badges to README

Add status badges at the top of README.md:

```markdown
[![GitHub release](https://img.shields.io/github/v/release/YOUR_USERNAME/bidsmart-claude-skills)](https://github.com/YOUR_USERNAME/bidsmart-claude-skills/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/bidsmart-claude-skills)](https://github.com/YOUR_USERNAME/bidsmart-claude-skills/stargazers)
```

### Share Your Work

- **Claude Code Community**: Share in relevant forums/Discord
- **Social Media**: Tweet about your release
- **Blog Post**: Write about your experience
- **Documentation Site**: Create a GitHub Pages site

### Submit to Claude Code Marketplace (Optional)

If there's an official marketplace, submit your skills for broader distribution.

## Maintenance

### Regular Updates

```bash
# Make changes
git add .
git commit -m "feat: add new feature"
git push

# Create new release
git tag -a v1.1.0 -m "Version 1.1.0: New features"
git push origin v1.1.0
```

### Update CHANGELOG.md

Keep CHANGELOG.md updated with each release following [Keep a Changelog](https://keepachangelog.com/) format.

### Monitor Issues

Regularly check and respond to:
- 🐛 Bug reports
- ✨ Feature requests
- 💬 Discussions
- 🔀 Pull requests

## Security

### Security Policy

Create `.github/SECURITY.md`:

```markdown
# Security Policy

## Reporting a Vulnerability

Please report security vulnerabilities to: security@bidsmart.local

We will respond within 48 hours.
```

### Dependabot

Enable Dependabot for automatic dependency updates:
- Go to **Settings** → **Security & analysis**
- Enable **Dependabot alerts** and **Dependabot security updates**

## Troubleshooting

### Push Rejected

```bash
# If you get "push rejected" error
git pull --rebase origin main
git push
```

### Large Files

If you have large files (> 50MB):

```bash
# Use Git LFS
git lfs install
git lfs track "*.pdf"
git lfs track "*.docx"
git add .gitattributes
git commit -m "chore: add Git LFS tracking"
git push
```

## Next Steps

1. ✅ Repository deployed
2. ✅ Release created
3. ✅ Documentation updated
4. ✅ Installation tested
5. 🎯 Share with community
6. 📊 Monitor usage and feedback
7. 🔄 Iterate and improve

---

Congratulations! Your BidSmart Claude Skills are now publicly available! 🎉

For questions, open an issue on GitHub.
