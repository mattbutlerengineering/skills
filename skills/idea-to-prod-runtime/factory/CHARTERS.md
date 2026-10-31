# Factory charters

The nine chartered roles PRD-0001 §Actors names — PM, architect, UX
designer, planner, engineer (`swe`), QA, reviewer, support, toolsmith —
plus the three human gates they all work between (ADR-0033).

Each role is two files:

- **an agent stub**, `factory/agents/factory-<role>.md` — frontmatter the
  dispatch plane reads (`name:`, `description:`, `tools:`, `route:`) and a
  compressed contract. The subagent registry keys on frontmatter `name:`,
  not the filename: a stub without it is silently undispatchable.
- **a charter**, `factory/charters/<role>/CHARTER.md` — the authoritative
  role definition: mission, stages with entry/exit criteria, actions per
  cycle, loadout, grants, `Must never`, handoff artifact, escalation.

The stub is a pointer; the charter wins wherever they disagree.

## Roles

| Role | Owns | Agent stub | Charter | Band |
|------|------|-----------|---------|------|
| PM | Idea → PRD; scope | `factory/agents/factory-pm.md` | `factory/charters/pm/CHARTER.md` | `architecture_review` |
| Architect | architecture.md + ADRs | `factory/agents/factory-architect.md` | `factory/charters/architect/CHARTER.md` | `architecture_review` |
| UX designer | flows, states, design system | `factory/agents/factory-ux.md` | `factory/charters/ux/CHARTER.md` | `architecture_review` |
| Planner | Decompose; work-order rows + blocked-by graph | `factory/agents/factory-planner.md` | `factory/charters/planner/CHARTER.md` | `implementation` |
| Engineer (SWE) | one work order → merge-ready PR | `factory/agents/factory-swe.md` | `factory/charters/swe/CHARTER.md` | `implementation` |
| QA | independent Verify; the evidence record | `factory/agents/factory-qa.md` | `factory/charters/qa/CHARTER.md` | `implementation` |
| Reviewer | Review; pre-chews the merge gate | `factory/agents/factory-reviewer.md` | `factory/charters/reviewer/CHARTER.md` | `architecture_review` |
| Support | signal intake, triage, Operate | `factory/agents/factory-support.md` | `factory/charters/support/CHARTER.md` | `mechanical` |
| Toolsmith | the factory's own machinery | `factory/agents/factory-toolsmith.md` | `factory/charters/toolsmith/CHARTER.md` | `implementation` |

Read the table left to right and the pipeline reads off it: PM → Architect
→ UX → Planner → SWE → QA → Reviewer, with Support feeding the front of
the line and the Toolsmith maintaining the line itself.

## Routing bands

A charter names a **band**, never a model id. The band resolves to a model
through the repo's `factory.json` `routing` table at dispatch (ADR-0034),
which is the single routing source of truth (ADR-0004). A `model:` in a
charter would be a second routing source — precisely the drift this
factory exists to detect — so `tests/test_factory_charters.py` fails the
build on one, in frontmatter or in prose.

Bands are assigned by the *class* of the work, per ADR-0034:

- `architecture_review` — roles whose artifact a human gate approves as
  judgment (PM at gate 1; architect and UX at gate 2) and the review that
  pre-chews gate 3.
- `implementation` — roles producing code or code-shaped plans and
  evidence: planner, SWE, QA, toolsmith.
- `mechanical` — intake and plumbing: support. ADR-0034 names sweeps and
  label plumbing as the cheap-model class explicitly.

Nothing here resolves a band to a model — that wiring is the routing work
order's job, not the charters'.

## Loadout evidence tiers

Charter loadout tables carry an evidence tier per pick. `MEASURED` and
`RUN` mean the ai-tooling evidence base has a result on record for that
pick. `UNRATED` means it does not: the pick is a starting default, and
saying so is cheaper than a fabricated tier (CLAUDE.md, eval honesty).
Tiers graduate only on a real run.

---

# The three human gates

