---
stage: capture
run: maintenance:marker-diagnostics-that-lie
date: 2026-08-24
re-entry: architect
assumptions: ["Severity is deliberately stated as low and not inflated. Neither diagnostic can buy a false SILENCE — both emit an extra problem string, never suppress a real one — and one_owner.py runs outside make check and outside every workflow, so neither has ever coloured main red. What they cost is the author's trust in the output, which is the whole value of a pass whose findings are questions for a human.", "re-entry is architect rather than implement: diagnostic 1's fix adds a field to FactSite, and tests/test_one_owner.py:968 pins the three namedtuples' fields as 'architecture.md's Data model'. A pinned shape is a recorded decision, so the change gets architecture.md and breakdown.md rather than going straight to code."]
---

# Defect: two marker diagnostics tell the author something false

Origin: backlog seed `docs/backlog.md:55`
(from: maintenance:one-fact-one-owner), claimed as
`(claimed: maintenance:marker-diagnostics-that-lie)`. Tracking issue #336.

## Diagnostic 1 — a marker above a decorated definition is rejected

`markers` (one_owner.py:266) joins its line scan to `fact_sites` by the
definition's own `lineno`:

```python
    for site in sites:
        lineno = site.lineno - 1
        while lineno in comments:
            owner_of[lineno] = site
            lineno -= 1
```

`ast.FunctionDef.lineno` is the `def` line, not the first decorator. So for

```python
# one-owner: other.g (ADR-0037) — the alias is sanctioned
@staticmethod
def f(payload): ...
```

the walk starts at the `@staticmethod` line, which is not a comment, and
stops before it ever reaches the marker. The marker is then reported as
attaching to nothing.

### Reproduction

`$SCRATCHPAD/probe_diag.py`, run at HEAD (6f51472), builds one module twice
— once with a bare `def`, once with the same `def` decorated — and asks
`markers` for both:

```
--- diagnostic 1: a marker above a DECORATED definition
  undecorated  markers=1 problems=[]
  decorated    markers=0 problems=['one-owner: a.py:1 is a one-owner marker above no definition']
```

Same marker, same definition, same fact — one placement of a decorator
apart. The message is false twice over: the marker *is* above a definition,
and the author has done exactly what ADR-0061 asks (record the carve-out at
the definition it excuses).

The only workaround is to bury the comment between the decorator and the
`def`, which reads as a note about the decorator rather than about the
function.

## Diagnostic 2 — a counterpart that exists is reported as deleted

`_rent` (one_owner.py:365) builds its universe of names from fact sites:

```python
    defined = {_ident(site.path, site.name) for site in sites}
```

A fact site is a module-level `NAME = <expr>` or a function reading at least
**two** named keys. So a function that exists, is tracked, and is perfectly
readable — but reads one key — is not in `defined`, and a marker naming it
gets:

```
--- diagnostic 2: a counterpart that EXISTS but states no fact
  fact sites: [('a.py', 'f')]
  other.py binds: ['other.g']
  _rent says: ['one-owner: a.py:1 names other.g, which is not defined in this repo']
```

`other.g` is defined in `other.py`, six lines away. The message sends the
maintainer looking for a deletion that never happened.

This is not a contrived shape: dropping below the two-key floor is exactly
what a **fold** does to one side of a duplicate. The author folds the
duplication the marker was excusing, the counterpart simplifies, and the
tool reports the counterpart as missing rather than saying the marker is now
unnecessary.

## What is NOT wrong

Both diagnostics add a problem string. Neither removes one:

- Diagnostic 1 emits an extra "marker above no definition" where a correct
  marker should be silent. The carve-out it fails to honour stays unhonoured,
  so the duplicate it excused is still reported — a *doubled* complaint, not
  a missed one.
- Diagnostic 2 emits the wrong text for a marker that genuinely does need
  attention. `_rent`'s job — a carve-out list nothing re-checks is the
  condition this tool exists to fix — is still done; it is done with the
  wrong reason attached.

So neither can let a second owner through unreported. `one_owner.py` is a
review pre-pass, deliberately outside `make check` and outside every
workflow, so neither has ever turned a build red.

## Scale of exposure today

```
root modules: 28
decorated definitions: ['cli.py:170 harness_run']
```

One decorator across the whole root tree, and it carries no marker. So
diagnostic 1 is currently unreachable in this repo and diagnostic 2 has no
live instance either — the eight standing findings are all duplicate
reports, none of them marker rent. The seed's own judgement holds: cheap to
leave, cheap to fix.

## Baseline to preserve

`python3 one_owner.py` at HEAD (6f51472), which this run must reproduce
exactly:

```
one-owner: assembler.py:54 READY_LABEL, validator.py:79 READY_LABEL and work_queue.py:39 READY_LABEL state the same value — one fact, one owner
one-owner: budget_guard.py:167 record and cost_ledger.py:126 row_key read the same payload keys (run_id, wo) — one fact, one owner
one-owner: budget_guard.py:55 CONTINUE and cost_report.py:44 CONTINUE state the same value — one fact, one owner
one-owner: charter_replay.py:49 ROOT and trigger_eval.py:42 ROOT state the same value — one fact, one owner
one-owner: dashboard.py:198 _pr_by_issue, gate_digest.py:187 run_daily and rejection_mining.py:192 run_mine read the same payload keys (body, number, state) — one fact, one owner
one-owner: eval_schema.py:182 validate and trigger_eval.py:303 score_case read the same payload keys (expected, id, kind, query) — one fact, one owner
one-owner: gate_digest.py:91 LIST_ARGS and rejection_mining.py:54 ISSUE_ARGS state the same value — one fact, one owner
one-owner: label_sync.py:69 plan, label_sync.py:115 sync and sweeps.py:269 ensure_labels read the same payload keys (color, description, name) — one fact, one owner
one-owner: 8 problem(s)
```

## Re-entry

`architect`. Diagnostic 2's fix is a message and a new source of names — a
local change. Diagnostic 1's is not: `markers` cannot see decorators without
a shape that carries them, and the shape it reads from,
`FactSite`, is pinned by `tests/test_one_owner.py:968` as architecture.md's
Data model. Changing a pinned shape is a decision, so it gets written down.

**2026-08-25 — the base moved, and the baseline above moved with it.** This
branch was cut from the tip of the still-open `one-labels-walk` branch
(6f51472) rather than from `main`, which would have stacked this PR on that
one. Ship rebased it onto `origin/main` (622e7c0) so it stands alone. The
eight findings above were measured at the old base and are left as the
record of what capture actually saw; on `origin/main` the pass reports
**nine**, the extra one being the `cli.label_names` / `plane_drift.issue_lifecycle`
group that PR #335 closes. `verification.md`'s C5 re-derives byte-identity
against the new base, not this one.
