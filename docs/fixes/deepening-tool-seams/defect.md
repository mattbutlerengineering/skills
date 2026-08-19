---
stage: capture
run: maintenance:deepening-tool-seams
date: 2026-08-18
re-entry: architect
assumptions:
  - "Root-cause hypothesis: the brief supplies evidence, target state and scope but names no root cause. The hypothesis below is mine, drawn only from facts re-verified at fbfa3c3 and labelled as a hypothesis — it is not the operator's answer, and it is the sentence to correct if it is wrong."
---

# Condition: four facts that have more than one owner

## Condition

A deepening review of this repo at commit `fbfa3c3` (2026-08-18) confirmed
six candidates against real call sites. Four are in scope here. The
degradation is not breakage: in each one a fact that should have a single
owner is stated in several places, and the copies have begun to disagree.

1. **The gh-listing ritual has no owner.** `cli.gh_json` (cli.py:315) and
   `cli.full_window` (cli.py:337) are two shallow halves of one operation,
   so the composition — window constant, matching `--limit`, failure catch,
   full-window check, label prefixing — is retyped in every caller. Seven
   modules declare their own `LIST_WINDOW`.
2. **The gate vocabulary lives inside a leaf tool.** `GATES`,
   `label_events`, `waiting_since` and `mirror_map` are gate_digest.py's,
   and three other modules — one of them a CI detector — reach in for them.
3. **`product_form` is two functions with one name.** tests/test_gates.py
   imports the production transform and then rebinds the name to a local
   copy that respells one fewer tool.
4. **Month-to-date spend is defined twice.** cost_report.py excludes gate
   rows before summing; work_queue.py does not. That number is what the
   monthly circuit breaker guards.

**Target state that ends this run.** Each fact has exactly one owner and
the copies are gone: one deep entry point at the cli seam that takes the
label, the operation name and the args, owns the window, and returns the
value with already-prefixed problems (the seven `LIST_WINDOW` constants
collapse to a parameter); a gate plane module owning the gate rows, the
label-event walk and the stay partition, with the digest, the miner, the
dashboard and detector J as thin callers, and detector J no longer
depending on tuple field order; the test shadow deleted so the line-18
import is the only `product_form`, plus the missing `toolsmith-mine`
lockstep assertion; and one `month_to_date` at the `cost_ledger` seam used
by both callers, which keep their own cap comparisons.

Two facts about the *shape* of that state, decided before this run and not
reopened by it: the new-shared-module bar (multiple real callers **and**
observed divergence between their copies) is met by items 1, 2 and 4, and
the problem-string contract stays — checkers return label-prefixed problem
strings and callers print and exit nonzero.

## Reproduction / Evidence

Enumerated at `fbfa3c3`, each line visited. Counts below exclude
`tests/`, `factory/templates/` (the mirrored payload twins) and the
`.claude/worktrees/` copies.

**1. The gh-listing ritual.** What a caller must know, none of it in a
signature: declare a window constant; embed `str(LIST_WINDOW)` in its own
`--limit`; catch `cli.CLI_FAILURES`; call `full_window` separately with a
limit that must match the `--limit` it did not pass; and hand-prefix
`"<label>: <operation> "` onto both returned suffixes.

- `gh_json`: **14 call sites in 8 modules** — label_sync.py:109,
  validator.py:323, assembler.py:259, dashboard.py:147, :166, :240,
  gate_digest.py:198, :295, sweeps.py:337, :465, work_queue.py:178,
  rejection_mining.py:174, :193, :244.
- `full_window`: **10 call sites in 7 modules** — label_sync.py:112,
  assembler.py:265, gate_digest.py:302, dashboard.py:178, :252,
  sweeps.py:345, :478, work_queue.py:184, rejection_mining.py:200, :250.
- `LIST_WINDOW` is declared **7 times**: assembler.py:60=1000,
  dashboard.py:70=1000, gate_digest.py:169=1000, label_sync.py:94=1000,
  rejection_mining.py:51=1000, sweeps.py:117=500, work_queue.py:43=100.
- The warning travels with the copy. label_sync.py:92–93,
  gate_digest.py:167–168 and rejection_mining.py:49–50 carry the same two
  comment lines byte for byte; assembler.py:57–59 is those two lines plus
  an attribution (`(rejection_mining's discipline)`); dashboard.py:68–69
  paraphrases them and cites gate_digest.
