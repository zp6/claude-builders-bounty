#!/usr/bin/env node
/**
 * Weekly Dev Report Generator
 *
 * Fetches weekly GitHub activity and generates a narrative summary using Claude API.
 * Can be used standalone or as part of an n8n workflow.
 *
 * Usage:
 *   GITHUB_TOKEN=xxx GITHUB_REPO=owner/repo ANTHROPIC_API_KEY=xxx node generate.js
 */

const https = require("https");
const http = require("http");
const fs = require("fs");
const path = require("path");

// ── Config ──────────────────────────────────────────────────────────────────

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_REPO = process.env.GITHUB_REPO; // "owner/repo"
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
const REPORT_LANGUAGE = process.env.REPORT_LANGUAGE || "EN";
const WEBHOOK_URL = process.env.WEBHOOK_URL || "";
const OUTPUT_FILE = process.env.OUTPUT_FILE || "weekly-report.md";

if (!GITHUB_TOKEN || !GITHUB_REPO || !ANTHROPIC_API_KEY) {
  console.error("Missing required env vars: GITHUB_TOKEN, GITHUB_REPO, ANTHROPIC_API_KEY");
  process.exit(1);
}

const [owner, repo] = GITHUB_REPO.split("/");
const REPO_NAME = GITHUB_REPO;

// ── Date helpers ────────────────────────────────────────────────────────────

function getDateRange() {
  const now = new Date();
  const dayOfWeek = now.getDay();
  // Go to last Friday (or today if Friday)
  const diff = dayOfWeek >= 5 ? dayOfWeek - 5 : dayOfWeek + 2;
  const friday = new Date(now);
  friday.setDate(now.getDate() - diff);
  friday.setHours(17, 0, 0, 0);

  const prevFriday = new Date(friday);
  prevFriday.setDate(friday.getDate() - 7);

  return {
    since: prevFriday.toISOString(),
    until: friday.toISOString(),
    sinceShort: prevFriday.toISOString().split("T")[0],
    untilShort: friday.toISOString().split("T")[0],
  };
}

// ── HTTP helpers ────────────────────────────────────────────────────────────

function fetchJSON(url, headers = {}) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const mod = parsed.protocol === "https:" ? https : http;
    const options = {
      hostname: parsed.hostname,
      path: parsed.pathname + parsed.search,
      method: "GET",
      headers: { "User-Agent": "weekly-report-generator", ...headers },
    };
    const req = mod.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, data });
        }
      });
    });
    req.on("error", reject);
    req.end();
  });
}

function postJSON(url, body, headers = {}) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const mod = parsed.protocol === "https:" ? https : http;
    const payload = JSON.stringify(body);
    const options = {
      hostname: parsed.hostname,
      path: parsed.pathname + parsed.search,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(payload),
        "User-Agent": "weekly-report-generator",
        ...headers,
      },
    };
    const req = mod.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, data });
        }
      });
    });
    req.on("error", reject);
    req.write(payload);
    req.end();
  });
}

// ── GitHub data fetching ────────────────────────────────────────────────────

async function fetchCommits(since, until) {
  const commits = [];
  let page = 1;
  while (true) {
    const url = `https://api.github.com/repos/${REPO_NAME}/commits?since=${since}&until=${until}&per_page=100&page=${page}`;
    const { status, data } = await fetchJSON(url, {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
    });
    if (status !== 200 || !Array.isArray(data) || data.length === 0) break;
    commits.push(...data);
    if (data.length < 100) break;
    page++;
  }
  return commits;
}

async function fetchClosedIssues(since, until) {
  const issues = [];
  let page = 1;
  while (true) {
    const url = `https://api.github.com/repos/${REPO_NAME}/issues?state=closed&since=${since}&per_page=100&page=${page}`;
    const { status, data } = await fetchJSON(url, {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
    });
    if (status !== 200 || !Array.isArray(data) || data.length === 0) break;
    // Filter: only real issues (not PRs), closed within range
    const filtered = data.filter(
      (i) =>
        !i.pull_request &&
        new Date(i.closed_at) >= new Date(since) &&
        new Date(i.closed_at) <= new Date(until)
    );
    issues.push(...filtered);
    if (data.length < 100) break;
    page++;
  }
  return issues;
}

async function fetchMergedPRs(since, until) {
  const prs = [];
  let page = 1;
  while (true) {
    const url = `https://api.github.com/repos/${REPO_NAME}/pulls?state=closed&per_page=100&page=${page}&sort=updated&direction=desc`;
    const { status, data } = await fetchJSON(url, {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
    });
    if (status !== 200 || !Array.isArray(data) || data.length === 0) break;
    const filtered = data.filter(
      (pr) =>
        pr.merged_at &&
        new Date(pr.merged_at) >= new Date(since) &&
        new Date(pr.merged_at) <= new Date(until)
    );
    prs.push(...filtered);
    if (data.length < 100) break;
    page++;
  }
  return prs;
}

