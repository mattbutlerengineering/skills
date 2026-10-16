# Process review: what the research notes recommended, and what landed

Review note, 2026-10-16, for issue #956 ("Review our research and make
changes to improve our ai sdlc"), filed the day the xerj note merged.
Method: every adopt/adapt verdict in `docs/research/`, plus the
`RATIFIED` and `(from: session:2026-10-16)` lines of `docs/backlog.md`,
checked against the tree at `a364649` (the Makefile, `gates.py`,
`lint.py`, `kb.py`, `trigger_eval.py`, the workflows, `docs/adr/`, the
skill bodies). Then the items that were S-sized, not started, and safe
without an Owner decision shipped as four independent PRs; the rest are
seeds. Everything here was read at the tip; nothing was re-run that
costs money.

## Sources

`docs/research/`: `xerj.md` (read first), `autonomous-agent-harnesses.md`,
`eval-and-memory.md`, `review-ci-automation.md`, `spec-driven-sdlc.md`,
`rea-learnings.md`, `jev-codemods-and-plugin-eval.md`,
`knowledge-base.md`, `knowledge-base-evidence.md`,
`knowledge-base-ablation.md`, `knowledge-system-over-time.md`,
`orchestrator.md`, `orchestrator-roles.md`,
`ux-writing-and-ux-patterns.md`, `workflow-summary-descriptions.md`,
`autonomy-baseline.md`. `beads-memories-archive.md` is a frozen export
(ADR-0083), not a note with verdicts, and was not reviewed.
`docs/backlog.md` lines 70–74 (the 2026-09-21 ratification pass for
issue #436) and 107–114 (the 2026-10-16 automate and xerj seeds).

## Inventory

Size: S is under about 100 lines including tests, M a few files or a
real design, L a new subsystem. Status is what the tree at `a364649`
shows, not what a note claimed.

| Item | Source | Verdict | Status | Size | Risk | Carrier |
|---|---|---|---|---|---|---|
| PR template with detector B's lines and Verified / Assumed / Not run | xerj 8; backlog 2026-10-16 | Adopt | **done this pass** (#960) | S | low | `.github/PULL_REQUEST_TEMPLATE.md`; gate path, human merge |
| Install block ends with a verify line and doctor's real summary | xerj 3a; backlog 2026-10-16 | Adopt | **done this pass** (#966) | S | low | `README.md` |
| `kb.py lint` as a root-only `make check` line | xerj 4; backlog 2026-10-16 | Adapt | **blocked** — needs a decision (below); its prerequisite, four stale pages re-verified, landed as #962 | S code, ADR-level rule | medium | Makefile + `validator.yml` fetch depth + a pin convention |
| `kb.py drift` as a root-only `make check` line | backlog 2026-10-16 (automate pass) | seed | **done this pass** (#964) | S | low | Makefile, `factory_init.product_makefile` |
| Field-report intake issue template for adopters | xerj 1 | Adapt, deferred | not started; the note itself waits for an adoption signal | S | low | `.github/ISSUE_TEMPLATE/`; seeded 2026-10-16 |
| Zero-experience onboarding harness (one headless run from the README) | xerj 9 | Adapt, deferred | not started; waits on 3a, which is now in #966 | M | low | a `claude -p` session written up here |
| `md_claims.py check` on living docs as a gate | xerj 10 | Adapt | not started; 18 living-doc findings to triage first | M | medium | consumer-path rule or ignore marker, then a Makefile line; seeded 2026-10-16 |
| PreToolUse hook on `gh pr create` running B's regexes | backlog 2026-10-16 (automate pass) | seed | not started; the fail-closed template (#960) covers the interactive half | S–M | medium (a hook needs a replay test) | `.claude/settings.json` + script |
| PostToolUse hook running `update-manifest` on template edits | backlog 2026-10-16 (automate pass) | seed | not started; convenience, evidence of forgetting is thin | S | low | `.claude/settings.json` |
| Per-skill precision/recall/F1 from the recorded confusion matrix | eval-and-memory 5; backlog RATIFIED | Adopt | **done** — `trigger_eval.skill_metrics`, `--metrics <results> [--kind]` | S | — | `trigger_eval.py` |
| ADD/UPDATE/DELETE/NOOP consolidation for durable knowledge | eval-and-memory 1 | Adapt, own ADR | partial — `docs/kb/` ingest uses it (ADR-0078); the improvement journal is still append-only | M | medium | held by the 2026-09-21 not-ratified seed |
| Scheduled memory-maintenance pass | eval-and-memory 2 | Adapt | partial — the hourly routine's rung 3 re-verifies kb pages; no journal consolidation | M | low | `docs/factory/*-routine.md`; same seed |
| Native merge queue | review-ci 1; backlog RATIFIED | Adopt | decided (ADR-0070); switched off — `docs/kb/main-unprotected.md` | operator action | medium | branch protection + `merge_group` triggers |
| Escaped-defect vs change-failure definition | review-ci 4 | Adapt, deferred | not started; fold into the ADR that first graduates a class | S docs | low | ADR-0033's successor; same seed |
| Reviewer precision/recall against a labelled defect corpus | review-ci 5 | Adapt, deferred | not started | L | low | `charter_replay.py`-shaped harness; own ADR; under the 2026-09-21 seed's "remaining mechanisms", not named in it |
| Inline `[NEEDS CLARIFICATION]` markers + bounded clarify | spec-driven 1; backlog RATIFIED | Adopt | **done** — ADR-0071, detector N, the PRD skill's clarify pass | — | — | — |
| Bidirectional PRD ↔ work-item coverage | spec-driven 2; backlog RATIFIED | Adopt | **done** — ADR-0072, detector O, the coverage waiver | — | — | — |
| ADR-compliance section + deviation table in the architecture template | spec-driven 3 | Adapt, own ADR | not started | S–M | medium | `skills/architect/TEMPLATE.md` + a detector; same seed |
| Pre-dispatch readiness verdict PASS / CONCERNS / FAIL | spec-driven 4 | Adapt, own ADR | not started | S | medium | decompose or work-queue skill; same seed |
| Living current-truth spec with delta merge at run close | spec-driven 5 | Adapt, when pain is shown | not started | L | high | `docs/spec/` tree; same seed |
| Requirement / Scenario grammar for success criteria | spec-driven 6 | Adapt, template-only | not started | S | medium (reshapes every future PRD) | `skills/prd/TEMPLATE.md` under ADR-0015; under the 2026-09-21 seed's "remaining mechanisms", not named in it |
| Requirements-quality checklist at gate 1 | spec-driven 7 | Adapt, folded into ADR-0071 | **done**, scoped down — the PRD skill's clarify step checks for unquantified claims | — | — | — |
| Per-work-item context pack derived at dispatch | spec-driven 8 | Adapt, deferred | not started | M | low | own ADR if pursued; under the 2026-09-21 seed's "remaining mechanisms", not named in it |
| Sub-agent remaining-budget inheritance | harnesses 1 | Adapt, deferred | not started; the Conductor's per-item spend isolation (#954) is adjacent | M | low | own ADR when recursive dispatch exists; same seed |
| Live budget-remaining dashboard field | harnesses 6 | Adapt | not started | M | low | `dashboard.py`; same seed |
| Known-answer output evals with a deterministic grader; should-ask-not-act scenarios | rea 1, 2 | Adopt | not started | M | medium | `eval_schema.py` record kind + oracle fixtures; own ADR beside ADR-0019 — seeded here |
| Epistemic vocabulary (observed / derived / inferred / unknown) and a fail-closed roll-up rule | rea 3 | Adopt | not started; detector H enforces the per-section half only | S docs, M gate | medium | `CONTEXT.md`, the protocol, verify and review templates — seeded here |
| Close out broad reports by revisiting the starting questions | rea 4 | Adopt | not started in the skills; the research notes already do it | S | low | audit, automate, deepen report sections — seeded here |
| Plugin version moves mechanically; doctor reports the installed version | rea 5 | Adopt | (a) superseded by ADR-0095; (b) argued against by ADR-0099's rejected alternative (the installed-plugins file is private and multi-valued); `conductor.py --version` prints the payload version instead | — | — | — |
| `factory-init stamp --plan` | rea 6 | Adopt, medium-low confidence | not started; stamp already refuses overwrites | S | low | `factory_init.py`; not seeded |
| Worked showcases from real runs | rea 7 | Adopt, low-medium confidence | not started | M | low | README section; not seeded |
| Skill-design guide | rea 8 | Adopt, low-medium confidence | not started | S | low | a page beside ADR-0023; not seeded |
| "A green regression test is not the fix" for maintenance runs | rea 9 | Adopt | not started | S | low | review skill rules + the ship template — seeded here |
| `claude plugin eval` as the with/without harness | jev 1 | Adopt | **done** — ADR-0081, `plugin-evals/` | — | — | — |
| Run `/skill-doctor` and `/doctor prompt-audit` once | jev 2 | Adopt | not started; free, needs a session | S | low | seeded here |
| Wire `lean` into implement and review | jev 3 | Adopt | **done** — both skills cite lean's ladder and cut-list | — | — | — |
| Per-stage effort and compaction in autorun / work-queue | jev 4 | Adopt | partial — the Conductor prices steps by charter band; autorun and work-queue set no effort | S–M | medium (caps and the ledger) | not seeded |
| Description-narration probe (address-pr-review, two variants) | workflow-summary-descriptions | a one-off test | not run; needs an explicit go-ahead (ten real runs) | S, paid | low | seeded here |
| Knowledge base, inline index, paired ablation | knowledge-base, -evidence, -ablation | recommendation | **done** — ADR-0078, `kb.py`, the 2026-10-10 ablation record | — | — | — |
| Derived trace view | knowledge-system-over-time | recommendation | **done** — ADR-0092, `trace.py` | — | — | — |
| Owner / Conductor / Worker, Reviewer as a dispatched role | orchestrator, orchestrator-roles | recommendation | **done** — the conduct skill, `conductor*.py`, ADR-0085, ADR-0086 | — | — | — |
| `ux-patterns` plus a slice of heuristics in polish | ux-writing-and-ux-patterns | recommendation | **done** — the ux-writing and ux-patterns skills, ADR-0079 | — | — | — |
| Accepted-order baseline and its formula fix | autonomy-baseline | finding | **done** — ADR-0080 | — | — | — |

## Why `kb.py lint` did not go into `make check`

The xerj note's row 4 and the 2026-10-16 seed price it as one Makefile
line. Two facts found while preparing it say otherwise, and both need
a decision rather than code:

1. **CI checks out at depth 1.** The validator's `check` job uses
   `actions/checkout@v4` with no `fetch-depth`, so the checkout holds
   one commit. `kb.py lint`'s staleness check runs `git rev-parse` on
   each page's `verified:` sha and `git diff <sha> HEAD` over its
   sources; in a `--depth 1` clone of `main` it reports all six pages
   as "verified … is not a commit in this repository" (reproduced on
   2026-10-16). Fixing it means `fetch-depth: 0` on a mirrored,
   gate-path workflow that every stamped repo also runs, for a line
   their Makefile never carries.
2. **Squash merges orphan a branch pin.** The re-verify convention
   (#950, #962) pins `verified:` to the `main` commit the page was
   checked against. A PR that itself changes a page's source cannot
   satisfy the gate that way: pinned to the base, its own CI sees the
   change and goes red; pinned to its branch head, `main` goes red
   after the squash merge deletes the branch and the sha is reachable
   from nothing. `gates.py` has the most-cited sources (three pages),
   so this would bite often.

Options the decision could pick: staleness measured against the merge
base with `origin/main` rather than `HEAD`; a lint mode without the git
half for CI (fields, links, index budget and sync are still worth
gating); or `fetch-depth: 0` plus a rule that the merge train re-pins
after each merge. None is a Makefile line, so the item is a seed with
these facts attached.

## What this pass changed

Four PRs, each from a fresh `origin/main` and independent of the
others, plus this note's PR. Each adopted item got its own plain issue
(`type:chore`) because detector B requires a `Closes #N` per PR and
#956 closes only with this note.

- #960 — `feat(github)`: `.github/PULL_REQUEST_TEMPLATE.md`, fail-closed
  (an unedited `No work order:` and `Closes #` both fail detector B),
  with the house sections and the provenance block. Closes #959. A gate
  path, so a human merges it.
- #962 — `docs(kb)`: the four pages #957 made stale re-verified against
  `a364649`; the two about the stamp and the manifest now say what a
  tools-only target does (ADR-0099). Closes #961. `kb: 0 problem(s)` on
  the branch — and stale again the moment #967 touched `factory_init.py`
  and `gates.py` after it, which is the pin mechanism working as
  designed: the hourly routine's rung 3 re-verifies, and re-pinning in
  a loop from a PR is exactly the squash-merge problem above.
- #964 — `feat(make)`: `python3 kb.py drift` after `lint.py` in `check`,
  dropped from the stamped twin by `product_makefile` (payload
  byte-identical), pinned by the lockstep and transform tests, listed
  in `CLAUDE.md`, `AGENTS.md` and `README.md`. Closes #963.
- #966 — `docs(readme)`: the Install block ends with
  `/idea-to-prod:doctor` and the summary line captured from a run of the
  skill at 0.19.0 against an empty repository. Closes #965.

Not changed, deliberately: `.claude-plugin/plugin.json` (ADR-0095); any
eval definition or result; any skill body — the doctor wording and the
rea-learnings prose rules are seeds, not surprises in a docs PR.

## Seeds

Appended to `docs/backlog.md` in its grammar, each
`(from: session:2026-10-16)`: the `kb.py lint` decision with the two
facts above; pinning doctor's plugin-only summary wording in its SKILL.md
so the README's quoted line is a contract; known-answer output evals
(rea 1 and 2); the epistemic vocabulary and roll-up rule (rea 3); the
close-out table for audit, automate and deepen (rea 4); the green
regression test rule (rea 9); the free `/skill-doctor` and
`/doctor prompt-audit` pass (jev 2); and the description-narration
probe, awaiting a go-ahead. The four-survey remainder stays under the
2026-09-21 "NOT ratified" seed, which already holds it for a dedicated
session; `stamp --plan`, showcases and the skill-design guide are listed
above as not seeded, on the rea note's own confidence.

## Couldn't verify

- Whether GitHub applies the PR template to PRs the hourly and
  merge-train routines open: they pass `--body-file`, which the
  template does not touch, so the answer is expected to be no and
  nothing here depends on it.
- The doctor summary's exact wording on a later run: the skill fixes
  the shape, not the words for a skipped tier. The README dates its
  quote; the seed above is the fix.
- That `kb.py drift` stays at 0 problems across the open PRs: it was
  run on `a364649` and on the branch, not against each open PR's
  instruction-file edits.
