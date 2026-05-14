# Claude Review — AI-powered PR Review Agent

A Python CLI tool that analyzes GitHub PR diffs and generates structured Markdown reviews with risk assessment, improvement suggestions, and confidence scores.

## Setup (3 steps)

```bash
# 1. Install (no dependencies needed — pure Python stdlib)
curl -O https://raw.githubusercontent.com/<your-username>/claude-builders-bounty/pr-review-agent/pr-review/claude-review.py

# 2. Run on any GitHub PR
python claude-review.py --pr https://github.com/owner/repo/pull/123

# 3. For private repos, set your GitHub token
export GITHUB_TOKEN=ghp_xxxxx
python claude-review.py --pr https://github.com/owner/repo/pull/456
```

## Usage

```bash
# Review a GitHub PR (public repo)
python claude-review.py --pr https://github.com/pandas-dev/pandas/pull/61789

# Review a private PR (requires token)
python claude-review.py --pr https://github.com/your-org/repo/pull/42 --token ghp_xxxxx

# Review from a local diff file
python claude-review.py --diff my-changes.patch

# Save output to file
python claude-review.py --pr https://github.com/owner/repo/pull/1 --output review.md
```

## GitHub Action Integration

Create `.github/workflows/pr-review.yml`:

```yaml
name: AI PR Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Download reviewer
        run: curl -O https://raw.githubusercontent.com/<your-repo>/claude-review.py
      - name: Run review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python claude-review.py --pr ${{ github.event.pull_request.html_url }} --output review.md
      - name: Post review comment
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              body: review
            });
```

## Sample Output

```
# 🤖 PR Review

**PR**: CLN: remove and update for outdated _item_cache
**Author**: @chilin0525 | **Branch**: `cln-item-cache` → `main`

## 📊 Summary

This PR is primarily removing code — affecting Python files.

| Metric | Value |
|--------|-------|
| Files changed | 11 |
| Additions | +0 |
| Deletions | -168 |
| Confidence | Low |

## ⚠️ Risks
- 🔴 Potential secret exposure in `config.py`: hardcoded credential
- 🟡 Database schema change — review for backwards compatibility

## 💡 Suggestions
- 💡 Large change in `api/handlers.py` (312 lines). Consider splitting.
- 💡 Dependency file changed: `requirements.txt` — review for version pinning

## 🔍 Confidence Score: **Medium**
> Moderate complexity. Recommend careful review of flagged items.
```

## Features

- **Zero dependencies** — pure Python stdlib (Python 3.8+)
- **Auto-categorization** of changes by file type
- **Risk detection**: hardcoded secrets, code injection patterns, schema changes
- **Confidence scoring**: Low / Medium / High
- **GitHub API integration** with optional token auth
- **CLI and GitHub Action** workflows

## Tested On

| PR | Repo | Files | Verdict |
|----|------|-------|---------|
| pandas-dev/pandas#61789 | pandas | 11 files, -168 lines | ✅ Clean removal PR |
| See `sample-outputs/` for more examples | | | |

## License

MIT
