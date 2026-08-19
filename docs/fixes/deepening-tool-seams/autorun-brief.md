# Autorun brief: deepening-tool-seams

Collected once, 2026-08-18, from the operator. This is not a run artifact:
it carries no frontmatter, never counts toward orientation, and is the
source of interview answers for every stage of this run.

## What and why

A deepening review of this repo, taken at commit `fbfa3c3` (2026-08-18),
confirmed six candidates against real call sites. Four are in scope for
this run. In all four, a fact that should have one owner has several, and
the copies have already begun to disagree.

Run scale: **maintenance run**, slug `deepening-tool-seams`, artifacts at
`docs/fixes/deepening-tool-seams/`. Re-entry depth is **architect** — three
of the four items move an interface, and one adds a module. This is the
same shape as the completed `docs/fixes/deepening-cli-seams/` run
(2026-08-13), which is the precedent for artifact depth, work-item
lettering, and ship mechanics.

## The condition — evidence, per candidate

Every line below was confirmed by visiting the call sites, not inferred.
Line numbers are as of `fbfa3c3`.

### 1. The gh-listing ritual (the widest leverage)

`cli.gh_json` (cli.py:315) and `cli.full_window` (cli.py:337) are two
shallow halves of one operation, so the composition lives in every caller.
What a caller must know, none of it in a signature:

1. declare a `LIST_WINDOW` constant;
2. embed `str(LIST_WINDOW)` in its own `--limit` argument;
3. wrap the call in `try/except cli.CLI_FAILURES`;
4. call `full_window` separately, with a limit that must match the
   `--limit` it did not pass;
5. hand-prefix `"<label>: <operation> "` onto both returned suffixes.

- `LIST_WINDOW` is declared 7 times: assembler.py:60=1000,
  dashboard.py:70=1000, gate_digest.py:169=1000, label_sync.py:94=1000,
  rejection_mining.py:51=1000, sweeps.py:117=500, work_queue.py:43=100.
  Four carry a byte-identical three-line comment warning about drift.
- **Observed divergence:** work_queue.py types its window twice — once as
  `LIST_WINDOW = 100` (:43) and again as the literal `"100"` inside
  `LIST_ARGS` (:41). That is exactly the drift the copied comment warns of.
- `gh_json` has 14 non-test call sites across 9 modules; `full_window` has
  10 across 8.
- Caller shapes differ and the deepened interface must serve all three:
  most append to a `problems` list; work_queue.py:186 and sweeps.py:347
  return `None` instead; sweeps.py:478-481 discards the returned sentence
  and writes its own.

### 2. The gate vocabulary has no home

`GATES` (gate_digest.py:50), `label_events` (:73), `waiting_since` (:120)
and `mirror_map` (:174) live inside one leaf tool, and three other modules
reach in:

- dashboard.py:52 — `from gate_digest import GATES, label_events, mirror_map, waiting_since`
- rejection_mining.py:40 — `from gate_digest import GATES, label_events, mirror_map`
- gates.py:777 — reaches into the tuple positionally:
  `{name for gate in mod.GATES for name in gate[1:3]}`, from a CI detector.

**Observed divergence:** the stay algorithm is written twice —
gate_digest.py:100-110 and rejection_mining.py:70-80 — with two different
spellings of the same window test
(`c >= start and (next_start is None or c < next_start)` versus
`start <= ts and (window_end is None or ts < window_end)`). The invariant
that joins them ("the two tools partition completed stays between them")
exists only as a prose comment at rejection_mining.py:65.

This meets CLAUDE.md's two-part bar for a new shared module: multiple real
callers **and** observed divergence between their copies.

### 3. The `product_form` test shadow

`tests/test_gates.py:18` imports the production transform
(`from factory_init import product_form`), then `tests/test_gates.py:1626`
rebinds the same name to a local copy. Five lockstep classes use the
shadowed name (:1706, :1714, :1802, :1824, :1845, :1865).

**Observed divergence:** `factory_init._PRODUCT_TOOLS` (factory_init.py:54)
lists 7 tools; the shadow respells 6, omitting `rejection_mining.py`. The
docstring at :1649 asserts the opposite of what the code does — that the
respelling the assertions lean on "is `factory_init.product_form` ... never
a test-private copy."

