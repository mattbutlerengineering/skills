---
stage: prd
run: feature:idea-ambition-ladder
date: 2026-10-20
ux: not-applicable
ux-reason: "Skill text, a template, a suite and tests only; no screens or flows."
assumptions:
  - "Interview answered from autorun-brief.md in this directory and issue #994; no live interview held. The brief holds four Owner answers (drive #994; demo reaches launch-demo via the PRD; suite only with no paid run; prepare-and-stop release). Everything else traces to the brief's sections marked as the orchestrator's reading, to idea.md, or to the issue."
  - "No interview question this stage offered named options with a recommended default that the brief and issue left open, so no skill default was taken. No evidentiary question was left unanswered, so nothing was surfaced."
  - "This PRD is produced by the current prd skill, which has no demo hand-off line yet. The proposed hand-off is a requirement for the work, not applied to this document."
  - "No PRD id assigned: the prd skill and TEMPLATE.md assign none, and the brief rules out work-order mirroring."
  - "The user's framing is kept, per the brief: the ladder is anchored on the user's own words, and the rule against replacing their idea is not removed. How the skill text expresses that is left to Architect."
  - "How skill text, TEMPLATE sections and the PRD hand-off line are made testable; whether TEMPLATE.md changes affect protocol.py artifact checks or old idea.md files; how unchosen rungs reach docs/backlog.md in the ADR-0029 seed grammar and which tool, if any, writes it; how the with/without-plugin suite cases are checked for free; and what the scaled-down feature-run version contains are left to Architect as open questions (orchestrator instruction)."
---

# PRD: An ambition ladder for the Idea stage, with an achievable showstopper as the default

## Problem statement

Every brief the Idea stage produces comes out achievable but never
memorable. Nothing in the interview asks for the bigger, more presentable
version, so each run stays the size of the user's opening framing. The rule
"don't replace their idea with yours", "no solution design here" and a
single Solution hunch slot hold it there. Downstream, the launch-demo skill
has nothing worth recording when the brief named no demo moment.

No verified source shows that offering a ladder produces better briefs or
better shipped features. The evidence is the issue's own observation across
runs, labelled anecdote and unmeasured. This run authors the ladder and a
suite; it produces no measured delta.

## Solution

1. **`skills/idea/SKILL.md` gains an ambition-ladder step**, after the
   problem and evidence questions and before the solution hunch. It offers
   three rungs anchored on the user's own framing: Solid (fixes it, ships
   fast; the fallback), Showstopper (same problem plus one "wait, do that
   again" moment; recommended by default) and Moonshot (beyond this run's
   scale; saved as a seed, never chosen). The user picks; the pick is
   recorded. Feature runs get a scaled-down version.
2. **Four showstopper tests** and **three prompts** in that step: a
   30-second demo exists (before and after in two sentences, the after
   something seen); it removes a step rather than speeding one; it rests on
   something only this product has; it is achievable, with the riskiest
   piece named and a spike of about two days that could prove it, else it
   drops to the moonshot rung. Prompts: what would you show first in a
   demo; what does the user do today that they would never have to do
   again; what does the product already know that it is not using.
3. **`skills/idea/TEMPLATE.md` gains four sections**: Ambition rung, The
   demo, Riskiest piece + spike, Cheapest kill test.
4. **Unchosen rungs land in `docs/backlog.md` as seeds** in the existing
   seed grammar (ADR-0029). The moonshot is always one.
5. **The demo reaches launch-demo through the PRD** (Owner decision). The
   PRD of a run whose idea.md has a demo copies it into a success criterion,
   "the demo runs as written"; `verify` checks it. `skills/prd/SKILL.md`
   gains one line that carries the script forward. `launch-demo` is
   unchanged.
6. **A `plugin-evals/idea/` with/without-plugin suite** whose cases check
   that the brief names a showstopper passing all four tests, the user's
   framing is kept, and the moonshot is saved as a seed and not chosen.
   Authored and tested statically; never run.

No paid run, no `claude plugin eval` call, no `plugin-evals/records/`
entry, no LEDGER maturity change (ADR-0012, ADR-0019, ADR-0081).

## Actors

- **Owner**: runs the pipeline, picks the rung, decides any first paid run.
- **Idea-skill user**: anyone running `idea` on a product or feature run.
- **Idea skill**: the stage that runs the ladder and writes idea.md.
- **PRD skill / verify skill**: carry the demo into a success criterion and
  check it.
- **launch-demo skill**: downstream consumer; unchanged, reads only what
  ship produces.
- **Plugin-eval harness**: would run the suite; does not run it here.
- **Reviewer**: judges at the merge gate whether the tests guard anything.

## User stories

1. As an idea-skill user, I want the interview to offer Solid, Showstopper
   and Moonshot anchored on my own framing, so that I can choose a bigger
   version without losing my idea.
2. As the Owner, I want the showstopper judged by four stated tests, so that
   "wow" is not left to taste.
3. As an idea-skill user, I want the three prompts asked, so that I find the
   demo moment, the step removed and the unused knowledge.
4. As the Owner, I want the moonshot and any other unchosen rung saved as
   backlog seeds, so that bigger ideas are kept without being built.
