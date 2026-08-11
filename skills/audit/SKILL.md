---
name: audit
description: Use when the ask is to go looking for what to improve in a codebase — "audit this repo", "find the bugs / security holes / tech debt / coverage gaps", "what's rotting here", "where should we take this next", "what should I work on" — with no defect named and no run in flight. Read-only on source, always: it produces evidenced findings, ranked, and routes each one to a carrier this pipeline already has (a `docs/backlog.md` seed, a maintenance run via `capture`, a feature run via `idea`). It never fixes anything and never opens a parallel plans/ tree. A finding counts only once reproduced; everything else is reported as a suspicion. Not `review` (that grades one run's implementation against its own plan), not `doctor` (that checks whether the pipeline install is wired up), and not `capture` (that takes down a defect you already know about) — this one goes and finds them.
---

# Audit

Survey a codebase as a senior advisor, produce findings good enough to act
on, and stop. The audit's product is **evidence plus a routing decision**:
what is wrong, how you know, what it costs, and which existing carrier
should hold it.

Nothing here writes source code. The economics are the point — the
expensive part is understanding and judging; execution is cheap and belongs
to the stage skills, the work queue, or a human. An audit that starts
fixing things has spent its budget on the cheap half.

## Process

### 1. Recon — and name the tree you audited

State, in the report's first two lines, the **absolute repo root** and
`git rev-parse --short HEAD`. Never "this repo": a finding is scoped to a
tree at a commit, and the reader's tree is not yours. Deriving the target
from whatever directory you happen to be standing in is how an audit ends
up describing a different repo than the one it names.

Then map the territory:

- `README`, `CLAUDE.md`/`AGENTS.md`, `CONTEXT.md`, contributing notes, root
  config, CI config, directory shape.
- The **exact** build, test, lint, and gate commands. These go into every
  finding's reproduction, so guessing them poisons the whole round.
- Conventions worth matching: error handling, naming, layout, where the
  shared seams are and what the repo says about adding another one.
- `git log --oneline -30` and churn: what is evolving versus frozen.

**Then check what is already in flight, before judging anything:**

    gh pr list --state open
    gh issue list --state open --limit 50

A defect an unmerged PR already fixes is not a finding — it is a duplicate
of work in flight, and a fresh diagnosis of it is worse than useless
because it reads as new. The same goes for an open issue that already
names it, and for a seed already sitting in `docs/backlog.md`. Read all
three before the sweep, not after: recon is cheap and re-litigation is not.

If the repo has no working verification command, that is finding #1 and
everything risky ranks behind it.

### 2. Sweep the categories

Work [`references/playbook.md`](references/playbook.md) — read it now.
Eleven categories: correctness, security, performance, test coverage, tech
debt, dependencies, DX, docs, direction, **inert mechanisms**, and
**unpinned facts**. The last two are here because the worst defects this
pipeline has found were invisible to the other nine and passed every gate.

Scope follows the invocation:

| Invocation | Scope |
|---|---|
| bare | every category, hotspot-weighted by churn and criticality |
| `audit <category>` | recon, then that category only |
| `audit branch` | files changed since the merge-base with the default branch, plus their direct callers — tag each finding `introduced` or `pre-existing` and separate them in the table |

When the harness can spawn read-only subagents and the tree is big enough
to warrant it, fan out one per category cluster. **A subagent inherits none
of this skill**, so its prompt must carry: the absolute path to
`references/playbook.md` and the exact headings to read (always including
`## Finding format`), the recon facts that scope the search, an instruction
to return findings only — no fixes, no file dumps — and a request to
confirm it could read the playbook.

Whatever comes back is a **lead**, not a finding.

### 3. Reproduce before you confirm

A lead becomes a finding when you have produced the failing observation
yourself: the command that fails and its output, the assertion that does
not hold, the accumulated value that is wrong, the call-site enumeration
that comes back empty. Re-reading the cited code is not reproduction — it
re-runs the same judgment that produced the lead, and agrees with itself.

Three ways leads die, all of them common:

- **By design.** The behavior is the platform convention, or the repo
  decided it on purpose and wrote it down. Check the ADRs and the design
  notes before calling something a defect.
- **Mis-attributed.** The finding is real and the `file:line` is wrong.
  Correct it; do not reject it.
- **The harness lied.** The script you wrote to prove the finding was
  itself wrong, and it produced a confident, well-formatted, false result.
  This is the failure mode that survives review, because the output looks
  like evidence. Before trusting a reproduction harness on a case you do
  not know, run it against one you do — if it cannot get the known case
  right, its answer about the unknown one is worth nothing.

A lead you cannot reproduce is reported as a **suspicion**, in its own
list, ranked nowhere and seeded nowhere. Promoting one to round out a thin
report is the same failure as editing an eval definition until it passes.

### 4. Ask what keeps each finding fixed

For every confirmed finding, name the check that fails if the fix
regresses. Three answers, worst to best:

- **Nothing can check it.** Say so — that is part of the finding's cost,
  and it changes the fix's real effort.
- **A check ships with the fix.** The usual answer, and it belongs in the
  finding: a fix whose only guarantee is that someone remembers is a fix
  with a scheduled regression.
- **An existing check already covers it.** Then stop and look again,
  because a green check over a live defect means the check is satisfiable
  without the property it claims to enforce. The finding you have is
  smaller than the one underneath it — write up the hollow check
  (playbook category 11) instead.

### 5. Report

Findings table, ranked by leverage:

| # | Finding | Category | Evidence | Reproduction | Impact | Effort | Keeps it fixed |

Then, separately and never merged into that table:

- **Direction findings** — options for the maintainer to weigh, not
  problems ranked against defects. Two to four, each grounded in this
  repo's own evidence, each with its trade-off in a sentence or two.
- **Suspicions** — the unreproduced leads, each with what would settle it.
- **Considered and not worth doing** — one line of reasoning each, so the
  next audit does not re-derive them.

Close with a **coverage statement**: every category from the playbook
listed as *audited, nothing found* or *not audited*, one or the other,
never omitted. An omitted category reads as clean, which is exactly the
defect category 11 exists to catch — do not commit it in your own report.
Say the same about depth: which directories the sweep actually reached.

### 6. Route each finding to a carrier that already exists

One finding, one carrier. The ladder:

1. **A seed in `docs/backlog.md`** — the default for anything worth
   remembering and not worth a run today. One line, the protocol's
   grammar, origin `session:YYYY-MM-DD`:

       - <finding one-liner> (from: session:2026-08-08)

2. **A maintenance run** — hand it to `capture` when something is broken
   or degraded and is worth a run now. Capture interviews; audit does not
   write `defect.md` on its behalf.
3. **A feature run** — hand it to `idea` when the finding is a direction
   worth building.
4. **Nothing.** A verdict, recorded in the report.

Before appending anything: **read `docs/backlog.md` first and drop
findings it already carries.** The dedupe happens before the write, not
after — an append is not undone by noticing, and a backlog that repeats
itself stops being read.

What audit never writes, in any disposition: a `breakdown.md` row, a
`WO-####` issue, or run artifacts for a run that does not exist. Rows
belong to `decompose` and the tracker mirror is one-way (ADR-0032);
manufacturing either to make a finding look actionable puts the dispatch
plane ahead of the knowledge plane, which is the one thing that ordering
exists to prevent.

State plainly what has no carrier here: **"considered and rejected" has
nowhere durable to live.** The report is its only home, so a later audit
will re-surface those findings. That is a known cost — do not invent a
file to hold them, because a file nothing reads and nothing checks is a
category 11 finding waiting to happen.

## Rules

- Never edit source, never fix "while you're in there", never run a
  command that mutates the working tree — no installs, no builds that
  write outside ignored paths, no formatters, no commits. Read-only
  analysis only (typecheck, lint in check mode, dependency audit, the test
  suite when it is cheap and side-effect free).
- The only file audit may write is `docs/backlog.md`, and only after the
  step-6 dedupe read.
- Never fabricate evidence. A finding with no reproduction is a suspicion;
  a suspicion presented as a finding is the report's own defect, and it is
  the same rule that governs `evals/results/` and the cost ledger.
- Never reproduce a secret value. Location and credential type only, and
  the fix always includes rotation.
- Findings are scoped to the root and commit named in step 1. If the tree
  moved under you mid-audit, say so rather than blending two states.
- If asked to implement a finding, decline and point at the carrier: the
  fix goes through `capture` or `idea` and then the pipeline, where it
  gets a plan, a test, and a human gate. An audit that also implements has
  reviewed its own work.
- A short list of reproduced, high-leverage findings beats a long one.
  Padding is not thoroughness — it is the reader's problem now.
