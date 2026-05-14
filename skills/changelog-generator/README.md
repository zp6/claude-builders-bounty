# CHANGELOG Generator

> Auto-generate a structured `CHANGELOG.md` from git history using Conventional Commits.

## Setup (3 steps)

1. **Copy** `skills/changelog-generator/` into your project
2. **Run** `node skills/changelog-generator/generate.js`
3. **Done** — `CHANGELOG.md` is in your project root ✅

## What It Does

- Parses `git log` for [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, etc.)
- Groups commits by category: **Added**, **Fixed**, **Changed**, **Removed**, **Documentation**, and more
- Detects breaking changes (`feat!:` or `BREAKING CHANGE` in commit body)
- Supports semantic versioning via git tags
- Filters by date range

## Options

```bash
node skills/changelog-generator/generate.js [options]

  --repo <path>       Path to git repo (default: .)
  --output <path>     Output file (default: CHANGELOG.md)
  --from <date>       Start date YYYY-MM-DD
  --to <date>         End date YYYY-MM-DD
  --tag <version>     Override version tag
  --no-auto-tag       Don't use git tags
```

## Requirements

- Node.js >= 14
- Git

## Example Output

See [`SAMPLE_OUTPUT.md`](./SAMPLE_OUTPUT.md) for a real example generated from this repository.
