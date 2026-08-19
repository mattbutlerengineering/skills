---
stage: review
run: maintenance:deepening-tool-seams
date: 2026-08-18
assumptions:
  - "No live user input — this run is driven from autorun-brief.md, so every severity call and every fix/defer decision below is mine, taken against CLAUDE.md, CONTEXT.md and the run's own artifacts rather than the operator's judgment. A severity the operator disagrees with is a line to correct, not a design change"
  - "Review depth is scaled to the blast radius defect.md records. It calls this small-to-medium but concentrates the risk in gates.py (the CI detector suite) and the mirrored payload, so those two got a full-depth pass — detector J driven at both revisions in this repo and in a freshly stamped one, the payload stamped and its tools imported and run — while the run's own documents got a lighter one"
  - "Nothing was driven against real GitHub, the same bound Verify recorded. Every gh call below went through an injected fake runner or a stamped fixture repo; no credential was read and no network call was made"
---

# Review: one owner each, four times

## Scope

`git diff main...HEAD` on `deepening-tool-seams` — 17 commits (`4a287ff`
through `3aca0f6`), 44 files, +3,756 / −915. Not the whole repo.

What that covers, by subject:

- **The seam** — `cli.gh_read` and `GhResult` replacing `cli.gh_json` +
  `cli.full_window`, and the fourteen call sites in eight modules that
  re-composed them by hand.
- **The new module** — `human_gates.py` (ADR-0056, provisional), its
  four callers, and `knowledge_plane.mirror_map`'s move.
- **The CI detector** — `gates.LABEL_DECLARERS` / detector J, and the
  expectation inside `gates.selftest()`.
- **The ledger** — `cost_ledger.dispatched` and its two callers.
- **The test shadow** — the deleted `product_form` copy and the new
  `toolsmith-mine` lockstep methods.
- **The payload** — 25 `MIRRORS` entries, the manifest, `docs/setup.md`'s
  counts.
- **The artifacts** — `defect.md`, `architecture.md`, `breakdown.md`,
  `verification.md`, ADR-0056.

**What I re-derived rather than read.** Verify's central claim is that
nothing observable moved, so I re-ran main's eight per-caller suites
against HEAD's production code in a `git archive` export — **419 tests,
OK** — which is the exact-string contract read as a regression net,
independent of Verify's own run. I also stamped a product repo into a
scratch tree and drove it: `gates.py` green, `gates.py --selftest` green,
`declared_labels` naming `human_gates.py` for all five gate labels, every
mirrored tool imported. I re-ran the full battery at `3aca0f6` (1,271
tests OK; `lint: 0 problem(s)`; `gates: 0 problem(s)`; `selftest: ok`) and
re-ran `factory_init.py update-manifest` on a clean tree to confirm it is
a no-op.

## Findings

**Zero critical.** Nothing here blocks the merge under the brief's
release authorization.

### Major: `human_gates.py` is absent from CLAUDE.md's shared-module list

