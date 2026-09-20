---
stage: capture
run: maintenance:closed-intake-mutes-the-detector
date: 2026-08-25
re-entry: architect
assumptions: ["The seed was checked before it was claimed and one of its claims is stale: the label drift it says is still live has been fixed. Recorded here rather than repeated, because a run that inherits its brief's evidence unread is how a stale number becomes a shipped one — which is itself backlog seed 58.", "Severity is stated as a SILENT hole, not a current outage. Neither detector has anything to report today, so nothing is being missed right now. What is broken is the guarantee: the next time either detector finds drift, the sweep files nothing and says the same words as a clean run.", "re-entry is architect because known_keys' docstring defends deduping across every issue state at length and this run narrows that rule. A documented decision gets amended in writing, not edited in passing."]
---

# Defect: a closed intake mutes its detector forever

Origin: backlog seed `docs/backlog.md:35` (from: session:2026-08-21),
claimed as `(claimed: maintenance:closed-intake-mutes-the-detector)`.
Tracking issue #338.

## The rule, and where it stops being right

`known_keys` (sweeps.py:331) collects intake keys from every issue on the
board and `file_issues` drops any plan whose key is already there:

```python
    read = gh_read(["issue", "list", "--state", "all", "--json",
                    "number,body"], "gh issue list", label="sweeps",
```

The docstring defends `--state all` explicitly, and for its own case the
defence is correct:

> EVERY state, not just open. A maintainer who triages `[sentry] PROJ-7K` and
> closes it (wontfix, known, tracked elsewhere) has answered it — but Sentry
> still calls the error unresolved, so it leads the payload again next week.
> Deduping against open issues alone would re-file it every Monday, forever:
> exactly the human-transcription churn this sweep exists to remove, inverted.

Every word of that is about a signal **an outside source keeps re-reporting**.
Two of the three intake kinds have no outside source. Nothing re-reports
them but this repo's own detectors, and each uses a fixed singleton key:

```
sweeps.py:164          key = f"sentry:{short_id}"
sweeps.py:188          key = "sweep:label-drift"
sweeps.py:208          key = "sweep:reconcile"
```

A per-error key deduped across all states is a maintainer's answer being
respected. A **singleton** key deduped across all states is a detector that
can fire exactly once in the repository's lifetime.

## Both detectors are already spent

Every intake key on the board today, with the state of the issue carrying
it:

```
$ gh issue list --state all --limit 500 --json number,state,body \
    --jq '... select(startswith("intake-key:")) ...' | sort | uniq -c
   1 intake-key: sweep:reconcile  #295  CLOSED
   1 intake-key: sweep:label-drift  #173  CLOSED
```

Two intakes, two singleton keys, both closed. So:

- the **label-taxonomy** detector can never file again, and
- the **reconcile** detector — the ADR-0032 cross-plane rule, the one that
  catches the knowledge plane and the dispatch plane disagreeing — can never
  file again.

#173 was filed 2026-07-27 and closed COMPLETED on 2026-07-28:

```
#173 CLOSED/COMPLETED created=2026-07-27T10:08:10Z closed=2026-07-28T22:31:16Z
[sweep] label taxonomy drift (3 problem(s))
```

## What this looks like when it bites

Nothing. That is the defect.

```
$ python3 sweeps.py reconcile
sweeps: 0 issue(s) filed, 0 problem(s)
exit=0
```

A suppressed intake and an empty sweep print the same line and exit the
same way. The only way to tell them apart is to read the workflow log, and
there is nothing in the log to read either — the plan is dropped by a set
membership test, not by anything that reports.

## Correcting the seed

The seed says `python3 label_sync.py` "still prints the same three
byte-identical lines 24 days later". As of today it does not:

```
$ python3 label_sync.py
label-sync: 0 problem(s)
exit=0
```

The `size:` label descriptions were brought back into line at some point
after the seed was written. The seed's *mechanism* is unaffected — an intake
stays deduped whether or not its condition currently holds — but this run
does not get to claim a live drift instance, and does not.

The sharper fact the seed did not have is the one above: **both** detectors
are spent, including reconcile, which the seed never mentions.

## What is not wrong

- **Sentry dedupe is correct and stays.** The docstring's reasoning is
  sound for a source that re-reports.
- **The window rule is correct and stays.** A full `LIST_WINDOW` listing is
  reported precisely because past it old keys are invisible and their intake
  is re-filed as a duplicate.
- **Nothing is being missed today.** Both detectors report clean:

```
$ python3 -c "from pathlib import Path; import sweeps; print(sweeps.reconcile(Path('.')))"
([], [])
```

  So a fix files no issue immediately. It restores a guarantee rather than
  draining a queue.

## Re-entry

`architect`. The change is a few lines, but it narrows a rule whose
justification is written down and argued. The design artifact has to say
which keys keep the old rule, which lose it, and what happens when the
listing cannot answer the question — none of which is a code detail.
