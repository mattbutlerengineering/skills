---
stage: architect
run: maintenance:deepening-tool-seams
date: 2026-08-18
assumptions:
  - "prd.md absent — this is a maintenance run, whose predecessor is defect.md (ADR-0025's maintenance table), not a PRD. The autorun brief plus defect.md's walked evidence are the design source; no PRD requirement tracing applies"
  - "ux not applicable — the run touches seven tools, one CI detector and a new module; no user-facing surface, so no ux: decision arises"
  - "The gate module is named human_gates.py, not gate_plane.py — the brief names the concept ('a gate plane module') but never the file, and CONTEXT.md spends 'plane' on exactly two authorities (knowledge, dispatch). The three gates are decision points ON the dispatch plane, so the module takes the repo's own noun from ADR-0033"
  - "mirror_map's destination was not stated in the brief; it joins knowledge_plane.py (ADR-0039's home for the tracker-mirror grammar) rather than the new gate module, because it names no gate"
  - "Item 4 is taken at its narrow size: the row-selection rule folds; the three month-string spellings and the two _utcnow twins do not. The brief lists them 'in the same cluster', but its target state and success criteria name only the month-to-date definition, and the two smaller copies fail the seam bar's second half (no divergence observed) and the depth test"
---

# Architecture: one owner each, four times

## Approach

Four facts have more than one owner and the copies have begun to
disagree. Three of the four are moves into seams that already exist and
already own the neighbouring facts; only one asks for a module that is
not there yet. The design applies the precedent run's rule —
**share the rule, keep the meaning local** — to each of them, which is
what decides how much travels: the *rule* (how a windowed listing is
composed, how a gate stay is partitioned, which ledger rows count as
spend) gets exactly one owner, and the *meaning* (what absence means to
this caller, what a full window costs here, which label prefixes the
sentence) stays where it is written today.

The alternative shape, considered and lost, was to move whole operations
rather than rules: one `gh_listing` per tool folded into the seam, a gate
module that also owns the timeline fetch and the create-or-update
epilogue, a ledger reader that returns the month's dollars ready-made.
That shape is shorter to describe and worse to own: it drags the network
adapter into a pure module, gives one seam two subjects, and puts
per-caller policy behind a seam's signature — a configuration table
wearing a seam's clothes, which is the shape the 2026-08-13 review
already refused once. What is genuinely shared here is narrower than the
operations that contain it, and the design says so per item.

Nothing a tool prints changes, with one stated exception (detector J's
declaring site name — see *Decisions & alternatives*).

## Components

### `cli.gh_read` — the one windowed gh read

- Responsibility: the whole gh-read operation as one call — run gh,
  catch the binary's failure vocabulary, parse and shape-check the JSON,
  own the window (both the `--limit` it sends and the truncation it
  reports), and return the value beside already-prefixed problem
  strings. It owns the five facts a caller carries today, none of which
  is in a signature.
- Collaborators: `cli.gh_runner` (default port), `cli.CLI_FAILURES` and
  `cli.detail` (unchanged), and the fourteen call sites in eight
  modules.
- Change: `cli.gh_json` (cli.py:315) and `cli.full_window` (cli.py:337)
  are absorbed and deleted. Two shallow halves become one deep name;
  seven `LIST_WINDOW` declarations stop being coupled by hand to a
  `--limit` literal, and work_queue's duplicate window literal
  (work_queue.py:41-43) has nowhere left to live.

### `human_gates.py` — the three gates and one issue's gate history (new)

- Responsibility: what the three human gates ARE (ADR-0033's names, the
  `wo:` label each waits on, the label that confirms its pass, the digest
  heading) and how to read one issue's label history against them — the
  label-event walk, the completed-stay partition, and the current stay's
  start. Pure: no gh, no ledger, no filesystem, no clock.
- Collaborators: `gate_digest.py`, `rejection_mining.py`,
  `dashboard.py`, and `gates.py`'s detector J, all as thin callers.
