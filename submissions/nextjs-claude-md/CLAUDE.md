# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Drop this file into the root of any Next.js 15 + SQLite project.
> Claude Code will understand the full context without asking questions.

---

## Stack & Versions

| Layer | Tool | Version | Why |
|-------|------|---------|-----|
| Framework | Next.js (App Router) | 15.x | Server Components, streaming, partial prerendering |
| Runtime | Node.js | 22+ | Required for latest Next.js features |
| Database | better-sqlite3 | 11.x | Synchronous, fast, zero-config, no external service |
| ORM (optional) | Drizzle ORM | latest | Type-safe queries, generates migrations |
| Auth | NextAuth.js v5 | 5.x | App Router native, multi-provider |
| Styling | Tailwind CSS | 4.x | Utility-first, zero runtime |
| Validation | Zod | 3.x | Schema validation shared between client/server |
| Testing | Vitest + Testing Library | latest | Fast, ESM-native |

**No Prisma.** It adds 3s cold-start and a Rust engine for a SQLite file. Not worth it.
**No PlanetScale.** We use a file. If we need scale, we migrate to Turso (libSQL), same SQL.

---

## Folder Structure

```
src/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Route group: auth pages
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/       # Route group: authenticated pages
│   │   ├── layout.tsx     # Shared dashboard layout (sidebar, nav)
│   │   ├── page.tsx       # Dashboard home
│   │   └── settings/
│   ├── api/               # API route handlers
│   │   └── [...route]/    # Catch-all for versioned APIs
│   ├── layout.tsx         # Root layout (html, body, providers)
│   └── globals.css
├── components/
│   ├── ui/                # Base UI primitives (Button, Input, Dialog...)
│   ├── forms/             # Form components with validation
│   └── features/          # Domain-specific composites
├── lib/
│   ├── db/
│   │   ├── schema.ts      # Table definitions (Drizzle) or raw SQL types
│   │   ├── migrations/    # Numbered SQL files: 001_create_users.sql
│   │   ├── index.ts       # DB connection singleton
│   │   └── seed.ts        # Development seed data
│   ├── auth/
│   │   ├── config.ts      # NextAuth configuration
│   │   └── middleware.ts   # Route protection logic
│   ├── validations/       # Zod schemas (one per domain)
│   └── utils.ts           # Pure utility functions only
├── hooks/                 # Custom React hooks
├── types/                 # Shared TypeScript types
└── actions/               # Server Actions (mutate data here, not in API routes)
```

### Rules
- **One component per file.** File name = component name (PascalCase).
- **Server Actions over API routes** for mutations. API routes are for external consumers only.
- **`lib/` is server-only.** Never import from `lib/db` or `lib/auth` in a `'use client'` component.
- **`components/ui/`** must have zero business logic. Props-driven, fully typed.

---

## SQL / Migration Conventions

### Rules
1. **Migrations are immutable.** Never edit a migrated file. Always create a new one.
2. **Numbered, not timestamped:** `001_create_users.sql`, `002_add_email_to_users.sql`
3. **Always include a rollback comment** at the top of every migration:
   ```sql
   -- Rollback: DROP TABLE users;
   CREATE TABLE users (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     email TEXT NOT NULL UNIQUE,
     name TEXT NOT NULL DEFAULT '',
     created_at TEXT NOT NULL DEFAULT (datetime('now')),
     updated_at TEXT NOT NULL DEFAULT (datetime('now'))
   );
   ```
4. **Dates as ISO 8601 TEXT.** SQLite has no datetime type. Always store as `TEXT` in ISO format.
5. **Foreign keys ON by default.** Every connection runs `PRAGMA foreign_keys = ON;`
6. **No `ALTER TABLE` for columns.** SQLite doesn't support dropping columns before 3.35.0. If you must change schema, create a new table and migrate data.
7. **Booleans as INTEGER 0/1.** Name them `is_*` or `has_*`.
8. **Index naming:** `idx_{table}_{column}`. Composite: `idx_{table}_{col1}_{col2}`.

### DB Connection Pattern
```typescript
// lib/db/index.ts
import Database from 'better-sqlite3';
import path from 'path';

const DB_PATH = path.join(process.cwd(), 'data', 'app.db');

// Singleton — Node.js module cache ensures one connection
let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');     // Better concurrent reads
    db.pragma('foreign_keys = ON');      // Enforce referential integrity
    db.pragma('busy_timeout = 5000');    // Wait up to 5s for locks
  }
  return db;
}
```

---

## Component Patterns

### Server Components (default)
Every component is a Server Component unless it explicitly needs interactivity.

```tsx
// app/(dashboard)/page.tsx — Server Component (default)
import { getDb } from '@/lib/db';

export default async function DashboardPage() {
  const db = getDb();
  const stats = db.prepare('SELECT COUNT(*) as count FROM users').get() as { count: number };
  return <div>Users: {stats.count}</div>;
}
```

### Client Components (only when needed)
```tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';

export function Counter() {
  const [count, setCount] = useState(0);
  return <Button onClick={() => setCount(c => c + 1)}>Count: {count}</Button>;
}
```

