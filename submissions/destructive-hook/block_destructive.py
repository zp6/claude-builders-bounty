#!/usr/bin/env python3
"""
pre-tool-use hook — Block destructive bash commands in Claude Code
Install: cp block_destructive.py ~/.claude/hooks/
Config: Add to ~/.claude/hooks.json

Detects and blocks: rm -rf, DROP TABLE, TRUNCATE, DELETE FROM without WHERE,
git push --force, and other destructive patterns.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# Patterns that get BLOCKED (exit code 2 = block + show message)
BLOCKED_PATTERNS = [
    # rm -rf variants
    (r'\brm\s+.*-[rRf].*\s+/', "Blocked: `rm -rf` with root/system path"),
    (r'\brm\s+.*-[rRf].*\s+\*', "Blocked: `rm -rf` with wildcard"),
    (r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\s+', "Blocked: `rm -rf` detected"),
    (r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\s+', "Blocked: `rm -rf` detected"),
    
    # DROP TABLE / DATABASE
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', "Blocked: `DROP TABLE/DATABASE/SCHEMA` detected"),
    
    # TRUNCATE
    (r'\bTRUNCATE\s+(TABLE\s+)?[\w`\"[\]]+', "Blocked: `TRUNCATE` detected"),
    
    # DELETE FROM without WHERE
    (r'\bDELETE\s+FROM\b(?![\s\S]*?\bWHERE\b)', "Blocked: `DELETE FROM` without WHERE clause"),
    
    # git push --force
    (r'\bgit\s+push\s+.*--force', "Blocked: `git push --force` detected"),
    (r'\bgit\s+push\s+.*-f\b', "Blocked: `git push -f` detected"),
    (r'\bgit\s+push\s+.*--delete', "Blocked: `git push --delete` detected"),
    
    # chmod 777 / 666
    (r'\bchmod\s+[0-7]*[0-7]77\b', "Blocked: `chmod 777` — overly permissive"),
    (r'\bchmod\s+[0-7]*666\b', "Blocked: `chmod 666` — overly permissive"),
    
    # curl/wget pipe to sh
    (r'\bcurl\s+.*\|\s*(ba)?sh', "Blocked: Piping curl output to shell"),
    (r'\bwget\s+.*\|\s*(ba)?sh', "Blocked: Piping wget output to shell"),
    
    # Format / wipe disk
    (r'\bmkfs\b', "Blocked: `mkfs` — filesystem formatting"),
    (r'\bdd\s+.*of=/dev/', "Blocked: `dd` writing to device"),
    
    # Kill all / system processes
    (r'\bkillall\b', "Blocked: `killall` — kills all matching processes"),
    (r'\bkill\s+-9\s+1\b', "Blocked: Killing PID 1 (init)"),
]

# Patterns that get WARNED (exit code 0 = allow but show warning)
WARNING_PATTERNS = [
    (r'\bgit\s+reset\s+--hard', "⚠️ Warning: `git reset --hard` will discard uncommitted changes"),
    (r'\bgit\s+clean\s+-', "⚠️ Warning: `git clean` will delete untracked files"),
    (r'\bgit\s+checkout\s+\.\s*$', "⚠️ Warning: Discarding all working directory changes"),
    (r'\bsudo\s+rm\b', "⚠️ Warning: Deleting with sudo privileges"),
    (r'\bnpm\s+publish\b', "⚠️ Warning: Publishing to npm registry"),
    (r'\bdocker\s+(rm|rmi)\s+', "⚠️ Warning: Removing Docker resources"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
PROJECT_PATH = os.getcwd()


def log_blocked(command: str, reason: str):
    """Log a blocked attempt."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] BLOCKED | {reason} | cmd: {command[:200]} | project: {PROJECT_PATH}\n")


def log_warned(command: str, reason: str):
    """Log a warning."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] WARNED | {reason} | cmd: {command[:200]} | project: {PROJECT_PATH}\n")


def check_command(command: str) -> tuple:
    """Check command against patterns. Returns (action, reason)."""
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', command.strip())
    
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE | re.DOTALL):
            return ("block", reason)
    
    for pattern, reason in WARNING_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE | re.DOTALL):
            return ("warn", reason)
    
    return ("allow", "")


def main():
    # Read hook input from stdin (Claude Code provides JSON)
    try:
        raw = sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
        else:
            data = {}
    except (json.JSONDecodeError, EOFError):
        data = {}
    
    # Extract the bash command
    command = ""
    if isinstance(data, dict):
        # Claude Code hooks format: tool_input contains the command
        tool_input = data.get("tool_input", {})
        if isinstance(tool_input, dict):
            command = tool_input.get("command", "")
        elif isinstance(tool_input, str):
            command = tool_input
        # Fallback: try tool_name + parameters
        if not command:
            params = data.get("parameters", {})
            command = params.get("command", "")
    
    if not command:
        # No command to check, allow
        sys.exit(0)
    
    action, reason = check_command(command)
    
    if action == "block":
        log_blocked(command, reason)
        # Exit code 2 = block with message (Claude Code hooks convention)
        print(f"🚫 {reason}. This command has been blocked for safety.", file=sys.stderr)
        print(f"   If you really need to run this, the user can override manually.", file=sys.stderr)
        sys.exit(2)
    
    elif action == "warn":
        log_warned(command, reason)
        # Exit code 0 = allow but print warning
        print(f"⚠️ {reason}", file=sys.stderr)
        sys.exit(0)
    
    else:
        # Normal command, no action needed
        sys.exit(0)


if __name__ == "__main__":
    main()