5. As the Owner, I want idea.md to carry the chosen rung, the demo script,
   the riskiest piece with its spike, and the cheapest kill test, so that
   the next stage inherits them.
6. As the Owner, I want the demo carried through the PRD and checked by
   verify, so that launch-demo has a script that was true when the feature
   shipped, with no change to launch-demo.
7. As the Owner, I want existing idea.md files to keep validating, so that
   past runs are not broken by the template change.
8. As a Reviewer, I want the skill text, the template, the hand-off line and
   the suite pinned by offline tests, so that I can trust them without a
   live run.

## Success criteria

Each criterion is checked by a test asserting exact strings or a named
command's output. Exact wording is fixed by Architect.

- [ ] `skills/idea/SKILL.md` contains the ambition-ladder step, placed after
      the problem and evidence questions and before the solution hunch, and
      names the three rungs Solid, Showstopper and Moonshot with Showstopper
      marked as the recommended default. A test asserts the strings and
      their order.
- [ ] `skills/idea/SKILL.md` contains the four showstopper tests and the
      three prompts. A test asserts each of the seven by an exact phrase.
- [ ] `skills/idea/SKILL.md` states that the user's pick is recorded, that
      the moonshot is saved as a seed and never chosen, that an
      unachievable showstopper (no two-day spike) drops to the moonshot
      rung, and that feature runs get a scaled-down version. A test asserts
      each.
- [ ] `skills/idea/TEMPLATE.md` contains the four sections Ambition rung,
      The demo, Riskiest piece + spike and Cheapest kill test. A test
      asserts the headings.
- [ ] An idea.md written before this change, without those four sections,
      still validates under `protocol.py`'s artifact checks and `lint.py`.
      A test builds one and asserts no problem string.
- [ ] A seed line for an unchosen rung, written as the skill text
      instructs, passes the protocol's seed grammar (ADR-0029) and
      `python3 gates.py`. A test or gates run asserts it, and that the
      moonshot seed ends with the `(from: <run-ref>)` suffix.
- [ ] `skills/prd/SKILL.md` gains one line that tells the PRD to copy
      idea.md's The demo into a success criterion worded "the demo runs as
      written"; `skills/verify` is told by that criterion, not changed in
      behaviour; `skills/launch-demo` is byte-identical to main. A test
      asserts the line and a `git diff` against main shows no change under
      `skills/launch-demo/`.
- [ ] The `plugin-evals/idea/` suite exists, tagged `idea`, and is wired so
      `claude plugin eval . --tag idea` would select it, checked statically:
      a test reads the case files and the manifest's `experimental.evals`
      entry and asserts every case carries the tag and the layout matches
      the existing suites.
- [ ] The suite's cases cover the three checks (showstopper passes all four
      tests, user framing kept, moonshot saved as a seed and not chosen),
      each with a with-plugin and a without-plugin arm. A test asserts the
      cases and arms exist.
- [ ] No paid run: nothing in this change invokes `claude plugin eval` or
      any model. `LEDGER.md` is byte-identical to main, `plugin-evals/
      records/` gains no file, and `.claude-plugin/plugin.json`'s version is
      unchanged.
- [ ] No existing eval definition is edited: `git diff` against main shows
      no change to files under `evals/` or to the other `plugin-evals/`
      suites.
- [ ] `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
      `python3 gates.py` and `python3 gates.py --selftest` all pass.

## Out of scope

- Any paid run, a cited run under `plugin-evals/records/`, and any LEDGER
  maturity change. The issue's acceptance box for a cited run stays
  unchecked; it needs the Owner's own authorization and is a follow-up.
- Changing `skills/launch-demo` or having it read idea.md directly (the
  issue's rejected alternative).
- Choosing the moonshot rung, or building any moonshot.
- Measuring whether the ladder improves briefs or shipped features.
- A plugin version bump; the wave release PR is a follow-up (ADR-0095).
- Mirroring items to work orders; the PR body carries a `No work order:`
  line and closes #994.
- A new tool or shared module, unless Architect finds one is needed under the
  CLAUDE.md seam rule.
- Applying the ladder to this run's own idea.md or prd.md.

## Open questions

- How is skill text made testable here, given the repo asserts skill text
  through public interfaces (see the skill-text tests in
  tests/test_decompose_lessons.py)? Which strings are pinned and where do
  the tests live? For Architect.
- Do the new TEMPLATE.md sections affect `protocol.py` artifact checks or
  lint, and do old idea.md files still validate? For Architect.
- How do unchosen rungs get appended to `docs/backlog.md` in the ADR-0029
  seed grammar, and which tool writes it, if any, given the idea skill is
  text only? Idea is not a backlog producer today. For Architect.
- How are the with/without-plugin suite cases checked for free, offline,
  and what makes them discriminate once run? For Architect.
- What does the scaled-down feature-run version of the ladder contain, and
  is it light enough not to become ceremony? For Architect.
- Do the four tests guard anything, or can a hurried user or model always
  pass "only this product has it" and "removes a step"? Unproven; a known
  limit for Review.
- Does "drops to the moonshot" demote too much when no two-day spike can be
  named at the idea stage? For Architect, and a known limit for Review.
