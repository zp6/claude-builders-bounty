# Weekly Dev Summary — n8n + Claude API Workflow

An n8n workflow that automatically generates a narrative weekly summary of GitHub repo activity using the Claude API.

## Setup (5 steps)

### 1. Import the workflow
```bash
# In n8n UI: Workflows → Import from File
# Select: weekly-dev-summary.json
```

### 2. Configure GitHub credentials
In n8n, go to **Credentials → Add → Header Auth**:
- Name: `GitHub Token`
- Header Name: `Authorization`
- Header Value: `Bearer ghp_YOUR_GITHUB_TOKEN`

Then edit the workflow nodes and update `GITHUB_TOKEN_CRED_ID` to your credential ID.

### 3. Configure Claude API credentials
In n8n, go to **Credentials → Add → Anthropic API**:
- Name: `Anthropic API`
- API Key: Your Anthropic API key

Then edit the workflow nodes and update `ANTHROPIC_CRED_ID` to your credential ID.

### 4. Set environment variables
In n8n, go to **Settings → Environment Variables** (or set in `.env`):
```env
GITHUB_REPO=owner/repo
DELIVERY_METHOD=webhook       # or "email"
WEBHOOK_URL=https://discord.com/api/webhooks/...
LANGUAGE=EN                   # or "FR" for French
# If using email:
EMAIL_FROM=noreply@example.com
EMAIL_TO=team@example.com
```

### 5. Activate the workflow
Click **Active** toggle in n8n. It will run every Friday at 5PM.

## How It Works

```
┌─────────────────┐
│ Friday 5PM Cron  │
└────────┬────────┘
         │
    ┌────┴────┐
    │  Fetch  │──→ GitHub Commits (last 7 days)
    │  Fetch  │──→ GitHub Closed Issues
    │  Fetch  │──→ GitHub Merged PRs
    └────┬────┘
         │
    ┌────┴────────┐
    │ Merge Data  │
    └────┬────────┘
         │
    ┌────┴──────────────┐
    │ Prepare Prompt    │  Formats data into Claude prompt
    └────┬──────────────┘
         │
    ┌────┴──────────────┐
    │ Claude API Call   │  Generates narrative summary
    └────┬──────────────┘
         │
    ┌────┴────────┐
    │  Route      │──→ Discord/Slack Webhook
    │  Delivery   │──→ Email
    └─────────────┘
```

## Features

- ✅ Weekly cron trigger (Friday 5PM, configurable)
- ✅ Fetches: commits, closed issues, merged PRs from GitHub API
- ✅ Calls Claude API (`claude-sonnet-4-20250514`) for narrative summary
- ✅ Delivers via Discord/Slack webhook OR email
- ✅ Configurable: repo, destination, language (EN/FR)
- ✅ Zero custom code — all native n8n nodes

## Sample Output

### Discord/Slack
```
## 📋 Weekly Dev Summary — myorg/myapp
**Week**: 2026-05-07 → 2026-05-14
**Stats**: 23 commits | 5 issues closed | 8 PRs merged

This was a productive week for the project. The team focused on two major areas:
improving the authentication flow and optimizing database queries...

[Full narrative summary continues]
```

### Email
Subject: `📋 Weekly Dev Summary — myorg/myapp (2026-05-07 → 2026-05-14)`

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_REPO` | (required) | GitHub repo in `owner/repo` format |
| `DELIVERY_METHOD` | `webhook` | `webhook` for Discord/Slack, `email` for email |
| `WEBHOOK_URL` | (required) | Discord or Slack webhook URL |
| `EMAIL_FROM` | (required) | Sender email address |
| `EMAIL_TO` | (required) | Recipient email address |
| `LANGUAGE` | `EN` | `EN` for English, `FR` for French |
| `GITHUB_API_URL` | `https://api.github.com` | Override for GitHub Enterprise |

## Troubleshooting

- **No data fetched**: Check GitHub token has `repo` scope
- **Claude API error**: Verify API key and model access
- **Webhook not delivered**: Test webhook URL with `curl -X POST`
- **Workflow not triggering**: Ensure it's toggled to Active in n8n
