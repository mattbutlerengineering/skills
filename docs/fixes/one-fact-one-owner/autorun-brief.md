# Autorun brief: one-fact-one-owner

Collected 2026-08-23 by the operator, who chose this seed from
`docs/backlog.md` and left release authorization unstated. This is not a
run artifact: it carries no frontmatter, never counts toward orientation,
and is the source of interview answers for every stage of this run.

## What and why

Two backlog seeds, both produced by completed maintenance runs, name the
same gap:

- **`docs/backlog.md:19`** (from `maintenance:deepening-cli-seams`) — "A
  drift detector for retyped seam grammar — post-fold adopters are never
  re-checked: two mirrored tools retyped `cli.report`'s epilogue days
  after the ADR-0051 fold and only a manual deepening review caught it;
  the detector suite covers citations, checksums and staleness but not
  'a tool restates a seam it should call'."
- **`docs/backlog.md:45`** (from `maintenance:deepening-tool-seams`) —
  the same gap with a measured number attached, quoted under *The
  condition* below.

This run claims both. Capture appends `(claimed: maintenance:one-fact-one-owner)`
to each of those two lines — the protocol's in-place claim, which appends
to the line and never rewrites the `(from: …)` origin marker.

Run scale: **maintenance run**, slug `one-fact-one-owner`, artifacts at
`docs/fixes/one-fact-one-owner/`. Re-entry depth is **architect** — this
adds a tool that does not exist and the design question below is real, so
the run uses the `architecture.md` + `breakdown.md` chain. The precedent
for artifact depth and work-item lettering is `docs/fixes/deepening-tool-seams/`
(2026-08-18), which is also the run that produced the sharper of the two
seeds.

## The condition

The repo's stated bar is that a fact has one owner. CLAUDE.md puts it as
the shared-module rule; ADR-0037, ADR-0039, ADR-0040, ADR-0056 and
ADR-0060 are each one instance of enforcing it by hand. **Nothing
mechanical checks it.** The only finder the class has is a human reading
the tree during a deepening review, and that finder now has a measured
miss rate.

### Evidence — verified against git history at HEAD `7650052`

The seeding review was taken at `fbfa3c3` (2026-08-17). Three instances
of the class were **already in the tree at that commit** and the review
did not surface them:

