---
stage: capture
run: maintenance:a-timestamp-the-digest-cannot-parse
date: 2026-09-15
re-entry: architect
origin:
  - "docs/backlog.md:26 — `human_gates.waited_seconds` propagates ValueError on a completed stay whose timestamp is truthy but not ISO-8601 (from: maintenance:deepening-tool-seams)"
assumptions:
  - "Origin shape: the protocol names no frontmatter form for a run seeded by a backlog seed, so the single seed is recorded in the form `docs/fixes/one-fact-one-owner/defect.md` established — a YAML list of `docs/backlog.md:<line> — <gist> (from: <run-ref>)` entries, one entry here. The seed was claimed in place with the sanctioned suffix append; its `(from: …)` marker was not rewritten."
  - "Section set: `skills/capture/TEMPLATE.md` has no section for a design question handed to Architect, for scope, or for success criteria. The repo's only other `re-entry: architect` defect brief (`docs/fixes/one-fact-one-owner/defect.md`) adds exactly those three, so this brief takes that precedent as the default rather than compressing them into `## Notes`. The template's own sections keep their order and none is dropped."
  - "Root-cause hypothesis: the seeding brief states a mechanism (`label_events` admits an event on truthiness alone) but never labels a root cause. This brief promotes that mechanism to a hypothesis, widens it to the third layer the brief does not mention (the fetcher), and labels the whole thing a hypothesis — per the capture skill's rule that a guess must not be dressed as a finding."
---

# Defect: a timestamp the digest cannot parse

## Defect

`gate_digest.py` is a factory CLI. Its contract, stated in its own module
docstring, is the repo-wide one: *"functions return gd:-prefixed problem
strings; the CLI prints them and exits nonzero."*

**It does not hold that contract against a malformed timestamp.** A
GitHub label-timeline event whose `created_at` is truthy but not
ISO-8601 reaches `human_gates.waited_seconds`, which calls
`datetime.fromisoformat` with no guard. The `ValueError` propagates out
of `waited_seconds`, out of `gate_digest.run_daily`, out of
`gate_digest.main`, and out of `sys.exit(main(sys.argv[1:]))`.

- **Observed:** an uncaught `ValueError: Invalid isoformat string:
  'not-a-timestamp'`. The daily workflow step fails on a Python
  traceback. No `gd:` problem string is printed, no `changed` output is
  written, and the digest issue is never posted.
- **Expected:** a `gd:`-prefixed problem string and a nonzero exit — the
  same shape every other failure in this tool already produces
  (`gd: gh issue edit 12 failed: …`, `gd: gh issue list returned
  unparseable JSON: …`).

This is not a missing capability. The tool has an error channel; this
input walks past it.

## Reproduction / Evidence

Every command below was run in this working tree at HEAD `622e7c0`
(`docs(adr): confirm seven pipeline-design decisions; 0028 stays
provisional`) on 2026-09-15, and every block is that run's real output.

### 1. The minimal raise

The seeding brief's repro, re-run rather than inherited:

```
$ python3 - <<'PY'
import human_gates as hg
timeline = [
    {"event": "labeled",   "label": {"name": "wo:draft"},
     "created_at": "2026-08-30T10:00:00Z"},
    {"event": "labeled",   "label": {"name": "wo:prd-approved"},
     "created_at": "2026-08-30T11:00:00Z"},
    {"event": "unlabeled", "label": {"name": "wo:draft"},
     "created_at": "not-a-timestamp"},
]
events = hg.label_events(timeline)
print("completed_stays:", hg.completed_stays(events, hg.GATES[0]))
for fn in (hg.gate_passages, hg.gate_rejections):
    try:
        print(fn.__name__, "->", fn(events))
    except Exception as err:
        print(f"--- {fn.__name__} raised: {type(err).__name__}: {err}")
PY
completed_stays: [('2026-08-30T10:00:00Z', 'not-a-timestamp', True)]
--- gate_passages raised: ValueError: Invalid isoformat string: 'not-a-timestamp'
gate_rejections -> []
```

Confirmed, byte for byte, including the two facts the seed line does not
state: `completed_stays` returns the malformed stay cleanly, and
`gate_rejections` survives it.

### 2. The whole tool dies, not one row

The seed's blast-radius claim is that the traceback escapes. It does.
Driven through the real `run_daily` and the real `main`, against a real
mirrored issue number taken from this repo's own breakdown rows, with
only the `gh` runner injected:

```
$ python3 - <<'PY'
import json
from datetime import datetime, timezone
import knowledge_plane, gate_digest
root = knowledge_plane.repo_root()
mirror = knowledge_plane.mirror_map(root)
number = sorted(mirror)[0]
print("using real mirrored issue:", number, "->", mirror[number])
TIMELINE = [...]                      # the same three events as above
def fake_run(argv):
    if argv[:2] == ["issue", "list"]:
        return json.dumps([{"number": number, "title": "WO-x mirror",
                            "state": "OPEN", "labels": [], "body": ""}])
    if argv[0] == "api" and argv[1].endswith("/timeline"):
        return json.dumps([TIMELINE])
    return "[]"
clock = lambda: datetime(2026, 9, 15, tzinfo=timezone.utc)
try:
    out, problems = gate_digest.run_daily(root, run=fake_run, clock=clock)
    print("run_daily ->", out, problems)
except Exception as err:
    print(f"--- run_daily raised: {type(err).__name__}: {err}")
try:
    rc = gate_digest.main(["daily"], env={}, root=root, run=fake_run,
                          clock=clock)
    print("main -> exit", rc)
except Exception as err:
    print(f"--- main raised: {type(err).__name__}: {err}")
PY
using real mirrored issue: 106 -> WO-0001
--- run_daily raised: ValueError: Invalid isoformat string: 'not-a-timestamp'
--- main raised: ValueError: Invalid isoformat string: 'not-a-timestamp'
```

One malformed event on one mirrored issue takes down the whole daily
run. There is no per-issue isolation: `_timelines` builds the events for
every mirrored issue into one dict, and `_capture_latency` walks the
whole dict in one loop.

### 3. Both call sites reach it, independently

`gate_digest.py:124` — `_capture_latency`, through `gate_passages`:

```
$ python3 - <<'PY'   # events = the three-event history from §1
problems = []
try:
    print(gate_digest._capture_latency(root, {106: "WO-0001"},
                                       {106: events}, problems))
except Exception as err:
    print(f"--- gate_digest._capture_latency raised: {type(err).__name__}: {err}")
print("problems collected before the raise:", problems)
PY
--- gate_digest._capture_latency raised: ValueError: Invalid isoformat string: 'not-a-timestamp'
problems collected before the raise: []
```

`gate_digest.py:149` — `_queues`, through `waited_seconds` directly. It
needs no completed stay at all: one *open* stay whose `labeled` event
carries the malformed timestamp is enough, because `waiting_since`
returns whatever string `label_events` admitted.

```
$ python3 - <<'PY'
open_timeline = [
    {"event": "labeled", "label": {"name": "wo:draft"},
     "created_at": "not-a-timestamp"},
]
events = hg.label_events(open_timeline)
print("label_events        ->", events)
print("waiting_since       ->", hg.waiting_since(events, "wo:draft"))
print("gate_passages       ->", hg.gate_passages(events))
entry = {"number": 106, "title": "WO-0001 mirror",
         "labels": [{"name": "wo:draft"}]}
try:
    print("_queues ->", gate_digest._queues({106: "WO-0001"}, [entry],
                                            {106: events}, now))
except Exception as err:
    print(f"--- gate_digest._queues raised: {type(err).__name__}: {err}")
try:
    print("dashboard._age_seconds ->",
          dashboard._age_seconds("not-a-timestamp", now))
except Exception as err:
    print(f"--- dashboard._age_seconds raised: {type(err).__name__}: {err}")
PY
label_events        -> [('not-a-timestamp', 'labeled', 'wo:draft')]
waiting_since       -> not-a-timestamp
gate_passages       -> []
--- gate_digest._queues raised: ValueError: Invalid isoformat string: 'not-a-timestamp'
--- dashboard._age_seconds raised: ValueError: Invalid isoformat string: 'not-a-timestamp'
```

Note `gate_passages -> []` on that same history: a fix that only guards
the passage path leaves the queue path raising. The two sites must be
answered together.

The last line is a **third** exposure the seeding brief does not mention;
see §7.

### 4. Nothing above the raise catches it

Read rather than assumed:

- `run_daily` (`gate_digest.py:187-221`) contains **no** `try`/`except`
  at all. `main` (`:224-235`) contains none either.