- **Observed divergence:** work_queue.py types its window twice — the
  literal `"100"` inside `LIST_ARGS` (work_queue.py:41–42) and
  `LIST_WINDOW = 100` (:43). That is the drift the copied comment warns of,
  already present.
- The deepened interface must serve every caller shape in the tree:
  - *continue with a warning* — label_sync.py:112–113, assembler.py:265–267,
    gate_digest.py:302–304, dashboard.py:178–180, :252, rejection_mining.py:200–202,
    :250–252;
  - *refuse, because absence would read as a finding* — work_queue.py:184–186
    and sweeps.py:345–347 return `None`;
  - *use the check for its truth value and write its own sentence* —
    sweeps.py:474–481, deliberately, with the reason in the comment.
  - The empty value differs per caller too: `None` (label_sync.py:111,
    assembler.py:261, sweeps.py:342, work_queue.py:181),
    `{"changed": "false"}` (gate_digest.py:297–299), `{}`
    (rejection_mining.py:246–248), `[]` (rejection_mining.py:194–198), and
    dashboard.py:171–177 appends then returns `None`.
  - Prefixing is not uniform either: most callers prefix at the call site,
    but label_sync's `live_labels` returns *unprefixed* suffixes
    (label_sync.py:111–113) and `sync` adds `L: ` one frame up
    (label_sync.py:127–129) — and that one call site does not wrap
    `gh_json` at all (label_sync.py:109), letting `CLI_FAILURES` (aliased
    at the door, label_sync.py:21) reach the caller instead.

**2. The gate vocabulary has no home.** `GATES` (gate_digest.py:50),
`label_events` (:73), `gate_passages` (:89), `waiting_since` (:120) and
`mirror_map` (:174) live in one leaf tool. Reaching in:

- dashboard.py:52 — `from gate_digest import GATES, label_events, mirror_map, waiting_since`
- rejection_mining.py:40 — `from gate_digest import GATES, label_events, mirror_map`
- gates.py:777–778 reads the tuple positionally —
  `{name for gate in mod.GATES for name in gate[1:3]}` — inside
  `LABEL_DECLARERS` (gates.py:774), consumed at :798 by
  `check_label_wiring`, detector J (gates.py:814).

**Observed divergence:** the stay algorithm is written twice.
gate_digest.py:99–110 and rejection_mining.py:69–80 are the same
confirmations list and stay-collection loop; the window test that follows
is spelled two ways for the same rule — `c >= start and (next_start is
None or c < next_start)` (gate_digest.py:114–115) versus `start <= ts and
(window_end is None or ts < window_end)` (rejection_mining.py:85–87). The
invariant that joins them — the two tools partition completed stays
between them, every stay a passage there or a rejection here, never both —
exists only as prose, in `gate_rejections`'s docstring
(rejection_mining.py:62–66).

**3. The `product_form` test shadow.** tests/test_gates.py:18 imports the
production transform (`from factory_init import product_form`);
tests/test_gates.py:1626 rebinds the same name to a module-level copy. Six
call sites use the shadow — :1706, :1714, :1802, :1824, :1845, :1865 — in
six methods of one class, `TestLockstep` (tests/test_gates.py:1641).