### Server Actions (mutations)
```tsx
// actions/create-user.ts
'use server';

import { z } from 'zod';
import { getDb } from '@/lib/db';
import { revalidatePath } from 'next/cache';

const schema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
});

export async function createUser(formData: FormData) {
  const parsed = schema.parse({
    email: formData.get('email'),
    name: formData.get('name'),
  });

  const db = getDb();
  db.prepare('INSERT INTO users (email, name) VALUES (?, ?)').run(parsed.email, parsed.name);

  revalidatePath('/dashboard');
}
```

### Form Pattern
```tsx
// components/features/user-form.tsx
'use client';

import { useTransition } from 'react';
import { createUser } from '@/actions/create-user';

export function UserForm() {
  const [pending, startTransition] = useTransition();

  return (
    <form action={(fd) => startTransition(() => createUser(fd))}>
      <input name="email" type="email" required />
      <input name="name" required />
      <button type="submit" disabled={pending}>
        {pending ? 'Creating...' : 'Create User'}
      </button>
    </form>
  );
}
```

---

## What We Don't Do (and Why)

| ❌ Don't | Why |
|----------|-----|
| `getServerSideProps` / `getStaticProps` | Pages Router API. We use App Router. |
| `axios` | `fetch` is built into Next.js (polyfilled on server). No need for a 30KB library. |
| `moment.js` | 300KB. Use `Intl.DateTimeFormat` or `date-fns` (tree-shakeable). |
| `useEffect` for data fetching | Use Server Components or `use()` hook. `useEffect` for syncing to external systems only. |
| `any` type | Fix it. No exceptions. Use `unknown` if you genuinely don't know the shape. |
| `localStorage` for auth tokens | Use httpOnly cookies via NextAuth. localStorage is XSS-vulnerable. |
| ORM-generated migrations for SQLite | Raw SQL is clearer, more debuggable, and doesn't need a build step. |
| `.env` without `.env.example` | Always commit `.env.example` with all required keys documented. Never commit `.env`. |
| `console.log` in production | Use a logger (`pino` or structured console). Remove before merge. |
| Barrel exports (`index.ts` re-exports) | Tree-shaking breaks. Import directly: `import { Button } from '@/components/ui/button'` |

---

## Dev Commands

```bash
# Development
npm run dev              # Start dev server (http://localhost:3000)

# Database
npm run db:migrate       # Run pending migrations
npm run db:seed          # Seed development data
npm run db:reset         # Drop and recreate (dev only!)

# Build & Deploy
npm run build            # Production build
npm run start            # Start production server
npm run lint             # ESLint
npm run type-check       # TypeScript compiler check (no emit)

# Testing
npm run test             # Run Vitest
npm run test:watch       # Watch mode
npm run test:coverage    # Coverage report
```

---

## Anti-Patterns to Avoid

1. **Don't fetch data in layouts.** Layouts don't re-render on navigation. Fetch in pages or use streaming.
2. **Don't use `useEffect` for derivable state.** Compute during render: `const fullName = firstName + ' ' + lastName`.
3. **Don't put business logic in API routes.** Put it in `lib/` and call from Server Actions.
4. **Don't use `NEXT_PUBLIC_` for secrets.** Only for values safe in browser bundles.
5. **Don't create a new DB connection per request.** Use the singleton `getDb()`.
6. **Don't use `SELECT *`.** Always specify columns. Schema changes won't break your code.
7. **Don't use string concatenation for SQL.** Always use parameterized queries (`?` placeholders).
8. **Don't skip input validation.** Every Server Action and API route must validate with Zod.
9. **Don't use `@heroicons` for everything.** Use `lucide-react` — tree-shakeable, smaller bundle.
10. **Don't use `next/link` for external links.** Use `<a>` with `target="_blank"` and `rel="noopener noreferrer"`.

---

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Files (components) | PascalCase | `UserCard.tsx` |
| Files (utilities) | camelCase | `formatDate.ts` |
| Files (pages) | `page.tsx` | `app/(dashboard)/settings/page.tsx` |
| Directories | kebab-case | `user-profile/` |
| Components | PascalCase | `function UserCard()` |
| Hooks | camelCase with `use` prefix | `function useAuth()` |
| Server Actions | camelCase verbs | `createUser`, `deletePost` |
| DB tables | snake_case plural | `users`, `order_items` |
| DB columns | snake_case | `created_at`, `is_active` |
| CSS classes | Tailwind utilities only | No custom classes unless in `globals.css` |
| Environment vars | SCREAMING_SNAKE | `DATABASE_PATH`, `AUTH_SECRET` |
| Types/Interfaces | PascalCase | `type UserRow`, `interface AuthConfig` |
| Zod schemas | camelCase + Schema | `const userSchema = z.object(...)` |

---

## Git Workflow

- **Branch naming:** `feat/short-description`, `fix/short-description`
- **Commit format:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **PR size:** < 400 lines changed. Split larger changes into stacked PRs.
- **Merge strategy:** Squash and merge to `main`. Keep history clean.

---

## Security Checklist

Before every deploy:
- [ ] No secrets in code (use `.env`)
- [ ] All inputs validated with Zod
- [ ] SQL queries parameterized (no string concat)
- [ ] Auth middleware protects `/dashboard/*` routes
- [ ] `PRAGMA foreign_keys = ON` in DB connection
- [ ] Rate limiting on API routes (`@upstash/ratelimit` or custom)
- [ ] CORS configured for API routes if external access needed
- [ ] No `any` types
