# Claude PR Review Agent

A CLI tool that takes a GitHub PR, analyzes the diff with Claude, and returns a structured Markdown review.

## Setup

```bash
# 1. Install dependencies (none! pure Python stdlib)
chmod +x claude-review

# 2. Set environment variables
export GITHUB_TOKEN=ghp_your_token
export ANTHROPIC_API_KEY=sk-ant-your_key
```

## Usage

```bash
# Review a PR (print to stdout)
python claude-review --pr https://github.com/owner/repo/pull/123

# Post review as a PR comment
python claude-review --pr https://github.com/owner/repo/pull/123 --post-comment

# Save review to file
python claude-review --pr owner/repo/123 --output review.md

# Shorthand
python claude-review --pr owner/repo/123
```

## Output Format

```markdown
## Summary
Brief 2-3 sentence summary of the changes.

## Risks
- Risk 1
- Risk 2

## Suggestions
- Suggestion 1
- Suggestion 2

## Confidence: Medium
```

## Requirements
- Python 3.7+
- GitHub token
- Anthropic API key

Zero external dependencies — uses only Python stdlib.