Exactly three, each a physical control rather than a norm (ADR-0033).
Everything between them runs unattended. Gates 1 and 2 merge only by
the human code owner. At gate 3, ADR-0036 amends ADR-0033: the
independent, non-authoring Reviewer may merge when required checks are
green on the merge result, its re-executed review is recorded on the
PR, and the PR is not a gate change — gate-change PRs (`docs/adr/**`,
a run's `prd.md`, `architecture.md`, `docs/design/**`) stay with the
human owner, and authoring agents never self-merge. No charter may
move the gates.

Rejections at a gate are **comments, never silent edits** — the
correction stream is the raw material the toolsmith mines into charter
rules.

## Gate 1 — PRD approval

The scope artifact enters only via a PR touching the run's `prd.md`;
CODEOWNERS plus required code-owner review makes the merged PR the
approval record. Handed up by the **PM**.

- [ ] The PR touches `prd.md` only — no code, no ADRs riding along.
- [ ] The problem statement is one I recognize, and the evidence behind
      it is cited rather than asserted.
- [ ] Every success criterion is **measurable** — I can name the command
      or metric QA will run against it.
- [ ] The out-of-scope list is explicit and I agree with what it excludes.
- [ ] Open questions carry an owner and a stage that will answer them.
- [ ] `id: PRD-####` is in frontmatter and unique (detector C).
- [ ] Rejections go back as PR comments; nothing is silently rewritten.

## Gate 2 — Blueprint/ADR approval

The same mechanism on `docs/adr/**`, `architecture.md`, and
`docs/design/**`: architecture and design cannot exist on main
un-approved. Handed up by the **architect** and the **UX designer**.

- [ ] Every design claim traces to a PRD section — nothing widens scope
      approved at gate 1.
- [ ] Each hard-to-reverse decision has an ADR with honest consequences,
      including the unwelcome ones.
- [ ] Changed decisions **supersede** an accepted ADR; none is rewritten.
- [ ] No second source of truth is introduced for anything already
      tracked once (ADR-0004).
- [ ] New dependencies are justified, one by one.
- [ ] For user-facing surface: every flow has empty, loading, error, and
      success states, and the accessibility pass is recorded (or the
      stage is skipped on the record).
- [ ] The design's invariants are stated in a form a detector could check.

## Gate 3 — PR merge

Branch protection on main: required status checks (the detector suite and
tests), with code-owner review on the gate-change paths. Agent review
pre-chews every PR so this gate is judgment, not linting — and under
ADR-0036's conditions the independent Reviewer completes the merge
itself; the human owner merges the rest and audits post-merge. Handed up
by the **SWE**, pre-chewed by **QA** and the **Reviewer**.

- [ ] The PR body cites `WO-#### (PRD-#### §…)` and closes its issue
      (detector B) — the audit trail from code back to scope holds.
- [ ] Required status checks are green; none was bypassed.
- [ ] QA's verification record shows, per acceptance criterion, literal
      command output — or an explicit **NOT RUN** with a reason.
- [ ] **The Reviewer RE-EXECUTED that record — it did not read it.** The
      verdict carries the command the Reviewer ran and the literal output
      the Reviewer got, per criterion, or an explicit **NOT RE-EXECUTED**
      naming what could not be driven. Green CI plus a checked box is not
      evidence a criterion holds; it is evidence someone said it does. An
      agent's claim to have verified something is a claim, not evidence,
      and is verified by execution, never by reading the diff. (2026-07-11:
      an honesty gate reported a table claiming its own bypasses "now
      fire"; an independent reviewer re-ran the identical artifacts and
      every one passed silently.)
- [ ] Every place re-execution contradicted the author's self-report is
      recorded on the PR, and was escalated — a false self-certification
      impeaches the author's *other* claims, so the whole PR is suspect,
      not just the claim that broke.
- [ ] No test was weakened, skipped, or deleted to reach green.
- [ ] The Reviewer's verdict is posted and every security finding is
      closed or explicitly escalated.
- [ ] The diff stays inside the work order's row; scope creep goes back
      to the Planner.
- [ ] The run's cost line landed in the ledger (ADR-0034) — autonomy
      graduation has no data without it.
- [ ] Merging is mine or the independent Reviewer's under ADR-0036's
      conditions — never the author's, and gate-change PRs are mine
      alone. No graduation happens except as a deliberate,
      evidence-backed, owner-applied config change.

## Dormant fourth gate

Deploy workflows sit behind a GitHub environment with required-reviewer
approval (ADR-0033). It costs nothing while unused and is the gate that
activates the day a product has real users — no redesign needed.