// ── Claude API ──────────────────────────────────────────────────────────────

async function generateNarrative(activityData) {
  const langInstruction =
    REPORT_LANGUAGE === "FR"
      ? "Génère le rapport en français."
      : "Generate the report in English.";

  const prompt = `You are a technical writer generating a weekly development report for a GitHub repository.

${langInstruction}

Based on the following GitHub activity data, generate a clean, well-structured Markdown report.

## GitHub Activity Data:
${JSON.stringify(activityData, null, 2)}

## Instructions:
1. Write an engaging executive summary (2-3 sentences)
2. List key highlights and achievements
3. Group notable commits by functional area
4. Summarize closed issues with their titles and links
5. Summarize merged PRs with their titles and links
6. Add a "Looking Ahead" section based on open issues and patterns
7. Use emoji section headers for visual appeal
8. Keep it concise but informative — developers will read this
9. Do NOT include empty sections — if no issues were closed, skip that section

Format the output as clean Markdown suitable for posting to Slack/Discord or a wiki.`;

  const { status, data } = await postJSON(
    "https://api.anthropic.com/v1/messages",
    {
      model: "claude-sonnet-4-20250514",
      max_tokens: 4000,
      messages: [{ role: "user", content: prompt }],
    },
    {
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    }
  );

  if (status !== 200) {
    throw new Error(`Claude API error ${status}: ${JSON.stringify(data)}`);
  }

  return data.content[0].text;
}

// ── Webhook delivery ────────────────────────────────────────────────────────

async function deliverViaWebhook(report) {
  if (!WEBHOOK_URL) return;

  // Discord webhook format
  if (WEBHOOK_URL.includes("discord.com") || WEBHOOK_URL.includes("discordapp.com")) {
    await postJSON(WEBHOOK_URL, {
      content: report.substring(0, 2000), // Discord limit per message
      username: "Weekly Dev Report",
    });
    return;
  }

  // Slack webhook format
  if (WEBHOOK_URL.includes("slack.com") || WEBHOOK_URL.includes("hooks.slack.com")) {
    await postJSON(WEBHOOK_URL, {
      text: report,
      username: "Weekly Dev Report",
      mrkdwn: true,
    });
    return;
  }

  // Generic webhook
  await postJSON(WEBHOOK_URL, { report });
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  console.log(`📊 Generating weekly report for ${REPO_NAME}...`);

  const dates = getDateRange();
  console.log(`📅 Date range: ${dates.sinceShort} → ${dates.untilShort}`);

  // Fetch all data in parallel
  const [commits, issues, prs] = await Promise.all([
    fetchCommits(dates.since, dates.until),
    fetchClosedIssues(dates.since, dates.until),
    fetchMergedPRs(dates.since, dates.until),
  ]);

  console.log(`📈 Found: ${commits.length} commits, ${issues.length} issues, ${prs.length} PRs`);

  // Build activity summary for Claude
  const contributors = [...new Set(commits.map((c) => c.author?.login).filter(Boolean))];

  const activityData = {
    repo: REPO_NAME,
    period: { from: dates.sinceShort, to: dates.untilShort },
    stats: {
      commits: commits.length,
      issuesClosed: issues.length,
      prsMerged: prs.length,
      contributors: contributors.length,
    },
    commits: commits.slice(0, 50).map((c) => ({
      sha: c.sha?.substring(0, 7),
      message: c.commit?.message?.split("\n")[0],
      author: c.author?.login,
      date: c.commit?.author?.date,
      url: c.html_url,
    })),
    issues: issues.map((i) => ({
      number: i.number,
      title: i.title,
      url: i.html_url,
      labels: i.labels?.map((l) => l.name),
      closedAt: i.closed_at,
    })),
    pullRequests: prs.map((p) => ({
      number: p.number,
      title: p.title,
      url: p.html_url,
      author: p.user?.login,
      mergedAt: p.merged_at,
      additions: p.additions,
      deletions: p.deletions,
    })),
  };

  // Generate narrative with Claude
  console.log("🤖 Generating narrative summary with Claude...");
  const report = await generateNarrative(activityData);

  // Write to file
  const header = `# Weekly Report: ${REPO_NAME}\n**Period:** ${dates.sinceShort} → ${dates.untilShort}\n**Generated:** ${new Date().toISOString().split("T")[0]}\n\n---\n\n`;
  const fullReport = header + report;

  fs.writeFileSync(OUTPUT_FILE, fullReport, "utf-8");
  console.log(`✅ Report saved to ${OUTPUT_FILE}`);

  // Deliver via webhook if configured
  if (WEBHOOK_URL) {
    console.log("📤 Delivering via webhook...");
    await deliverViaWebhook(fullReport);
    console.log("✅ Delivered!");
  }

  console.log("\n" + fullReport);
}

main().catch((err) => {
  console.error("❌ Error:", err.message);
  process.exit(1);
});
