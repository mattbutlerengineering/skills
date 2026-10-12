---
name: prisma-migrations
description: Use when a repo's Prisma schema change has to reach a database safely — "create a migration", "run prisma migrate", "deploy the database changes", "baseline the existing production database", "set up Prisma migrations in CI/CD", "a migration failed halfway in prod", "prisma says drift detected", "P3009". A reference skill for Prisma Migrate — migrate dev versus migrate deploy versus db push, migration naming, deploy ordering, baselining a database created without migrations, CI/CD wiring, and recovering from failed or drifted migrations — with copyable workflow and script assets. It never runs migrate dev, migrate reset or db push against a shared or production database. Designing the data model is architect; reviewing a migration diff for defects is review; releasing a run is ship. Owns no run artifact and is never routed to.
---

# Prisma Migrations

Get a Prisma schema change from `schema.prisma` to every database it
must reach — development, CI, staging, production — without losing
data and without the migration history drifting from the databases it
describes.

This is not a stage in the lifecycle pipeline and it owns no run
artifact. It is reference knowledge for any repo that uses Prisma
Migrate, whether or not the repo has ever heard of the pipeline. Its
assets are templates a consumer repo copies and adapts; nothing here
runs from the plugin's own checkout.

Paths below assume Prisma's defaults (`prisma/schema.prisma`,
`prisma/migrations/`) and `npx` as the runner. Read the repo's actual
schema location, package manager and deploy platform before giving a
command — adapt the paths, never assume them.

## Must never

- Run `prisma migrate dev`, `prisma migrate reset` or `prisma db push`
  against a shared, staging or production database. They can drop
  tables. Production applies migrations with `prisma migrate deploy`
  only.
- Edit a `migration.sql` that has already been applied anywhere. Write
  a new migration instead.
- Mark a migration applied or rolled back (`migrate resolve`) without
  first confirming, against the database itself, what state it is in.
- Put a database URL in a committed file. It belongs in the platform's
  secret store.

## Key concepts

- **Migration files** — SQL in `prisma/migrations/<timestamp>_<name>/`,
  one directory per schema change, committed to version control.
- **Migration history** — the `_prisma_migrations` table, recording
  which migrations each database has applied.
- **Shadow database** — a temporary database `migrate dev` uses to
  detect drift; development only.

## Which command

| Scenario | Command | Why |
|---|---|---|
| Changing the schema in development | `prisma migrate dev` | Creates a versioned migration file and applies it |
| Deploying to staging or production | `prisma migrate deploy` | Applies only pending, committed migrations |
| Throwaway prototyping, no history wanted | `prisma db push` | Syncs the schema without migration files |
| Checking what is pending | `prisma migrate status` | Lists applied and pending migrations |

```
Need to change the database schema?
│
├─ Production or staging? → prisma migrate deploy
│                            (applies existing migrations only)
├─ Development?           → prisma migrate dev
│                            (creates and applies a migration)
└─ Just prototyping?      → prisma db push (no migration history)
```

## Development workflow

After editing `schema.prisma`:

```bash
npx prisma migrate dev --name descriptive_name
```

This creates the migration file, applies it to the development
database, and regenerates Prisma Client.

Name migrations in snake_case, descriptively, with the action first:
`add_email_verified_column`, not `update_users`. Prefixes that read
well: `create_`, `add_`, `remove_`, `rename_`.

To review the SQL before it runs:

```bash
npx prisma migrate dev --create-only   # writes migration.sql, applies nothing
# read prisma/migrations/<timestamp>_<name>/migration.sql, edit if needed
npx prisma migrate dev                 # applies it
```

`--create-only` is also the moment to hand-edit the SQL — a backfill
before a `NOT NULL`, a concurrent index — before anything has applied
it.

`npx prisma migrate reset` drops the development database and reapplies
every migration. It destroys all data; development only.

## Production workflow

```bash
npx prisma migrate deploy
```

`migrate deploy` applies only pending migrations that exist in the
migrations directory, never creates one, needs no shadow database, and
stops on the first failure.

Before deploying a schema change:

1. **Migrations are committed** — every migration directory is in
   version control.
2. **Tested against production-shaped data** — run `migrate deploy`
   against a restored copy of production, not only an empty database.
3. **A backup exists** — Prisma has no automatic rollback.
4. **Migrations ship before the code that needs them** — deploy the
   migration, then the application code, then remove old columns and
   code in a later change (expand, then contract).

## Common mistakes

| Mistake | Instead |
|---|---|
| `DATABASE_URL=<prod> npx prisma migrate dev` | `DATABASE_URL=<prod> npx prisma migrate deploy` |
| `prisma db push` as the production deploy | `migrate dev --name …` locally, commit, `migrate deploy` in the pipeline |
| Testing migrations only on an empty database | Restore a production backup locally and run `migrate deploy` against it |
| Deploying code that reads a column before the migration that adds it | Migrations first, code second, cleanup last |

## Command reference

| Command | Environment | Purpose |
|---|---|---|
| `prisma migrate dev` | Development | Create and apply migrations |
| `prisma migrate dev --name <name>` | Development | Create a named migration |
| `prisma migrate dev --create-only` | Development | Generate SQL without applying it |
| `prisma migrate deploy` | Production / CI | Apply pending migrations |
| `prisma migrate status` | Any | Show applied and pending migrations |
| `prisma migrate reset` | Development | Drop the database and reapply every migration |
| `prisma migrate resolve --applied <name>` | Production | Record a migration as applied without running it |
| `prisma migrate resolve --rolled-back <name>` | Production | Record a failed migration as rolled back |
| `prisma migrate diff` | Any | Compare schema, migrations and a live database |
| `prisma db push` | Development | Sync the schema without migrations |

## CI/CD

Migrations run once, before the application deploys, from a single
job, with the database URL from the platform's secrets:

```yaml
jobs:
  migrate:
    steps:
      - name: Apply database migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

Platform patterns (GitHub Actions, Vercel, Railway, Docker, Kubernetes),
connection-pooler handling, rollback planning and failure alerts are in
[CI/CD patterns](references/ci-cd-patterns.md).

## Baselining an existing database

A database created with `db push`, raw SQL or another migration tool
has no migration history, so `migrate deploy` would try to create
tables that already exist. Baseline it first:

1. Make `schema.prisma` match the database (`prisma db pull`).
2. Generate an initial migration with `--create-only`.
3. Record it as already applied on every existing database with
   `migrate resolve --applied`.
4. Every later migration works normally.

The full procedure, multi-environment cases and baselining failures are
in the [baselining guide](references/baselining-guide.md).

## Troubleshooting

Failed migrations (`P3009`), drift, checksum mismatches, shadow-database
permissions, pooler timeouts, required columns on populated tables,
long-running and locking migrations, and partial-application recovery
are in the [troubleshooting guide](references/troubleshooting.md).

## Assets

Templates to copy into the consumer repo and adapt — runner, package
manager, Node version, database image and deploy step are placeholders:

- [assets/github-action.yml](assets/github-action.yml) — a GitHub
  Actions workflow that tests migrations on a fresh Postgres service,
  applies them to production on `main`, then deploys.
- [assets/migration-script.sh](assets/migration-script.sh) — a guarded
  production deploy (`--dry-run`, `--backup`) that verifies status
  afterwards.
- [assets/check-pending.sh](assets/check-pending.sh) — exits 0 when the
  database is up to date, 1 when migrations are pending, 2 on error,
  for gating a CI step.
