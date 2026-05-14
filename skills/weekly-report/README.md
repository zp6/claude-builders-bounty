# Weekly Dev Report — n8n + Claude Code

> Automatically generate a narrative weekly summary of GitHub repo activity, delivered via webhook.

## ✨ What It Does

Every **Friday at 17:00**, this n8n workflow:

1. Fetches the week's **commits**, **closed issues**, and **merged PRs** from GitHub API
2. Sends the data to **Claude** (`claude-sonnet-4-20250514`) for narrative summarization
3. Delivers a polished Markdown report via **Discord** or **Slack webhook**

## 🚀 Setup (3 Steps)

### Step 1: Import Workflow

In n8n, go to **Workflows → Import from File** and upload `workflow.json`.

### Step 2: Configure Environment Variables

Set these in your n8n instance (`.env` file or Docker environment):

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | ✅ | GitHub PAT with `repo` scope |
| `GITHUB_REPO` | ✅ | Repository in `owner/repo` format |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API key |
| `REPORT_LANGUAGE` | ❌ | `EN` (default) or `FR` |
| `WEBHOOK_URL` | ❌ | Discord or Slack webhook URL |

### Step 3: Enable & Test

1. Click **Execute Workflow** to test
2. Verify the output in the last node
3. **Enable** the workflow for automatic Friday runs

## 📁 Files

```
skills/weekly-report/
├── SKILL.md           # Skill definition
├── workflow.json      # n8n importable workflow
├── generate.js        # Standalone Node.js CLI generator
├── report-template.md # Markdown template
└── README.md          # This file
```

## 🖥️ Standalone CLI Usage

No n8n? Use the Node.js script directly:

```bash
export GITHUB_TOKEN="ghp_xxx"
export GITHUB_REPO="owner/repo"
export ANTHROPIC_API_KEY="sk-ant-xxx"
export REPORT_LANGUAGE="EN"
export WEBHOOK_URL="https://discord.com/api/webhooks/..."  # optional

node generate.js
```

Output is saved to `weekly-report.md` and optionally posted to your webhook.

## 📊 Report Sections

| Section | Content |
|---------|---------|
| 🎯 Executive Summary | 2-3 sentence overview |
| 📊 Activity Overview | Commit/issue/PR counts |
| 🚀 Highlights | Key achievements |
| 🔀 Notable Commits | Commits grouped by area |
| ✅ Issues Closed | Closed issues with links |
| 🔀 PRs Merged | Merged PRs with links |
| 📅 Looking Ahead | Patterns & next steps |

## ⚙️ Customization

- **Schedule**: Edit the cron node (`0 17 * * 5` = Fri 5PM). Change to any cron expression.
- **Language**: Set `REPORT_LANGUAGE=FR` for French output
- **Webhook**: Supports Discord and Slack webhook formats
- **Model**: Edit `generate.js` or the Code node to use a different Claude model

## 🧪 Example Output

```markdown
# Weekly Report: myorg/myrepo
**Period:** 2026-05-02 → 2026-05-09

---

### 🎯 Executive Summary
This week the team shipped 3 major features including the new auth system,
resolved 5 long-standing bugs, and merged 8 pull requests from 4 contributors.

### 🚀 Highlights
- 🔐 New OAuth2 authentication system (#142)
- 📊 Dashboard performance improved by 40% (#138)
- 🌐 Added French locale support (#145)
```

## Requirements

- n8n >= 1.0 (for workflow mode)
- Node.js >= 18 (for CLI mode)
- GitHub PAT with `repo` scope
- Anthropic API key

## License

MIT