- Scenario: the decayed contract is CLAUDE.md's own. Its **Hard
  conventions** bullet reads "**Seam modules, everything else thin
  callers**: `protocol.py` …, `eval_schema.py` …, and the four factory
  seams … `knowledge_plane.py` …, `cli.py` …, `factory_config.py` …,
  `cost_ledger.py` …. A new shared module needs multiple real callers AND
  observed divergence between their copies." `human_gates.py` is a new
  shared root module that meets that bar by name — four real callers
  (`gate_digest.py`, `rejection_mining.py`, `dashboard.py`, detector J)
  and an observed divergence (two spellings of the stay window test) —
  and it ships in the payload, yet it is not in the enumeration that sits
  directly above the rule it satisfies. The precedent is explicit:
  commit `4856311` ("refactor(factory): ADR-0037 seam modules") added
  `knowledge_plane.py`, `cli.py`, `factory_config.py` and
  `cost_ledger.py` and edited that same CLAUDE.md sentence in the same
  commit. This run covered three of the four documentation surfaces a new
  mirrored module owes — the `MIRRORS` comment block, `docs/setup.md`'s
  counts, `docs/adr/README.md`'s index row — and missed the fourth.
  The concrete recurrence: a dispatched agent asked to add a fifth
  gate-aware tool reads CLAUDE.md to learn where shared facts live, does
  not find `human_gates.py`, and copies the stay walk out of
  `gate_digest.py`. That is verbatim the failure ADR-0056's last
  Consequence names as the reason the module exists ("A fourth tool that
  needs to know what a gate is imports one module instead of copying a
  stay walk out of the digest — which is how the divergence this ADR
  closes was created in the first place"), and it directly undercuts the
  run's own stated *why now* ("The factory is about to dispatch agents at
  these tools for the first time").
- Not out of scope: the brief's exclusion list names `skills/**`,
  `evals/**` and the pipeline protocol. CLAUDE.md is on none of them, and
  the run already accepted the documentation-consequence obligation
  elsewhere.
- Decision: **fix** — one sentence in CLAUDE.md's seam-module bullet
  naming `human_gates.py` (ADR-0056) as the gate vocabulary and stay
  partition. Prose only; no code, no test, no manifest churn.

### Minor: `TestThePartition`'s docstring asserts the opposite of what its own class does

- Scenario: `tests/test_human_gates.py:243-247` still carries B1's
  pre-move text — "Nothing executes this today — it is a sentence in a
  docstring, and the window test it describes is spelled two ways." Both
  clauses are false at HEAD. This class *is* what executes the invariant,
  and there is exactly one spelling of the window test, which the run's
  own S1 grep proves (`git grep -n "c >= start"` → none;
  `start <= ts` → `human_gates.py:112` and its twin). B3 rewrote the
  module docstring to past tense and left the class docstring behind; B5,
  which deleted the second spelling, did not revisit it. A reader at HEAD
  is told to go find a second spelling that does not exist, and told the
  invariant is unpinned by the very class that pins it.
- Why this is a finding and not prose taste: item 3 of *this run* treated
  "the docstring asserts the opposite of what the code does" as a live
  defect worth its own milestone (`factory_init.py:63-64` and
  `tests/test_gates.py:1649-1652`), and closed it. This is the same class
  of defect, one band down because it is a test-class docstring rather
  than a production contract — but the standard is the run's own.
- Decision: **fix** — rewrite the three-line class docstring to the state
  it now describes. No assertion changes.

### Minor: architecture.md and breakdown.md claim `human_gates` raises nowhere; it can

- Scenario: `architecture.md` states "Failure modes across the module:
  none raise", and B3's Accept line requires the module be "raising
  nowhere". Verify checked it as `raise sites: 0` — a grep for the
  keyword, which cannot see an exception that propagates rather than
  being raised. `human_gates.waited_seconds` → `_parse_ts` →
  `datetime.fromisoformat` raises `ValueError` on a timestamp that is
  truthy but not ISO-8601, and `label_events` admits exactly such an
  event (it tests `name and ts` for truthiness, nothing more). Driven:
  a timeline whose completed stay ends at `created_at: "yesterday"`
  gives `label_events` three clean events and then
  `gate_passages(events)` → `ValueError: Invalid isoformat string:
  'yesterday'`. `gate_digest.run_daily` catches only `CLI_FAILURES`
  (`CalledProcessError`, `OSError`), so the daily digest workflow would
  die on a traceback rather than a problem string — the outcome the
  original `gh_json` docstring said the seam existed to prevent.
- **The hazard is not this run's.** I drove the same input against main's
  `gate_digest.gate_passages` and got the identical `ValueError`: the
  behavior was relocated byte-for-byte, not introduced, and Verify's
  "observable output unchanged" claim survives intact. What this run
  introduced is the *contract statement* — a new, false "none raise"
  claim about code it authored, in two artifacts. ADR-0056 and the
  shipped module docstring make no such claim, which is why the blast
  radius stops at the artifacts.
- Decision: **fix the claim, defer the hazard.** Soften
  `architecture.md`'s failure-modes line and B3's Accept clause to what
  is true — pure, no I/O, malformed *events* skipped; a malformed
  timestamp on a completed stay propagates a `ValueError`. Hardening
  `_parse_ts` is a behavior change to a shipped tool with no evidence
  behind it and belongs in a `docs/backlog.md` seed, not in a run whose
  brief names "an interface move quietly changes a tool's output" as how
  it dies.

### Minor: B4's Accept line undercounts its sanctioned string edits by one

- Scenario: the decayed contract is `breakdown.md`'s own. B4's Accept
  line names "the two assertions at tests/test_gates.py:699 and :769" as
  "the only exact-string edits sanctioned anywhere in this run". A third
  moved — `gates.py:1270`, the expectation inside `gates.selftest()`. The
  row's enumeration and its count are both incomplete, and the run's stop
  rule ("An exact-string test that needs editing anywhere else is the
  signal to revert the move, not to edit the test") reads, taken
  literally, as tripped.
- Adjudication is in *Verify's two observations* below. Short form:
  neither the change nor the row's intent is wrong; the row's
  enumeration is.
- Decision: **defer** — the correction is already on the record twice, in
  `6ec22a5`'s own commit message ("Three sites move with it and no
  others") and in `verification.md`'s Failures section. Rewriting a
  closed Accept line after the fact edits the run's history rather than
  recording it. If the operator wants the row itself to carry the
  correction, this run's own idiom is a `## Notes` entry in
  `breakdown.md` — it already carries one for A6's `--limit` reword —
  not an Accept-line edit.

## Verify's two observations, adjudicated

### B4's off-by-one — *neither the artifact's intent nor the change is wrong; the enumeration is*

The change is right and was forced. `gates.py:1270` is not a second
output change; it is the expectation *of the very string* B4 renames,
inside `gates.selftest()`. Leaving it would have made
`python3 gates.py --selftest` red — in this repo and, because `gates.py`
is `MIRRORS` entry one and the payload `Makefile`'s `check` target runs
`python3 tools/factory/gates.py --selftest`, in every stamped product
repo. Reverting instead, as the literal stop rule would have it, would
have reverted the sanctioned change to satisfy an expectation of the
sanctioned change. That is the rule being under-specified, not violated:
it was written to catch *a second output change hiding behind the first*,
and this is the first one's own mirror.

The artifact is wrong in one narrow way and it is worth naming precisely:
the Accept line fixes both a **count** ("two") and a **location set**
("in `tests/test_gates.py`"), and the true answer is three across two
files, one of which is a shipped production module. A reader auditing the
diff against that row finds a third edit the row says should not exist,
and the row gives them no way to tell a forced mirror from a violation.
Recorded as a minor finding above, deferred, because the accurate account
already exists in two places.

### The copied comments — *an aesthetic preference, not a finding, by the repo's own standard*

Five modules (`assembler.py:56-58`, `dashboard.py:67-69`,
`gate_digest.py:87-89`, `label_sync.py:92-94`,
`rejection_mining.py:51-53`) now carry a near-byte-identical three-line
comment above `LIST_WINDOW`, `work_queue.py:42-45` a four-line variant of
it, and `sweeps.py:115-116` still its own. Verify is right that the shape of
these six files is unchanged. It is still not a finding, for three
reasons, all from the repo:

1. **The old comment was load-bearing; the new one is not.** The old
   text warned of a real trap — a hand-typed `--limit` that had to keep
   agreeing with `LIST_WINDOW`, and `work_queue.py` had already fallen
   into it. `cli.gh_read` now sends the limit, so there is no longer a
   trap for the warning to guard. The five copies are descriptive prose
   about where a rule moved. They can go stale; they cannot disagree in
   a way that changes behavior, and nothing downstream reads them.
2. **CLAUDE.md's duplication bar governs modules, not sentences.** The
   bar is "multiple real callers AND observed divergence between their
   copies", and its subject is a shared module — code with an owner. No
   divergence between these five copies was observed, so the bar's own
   second half is unmet. Consolidating them would be the anticipated
   reuse the same sentence rejects.
3. **The codebase holds the copied-prose habit itself.** On main,
   `assembler.py:57-59` carried the shared two lines plus an attribution
   (`(rejection_mining's discipline)`) and `dashboard.py:68-69`
   paraphrased them and cited `gate_digest`; `sweeps.py` carries its own
   variant at HEAD, untouched. A finding here would be a style preference
   the codebase does not hold, which this stage's rules forbid.

What survives is a true observation with no owner in this run: five
comments that go stale together the day `gh_read`'s window semantics
change. That belongs where its neighbour already sits — `docs/backlog.md`
carries the unclaimed seed "A drift detector for retyped seam grammar"
from `maintenance:deepening-cli-seams`, which is the same idea one level
up. Route it there, not into this diff.

## The four checks the run's shape demanded

### `.get("cost") or 0` → `entry["cost"]` in `work_queue.month_to_date` — refuted, no KeyError path

The implementer's justification holds against `cost_ledger.read` itself.
`read()` (cost_ledger.py:244) appends a record to `entries` only when
`not located` — i.e. only when `line_problems(record)` returned nothing —
and `line_problems` (cost_ledger.py:147) reports a missing `cost` in its
`missing` check and a non-numeric, boolean or negative one in its `cost`
branch. Every entry `read()` yields therefore carries `cost` as a
non-bool `int|float >= 0`. `month_to_date` reads its entries from
`cost_ledger.read(root)` and nowhere else, and `dispatched` is a pure
filter that removes rows rather than adding them.

Driven adversarially, with a seven-line ledger carrying a missing `cost`,
a string `cost`, a negative `cost`, an unparseable line, a JSON array, a
costly gate row and one good row:

```
admitted entries: ['r4', 'r5']      (the gate row and the good row)
problems: 5
month_to_date -> 7.5 | problems: 5
cost_report month total -> 7.5
```

No exception; the five malformed rows are excluded and reported, both
month figures agree, and the $2.50 gate row is out of both. `dispatched`'s
other two callers (`cost_report.aggregate` via `cost_report.guard` and
`dashboard._costs`) also take their entries from `cost_ledger.read`.
Not a finding.

### `human_gates` shipping into the payload — works, but B3's cited test is not what proves it

**The claim holds.** I stamped a fresh product repo and drove it:
`tools/factory/` lands 17 files including `human_gates.py`; `import
human_gates` and `import gate_digest` both succeed from the payload
directory; `python3 tools/factory/gates.py` prints `gates: 0 problem(s)`;
`declared_labels` names `human_gates.py` for all five gate labels.

**The cited test is not the reason.** `declared_labels`
(gates.py:797-801) wraps its `importlib.import_module(name)` in
`except ImportError: continue` — deliberately, and the comment says why —
so detector J degrades *silently* when a declarer will not import.
`test_stamped_repo_passes_its_own_gates` runs plain
`tools/factory/gates.py`, which is exactly the path that swallows the
import, so it would pass with `human_gates.py` absent from the payload
entirely. B3's Accept line cites it as evidence of a working stamp; it is
evidence of a stamp that does not *fail*, which is weaker.

What actually closes it is better than the citation. The payload
`Makefile`'s `check` target (factory/templates/Makefile:27-30) runs
`python3 tools/factory/gates.py --selftest`, and `selftest()` asserts the
**positive** string `"human_gates.py names wo:merged"` (gates.py:1270).
A silent import failure in a product repo turns that red, in that repo's
own CI. Driven in the stamped tree: `selftest: ok`, exit 0. Presence in
the payload is separately pinned three ways — the `MIRRORS` row,
`EXPECTED_RELS` in `tests/test_factory_init.py`, and detector E's
checksum — and because the entry is `identity`, root and payload cannot
diverge. Not a finding; recorded because a future reader should not lean
on the test B3 names.

### Detector J's rename — still detects

The rename is name-for-name, not behavior-for-name. `gate_labels()`
returns exactly what `{name for gate in mod.GATES for name in gate[1:3]}`
returned — verified by evaluating both against `human_gates.GATES`:

```
gate_labels:      ['wo:blueprint-approved','wo:draft','wo:merged','wo:needs-review','wo:prd-approved']
main slice equiv: ['wo:blueprint-approved','wo:draft','wo:merged','wo:needs-review','wo:prd-approved']
```

A genuinely broken taxonomy still fires it, and I checked that in three
places rather than one: `gates.selftest()` prunes `wo:merged` from an
otherwise correct taxonomy and expects two problems, and it passes at
HEAD in this repo and in a stamped one; `tests/test_gates.py:690-700`
prunes the same label and asserts both declaring sites; and in the
stamped repo `declared_labels` returns thirteen labels with
`human_gates.py` against the five gate labels and `Makefile:NN` against
the lifecycle ones. Verify's enumeration of all eleven pruned labels at
both revisions — twelve problems each, in the same order, five site names
changed and nothing else — is consistent with all three. The detector
also got strictly less fragile: it no longer knows how many label fields
a gate row has. Not a finding.

### `label_sync.live_labels`' shape change — no caller proceeds with `None`

Three callers, all confirmed by reading them at HEAD:

| Caller | Guard | Behavior on a failed gh |
|---|---|---|
| `label_sync.sync` (label_sync.py:124-127) | `if current is None: return problems` | returns `["L: gh label list failed: <detail>"]` |
| `sweeps.ensure_labels` (sweeps.py:395-398) | `if listing is None: return problems` | returns `["sweeps: gh label list failed: <detail>"]` |
| `sweeps.label_drift` (sweeps.py:523-526) | `if current is None: return [], problems` | returns `([], ["sweeps: gh label list failed: <detail>"])` |

Each deleted an `except GH_FAILURES` that returned one problem and now
reaches a `None` guard that returns the same one problem, built from the
same `cli.detail` through the seam's `"<operation> failed: <detail>"`
format. The strings are byte-identical, which main's `tests/test_label_sync.py`
and `tests/test_sweeps.py` confirm unchanged against HEAD's production
code in the 419-test cross-run. `git grep live_labels` finds no fourth
caller. Not a finding.

## The three passes

### Correctness — no findings

- **Every one of the fourteen `gh_read` sites** was read against its main
  counterpart for the five outcomes (`CLI_FAILURES`, unparseable,
  wrong shape, full window, clean) on three axes: the problem string, the
  returned value, and whether the caller continues or refuses. All
  fourteen match. The three shapes the design promised to serve are
  intact — seven report and continue, `work_queue.ready_issue_numbers`
  and `sweeps.live_issues` refuse on `truncated`, `sweeps.known_keys`
  replaces the sentence through `full_note`. Problem ordering within each
  caller's list is preserved (the window problem stays first, ahead of
  per-item problems).
- **`--limit` placement.** All ten windowed sites put `--limit` last on
  main, so `[*args, "--limit", str(window)]` reconstructs a byte-identical
  argv. `cli.gh_read` never mutates the caller's list (`list(args)` /
  `[*args, …]`), which `test_the_callers_args_are_not_mutated` pins —
  worth naming because six callers pass a module-level tuple or list that
  a mutation would have poisoned for the process's lifetime.
