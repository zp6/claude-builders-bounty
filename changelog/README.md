# Changelog Generator

A bash script that generates a structured `CHANGELOG.md` from your git history, automatically categorizing commits since the last tag.

## Install & Use

1. **Copy the script** into your repo (or symlink it):

   ```bash
   cp changelog/changelog.sh ./changelog.sh
   chmod +x changelog.sh
   ```

2. **Run it** from inside any git repository:

   ```bash
   ./changelog.sh              # writes CHANGELOG.md at repo root
   ./changelog.sh docs/CHANGELOG.md   # custom output path
   ```

3. **Done!** Open the generated `CHANGELOG.md` — commits are grouped under **Added**, **Changed**, **Fixed**, **Removed**, and **Other**.

## How It Works

- Finds the most recent git tag (`git describe --tags --abbrev=0`).
- Collects all commit messages from that tag to `HEAD`.
- Classifies each commit subject by conventional-commit prefix (`feat`, `fix`, `refactor`, etc.).
- Writes a Markdown file with sections for each category.

## Example Output

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] — 2026-06-20

*Changes since **v0.1.0** until **HEAD**.*

### Added
  - feat: add user authentication flow
  - add dark mode support

### Fixed
  - fix: resolve crash on empty input
  - fixed memory leak in worker thread

### Changed
  - refactor: simplify config parsing
  - update dependencies to latest versions
```
