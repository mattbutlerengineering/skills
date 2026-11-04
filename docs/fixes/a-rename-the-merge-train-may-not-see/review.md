---
stage: review
run: maintenance:a-rename-the-merge-train-may-not-see
date: 2026-11-03
assumptions: []
---

# Review: a rename the merge train may not see

## Scope

`git diff origin/main...HEAD` (base `397a987`, which is also the merge
base and the current `origin/main`): code commit `d0ccebe` (`fast_path.py`
`gate` mode, `tests/test_fast_path.py`, `skills/implement-queue/SKILL.md`,
`.claude/implement-queue.md`, `docs/factory/merge-train-routine.md`,
backlog claim), plus the run's artifacts (`autorun-brief.md`, `defect.md`,
`verification.md`: 13 PASS, 1 FINDING, 1 NOT RUN). The predecessor
`verification.md` exists, so no soft-gate inversion. Maintenance patch:
a light pass. Verify's regression tests are the floor and were not
re-run; I probed the producing boundary (`changed_paths` / `gate`) and
its consumers (the profile's two sources, the skill default) with real
git repos.

## Findings

### Major: `gate` mode reports `clear` for a gate-path file whose name has a non-ASCII character

- Scenario: `git diff --name-only` quotes such a path (`core.quotepath`
  default) and `changed_paths` does not undo that. Probe, a branch adding
  `docs/adr/0999-café.md`:

      $ git diff --name-only --no-renames main...pr
      "docs/adr/0999-caf\303\251.md"
      $ python3 fast_path.py gate main pr
      gate-paths: clear          (exit 0)
      $ python3 fast_path.py main pr
      fast-path: review ("docs/adr/0999-caf\303\251.md")   (exit 1)

  The listed string starts with `"`, so `is_gate_path` matches none of
  its prefixes, basenames or files. The classifier is safe only by
  accident (its extra `not path.startswith("docs/")` test sends the
  quoted string to review). `gate_verdict` has no such backstop, so the
  new consent source passes the same path as `clear`. The same holds for
  `.github/workflows/é.yml`, `docs/factory/é.md`, `docs/design/é/x.md`.
  Effect under `merge: auto`: the `gate_paths` condition of ADR-0087 is
  silently skipped for that PR; the other conditions (`check`, review or
  fast-path, hold label) still apply. The quoting predates this run in
  `changed_paths`, but this run makes `gate` the one source the skill
  names and its exit 0 the consent, and the fix is owed at the same
  boundary. The REST source is unaffected (JSON carries raw names).
- Standard: none
- Decision: open — needs a fix before Ship (route to Implement): make
  `changed_paths` read unquoted paths (`-c core.quotepath=false`, or
  `-z`), with a real-git test on a non-ASCII gate path (`gate` exit 1
  naming the path). The tests assert the exact diff args (`DIFF`), so
  that constant changes with it. Not deferred: a major is the user's to
  defer, and no user decision is on record.

### Major: the skill's new `changed-files` default turns every consumer's `merge: auto` into a human merge, with no ADR, changelog line or consumer-usable hook

- Scenario: `skills/implement-queue/SKILL.md` is the plugin payload, read
  by every consumer repo; it is not mirrored into stamped repos
  (`grep -c implement-queue factory/manifest.json` printed `0`;
  `.claude-plugin/plugin.json` and `factory/templates/tools/factory/protocol.py`
  are the only other hits, neither a mirror of the skill). The new table
  row says `changed-files`: "none: no `gate_paths` check can pass, so
  under `merge: auto` every PR needs a human merge". A consumer whose
  profile says `merge: auto` and names no `changed-files` hook (none can
  have, the hook did not exist) gets every PR held after this release
  that it merged before. ADR-0087's own "If rejected" section calls that
  outcome fail-closed and non-silent ("sees every PR reported as awaiting
  a human merge"), so the direction is consistent with the ADR and
  ADR-0096. What is not: the ADR's Decision and Consequences still read
  as though `merge: auto` plus the four conditions enables merging, and
  nothing tells a consumer the key now needs a second one. Their
  remedy is also out of reach: the profile's local hook is
  `python3 fast_path.py gate`, a root-only tool (not in `MIRRORS`,
  ADR-0060), so a consumer must write its own hook from the REST prose,
  which lives only in this repo's profile, not in the skill. Brief and
  Implement's Notes call the default "inside the brief"; the Owner's
  answers do not mention a behavior change for other repos. Not a
  safety bug; a silent behavior change for consumers, which the review
  contract names a finding.
- Standard: none
- Decision: open — the user decides: (a) accept it as intended and add a
  one-line consequence to ADR-0087 (status-line pointer, no Decision
  rewrite) or a short ADR, plus a release-note line, or (b) change the
  default so the skill ships a usable source (the REST `pulls/<N>/files
  --paginate` command, both `filename` and `previous_filename`) and only
  a failing hook fails closed. Not deferred.

### Minor: a truncated REST list is not detectable by the rule the profile gives

- Scenario: the profile says "if the call ... returns part of the list,
  fail closed". The skill adds "a list the source capped or paged short".
  GitHub's `pulls/{n}/files` caps at 3000 files even with `--paginate`
  (GitHub's REST docs; not re-queried here), and the response carries no
  truncation flag. A 3000-file PR's gate path past the cap is invisible,
  and "returns part of the list" gives the agent nothing to test. No
  instruction compares the count to the PR's `changed_files` (from
  `pulls/{n}`) or treats a list of 3000 as failing closed. `defect.md`'s
  129-file PR (Verify: 129 returned, 19 renames) shows pagination works
  under the cap; the cap itself was not exercised. A PR that size is
  not a realistic scenario in this repo.
- Standard: none
- Decision: deferred — reason: the cap case is a very large PR that
  other gates (human review of the diff size) also catch; recommend
  adding "a list of 3000 entries, or one whose length differs from the
  PR's `changed_files`, fails closed" to the profile in the next touch of
  that file. Defer is the reviewer's recommendation; the user may
  overrule.

### Minor: the new doc-pin test asserts wrapped prose and cannot tell a consumer-visible bug from a rewording

- Scenario: `test_the_skill_profile_and_routine_name_one_changed_files_source`
  asserts substrings including a line break:
  `"**both** its old path and\nits new one"` and `"fail closed: the PR
  needs a human merge"`. Re-wrapping the skill paragraph, or rewording
  the sentence while keeping the rule, turns it red; deleting the REST
  fallback (the second source, `previous_filename`) leaves it green,
  since no assertion touches it. Repo convention does allow pinning prose
  to code: `tests/README.md` lists `test_open_pr_preflight.py` and
  `test_protocol_conformance.py` as suites that "pin what the prose
  promises, against the real files", and AGENTS.md's rule is exact
  strings through public interfaces (the `TestGateMode` cases do that).
  So the test is within convention, but it is the weak kind: its
  breakage mode is rewording, and the gap it leaves is the REST source.
- Standard: none
- Decision: deferred — reason: convention-permitted; the behavior that
  matters (`gate`) has exact-string, real-git tests. Suggest dropping the
  `\n`-dependent assertion and adding the REST `previous_filename` line
  to what is pinned, when the profile is next edited.

### Minor: Verify's harness-neutrality finding stands as a pre-existing condition, not a regression

- Scenario: Verify found concrete `gh`/`git` commands in the skill file.
  I checked the added lines of `d0ccebe` (`git show d0ccebe --
  skills/implement-queue/SKILL.md`): the new paragraph and row name the
  hook, not a command, so the fix added none; the commands sit in the
  pre-existing hook-default table. Agreed: no routing to Implement. One
  inconsistency remains and is the Major above: the skill ships commands
  for its other defaults but none for this one.
- Standard: none
- Decision: deferred — reason: pre-existing, not introduced here; resolved
  or not by the user's choice on the second Major.

## Passes with no findings

- **Correctness (the gate list).** `gate` calls the existing
  `changed_paths` and `is_gate_path` (one `changed_paths` call; the test
  `test_the_same_diff_args_as_the_classifier_are_used` pins the diff
  args); no copy of the matcher, seam rule kept. Its list is the
  classifier's constants, not the profile at run time; the existing pin
  `test_the_profile_gate_paths_equal_the_classifiers_list` ties the
  profile's 11 `gate_paths` to `gate_globs()`. I ran `gate_verdict` on a
  path under each of the 11 entries: `docs/adr/0001-x.md`,
  `docs/design/a.md`, `a/b/prd.md` and root `prd.md`, `x/architecture.md`,
  `docs/x/autorun-brief.md` and root `autorun-brief.md`,
  `factory/templates/a`, `.github/workflows/a.yml`,
  `.claude-plugin/plugin.json`, `docs/factory/x.md`,
  `docs/pipeline-protocol.md`, `docs/standards.json` all gave `human
  (<path>)`; `factory/templatesX/a` and `lint.py` gave `clear`. No entry
  is missed (the non-ASCII gap above is the matcher's input, not its
  list).
- **Fail-closed behavior of `gate`.** Real-git probes: a shallow clone
  with no `origin/main` and one with a depth-1 `origin/main` both printed
  the `fast-path: git diff --name-only --no-renames origin/main...HEAD
  failed:` string, exit 2 (a human gate per the profile). A stale
  `origin/main` (no fetch) with a PR branch cut before newer `main`
  commits compared against the fork point and gave the correct `human
  (.github/workflows/v.yml)` for a renamed gate file. The three-dot diff
  runs from the merge base, so a stale base can only over-report, not
  hide a path, unless the base is stale and unrelated, which errors. The
  profile says `git fetch origin` first; nothing in `gate` enforces it,
  and none is needed for safety. Empty diff and bad ref: Verify's
  runs stand (exit 1 `empty diff`, exit 2). The git failure detail is the
  usage line of `git`, not the error (`cli.detail`, pre-existing, not a
  finding).
- **Remote REST path.** Verify's PR #247 run stands (129 files, 19
  `previous_filename`, all absent from a `filename`-only set); the
  `previous_filename` collection is stated as "every `filename` **and**
  every `previous_filename`". The cap case is the Minor above; the
  MCP-tool path is excluded by the profile and NOT RUN here (Verify's
  unknown, carried).
- **ADR judgement (Notes: "No ADR").** The protocol's test needs all
  three legs. The hook name and the `gate` mode are easy to reverse and
  the obvious reading of ADR-0087's existing rule, so the hook itself
  fails the test; I agree. The decision that does lean toward the test is
  the consumer-facing default, filed as the second Major rather than as a
  separate "ADR owed" finding. No existing ADR's Decision section was
  edited (`git diff` shows none under `docs/adr/`).
- **Security.** No shell string built from input: `gate` passes argv to
  `cli.runner("git")`; no secrets; refs are argv elements, not
  interpolated into a shell. The skill forbids filling a gap from the PR
  body, which closes the journal's "rests on the PR body's stated paths"
  case. The only boundary gap is the quoting Major.
- **Complexity.** Cut-list applied to the diff: no hits; no `lean:`
  markers added; `gate_verdict` mirrors `classify` in shape rather than
  duplicating logic (two small functions of 6 lines, distinct verdict
  vocabularies). No `deepen` hand-off.
- **ADR compliance.** Live ADRs from `adr_status.py`: ADR-0036 (amended by
  ADR-0085), ADR-0087 (amended by ADR-0088), ADR-0088, ADR-0096 (amended
  by ADR-0121), ADR-0121, ADR-0122 (provisional). The diff keeps
  ADR-0087's gate-path condition, ADR-0096's profile and
  ADR-0121/0122's list unchanged (profile `gate_paths` untouched), and
  does not touch `plugin.json` (ADR-0095). The consent-default question
  is the second Major.
- **Domain passes.** None selected (no payments, migration or dependency
  paths in the diff).
- **Standards.** `docs/standards.json` read; no `enforced` statement in the
  `factory`, `pipeline` or `docs` domains, so no enforced trigger applies.

## Verdict

**Not ready to ship: Ship may not proceed yet.** No critical findings;
**two open majors**, neither deferred by the user:

1. Non-ASCII gate path reads `clear` (fix in `changed_paths`, route to
   Implement, then re-verify).
2. The `changed-files` default's silent change for consumers (the user
   decides: accept with an ADR-0087 note and release line, or ship a
   default source).

Minors: three, deferred with reasons above (REST 3000-file cap, doc-pin
test brittleness, harness-neutrality carried from Verify). Fail-closed
roll-up: not run or unknown, and not read as passes: the GitHub MCP
file-list tool's rename behavior (Verify's NOT RUN), the 3000-file cap
(not exercised), a live train run that follows the profile's hook (prose
contract only), the GitHub-side glob matcher for `**/` patterns (backlog
line 154, out of scope), and the full suite (not re-run here; Verify's
`run_tests.py` 0 problem(s) stands). Ship waits on the two majors.