- **`expect` default changed from `None` to `list`.** Not a behavior
  change: all fourteen main call sites passed `expect=list` or
  `expect=dict` explicitly; no site relied on the unchecked path.
- **The stay walk.** `completed_stays` is semantically identical to both
  deleted copies — `start <= ts and (next_start is None or ts < next_start)`
  is `c >= start and (next_start is None or c < next_start)` re-spelled,
  and the confirmations list and stay-collection loop are byte-equal.
  Result ordering is preserved on both sides: `gate_passages` iterates
  `GATES` outer / stays inner as before, and `gate_rejections` sorts by
  end over a stably-ordered generator.
- **`waited_seconds` is `_seconds`.** `gate_digest._queues` passes
  `now.isoformat()` on a tz-aware UTC datetime, so the `Z` replace is a
  no-op there, exactly as on main.
- **The ledger fold.** `dispatched` reproduces `cost_report.aggregate`'s
  two `continue`s exactly, and `aggregate`'s four figures are now the
  same row set by construction. `cost_report.py:98`'s `>=` and
  `work_queue.py:153`'s `>` are untouched, which is right — they answer
  different questions.
- **No orphaned imports.** An AST pass over all fifteen touched modules
  found none; `label_sync`, `sweeps`, `validator`, `gate_digest` and
  `rejection_mining` still import `CLI_FAILURES`/`detail` because their
  *mutation* paths still catch, and `dashboard` still imports
  `CLI_FAILURES` for its `git` call at :123. `dashboard`'s
  `detail as run_detail` was correctly dropped with its last use.