- The four `except GH_FAILURES` clauses the seed cites — `:166`, `:172`,
  `:178`, `:183` — are all inside `_post_digest` (`:156-184`), which
  `run_daily` calls. The brief attributes them to `run_daily`; the line
  numbers are right and the frame is one out. Substance unchanged: they
  guard `gh` mutations, not the walk.
- `cli.gh_read` (`cli.py:325`) catches `CLI_FAILURES` and
  `json.JSONDecodeError` on its callers' behalf, and shape-checks the
  **top level** only (`expect=list`). It never inspects a field value,
  so a well-formed JSON array of events with a garbage `created_at`
  passes it without comment.
- `GH_FAILURES` is `cli.CLI_FAILURES` = `(subprocess.CalledProcessError,
  OSError)` (`cli.py:50`). `ValueError` is not in it.

So the seed's claim — *"`gate_digest.run_daily` catches only
CLI_FAILURES"* — holds, one frame further out than stated.

### 5. The ledger write is made, then thrown away

Sharper than the seed. When the malformed timestamp is on an *open*
stay, `_capture_latency` completes first and appends real rows to
`docs/factory/costs.jsonl`; `_queues` then raises, so `write_outputs`
never runs, the workflow's `if: steps.digest.outputs.changed == 'true'`
commit step is skipped, and the rows die with the runner. Demonstrated
against a throwaway root (this repo's ledger was not touched):

```
$ python3 - <<'PY'   # throwaway root: one breakdown row
                     # (**WO-0001** … (tracker: #106), matching this
                     # repo's own mirror) and an empty ledger
env = {}
try:
    print("main ->", gate_digest.main(["daily"], env=env, root=root,
                                      run=fake_run, clock=clock))
except Exception as err:
    print(f"--- main raised: {type(err).__name__}: {err}")
print("GITHUB_OUTPUT written:", env)
print("ledger after the raise:", ledger.read_text(encoding="utf-8").strip())
PY
--- main raised: ValueError: Invalid isoformat string: 'not-a-timestamp'
GITHUB_OUTPUT written: {}
ledger after the raise: {"wo": "WO-0001", "run_id": "gate-prd-2026-08-30T11:00:00Z", "model": "none", "tokens": 0, "cost": 0.0, "outcome": "gate_wait:prd:3600s", "at": "2026-08-30"}
```

The ledger is not corrupted — the row is real, and `cost_ledger.row_key`
dedup makes the next day's re-scan safe. It is *lost*, every day, for as
long as the malformed event is inside the fetched timeline window.

### 6. The partition is asymmetric, and the miner really does survive

ADR-0056's stated invariant is that the digest and the miner *"partition
one list between them — every stay a passage there or a rejection here,
never both."* Against a malformed timestamp they do not behave as two
views of one walk. `gate_rejections` (`human_gates.py:128-136`) reads
only `end` and never calls `waited_seconds`. Driven end to end through
the miner's own `run_mine`, with the identical timeline that killed the
digest in §2:

```
$ python3 - <<'PY'
out, problems = rejection_mining.run_mine(root, run=fake_run)
print("rejection_mining.run_mine -> outputs:", out)
print("  problems:", problems)
PY
rejection_mining.run_mine -> outputs: {'reason': 'rm: 0 candidate WO(s), 0 correction(s) mined'}
  problems: []
```

Clean exit, no problems. The asymmetry the brief claims is real, and it
is not a coincidence of the two tools: it is a property of which half of
the partition needs a duration.

### 7. Where else the same hazard lives

`fromisoformat` across the root modules:

```
$ grep -rn "fromisoformat" *.py
cost_ledger.py:38:# The at field's shape: the dashed calendar form ONLY. date.fromisoformat
cost_ledger.py:189:                    date.fromisoformat(value)
dashboard.py:142:    quirk (fromisoformat accepts Z only from 3.11)."""
dashboard.py:143:    then = datetime.fromisoformat(since.replace("Z", "+00:00"))
human_gates.py:55:    """GitHub timestamps end in Z; fromisoformat only accepts that from
human_gates.py:57:    return datetime.fromisoformat(iso.replace("Z", "+00:00"))
```

Three parse sites, two verdicts:

- `cost_ledger.py:189` is **already guarded** — `try: date.fromisoformat(value)
  / except ValueError: valid = False`, feeding a problem string. Not an
  instance; see Ruled out.
- `dashboard.py:143` (`_age_seconds`) is **the same hazard, a third
  exposure**, and it is fed from the same two functions: `dashboard._queues`
  (`dashboard.py:187`) calls `human_gates.waiting_since` over
  `human_gates.label_events` and hands the result straight to its own
  unguarded parse. It raised in §3. `dashboard.main` has no guard over
  `gather`. It is **out of this run's scope** by the seeding brief's own
  boundary — recorded as seed text in Notes, not fixed here — but it is a
  real design input: a policy placed inside `label_events` fixes it for
  free, and a policy placed at the digest's two call sites does not.

Caller exposure in full — four importers of `human_gates`, two exposed:

| Caller | Imports | Exposed? |
|---|---|---|
| `gate_digest.py:42` | `GATES, gate_passages, label_events, waited_seconds, waiting_since` | **Yes** — `:124` and `:149` |
| `dashboard.py:51` | `GATES, label_events, waiting_since` | **Yes** — its own parse at `:143`; out of scope |
| `rejection_mining.py:42` | `gate_rejections, label_events` | No — no duration arithmetic (§6) |
| `gates.py:772` detector J | `gate_labels()` | No — label names only |

### 8. It has never actually fired

Read-only, no tracker write:

```
$ gh run list --workflow gate-digest.yml --limit 200 --json conclusion -q '.[].conclusion' | sort | uniq -c
   1 failure
  54 success
$ gh run list --workflow gate-digest.yml --limit 200 --json createdAt -q '.[].createdAt' | tail -1
2026-07-23T07:44:57Z
```

The one failure (`31867653848`, 2026-08-15) is **not** this defect — see
Ruled out. So: 55 scheduled runs since 2026-07-23, zero occurrences. This
is a latent defect, reproduced in the lab and never observed in
production. Nothing below claims otherwise.

### 9. No regression test exists

`grep` for a malformed-timestamp case across `tests/test_human_gates.py`,
`tests/test_gate_digest.py` and `tests/test_dashboard.py` returns only
`test_dashboard.py` hits about malformed *config*, *ledger lines*,
*corrections lines*, *request bodies* and *backlog bullets* — nothing
about a timestamp. The repro in §1 is the regression test this run owes,
and Verify is not skippable.

## Root-cause hypothesis

**Hypothesis, not a finding.** Three layers each assume a different one
validated the timestamp, and none does.

1. **`human_gates.label_events` (`:65-79`)** admits an event when its
   name and `created_at` are merely truthy, and its docstring states the
   delegation on purpose: *"Anything that is not a well-formed label flip
   is not this module's business; an unusable timeline is the fetcher's
   problem, never this walk's."* So it believes the fetcher checked.
2. **`human_gates._parse_ts` (`:54-57`)** exists to paper over a Python
   version quirk (`Z` before 3.11) and assumes a well-formed input. Its
   docstring makes a claim about GitHub — *"GitHub timestamps end in
   Z"* — and treats that as a guarantee rather than an expectation.
3. **The fetchers** — `gate_digest._timelines (:95-111)` and
   `dashboard._timeline (:147-158)` — validate through `cli.gh_read`,
   which owns *transport* failure (`CLI_FAILURES`, unparseable JSON,
   wrong top-level shape, window truncation) and deliberately owns no
   field semantics. So they believe transport success means usable data.

The root cause, then, is not the missing `try` in `_parse_ts` — that is
the symptom's location. It is that **no layer owns field-level validation
of a timeline event**, and the one layer that documents its non-ownership
names a fetcher that never took the job.

Corollary, offered as part of the same hypothesis: the miner/digest
asymmetry in §6 is a *consequence* of this, not a separate bug. Because
the raise lives in the duration helper rather than in the walk, the half
of ADR-0056's partition that needs a duration is fragile and the half
that does not is durable — which is exactly the shape of a validation
gap sitting one layer too low.

## The design question — Architect's to answer, not capture's

The seeding brief flags this and does not settle it; this brief does not
settle it either. It is the reason for `re-entry: architect`.

**Where is a malformed timestamp caught, and what does the caller then
report?** `label_events`' docstring is an explicit, deliberate,
ADR-0056-era delegation. The run cannot simply wrap `_parse_ts` in a
`try` and call it done, because doing so silently overrides a documented
decision. The three candidate answers, with what each costs:

1. **The walk drops it.** `label_events` refuses an event whose
   timestamp does not parse. Cheapest, fixes all three exposures
   including `dashboard` for free, and keeps every caller unchanged —
   but it reverses the docstring's stated delegation, makes the pure
   module the validator, and *loses data silently* unless the walk also
   returns what it dropped.
2. **The caller reports it.** A malformed stay becomes a `gd:` problem
   string in the digest (and a `dashboard:` one in the dashboard).
   Honours the problem-string contract most directly and loses nothing —
   but each caller must learn the rule separately, which is how
   ADR-0056's original divergence was created, and `dashboard` is out of
   this run's scope so the two halves would ship apart.
3. **The fetcher validates before the walk.** Takes the docstring at its
   word and puts the check where it says the check belongs — but the
   fetchers go through `cli.gh_read`, whose own docstring scopes it to
   transport failure and not to field semantics (quoted in §4; no ADR
   names `gh_read` at all), so this either grows `gh_read` a new
   responsibility or adds a fourth validating layer.

Second question, inseparable from the first: **is the asymmetry in §6
removed or documented as intentional?** ADR-0056's partition invariant is
the thing at stake, and ADR-0056 is **accepted** — which makes it harder to
move, not easier: it is superseded or amended by a new ADR, never rewritten.
That the invariant at stake sits in an accepted decision is part of why this
run re-enters at Architect.

Third, smaller: **does the fix reach `dashboard._age_seconds`?** The
brief scopes it out. Answer 1 above fixes it incidentally; answers 2 and
3 leave it raising. Whichever is chosen, the decision should be explicit
rather than a side effect.

## Blast radius

**Who.** Every repo the factory is stamped into, plus this one. Both
`human_gates.py` and `gate_digest.py` ship under
`factory/templates/tools/factory/` — verified byte-identical to their
roots (`diff` clean for both), mirrored through `factory_init.MIRRORS` as
identity entries.

**What, when it fires.** Total loss of the daily gate digest for that
day, not a degraded one:

- the workflow step (`make gate-digest`) exits on a traceback, so the
  `gate-digest` job goes red;
- no `gd:` problem string is printed — the operator sees a Python stack
  trace where the tool's whole convention promises a labelled line;
- the pinned digest issue is not updated, so the human-gate queues show
  stale waits;
- gate-latency rows are appended on the runner and then discarded (§5),
  so ADR-0041's latency capture silently misses a day;
- it repeats every day for as long as the malformed event stays inside
  the fetched timeline window — this is not a transient.

**How badly, honestly.** It has never happened (§8): 54 successes and one
unrelated push race in 55 scheduled runs since 2026-07-23. Real GitHub
timeline payloads carry well-formed `created_at` values. The realistic
triggers are an API shape change, a proxy or mirror in front of `gh`, a
replayed or hand-edited fixture, or a stamped repo whose `gh` is wrapped.
Severity is therefore **low likelihood, high impact, zero current
incidence** — and downstream Review and Ship should scale to that, not to
the impact alone.

**Since when.** 2026-07-22, `3d94380` (*feat(factory): WO-0017
gate-queue daily digest + gate-latency capture (#122) (#163)*), which
introduced `gate_digest.py` with a byte-identical unguarded `_parse_ts`:

```
$ git show 3d94380:gate_digest.py | grep -n "_parse_ts\|fromisoformat\|def waited"
64:def _parse_ts(iso):
65:    """GitHub timestamps end in Z; fromisoformat only accepts that from
67:    return datetime.fromisoformat(iso.replace("Z", "+00:00"))
71:    return int((_parse_ts(end) - _parse_ts(start)).total_seconds())
```

It moved to `human_gates.py` on 2026-08-18 at `60f867f` (*fix(factory):
one owner each, four times — the deepening-tool-seams run (#302)*), the
ADR-0056 relocation:

```
$ git log --diff-filter=A --format='%h %ad %s' --date=short -- human_gates.py
60f867f 2026-08-18 fix(factory): one owner each, four times — the deepening-tool-seams run (#302)
```

The seed's *"behavior relocated from gate_digest, not introduced"* is
confirmed. The defect is ~8 weeks old, not 4.

## Ruled out

- **`completed_stays` is not the raise site.** It admits the malformed
  stay and returns it intact (§1). Do not go looking for a fix there.
- **`gate_rejections` / `rejection_mining` are not affected.** Verified
  end to end against the same timeline: clean exit, no problems (§6). A
  fix must not be justified by "the miner breaks too" — it does not.
- **`cost_ledger.py:189` is not a second instance.** Its
  `date.fromisoformat` is already inside `try/except ValueError`, feeding
  the `at <value> is not an ISO date (YYYY-MM-DD)` problem string.
  Already correct; leave it alone.
- **`gates.py` detector J is not affected.** It reaches `human_gates`
  only through `gate_labels()` (`gates.py:772`), which touches no
  timestamp.
- **The one red `gate-digest` run in history is not this defect.** Run
  `31867653848`, 2026-08-15: the digest step itself succeeded and the
  *commit* step lost a push race —
  `! [rejected] main -> main (fetch first)`, *"Updates were rejected
  because the remote contains work that you do not have locally"*. A
  concurrency bug in the workflow, not a parse failure. Do not cite it as
  evidence for this run.
- **Widening `cli.gh_read`'s shape check is not a free fix.** It checks
  the top-level type only, by design (`expect=list`), and its docstring
  scopes it to transport failure. Extending it to field semantics is
  option 3 of the design question, not a shortcut around it.
- **Two adjacent backlog seeds were investigated and found stale** during
  run selection on 2026-08-31, per the seeding brief: seed 25
  (`toolsmith-mine` broken in every stamped repo — the `sanitize` import
  had moved to the mirrored `knowledge_plane`) and seed 28 (validator
  reds non-WO PRs — `Makefile:40` already passes `--uncited skip`).
  Neither bears on this defect; recorded so the same two are not
  re-walked.

## Scope

**In scope.** `human_gates.py` (`_parse_ts`, `waited_seconds`, and
`label_events` if the design lands there); `gate_digest.py`'s two call
sites (`:124`, `:149`); their payload twins under
`factory/templates/tools/factory/`; `factory/manifest.json`; regression
tests in `tests/test_human_gates.py`, and `tests/test_gate_digest.py` if
caller behavior changes. A new ADR if the chosen answer amends or
supersedes ADR-0056.

**Out of scope.** The rest of ADR-0056's partition beyond the asymmetry
question; `rejection_mining` behavior; `dashboard.py` (including
`_age_seconds`, §7 — flagged as a seed, not fixed); every other seed on
`docs/backlog.md`; the `gate-digest.yml` push race in Ruled out. No
drive-by hardening of unrelated parse sites.

## Success criteria

- A malformed-but-truthy timestamp anywhere in a gate timeline produces a
  `gd:`-prefixed problem string and a nonzero exit — **never** a
  traceback.
- **Both** call sites are covered: the completed-stay path
  (`_capture_latency` → `gate_passages`) and the open-stay path
  (`_queues` → `waited_seconds`), which the §3 evidence shows can be
  reached independently.
- The §1 repro is a passing regression test, and a second test covers the
  open-stay history from §3 that `gate_passages` returns `[]` for.
- The §6 asymmetry is either removed or recorded as intentional in an
  ADR, with ADR-0056 amended or superseded rather than rewritten.
- The payload twins and `factory/manifest.json` match root:
  `python3 factory_init.py update-manifest` is run and committed with the
  change, and detector E is green.
- The full battery is green: `python3 -m unittest discover tests`,
  `python3 lint.py` (matching `lint: 0 problem(s)`), and
  `python3 gates.py && python3 gates.py --selftest` (matching
  `gates: 0 problem(s)` and `selftest: ok`).
- `python3 one_owner.py` gains no new problems (it carries 9 pre-existing
  ones on `main`; clearing them is not this run's job).

## Constraints and things already decided

- **Stdlib only.** Standalone Python 3 standard library, no third-party
  imports.
- **Problem-string contract.** Checkers and validators return lists of
  label-prefixed problem strings; callers print and exit nonzero, never
  raise. Tests assert exact strings through public interfaces.
- **The never-a-traceback bar** — a factory CLI reports, it does not
  traceback — is what this defect fails, and is not up for re-litigation.
  Its actual sources are `gate_digest.py`'s own module docstring (quoted
  in `## Defect`), ADR-0051 (`accepted`), which restates the convention
  as *"checkers return label-prefixed problem strings; callers print and
  exit nonzero"*, and CLAUDE.md's hard conventions. **Not** ADR-0039, to
  which the seeding brief attributes it — see Notes.
- **ADR-0056 is the authority on the stay partition**, and its status is
  `accepted`. Citable, and moved only the repo's way: supersede or amend
  with a new ADR, never rewrite.
- **Template mirroring is checksum-pinned.** Any edit under
  `factory/templates/**` or to a root file in `factory_init.MIRRORS`
  requires `python3 factory_init.py update-manifest` committed with the
  change, or detector E fires.
- **No tracker interaction.** No issue is created, edited or closed by
  this run, and no `intake:` is recorded — the run was seeded from the
  backlog, not from a tracker issue. Work items will carry no
  `(tracker: #N)` references.
- **Release authorization: prepare-and-stop.** Ship runs the pre-flight
  checks and writes `release.md` recording readiness and the exact steps,
  and executes **no** externally visible release action — no deploy,
  publish, tag, or merge. Merging an agent-authored PR needs separate
  human approval.
- **User-facing surface: none.** CLI/tooling only; maintenance runs skip
  PRD, so no `ux:` decision arises.
- **Artifact-depth precedent:** `docs/fixes/one-fact-one-owner/`
  (2026-08-23), the repo's other `re-entry: architect` maintenance run.

## Notes

- **Re-entry is `architect`**, and the call is this stage's, made from
  the evidence above. Four things push it past a scoped fix: the
  catch-site question has three answers with materially different
  behavior and no supplied default; answering it overrides a docstring
  that states its delegation deliberately, which is an ADR-0056 decision;
  the asymmetry in §6 is a question about that ADR's partition invariant,
  not an implementation detail; and the change lands in a shipped,
  mirrored CLI in every stamped repo, which the seed itself says "wants
  its own evidence." There is deliberately **no inline checkbox
  breakdown** in this file — the `architecture.md` + `breakdown.md` chain
  owns the work items.

- **Backlog seed text for the third exposure — NOT appended, by
  instruction.** This run is authorized for exactly one backlog write
  (its own seed claim). The Architect or a follow-on session should
  append this line, once the catch-site answer is known and it is clear
  whether the dashboard is fixed incidentally:

  > `dashboard._age_seconds` (dashboard.py:143) carries the same
  > unguarded `datetime.fromisoformat` as `human_gates._parse_ts` and is
  > fed from the same pair — `dashboard._queues:187` takes
  > `human_gates.waiting_since` over `human_gates.label_events`, which
  > admits an event on truthiness alone — so a truthy-but-unparseable
  > `created_at` raises ValueError out of `gather` and `main`, which
  > guard it nowhere; `dashboard.py` is root-only (not in
  > `factory_init.MIRRORS`) so no stamped repo is affected, and whether
  > this is fixed at all depends on where
  > maintenance:a-timestamp-the-digest-cannot-parse puts its catch
  > (from: maintenance:a-timestamp-the-digest-cannot-parse)

  No other parse site qualifies: `cost_ledger.py:189` is already guarded
  (see Ruled out).

- **Corrections to the seeding brief**, all minor, all recorded rather
  than silently fixed:
  1. The four `except GH_FAILURES` clauses at `:166/:172/:178/:183` are
     in `_post_digest`, not in `run_daily`. `run_daily` and `main` guard
     nothing at all, which is if anything stronger than the brief's
     claim.
  2. The brief says the digest "would die on a traceback." True, and
     also never yet observed: 55 scheduled runs, one unrelated failure
     (§8). The brief does not overstate incidence, but neither does it
     state it, and Review/Ship scale to it.
  3. The brief's blast radius omits the lost ledger write (§5) and the
     third exposure in `dashboard` (§7).
  4. **The brief attributes the never-a-traceback CLI contract to
     ADR-0039.** It does not check out. ADR-0039 is *"The tracker-mirror
     grammar joins the knowledge plane"* (status: `amended by ADR-0040
     (roster further amended by ADR-0058)`); it decides that
     `knowledge_plane` owns `row_tracker_issue(line)` and says nothing
     about tracebacks. The convention is stated verbatim in ADR-0051
     (`accepted`) and in `gate_digest.py`'s own docstring. The bar this
     defect fails is real; only the citation was wrong, and this brief
     does not repeat it.

- **The seed is claimed.** `docs/backlog.md:26` now carries
  ` (claimed: maintenance:a-timestamp-the-digest-cannot-parse)` appended
  to the end of the line; the `(from: maintenance:deepening-tool-seams)`
  origin marker was not rewritten and no other line in that file was
  touched. It is the only write this stage made outside this run
  directory.

- **Nothing in this run's tree was changed.** Capture wrote this file and
  appended the seed claim. `human_gates.py`, `gate_digest.py`,
  `dashboard.py`, the tests, the templates and the manifest are
  untouched.
