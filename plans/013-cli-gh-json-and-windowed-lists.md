# Plan 013: `cli.gh_json` — gh output that parses or becomes a problem string, and full-window guards on the big listings

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 2e63a04..HEAD -- cli.py gate_digest.py label_sync.py sweeps.py validator.py tests/test_cli.py tests/test_gate_digest.py tests/test_label_sync.py tests/test_sweeps.py tests/test_validator.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (but land BEFORE plan 014, which adds a new
  gh-JSON call site that should use this helper)
- **Category**: bug
- **Planned at**: commit `2e63a04`, 2026-08-02

## Why this matters

Five call sites run `json.loads(run(...))` over `gh` stdout inside
`try/except GH_FAILURES` — but `GH_FAILURES` is `cli.CLI_FAILURES =
(subprocess.CalledProcessError, OSError)`, and `json.JSONDecodeError` is
a `ValueError`. A `gh` that exits 0 with a banner, empty, or truncated
stdout therefore raises an uncaught traceback out of the three scheduled,
network-facing jobs (sweeps, gate-digest, validator lifecycle) — exactly
the "traceback is noise" failure the repo's own comments say must become
a label-prefixed problem string (`label_sync.py:104`). Separately, two of
the listings (`gate_digest`, `label_sync`) use `--limit 1000` with **no
full-window check**, while `sweeps.known_keys` already reports its full
window as a problem — past the window, gate-latency rows silently stop
being captured. One seam helper fixes both classes at all five sites.

## Current state

- `cli.py:31`: `CLI_FAILURES = (subprocess.CalledProcessError, OSError)`.
  `gh_runner(args)` (line 116) returns stdout, raising `CLI_FAILURES`.
  `tests/test_cli.py:60-68` (`TestFailureVocabulary`) currently pins that
  `ValueError` is *excluded* — the comment says "The two ways a shell-out
  goes wrong". This plan adds the third way.

- The five call sites (each aliases `from cli import CLI_FAILURES as
  GH_FAILURES` or similar — grep to confirm the alias in each file):
  1. `gate_digest.py:292` — `listing = json.loads(run(list(LIST_ARGS)))`
     inside `except GH_FAILURES`; `LIST_ARGS` (line 168) carries
     `"--limit", "1000"`; **no window check**; result iterated as a list.
  2. `gate_digest.py:200` — per-issue timeline:
     `pages = json.loads(run(["api", path, "--paginate", "--slurp"]))`.
  3. `label_sync.py:97` — `live_labels(run)` = `json.loads(run(list(LIST_ARGS)))`
     with `--limit 1000` (line 90); **raises** to its two callers
     (`label_sync.sync`, `sweeps.label_drift`), which catch `GH_FAILURES`
     only; no window check.
  4. `sweeps.py:291-301` — `known_keys`: has the `isinstance(issues, list)`
     shape guard AND the full-window problem
     (`sweeps: gh issue list returned a full {LIST_WINDOW}...`) — the
     model to generalize; only its JSON-decode hole needs closing.
  5. `validator.py:301` — `current = json.loads(run(["issue", "view", ...]))`
     then `current.get("labels")` — a list result would also crash with
     `AttributeError`.

- Injected-runner test pattern: every suite passes a fake `run` callable
  (see `tests/test_label_sync.py`, `tests/test_gate_digest.py`,
  `tests/test_sweeps.py`, `tests/test_validator.py`). No test anywhere
  returns unparseable stdout from a "successful" runner.

- Conventions: seam modules own shared knowledge (`cli.py` is the
  external-CLI seam, ADR-0037/0040/0042); callers keep their own problem
  label prefixes (`gd:`, `L:`, `sweeps:`, `V:`); helpers that can't know
  the caller's label return **unlocated suffixes** the caller prefixes
  (the `cost_ledger.line_problems` idiom). Mirrored files: `cli.py`,
  `gate_digest.py`, `label_sync.py`, `validator.py` are in
  `factory_init.MIRRORS`; `sweeps.py` is NOT (confirm with
  `grep sweeps factory_init.py`).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Full local gate | `make check` | exit 0 |
