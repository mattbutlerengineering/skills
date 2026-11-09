# A knowledge-base page declares its outside check, and lint ages it offline

- Status: provisional
- Date: 2026-11-08

Recorded by the `kb-from-knowledge-work-plugins` feature run
(`docs/features/kb-from-knowledge-work-plugins/architecture.md`, issue
#1274), unattended, so it is provisional. Amends
[ADR-0078](0078-a-project-knowledge-base-indexed-inline.md): its
decision 2 (page frontmatter is exactly `summary`, `sources`, `verified`
and `related`) and decision 6 (what lint calls stale). The rest of
ADR-0078 stands.

## Context

ADR-0078 made freshness mechanical by tying each page to repo files: a
page is stale once a cited source changes in git after its `verified`
commit. A claim about a system outside the repo (a GitHub setting, a
vendor's behaviour) cites no file that will ever change, so lint passes
over it forever. This repo's `docs/kb/main-unprotected.md` shows it: it
carries a hand-written note telling the reader to re-run two `gh api`
commands, because nothing else will. The page rubric admits
external-system facts in every repo that installs the skill, and lint
can check none of them.

Three shapes were on the table:

- **Run the page's check from lint** (a declared command such as
  `gh api ...`). It is the only shape that knows whether the claim still
  holds. It also puts network access and credentials inside a tool that
  is offline today, and the Owner ruled it out of this run (the Moonshot
  rung, seeded to the backlog).
- **A default age for every page.** Nothing to declare, but the number
  would be a policy with no evidence behind it, and it would start
  failing pages whose claims rest wholly on repo files that git already
  watches.
- **A declared age, read offline.** The page says what it was checked
  against, on what date, and how long that check holds; lint compares
  the date with today and runs nothing.

A second question was whether "what a claim was verified against, and
what it was not" (an environment, a tool version) is a separate field
from "the outside system this page was checked against". They answer
the same question about different claims, so two fields would be two
owners of one idea.

## Decision

1. **Three optional page fields.** `checked-against:` is free text: what
   the page's claims were checked against, and what they were not (for
   example "the GitHub API; not GitHub's merge-queue docs", or "macOS
   zsh with gh 2.62; not Linux CI"). `checked:` is the date of that
   check, `YYYY-MM-DD`. `max-age:` is how long the check holds, as a
   whole number of days written `<N>d`. ADR-0078's four fields stay
   required and unchanged; a page with none of the three lints exactly
   as before.
2. **`checked` and `max-age` come as a pair, and need `checked-against`.**
   Declaring either without the other two is a lint problem naming the
   missing field. `checked-against` alone is allowed: it records where a
   claim was verified and never ages.
3. **Lint ages the pair offline.** `kb.py lint` reports a page once
   today is after `checked` plus `max-age`, as one problem string naming
   the page, its date, its age and its due date. It reports a `checked`
   that is not a date or is after today, a `max-age` that is not `<N>d`
   with N at least 1, and an empty `checked-against`, each naming the
   page and the field. It never runs a command or opens a connection for
   this check, and it never treats a malformed declaration as fresh.
4. **No default age.** A page that should age declares it; the rubric
   tells the writer of an external-system fact to declare all three
   fields.
5. **The index line is unchanged.** `summary` stays the one owner of a
   page's index line; the age is never rendered into the always-loaded
   block, whose 2,048-byte budget is paid on every turn.

## Consequences

- Lint becomes time-dependent: a page can go from clean to failing with
  no commit. That is safe today because `kb.py lint` is not in `make
  check`. If a later change puts it there (the 2026-10-16 backlog seed
  proposes it), an aged page would turn the gate red on a date alone,
  and that change has to weigh this.
- Lint knows only that a check is due, not whether the claim still
  holds. Re-checking stays a person's or an agent's job, guided by the
  skill's step 3; the scheduled re-check that would close the loop stays
  in the backlog.
- Page frontmatter is a contract shipped to every repo that installs the
  skill. Once pages carry these fields, removing or renaming them means
  migrating pages in repos this one does not own.
- One field serving both "outside system" and "environment" means lint
  cannot tell an external-system page that forgot its age from a page
  that only records its environment. The rubric carries that rule, not
  lint.
