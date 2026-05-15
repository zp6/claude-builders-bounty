# n8n Weekly Dev Summary Workflow

Automated weekly narrative summary of GitHub repo activity using the Claude API.

## Setup (5 steps)

### 1. Import the workflow
In n8n: **Workflows → Import from File** → select `workflow.json`

### 2. Configure GitHub credentials
- Create a GitHub Personal Access Token with `repo` scope
- In n8n: **Credentials → Add → Header Auth**
- Name: "GitHub Token", Header Name: "Authorization", Value: "token YOUR_GITHUB_TOKEN"

### 3. Configure Claude API
- Edit the "Summarize with Claude" node
- Add your Anthropic API key in the headers (`x-api-key`)

### 4. Configure destination
- The workflow uses Slack by default
- To use Discord: replace "Send Summary" node with a Discord webhook node
- To use email: replace with an email node

### 5. Set environment variables
In n8n settings:
```
GITHUB_REPO=owner/repo       # Target repository
LANGUAGE=en                   # Output language (en/fr)
```

## What it does

Every Friday at 5PM:
1. Fetches commits, closed issues, and merged PRs from the past week
2. Sends data to Claude for narrative summarization
3. Delivers the summary to your configured channel

## Configurable Variables

| Variable | Description | Default |
|----------|-------------|---------|
| GITHUB_REPO | Target repository | Required |
| LANGUAGE | Summary language (en/fr) | en |
| Schedule | Cron expression | Friday 5PM |

## Sample Output

```
Weekly Dev Summary — my-org/my-project

🔥 Highlights
This week saw significant progress on the authentication module...
Three new features were merged including...

👥 Contributors
@alice shipped 12 commits, @bob closed 8 issues...

🎯 Focus Areas
- Authentication & Security
- Performance optimizations
- Bug fixes in the API layer

🔮 What's Next
Based on open issues, expect progress on...
```
