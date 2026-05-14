#!/usr/bin/env node

/**
 * CHANGELOG Generator — generates a structured CHANGELOG.md from git history.
 *
 * Supports:
 *   - Conventional Commits (feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)
 *   - Semantic versioning via git tags
 *   - Date range filtering (--from, --to)
 *   - Breaking changes notation (feat!: or BREAKING CHANGE in body)
 *   - Merge commit filtering
 *
 * Usage:
 *   node generate.js [options]
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// ── CLI argument parsing ─────────────────────────────────────────────────────

function parseArgs(argv) {
  const args = { repo: '.', output: 'CHANGELOG.md' };
  for (let i = 2; i < argv.length; i++) {
    switch (argv[i]) {
      case '--repo':   args.repo = argv[++i]; break;
      case '--output': args.output = argv[++i]; break;
      case '--from':   args.from = argv[++i]; break;
      case '--to':     args.to = argv[++i]; break;
      case '--tag':    args.tag = argv[++i]; break;
      case '--no-auto-tag': args.noAutoTag = true; break;
      case '--help':
        console.log(`Usage: node generate.js [options]

Options:
  --repo <path>       Path to git repository (default: .)
  --output <path>     Output file path (default: CHANGELOG.md)
  --from <date>       Start date YYYY-MM-DD (default: since last tag)
  --to <date>         End date YYYY-MM-DD (default: today)
  --tag <version>     Version tag for this release (default: auto-detect)
  --no-auto-tag       Skip auto version tag detection
  --help              Show this help`);
        process.exit(0);
    }
  }
  return args;
}

// ── Git helpers ──────────────────────────────────────────────────────────────

function git(args, repo) {
  try {
    return execSync(`git -C "${repo}" ${args}`, { encoding: 'utf-8', maxBuffer: 10 * 1024 * 1024 }).trim();
  } catch {
    return '';
  }
}

function getTags(repo) {
  const raw = git('tag --sort=-version:refname', repo);
  if (!raw) return [];
  return raw.split('\n').filter(Boolean);
}

function getLatestTag(repo) {
  const tags = getTags(repo);
  return tags.length > 0 ? tags[0] : null;
}

function getCommits(repo, from, to) {
  const range = from ? `${from}..` : '';
  const until = to ? ` --until="${to}"` : '';
  // Format: hash|date|subject|body (body may be multiline, we use %b)
  const format = '%H%n%ai%n%s%n%b%n---COMMIT_SEP---';
  const raw = git(`log --no-merges --format="${format}" ${range}${until}`, repo);
  if (!raw) return [];

  return raw.split('---COMMIT_SEP---')
    .filter(s => s.trim())
    .map(block => {
      const lines = block.trim().split('\n');
      const hash = lines[0] || '';
      const date = lines[1] || '';
      const subject = lines[2] || '';
      const body = lines.slice(3).join('\n').trim();
      return { hash, date: date.split(' ')[0], subject, body };
    })
    .filter(c => c.hash && c.subject);
}

function getCommitsBetweenTags(repo, fromTag, toRef) {
  const range = fromTag ? `${fromTag}..${toRef || 'HEAD'}` : (toRef || 'HEAD');
  const format = '%H%n%ai%n%s%n%b%n---COMMIT_SEP---';
  const raw = git(`log --no-merges --format="${format}" ${range}`, repo);
  if (!raw) return [];

  return raw.split('---COMMIT_SEP---')
    .filter(s => s.trim())
    .map(block => {
      const lines = block.trim().split('\n');
      const hash = lines[0] || '';
      const date = lines[1] || '';
      const subject = lines[2] || '';
      const body = lines.slice(3).join('\n').trim();
      return { hash, date: date.split(' ')[0], subject, body };
    })
    .filter(c => c.hash && c.subject);
}

function getTagDate(repo, tag) {
  const d = git(`log -1 --format="%ai" ${tag}`, repo);
  return d ? d.split(' ')[0] : null;
}

// ── Commit parsing ───────────────────────────────────────────────────────────

const CATEGORY_MAP = {
  feat:     { label: '🚀 Added',         order: 1 },
  fix:      { label: '🐛 Fixed',         order: 2 },
  perf:     { label: '⚡ Performance',   order: 3 },
  revert:   { label: '⏪ Reverted',      order: 4 },
  docs:     { label: '📚 Documentation', order: 5 },
  style:    { label: '💄 Style',         order: 6 },
  refactor: { label: '♻️ Changed',       order: 7 },
  test:     { label: '🧪 Tests',         order: 8 },
  build:    { label: '📦 Build',         order: 9 },
  ci:       { label: '👷 CI',            order: 10 },
  chore:    { label: '🔧 Maintenance',   order: 11 },
};

function parseCommit(commit) {
  // Match: type(scope)!: description  or  type!: description  or  type: description
  const match = commit.subject.match(/^(\w+)(?:\(([^)]*)\))?(!)?:\s*(.*)/);
  const isBreakingByBody = /BREAKING[ -]CHANGE/i.test(commit.body);

  if (!match) {
    return { ...commit, type: 'other', scope: '', breaking: isBreakingByBody, description: commit.subject };
  }

  const type = match[1].toLowerCase();
  const scope = match[2] || '';
  const breaking = !!match[3] || isBreakingByBody;
  const description = match[4];

  return { ...commit, type, scope, breaking, description };
}

function categorize(parsed) {
  const cat = CATEGORY_MAP[parsed.type];
  return cat ? cat.label : '🔀 Other';
}

function groupCommits(commits) {
  const parsed = commits.map(parseCommit);
  const groups = {};

  for (const p of parsed) {
    const cat = categorize(p);
    if (!groups[cat]) groups[cat] = [];
    groups[cat].push(p);
  }

  // Sort categories by their defined order
  const orderMap = {};
  for (const [, v] of Object.entries(CATEGORY_MAP)) orderMap[v.label] = v.order;
  orderMap['🔀 Other'] = 99;

  const sorted = Object.entries(groups)
    .sort(([a], [b]) => (orderMap[a] || 99) - (orderMap[b] || 99));

  return sorted;
}

// ── Output formatting ────────────────────────────────────────────────────────

function formatEntry(p) {
  const short = p.hash.slice(0, 7);
  const scope = p.scope ? `**${p.scope}**: ` : '';
  const breaking = p.breaking ? ' **BREAKING**' : '';
  return `- ${scope}${p.description}${breaking} (${short})`;
}

function renderSection(title, entries) {
  let md = `### ${title}\n\n`;
  for (const e of entries) md += formatEntry(e) + '\n';
  return md + '\n';
}

function renderChangelog(releases) {
  let md = '# Changelog\n\n';
  md += '> All notable changes to this project will be documented in this file.\n\n';

  for (const release of releases) {
    md += `## [${release.version}] - ${release.date}\n\n`;
    if (release.breakingNotes.length) {
      md += '### ⚠️ BREAKING CHANGES\n\n';
      for (const n of release.breakingNotes) md += `- ${n}\n`;
      md += '\n';
    }
    for (const [cat, entries] of release.sections) {
      md += renderSection(cat, entries);
    }
  }

  return md;
}

// ── Main ─────────────────────────────────────────────────────────────────────

function main() {
  const opts = parseArgs(process.argv);
  const repo = path.resolve(opts.repo);

  // Verify it's a git repo
  if (!git('rev-parse --is-inside-work-tree', repo)) {
    console.error(`Error: "${repo}" is not a git repository.`);
    process.exit(1);
  }

  const tags = getTags(repo).reverse(); // oldest first
  const releases = [];

  if (!opts.noAutoTag && !opts.from && tags.length > 0) {
    // Generate sections per tag range
    for (let i = 0; i < tags.length; i++) {
      const tag = tags[i];
      const prevTag = i > 0 ? tags[i - 1] : null;
      const commits = getCommitsBetweenTags(repo, prevTag, tag);
      if (commits.length === 0) continue;

      const sections = groupCommits(commits);
      const breakingNotes = [];
      for (const [, entries] of sections) {
        for (const e of entries) {
          if (e.breaking) {
            const note = e.body.match(/BREAKING[ -]CHANGE:\s*(.*)/i);
            if (note) breakingNotes.push(note[1]);
            else breakingNotes.push(`${e.description} (${e.hash.slice(0, 7)})`);
          }
        }
      }

      const ver = tag.replace(/^v/, '');
      const date = getTagDate(repo, tag) || commits[0].date;

      releases.push({ version: ver, date, sections, breakingNotes });
    }

    // Also handle commits after last tag
    const latestTag = tags[tags.length - 1];
    const headCommits = getCommitsBetweenTags(repo, latestTag, 'HEAD');
    if (headCommits.length > 0) {
      const sections = groupCommits(headCommits);
      const breakingNotes = [];
      for (const [, entries] of sections) {
        for (const e of entries) {
          if (e.breaking) {
            const note = e.body.match(/BREAKING[ -]CHANGE:\s*(.*)/i);
            if (note) breakingNotes.push(note[1]);
            else breakingNotes.push(`${e.description} (${e.hash.slice(0, 7)})`);
          }
        }
      }
      const nextVer = opts.tag || 'Unreleased';
      const date = headCommits[0].date;
      releases.push({ version: nextVer, date, sections, breakingNotes });
    }

  } else {
    // Single range mode
    const commits = getCommits(repo, opts.from ? undefined : null, opts.to);
    // Re-fetch with proper range
    let rangeCommits;
    if (opts.from) {
      const after = ` --after="${opts.from}"`;
      const before = opts.to ? ` --before="${opts.to} 23:59:59"` : '';
      const format = '%H%n%ai%n%s%n%b%n---COMMIT_SEP---';
      const raw = git(`log --no-merges --format="${format}"${after}${before}`, repo);
      rangeCommits = raw ? raw.split('---COMMIT_SEP---').filter(s => s.trim()).map(block => {
        const lines = block.trim().split('\n');
        return { hash: lines[0] || '', date: (lines[1] || '').split(' ')[0], subject: lines[2] || '', body: lines.slice(3).join('\n').trim() };
      }).filter(c => c.hash && c.subject) : [];
    } else {
      rangeCommits = getCommits(repo, null, opts.to);
    }

    if (rangeCommits.length === 0) {
      console.log('No commits found for the specified range.');
      process.exit(0);
    }

    const sections = groupCommits(rangeCommits);
    const breakingNotes = [];
    for (const [, entries] of sections) {
      for (const e of entries) {
        if (e.breaking) {
          const note = e.body.match(/BREAKING[ -]CHANGE:\s*(.*)/i);
          if (note) breakingNotes.push(note[1]);
          else breakingNotes.push(`${e.description} (${e.hash.slice(0, 7)})`);
        }
      }
    }

    const version = opts.tag || 'Unreleased';
    const date = opts.to || rangeCommits[0].date;
    releases.push({ version, date, sections, breakingNotes });
  }

  if (releases.length === 0) {
    console.log('No commits found.');
    process.exit(0);
  }

  // Reverse so newest release is first
  releases.reverse();

  const md = renderChangelog(releases);
  const outputPath = path.resolve(opts.output);
  fs.writeFileSync(outputPath, md, 'utf-8');
  console.log(`✅ CHANGELOG generated: ${outputPath}`);
  console.log(`   ${releases.length} release(s), ${releases.reduce((n, r) => n + r.sections.reduce((m, [, e]) => m + e.length, 0), 0)} commit(s)`);
}

main();
