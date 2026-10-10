---
stage: review
run: feature:lean-and-polish
date: 2026-10-10
assumptions:
  - "Review scaled to the blast radius: two new instruction files that nothing calls, roster entries pinned by lint, and a version bump. The skills' process content was read for convention conformance and for anything that contradicts the protocol, not re-litigated on taste. Taken without user input."
---

# Review: lean and polish

Diff reviewed: `git diff origin/main...HEAD` — 24 files, 1465 insertions,
9 deletions, of which 874 lines are the two skills and their references
carried verbatim from WIP commit 18b5e10.

## Defects

None found.

- **Merge resolutions.** Each conflict kept both sides: main's
  `launch-demo` sits beside `lean` and `polish` in `UTILITY_SKILLS`, its
  mirror, `plugin.json`'s utility list and `LEDGER.md`; the routing file
  gains 139 lines and loses none (verification.md, Up to date).
- **Protocol fit.** Neither skill reads or writes `docs/backlog.md`
  (both say a seed is the user's to file), which keeps the protocol's
  "no other skill reads the backlog" rule; neither claims a stage
  artifact, a soft gate or a `next stage is` hand-off; both route
  out-of-lane findings to existing skills by name in prose, which is
  advice to the user, not an operative hand-off.
- **Licences.** The references credit Ponytail (MIT) and Impeccable
  (Apache-2.0) and say the text is a restatement, not a copy; both
  licences confirmed against the GitHub API on 2026-10-10.

## Design

- The figure card choice ("Reshaping what's built") is recorded in
  architecture.md with the option that lost. `lean`'s build-time ladder
  arguably also belongs "Before a run exists"; a skill appears once on
  the figure, so the card names its more distinctive mode (cut-list).
- README: the attribution sentence the WIP prose carried is kept as one
  short paragraph under main's table, since a table cell has no room
  for it.

## Security

No executable code changes besides one list literal in `protocol.py`
(and its mirror). No secrets, no network calls, no new dependency.

## Follow-ups

- The routing eval is owed (paid). Until it runs, the 21 new cases are
  unscored and both LEDGER rows stay draft.
- Issues #624, #626 and #627 are untouched; a later gap analysis decides
  what they still need on top of these skills.
