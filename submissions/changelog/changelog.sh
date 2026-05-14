#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [since_tag] [repo_path]
# If no tag specified, uses the latest git tag as baseline.

set -euo pipefail

REPO_PATH="${2:-.}"
cd "$REPO_PATH"

# Ensure we're in a git repo
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: Not a git repository" >&2
  exit 1
fi

# Determine the range
SINCE_TAG="${1:-}"
if [ -z "$SINCE_TAG" ]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -n "$SINCE_TAG" ]; then
  RANGE="$SINCE_TAG..HEAD"
  HEADER="Changes since $SINCE_TAG"
else
  RANGE="HEAD"
  HEADER="All changes"
fi

# Get the new version for the header
NEW_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")
if [ "$NEW_VERSION" = "$SINCE_TAG" ]; then
  NEW_VERSION="Unreleased"
fi
TODAY=$(date +%Y-%m-%d)

# Fetch commits and categorize
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  HASH=$(echo "$line" | cut -d'|' -f1)
  MSG=$(echo "$line" | cut -d'|' -f2-)

  # Skip merge commits
  if echo "$MSG" | grep -qi "^merge "; then
    continue
  fi

  # Categorize based on conventional commit prefixes and keywords
  if echo "$MSG" | grep -qiE '^(feat|add|create|introduce|implement|support|new )'; then
    ADDED="$ADDED\n- $MSG ($HASH)"
  elif echo "$MSG" | grep -qiE '^(fix|bug|patch|resolve|repair|correct|hotfix)'; then
    FIXED="$FIXED\n- $MSG ($HASH)"
  elif echo "$MSG" | grep -qiE '^(remove|delete|drop|deprecate|strip|eliminate)'; then
    REMOVED="$REMOVED\n- $MSG ($HASH)"
  elif echo "$MSG" | grep -qiE '^(change|update|refactor|improve|enhance|modify|rename|move|upgrade|migrate|rework)'; then
    CHANGED="$CHANGED\n- $MSG ($HASH)"
  else
    # Default: put in Changed
    CHANGED="$CHANGED\n- $MSG ($HASH)"
  fi
done < <(
  git log "$RANGE" --pretty=format:"%h|%s" --no-merges 2>/dev/null || true
)

# Count total changes
TOTAL=$(git log "$RANGE" --oneline --no-merges 2>/dev/null | wc -l | tr -d ' ')

if [ "$TOTAL" -eq 0 ]; then
  echo "No new commits found since $SINCE_TAG"
  exit 0
fi

# Generate CHANGELOG.md
OUTPUT="## [$NEW_VERSION] - $TODAY"
OUTPUT="$OUTPUT\n\n"

# Build sections
sections=0
if [ -n "$ADDED" ]; then
  OUTPUT="$OUTPUT### Added\n"
  OUTPUT="$OUTPUT$(echo -e "$ADDED")\n\n"
  sections=$((sections + 1))
fi

if [ -n "$FIXED" ]; then
  OUTPUT="$OUTPUT### Fixed\n"
  OUTPUT="$OUTPUT$(echo -e "$FIXED")\n\n"
  sections=$((sections + 1))
fi

if [ -n "$CHANGED" ]; then
  OUTPUT="$OUTPUT### Changed\n"
  OUTPUT="$OUTPUT$(echo -e "$CHANGED")\n\n"
  sections=$((sections + 1))
fi

if [ -n "$REMOVED" ]; then
  OUTPUT="$OUTPUT### Removed\n"
  OUTPUT="$OUTPUT$(echo -e "$REMOVED")\n\n"
  sections=$((sections + 1))
fi

# If CHANGELOG.md exists, prepend; otherwise create new
if [ -f "CHANGELOG.md" ]; then
  # Remove the leading # Changelog header if it exists, we'll add it back
  BODY=$(echo -e "$OUTPUT")
  # Prepend to existing file, keeping the header
  HEADER_LINE="# Changelog"
  
  # Check if first line is the header
  FIRST_LINE=$(head -n1 CHANGELOG.md)
  if [ "$FIRST_LINE" = "$HEADER_LINE" ]; then
    # Remove first two lines (header + blank line), prepend new content
    echo "$HEADER_LINE" > CHANGELOG.new
    echo "" >> CHANGELOG.new
    echo -e "$OUTPUT" >> CHANGELOG.new
    tail -n +3 CHANGELOG.md >> CHANGELOG.new
    mv CHANGELOG.new CHANGELOG.md
  else
    # Just prepend
    echo -e "$OUTPUT$(cat CHANGELOG.md)" > CHANGELOG.md
  fi
else
  echo "# Changelog" > CHANGELOG.md
  echo "" >> CHANGELOG.md
  echo -e "$OUTPUT" >> CHANGELOG.md
fi

echo "✅ CHANGELOG.md updated with $TOTAL commits ($sections categories) since ${SINCE_TAG:-beginning}"
echo ""
echo "Preview:"
echo "---"
head -30 CHANGELOG.md
