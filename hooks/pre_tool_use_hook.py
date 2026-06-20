#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: Blocks destructive bash commands.

Intercepts dangerous bash commands before execution, logs blocked attempts,
and displays clear messages to Claude explaining why the command was blocked.

Usage: Configure in ~/.claude/hooks/hooks.json:
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/pre_tool_use_hook.py"
          }
        ]
      }
    ]
  }
}

Input (stdin): JSON from Claude Code with tool_name, tool_input, etc.
Output (stdout): JSON response with { "decision": "block", "reason": "..." } or { "decision": "allow" }
"""

import json
import sys
import os
import re
from datetime import datetime

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    # Destructive file operations
    (r'\brm\s+(-[a-zA-Z]*f[a-zA-Z]*|--force)\b', "rm with --force flag: potential mass file deletion"),
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*|--recursive)\s+.*-(?:f|--force)', "rm -rf: recursive force delete is blocked"),
    (r'\brm\s+.*--no-preserve-root\b', "rm --no-preserve-root: system root deletion risk"),
    (r'\bshred\b', "shred: permanent file destruction is blocked"),
    (r'\bdd\s+.*of=/dev/', "dd to device: potential disk destruction"),

    # Database destructive operations
    (r'\bDROP\s+TABLE\b', "DROP TABLE: irreversible table deletion is blocked"),
    (r'\bDROP\s+DATABASE\b', "DROP DATABASE: irreversible database deletion is blocked"),
    (r'\bTRUNCATE\b', "TRUNCATE: bulk data deletion without WHERE clause is blocked"),
    (r'\bDELETE\s+FROM\b(?!\s.*\bWHERE\b)', "DELETE FROM without WHERE clause: bulk data deletion is blocked"),
    (r'\bDROP\s+COLUMN\b', "DROP COLUMN: irreversible schema change is blocked"),
    (r'\bALTER\s+TABLE\b.*\bDROP\b', "ALTER TABLE DROP: irreversible schema modification is blocked"),

    # Git destructive operations
    (r'\bgit\s+push\s+.*--force\b', "git push --force: rewrites remote history, use --force-with-lease instead"),
    (r'\bgit\s+push\s+.*-f\b', "git push -f: rewrites remote history"),
    (r'\bgit\s+reset\s+.*--hard\b', "git reset --hard: discards all uncommitted changes permanently"),
    (r'\bgit\s+clean\s+.*-fd\b', "git clean -fd: deletes untracked files and directories"),
    (r'\bgit\s+branch\s+.*-D\b', "git branch -D: force-deletes branch without merge check"),
    (r'\bgit\s+filter-branch\b', "git filter-branch: rewrites entire repository history"),
    (r'\bgit\s+rebase\s+.*--abort\b', ""),  # Allow this one, not destructive
    (r'\bgit\s+reflog\s+expire\b', "git reflog expire: loses recovery history"),

    # System dangerous operations
    (r'\bshutdown\b', "shutdown: system power-off command is blocked"),
    (r'\breboot\b', "reboot: system restart command is blocked"),
    (r'\bmkfs\b', "mkfs: filesystem formatting destroys all data"),
    (r'\bchmod\s+(-R\s+)?777\b', "chmod 777: sets world-writable permissions"),
    (r'\biptables\s+.*-F\b', "iptables -F: flushes all firewall rules"),
    (r'\bkill\s+(-9|-SIGKILL)\s+1\b', "kill -9 1: attempts to kill init process"),
    (r'\b:()\s*{\s*:\|\|:\s*&\s*}\s*;', ":(){ :|:& };: fork bomb is blocked"),

    # Permission/credential destruction
    (r'\bssh-keygen\s+.*-f\b.*\s*-\s*N\b', "ssh-keygen overwrite without backup"),
]

# Patterns that should be allowed even if they contain dangerous substrings
SAFE_CONTEXTS = [
    r'echo.*DROP',       # Echoing SQL, not executing
    r'print.*DROP',       # Printing SQL
    r'comment.*#.*rm',    # Commented out commands
    r'""".*?rm.*?"""',   # Inside strings/docstrings
    r"'.*?rm.*?'",        # Inside strings
    r'cat\s+.*README',    # Reading files
    r'grep\s+.*rm\b',     # Searching for 'rm' in text
    r'#\s*(rm|DROP|DELETE)', # Shell comments
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


def is_safe_context(command):
    """Check if the dangerous pattern appears in a safe context (comment, string, echo)."""
    for safe_pattern in SAFE_CONTEXTS:
        if re.search(safe_pattern, command, re.IGNORECASE):
            return True
    return False


def check_command(command):
    """Check a command against dangerous patterns. Returns (blocked, reason) tuple."""
    if not command or not command.strip():
        return False, ""

    cmd = command.strip()

    # Skip if it's in a safe context
    if is_safe_context(cmd):
        return False, ""

    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True, reason

    return False, ""


def log_blocked(command, reason, project_path):
    """Log a blocked command attempt to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "attempted_command": command.strip(),
        "reason": reason,
        "project_path": project_path or "unknown"
    }
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Log failure should not block operation


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # If we can't parse input, allow the command (fail open)
        sys.stdout.write(json.dumps({"decision": "allow"}) + "\n")
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("project_path", os.getcwd())

    # Only intercept Bash tool calls
    if tool_name != "Bash":
        sys.stdout.write(json.dumps({"decision": "allow"}) + "\n")
        return

    command = tool_input.get("command", "") or ""

    blocked, reason = check_command(command)
    if blocked:
        log_blocked(command, reason, project_path)
        response = {
            "decision": "block",
            "reason": f"🚫 BLOCKED: {reason}\n\n"
                       f"Command: `{command.strip()}`\n\n"
                       f"This command was intercepted by the pre-tool-use safety hook. "
                       f"If you genuinely need to run this command, ask the user for explicit confirmation."
        }
        sys.stdout.write(json.dumps(response) + "\n")
        return

    sys.stdout.write(json.dumps({"decision": "allow"}) + "\n")


if __name__ == "__main__":
    main()
