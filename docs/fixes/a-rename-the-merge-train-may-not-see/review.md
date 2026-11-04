---
stage: review
run: maintenance:a-rename-the-merge-train-may-not-see
date: 2026-11-03
assumptions: []
---

# Review: a rename the merge train may not see

## Scope

Re-review in the fix loop (second pass) is at the end of this section. First
pass: `git diff origin/main...HEAD` (base `397a987`, which is also the merge
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

**Second pass (fix loop).** `git show 4024915` and `git diff
aa6d314..HEAD` (`fast_path.py` +6/-3, `skills/implement-queue/SKILL.md`,
`.claude/implement-queue.md`, `tests/test_fast_path.py`, `defect.md`,
`verification.md` re-verified in `c7233a3`: 16 PASS, 1 FINDING, 3
unknown). The Owner answered the two majors "Fix now" and "Ship REST
default" (`defect.md` Notes, 2026-11-04). I probed `changed_paths`/`gate`
in a fresh git repo and read the skill, profile and test text against
PR #247. `python3 -m unittest tests.test_fast_path` ran here:
`Ran 35 tests in 1.765s` / `OK`; the full suite was not re-run (Verify's
`0 problem(s)` stands).

## Findings

### Major (FIXED in `4024915`): `gate` mode reported `clear` for a gate-path file with a non-ASCII name

- Scenario (first pass): `git diff --name-only` quoted `docs/adr/0999-café.md`
  as `"docs/adr/0999-caf\303\251.md"`; no gate prefix matched it, so `gate`
  printed `clear` (exit 0) under `merge: auto`.
- Fix: `changed_paths` now runs `git diff --name-only -z --no-renames
  <base>...<head>` and splits on NUL (`fast_path.py`); the tests' `DIFF`
  and fake output follow.
- Second-pass probes (temp repo, `main` holding `notes.txt`,
  `docs/adr/0001-x.md`, `.github/workflows/v.yml`; the worktree's
  `fast_path.py`):

      $ git diff --name-only -z --no-renames main...mixed | od -c
      0000000   d o c s / a d r / 0 0 0 1 - x . m d \0 d o c s / 303 251 . m d \0
      (trailing NUL; split on "\0" with the `if path` filter drops the empty tail)
      newline in a name (docs/adr/0002-a\nb.md):
        gate-paths: human (docs/adr/0002-a
        b.md)                                   exit 1
        fast-path: review (docs/adr/0002-a
        b.md)                                   exit 1
      rename .github/workflows/v.yml -> docs/v.yml (with --no-renames):
        gate-paths: human (.github/workflows/v.yml)   exit 1
      empty diff:  gate-paths: human (empty diff) exit 1;  fast-path: review (empty diff) exit 1
      plain edit of notes.txt:  gate-paths: clear exit 0;  fast-path: review (notes.txt) exit 1
      docs/adr/0001-x.md plus docs/é.md:  fast-path: review (docs/adr/0001-x.md) exit 1;
                                          gate-paths: human (docs/adr/0001-x.md) exit 1

  A trailing NUL, an empty output, a newline in a path and `-z` with
  `--no-renames` all behave. `changed_paths` has exactly two callers
  (`fast_path.py` lines 116 and 134: the classifier and `gate`; `grep`
  found no other); both take the list, so the only change visible to them
  is that non-ASCII and quote-bearing names are now the real path. For
  ASCII paths the output is unchanged (plain edit, rename, empty diff
  above match the first pass). The new real-git tests (non-ASCII ADR,
  `"` in a name, non-ASCII workflow through `gate`) pass; Verify showed
  them red on the pre-fix file. A path containing a backslash or other
  control character was not run; `-z` lists those raw by construction.
- Standard: none
- Decision: fixed, evidence above. Closed.

### Major (FIXED in `4024915`, by the Owner's choice): the skill's `changed-files` default turned every consumer's `merge: auto` into a human merge

- Scenario (first pass): the skill's default row was `none`, so a
  consumer with `merge: auto` and no `changed-files` hook got every PR
  held, with no usable source and nothing in the skill to say how to
  write one.
- Fix (the user's option (b), "Ship REST default"): the table row now
  names `gh api repos/{owner}/{repo}/pulls/<N>/files --paginate`, every
  `filename` plus every `previous_filename`, checked against `changed_files`;
  the Phase 3 paragraph says a hook-less repo uses that default; the
  profile keeps its `gate` hook and the same REST fallback. A consumer
  now gets a working source with no hook. Verify ran the command against
  PR #247: 129 entries, `changed_files` 129, 19 `previous_filename`s all
  absent from the `filename` set.
- ADR judgement (agree). The protocol's test needs all three legs. The
  change is a default row in a skill file, reversible by one edit with no
  migration; it makes a source available where there was none and keeps
  ADR-0087's fail-closed "If rejected" reading (read: lines 62-66 of
  ADR-0087: a consumer "sees every PR reported as awaiting a human merge,
  never a silent merge"). Option (b) removes the behavior change that
  made the first pass lean toward an ADR, so the test fails on the
  first leg. No `docs/adr/` file was touched (`git show --stat 4024915`).
- Standard: none
- Decision: fixed, evidence above. Closed. The residual wording question
  is the new Minor below.

### Minor (NEW, open): the table row's count check is ambiguous between file entries and unique paths

- Scenario: the check is meant to compare the number of entries the REST
  list returns (PR #247: 129) with `changed_files` (129). The row reads
  "every `filename` plus every `previous_filename`; its length must
  equal `... .changed_files`". "its" can mean the collected path set,
  which for #247 is 129 + 19 = 148 paths (Verify: 19 `previous_filename`s,
  none in the `filename` set). An agent that compares 148 with 129 sees a
  mismatch on every PR with a rename and fails closed. The paragraph says
  "the REST file list, whose length is checked" and the profile says "The
  list's length must equal the PR's `changed_files`", which read as
  entries, so the three places do not say the same thing about which
  count is meant, and nothing states that a rename is one entry with two
  paths. Direction of the error: spurious human merge, never a pass of a
  short list; the only way the wrong count passes a truncated list is the
  coincidence that the union of a capped list happens to equal a larger
  `changed_files`. Fail closed, so not a safety defect; but a PR that
  renames files, the very case this run is about, is held for a human
  by a misread rule.
- Standard: none
- Decision: open, not deferred by the user. A minor may be deferred
  freely; recommend a one-clause fix at the next touch of the row and the
  profile: "the number of entries the call returns (a rename is one
  entry holding two paths) must equal `changed_files`". No code change.

### Minor (deferred, partly closed): a truncated REST list

- First-pass scenario: no instruction compared the list to the 3000-file
  cap. Now closed in text: both the skill and the profile compare the
  list's length to `changed_files` and say a difference fails closed.
- Still unknown, not a pass: (1) whether `pulls/<N>`'s `changed_files` is
  itself capped. GitHub's REST docs list it as a required integer in the
  response schema (docs.github.com, pulls) and cap only the files list
  ("Responses include a maximum of 3000 files"); the docs do not say
  `changed_files` is capped, and no PR over 3000 files was queried, so
  that it keeps counting past 3000 is an [INFERENCE]. If it were capped at
  3000 a truncated list of 3000 would match and pass. (2) The 3000-file
  case itself, not exercised (Verify: largest PR 129).
- Standard: none
- Decision: deferred — reason: the count check closes the cap case on
  the documented behavior; a 3000-file PR is not realistic here and
  human review catches its size. Recommend, at the next touch of the
  profile, adding "a list of 3000 entries fails closed" to remove the
  one coincidence the `changed_files` assumption leaves.

### Minor (deferred, improved): the doc-pin test

- Before: asserted a wrapped line break and left the REST source
  unpinned. Now: `test_the_skill_profile_and_routine_name_one_changed_files_source`
  asserts `**both**` and `fail closed` in the skill and, for the skill
  and the profile each, `pulls/<N>/files --paginate`, `` `filename` ``,
  `` `previous_filename` `` and `changed_files`. The line-break
  assertion is gone, and deleting the REST command, the
  `previous_filename` instruction or the count check from either file now
  turns it red. Weaknesses left: the tokens are checked independently, so
  they could all appear in unrelated sentences, and none distinguishes
  entries from unique paths (the new Minor above). `Ran 35 tests ... OK`
  here.
- Standard: none
- Decision: deferred — reason: within the repo's convention of pinning
  prose to files (`tests/README.md`); the behavior that matters (`gate`)
  has exact-string real-git tests. The test would not catch the
  ambiguity above; fix the wording, not the test.

### Minor (deferred; Verify's FINDING resolved as no violation): harness neutrality

- Verify marked a FINDING because `4024915` adds a concrete `gh api`
  command to the skill's default table. I checked the rule: the
  protocol's "Harness neutrality" section (`docs/pipeline-protocol.md`
  line 468) bars content specific to one *harness* (Claude Code
  invocation mechanics, plugin paths); it does not name `gh` or `git`.
  The `Hooks` table at `skills/implement-queue/SKILL.md` lines 43-57
  already holds `gh run list`, `gh issue edit`, `gh pr checks`,
  `gh pr merge`, `gh pr update-branch`, and the "Cloud sessions"
  paragraph (line 59) says "each `gh` command in this file states an
  intent" that the environment may carry out through MCP or REST. The new
  row is a `gh api` REST command in the same column and register as
  those rows, and the other defaults' REST twins are written the same
  way. So it is consistent with the table's existing defaults and is not
  a new violation, nor a regression to route to Implement. Whether a
  repo-wide rule against provider CLIs in skills is wanted is a seed for
  later, not a finding here.
