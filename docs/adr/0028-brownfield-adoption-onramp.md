# Brownfield adoption on-ramp

- Status: provisional
- Date: 2026-07-05

## Context

A repo with an existing codebase and no pipeline artifacts has no honest
entry. The router's default is greenfield: "If no run exists at all, the
next stage is Idea (ask product or feature first)"
(`skills/next/SKILL.md`). And the Architect stage's codebase-exploration
branch fires only for feature runs — for product runs it "establish[es]
the ground rules instead", a blank-slate assumption
(`skills/architect/SKILL.md`, step 3). So the largest population of real
adopters — teams with working software and zero artifacts — must either
fake an Idea/product run for software that already exists, or run
features against an undocumented baseline that downstream stages assume
is present.

The three existing on-ramps don't cover this. A product run (ADR-0003)
assumes greenfield. A feature run assumes a documented ground to build
on. A maintenance run (ADR-0025) assumes a defect or degraded condition —
"the pipeline has never seen this codebase" is neither.

## Decision (recommended, provisional)

Add a fourth on-ramp alongside the product, feature, and maintenance
entries: an **adopt/onboard entry** for existing codebases with no
artifacts. It reads the codebase and interviews the maintainer to
reverse-engineer a baseline — the project's `CONTEXT.md` vocabulary and
an architecture baseline (`docs/baseline.md`) — then hands off to feature
or maintenance runs. It is an entry, not a fourth run scale: ADR-0003's
and ADR-0025's three run scales stand unchanged; adoption produces the
documented ground those runs re-enter onto.

ADR-0004 holds throughout. The baseline is an artifact oriented from like
any other — the router recognizes an adopted repo purely by which files
exist. It records knowledge (vocabulary, architecture), never pipeline
position; no manifest or state file is introduced.

## Skill sketch

A capture-style entry skill (interview-first, no predecessor artifact,
never a soft gate — like `capture`, the protocol read still comes first).

**Entry trigger / description draft:**

```yaml
name: adopt
description: Use when the pipeline is being introduced to an existing
  codebase that has no run artifacts — the user wants to adopt the
  pipeline, onboard an existing project, or needs a documented baseline
  before feature or maintenance work. Reads the codebase and interviews
  the maintainer to produce the architecture baseline (baseline.md) and
  the project's CONTEXT.md vocabulary, then hands off to a feature or
  maintenance run.
```

**Interview coverage** (one question at a time, each with a recommended
answer drafted from the codebase read, capture-style):

- What the product does and who it serves — the maintainer's own words,
  one paragraph.
- Domain vocabulary: confirm or correct candidate terms mined from code
  and docs; capture avoid-terms. Output feeds the project's `CONTEXT.md`.
- Ground rules: language, framework, storage, deployment target — the
  same questions Architect asks greenfield product runs, answered once
  here so feature runs never re-ask them.
- Major components and their responsibilities; which are load-bearing
  and which are peripheral.
- Known constraints, tech debt, and no-go zones — the deliberate
  weirdness the code can't explain about itself.
- Verification reality: how the team verifies today (test suites, CI,
  manual passes) — what Verify will lean on in later runs.
- Near-term intent: the first feature or fix, so the hand-off lands
  somewhere concrete.

**Seed artifact:** `docs/baseline.md` (architecture baseline) plus the
target repo's `CONTEXT.md` (vocabulary). Baseline frontmatter follows the
protocol convention:

```yaml
---
stage: adopt
run: adoption
date: 2026-07-05
coverage: <one line — what the codebase read did and did not cover>
# assumptions: [...]   any decision made without live maintainer input
---
```

(`adoption` is a new value in the frontmatter `run:` grammar — a protocol
edit deferred until this ADR is accepted.)

**Orientation-table row addition** (protocol edit, deferred):

| Stage | Artifact | Complete when |
|-------|----------|---------------|
| Adopt | `baseline.md` at docs root, plus project `CONTEXT.md` | files exist |

