# Changelog Generator

A bash script that automatically generates a structured `CHANGELOG.md` from a project's git history. Categorizes commits into **Added**, **Fixed**, **Changed**, and **Removed** sections based on conventional commit prefixes.

## Setup (3 steps)

```bash
# 1. Download the script
curl -O https://raw.githubusercontent.com/<your-username>/claude-builders-bounty/changelog-skill/changelog/changelog.sh
chmod +x changelog.sh

# 2. Run it in any git repository
cd /path/to/your/repo
/path/to/changelog.sh

# 3. Check the generated CHANGELOG.md
cat CHANGELOG.md
```

## Usage

```bash
# Auto-detect latest tag and generate changelog
./changelog.sh

# Specify a starting tag
./changelog.sh v1.0.0

# Specify tag and repo path
./changelog.sh v2.0.0 /path/to/repo
```

## How It Works

1. Finds the latest git tag (or uses the one you specify)
2. Collects all commits between that tag and HEAD
3. Auto-categorizes each commit by prefix:
   - `feat`, `add`, `create`, `implement` → **Added**
   - `fix`, `bug`, `patch`, `resolve` → **Fixed**
   - `change`, `update`, `refactor`, `improve` → **Changed**
   - `remove`, `delete`, `drop`, `deprecate` → **Removed**
4. Prepends the new entries to existing `CHANGELOG.md`

## Sample Output

```markdown
# Changelog

## [v2.1.0] - 2026-05-13

### Added

- feat: add dark mode support (a3f2b1c)
- create new dashboard component (b7d4e2f)
- implement CSV export for reports (c1a8d3e)

### Fixed

- fix: resolve login timeout on slow connections (d9c5f7a)
- patch memory leak in websocket handler (e2b6g4d)

### Changed

- update dependencies to latest versions (f5a3h8c)
- refactor database query builder (g8d2j1e)

### Removed

- drop support for Node.js 14 (h1e5k9f)
```

## Requirements

- Bash 4.0+
- Git
- A repository with git tags (recommended)

## License

MIT
