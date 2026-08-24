---
stage: capture
run: maintenance:one-labels-walk
date: 2026-08-24
re-entry: architect
assumptions: ["This is a CONDITION brief, not a bug report. The two walks are behaviourally identical on every input reachable through reconcile_drift, measured below — so there is no failure scenario in the field, and saying otherwise to make the run look urgent would be the dishonesty this repo's evidence rules exist to prevent. What is degraded is ownership, which is the class the one-owner pre-pass exists to name.", "re-entry is architect, not implement: the fold makes a module whose docstring calls itself PURE import the CLI seam, and whether that is allowed is a design question with a real alternative. A one-line change with a decision behind it still gets the decision written down."]
---

# Defect: the drift rule retypes the labels walk the cli seam owns

Origin: backlog seed `docs/backlog.md:46`
(from: maintenance:deepening-tool-seams), claimed as
`(claimed: maintenance:one-labels-walk)`. Tracking issue #334.

## Condition

`plane_drift.issue_lifecycle` (plane_drift.py:31) walks a gh labels array
with its own `entry.get("name")` loop:

```python
def issue_lifecycle(issue):
    labels = issue.get("labels")
    names = [entry.get("name") for entry in labels
             if isinstance(entry, dict)] if isinstance(labels, list) else []
    return sorted(name for name in names
                  if isinstance(name, str) and name.startswith("wo:"))
```

That walk is `cli.label_names` (cli.py:376), and ADR-0037 gives the cli
seam the harness-IO conventions precisely so a gh payload shape has one
reader. `label_names`' docstring states the strictness as a decision —
*"One deliberate strictness for every caller — the strictest all of them
tolerate"* — which is a claim about every caller, and one caller is not
asking it.

Both of `plane_drift`'s callers already import the seam and use it feet
away from where they call the copy:

```
$ grep -n "label_names\|^from cli\|^from plane_drift\|^import plane_drift" sweeps.py dashboard.py
dashboard.py:46:from cli import CLI_FAILURES, gh_read, gh_runner, label_names
dashboard.py:47:from cli import report, runner
dashboard.py:55:import plane_drift
dashboard.py:184:                    queue_label not in label_names(issue):
dashboard.py:254:                              for name in label_names(issue)
sweeps.py:61:from cli import CLI_FAILURES as GH_FAILURES
sweeps.py:62:from cli import detail as gh_detail
sweeps.py:63:from cli import gh_read, label_names, report
sweeps.py:65:from plane_drift import reconcile_drift
sweeps.py:66:from cli import gh_runner
sweeps.py:291:    live = set(label_names(listing))
```

## Reproduction / Evidence

The pre-pass names it, and has since the day it was built:

```
$ python3 one_owner.py | grep plane_drift
one-owner: cli.py:376 label_names and plane_drift.py:31 issue_lifecycle read the same payload keys (labels, name) — one fact, one owner
```

**The archaeology, verified rather than inherited.** The seam and the copy
were created on the same day:

```
$ git show -s --format="%h %ad %s" --date=short 622e2bf f38fbdd
622e2bf 2026-08-10 refactor: land the 2026-08-05 architecture deepening — seams, renames, quick wins (wo-lbi) (#247)
f38fbdd 2026-08-10 feat(factory): wo:failed writer + cross-plane reconcile sweep (ADR-0045) (#204)
```

And `7650052` (#316) — the refactor whose stated purpose was collapsing a
duplicated rule into one owner — moved this one across untouched:

```
$ git show 7650052^:sweeps.py | sed -n '/^def issue_lifecycle/,/^$/p' > a
$ sed -n '/^def issue_lifecycle/,/^$/p' plane_drift.py > b
$ diff a b && echo "IDENTICAL"
IDENTICAL
```

## What is NOT claimed — there is no bug here

The two walks agree on every input `reconcile_drift` can hand them.
Driven over twelve label-entry shapes in every arrangement up to length
two, plus every malformed `labels` value and a missing key:

```
$ python3 probe_equivalence.py
missing labels key: [] [] agree
mismatches over all label-array shapes: 0
```

**One input does separate them, and it is unreachable.** `label_names`
accepts a bare list as its payload; `issue_lifecycle` calls
`issue.get("labels")` and would raise `AttributeError` on a non-dict.
`reconcile_drift` drops a non-dict entry with a `drift:` problem before
either walk is called (plane_drift.py:68-72), so no caller can reach it.
The fold therefore *widens* tolerance in the safe direction and narrows
nothing.

So the cost is not a wrong drift report. It is:

- **A standing pre-pass finding nobody can clear**, one of nine, in a tool
  whose whole value is that its output is short enough to read.
- **Two strictnesses for one rule**, one of them documented as a decision
  covering callers that are not honouring it — the exact shape that made
  the checked-row grammar need ADR-0058 four days after a run went hunting
  for it.
- **A stale record.** `tests/test_one_owner.py:786-789` calls this group
  "STILL OPEN at HEAD … this run's acceptance fixture rather than its
  cleanup target", which stops being true the moment it is folded.

Expected: one owner for the labels-array walk, as ADR-0037 decided.
Observed: two, one of them carried across by the refactor that was
collapsing the other.

## Why the copy exists

`plane_drift.py`'s module docstring says the module is PURE — *"the
listing arrives as data, so neither caller's runner reaches this file, and
no test here needs one"* — and `cli.py` is the module that shells out to
`gh`. Nothing records whether that purity claim was meant to forbid
importing the seam at all, or only to forbid running a subprocess. That is
the decision this run owes, and it is why re-entry is architect.