### Design — one major, one minor (both above)

Against `architecture.md`'s contracts, clause by clause: `cli.gh_read`'s
signature, its `GhResult` shape and all five failure-mode strings match
the design exactly; `human_gates` exports exactly the eight names the
design lists and imports only `datetime` and `collections`;
`knowledge_plane.mirror_map(root)` is unchanged in behavior;
`cost_ledger.dispatched(entries, month=None)` matches; the `Gate`
namedtuple keeps positional unpacking working at both iteration sites
that use it (`gate_digest._queues:140`, `dashboard._queues:175`) while
`gate_labels()` reads by name. Every item on the design's *What does not
move* list is still where it was, locally defined: `_timelines` in both
tools, `dashboard._timeline`, `_post_digest`, `_post_queue`,
`compose_digest`, `compose_queue`, `_capture_latency`, the marker idioms,
`dashboard._age_seconds`. The gate item did not grow past its evidence,
which is the first way `defect.md` said this run could die.

**Did the deepenings deepen?** Checked one at a time, because an inert
seam is a finding:

- `cli.gh_read` — fourteen callers, each of which gave up five facts: a
  `--limit` literal, a `try/except`, a shape check, a second window call,
  and a hand-typed prefix. `cli.py` is net +27 (+57 / −30) while the
  eight caller modules are net −203 between them (+158 / −361) across
  items 1 and 2 together. Not inert.
