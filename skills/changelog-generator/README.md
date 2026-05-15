# CHANGELOG Generator

Automatically generates a structured `CHANGELOG.md` from git history.

## Setup (3 steps)

1. Copy this folder to your project
2. Run: `bash skills/changelog-generator/generate-changelog.sh`
3. Check the generated `CHANGELOG.md`

## Usage

```bash
# Generate from last tag to HEAD
bash generate-changelog.sh

# Generate from specific tag
bash generate-changelog.sh v1.2.0

# Custom output file
bash generate-changelog.sh v1.2.0 docs/CHANGELOG.md
```

## Sample Output

```markdown
# Changelog

## 1.3.0 (2025-05-15)

### Added
- feat: add user authentication module
- feat: implement dark mode toggle

### Fixed
- fix: resolve login redirect loop
- fix: correct timezone handling in scheduler

### Changed
- refactor: optimize database query layer
- chore: update dependencies

### Removed
- deprecate: remove legacy API v1 endpoints
```

## How it works

1. Detects the latest git tag
2. Fetches all commits since that tag
3. Categorizes by conventional commit prefix
4. Generates formatted CHANGELOG.md
