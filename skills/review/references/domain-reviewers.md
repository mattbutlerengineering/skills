# Domain passes

Some bugs only show up if you know the domain. A webhook that skips
signature verification, a migration that drops a column the code still
reads, a lockfile that resolves one library at two versions: each passes
lint, types and tests. These passes add the domain knowledge. Which ones
run depends on the paths the diff changes.

## Selecting the passes

List the changed paths (`git diff --name-only <base>...HEAD`). Run every
pass with at least one matching path. Match on the path, ignoring case.
A pass matches when a path segment or file name contains one of its
words, or when the path matches one of its patterns.

| Pass | Selected when a changed path matches | Read |
|---|---|---|
| Payments | `payment`, `stripe`, `checkout`, `billing`, `invoice`, `charge`, `refund`, `deposit`, `payout`, `subscription`, `webhook`; or any changed file that imports a payment provider's SDK | [payments.md](payments.md) |
| Migrations | a `migrations/`, `migrate/` or `alembic/versions/` directory; `*.sql`; an ORM schema file (`schema.prisma`, a Drizzle or SQLAlchemy model module, `db/schema.rb`, `structure.sql`); a Liquibase changelog | [migrations.md](migrations.md) |
| Dependencies | a package manifest or lockfile: `package.json` and its lockfiles, `requirements*.txt`, `pyproject.toml`, `poetry.lock`, `uv.lock`, `Pipfile*`, `go.mod`/`go.sum`, `Cargo.*`, `Gemfile*`, `pom.xml`, `build.gradle*`, `libs.versions.toml`, `composer.*`, `*.csproj`, `packages.lock.json`; or a dependency-override block in one of them | [dependencies.md](dependencies.md) |

The word matching is broad on purpose. A false selection costs one
quick read that comes back clean. A missed selection costs a payment
bug in production. When a word matches a file that has nothing to do
with the domain (a `chargeback-faq.md` page), say so in one line and
move on.

No match means no domain pass. Say so in "Passes with no findings":
"domain passes: none selected".

## The shared contract

Every domain pass follows these rules on top of the skill's own:

- **Read the whole changed file**, not just the hunk. Most domain bugs
  come from context the hunk leaves out: the middleware order before a
  webhook handler, or the code that still reads a dropped column.
- **Findings use the skill's format.** Give each one a severity, a
  `path:line`, the concrete failure scenario and the fix. The pass name
  goes in the heading: `### Major: payments — refund amount has no upper
  bound`.
- **Read only.** A pass reads and reports. It never edits, stages or
  commits. A command that can rewrite files, such as an install or a
  build that touches a lockfile, runs only in a throwaway checkout or
  with the package manager's frozen-lockfile flag. The working tree must
  end exactly as the pass found it (`git status --porcelain` unchanged).
- **Evidence or silence.** In these domains a false positive costs more
  than a missed nit. Flag a pattern only when the code shows it. A
  suspicion goes down as a suspicion, with what would settle it. "Clean"
  is a valid and common result for a selected pass.
- **Stay in your lane.** A domain pass does not grade style, coverage or
  ADR compliance. The other passes own those. When a domain finding is
  also a security finding (a hardcoded webhook secret, say), report it
  once, under whichever pass gives the sharper scenario.

## Who runs these

Any review under this skill runs the passes the diff selects. That
includes a stage-by-stage run, an autorun's review stage, and a
distinct-worker review that a batch conductor launches under this skill.