- `human_gates` — `gate_digest.py` net −103 and `rejection_mining.py` net
  −47 across the run, and the detector stopped slicing a tuple. Four real
  callers, all constructed. Not inert.
- `cost_ledger.dispatched` — absorbed `cost_report`'s two `continue`s
  *and* supplied the skip `work_queue` never had. Two real callers, and
  the second one's behavior actually changed, which is the item's point.
  Not inert.
- `GhResult.truncated` — two real consumers (`work_queue`,
  `sweeps.live_issues`). `full_note` and `label=None` have one production
  caller each, but each exists because a caller's *string* would
  otherwise have to be rebuilt outside the seam; neither is anticipated
  reuse. Not inert.
- `knowledge_plane.mirror_map` — a relocation, not a deepening, and
  correctly priced as one in the design.

### Security — no findings

- **argv construction.** `cli.gh_read` builds `[*args, "--limit",
  str(window)]` as a list and hands it to `runner`, which calls
  `subprocess.run([binary, *args], check=True, capture_output=True,
  text=True)`. No `shell=True` anywhere in the tree; no `os.system`, no
  `os.popen`. Nothing is string-interpolated into a command — the only
  f-strings in the seam build problem text. `window` is coerced with
  `str()` and every call site passes a module constant.
- **Credential handling is untouched.** The diff does not go near
  `cli.child_env`, `cli.read_event`, `cli.read_execution` or any
  token-bearing path; `cli.py`'s only changes are the docstring and the
  `gh_json`/`full_window` → `gh_read` swap. No workflow file changed.
  `gh` still authenticates from the environment, unread by this code.
