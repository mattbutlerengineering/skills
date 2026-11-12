# Migrations pass

A pattern-matching script can find `DROP COLUMN`. It cannot find a drop
that the rest of the diff still depends on. This pass checks the
migration against the code that ships with it. It applies to raw SQL
migrations and to ORM-generated ones (Prisma, Drizzle, Alembic, Django,
Rails, Flyway, Liquibase). Follow the shared contract in
[domain-reviewers.md](domain-reviewers.md).

## What to check

### 1. Destructive operations without recorded intent

Flag these unless the change records the intent:

- `DROP TABLE`, `DROP COLUMN`, `TRUNCATE`
- `DELETE FROM` with no `WHERE`, or with a `WHERE` that matches more
  than the change describes
- dropping a constraint that enforces foreign-key integrity

Recorded intent means a comment in the migration, the run's
`architecture.md` or breakdown, or an ADR that says the data loss is
meant. If the repo has its own marker convention, use that instead. An
unmarked destructive operation is critical. It deletes production data
on deploy.

### 2. NOT NULL added to a table with existing rows

`ADD COLUMN ... NOT NULL` with no `DEFAULT` fails on a table that
already has rows. That can break a deploy that passed every test on an
empty test database. The safe shape is three migrations: add the column
as nullable, backfill it, then set NOT NULL. Or add it with a default.

### 3. A rename done as drop plus add

A migration that drops column `a` and adds column `b` of the same type
destroys `a`'s data, even if the intent was a rename. ORM diff tools
generate this when a field is renamed in the schema. Flag it and point
to `RENAME COLUMN` (or the ORM's explicit rename).

### 4. The migration and the code disagree

This is the check the pass exists for. A regex cannot do it.

- For each column or table the migration drops or renames, search the
  application source for both the ORM field name and the database
  column name. Code that still reads or writes it breaks at runtime the
  moment the migration runs.
- For each column the migration adds, find the insert and update paths
  that should write it. Code that writes a field name the migration
  never creates is the mirror image of the same bug.
- Read the schema file (ORM model, `schema.prisma`, `schema.rb`) beside
  the migration. A schema change with no migration, or a migration with
  no schema change, means the two are out of sync.
- Check the deploy order. If the old code version still runs while the
  migration applies (rolling deploys), a dropped column breaks the old
  version too. The safe sequence is to stop reading the column in one
  release and drop it in the next.

### 5. Index and lock churn

Creating or dropping an index on a large or busy table without the
non-blocking form (`CREATE INDEX CONCURRENTLY` on Postgres, or the
online-DDL option elsewhere) locks writes for the whole build. Flag it
when the table is plausibly large or hot. Also flag a column type change
that rewrites the table.

### 6. Cascade surprises

A new foreign key with `ON DELETE CASCADE` quietly turns one delete
into many. Confirm that the cascade is intended, and compare it with how
the schema's other relationships behave. An unexplained cascade on a
parent of user data is major.

## How to run it

1. List the changed migration and schema files this pass selected.
2. Read each migration in full, and the schema file it belongs to.
3. Search the application source for every dropped, renamed or added
   name (field and column).
4. Write the findings in the review's format, grouped by migration. A
   clean migration gets one line saying so.

## What this pass does not do

- Grade the schema file's formatting. The formatter owns that.
- Suggest performance work unrelated to the migration's own operations.
- Rewrite the migration. It flags the problem and names the safer shape.
