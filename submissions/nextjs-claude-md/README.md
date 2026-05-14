# Next.js 15 + SQLite CLAUDE.md Template

A production-ready, opinionated `CLAUDE.md` for SaaS projects built with Next.js 15 App Router and SQLite.

## Setup (3 steps)

1. **Create a new Next.js project:**
   ```bash
   npx create-next-app@latest my-saas --typescript --tailwind --app --src-dir
   cd my-saas
   npm install better-sqlite3 zod next-auth@beta
   ```

2. **Copy CLAUDE.md to project root:**
   ```bash
   cp CLAUDE.md my-saas/CLAUDE.md
   ```

3. **Open in Claude Code and start building:**
   ```bash
   cd my-saas
   claude
   ```
   Claude will read `CLAUDE.md` and understand the full project context.

## What's Included

- ✅ Stack & versions with rationale for every choice
- ✅ Complete folder structure with rules
- ✅ SQL migration conventions (immutable, numbered, rollback-ready)
- ✅ Component patterns (Server Components, Client Components, Server Actions)
- ✅ Anti-patterns with explanations
- ✅ Naming conventions table
- ✅ Dev commands reference
- ✅ Git workflow rules
- ✅ Security checklist
- ✅ "What we don't do" table with reasons

## Design Decisions

| Decision | Why |
|----------|-----|
| better-sqlite3 over Turso | Zero config for dev, synchronous API (no async complexity), fast |
| Drizzle over Prisma | No Rust engine, no 3s cold start, generates plain SQL |
| Server Actions over API routes | Type-safe, no serialization, progressive enhancement |
| Zod for validation | Shared between client and server, TypeScript inference |
| WAL mode | Better concurrent read performance |
| No barrel exports | Preserves tree-shaking |

## Tested With

This template was tested by:
1. Creating a fresh Next.js 15 project
2. Pasting this CLAUDE.md into the root
3. Asking Claude Code to "create a user registration system"
4. Claude understood the full context: used Server Actions, better-sqlite3, Zod, proper folder structure — no clarifying questions needed

## Compatibility

- Next.js 15.x (App Router)
- Node.js 22+
- SQLite 3.35+ (for ALTER TABLE DROP COLUMN support)
- TypeScript 5.x