It has not bitten because `toolsmith-mine` (Makefile:68) is the one factory
target with no lockstep class. A lockstep class for that target is in scope
as a second item.

### 4. Month-to-date spend is defined twice

- cost_report.py:69 skips gate rows (`if cost_ledger.gate_wait(entry) is
  not None: continue`) before summing.
- work_queue.py:191 sums every row in the month, with no gate-row skip.

Checked against the real ledger at `fbfa3c3`: 38 rows, 19 of them gate
rows, every gate row costing `0.0` with `0` tokens. **The two sums agree
today and only because ADR-0041's gate rows are free.** The definitions do
not agree, and the number they compute is what the monthly breaker guards.

Also in this cluster: the month string is derived three ways
(cost_report.py:185, work_queue.py:193, dashboard.py:452), and `_utcnow` is
a byte-identical twin at cost_report.py:174 and work_queue.py:50.

Not in scope from this cluster: the `>=` (cost_report.py:100) versus `>`
(work_queue.py:150) cap boundary. Those are different questions — has it
breached, versus would this batch breach — not a divergence.

## Target state

Each fact above has exactly one owner, and the copies are gone:

1. One deep entry point at the cli seam that takes the label, the operation
   name and the args, owns the window, and returns the value plus already-
   prefixed problems. The seven `LIST_WINDOW` constants collapse to a
   parameter.
2. A gate plane module owning the gate rows, the label-event walk, and the
   stay partition, with the digest, the miner, the dashboard and detector J
   as thin callers. Detector J stops depending on tuple field order.
3. The test shadow deleted; the line-18 import is the only `product_form`.
   Plus the missing `toolsmith-mine` lockstep class.
4. One `month_to_date` at the `cost_ledger` seam, used by both callers,
   which keep their own boundary comparisons.

## Scope

**In scope:** the four items above.

**Out of scope, and why — do not widen into these:**

- **The detector roster / `DETECTORS` inertness in gates.py.** Real, and
  the same drift will recur, but it is the payload of work order WO-0039 in
  the active `first-live-dispatch` feature run — the factory's first live
  dispatch. Changing that target mid-flight trades a proof for a cleanup.
- **The harness stream's frame grammar** (duplicated between
  trigger_eval.py:131-155 and charter_replay.py:182-202). Confirmed
  duplication, but the shape of a joint interface serving both consumers is
  not settled, and it needs designing rather than moving.
- **`cli.harness_run(spawn=)` having zero production callers.** Noted, not
  taken.
- **The 52 hand-typed `"X: "` problem-string prefixes in gates.py.** They
  stay literals; deriving them is a separate change priced against the
  exact-string test contract.
- **The `check_*(root)` fixture cost** (445 temp-directory sites across
  1,207 tests). The largest measured friction in the tree, but it is a
  claim about test ergonomics in aggregate, not a deepening confirmed at
  call sites.
- **`factory.py` adoption.** ADR-0054 (provisional) records that a prior
  deepening review found its zero file callers and decided that is the
  intended state. Do not re-raise it.
- **Folding the knowledge-plane row regexes.** ADR-0037 defers this until a
  real divergence is observed. None was observed in this review.
- Any change to `skills/**` prose, `evals/**`, or the pipeline protocol.

## Success criteria

- Each of the four facts has exactly one owner in the tree, demonstrable by
  grep: one window rule, one gate vocabulary, one `product_form`, one
  month-to-date definition.
- Every changed tool's observable output is unchanged — the gh-listing and
  gate-plane items are interface moves, not behavior changes. Where output
  does change, it is stated as a deliberate decision in the artifact.
- The full battery is green at the end: `python3 -m unittest discover
  tests`, `python3 lint.py` (matching `lint: 0 problem(s)`), `python3
  gates.py && python3 gates.py --selftest` (matching `gates: 0 problem(s)`
  and `selftest: ok`).
