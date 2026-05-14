# CHANGELOG Generator Skill

> Automatically generate a structured `CHANGELOG.md` from a project's git history.

## Overview

This skill parses `git log` output, categorizes commits by [Conventional Commits](https://www.conventionalcommits.org/) format, and produces a clean, semantically-versioned `CHANGELOG.md`.

## Usage

### Via Claude Code Command

```
/generate-changelog
```

Claude will execute the generator script and produce `CHANGELOG.md` in your project root.

### Via CLI (Node.js)

```bash
node skills/changelog-generator/generate.js [options]
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--repo <path>` | Path to git repository | `.` (current directory) |
| `--output <path>` | Output file path | `CHANGELOG.md` |
| `--from <date>` | Start date filter (YYYY-MM-DD) | Since last tag |
| `--to <date>` | End date filter (YYYY-MM-DD) | Today |
| `--tag <version>` | Version tag for the release | Auto-detected |
| `--no-auto-tag` | Skip auto version tag detection | — |

### Examples

```bash
# Generate CHANGELOG from last tag to HEAD
node skills/changelog-generator/generate.js

# Generate for a specific date range
node skills/changelog-generator/generate.js --from 2026-01-01 --to 2026-03-01

# Generate for a specific repo
node skills/changelog-generator/generate.js --repo /path/to/project
```

## Commit Categories

The generator maps Conventional Commit prefixes to sections:

| Prefix | Section |
|--------|---------|
| `feat` | 🚀 Added |
| `fix` | 🐛 Fixed |
| `docs` | 📚 Documentation |
| `style` | 💄 Changed |
| `refactor` | ♻️ Changed |
| `perf` | ⚡ Changed |
| `test` | 🧪 Changed |
| `build` | 📦 Changed |
| `ci` | 👷 Changed |
| `chore` | 🔧 Changed |
| `revert` | ⏪ Removed |
| `remove` | 🗑️ Removed |
| *(uncategorized)* | 🔀 Other |

## Output Format

```markdown
# Changelog

## [1.2.0] - 2026-05-15

### 🚀 Added
- Add user authentication flow (abc1234)
- Add dark mode support (def5678)

### 🐛 Fixed
- Fix login redirect loop (ghi9012)

### ♻️ Changed
- Refactor database connection pool (jkl3456)

## [1.1.0] - 2026-04-01
...
```

## Requirements

- Node.js >= 14
- Git (must be run inside or pointing to a git repository)

## Setup (3 steps)

1. Copy `skills/changelog-generator/` into your project
2. Run `node skills/changelog-generator/generate.js`
3. Done — `CHANGELOG.md` is generated in your project root
