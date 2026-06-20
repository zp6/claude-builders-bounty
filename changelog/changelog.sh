#!/usr/bin/env bash
set -euo pipefail

# ── changelog.sh ──────────────────────────────────────────────────────
# Generates a structured CHANGELOG.md from git history since the last tag.
# Usage: ./changelog.sh [output_file]
#   output_file defaults to CHANGELOG.md in the repo root.
# ───────────────────────────────────────────────────────────────────────

REPO_ROOT="$(git rev-parse --show-toplevel)"
OUTPUT="${1:-$REPO_ROOT/CHANGELOG.md}"

# Find the most recent tag (annotated or lightweight)
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"

if [ -z "$LAST_TAG" ]; then
  echo ":: No tags found — using full history."
  RANGE="HEAD"
else
  RANGE="$LAST_TAG..HEAD"
fi

# Collect commit messages (subject + body) in the range
COMMITS="$(git log "$RANGE" --pretty=format:"---COMMIT---%n%B" 2>/dev/null)"

if [ -z "$COMMITS" ]; then
  echo ":: No commits found since ${LAST_TAG:-the beginning}."
  exit 0
fi

# ── Classify commits ──────────────────────────────────────────────────
declare -A SECTIONS
SECTIONS[Added]=""
SECTIONS[Changed]=""
SECTIONS[Fixed]=""
SECTIONS[Removed]=""
SECTIONS[Other]=""

while IFS= read -r line; do
  # Skip separators
  [ "$line" = "---COMMIT---" ] && continue

  # Trim leading/trailing whitespace
  entry="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [ -z "$entry" ] && continue

  # First non-empty line = subject; treat as conventional-commit prefix
  shopt -s nocasematch
  if [[ "$entry" =~ ^(feat|add|added|new)\b ]]; then
    SECTIONS[Added]+="  - $entry"$'\n'
  elif [[ "$entry" =~ ^fix(ed|ed)?\b ]]; then
    SECTIONS[Fixed]+="  - $entry"$'\n'
  elif [[ "$entry" =~ ^(change|update|updated|improve|refactor|chore)\b ]]; then
    SECTIONS[Changed]+="  - $entry"$'\n'
  elif [[ "$entry" =~ ^(remove|removed|delete|deleted|deprecate)\b ]]; then
    SECTIONS[Removed]+="  - $entry"$'\n'
  else
    SECTIONS[Other]+="  - $entry"$'\n'
  fi
  shopt -u nocasematch
done <<< "$COMMITS"

# ── Build markdown ────────────────────────────────────────────────────
DATE="$(date +%Y-%m-%d)"

cat > "$OUTPUT" <<HEADER
# Changelog

All notable changes to this project will be documented in this file.

HEADER

if [ -n "$LAST_TAG" ]; then
  cat >> "$OUTPUT" <<SECTION

## [Unreleased] — $DATE

*Changes since **$LAST_TAG** until **HEAD**.*
SECTION
else
  cat >> "$OUTPUT" <<SECTION

## [$DATE]

*Full history (no prior tags).*
SECTION
fi

for section in Added Changed Fixed Removed Other; do
  content="${SECTIONS[$section]}"
  [ -z "$content" ] && continue
  echo "" >> "$OUTPUT"
  echo "### $section" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
  printf "%s" "$content" >> "$OUTPUT"
done

echo "" >> "$OUTPUT"

echo "✅ CHANGELOG written to $OUTPUT ($(wc -l < "$OUTPUT") lines)"
