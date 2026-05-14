# Weekly Dev Report Skill

> Automatically generate a narrative weekly summary of GitHub repo activity using n8n + Claude API.

## Overview

This skill provides a complete n8n workflow that fetches weekly activity from a GitHub repository (commits, closed issues, merged PRs), uses the Claude API to generate a narrative summary, and delivers it via webhook (Discord/Slack) or email.

## What's Included

| File | Description |
|------|-------------|
| `workflow.json` | Importable n8n workflow |
| `report-template.md` | Markdown template for the report |
| `generate.js` | Standalone Node.js generator script |
| `README.md` | Setup instructions |

## Quick Start (n8n)

1. Import `workflow.json` into your n8n instance
2. Configure the 4 environment variables (see README)
3. Enable the workflow — runs every Friday at 17:00

## Quick Start (CLI)

```bash
# Set required env vars
export GITHUB_TOKEN="ghp_xxx"
export GITHUB_REPO="owner/repo"
export ANTHROPIC_API_KEY="sk-ant-xxx"
export REPORT_LANGUAGE="EN"

# Generate report
node skills/weekly-report/generate.js
```

## Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GITHUB_TOKEN` | ✅ | GitHub personal access token | — |
| `GITHUB_REPO` | ✅ | Repository in `owner/repo` format | — |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key for Claude | — |
| `REPORT_LANGUAGE` | ❌ | Report language (`EN` or `FR`) | `EN` |
| `WEBHOOK_URL` | ❌ | Discord/Slack webhook URL | — |

## Report Sections

The generated report includes:

- 📊 **Activity Overview** — high-level stats
- 🚀 **Highlights** — key achievements this week
- 🔀 **Commits** — notable commits grouped by area
- ✅ **Issues Closed** — resolved issues with links
- 🔀 **PRs Merged** — merged pull requests with links
- 📅 **Coming Up** — open issues & next steps

## Requirements

- n8n >= 1.0 (for workflow)
- Node.js >= 18 (for CLI script)
- GitHub PAT with `repo` scope
- Anthropic API key
