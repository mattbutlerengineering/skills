# Autorun brief: a-zero-count-names-nothing

Not an artifact. Written 2026-10-17 by the orchestrator. The Owner invoked
`/idea-to-prod:autorun` with no description. No run was mid-pipeline, so
the Owner answered four questions one at a time in session, each taking
the recommended option:

1. What to drive: "0 NOT RUN gap (Recommended)", the backlog seed at
   `docs/backlog.md` line 125 (from: feature:fail-closed-roll-up), raised
   by that run's retro (`docs/features/fail-closed-roll-up/retro.md`).
2. Fix shape: "Zero doesn't name (Recommended)".
3. Release: "Prepare and stop (Recommended)".
4. Operate: "Skip (Recommended)".

Everything else below is the orchestrator's reading of the seed, the
retro and the code, and is marked as such. A stage that needs an answer
this brief does not hold applies the autorun rule: take a skill-supplied
default and log it, or else stop and surface.

## Run scale

Maintenance (fix) run at `docs/fixes/a-zero-count-names-nothing/`,
entering at Capture. It is a defect: detector H's roll-up rule
(ADR-0107) is switched off by the count shape its own verify template
teaches.

## Capture inputs

- **What is broken.** `gates._rollup_problems` returns `[]` whenever any
  `## Summary` section has `names_unknown` set, and `names_unknown` is set
  by any unfenced `SUMMARY_UNKNOWN_TERM` match. "11 PASS, 0 FAIL, 0 NOT
  RUN" matches on "NOT RUN", so a Summary that says zero items were not
  run counts as having named the item, even when a criterion section's
  `- Result:` is a NOT RUN disclosure. The stale-Summary drift the rule
  targets (a criterion re-run and dropped to NOT RUN, the Summary left as
  written) slips through.
- **Reproduction.** Capture must reproduce this for real, not cite the
  retro. The retro's probe: take
  `docs/fixes/a-quoted-date-dodges-the-cutoff/verification.md`, flip
  criterion 9's `- Result:` to `NOT RUN — probe` in memory, and run H
  through its public function: `[]` with the Summary unchanged, the
  roll-up problem with the "0 NOT RUN" count removed. Re-run it and quote
  both outputs. A scratchpad script from that retro may still exist at
  `/private/tmp/claude-501/-Users-mbutler-github-skills/61791cec-ce5d-4fbf-a8e5-60dc748e0ec7/scratchpad/judge.py`;
  re-derive it if not.
- **Evidence it bites today.** None on main (orchestrator's reading, from
  the retro): the rule judges two artifacts and both have 0 disclosures.
  This is prevention. Capture should say so plainly and re-check over
  every tracked verification.md dated on or after ROLLUP_ADOPTED.
- **Root cause (hypothesis).** `names_unknown` is a word-presence test,
  and a count of zero is a word that says the opposite of naming.
- **Blast radius.** `gates.py` and its payload copy
  (`factory/templates/tools/factory/gates.py`, manifest-pinned). Only a
  Summary whose only unknown-kind mention follows a zero changes
  outcome, and only when a criterion is disclosed. No artifact on main
  changes outcome; prove it with `python3 gates.py` on the real tree.
- **Re-entry depth.** Orchestrator's reading: `re-entry: implement`. The
  shape is decided (Owner decision 2), and the change sits inside the
  existing section parse. If Capture finds a real design question, it
  chooses `re-entry: architect` and logs why.

## Fix shape (Owner decision 2)

An unknown-kind term directly preceded by a zero count does not set
`names_unknown`. A zero count is `0` or `zero`, optionally followed by a
separator such as a space or hyphen. Every other mention still names,
including "1 NOT RUN", "2 skipped" and "criterion 4 was not run", so an
honest Summary that passes today keeps passing. Out: comparing counts
with the number of disclosed sections (the rejected "count must match"
option). It is logged here so the decision is recorded.

The orchestrator leaves the exact grammar to Implement, logged. It
should cover at least "0 NOT RUN", "0 not run", "zero skipped" and
"0 N/A", and decide whether "no criteria were skipped" counts as a zero
(recommended: yes, if it is cheap and tested; otherwise record it as an
accepted limit).

## Scope

In:
- the `names_unknown` change in `verification_sections` (or a helper it
  calls), keeping one section parse;
- failing-first tests through the public interface, with exact problem
  strings: the retro's probe as a fixture, each zero shape refused when a
  criterion is disclosed, each zero shape still passing with no
  disclosures, and a non-zero count still passing over a disclosure;
- the payload mirror and `python3 factory_init.py update-manifest`;
- the verify template's Summary guidance (`skills/verify/TEMPLATE.md`
  line 11) saying a zero count does not name a disclosed criterion, if
  Implement finds its current wording teaches the dodge;
- a provisional ADR succeeding ADR-0107's naming clause, as the seed
  asks, with its row in `docs/adr/README.md`. If Implement finds the
  protocol prefers an amendment line on a provisional ADR, it logs that
  choice instead;
- marking backlog line 125 claimed:
  `(claimed: maintenance:a-zero-count-names-nothing)`.

Out: changing ROLLUP_ADOPTED (no judged artifact changes outcome, so the
existing cutoff stands); the other three seeds from the retro (lines 126
to 128); H's per-section rule; rewriting shipped artifacts.

## Success criteria

- The retro's probe (a criterion flipped to NOT RUN under a "0 NOT RUN"
  Summary) returns H's existing roll-up problem string where it returned
  `[]` before.
- Each zero shape the fix covers is refused over a disclosed criterion,
  and passes with no disclosures.
- "1 NOT RUN" and other non-zero or named mentions still pass over a
  disclosure, and all of H's existing tests pass unchanged.
- `python3 gates.py` reports 0 problems on main's real tree with no
  shipped artifact edited.
- `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
  `python3 gates.py && python3 gates.py --selftest` all pass, and
  detector E is clean after `update-manifest`.

## Constraints

Stdlib only. Problem-string contracts. Never touch
`.claude-plugin/plugin.json` (ADR-0095). Delete stray `.orig`/`.rej`
before `update-manifest`. Gates scan every markdown file, so write no
literal four-digit work-order or PRD-style id that does not exist.

## Tracker

No issues seed the run, and there is no tracker interaction before Ship.
At Ship, file one plain `type:defect` issue, close it from the PR with
`Closes #N`, and include a `No work order:` line. Run `gh pr create` as
the first command of its own Bash call, with the body file written in an
earlier call, so the preflight hook judges it.

## User-facing surface

None.

## Release authorization

Prepare and stop (Owner decision 3). Ship pushes, files the issue, opens
the PR, records `outcome: prepared` with `pending-merge:`, and stops. No
merge, tag or version bump.

## Operate

skip. The Owner decided this run gets no retro (decision 4). It is
prevention with no signal expected in this repo; backlog line 128 tracks
the stamped-repo measurement. The run stays active.

stop-after: ship