- Change: `GATES` (gate_digest.py:50), `label_events` (:73),
  `gate_passages` (:89), `waiting_since` (:120) and the timestamp
  arithmetic (`_parse_ts`/`_seconds`, :63-70) move here from a leaf
  tool, joined by `gate_rejections` (rejection_mining.py:59). The two
  stay walks — gate_digest.py:99-110 and rejection_mining.py:69-80,
  with two spellings of the same window test — become one, and the
  invariant that today exists only as prose in a docstring
  (rejection_mining.py:62-66) becomes the return value both tools
  filter.

### `knowledge_plane.mirror_map` — the tracker mirror map moves home

- Responsibility: unchanged — `{tracker issue number: WO token}` from
  the breakdown rows (ADR-0032's one-way mirror).
- Collaborators: `gate_digest.py`, `rejection_mining.py`,
  `dashboard.py`.
- Change: moves from gate_digest.py:174 to knowledge_plane.py. It is
  built entirely from three knowledge-plane names
  (`breakdown_files`, `row_work_order`, `row_tracker_issue`) and names
  no gate; ADR-0039 already placed the tracker-mirror grammar there.
  This is what makes "no module reaches into a leaf tool" true rather
  than half true.

### `gate_digest.py`, `rejection_mining.py`, `dashboard.py` — thin callers

- Responsibility: unchanged. The digest composes and posts the daily
  digest and writes gate-latency rows; the miner harvests rejections and
  change-requests into the weekly queue issue; the dashboard renders.
- Change: each imports the gate vocabulary instead of declaring it or
  reaching for it, and each gh read becomes one `cli.gh_read` call.
  What stays theirs is listed under *What does not move* below.

### `gates.py` detector J — the declarer stops counting tuple fields

- Responsibility: unchanged — every label the factory's tools and
  Makefile name must exist in the taxonomy.
- Change: `LABEL_DECLARERS` (gates.py:774) keys `human_gates` instead of
  `gate_digest`, and its lambda calls `mod.gate_labels()` instead of
  slicing `gate[1:3]` (gates.py:777-778). The detector stops depending
  on field order, which is the fragility the positional tuple created.

### `cost_ledger.dispatched` — what counts as spend

- Responsibility: the one predicate composition over a ledger row that
  says whether it counts toward spend: a gate-latency observation never
  does (ADR-0041), and when a month is given only rows `in_month` places
  there do.
- Collaborators: `cost_report.aggregate`, `work_queue.month_to_date`.
- Change: `cost_report.aggregate`'s two `continue`s (cost_report.py:70,
  :72) become the thing it iterates; `work_queue.month_to_date`
  (work_queue.py:191) sums the same row set instead of every row. Each
  caller keeps its own arithmetic and its own cap comparison — `>=`
  (cost_report.py:100) and `>` (work_queue.py:150) answer different
  questions and are not touched.

### `tests/test_gates.py` — one `product_form`, and the missing lockstep

- Change: the module-level shadow (tests/test_gates.py:1626) is deleted
  so the line-18 import of the production transform is the only
  `product_form`, and `TestLockstep` gains the `toolsmith-mine` target
  it has never had (Makefile:68-69).

## Data model

No persisted shape changes. The cost ledger's line grammar, the
breakdown row grammar, the manifest's key grammar and every artifact's
frontmatter are untouched; `costs.jsonl` is still append-only and still
carries exactly ADR-0034's field set plus `at`.

Two in-memory shapes change, both read-only:

- **A gate row becomes named.** `GATES` stays a tuple of rows, but each
  row is a `Gate` namedtuple — `name`, `queue`, `passed`, `heading` —
  so positional unpacking at the three iteration sites keeps working
  unchanged while the detector reads a name. Same move, same reason, as
  `cost_report.GuardResult` (cost_report.py:49).
- **A gh read answers with a small named result.** `GhResult(value,
  problems, truncated)`; see the contract below.

A completed stay stays a plain `(start, end, confirmed)` tuple: both
consumers unpack it at one site each, and nothing reaches into it from a
distance, which is the only thing that earned `Gate` its names.

