---
stage: operate
run: maintenance:a-rename-the-merge-train-may-not-see
date: 2026-11-04
users-observed: 0
signal-source: "none found. Looked at PR #1150 (one comment, the factory reviewer bot's; no human review, no reactions), issue #1149 (no comments, no reactions), the merge-train journal #930 (98 comments; the newest, 2026-11-04T17:38:58Z, is before the merge at 19:54:21Z, so none since) and issues and PRs created since 2026-11-04 (only #1148, #1149 and #1150). The only human on the record, the Owner, filed #1149, authored and merged the PR; that is authoring, not using the change"
assumptions:
  - "Written the same day as the merge (2026-11-04, about an hour after it), against the let-it-breathe step. The brief's `operate:` section sets `minimum-signal: Ship written back as released (the PR merged)`, which is met (`release.md` Write-back), so the stage runs; the brief never supplies the count. Outcomes below record state and tests, not use."
  - "Outcomes are measured against the brief's Success criteria and `defect.md`'s work-item Accept lines, because a maintenance run has no `prd.md`."
  - "The factory reviewer bot's PR comment is not counted as a person. It is the repo's automated check on every PR."
  - "The change reaches a consumer's train only with the outstanding `chore(release)` bump (`release.md`, Write-back and Post-release checks), so the absence of any train use is the expected state today, not a finding."
---

# Retro: the merge train reads rename sources and non-ASCII gate paths

## Outcomes vs. intent

### A PR that renames a gate-path file into an ungated path is refused, naming the old path

- What happened: merged on main as `038dc0f` (`release.md`, Write-back). Post-release check from this tree (main plus the write-back commit), in a fresh temp repo whose `main` holds `.github/workflows/validator.yml` and `notes.txt`: a branch that `git mv`s the workflow to an ungated path printed `gate-paths: human (.github/workflows/validator.yml)`, exit 1 (the classifier printed `fast-path: review (.github/workflows/validator.yml)`, exit 1); a branch that appends a line to `notes.txt` printed `gate-paths: clear`, exit 0. That is the check `release.md` left for after the merge, and it matches `verification.md` §Criterion "A PR that renames a gate-path file".
- Signal strength: unobserved. It is measured at `fast_path.py gate` in a temp repo, but no real PR has renamed a gate file since the merge, so nothing has landed in use.

### A gate-path file with a non-ASCII or quote-bearing name is refused with its real path

- What happened: fixed in `4024915` after review's first major (`review.md`, Findings, first Major); `verification.md` shows the pre-fix `gate-paths: clear` exit 0 and the post-fix `gate-paths: human (docs/adr/0999-café.md)`, exit 1. Tests cover it in real git (`Ran 35 tests ... OK`). Not re-run here beyond the rename check above.
- Signal strength: unobserved (tests and temp-repo runs only).

### The skill names one changed-file source, and a partial list fails closed

- What happened: the skill's `changed-files` default, the profile and the routine name the same source, pinned by `test_the_skill_profile_and_routine_name_one_changed_files_source` (`verification.md`). Whether any train run follows it is not known: journal #930 has no comment since the merge, and `verification.md` §Not verified says a live train run was never exercised. The text reaches consumers only with the version bump.
- Signal strength: unobserved.

### Did the exposure ever bite? (the brief's reason for the fix)

- What happened: `defect.md` ("Does it bite today?") found no renamed file in any of 108 PRs merged since the train's first run, so none carried a gate-path source out. Since the merge, the only issues and PRs created are #1148, #1149 and #1150, none a rename. Nothing bit before the fix and nothing has been exposed since.
- Signal strength: unobserved. Absence of a renaming PR says nothing about the rule working, because no PR has existed to route.

### The cost: a hook-less consumer now gets the REST default and a count check

- What happened: not exercised. The count check's wording is open (see Open debt); read as unique paths it holds a renaming PR for a human (`review.md`, open Minor). No consumer train has read it.
- Signal strength: unobserved.

## Open debt

None filed against this run. #1149 is the run's intake (created 2026-11-04T05:22:03Z, before the merge) and closed with the PR; it counts toward nothing. The debt that stays visible lives in the run's artifacts:

- **Count-check wording** (`review.md`, open Minor; `release.md`, Flagged items): "its length" can be read as file entries or as collected paths; read as paths, a PR with renames mismatches and fails closed. Fails closed, never passes a short list.
- **A list of exactly 3000 entries** is not named to fail closed, and whether `changed_files` is itself capped is unknown (`review.md`, deferred Minor; `verification.md` §Not verified). The largest PR queried has 129 files.
- **The GitHub MCP file-list tool's rename behaviour** is unknown (`verification.md` §Not verified; `defect.md` (b), `[INFERENCE]` only). Most journal runs read GitHub through MCP (`defect.md` (a)), so this is the source the train most likely uses in the cloud.
- **Doc-pin test weaknesses** (`review.md`, deferred Minor): the tokens are pinned independently and none distinguishes entries from paths.
- The `chore(release)` version bump per ADR-0095 is outstanding for the Owner (`release.md`, Write-back).

