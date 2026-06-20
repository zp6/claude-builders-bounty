# 🛡️ Claude Code Pre-Tool-Use Safety Hook

A safety hook for [Claude Code](https://claude.ai/claude-code) that intercepts and blocks dangerous bash commands before they execute.

## What It Blocks

| Category | Patterns |
|----------|----------|
| **File Destruction** | `rm -rf`, `shred`, `dd` to devices |
| **Database** | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` (no WHERE) |
| **Git** | `git push --force`, `git reset --hard`, `git clean -fd` |
| **System** | `shutdown`, `mkfs`, `chmod 777`, fork bombs |
| **Credentials** | `ssh-keygen` overwrite without backup |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Install

```bash
# Copy the hook to your Claude hooks directory
git clone https://github.com/zp6/claude-builders-bounty.git /tmp/cbb
cp /tmp/cbb/hooks/pre_tool_use_hook.py ~/.claude/hooks/

# Add to Claude Code hooks config
echo '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/pre_tool_use_hook.py"}]}]}}' > ~/.claude/hooks/hooks.json
```

Two commands, you're protected. The hook activates on the next Claude Code session.

## How It Works

1. Claude Code sends a `PreToolUse` event (JSON on stdin) for every Bash tool call
2. The hook parses the command and checks against dangerous patterns
3. If blocked → returns `{ "decision": "block", "reason": "..." }` and logs the attempt
4. If safe → returns `{ "decision": "allow" }`

Safe contexts (comments, `echo`, `grep`) are detected and allowed through.

## Uninstall

```bash
rm ~/.claude/hooks/pre_tool_use_hook.py
```

## License

MIT
