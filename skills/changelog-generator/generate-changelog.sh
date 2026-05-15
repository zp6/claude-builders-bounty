#!/usr/bin/env bash
# CHANGELOG Generator - Generates structured CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [since-tag] [output-file]

set -euo pipefail

SINCE_TAG="${1:-}"
OUTPUT="${2:-CHANGELOG.md}"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)" 2>/dev/null || echo "project")

# Find the latest tag if not specified
if [ -z "$SINCE_TAG" ]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Get commits since tag (or all commits if no tag)
if [ -n "$SINCE_TAG" ]; then
  COMMITS=$(git log "$SINCE_TAG"..HEAD --pretty=format:"%s" 2>/dev/null)
  VERSION="${SINCE_TAG#v} ($(date +%Y-%m-%d))"
else
  COMMITS=$(git log --pretty=format:"%s" 2>/dev/null)
  VERSION="Unreleased ($(date +%Y-%m-%d))"
fi

if [ -z "$COMMITS" ]; then
  echo "No new commits found since $SINCE_TAG"
  exit 0
fi

# Categorize commits
declare -a ADDED FIXED CHANGED REMOVED

while IFS= read -r commit; do
  lower=$(echo "$commit" | tr '[:upper:]' '[:lower:]')
  if echo "$lower" | grep -qE '^(feat|add|feature)[:(!]'; then
    ADDED+=("$commit")
  elif echo "$lower" | grep -qE '^(fix|bugfix|hotfix)[:(!]'; then
    FIXED+=("$commit")
  elif echo "$lower" | grep -qE '^(remove|delete|deprecate)[:(!]'; then
    REMOVED+=("$commit")
  else
    CHANGED+=("$commit")
  fi
done <<< "$COMMITS"

# Generate CHANGELOG.md
{
  echo "# Changelog"
  echo ""
  echo "## $VERSION"
  echo ""

  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added"
    for c in "${ADDED[@]}"; do echo "- $c"; done
    echo ""
  fi

  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed"
    for c in "${FIXED[@]}"; do echo "- $c"; done
    echo ""
  fi

  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed"
    for c in "${CHANGED[@]}"; do echo "- $c"; done
    echo ""
  fi

  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed"
    for c in "${REMOVED[@]}"; do echo "- $c"; done
    echo ""
  fi
} > "$OUTPUT"

echo "Generated $OUTPUT with:"
echo "  Added: ${#ADDED[@]}, Fixed: ${#FIXED[@]}, Changed: ${#CHANGED[@]}, Removed: ${#REMOVED[@]}"