## Run retrospective

- Keep: **a brief that names its evidence checks.** Capture was told to test each candidate source on a real renamed PR and to say plainly if none bit; it found PR #247 with 19 renames, quoted all three sources, and found that `gh pr view --json files` also truncates at 100 files (`defect.md` (b)). That turned "may not see" into a table.
- Keep: **Review probing the consumers, not only the producer.** It found two majors after Verify's first pass: a non-ASCII gate path read as `clear`, and a default row that turned every consumer's `merge: auto` into a human merge (`review.md`). The Owner chose both fixes ("Fix now", "Ship REST default") and Verify re-ran with red tests against the pre-fix file (`verification.md`).
- Keep: **red first against the pre-fix file**, with the inflated count explained in-line (`verification.md`: 35 failures on the old file, 3 behavioural).
- Change: **Verify passed the first pass on a classifier that mis-read non-ASCII names.** Review found it with an ordinary `git diff --name-only` quoting case (`review.md`, first Major); the non-ASCII and quote-bearing cases appear in `verification.md` only as the second-pass criterion, added after Review.
- Change: **a wording minor shipped open** because it was found in the last pass, after the Owner's choices were made. The ambiguity sits in the one clause (the count) the run added to catch truncation.
- Stop: nothing.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| `changed_paths` read git's quoted form for a non-ASCII or quote-bearing name, so a gate-path file read as `clear` | `review.md` first Major; `verification.md` §"A gate-path file with a non-ASCII or quote-bearing name" | mechanical | `tests/test_fast_path.py` now holds the real-git cases for this tool. The wider carrier is one test, or a lint check, that no root tool calls `git diff --name-only` or `git ls-files` without `-z`; `defect.md` Blast radius names `conductor_*.py` and `kb.py` as other `git diff --name-only` callers, not checked here for the same quoting |
| The first `changed-files` default (`none`) turned every consumer's `merge: auto` into a human merge | `review.md` second Major | judgement | the Verify skill's checks (or `skills/review/SKILL.md`): for a change to a payload skill, name what a consumer with no local hook sees and probe it. A reader's question, not a deterministic check |
| The count check says "length" and can be read as entries or as unique paths | `review.md` open Minor | judgement | the doc-pin test, `test_the_skill_profile_and_routine_name_one_changed_files_source` in `tests/test_fast_path.py`, once the clause is reworded to "the number of entries the call returns (a rename is one entry holding two paths)": it can pin that phrase in the skill and the profile. The wording itself is a reader's call |
| Three facts the rule rests on were never observed: a truncated list (3000 cap), whether `changed_files` is capped, and the MCP tool's rename report | `verification.md` §Not verified; `review.md` fail-closed roll-up | judgement | none today: no PR over 3000 files exists here and the MCP tool was unavailable to the run. The carrier is the first cloud train run that records what its tool returned (see the seed below) |

## Idea seeds

Proposed only; the skill says to append them to `docs/backlog.md`, and they are appended there in a separate commit, not filed as issues:

- Reword the implement-queue count check to "the number of entries the call returns (a rename is one entry holding two paths) must equal `changed_files`", add "a list of 3000 entries fails closed" to the skill row and the profile, and pin both phrases in the doc-pin test (from: maintenance:a-rename-the-merge-train-may-not-see)
- Settle the two unknowns behind the REST default: whether `changed_files` keeps counting past 3000, and what the GitHub MCP file-list tool reports for a rename (`previous_filename` or not), by recording it from the first cloud train run that lists a PR's files (from: maintenance:a-rename-the-merge-train-may-not-see)
- A test or lint rule: no root tool calls `git diff --name-only` or `git ls-files` without `-z` (check `conductor_*.py` and `kb.py` first), so a non-ASCII path is never read as git's quoted string (from: maintenance:a-rename-the-merge-train-may-not-see)
- Add to the Verify probes for any tool that classifies paths: a non-ASCII name and a quote-bearing name; and for a payload-skill change: what a consumer with no hook sees (from: maintenance:a-rename-the-merge-train-may-not-see)
- After the version bump ships, read the first journal #930 comment that names how the train listed a PR's files, to see whether it followed the skill's default or the profile's `gate` hook (from: maintenance:a-rename-the-merge-train-may-not-see)

## Run complete

Closed 2026-11-04. Released as `038dc0f` (#1150). The seeds above are the input to the next Idea-stage run.
