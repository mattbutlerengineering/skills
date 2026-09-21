# Autorun brief — a crashed run is recorded as a no-fire

## Provenance (read this first)

**No user-supplied brief exists for this run.** The instruction was
`/idea-to-prod:autorun` with no defect named. This brief was authored
from the session's own investigation, searching for work that is both
evidenced and conflict-free against the 17 open pull requests.

Every "requirement" below is the author's inference. Where the pipeline
would interview, this brief substitutes measurement: the defect is
demonstrated before it is described.

## The work

A maintenance run against `trigger_eval.py`. A worker that crashes is
recorded as a run in which the router legitimately fired nothing, and the
recorded results file carries no trace that anything failed.

- **Run scale:** maintenance, slug `a-crashed-run-is-recorded-as-a-no-fire`.
- **Re-entry depth:** `implement`. The fix is additive — a new field on a
  recorded record — and changes no existing value or semantic, so there
  is no design question to route through Architect. The one decision that
  *would* have been design-touching was deliberately excluded from scope
  (see Scope, out).

## Scope

**In.** `trigger_eval.py` — `run_eval`'s per-future error accounting,
`score_case`'s record, and `summarize`'s totals. Tests through the
existing free seam in `tests/harness_contract.py`.

**Out.**

- **Penalising a case for having *some* errors.** Whether a case with
  three good runs and one crash should be marked down — a minimum-
  observation threshold, or failing any case that errored at all — is a
  real policy question with no default this skill supplies. Out of
  scope, recorded as a follow-up in `defect.md` Notes.

  Note what is deliberately **in** scope, after a correction made during
  implementation: a crashed run does not enter the `fired` Counter at
  all. An earlier draft of this brief tried to keep failures out of the
  scoring denominator as a separate concern, and that was wrong. The
  `fired` Counter is not only a scoring input — `summarize` feeds it
  straight into the **confusion matrix**, which is a record of observed
  routing behaviour. Writing a crash into it records an observation that
  never happened. Excluding crashes is therefore part of not fabricating
  evidence, not a scoring preference to defer.
- Any change to files already recorded under `evals/results/`. That tree
  is append-only and this run does not write to it.
- Running `trigger_eval.py` against a real harness. It costs model spend
  and this session never does it. The fake-binary seam in
  `tests/harness_contract.py` is free and is what the run uses.
- `charter_replay.py`, `lint.py`, `cli.py` — three defects found earlier
  in this session, each deferred for a recorded reason.

## Success criteria

1. A run that fails is not counted as a run in which nothing fired.
2. The recorded output states how many runs failed, per case and in
   total, so a reader of an append-only snapshot can tell a routing
   result from an infrastructure result.
3. No existing recorded field changes meaning or value when there are no
   failures — old snapshots stay readable and comparable. When there
   *are* failures, `runs` becomes the number of observations actually
   made, and a case with no successful runs does not pass.
4. The confusion matrix contains no entry derived from a crashed run.
5. The repo battery is green.

## Constraints already decided

- Stdlib only.
- `trigger_eval.py` is not in `factory_init.MIRRORS`, so no manifest
  regeneration. Verified, not assumed.
- Eval honesty is non-negotiable: no eval definition is edited to make a
  case pass, and no results file is rewritten.

## Release authorization

**None given.** Ship prepares and stops: pre-flight and `release.md`, no
merge, no tag, no PR opened. The 17-PR queue is held pending human
review and this run does not add to it.