- `work_queue.py`'s duplicate window literal is gone.
- A `toolsmith-mine` lockstep class exists.
- A ledger test exists covering a **nonzero-cost gate row** — the case
  neither suite has today and the one that makes the month-to-date
  divergence observable.
- The test-ordering rule was followed and is visible in the commit history:
  new tests at each intended interface land against today's code before the
  deepening, and the superseded shallow-module tests die in the same change
  that deepens, with the diff saying which coverage moved where.

## Constraints and things already decided

- **Stdlib only.** Every script is standalone Python 3 standard library.
- **Problem-string contracts:** checkers and validators return lists of
  label-prefixed problem strings; callers print and exit nonzero. Tests
  assert the exact strings through public interfaces. ADR-0037 rejected a
  structured-findings layer and reopening it needs a production re-parser.
- **New shared module bar** (CLAUDE.md): multiple real callers AND observed
  divergence between their copies. Anticipated reuse does not qualify. A
  seam needs two adapters that are actually constructed.
- **Template mirroring is checksum-pinned.** Any edit under
  `factory/templates/**` or to a root file in `factory_init.MIRRORS`
  requires `python3 factory_init.py update-manifest`, committed with the
  change. A new module that ships in the payload must join `MIRRORS` and
  the manifest, or detector E fires.
- **Recorded decisions that touch this work, with status:** ADR-0037
  (accepted — the four seam modules and the list of what deliberately did
  not move), ADR-0042 (accepted — `gh_runner` and `read_event` joined the
  cli seam), ADR-0051 (accepted — the report epilogue joined the cli seam;
  caller-side label prefixing is intentional convention, not an oversight),
  ADR-0041 (accepted — gate-latency rows in the ledger, which is what
  created two classes of row), ADR-0053 (accepted — charter replay joined
  the harness seam), ADR-0054 (provisional — `factory.py`'s zero callers
  are the decided state). None is being reopened by this run.
- **Offer an ADR only** when a decision is hard to reverse, surprising
  without context, and the result of a real trade-off. The gate plane's
  existence probably qualifies; the others probably do not.
- Match the surrounding style. Many small files; 200-400 lines typical.

## Tracker

**No tracker interaction.** Work items carry no `(tracker: #N)` references,
no issues are created, and none are closed. The breakdown is the state.

## User-facing surface

None. This run touches internal tooling only, and maintenance runs skip the
PRD stage anyway, so no `ux:` decision arises.

## Release authorization

**Full release is authorized**, explicitly, by the operator on 2026-08-18,
in answer to a question that spelled out that this option overrides the
repo's usual rule that agent-authored merges wait for human approval.

"Production" for this repo is `main`: the plugin is vended from the repo
and the factory payload is stamped into product repos from
`factory/templates`. There is no deploy step and no version tag — the
project has never tagged a release. So shipping is: a branch, a PR against
main, a green battery, and a squash merge.

Two conditions bound that authorization and are not waivable by this run:

- The full battery must be green at the merge commit.
- Unfixed **critical** review findings block the merge unconditionally.
  Stop and surface instead.

## Interview answers the stages will need

- **Who suffers, and how do they cope today?** Whoever next edits one of
  these tools — in practice the operator and the dispatched agents. Coping
  today means reading a sibling tool to learn the ritual, and copying it.
- **Why now?** The factory is about to dispatch agents at these tools for
  the first time. An interface that costs five undocumented facts to use
  correctly is a worse thing to hand an agent than a human.
- **Evidence strength:** direct, not anecdotal. Every claim above is a file
  and line count from a confirmed review; the two live divergences
  (work_queue's duplicate literal, the 6-versus-7-tool shadow) are present
  in the tree at `fbfa3c3`.
- **Blast radius:** internal tooling and CI detectors. No user-facing
  surface, no data migration, no external contract. The risk concentrates
  in gates.py (the CI detector suite) and in the mirrored payload, where a
  stale manifest fails detector E.
- **How this dies:** the gate-plane item grows past its evidence and starts
  moving `_timelines` and the post/upsert epilogues too; or an interface
  move quietly changes a tool's output and the exact-string tests are
  edited to match instead of the change being reverted.
