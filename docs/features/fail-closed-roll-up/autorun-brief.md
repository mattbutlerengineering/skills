# Autorun brief: fail-closed-roll-up

Not an artifact. Written 2026-10-17 by the orchestrator. The Owner invoked
`/idea-to-prod:autorun` with no description. No run was mid-pipeline, so
the Owner answered five questions one at a time in session, each taking
the recommended option:

1. What to drive: "Fail-closed roll-up (Recommended)", the backlog seed
   at `docs/backlog.md` line 118 (from: session:2026-10-16), which is
   recommendation 3 of `docs/research/rea-learnings.md`.
2. Scope: "Docs + gate (Recommended)". The vocabulary and rule go in the
   docs and templates, and detector H learns the summary half.
3. Already-shipped artifacts: "Grandfather by date (Recommended)".
4. Release: "Prepare and stop (Recommended)".
5. Operate: "After first real judgment (Recommended)".

Everything else below is the orchestrator's reading of the seed, the
research note and the repo, and is marked as such. A stage that needs an
answer this brief does not hold applies the autorun rule: take a
skill-supplied default and log it, or else stop and surface.

## What and why

Name the kinds of claim a verification or review artifact makes, and
state one roll-up rule: **unknown, unsupported, truncated and skipped
never aggregate to pass.** Then make detector H enforce the summary half
of that rule on `verification.md`.

Detector H (`gates.evidence_problems` / `check_evidence_honesty`) already
enforces the per-section half. Every section with a labelled verdict
needs a fenced evidence block or a NOT-RUN disclosure. Nothing states or
checks that a `## Summary` claiming a pass must not paper over a section
that disclosed NOT RUN, skipped or unknown.

## Idea-stage inputs

- **Problem, from the sufferer's view.** A reader (the Owner at a merge
  gate, Ship's pre-flight, or a later Review) reads a verification
  Summary as "all criteria pass" and acts on it. Further down, a section
  says the check was not run. The Summary is the line people read, and
  it is the one line nothing checks.
- **Who has it, and how they cope today.** Everyone who reads a
  verification.md: the Owner, Ship (whose pre-flight asks whether
  "verification has no unresolved failures"), Review, and the merge
  train. Today they cope by reading the whole artifact, and by verify
  authors who disclose counts on their own initiative (for example,
  `docs/fixes/toolsmith-mine-pr-permissions/verification.md` reads
  "7 PASS, 0 FAIL, 2 NOT YET VERIFIABLE").
- **Why now.** The merge train and the hourly improvement routine
  (2026-10-15) read and produce artifacts unattended, with no Owner
  reading the whole file. The research note (2026-10-16) found that no
  rule states the summary half.
- **Evidence (orchestrator's reading, measured 2026-10-17; partly
  unverified).** The research note says the hole exists but marks it
  "unverified against the gate's code paths". A rough grep over the 77
  tracked `verification.md` files found about 10 whose Summary mentions
  a pass while the body mentions NOT RUN, skipped or unknown. A hand
  sample of four found **no confirmed instance** of a Summary claiming
  an unqualified pass over a disclosed criterion. Each one either counted
  its gaps in the Summary or disclosed them outside any criterion (under
  "Not verified"). So the evidence is a reasoned gap plus a rough count,
  not an observed failure. The Idea stage must count over all 77 with a
  stated method and report the real number, zero included. A small or
  zero count is a legitimate finding, not a reason to inflate. The case
  for the gate then rests on prevention under unattended authors, and
  Idea should say so plainly.
- **Rough shape of a solution (a hunch).** (a) `CONTEXT.md` gains the
  claim kinds (observed: quoted output; derived: computed from observed;
  inferred: judgement; unknown: not examined) and the roll-up rule.
  (b) `docs/pipeline-protocol.md` states the rule once. (c) The
  `## Summary` of `skills/verify/TEMPLATE.md` and the `## Verdict` of
  `skills/review/TEMPLATE.md` say a Summary or Verdict counts its
  NOT RUN / unknown items and never reads as an unqualified pass over
  them. (d) Detector H gains one rule: on a `verification.md` dated on
  or after a cutoff, if any criterion section carries a NOT-RUN
  disclosure (H already parses this), the Summary must name that count
  or kind, and must not assert an unqualified pass. The exact grammar is
  Architect's call.
