#!/usr/bin/env bash
# Pre-tool-use hook: Block destructive bash commands
# Install: cp block-destructive.sh ~/.claude/hooks/block-destructive.sh && chmod +x ~/.claude/hooks/block-destructive.sh
# Config: Add to ~/.claude/settings.json hooks.pre-tool-use

set -euo pipefail

# Read the tool input from stdin
INPUT=$(cat)

# Extract the command from the JSON input
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
  echo '{"decision": "approve"}'
  exit 0
fi

# Dangerous patterns to block
DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf /*"
  "rm -rf ${HOME}"
  "DROP TABLE"
  "DROP DATABASE"
  "TRUNCATE TABLE"
  "TRUNCATE"
  "git push --force"
  "git push -f "
  "git push --force-with-lease"
  "DELETE FROM"
  ":(){:|:&};:"
  "dd if="
  "mkfs."
  "> /dev/sd"
  "chmod -R 777 /"
  "chown -R .* /"
)

# Check for DELETE FROM without WHERE clause
if echo "$COMMAND" | grep -qiE "DELETE FROM"; then
  if ! echo "$COMMAND" | grep -qiE "WHERE"; then
    LOG_FILE="${HOME}/.claude/hooks/blocked.log"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$(date -Iseconds)] BLOCKED (DELETE without WHERE): $COMMAND | Project: ${PWD:-unknown}" >> "$LOG_FILE"
    echo '{"decision": "block", "reason": "Blocked: DELETE FROM without WHERE clause. This would delete all rows. Add a WHERE clause to proceed."}'
    exit 0
  fi
fi

# Check all dangerous patterns
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    LOG_FILE="${HOME}/.claude/hooks/blocked.log"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$(date -Iseconds)] BLOCKED ($pattern): $COMMAND | Project: ${PWD:-unknown}" >> "$LOG_FILE"
    echo "{"decision": "block", "reason": "Blocked: dangerous command detected matching '$pattern'. If you really need to run this, use the --confirm flag or ask the user."}"
    exit 0
  fi
done

echo '{"decision": "approve"}'
