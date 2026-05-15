# Destructive Command Guard Hook

A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
# 1. Copy the hook
mkdir -p ~/.claude/hooks && cp block-destructive.sh ~/.claude/hooks/block-destructive.sh && chmod +x ~/.claude/hooks/block-destructive.sh

# 2. Add to settings (append to ~/.claude/settings.json)
# Add this to your hooks configuration:
# "hooks": {
#   "pre-tool-use": [
#     { "command": "~/.claude/hooks/block-destructive.sh", "matcher": "Bash" }
#   ]
# }
```

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /`, `rm -rf ~` | Recursive root/home deletion |
| `DROP TABLE`, `DROP DATABASE` | Database destruction |
| `TRUNCATE` | Table wipe |
| `DELETE FROM` (without WHERE) | Mass row deletion |
| `git push --force` | Force pushing to remote |
| `dd if=`, `mkfs.` | Disk operations |
| `chmod -R 777 /` | Permission destruction |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp
- Attempted command
- Project path

## How it works

1. Reads tool input from stdin (JSON)
2. Extracts the bash command
3. Checks against dangerous patterns
4. Special case: `DELETE FROM` without `WHERE` clause
5. Returns `{"decision": "block"}` or `{"decision": "approve"}`

## Normal commands

Normal bash commands pass through without interference. Only the specific dangerous patterns above are blocked.