## Interfaces & contracts

### `cli.gh_read(args, operation, label=None, run=gh_runner, expect=list, window=None, full_note=None)`

- Input: `args` — the gh argument list WITHOUT `--limit`; `operation` —
  the caller's name for the call as it appears in a problem string
  (`"gh pr list"`, `"gh api timeline for #12"`), never derived from
  `args`; `label` — the caller's problem-string label (`"asm"`, `"gd"`,
  `"V"`), or None for a reader whose callers own the label; `expect` —
  the required top-level JSON shape; `window` — the listing window, or
  None for a read that is not windowed; `full_note` — this caller's
  sentence for a full window, when the shared one under-states what
  truncation costs here.
- Output: `GhResult(value, problems, truncated)`. `value` is the parsed
  JSON, or None when the read is unusable. `problems` are complete,
  already-prefixed problem strings in the repo's contract form. `window`
  is appended to `args` as `--limit <window>` by the seam, so the limit
  that was sent and the limit the truncation check tests are the same
  number by construction.
- Failure modes, all of them:
  - gh missing, unauthenticated, or rate-limited (`CLI_FAILURES`) —
    caught here: `value=None`, one problem `"<label>: <operation>
    failed: <detail>"`, `truncated=False`.
  - ran and answered unreadably — `value=None`, `"<label>: <operation>
    returned unparseable JSON: <err>"`.
  - ran and answered the wrong shape — `value=None`, `"<label>:
    <operation> returned <got> where <expect> was expected"`.
  - came back full (only when `window` is given) — `value` is the
    listing, `truncated=True`, one problem carrying `full_note` or the
    shared sentence. **The caller decides what that means**: seven
    report and continue, two refuse the value outright, one replaces
    the sentence. The seam states the fact; the meaning stays local.
  - With `label=None` the problems carry the operation prefix only, so a
    reader whose three callers each own a different label
    (`label_sync.live_labels`, used with `L: ` and with `sweeps: `)
    keeps working, byte for byte.
- Timeout and retry, stated because this crosses a process seam: there
  is no timeout — `cli.runner` sets none today and this run does not
  add one, so a hung gh hangs the tool and the workflow's job timeout is
  the only bound. Retry is safe (every call is a read) and is never done
  here: the scheduled callers re-run daily or weekly, and their upserts
  are idempotent by design.
- Depth: a caller states args, a name and a window. It no longer states
  a `--limit`, a catch, a shape check, a second window call, or a
  prefix.

The fourteen sites the contract must serve, all confirmed in defect.md
and re-read at `fbfa3c3`:

| Site | operation | window | on truncation |
|---|---|---|---|
| label_sync.py:109 | `gh label list` | 1000 | report (unlabelled) |
| validator.py:323 | `gh issue view N` | — | n/a (`expect=dict`) |
| assembler.py:259 | `gh pr list` | 1000 | report |
| dashboard.py:147 | `gh api timeline for #N` | — | n/a |
| dashboard.py:166 | `gh issue list` | 1000 | report |
| dashboard.py:240 | `gh pr list` | 1000 | report |
| gate_digest.py:198 | `gh api timeline for #N` | — | n/a |
| gate_digest.py:295 | `gh issue list` | 1000 | report |
| rejection_mining.py:174 | `gh api timeline for #N` | — | n/a |
| rejection_mining.py:193 | `gh pr list` | 1000 | report |
| rejection_mining.py:244 | `gh issue list` | 1000 | report |
| sweeps.py:337 | `gh issue list` | 500 | refuse |
| sweeps.py:465 | `gh issue list` | 500 | report, own note |
| work_queue.py:178 | `gh issue list` | 100 | refuse |

Ten windowed, four not — which is why the name is `gh_read` and not
`gh_listing`, and why `window` is optional rather than required.