- **Nothing secret can reach a problem string, a log line or an
  artifact.** The three interpolations into problem text are `operation`
  (a caller-supplied literal, at worst carrying an issue number),
  `full_note` (one caller, a pinned literal), and `cli.detail(err)` —
  which is unchanged from main and yields either `gh`'s last stderr line
  or `str(err)`. `str(CalledProcessError)` echoes the argv, and every
  argv here is a static read plus an issue number. The seam never puts
  `gh`'s stdout into a problem: `json.JSONDecodeError`'s message carries
  a position, not content. Same exposure as main, at fourteen sites
  instead of fourteen.
- **The payload is coherent.** All 25 `MIRRORS` entries match their root
  files byte-for-byte under their transforms, `update-manifest` on a
  clean tree is a no-op with an empty `git status`, and detector E is
  green — so nothing was smuggled into a stamped repo's copy of a tool.

## Notes

Things worth the operator's eye that are not findings against this diff.

1. **Pre-existing, found while driving the payload: `toolsmith-mine` is
   dead in every stamped product repo.** The payload's
   `rejection_mining.py` carries `from sweeps import sanitize` (line 44)
   and `sweeps.py` is not in `factory_init.MIRRORS`. In a freshly stamped
   repo, `python3 tools/factory/rejection_mining.py mine` — the exact
   command `factory/templates/Makefile:64-65` runs, and the exact command
   this run's C1 lockstep now pins — fails with `ModuleNotFoundError: No
   module named 'sweeps'` before any work happens. Identical on main: the
   import and the `MIRRORS` omission both predate this run, so it is not
   a regression, and C1's assertion is correct as written because it pins
   command *text*, not runnability. But the run gave a lockstep class to
   a target that does not run where it ships, which is worth knowing
   before anyone reads S5 as "toolsmith-mine is now covered". Route to
   `capture` (or a `docs/backlog.md` seed): the fix is either a `MIRRORS`
   row for `sweeps.py` or lifting `sanitize` to a module that already
   ships, and both are design questions this run's brief forbids
   widening into.
2. **The stale-comment observation has a home already.**
   `docs/backlog.md` carries "A drift detector for retyped seam grammar"
   (from `maintenance:deepening-cli-seams`), unclaimed. The five window
   comments are that seed's subject one level up; append rather than
   re-file.
3. **`human_gates.completed_stays` has no production caller** — only
   `gate_passages`, `gate_rejections` and the tests. That is deliberate
   and correct (it is the one walk the two public halves filter, and
   exporting it is what made the partition property testable), so it is
   not the inert-indirection case. Named here so a future reader does not
   mistake it for one and delete it.
4. **Verify's "not verified" list is accurate and I did not close it.**
   Nothing was driven against real GitHub, so it remains unproven that a
   live rate-limit or auth failure still lands in `CLI_FAILURES` now that
   the catch moved into the seam, and that `live_labels`' three callers
   behave the same against a live failure. Verify's remedy — watch one
   scheduled run of `label-sync`, `gate-digest` and `toolsmith-mine`
   after merge for a nonzero exit or a changed problem line — is the
   right one and belongs in `release.md`. Note that `toolsmith-mine` in
   *this* repo runs from the root, where `sweeps.py` exists, so item 1
   above does not affect that watch here.
5. **ADR-0056 is provisional.** Confirming it at merge is the Ship
   stage's act, per the run's own precedent (ADR-0054). Not a review
   finding; flagged so it is not forgotten.
6. **Stale references to `gh_json` / `full_window` / `gate_digest.GATES`**
   exist in `plans/`, `.beads/`, and the completed
   `docs/features/process-dashboard/` and `docs/fixes/deepening-cli-seams/`
   run artifacts. All are historical records the repo treats as
   append-only. Correctly left alone.

## Passes with no findings

**Security** came back clean. **Correctness** came back clean — the four
targeted checks the run's shape demanded were each refuted with driven
evidence rather than reasoning, and main's eight per-caller suites pass
unchanged against HEAD's production code. **Design** carries the one
major and one of the minors.

## Verdict

**Ready to ship.** Zero critical findings, so nothing blocks the merge
under the brief's release authorization, and its two non-waivable
conditions are both satisfied: the battery is green at `3aca0f6`, and
there is no unfixed critical.

One major and three minors stand. The major (`human_gates.py` missing
from CLAUDE.md's shared-module list) and two of the minors (the
`TestThePartition` docstring, the "none raise" claim) are prose-only
fixes that touch no code, no assertion and no manifest, so they can land
in one commit before the merge without re-verifying anything — that is
the recommendation. The fourth is deferred with its reason recorded.

The run did what it said. Four facts have one owner each, both live
divergences are gone, the one deliberate output change is the one that
was priced, and every other observable string in the tree is
byte-identical — which I re-derived rather than took on trust.