| Affected suites | `python3 -m unittest tests.test_cli tests.test_gate_digest tests.test_label_sync tests.test_sweeps tests.test_validator -v` | all pass |
| Refresh mirrors + manifest | `python3 factory_init.py update-manifest` | exit 0 |

## Scope

**In scope**:
- `cli.py` (the new helper), `gate_digest.py`, `label_sync.py`,
  `sweeps.py`, `validator.py` (call-site conversions only)
- Their five test files
- `factory/templates/**`, `factory/manifest.json` — only via
  `update-manifest`
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `charter_replay.py` / `trigger_eval.py` — they parse `claude` output
  with their own deliberate line-by-line policies, not gh JSON.
- Batching/narrowing the gate-digest timeline fan-out (a separate,
  unselected finding) — this plan changes error handling, not call
  volume.
- Any existing problem-string text at the five sites beyond what the
  steps below specify — the suites pin them byte-for-byte.

## Git workflow

- Branch: `advisor/013-cli-gh-json-windowed-lists`
- Commit style: `fix(cli): gh_json seam — unparseable gh output becomes a
  problem, big listings report a full window`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add `gh_json` (and a window suffix helper) to `cli.py`

Below `gh_runner`:

```python
def gh_json(args, run=gh_runner, expect=None):
    """(parsed value, problem-suffix): run gh and parse its stdout as
    JSON. The third failure vocabulary entry — ran, exited 0, said
    something unreadable — becomes a suffix here instead of a traceback
    in a scheduled job; `expect` (list or dict) adds the wrong-shape
    case. Callers prefix their own label, exactly the
    cost_ledger.line_problems convention. (None, suffix) on any failure;
    a failed/missing gh still raises CLI_FAILURES — that vocabulary
    entry stays the caller's catch."""
    out = run(args)
    try:
        value = json.loads(out)
    except json.JSONDecodeError as err:
        return None, f"gh returned unparseable JSON: {err}"
    if expect is not None and not isinstance(value, expect):
        return None, (f"gh returned {type(value).__name__} where"
                      f" {expect.__name__} was expected")
    return value, None


def full_window(entries, limit):
    """Problem-suffix when a windowed gh listing came back full — gh
    truncates silently, so a full window means entries past it are
    invisible and must be reported, never trusted (the sweeps
    known_keys rule, made shared)."""
    if len(entries) >= limit:
        return (f"gh listing returned a full {limit}-issue window —"
                " older entries are invisible; raise the window or"
                " narrow the query")
    return None
```

Note `CLI_FAILURES` still propagates out of `gh_json` — callers keep
their existing `except GH_FAILURES` around the call, so the two existing
failure modes keep their existing per-site problem strings.

**Verify**: `python3 -m unittest tests.test_cli -v` → passes (new tests
come in step 3).

### Step 2: Convert the five call sites

At each site, keep the surrounding `try/except GH_FAILURES` and its
existing problem string; add handling for the new `(None, suffix)`
return with the caller's own prefix. Precisely:

1. `gate_digest.py:292` area:
   ```python
   try:
       listing, suffix = gh_json(list(LIST_ARGS), run, expect=list)
   except GH_FAILURES as err:
       return ({"changed": "false"},
               [f"gd: gh issue list failed: {gh_detail(err)}"])
   if suffix:
       return {"changed": "false"}, [f"gd: {suffix}"]
   window = full_window(listing, 1000)
   if window:
       problems.append(f"gd: {window}")
   ```
   (Declare the `1000` once — lift it into a named constant next to
   `LIST_ARGS`, e.g. `LIST_WINDOW = 1000`, and use it in both places.
   Note: `problems` is initialized after this call today — reorder so
   the window problem is collected, non-fatally, and reported with the
   digest's other problems.)
2. `gate_digest.py:200`: same conversion, `expect=list`; on `suffix`,
   append `f"gd: gh api timeline for #{number}: {suffix}"` and
   `continue` (mirror of the existing per-issue failure handling).
3. `label_sync.py`: change `live_labels(run)` to return
   `(labels, problems)` — inside it, catch nothing (callers own
   `GH_FAILURES`) but use `gh_json(..., expect=list)` and
   `full_window(labels, 1000)`; return
   `([], ["L: " + suffix])`-shaped problems. Update its two callers:
   `sync()` here, and `sweeps.label_drift` (which currently catches the
   raise) — each surfaces the returned problems with its own prefix
   convention preserved. Keep the existing raise-through behavior for
   `GH_FAILURES` untouched.
4. `sweeps.py:291-301` (`known_keys`): replace the manual
   `json.loads` + `isinstance` + window check with `gh_json(...,
   expect=list)` + `full_window(issues, LIST_WINDOW)` — **preserving the
   exact existing problem strings** where tests pin them
   (`tests/test_sweeps.py` asserts the full-window text; if the shared
   suffix differs from the pinned text, keep sweeps' own wording at this
   site and use the shared helper only for the JSON hole — the tests are
   the contract, do not weaken them).
5. `validator.py:301`: `current, suffix = gh_json(["issue", "view",
   str(number), "--json", "labels"], run, expect=dict)`; on suffix return
   `[f"V: gh issue view {number}: {suffix}"]`.

**Verify** after each file: its suite passes, e.g.
`python3 -m unittest tests.test_gate_digest -v`.

### Step 3: Pin the vocabulary and the new branches

- `tests/test_cli.py` `TestFailureVocabulary`: add
  `test_covers_ran_succeeded_and_said_nonsense` — a fake runner returning
  `"gh: banner text"` → `gh_json` gives `(None, suffix)`; a runner
  returning `"{}"` with `expect=list` → wrong-shape suffix; a runner
  returning valid JSON → `(value, None)`. Update the class comment ("the
  two ways" → three).
- One test per converted site, fake runner returning garbage stdout →
  the exact new problem string, no exception. For the two windowed
  listings, a fake runner returning exactly-limit entries → the window
  problem string appears (and the job still completes).

**Verify**: `python3 -m unittest discover tests` → all pass.

### Step 4: Refresh mirrors

```
python3 factory_init.py update-manifest
```

**Verify**: `make check` → exit 0.

## Test plan

Step 3. Pattern: each suite's existing fake-runner tests (e.g.
`tests/test_gate_digest.py:46`). Cases per site: unparseable stdout;
wrong top-level shape; full window (sites 1, 3, 4 only); plus the
positive path already covered by existing tests.

## Done criteria

- [ ] `make check` exits 0
- [ ] `grep -c "json.loads(run" gate_digest.py label_sync.py sweeps.py validator.py` → 0 total
- [ ] `TestFailureVocabulary` covers the third mode
- [ ] Full-window problems exist for the two `--limit 1000` listings
- [ ] `factory/manifest.json` regenerated and committed
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- The exact problem strings pinned by `tests/test_sweeps.py` /
  `tests/test_label_sync.py` cannot be preserved while adopting the
  helper — do not change a pinned string to fit the helper; report the
  conflict.
- `live_labels` has callers beyond `label_sync.sync` and
  `sweeps.label_drift` (`grep -rn live_labels --include="*.py" .`).
- A sixth `json.loads(run(` site exists that this plan doesn't list.

## Maintenance notes

- Plan 014 adds a new lifecycle gh call — it must use `gh_json` from day
  one.
- The unselected findings about batching the timeline fan-out and
  consolidating label reconciliation touch these same sites; this plan's
  conversions are deliberately mechanical so those later refactors
  rebase cleanly.
- Reviewer should scrutinize: no call site lost its `GH_FAILURES` catch
  (the helper adds a failure mode, it must not swallow the existing two).
