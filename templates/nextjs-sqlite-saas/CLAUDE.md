# CLAUDE.md — Next.js 15 + SQLite SaaS Project

> Opinionated project context for Claude Code. Paste into your project root.

## Stack & Versions

| Layer | Tech | Version |
|-------|------|---------|
| Framework | Next.js (App Router) | 15.x |
| Runtime | Node.js | 20 LTS |
| Database | SQLite via better-sqlite3 | 11.x |
| ORM | Drizzle ORM | Latest |
| Auth | NextAuth.js | 5.x (beta) |
| Styling | Tailwind CSS | 4.x |
| Language | TypeScript | 5.x strict |
| Package Manager | pnpm | 9.x |

## Folder Structure

```
src/
  app/                    # Next.js App Router
    (auth)/               # Auth route group (login, register)
    (dashboard)/          # Protected routes
      layout.tsx          # Dashboard shell (sidebar + nav)
      settings/           # User settings pages
      billing/            # Subscription management
    api/                  # API routes
      auth/[...nextauth]/ # NextAuth handler
      webhooks/           # Stripe webhooks
      trpc/               # tRPC router
    layout.tsx            # Root layout (fonts, providers)
    page.tsx              # Landing page (public)
  components/
    ui/                   # Shared primitives (Button, Input, Dialog...)
    forms/                # Form components with validation
    charts/               # Data visualization
  lib/
    db/                   # Database client, schema, migrations
      schema.ts           # Drizzle schema definitions
      client.ts           # DB connection singleton
      migrate.ts          # Migration runner
    auth.ts               # NextAuth config
    stripe.ts             # Stripe client
    validators.ts         # Zod schemas
  server/
    trpc/                 # tRPC routers
      router.ts           # Root router
      user.ts             # User procedures
      billing.ts          # Billing procedures
    middleware.ts         # tRPC context + auth check
drizzle/                  # Migration files
public/                   # Static assets
.env.local                # Environment variables (never commit)
```

## Database Conventions

### Schema Rules
- One schema file: `src/lib/db/schema.ts`
- Every table has: `id` (integer PK auto-increment), `createdAt`, `updatedAt`
- Use Drizzle's `text` for strings, `integer` for numbers and timestamps
- Foreign keys are explicit with `references()`
- Enums stored as `text` with TypeScript union types

### Migration Rules
- Generate with: `pnpm drizzle-kit generate`
- Never edit generated migration files
- Run with: `pnpm drizzle-kit migrate`
- For dev: `pnpm drizzle-kit push` (schema → DB directly)
- Always test migrations up AND down before shipping

### Query Patterns
- All DB queries go through tRPC procedures, never in components directly
- Use `db.select()` with explicit column lists (no `*`)
- Joins: prefer `db.select({}).from().leftJoin()` syntax
- Transactions: wrap multi-step writes in `db.transaction()`

## Component Patterns

### Server vs Client Components
- **Default to Server Components** (no `"use client"`)
- Add `"use client"` ONLY when: useState, useEffect, event handlers, browser APIs
- Data fetching: `async/await` in Server Components, not `useEffect`
- Client state: React Context or Zustand, never prop drilling >2 levels

### Form Pattern
```tsx
// src/components/forms/create-item-form.tsx
"use client"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { createItemSchema } from "@/lib/validators"

type FormData = z.infer<typeof createItemSchema>

export function CreateItemForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(createItemSchema)
  })
  // ...
}
```

### Naming
- Components: PascalCase files matching component name
- Hooks: `use-[name].ts` in `src/hooks/`
- Utils: camelCase in `src/lib/`
- Types: co-located or in `src/types/` for shared types

## What We Don't Do (and Why)

| Don't | Why |
|-------|-----|
| Use Prisma | Drizzle is lighter, SQL-first, better SQLite support |
| Serverless SQLite | SQLite needs persistent disk; deploy on VPS or use Turso |
| CSS-in-JS | Tailwind is faster to write and has zero runtime |
| REST APIs | tRPC gives end-to-end type safety |
| client-side fetching | Server Components with async/await is simpler and faster |
| `getServerSideProps` | App Router uses `async` page components instead |

## Dev Commands

```bash
pnpm dev              # Start dev server (http://localhost:3000)
pnpm build            # Production build
pnpm db:generate      # Generate migration from schema changes
pnpm db:migrate       # Run pending migrations
pnpm db:push          # Push schema to DB (dev only)
pnpm db:studio        # Open Drizzle Studio
pnpm lint             # ESLint
pnpm typecheck        # TypeScript compiler check
```

## Anti-patterns to Avoid

1. **Never import `db` in a client component** — all DB access through API routes or Server Components
2. **Never use `any`** — use `unknown` and narrow, or define proper types
3. **Never store secrets in `src/`** — use `.env.local` and `process.env`
4. **Never fetch in `useEffect`** — use Server Components or tRPC queries
5. **Never inline styles** — use Tailwind classes
6. **Never commit `.env.local`** — it's in `.gitignore` for a reason

## Stripe Integration

- Webhooks at `/api/webhooks/stripe`
- Always verify signature with `STRIPE_WEBHOOK_SECRET`
- Idempotency: use Stripe event ID to prevent double processing
- Test mode: use Stripe CLI `stripe listen --forward-to localhost:3000/api/webhooks/stripe`
