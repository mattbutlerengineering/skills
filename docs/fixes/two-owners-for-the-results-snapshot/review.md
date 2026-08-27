---
stage: review
run: maintenance:two-owners-for-the-results-snapshot
date: 2026-08-27
assumptions: []
---

# Review: two owners for the results snapshot

Scope: the diff this run produced — `eval_schema.py` (+30),
`trigger_eval.py` (-6/+3), `charter_replay.py` (-5/+2),
`tests/test_eval_schema.py` (+46).

This review was written by the same agent that wrote the change.
ADR-0036 clause 2 is therefore unsatisfied: a non-authoring reviewer
must re-execute the verification and record it on the pull request
before this can merge.

## Correctness

**Minor — the refusal message diverges from `results_path`'s.** A
direct caller passing a kind that is neither a snapshot kind nor a
known results kind (`write_snapshot(out, dir, "bogus")`) now gets
`'bogus' results are not a single snapshot file` where `results_path`
would have said `unknown results kind 'bogus'`. Not reachable from
either `record`, both of which pass a literal. Deferred: two messages
for two questions is correct, and collapsing them would make the
snapshot writer restate the kind taxonomy it deliberately does not own.

**Checked, not a finding — the refusal happens before the mkdir.** The
kind check precedes `results_dir.mkdir`, so a refused call leaves no
directory behind. The old code had no such check, so this is new
behaviour, and it is the safer direction: nothing observable to the two
callers, which never reach it.

**Checked, not a finding — `output["date"]` still raises KeyError on a
payload with no date.** Unchanged from both original implementations;
this run did not widen or narrow it.

## Design

The change follows ADR-0024's own reasoning rather than extending it.
That ADR moved the naming grammar into `eval_schema` because "the
runner's record step held the only implementation", and set the rule
"one owner, thin callers". The serialisation half stayed behind in two
copies. Both `record` functions survive as two-line wrappers, which
keeps the existing test surface and the call sites unchanged.

**Observation, no change made — ADR-0024 contradicts itself about its
own status.** Its `Status:` field reads `accepted`; its closing
paragraph reads "Provisional because it widens an accepted ADR's rule
without an operator decision." Both cannot hold. This run relied on the
`Status:` field. Recorded here rather than edited: an ADR is superseded
or amended, never rewritten in place.

**Observation, no change made — `one_owner.py` cannot see this class of
duplication.** It compares stated values and payload-key reads, so two
structurally identical function bodies are invisible to it; this pair
was found by hand while confirming the `ROOT` finding it does report.
Not fixed here — `one_owner.py` is claimed by PRs #322 and #337, and
widening a detector is not this run's scope.

## Security

No new input surface. The written path still comes from
`results_path`, unchanged, so the containment properties of the results
tree are as before. No secrets, no external calls, no subprocess.

## Verdict

No critical findings. One minor, deferred with a reason above. The
blocking condition on shipping is ADR-0036 clause 2, not the diff.
