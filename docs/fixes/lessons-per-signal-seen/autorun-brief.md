# Autorun brief: lessons-per-signal-seen

Not an artifact. Written 2026-10-23 by the orchestrator. The Owner asked
repeatedly to "keep going" after every real issue was closed, and chose
#1061 as part of the follow-up issues filed on 2026-10-22. This run drives
it. The Owner has not seen a design for it; the design below is the
orchestrator's reading of the review that deferred it. Merges are not
authorised by this brief: a green pull request waits for the Owner's own
answer.

Source: issue #1061 and `docs/features/decompose-lessons/review.md`
("Major (deferred): `seen` is per run, so a signal that matures later is
lost" and the four minors). The tool is `decompose_lessons.py` (shipped as
#1050) under ADR-0113.

## The defect (from the review)

`seen` takes every run that has an implement boundary. review.md is written
after Implement. If the Owner runs `update` between Implement and Review,
run R is folded into `seen` with its review signal unmeasurable. When
review.md lands, R's review hits are skipped (`pairs(skip=seen)`) and R can
no longer vote on review lessons. The loss is silent (an undercount).

## Scope: what this run changes

1. **Per-signal `seen`.** Replace the per-run `seen` set with one entry per
   (signal, run), so a run that is unmeasurable for one signal can still
   produce or vote on another when that signal matures. The on-disk shape
   changes (line 1 of the JSONL ledger is `{"seen": [...]}`), so this needs a
   NEW provisional ADR that supersedes ADR-0113's on-disk-shape decision
   (supersede, never rewrite; next free number on origin/main; update
   ADR-0113's status line and the ADR README row the way earlier
   supersessions did) and a load-time migration of the old per-run entries.
   No lessons file is committed on main yet, so the migration is a
   compatibility shim that must still be tested; decide with a logged
   assumption whether `load` accepts and upgrades the old shape or refuses it
   with a labelled problem (prefer the cheaper honest one, and say why).
2. **Zero-item treated pool.** A treated pool whose breakdowns hold zero
   items prints `0/0` as "not higher" although the rate is undefined. Make
   the line say the rate is undefined instead (a labelled, pinned string).
3. **File size bound.** `load` and the Decompose skill read the lessons file
   whole. Add a refusal above a named size constant, as a labelled problem
   (exit 1), set a clear multiple above any realistic file (a ledger of a few
   hundred short lines is a few tens of KB; measure what five lessons weigh
   and size the constant from that), same pattern as `MAX_RECORD_BYTES` in
   `eval_trends.py`.

## Explicitly not changed (stay documented decisions)

- Vote order: sequential voting is ExpeL's own rule and the original brief's;
  a net-sum rule would change a recorded semantic.
- Early exposure: commit the first lessons file only after the 0.22.0
  release is installed. This is operational, not code.

## Constraints

- Entry depth is Architect (the ADR). The rest of the maintenance run
  follows: capture the defect brief with reproduction, architect the change
  (including the ADR and the migration question), implement test-first,
  verify, review, ship.
- Stdlib only, root-only (no new import pair; dual-membership pin stays 55
  unless Architect proves otherwise), no network or model call, no paid
  run, LEDGER unchanged. `decompose_lessons.py` stays read-only on git
  history and never fetches.
- If `skills/decompose/SKILL.md` must change (it names the lessons file
  format), that is a skill change: record the wave release PR as a
  follow-up for the Owner, never edit `.claude-plugin/plugin.json`'s version
  on this branch (ADR-0095). Prefer no skill change; the skill reads lines,
  not the `seen` header.
- No permanent test may assert a path is "unchanged against main".
- Reproduce the defect for real in a scratch clone (never write
  `docs/factory/decompose-lessons.jsonl` in this repo), quoting commands and
  output.
- The PR closes #1061 (`Closes #1061`) and says plainly what was fixed and
  what stayed a documented decision. `No work order:` line in the body.

stop-after: ship