**Observed divergence:** `factory_init._PRODUCT_TOOLS`
(factory_init.py:54–56) lists **7** tools and `product_form`
(factory_init.py:59) respells all of them; the shadow respells **6**,
omitting `rejection_mining.py`. Both docstrings assert the opposite of
what the code does — factory_init.py:63–64 ("never a test-private copy")
and tests/test_gates.py:1649–1652 ("the root->product respelling the
assertions lean on is factory_init.product_form ... never a test-private
copy of the translation rule").

Why it has not bitten, and how it would: `toolsmith-mine` is the one
factory target with no lockstep assertion. The root spelling is
`python3 rejection_mining.py mine` (Makefile:68–69) and the payload's is
`python3 tools/factory/rejection_mining.py mine`
(factory/templates/Makefile:64–65), generated through the production
transform. `TestLockstep`'s target constants cover only assembler
(tests/test_gates.py:1663), cost-report (:1669), gate-digest (:1675),
wo-record (:1676) and `CANONICAL_CHECK` (:1681). An assertion for
`toolsmith-mine` written against the shadow fails, because the shadow
leaves that command unrespelled.

**4. Month-to-date is defined twice.**

- `cost_report.aggregate` (cost_report.py:53) skips gate rows —
  `if cost_ledger.gate_wait(entry) is not None: continue`
  (cost_report.py:70–71) — before summing.
- `work_queue.month_to_date` (work_queue.py:191) sums every row the month
  predicate admits (work_queue.py:195–196), with no gate-row skip.

Checked against the live ledger at `fbfa3c3`: **38 rows, 19 of them gate
rows** (`gate_wait:merge:*`), the other 19 `owner-session:unmetered`. Every
row — gate and dispatched alike — records `0.0` cost and `0` tokens, so
both definitions return `$0.00` today and neither the divergence nor its
absence is visible. Two things keep it invisible: gate rows are free *by
construction* at the writer (`cost_ledger.gate_entry`, cost_ledger.py:64,
always writes `0` tokens and `0.0` cost), and no test pins the case —
`gate_wait` appears **0 times** in tests/test_cost_report.py and **0
times** in tests/test_work_queue.py.

In the same cluster, two smaller copies: the month string is derived three
ways — cost_report.py:185–186 (`clock().date().isoformat()` then `[:7]`),
work_queue.py:194 (`now.strftime("%Y-%m")`), dashboard.py:452
(`now.date().isoformat()[:7]`) — and `_utcnow` is a byte-identical twin at
cost_report.py:174–175 and work_queue.py:50–51.

Not part of this item: `>=` (cost_report.py:100) versus `>`
(work_queue.py:150). Those answer different questions — has the month
breached the cap, versus would this batch breach it — and are not a
divergence.

## Root-cause hypothesis

**Hypothesis, not a finding, and mine rather than the brief's.** Two
forces, both visible in the evidence:

*Shallow halves propagate by copy.* `gh_json` and `full_window` are each
individually correct and each individually too small to be useful alone.
A module that needs a windowed listing cannot import the operation,
because no module owns it — so it imports the halves and copies a
sibling's composition, comment included. The three byte-identical comments
and assembler's attributed near-copy are the propagation path made
literal: the warning about drift is itself the thing being duplicated.

*The repo's own bar schedules this class of drift.* CLAUDE.md admits a
shared module only on multiple real callers **and** observed divergence
between their copies. That rule is right — it is what keeps this tree from
premature seams — but its consequence is that a fact must first be
duplicated and then be *seen to disagree* before it may be given an owner.
Items 1, 2 and 4 are exactly that rule arriving at its due date: work
queue's duplicate literal, the miner's re-spelled window test, and two
month-to-date definitions are the divergences the bar was waiting for.

A narrower hypothesis for item 3: the shadow predates `_PRODUCT_TOOLS`'s
seventh entry and nothing re-checks a test-private copy against the
production transform it claims not to be. Nothing in the detector suite
looks for a name imported and then rebound.

## Blast radius

- **Internal tooling and CI detectors. No user-facing surface, no data
  migration, no external contract.**
- **Most of it ships.** cli.py, cost_ledger.py, cost_report.py,
  gate_digest.py, rejection_mining.py, label_sync.py, assembler.py,
  work_queue.py and gates.py all have payload twins under
  `factory/templates/tools/factory/`, so every stamped product repo
  carries these copies. dashboard.py and sweeps.py are factory-repo-only.
- **Risk concentrates in two places.** gates.py, because detector J reads
  `GATES` positionally and the detectors are the CI suite; and the
  mirrored payload, where any edit to a mirrored root file without
  `python3 factory_init.py update-manifest` fires detector E.
- **Who suffers today:** whoever next edits one of these tools — in
  practice the operator and the dispatched agents. Coping means reading a
  sibling tool to learn the ritual, and copying it. The factory is about
  to dispatch agents at these tools for the first time, and an interface
  costing five undocumented facts to use correctly is worse to hand an
  agent than a human.
- **Nothing is currently wrong for a user of the tools.** Every observable
  output is what it should be; item 4's two definitions agree at `$0.00`.

**Scale: small-to-medium.** Review and Ship scale to that. Verify does
not: the ledger case in the success criteria — a gate row with a nonzero
cost — is the regression evidence this run owes, because it is the case
that makes the month-to-date divergence observable, and no suite has it.

## Ruled out

Deliberate exclusions. Each is closed for a stated reason; none should be
re-opened inside this run.

- **The detector roster / `DETECTORS` inertness in gates.py.** Real, and
  the same drift will recur, but it is the payload of WO-0039 in the
  active `first-live-dispatch` feature run
  (docs/features/first-live-dispatch/breakdown.md:31) — the factory's
  first live dispatch. Changing that target mid-flight trades a proof for
  a cleanup.
- **The harness stream's frame grammar**, duplicated between
  trigger_eval.py (the decode loop from :131) and
  `charter_replay._consume_frame` (charter_replay.py:182). Confirmed
  duplication, but the shape of one interface serving both consumers is
  not settled — it needs designing, not moving.
- **`cli.harness_run(spawn=)`** (cli.py:167). No production caller passes
  it: charter_replay.py:389 and trigger_eval.py:297 both omit it, and only
  tests inject. Noted, not taken.
- **The hand-typed `"<label>: "` problem-string prefixes in gates.py.**
  They stay literals; deriving them is a separate change, priced against
  the exact-string test contract. (The review counted 52; I did not
  re-count, and no count is load-bearing here.)
- **The `check_*(root)` temp-directory fixture cost.** The largest
  measured friction in the tree — 421 `TemporaryDirectory` sites across
  tests/, with the suite at 1,234 tests today — but it is a claim about
  test ergonomics in aggregate, not a deepening confirmed at call sites.
- **`factory.py` adoption.** ADR-0054 (provisional) records that a prior
  deepening review found its zero file callers and decided that is the
  intended state. Do not re-raise it.
- **Folding the knowledge-plane row regexes.** ADR-0037 defers this until
  a real divergence is observed. None was observed in this review.
- **Any change to `skills/**` prose, `evals/**`, or the pipeline
  protocol.**

## Notes

- **Variant.** This is a *condition* brief, not a defect brief: nothing is
  broken. The filename stays `defect.md` per the protocol.
- **Re-entry is architect** because three of the four items move an
  interface and one adds a module. Work items therefore live in
  `architecture.md` and `breakdown.md`, not here.
- **Capture interviews; this one did not.** Every answer came from
  `autorun-brief.md`, collected from the operator in one sitting on
  2026-08-18. That file is not a run artifact and never counts toward
  orientation.
- **Corrections made while re-verifying the brief at `fbfa3c3`** — the
  numbers above are the checked ones:
  - `gh_json` has 14 call sites across **8** modules, not 9;
    `full_window` has 10 across **7**, not 8. (The higher counts appear to
    include cli.py, which defines them.)
  - **Three** modules carry the byte-identical **two-line** window comment
    (label_sync, gate_digest, rejection_mining); assembler's is those two
    lines plus a third attribution line, and dashboard's is a paraphrase.
    The brief said four byte-identical three-line copies.
  - The `product_form` shadow is used by six methods of **one** class,
    `TestLockstep` — not five classes.
  - Every ledger row at `fbfa3c3` costs `0.0`, not only the gate rows, so
    the two month-to-date sums agree for a second reason as well; and gate
    rows are free *by construction* at `cost_ledger.gate_entry`, which is
    why a nonzero-cost gate row has to be written by hand to observe the
    divergence.
  - Line drift, all small: the gate-row skip is cost_report.py:70 (`:69`
    is the `for`); work_queue's month string is `:194` (`:193` is the
    ledger read); the duplicated stay blocks are gate_digest.py:99–110 and
    rejection_mining.py:69–80; the shadow's contradicted docstring runs
    tests/test_gates.py:1649–1652; the invariant prose is
    rejection_mining.py:62–66 and is a docstring, not a comment.
  - ADR statuses read differently in the tree than in the brief: ADR-0037
    is "amended by ADR-0039", ADR-0041 "amended by ADR-0049", ADR-0042
    "amended by ADR-0051". The decisions stand and this run reopens none
    of them; only the header word differs. ADR-0051, ADR-0053 and
    ADR-0049 are accepted; ADR-0054 is provisional.
- **No tracker interaction and no backlog claim.** Work items carry no
  `(tracker: #N)` reference, no issues are created or closed, and no
  `docs/backlog.md` seed was claimed for this run — none names this
  condition. (The seed "A drift detector for retyped seam grammar", from
  `maintenance:deepening-cli-seams`, is adjacent and stays unclaimed.)
- **Precedent.** `docs/fixes/deepening-cli-seams/` (2026-08-13) is the
  precedent for artifact depth, work-item lettering and ship mechanics.
- **How this run dies:** the gate-plane item grows past its evidence and
  starts moving `_timelines` and the post/upsert epilogues too; or an
  interface move quietly changes a tool's output and the exact-string
  tests are edited to match instead of the change being reverted.