**Which callers change shape, and the price.** Exactly one:
`label_sync.live_labels` (label_sync.py:99) stops raising
`CLI_FAILURES` and returns `(None, [suffix])` instead, because the catch
now lives in the seam. Its three callers — `label_sync.sync`
(label_sync.py:126), `sweeps.ensure_labels` (sweeps.py:403) and
`sweeps.label_drift` (sweeps.py:538) — each delete a `try/except` and
keep the `[f"<label>: {suffix}" for suffix in suffixes]` line they
already have. Every resulting problem string is byte-identical
(`"L: gh label list failed: …"`, `"sweeps: gh label list failed: …"`),
because the seam formats `"<operation> failed: <detail>"` with the same
`cli.detail` those callers use today. The price is three deleted
`except` blocks and one docstring that must stop promising a raise; no
test string moves, and no test in the tree asserts the raise
(`assertRaises` appears nowhere in test_label_sync.py or
test_sweeps.py). This is priced here rather than assumed away because it
is the one place where "the seam owns the catch" is visible in a
signature.

Every other caller keeps its shape: `dashboard._timeline`,
`gate_digest._timelines` and `rejection_mining._timelines` keep
appending to the `problems` list they are handed;
`sweeps.live_issues` and `work_queue.ready_issue_numbers` keep returning
`(None, problems)` and read `truncated` to decide it;
`sweeps.known_keys` keeps its own pinned sentence through `full_note`;
`gate_digest.run_daily` keeps its `{"changed": "false"}` early return;
`rejection_mining` keeps `{}` and `[]`.

### `human_gates` — the gate vocabulary

- `GATES` — the three gates in pipeline order as `Gate(name, queue,
  passed, heading)` rows. Input: none. Failure modes: none; it is data.
- `gate_labels()` — the set of every label the gates name (six labels,
  five distinct). Detector J's one reach, replacing `gate[1:3]`.
- `label_events(timeline)` — `[(ts, 'labeled'|'unlabeled', name)]` in
  timeline order from a GitHub issue timeline. Anything that is not a
  well-formed label flip contributes nothing; an unusable timeline is
  the fetcher's problem, never this walk's.