- Standard: none
- Decision: deferred — reason: not a violation of the protocol rule;
  consistent with the table's convention.

## Passes with no findings

First-pass text, kept; where it refers to the two majors, both are now fixed
(see Findings).

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
  the consumer-facing default, filed as the second Major (now fixed) rather than as a
  separate "ADR owed" finding. No existing ADR's Decision section was
  edited (`git diff` shows none under `docs/adr/`).
- **Security.** No shell string built from input: `gate` passes argv to
  `cli.runner("git")`; no secrets; refs are argv elements, not
  interpolated into a shell. The skill forbids filling a gap from the PR
  body, which closes the journal's "rests on the PR body's stated paths"
  case. The only boundary gap was the quoting Major (now fixed by `-z`).
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
  was the second Major (now fixed).
- **Domain passes.** None selected (no payments, migration or dependency
  paths in the diff).
- **Standards.** `docs/standards.json` read; no `enforced` statement in the
  `factory`, `pipeline` or `docs` domains, so no enforced trigger applies.

## Verdict

**Ready for Ship.** Ship may proceed. No critical finding. **No major is
open:** both first-pass majors are fixed with evidence above (non-ASCII
gate path now reads `human` with the real path; the REST default ships
with a count check, by the Owner's "Ship REST default"). No new major.

Open or deferred minors (none blocks): (1) the count check's wording is
ambiguous between entries and unique paths, a spurious fail-closed on
renaming PRs; new, open, recommend a one-clause fix at the next touch of
the skill row and profile; (2) the 3000-file/`changed_files` coincidence,
deferred with a reason; (3) the doc-pin test's weaknesses, deferred;
(4) harness neutrality, resolved as no violation.

Fail-closed roll-up. Not run or unknown, and not read as passes: whether
`changed_files` on `pulls/<N>` is capped (docs silent; no PR over 3000
files queried); the 3000-file case itself; the GitHub MCP file-list
tool's rename behavior (Verify's NOT RUN); a live train run that follows
the profile's hook or the skill default (prose contract only); a path
with a backslash or control character through `gate` (`-z` passes them
raw by construction, not run); the GitHub-side glob matcher for `**/`
patterns (backlog line 154, out of scope); the full suite (not re-run
here; Verify's `run_tests.py` `0 problem(s)` at `4024915` stands). None of
these is a known failure, and none changes the verdict: the open items are
a wording minor and unknowns that fail closed in the written rule.