- **Success, in one sentence.** A new verification.md whose Summary
  reads as a full pass while one of its criteria disclosed NOT RUN fails
  `python3 gates.py`, and no artifact shipped before the cutoff does.
- **Biggest unknowns, and how this dies.** (a) The Summary is free
  prose, so a grammar that judges "asserts an unqualified pass" can
  false-positive on honest Summaries, or be dodged by rewording. A rule
  that teaches authors to dodge it is worse than none. (b) The zero-count
  outcome above. (c) Mirroring: `gates.py` ships into the payload, so a
  new H rule reaches stamped repos and needs the manifest regenerated
  (CLAUDE.md, `factory_init.MIRRORS`). (d) Review artifacts are not
  gated by H. The rule reaches review.md through its template only.

## Scope

In:

- the claim-kind vocabulary and the roll-up rule in `CONTEXT.md` and
  `docs/pipeline-protocol.md`;
- the verify template's Summary guidance and the review template's
  Verdict guidance (plus each skill's SKILL.md wherever it describes
  writing those lines);
- one new detector H rule over `verification.md`, with tests asserting
  the exact problem strings through the public interface (CLAUDE.md
  problem-string contract), its payload mirror, and the regenerated
  manifest;
- the grandfather cutoff (Owner decision 3): a single named constant
  compared with the artifact's frontmatter `date:`, pinned by a test. An
  artifact with no readable date is Architect's call, logged;
- an ADR recording the rule and the cutoff (provisional, since it is
  written unattended).

Out:

- rewriting any shipped verification.md or review.md (Owner decision 3);
- gating review.md mechanically;
- the other rea-learnings recommendations (known-answer evals, close-out
  questions, the regression-test rule);
- changing H's existing per-section rule.

## Success criteria

- A fixture verification.md, dated on or after the cutoff, with one
  criterion disclosing NOT RUN and a Summary reading as a full pass
  fails `python3 gates.py` with an exact `H:` problem string.
- The same fixture passes when its Summary counts or names the NOT RUN
  item, as does one with no disclosed sections.
- The same failing shape dated before the cutoff passes.
- `python3 gates.py` reports 0 problems on main's real tree after the
  change. Every shipped artifact passes, with none edited.
- `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
  `python3 gates.py && python3 gates.py --selftest` all pass, and
  detector E (manifest) is clean after `factory_init.py update-manifest`.

## Constraints and already decided

- Stdlib only. Problem-string contracts. One owner per fact: the
  vocabulary lives in `CONTEXT.md`, and other files point to it.
- The H rule reuses H's existing section parse
  (`verification_sections`, `_is_disclosure`). It must not be a second
  parse.
- Feature branches never touch `.claude-plugin/plugin.json`'s version
  (ADR-0095). Skill templates change, so a `chore(release)` PR follows
  the wave. That is the Owner's, after merge.
- Gates scan every repo markdown, so examples in docs must not carry
  literal four-digit work-order or PRD ids
  (`docs/kb/gates-scan-every-doc.md`).

## Tracker

No issues seed the run, and there is no tracker interaction before Ship.
At Ship, file one plain `type:feature` issue for the run, close it from
the PR with `Closes #N` (one keyword per issue), and include a
`No work order:` line. The PR body must pass the `pr_body_preflight.py`
hook. Run `gh pr create` as the first command of its Bash call, with the
body file written in an earlier call.

The Idea stage also claims the seed: it appends
`(claimed: feature:fail-closed-roll-up)` to `docs/backlog.md` line 118.
That edit is committed with idea.md.

## User-facing surface

None in the UX-stage sense. These are docs, templates and a gate rule.
The PRD's `ux:` decision is expected to record it as not required.

## Release authorization

Prepare and stop (Owner decision 4). Ship pushes the branch, opens the
PR, records `outcome: prepared` with `pending-merge: <PR url>`, and
stops. No merge, tag or version bump. The orchestrator asks the Owner
about the merge after the run.

## Operate

minimum-signal: the first verification.md written after this PR merges
that the new H rule judges (it passes or it is refused). It is counted
from the repo, never from this brief.

stop-after: ship