- `completed_stays(events, gate)` — `[(start, end, confirmed)]` for one
  gate: every stay that was entered and left, with `confirmed` true when
  the gate's pass label was applied within that stay's window (from its
  start up to the gate's next re-entry). **This is the invariant made
  executable**: a completed stay is confirmed or not, so the digest and
  the miner partition the same list between them instead of agreeing by
  two hand-written window tests. An open stay is absent from the list —
  still waiting, neither passage nor rejection.
- `gate_passages(events)` — `[(gate name, waited seconds, passed at)]`;
  the confirmed stays, unchanged in shape and order.
- `gate_rejections(events)` — `[(gate name, stay ended at)]` sorted by
  end; the unconfirmed stays, unchanged in shape and order.
- `waiting_since(events, queue_label)` — the current stay's start, or
  None when the label is not applied now (or its `labeled` event fell
  off the fetched timeline).
- `waited_seconds(start, end)` — seconds between two GitHub timestamps,
  carrying the documented `Z`-compat quirk (`fromisoformat` accepts `Z`
  only from 3.11). Used by `gate_passages` and by
  `gate_digest._queues`, which today calls `_seconds` for the same
  reason.
- Failure modes across the module: none raise. Malformed events are
  skipped, an empty history yields empty lists. The module is pure, so
  every one of these is testable with a literal list of events and no
  network — which is why it is the module and the fetch is not.

**What does not move, and why** (the way this item dies is by growing
past its evidence):

- `_timelines` (gate_digest.py:189, rejection_mining.py:165) and
  `dashboard._timeline` (dashboard.py:141) — they are gh reads, and item
  1 already gives them an owner. After `gh_read` each is about six
  lines whose only remaining difference is its label and its local
  meaning ("a failed fetch is a problem, never a lost queue item" vs
  "never a silently thinner harvest"). Moving them into the gate module
  would put a network adapter inside a pure module and couple two seams
  to save nothing.
- `_post_digest` (gate_digest.py:253) and `_post_queue`
  (rejection_mining.py:206) — tracker mutations with per-tool titles,
  markers and pin semantics. defect.md confirmed no divergence between
  them; they already cite one another as one contract. Folding them is a
  separate candidate that needs its own evidence and a home that is not
  the gate vocabulary.
- `compose_digest` / `compose_queue`, `_capture_latency`, the ledger
  writes, the `DIGEST_MARKER` / `MARKER` idioms — per-tool text and
  cost-ledger business.
- `dashboard._age_seconds` (dashboard.py:130) — takes a live `datetime`
  for `now` rather than two ISO strings, is the dashboard's rendering
  concern, and was not confirmed as a divergence. Left visible.

### `knowledge_plane.mirror_map(root)`

- Input: the repo root. Output: `{tracker issue number: WO token}` from
  every breakdown row that carries both. Failure modes: unchanged — a
  row with no `(tracker: #N)` is simply not in any queue, and an issue
  with no row is not a work order (ADR-0032). Callers: the digest, the
  miner, the dashboard.

### `cost_ledger.dispatched(entries, month=None)`

- Input: validated ledger entries (the read contract at
  cost_ledger.py:226 already establishes their shape) and an optional
  `"YYYY-MM"` month.
- Output: the rows that count as spend — never a gate-latency row
  (`gate_wait` is not None), and when `month` is given only rows
  `in_month` admits.
- Failure modes: none; a pure filter over already-validated rows, in the
  same family as `in_month`, `gate_wait`, `row_key` and `wo_token` —
  the semantic rules over a row that cost_ledger.read's docstring
  already names as the seam's.
- Callers: `cost_report.aggregate` walks it (its month total is then
  the same row set as its token and run counts, by construction rather
  than by two matching `continue`s); `work_queue.month_to_date` sums
  `entry["cost"]` over it and keeps its `(dollars, problems)` shape.

**Honesty about this one.** The two definitions cannot disagree through
any production path today: `cost_ledger.gate_entry` (cost_ledger.py:64)
writes `0` tokens and `0.0` cost by construction, so every gate row is
free and both sums return the same number. This is prevention, not
repair, and the artifact says so. It is still worth taking, at exactly
this size, for a reason stronger than symmetry: ADR-0041 *decided* the
rule — "cost_report.aggregate keeps gate rows out of its run counts and
spend breakdown" — and work_queue's sum does not implement it. One
conforming implementation and one non-conforming one is a decided rule
with a hole in it, and the hole is in the input to the monthly circuit
breaker. The fold is six lines at a seam that already owns both
predicates, with no new module and no new mirror. What is deliberately
NOT taken with it: the three month-string spellings (cost_report.py:185,
work_queue.py:194, dashboard.py:452) and the byte-identical `_utcnow`
twins (cost_report.py:174, work_queue.py:50) — no divergence was
observed in either, and a one-line stdlib call behind an imported name
fails the depth test, costing about as much interface as
implementation. Also recorded and not taken: `dashboard._spend`
(dashboard.py:269) sums every row per work order, gate rows included —
correct today for the same $0 reason, a lifetime-by-work-order figure
rather than a month-to-date one, and not confirmed by defect.md.

## Stack & dependencies

- Python 3 standard library only — unchanged. Nothing here adds a
  dependency, and `human_gates.py` imports nothing outside `datetime`
  and `collections`.
- One new root module, `human_gates.py`, which joins
  `factory_init.MIRRORS` as an identity entry. Justified against
  CLAUDE.md's two-part bar **by name**: multiple real callers —
  gate_digest.py, rejection_mining.py, dashboard.py and gates.py's
  detector J, four modules that reach into a leaf tool today (three by
  import at dashboard.py:52 and rejection_mining.py:40, one by
  positional slice at gates.py:777) — AND observed divergence between
  the copies: the stay walk is written twice with two spellings of the
  same window test (gate_digest.py:114-115 vs
  rejection_mining.py:85-87). Two adapters that are actually
  constructed, not anticipated reuse.
- `cli.gh_read` and `cost_ledger.dispatched` add no module: both land in
  seams that already own the neighbouring facts (ADR-0037, ADR-0042,
  ADR-0051 for cli; ADR-0034, ADR-0041, ADR-0049 for the ledger), so the
  new-module bar does not apply to them and is not claimed.
- The problem-string contract is untouched: every checker still returns
  label-prefixed strings, callers still print and exit nonzero, and
  ADR-0037's rejection of a structured-findings layer is not reopened —
  `GhResult` is one function's return value, never a finding type, and
  its `problems` field carries the same strings the same tests assert.

## Mirroring consequences

The single most likely way this run breaks CI, so it is stated per item.
`factory_init.MIRRORS` (factory_init.py:127) is the authority on what
ships; `python3 factory_init.py update-manifest` must run and its
manifest be committed with the change, or detector E fires.

- **Item 1 (gh_read).** Touches `cli.py`, `label_sync.py`,
  `validator.py`, `assembler.py`, `gate_digest.py`,
  `rejection_mining.py`, `work_queue.py` — all seven are MIRRORS
  entries, so all seven payload twins change. `dashboard.py` and
  `sweeps.py` are factory-repo-only and mirror nothing. No new MIRRORS
  row. Manifest regeneration required.
- **Item 2 (human_gates).** A new payload file. `human_gates.py` joins
  MIRRORS as `("human_gates.py", "tools/factory/human_gates.py",
  identity)` — required, not optional: gate_digest.py and
  rejection_mining.py both ship and both import it as a bare sibling, so
  a stamped repo without it is a broken stamp. Consequences that travel
  with that row:
  - the MIRRORS comment block (factory_init.py:109-126) gains a
    sentence naming why the module ships, matching how the four ADR-0037
    seams are introduced there;
  - `EXPECTED_RELS` in tests/test_factory_init.py:34 gains
    `"templates/tools/factory/human_gates.py"` — a hand-maintained set
    that `test_happy_path_writes_manifest_and_syncs` asserts equal;
  - docs/setup.md:52's stamped-file table says `tools/factory/` lands
    16 files; it becomes 17, and the two totals in the sentence above
    the table move with it;
  - `gates.py` gains no import (detector J imports lazily by module
    name), but the module must be importable from a stamped repo's
    `tools/factory/`, which the MIRRORS row is exactly what guarantees.
  - It does NOT join `factory_init._PRODUCT_TOOLS` (factory_init.py:54):
    that tuple respells Makefile *commands*, and no target invokes this
    module.
  - `knowledge_plane.py` is already a MIRRORS entry, so `mirror_map`'s
    move changes a payload twin but adds no row.
- **Item 3 (test shadow).** `tests/` is not mirrored. Zero mirroring
  consequence — the only item with none.
- **Item 4 (dispatched).** `cost_ledger.py`, `cost_report.py` and
  `work_queue.py` are all MIRRORS entries; three payload twins change,
  no new row.

One `update-manifest` run at the end of the change covers all of it;
detector E gates manifest-vs-payload and `tests/test_factory_init.py`
pins payload-vs-root.

## Tests: what lands first, what dies last

The ordering rule this run follows: new tests at the intended interface
are written FIRST, against today's code; the deepening happens with
those tests as the net; the superseded shallow-module tests die LAST, in
the same change, with the diff saying which coverage moved where.

- **Item 1.** First, against today's code: a `TestGhRead` suite in
  tests/test_cli.py covering the five failure modes above, `label=None`
  leaving problems unprefixed, `window` reaching gh as `--limit` (assert
  the exact argv the fake runner receives), `truncated` on a full
  window, and `full_note` replacing the shared sentence. It cannot pass
  before the seam exists, so it lands red on the same commit that lands
  `gh_read` — the net, written to the interface, not to the
  implementation. The existing per-caller suites (test_label_sync,
  test_sweeps, test_work_queue, test_gate_digest,
  test_rejection_mining, test_assembler, test_dashboard,
  test_validator) already assert the exact strings and must pass
  UNCHANGED across the move; that is the regression net for "no
  observable output changed", and any edit to one of them is the signal
  to revert rather than to adjust. Dying last, in the same change:
  `TestGhJson` (tests/test_cli.py:129) and `TestFullWindow` (:156) —
  their coverage moves into `TestGhRead`, whose unparseable/wrong-shape/
  full-window cases assert the same sentences one frame further out.
- **Item 2.** First: `tests/test_human_gates.py`, written against
  today's code by importing the functions from `gate_digest` and
  `rejection_mining` where they still live — the passage cases
  (test_gate_digest.py:95-143), the rejection cases
  (test_rejection_mining.py:104-135), `label_events`
  (test_gate_digest.py:81) and `waiting_since` (:144), plus the case
  neither suite has: **the partition property** — for one event history,
  passages and rejections together are exactly the completed stays, and
  no stay is in both. That test is the invariant defect.md found living
  in a docstring, and it passes before the move (the two spellings agree
  today) and after it (there is one spelling), which is precisely what
  makes it a net rather than a re-statement. Then the move, with the
  import lines re-pointed. Dying last: the duplicated classes in
  test_gate_digest.py and test_rejection_mining.py whose subject is now
  the shared module; each of those suites keeps its own tool-level tests
  (run_daily, run_mine, posting, dedup) untouched. Also updated in the
  same change, deliberately: the two detector-J assertions naming
  `gate_digest.py` as the declaring site (tests/test_gates.py:699,
  :769) become `human_gates.py`.
- **Item 3.** First, and this one lands genuinely RED: add
  `TOOLSMITH_MINE_TARGET = ["python3 rejection_mining.py mine"]` and the
  three `toolsmith-mine` methods to `TestLockstep`, shaped exactly like
  the gate-digest trio (both Makefiles expose the target; the workflow
  names no command of its own; the payload workflow is a byte mirror).
  Against today's code the Makefile assertion FAILS, because the shadow
  (tests/test_gates.py:1626) respells six tools and omits
  `rejection_mining.py` while the payload Makefile carries
  `python3 tools/factory/rejection_mining.py mine`. Then delete the
  shadow: the line-18 import of `factory_init.product_form` becomes the
  only `product_form`, the seven-tool production transform respells the
  command, and the test goes green. That red-to-green is the evidence
  the shadow was a live defect and not a tidiness complaint. Nothing
  dies here beyond the shadow itself — the other five call sites
  (:1706, :1714, :1802, :1824, :1845, :1865) resolve to the import with
  no change in outcome, because none of their constants names
  `rejection_mining.py`. The contradicted docstring
  (tests/test_gates.py:1649-1652) becomes true.
- **Item 4.** First: a `dispatched` suite in tests/test_cost_ledger.py,
  and — the case the success criteria name and neither suite has today
  — **a nonzero-cost gate row**, hand-written into a fixture ledger
  (`gate_entry` cannot produce one; that is the whole reason the
  divergence is invisible). Written against today's code it pins the
  disagreement: `cost_report`'s month total excludes the row,
  `work_queue.month_to_date`'s includes it. Then the fold makes the two
  agree, and the same test asserts the agreement. Dying last: nothing —
  no existing test asserts work_queue's gate-row-inclusive sum, which is
  exactly why the divergence survived (`gate_wait` appears zero times in
  test_cost_report.py and zero times in test_work_queue.py).

## Decisions & alternatives

- **One `gh_read` covering all fourteen sites** over a `gh_listing`
  covering only the ten windowed ones — a listings-only entry point
  leaves `gh_json` alive for the other four, and a shallow half that
  survives is the ritual surviving.
- **`GhResult(value, problems, truncated)`** over `(value, problems)`
  with the refusing callers inferring truncation from "a problem on a
  usable listing" — the inference is correct today and silently wrong
  the first time the seam adds a second advisory problem.
- **`full_note` as one optional suffix** over three-valued policy
  parameter (`report` / `refuse` / `caller`) — the policy parameter puts
  per-caller meaning behind the seam's signature, which is what the
  2026-08-13 review refused; a note is a verb phrase in the same grammar
  as every other suffix, and the refusal stays at the two call sites
  that own it.
- **`operation` passed in** over derived from `args` — `"gh api
  timeline for #12"` is not derivable, and deriving the rest would
  change strings the exact-string tests pin.
- **The seam appends `--limit`** over the caller passing it — this is
  the move that kills work_queue's duplicate literal and the
  three-times-copied drift comment; the limit sent and the limit checked
  become the same number by construction. All ten sites already put
  `--limit` last, so the argv gh receives is byte-identical.
- **Per-tool window values stay per-tool** (1000 / 500 / 100, declared
  once per module and passed as `window=`) over one shared constant —
  they are genuine policy differences with documented reasons
  (sweeps.py:111-117 explains 500; work_queue's 100 is a ready-label
  listing), and a shared constant would be a fourth owner of a fact that
  is correctly local.
- **`human_gates.py`** over `gate_plane.py` — CONTEXT.md spends "plane"
  on exactly two authorities, and the gates are decision points on one
  of them, not a third.
- **`mirror_map` joins knowledge_plane** over joining `human_gates` with
  the rest — a module that also owns the mirror map has two subjects,
  and the next reviewer cannot say in one sentence what it is.
- **`Gate` as a namedtuple** over a dict or a small class —
  `cost_report.GuardResult` set the precedent for exactly this problem
  (positional unpacking keeps working at the three iteration sites; the
  detector names the field it wants), and a dict would break all three.
- **Detector J calls `gate_labels()`** over reading `gate.queue` and
  `gate.passed` itself — the detector should not know how many label
  fields a gate row has, which is the same coupling it has today spelled
  more politely.
- **The partition returns `(start, end, confirmed)`** over two functions
  (`confirmed_stays` / `rejected_stays`) — two functions is two walks
  and re-opens the possibility of two window tests, which is the defect.
- **Item 4 at its narrow size** over folding the month string and
  `_utcnow` too — recorded above with the reason; the operator
  explicitly allowed a narrower item 4 and this design takes exactly the
  part that disagrees.
- **One deliberate output change, stated:** detector J's problem string
  and `declared_labels`' site key name the module that declares the
  label, so after the move a pruned gate label reports `"J:
  human_gates.py names wo:merged …"` instead of `"J: gate_digest.py
  names wo:merged …"`. That string fires only against a broken taxonomy
  (no shipped run emits it), and the new name is the true one. Two
  assertions in tests/test_gates.py move with it. Every other observable
  string in the tree is byte-identical, and an exact-string test that
  needs editing anywhere else is the signal to revert the move, not to
  edit the test.

## ADRs

One, and only for item 2: [ADR-0056](../../adr/0056-human-gates-module.md)
— the three human gates get a module of their own. It meets all three
bars: hard to reverse (a new mirrored module lands in every stamped
product repo, and unwinding it is a re-stamp), surprising without
context (a reader will ask why the gate vocabulary does not live in the
tool that writes the digest, and why a `human_gates` module sits beside
`gates.py`), and the result of a real trade-off (the alternative —
leave `GATES` in the leaf tool and let three modules and a detector
reach in — is what the tree does today, and the module costs a payload
file in every stamped repo). It is recorded **provisional**, matching
ADR-0054's precedent from the sibling run: a recommended answer adopted
in flight, awaiting the operator's confirmation at merge.

The other three warrant none, and the one-line records above are enough:

- **Item 1** adds a name to a seam whose charter already covers it —
  ADR-0037 established the cli seam, ADR-0040, ADR-0042 and ADR-0051
  each added to it, and the last of those already settled the
  label-prefixing convention this uses. Reversible by inlining, and
  surprising to nobody who reads those four.
- **Item 3** deletes a test-private copy of a production transform. No
  trade-off exists; the docstring at tests/test_gates.py:1649-1652
  already asserts the decision.
- **Item 4** implements a rule ADR-0041 already decided, in the seam
  ADR-0049 already extended. Recording it again would be recording it
  twice.
