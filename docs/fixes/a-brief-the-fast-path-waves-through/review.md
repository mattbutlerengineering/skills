---
stage: review
run: maintenance:a-brief-the-fast-path-waves-through
date: 2026-11-03
---

# Review: the fast path waves through a brief edit

## Scope

`git diff origin/main...HEAD` (base `57db41b`): code commit `d5adfab`
(`fast_path.py`, `tests/test_fast_path.py`, `.claude/implement-queue.md`,
ADR-0121 status line, new ADR-0122, ADR index row, backlog claim), plus
the run's artifacts (`autorun-brief.md`, `defect.md`, `verification.md`,
11/11 PASS). Predecessor `verification.md` exists, so no soft-gate
inversion. Maintenance patch, so a light pass: Verify's regression tests
are the floor and were not re-run; I probed the matcher and read the
producing boundary and its consumers.

## Findings

### Minor: the profile glob `**/autorun-brief.md` is not proven to match a root-level brief, and the pin test cannot say

- Scenario: the classifier matches by basename, so root-level
  `autorun-brief.md` is a gate path. The profile spells that
  `**/autorun-brief.md`. Probe: `fnmatch("autorun-brief.md",
  "**/autorun-brief.md")` is `False`, `PurePath.full_match` is `True`;
  `skills/implement-queue/SKILL.md` names no glob dialect. The pin test
  (`test_the_profile_gate_paths_equal_the_classifiers_list`) compares
  the two lists as strings, so it proves the spellings agree, not that a
  matcher reads them alike. The effect today is nil: the classifier
  already sends every non-`docs/` path (including a root brief) to
  review (`classify`: `not path.startswith("docs/")`), and `**/prd.md`
  and `**/architecture.md` carry the identical ambiguity. The
  disagreement is latent, not live, and it is the territory of the
  backlog item "settle how implement-queue obtains its changed-file
  list", which ADR-0122 names as out of reach.
- Standard: none
- Decision: deferred — pre-existing glob spelling shared with two older
  entries; no behaviour differs; the open backlog seed owns the
  GitHub-side matcher.

### Minor: the basename match is case-sensitive

- Scenario: probe `classify(["docs/x/Autorun-Brief.md"])` returns
  `low-risk`. On a case-insensitive checkout (macOS, Windows) a docs-only
  PR adding that spelling next to an existing `autorun-brief.md` would
  collide with it on a resume's machine, with no human merge. Requires a
  case-insensitive resume host and a deliberately hostile PR; `prd.md`
  and `architecture.md` behave the same, and the tests do not pin the
  choice either way.
- Standard: none
- Decision: deferred — same stance as the older basenames; widening one
  entry would make the three disagree. Not worth its own ADR.

## Passes with no findings

- **Correctness.** Probes of `is_gate_path`/`classify`:
  `autorun-brief.md` (root) → review; `a/autorun-brief.md` → review;
  `docs/x/autorun-brief.md/notes.md` (a directory named like the brief)
  → low-risk, correct, since that file is not the brief;
  `docs/x/autorun-brief.md/autorun-brief.md` → review;
  `autorun-brief.md ` (trailing space), `autorun-brief-notes.md`,
  `my-autorun-brief.md` → low-risk, correct. A backslash path is review
  only because it is outside `docs/`; git emits `/`, so moot. Renames
  both ways are covered by the real-git tests via `--no-renames`. Other
  paths: the diff to `is_gate_path` is one tuple entry, so prefix and
  file behaviour is unchanged (existing tests pass per `verification.md`).
- **Design.** The tuple entry follows the `prd.md` pattern and
  `gate_globs()` renders `**/autorun-brief.md` automatically, so
  classifier and profile cannot drift in spelling (the pin test binds
  it). ADR-0122 passes the protocol's ADR test (hard to reverse in
  effect, surprising, a real trade-off against gating all run
  directories). ADR-0121 was amended not rewritten: only its status line
  changed (Decision untouched), and `adr_status.py` reports ADR-0121
  `active`, ADR-0122 `provisional`. Index row matches. Backlog line
  carries `(claimed: maintenance:...)` in the protocol's grammar; only
  that line changed.
- **Side effect named by the brief.** Stated in ADR-0122 Consequences:
  "A PR that only edits a brief, such as a resume's brief commit, needs
  an independent review and a human merge." Present and explicit.
- **Doc/code drift.** `fast_path.py` docstring and comment,
  `.claude/implement-queue.md` prose, and ADR-0122 all describe the same
  list; `skills/implement-queue/SKILL.md`'s table lists documented
  defaults only, which a profile overrides, so it needs no edit.
- **Test strength.** New tests assert exit code and exact output for
  three depths, brief-alone, neighbours that must stay low-risk, two
  rename directions and a real-git edit; `verification.md` shows them
  red before the fix and green after. Gap is only the two minors above.
- **Security.** No new input surface; the change tightens a gate.
- **Complexity.** No cut-list hits; one tuple entry, no new abstraction.
  No `lean:` markers added.
- **ADR compliance.** Live ADRs checked via `adr_status.py`; the diff
  honours ADR-0087/0096/0121 (docs-prefix low-risk rule, exit codes,
  profile/classifier equality) and ADR-0036 `gate_paths` intent. No
  violation.
- **Domain passes.** None selected (no payments, migration or
  dependency paths in the diff).
- **Standards.** `docs/standards.json` read; no filtered statement
  matched a finding, so no `enforced` trigger applies.

## Verdict

**Ready to ship.** No critical findings and no open major findings. Two
minor findings are deferred with reasons logged above (root-level glob
dialect unproven but behaviourally inert; case-sensitive basename shared
with `prd.md`/`architecture.md`). Not examined or unknown: the
GitHub-side `gate_paths` matcher (outside this diff and recorded in
ADR-0122 and the backlog as out of reach), and I did not re-run the test
suite, relying on Verify's recorded run (`run_tests.py`, 0 problems).
Nothing blocks Ship.