Run discovery is clarified alongside: `baseline.md` at the docs root is
not a product-run artifact — its presence alone never makes `docs/` an
active run.

**Router recognition afterward.** The router's "no run exists" branch
becomes two-way, still orienting purely from artifacts:

- No run and no `docs/baseline.md` → greenfield default, unchanged:
  next stage is Idea (ask product or feature first).
- No run but `docs/baseline.md` exists → adopted-but-runless repo:
  announce it ("Adopted repo, baseline in place, no active run") and
  offer a feature run or a maintenance run — never Idea-as-product,
  because the product already exists.

Architect gains a matching read (deferred edit): in an adopted repo, the
feature-run exploration branch starts from `baseline.md`, and the
greenfield "establish the ground rules" branch is skipped because the
ground rules are already recorded.

## Alternatives considered

- **Fake an Idea/product run.** Write `idea.md` and `prd.md` for
  software that already shipped. Rejected: it fabricates history the
  interview-early principle exists to capture honestly, the product-run
  orientation table then demands Verify/Ship/Operate artifacts for
  nothing that shipped, and the retro loop inherits a run that never
  happened.
- **Document nothing; rely on Architect's feature-run exploration.**
  Rejected: that exploration is per-run and unrecorded — every feature
  run re-derives the same baseline, vocabulary never converges (no
  `CONTEXT.md` ever exists), and maintenance runs with
  `re-entry: implement` get no exploration at all, so exactly the runs
  brownfield repos start with see the least of the codebase.
- **A one-shot script instead of a skill.** Rejected: the baseline's
  value is what code can't tell you — intent, avoid-terms, known debt,
  deliberate weirdness — which only a maintainer interview surfaces; a
  script can only inventory files. It would also sit outside every
  routing, lint, and eval mechanism this repo has: no trigger
  description, no orientation, no interview.

## Open questions (each with a recommended answer)

- **Is the baseline a run artifact or a repo-level doc?** Recommended:
  repo-level (`docs/baseline.md` + project `CONTEXT.md`). The baseline
  outlives any single run — it is the ground every later run re-enters
  onto, the adoption analog of what a completed product run leaves at
  the docs root. Burying it in a run directory would entomb permanent
  ground truth inside one completed run.
- **How much codebase reading is in scope?** Recommended: breadth-first
  and bounded — the repo's own signposts (README, docs, manifests,
  top-level layout, entry points) plus a representative sample per major
  component; no exhaustive file-by-file pass. The interview corrects
  what reading gets wrong, and the `coverage:` frontmatter line records
  what was not read so downstream stages don't over-trust the baseline.
  Depth scales with codebase size — when in doubt, ask the maintainer
  how big this really is, mirroring the run-scale rule.
- **Does adoption complete as a "run" with a retro?** Recommended: no.
  Adoption is an entry, not a run — it ships nothing and verifies
  nothing, so a `retro.md` would close a loop that never opened, and run
  discovery would gain a fake run. Completion is the baseline artifacts
  existing; the first real feature or maintenance run's retro is where
  adoption lessons land.

## Consequences

- A new entry skill (`adopt`) joins `capture` as the second
  interview-style entry with no predecessor and no soft gate.
- Deferred protocol edits, pending acceptance: the Adopt orientation
  row, the run-discovery clarification that `baseline.md` never
  activates a run by itself, and `adoption` in the frontmatter `run:`
  grammar.
- The router's no-run branch becomes two-way (greenfield → Idea;
  adopted → feature or maintenance), still deciding purely from which
  artifacts exist (ADR-0004).
- Architect reads `baseline.md` when present instead of re-establishing
  ground rules or exploring cold.
- Trigger evals must discriminate `adopt` from `idea` (new thing vs
  existing thing) and from `capture` (nothing is broken — the pipeline
  is just new here).
- ADR-0003 and ADR-0025 are unchanged: three run scales; adoption is an
  on-ramp that feeds them.
