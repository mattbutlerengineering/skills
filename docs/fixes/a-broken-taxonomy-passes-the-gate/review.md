---
stage: review
run: maintenance:a-broken-taxonomy-passes-the-gate
date: 2026-08-30
---

# Review — a broken taxonomy passes the gate

Scope: the run's own diff (`git diff origin/main...HEAD`) — `gates.py`,
`label_sync.py`, their payload mirrors, `factory/manifest.json`, and the
two test suites. Reviewed against ADR-0032 (one-way dispatch mirror),
ADR-0048 (artifact-path candidates), and the repo's problem-string
convention.

## Correctness

**No critical findings.**

Checked, with the failure scenario each check was looking for:

- **An unstamped repo becomes noisy.** Scenario: a repo with no
  `labels.json` in either candidate home runs `make check` and is told
  `L: missing labels.json (...)` — a finding about a file it has no
  reason to have. Does not occur: `taxonomy_path(root) is None` returns
  before `load_labels` is called, and both the selftest's `J unstamped`
  fixture and `test_a_tree_with_no_taxonomy_is_silent` assert it.
- **A partial stamp crashes the gate.** Scenario: `tools/factory/`
  exists but `label_sync.py` does not, and `gates.py` raises
  `ImportError` before any detector runs. Unchanged: the lazy import and
  its `except ImportError: return []` are untouched and still precede
  everything new.
- **The wiring findings change.** Scenario: a curated taxonomy that
  prunes a label produces different strings than before, breaking a
  consumer that greps them. Does not occur: the `J:` string is
  byte-identical and its two exact-string tests
  (`test_a_pruned_label_is_reported_against_every_site_that_names_it`,
  `test_a_pruned_tool_label_is_reported_without_any_makefile`) are
  unchanged and pass.
- **A file that fails to parse floods the output.** Scenario: a corrupt
  taxonomy yields one `L:` line plus fifteen `J: ... no such label`
  lines, burying the one line that explains why. Does not occur:
  `if not taxonomy: return problems` short-circuits, and
  `test_an_unreadable_taxonomy_is_reported_not_a_traceback` pins the
  result as a single-element list.
- **`load_labels` behaviour drifts under the extraction.** Scenario:
  the missing-taxonomy message names a different set of homes after
  `candidates` moved into the branch. Does not occur: the same
  `artifact_paths(root, "labels.json")` call produces it, and
  `test_missing_everywhere_is_flagged` compares against the module-level
  `MISSING_PROBLEM` constant, unchanged.

## Design

**Minor — the `L:` prefix inside `gates` output.** Detector L is
documented as a network detector "NEVER wired into gates.py CHECKERS",
so an `L:`-prefixed line in `make check` output invites the reading that
it now is. Two things make this the right call anyway, and both are
written into the code: `sweeps.py` faced the identical question at the
identical seam and recorded "forwarded as they arrive, since a broken
taxonomy is that detector's finding, not ours"; and restamping the
strings with J's letter would put the taxonomy-shape message text under
two owners. The comment in `check_label_wiring` says explicitly that
forwarding the strings is not wiring L's network half into CHECKERS.
**Accepted, not deferred** — the alternative is worse.

**Minor — `artifact_paths` is walked twice on the missing path.**
`taxonomy_path` walks it to find nothing, then `load_labels` walks it
again to name the homes. Cold path only (it runs when there is no
taxonomy at all), and the alternative — returning the candidate list
from `taxonomy_path` — would make it answer two questions instead of
one. **Deferred**, reason: the duplication is one `is_file()` sweep over
two paths, and collapsing it costs the helper its single purpose.

**Minor, fixed during review — a dead restore in the selftest.** The
first draft wrote the good taxonomy back and then the pre-existing line
wrote it again. The unchecked one was removed and the surviving restore
is now asserted (`expect_clean("J restored", ...)`), so the later
fixtures' dependency on it is stated rather than assumed.

**Minor, fixed during review — an over-broad docstring claim.** The
draft said J is "the only offline reader of the installed
`.github/labels.json`". `validator.py lifecycle` also reads it without
touching the network — but it runs in the dispatch plane, which is the
moment J exists to precede. Sharpened to "the only reader ... that runs
BEFORE the dispatch plane", which is the claim the run actually
establishes.

**Deviation check.** No architecture contract changed. `load_labels`'s
signature and return shape are unchanged; `taxonomy_path` is additive.
The four other callers were read and none is affected — they never asked
this question.

## Security

Nothing new reaches the network, the filesystem outside the repo root,
or a subprocess. `taxonomy_path` performs `is_file()` on paths
`factory_config.artifact_paths` already produced and `load_labels`
already opened. No secret, token, or credential is touched. The
reproduction script lives in the scratchpad and is not committed.

## The pinning test

`test_an_unusable_taxonomy_is_silent_not_a_traceback` asserted the
defect deliberately. Replacing a deliberate pin is a decision, not a
cleanup, so the reasoning is recorded in `defect.md` and in the new
test's docstring: the name bundled two properties, "not a traceback" is
the requirement, and "silent" does not follow from it. The
not-a-traceback half is preserved — the replacement drives the same four
payloads through the same public checker and would still fail on a
raise.

## Minor, found and fixed after the first push

**The doctor checklist described only J's old half.**
`skills/doctor/SKILL.md` step 4 explains what E, F and J report, so an
operator can place a problem string without re-deriving it. Its J
paragraph ended "Adding labels stays free — J looks in one direction
only", which stays true of the wiring check and says nothing about the
`L:` lines J now forwards. Scenario: an operator runs doctor against a
stamped repo with a corrupt taxonomy, sees an `L:` line under
`gates: 1 problem(s)`, and reads it as the networked label-sync sweep
having somehow run inside the offline gate — the one reading the
paragraph exists to prevent. Fixed in the same PR rather than a
follow-up, because a checklist that describes a detector's behaviour is
part of that behaviour's change.

**Deferred: no mechanical pin for that paragraph.** Doctor's target list
and workflow list are pinned both ways because both are derivable
enumerations. This is prose about meaning, and the only cheap pin —
"the paragraph mentions `L:`" — would pass on any sentence containing
those characters. Deferring rather than adding coverage-shaped noise;
recorded in `verification.md` §9.

## Verdict

No critical findings. Two minors accepted with reasons, one minor
deferred with a reason, two minors found and fixed inside this run.
Ready for Ship.
