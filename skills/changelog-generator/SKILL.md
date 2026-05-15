# CHANGELOG Generator Skill

## Usage
```
/generate-changelog
```
Or run as a bash script: `bash skills/changelog-generator/generate-changelog.sh`

## What it does
Automatically generates a structured `CHANGELOG.md` from a project's git history.

## How it works
1. Detects the latest git tag
2. Fetches all commits since that tag
3. Auto-categorizes into: Added / Fixed / Changed / Removed
4. Outputs a properly formatted CHANGELOG.md

## Categorization Rules
- **Added**: commits matching `feat:`, `add:`, `feature:`
- **Fixed**: commits matching `fix:`, `bugfix:`, `hotfix:`
- **Changed**: commits matching `change:`, `update:`, `refactor:`, `chore:`
- **Removed**: commits matching `remove:`, `delete:`, `deprecate:`

## Requirements
- Git
- Bash or Python 3
