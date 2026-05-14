#!/usr/bin/env python3
"""
claude-review — PR Review Agent
Analyzes a GitHub PR diff and outputs a structured Markdown review.

Usage:
  python claude-review.py --pr https://github.com/owner/repo/pull/123
  python claude-review.py --pr https://github.com/owner/repo/pull/123 --token $GITHUB_TOKEN
  python claude-review.py --diff diff.patch  # local diff file
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error


def fetch_pr_diff(pr_url: str, token: str = None) -> tuple:
    """Fetch PR diff and metadata from GitHub API."""
    # Parse PR URL
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        print(f"Error: Invalid PR URL: {pr_url}", file=sys.stderr)
        sys.exit(1)
    
    owner, repo, pr_num = m.group(1), m.group(2), m.group(3)
    api_base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    # Fetch diff
    req = urllib.request.Request(api_base, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            diff_text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"Error fetching PR (HTTP {e.code}): {e.reason}", file=sys.stderr)
        sys.exit(1)
    
    # Fetch metadata (title, author, etc.)
    meta_headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "claude-review/1.0"}
    if token:
        meta_headers["Authorization"] = f"token {token}"
    
    meta_req = urllib.request.Request(api_base, headers=meta_headers)
    try:
        with urllib.request.urlopen(meta_req, timeout=30) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
    except Exception:
        meta = {}
    
    return diff_text, meta


def load_local_diff(diff_path: str) -> tuple:
    """Load a local diff file."""
    with open(diff_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read(), {}


def analyze_diff(diff_text: str) -> dict:
    """Analyze the diff and extract structured information."""
    files_changed = []
    additions = 0
    deletions = 0
    risks = []
    suggestions = []
    
    # Split by file
    current_file = None
    current_add = 0
    current_del = 0
    current_hunks = []
    
    for line in diff_text.split("\n"):
        if line.startswith("diff --git"):
            if current_file:
                files_changed.append({
                    "file": current_file,
                    "additions": current_add,
                    "deletions": current_del,
                })
            current_file = line.split(" b/")[-1] if " b/" in line else line
            current_add = 0
            current_del = 0
            current_hunks = []
        elif line.startswith("+") and not line.startswith("+++"):
            current_add += 1
            additions += 1
            current_hunks.append(line[1:])
            
            # Risk detection
            if re.search(r'(password|secret|api_key|token|private_key)\s*[=:]', line, re.I):
                risks.append(f"🔴 **Potential secret exposure** in `{current_file}`: hardcoded credential")
            if re.search(r'(eval|exec|compile)\s*\(', line):
                risks.append(f"🔴 **Code injection risk** in `{current_file}`: dynamic code execution")
            if re.search(r'(TODO|FIXME|HACK|XXX)', line, re.I):
                suggestions.append(f"💡 Unresolved marker in `{current_file}`: {re.search(r'(TODO|FIXME|HACK|XXX).*', line, re.I).group()}")
        elif line.startswith("-") and not line.startswith("---"):
            current_del += 1
            deletions += 1
    
    # Last file
    if current_file:
        files_changed.append({
            "file": current_file,
            "additions": current_add,
            "deletions": current_del,
        })
    
    # File-level analysis
    for fc in files_changed:
        fname = fc["file"]
        ext = os.path.splitext(fname)[1].lower()
        
        # Large file changes
        total = fc["additions"] + fc["deletions"]
        if total > 300:
            suggestions.append(f"💡 **Large change** in `{fname}` ({total} lines). Consider splitting into smaller PRs.")
        
        # Config files
        if fname.endswith((".env", ".env.local", ".env.production")):
            risks.append(f"🔴 **Environment file modified**: `{fname}` — verify no secrets are committed")
        
        # Database migrations
        if "migration" in fname.lower() or "schema" in fname.lower():
            risks.append(f"🟡 **Database schema change** in `{fname}` — review for backwards compatibility")
        
        # Dependency changes
        if fname in ("package.json", "requirements.txt", "go.mod", "Cargo.toml", "pom.xml"):
            suggestions.append(f"💡 **Dependency file changed**: `{fname}` — review for version pinning and license compatibility")
    
    # Summary
    summary_parts = []
    if additions > deletions * 3:
        summary_parts.append("This PR is primarily additive")
    elif deletions > additions * 3:
        summary_parts.append("This PR is primarily removing code")
    else:
        summary_parts.append("This PR involves mixed additions and modifications")
    
    file_types = set(os.path.splitext(f["file"])[1] for f in files_changed if "." in f["file"])
    if file_types:
        lang_map = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", 
                    ".go": "Go", ".rs": "Rust", ".java": "Java", ".rb": "Ruby",
                    ".jsx": "React JSX", ".tsx": "React TSX", ".css": "CSS",
                    ".html": "HTML", ".sql": "SQL", ".sh": "Shell"}
        langs = [lang_map.get(ext, ext) for ext in file_types]
        summary_parts.append(f"affecting {', '.join(langs)} files")
    
    if len(files_changed) > 20:
        summary_parts.append(f"across {len(files_changed)} files (large scope)")
    
    summary = " — ".join(summary_parts) + "."
    
    # Confidence
    if len(files_changed) <= 3 and additions + deletions < 200:
        confidence = "High"
    elif len(files_changed) <= 10 and additions + deletions < 500:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    return {
        "summary": summary,
        "files_changed": files_changed,
        "total_files": len(files_changed),
        "additions": additions,
        "deletions": deletions,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence,
    }


def format_review(analysis: dict, meta: dict) -> str:
    """Format the review as Markdown."""
    lines = []
    lines.append("# 🤖 PR Review")
    lines.append("")
    
    # Meta info
    if meta:
        title = meta.get("title", "Unknown PR")
        author = meta.get("user", {}).get("login", "unknown")
        base = meta.get("base", {}).get("ref", "?")
        head = meta.get("head", {}).get("ref", "?")
        lines.append(f"**PR**: {title}")
        lines.append(f"**Author**: @{author} | **Branch**: `{head}` → `{base}`")
        lines.append("")
    
    # Stats
    lines.append("## 📊 Summary")
    lines.append("")
    lines.append(analysis["summary"])
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Files changed | {analysis['total_files']} |")
    lines.append(f"| Additions | +{analysis['additions']} |")
    lines.append(f"| Deletions | -{analysis['deletions']} |")
    lines.append(f"| Confidence | {analysis['confidence']} |")
    lines.append("")
    
    # Changed files
    lines.append("## 📁 Files Changed")
    lines.append("")
    for fc in analysis["files_changed"]:
        lines.append(f"- `{fc['file']}` (+{fc['additions']}/-{fc['deletions']})")
    lines.append("")
    
    # Risks
    lines.append("## ⚠️ Risks")
    lines.append("")
    if analysis["risks"]:
        for r in analysis["risks"]:
            lines.append(f"- {r}")
    else:
        lines.append("- No significant risks detected ✅")
    lines.append("")
    
    # Suggestions
    lines.append("## 💡 Suggestions")
    lines.append("")
    if analysis["suggestions"]:
        for s in analysis["suggestions"]:
            lines.append(f"- {s}")
    else:
        lines.append("- No specific suggestions")
    lines.append("")
    
    # Confidence
    lines.append("## 🔍 Confidence Score")
    lines.append("")
    lines.append(f"**{analysis['confidence']}**")
    if analysis["confidence"] == "High":
        lines.append("> Small, focused change. Review straightforward.")
    elif analysis["confidence"] == "Medium":
        lines.append("> Moderate complexity. Recommend careful review of flagged items.")
    else:
        lines.append("> Large or complex change. Recommend thorough line-by-line review.")
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="AI-powered PR review tool")
    parser.add_argument("--pr", help="GitHub PR URL")
    parser.add_argument("--diff", help="Local diff file path")
    parser.add_argument("--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()
    
    token = args.token or os.environ.get("GITHUB_TOKEN", "")
    
    if args.pr:
        print(f"Fetching PR: {args.pr}...", file=sys.stderr)
        diff_text, meta = fetch_pr_diff(args.pr, token)
    elif args.diff:
        diff_text, meta = load_local_diff(args.diff)
    else:
        parser.print_help()
        sys.exit(1)
    
    print("Analyzing diff...", file=sys.stderr)
    analysis = analyze_diff(diff_text)
    
    review = format_review(analysis, meta)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        sys.stdout.buffer.write(review.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()