| Instance | Duplicate created | Closed |
|---|---|---|
| `knowledge_plane.DONE_ROW` byte-identical to `gates.MERGED_ROW` | `MERGED_ROW` `208ffdb` 2026-07-11 (#130); `DONE_ROW` `4333370` 2026-08-10 (#221) | ADR-0058, `7988962` 2026-08-22 (#312) |
| `sweeps.reconcile_drift` vs `dashboard._drift` | `_drift` `02de371` 2026-08-13 (#268) | ADR-0060, `7650052` 2026-08-22 (#316) |
| `sweeps.issue_lifecycle` retyping `cli.label_names` | `issue_lifecycle` `f38fbdd` 2026-08-10 (#204); `label_names` `622e2bf` 2026-08-10 (#247) — same day | **Still open.** ADR-0060 moved the copy into `plane_drift.issue_lifecycle` unchanged |

The seeding review confirmed six candidates and its run fixed four, so
the hit rate of the only finder this class has is **4 of 7**. Two of the
three misses needed their own ADRs within four days of that run shipping.

The third is the sharpest fact in this brief: **the refactor whose whole
purpose was collapsing a duplicated rule carried a different duplicated
rule across with it**, and said so in its own ADR. Both of
`plane_drift.py`'s callers import `label_names` from the cli seam and use
it feet away — `sweeps.py:63` with `:291`, `dashboard.py:46` with `:181`
and `:251` — while `plane_drift.py` imports only `knowledge_plane` and
runs its own `entry.get("name")` loop with its own strictness.

**Re-verify every line number above against HEAD before relying on it.**
They are as of `7650052` and this tree moves daily.

## Target state

Something mechanical answers "is this fact stated twice?" and runs often
enough to catch a duplicate in days rather than at the next manual
review. Seed 45 bounds the ambition deliberately: *"the mechanical form
is cheap enough to be a pre-pass rather than a detector at first."*

The two mechanical forms both seeds name:

1. **Identical module-level bodies** — the same regex or constant
   defined in two modules (the `DONE_ROW` / `MERGED_ROW` shape).
2. **A module that imports a seam helper and also retypes it** — the
   `plane_drift` / `label_names` shape, and the `cli.report` epilogue
   shape from seed 19.

## The design question this run exists to answer

**Do not let any stage skip past this.** A checker for this class has a
false-positive problem the other detectors do not, because this repo has
*recorded, deliberate* duplicates:

- `protocol._CHECKBOX` is deliberately a second owner of the checkbox
  grammar — it captures the box contents and is deliberately
  factory-agnostic (ADR-0058 says so explicitly, and ADR-0039 said it
  before that).
- ADR-0037 lists what deliberately did **not** move to the seams.
- ADR-0056 lists what deliberately did not move to `human_gates`.

So the tool needs a way to say "this pair is deliberate, and here is the
ADR" — an annotation, an allow-list, or a carve-out roster — or it cries
wolf on decisions the repo already made and gets ignored, which is worse
than not having it. **Where that list lives, and what stops IT from going
stale, is the design question.** ADR-0039's roster went stale in exactly
this way (that is what ADR-0058 records), so an unchecked carve-out list
would reproduce the very failure this run is fixing.

Architect owns the answer. The brief does not pre-decide it.

## Scope

**In scope:**

1. The mechanical check itself, in whichever of the two forms above the
   Architect stage justifies — one form is an acceptable first cut if the
   second is argued and deferred in the artifact.
2. The carve-out mechanism for deliberate duplicates, per the design
   question above.
3. Its home and its trigger: a `gates.py` detector, a standalone script,
   a Makefile target, or a review-time pre-pass. **Facts, not decisions:**
   detector letters `A`–`L` are all in use, so `M` is the next free one;
   a `gates.py` detector runs in CI on every push and must be
   exact-string tested with near-zero false positives; a pre-pass carries
   a much lower bar because a human reads its output.
4. **The acceptance fixture:** the tool must find the one instance that
   is still open — `plane_drift.issue_lifecycle` retyping
   `cli.label_names`. A tool that cannot find the known-live instance is
   not done.

**Out of scope, and why — do not widen into these:**

- **Fixing `plane_drift.issue_lifecycle`.** It is this run's *fixture*,
  not its cleanup target. It is already seeded separately
  (`docs/backlog.md:46`) and fixing it here would leave the tool with
  nothing live to prove itself against.
- **`row_done`'s missing `ROW.match` guard** (`docs/backlog.md:41`).
  A behaviour change that moves what detector G counts as a merged work
  order — it needs its own decision, not a ride-along.
- **Provisional-ADR staleness** (`docs/backlog.md:47`) and
  **`label_sync.py` having no runner** (`docs/backlog.md:48`). Real,
  seeded, different runs.
- **Restructuring the `DETECTORS` roster or detector J's roster.** That
  is the payload of `WO-0039` in the active `first-live-dispatch` feature
  run. *Adding* an entry to the roster is fine; changing how the roster
  works is not. That run is mid-flight and blocked on operator-held
  secrets — do not disturb its target.
- Any change to `skills/**` prose, `evals/**`, or the pipeline protocol.
- Re-litigating any ADR listed under the design question. They are the
  input to the carve-out list, not candidates for reopening.

## Success criteria

- The check exists, runs from a documented command, and its output is
  label-prefixed problem strings per the repo's contract.
- **It finds `plane_drift.issue_lifecycle` retyping `cli.label_names`**
  without being told about it specifically.
- **It stays silent on every recorded deliberate duplicate**, at minimum
  `protocol._CHECKBOX` versus `knowledge_plane.ROW`. Zero false positives
  on the tree at HEAD, or every exception is in the carve-out list with
  its ADR named.
- A test exists that would have caught each of the three historical
  instances in the evidence table — run against fixtures reproducing
  their shapes, not against the live tree, so the test does not decay as
  the tree is cleaned.
- The full battery is green: `python3 -m unittest discover tests`,
  `python3 lint.py` (matching `lint: 0 problem(s)`), `python3 gates.py &&
  python3 gates.py --selftest` (matching `gates: 0 problem(s)` and
  `selftest: ok`).
- If the check ships as a `gates.py` detector or a mirrored root tool,
  `python3 factory_init.py update-manifest` is run and committed in the
  same change, and detector E is green.
- The test-ordering rule is visible in the history: tests at the intended
  interface land before the implementation.

## Constraints and things already decided

- **Stdlib only.** Standalone Python 3 standard library, no third-party
  imports. Note the consequence: there is no AST-diffing library and no
  YAML parser; `ast` itself is stdlib and is available.
- **Problem-string contracts:** checkers return lists of label-prefixed
  problem strings; callers print and exit nonzero. Tests assert exact
  strings through public interfaces.
- **New shared module bar** (CLAUDE.md): multiple real callers AND
  observed divergence. Anticipated reuse does not qualify.
- **Mirrored-into-payload rule** (ADR-0060): a module is mirrored iff a
  payload tool imports it — not because it is shared. A new root tool
  that no payload tool imports stays root-only and joins no manifest.
- **Template mirroring is checksum-pinned.** Any edit under
  `factory/templates/**` or to a root file in `factory_init.MIRRORS`
  requires `python3 factory_init.py update-manifest`, committed with the
  change, or detector E fires.
- **Recorded decisions that touch this work, all live:** ADR-0037
  (accepted — the seam modules and what deliberately did not move),
  ADR-0039 (amended — the checkbox-regex roster, and the record of how a
  roster goes stale), ADR-0051 (accepted — the report epilogue fold, whose
  adopters are seed 19's subject), ADR-0056 (provisional — `human_gates`),
  ADR-0058 (provisional — two owners, not three), ADR-0060 (provisional —
  the drift rule and the mirrored-iff-imported rule). **None is being
  reopened.** Six of the last seven ADRs are provisional and unconfirmed;
  treat a provisional ADR as citable but unsettled, exactly as ADR-0060
  had to.
- **Offer an ADR only** when a decision is hard to reverse, surprising
  without context, and the result of a real trade-off. The carve-out
  mechanism probably qualifies; the tool's existence probably does not.
- Match the surrounding style. Many small files; 200-400 lines typical.

## Tracker

**No tracker interaction.** No issues created, imported, or closed; work
items carry no `(tracker: #N)` references. Under prepare-and-stop there is
no PR, so detector B never arises. If release authorization is later
raised to open a PR, a `Closes #N` target must be decided **before** the
PR is opened — detector B cannot be pre-flighted locally.

## User-facing surface

None. Internal tooling only, and maintenance runs skip the PRD stage, so
no `ux:` decision arises.

## Release authorization

**Prepare and stop — no release is authorized.**

The operator was asked and expressed no preference, and the autorun rule
is that absent an explicit yes the default is prepare-and-stop. Ship runs
its pre-flight checks and writes `release.md` recording readiness and the
exact release steps, and executes **no externally visible action**: no
branch push, no PR, no merge, no tag, no workflow dispatch.

"Production" for this repo is `main` — the plugin is vended from the repo
and the payload is stamped from `factory/templates`. There is no deploy
step and no version tag; the project has never tagged a release. So the
steps `release.md` records are: a branch, a PR against main, a green
battery, and a squash merge — recorded for the operator to execute, not
executed here.

## Interview answers the stages will need

- **Who suffers, and how do they cope today?** The operator and the
  dispatched agents. Coping today means a duplicate lives in the tree
  until someone runs a manual deepening review and happens to see it —
  which, measured, happens 4 times in 7.
- **Why now?** Two instances needed emergency ADRs on 2026-08-22, four
  days after a run that was specifically hunting this class shipped, and
  a third is still open in a module created that same day. The class is
  not slowing down, and the factory is about to dispatch agents at these
  tools.
- **Evidence strength:** direct and dated, not anecdotal. Every row in
  the evidence table is a commit hash, a date and a PR number verified
  against git history at `7650052`. The 4-of-7 hit rate is the seeding
  run's own count, recorded in its retro.
- **Blast radius:** internal tooling and, if it ships as a detector, CI.
  No user-facing surface, no data, no external contract. The risk is a
  noisy check that gets ignored or, worse, one that fails CI on a
  deliberate carve-out.
- **How this dies:** the carve-out list is skipped and the tool fires on
  `protocol._CHECKBOX` on day one, so it gets disabled; or the check is
  built so cleverly (AST equivalence, cross-module call analysis) that it
  costs more to maintain than the manual review it replaces; or it ships
  as a detector with a bar it cannot meet and turns CI red on a false
  positive.
