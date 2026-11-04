---
stage: capture
run: maintenance:a-rename-the-merge-train-may-not-see
date: 2026-11-03
re-entry: implement
intake: #1149
origin: docs/backlog.md line 144 seed (from: feature:faster-sdlc)
assumptions: ["re-entry: implement, taken from the brief's reading (the orchestrator's, not an Owner answer) under the skill's rule that a scoped fix with no design decisions re-enters at Implement. The brief reserves architect for a fix whose source choice needs a design decision across tools; Capture found the choice sits inside one contract (the skill's Phase 3 text, with fast_path.py as an existing owner of the rename-safe diff), so it stays at implement", "Capture: the in-flight check ran. gh pr list --state open returned [], so the review surface was reachable and the result is a clean 'nothing matched', not a check that could not run", "Capture outcome: 'undefined source', the brief's second outcome. The brief names it as a defect in the skill's contract and tells Capture to take it with implement as the probable re-entry, so no skill default was needed", "Implement: an empty changed-file list fails closed (`gate-paths: human (empty diff)`), matching the classifier's `review (empty diff)`; an empty list cannot be told from a failed read", "Implement: the GitHub MCP file-list tool is not named as a source in the profile, because no run has recorded that it reports previous_filename (untested, per Capture)"]
---

# Defect: the merge train's changed-file source is unspecified and two of its three candidates drop a rename's old path

Intake: #1149, "implement-queue: the train's gate_paths check may not see
a rename's source path" (`type:defect`, filed 2026-11-04T05:22:03Z).

## Defect (or Condition)

The `implement-queue` skill's Phase 3 consent rule refuses a PR that
"changes a file `gate_paths` matches" (`skills/implement-queue/SKILL.md`
line 198). Nothing says how the PR's changed-file list is obtained: not
the skill, not `skills/implement-queue/references/reviewer-contract.md`,
not `.claude/implement-queue.md`, not `docs/factory/merge-train-routine.md`
(its only words are "changed paths against `main`", §2 step 3, and
"changes a `gate_paths` file", §3). The agent may pick any source.

Expected: the skill names one source, and that source counts a rename's
old path as well as its new one, so a PR that moves a gate-path file
(`.github/workflows/*.yml`, `docs/adr/*.md`,
`.claude-plugin/plugin.json`) into an ungated path is refused under
`merge: auto` (ADR-0096).

Observed: of the three sources the brief named, two report only a
rename's destination. Evidence below. This is the blind spot
`fast_path.py` had until #1144.

## Reproduction / Evidence

**Outcome reached: undefined source, with a proven gap in two of the
candidate sources.** Not a "not a defect" record: the source is not
specified anywhere, and the journal shows the train's real source is a
tool this run cannot read.

### (a) What the train runs

Searched journal #930 (`gh api repos/{owner}/{repo}/issues/930/comments
--paginate`, 94 comments, 1080 lines) for `name-only`, `--json files`,
`pulls/<n>/files`, `no-renames`, `git diff`, `gh pr diff`,
`list_pull_request_files`, `get_pull_request_files`. No comment names
a command or tool for the file list. What the comments do say:

- Most runs read GitHub through MCP only: "`gh` not used; GitHub MCP only"
  (first run); "the `gh` CLI may be absent" (routine's Environment
  paragraph); "`gh` GraphQL is also blocked, so `gh pr view` and `gh pr
  merge --auto` are unavailable". `gh pr view --json files` is GraphQL, so
  it is closed to that environment.
- The verdicts cite the result, not the call: "only `docs/kb/...` changed
  (fast-path low-risk by changed-file list, no gate path)"; "`fast_path.py`
  was not run (no PR checkout); the verdict came from the changed-file
  list" (several runs); "fast-path low-risk, derived from the file list".
- One run says the list was incomplete: "Diff file list was read via the
  saved tool output only in part, and the gate verdict rests on the PR
  body's stated paths".

So the source is an MCP file-list call in cloud runs, a call this run
cannot make, and nothing in the repo names it. Where a checkout exists the
profile's `fast-path` hook (`python3 fast_path.py origin/main HEAD`) runs
instead, but that hook classifies "docs-only and clear of the gate paths";
it is not named as the source of the Phase 3 `gate_paths` check, and the
journal says it is often not run.

### (b) What each candidate reports for a rename

Real merged PR: **#247** ("refactor: land the 2026-08-05 architecture
deepening — seams, renames, quick wins (wo-lbi)", merged
2026-08-11T04:50:33Z). A scan of the 400 most recent merged PRs
(earliest merged 2026-08-14) with `pulls/<n>/files --paginate` found no
renamed file, and `git log origin/main --diff-filter=R -M` lists exactly
one commit with renames, `622e2bf`, PR #247. It has 19 renames. Mapped to
the gate list, the pair `tests/test_factory_gates.py` →
`tests/test_gates.py` stands in for any gate-path move.

REST `gh api repos/mattbutlerengineering/skills/pulls/247/files
--paginate --jq '.[]|select(.filename=="tests/test_gates.py")|{filename,previous_filename,status}'`:

    {"filename":"tests/test_gates.py","previous_filename":"tests/test_factory_gates.py","status":"renamed"}

and for all of them `--jq '.[]|select(.status=="renamed")|[.status,.previous_filename,.filename]|@tsv'`
printed 19 lines, for example:

    renamed	factory/skills/pm/SKILL.md	factory/charters/pm/CHARTER.md
    renamed	tests/test_factory_gates.py	tests/test_gates.py

`gh pr diff 247 --name-only | grep -c -E "factory/skills/pm/SKILL.md|test_factory_gates"`
printed `0`. The two destinations are there:

    factory/charters/pm/CHARTER.md
    tests/test_gates.py

`gh pr diff 247 --name-only` (129 lines) equals the REST `filename` set
(`diff` of the sorted lists printed no difference). The raw diff has the
old path only on a `rename from` line:

    similarity index 100%
    rename from factory/skills/architect/SKILL.md
    rename to factory/charters/architect/CHARTER.md

`gh pr view 247 --json files --jq '.files[0]|keys'` printed
`["additions","deletions","path"]`: one `path`, no `previous_filename`, no
`status`. The `factory/charters/pm/CHARTER.md` entry printed as
`{"additions":0,"deletions":0,"path":"factory/charters/pm/CHARTER.md"}`;
`[.files[].path|select(test("factory/skills/pm/SKILL.md|test_factory_gates"))]|length`
printed `0`.

A second defect of the same source, found while testing it:
`gh pr view 247 --json files --jq '.files|length'` printed **100** while
the REST list and `gh pr diff --name-only | wc -l` both printed **129**. So
`gh pr view --json files` truncates a large PR to 100 files, and a gate
path past the cap is invisible to it. This is not a rename issue, but it
means the source the skill names must be complete as well as rename-aware.

| Source | Rename old path | Complete on a 129-file PR |
| --- | --- | --- |
| `gh pr diff <N> --name-only` | no (destination only) | yes (129) |
| `gh pr view <N> --json files` | no (`path` only) | **no (100)** |
| REST `pulls/{n}/files` | yes (`previous_filename`, `status: renamed`) | yes (129) |
| GitHub MCP file-list tool | not tested: unavailable to this run | not tested |

The MCP tool's report for a rename is `[INFERENCE]` only: it presumably
wraps REST `pulls/{n}/files`, which would carry `previous_filename`, but no
repo text or journal line shows it, and this run could not call it.

### (c) Local `git diff --name-only` on the train's path

Searched the skill, its `references/`, `.claude/implement-queue.md` and
`docs/factory/merge-train-routine.md` for `name-only`, `name-status` and
`no-renames`: no match. The only train-path use of git for paths is the
profile's `fast-path` hook, which runs `fast_path.py`, and that passes
`--no-renames` (`fast_path.py` line 79: `args = ["diff", "--name-only",
"--no-renames", f"{base}...{head}"]`), so it is rename-safe. Other
`git diff --name-only` calls in the repo (`conductor_*.py`, `kb.py`,
`skills/review/references/domain-reviewers.md` line 11) are not on the
train's path; the last routes review specialists and does not decide
`gate_paths`. In a temp repo (`main` holding `.github/workflows/validator.yml`,
a branch that `git mv`s it to `docs/validator.yml`):

    $ git diff --name-only main...pr
    docs/validator.yml
    $ git diff --name-only --no-renames main...pr
    .github/workflows/validator.yml
    docs/validator.yml
    $ python3 fast_path.py main pr
    fast-path: review (.github/workflows/validator.yml)
    exit 1

So a bare local `git diff --name-only` has the blind spot, `fast_path.py`
does not, and the skill does not require either.

## Root-cause hypothesis

Hypothesis, not a finding: ADR-0087's consent rule was written as policy
("no `gate_paths` file") with no hook for the file list. Every other input
to the gate has a hook (`ci-status`, `fast-path`, `merge-command`); the
changed-file list does not, so each environment improvises it. ADR-0121
and #1144 hardened the classifier (`fast_path.py`), the one place the file
list is specified, and did not reach the skill's own check.

## Blast radius

- Who: any repo whose queue profile has `merge: auto` and a `gate_paths`
  list, which today is this repo (ADR-0096) running the
  `factory-merge-train` routine every four hours. The exposure is a
  gate-path file moved into an ungated path (a workflow, an ADR, the
  plugin manifest) merging with no human, if the train's source reports
  only destinations. The paths a rename can carry out of the gate are the
  ones `gate_paths` protects: `.github/**`, `docs/adr/**`,
  `.claude-plugin/plugin.json`, `docs/factory/**`.
- Severity: a human gate silently skipped; the other conditions
  (`check` green, reviewer pass or fast-path, no hold label) still apply.
- Since when: ADR-0087's rule (the skill) and the train's first run,
  2026-10-16 00:38 UTC (journal #930).
- Code and docs touched by the fix: `skills/implement-queue/SKILL.md`
  (Phase 3 and the `gate_paths` row), `.claude/implement-queue.md`,
  `docs/factory/merge-train-routine.md`, and a stdlib helper only if
  Implement needs one. `fast_path.py` already owns the rename-safe
  `changed_paths`; the seam rule (AGENTS.md, "Seam modules") forbids a
  second copy, so a helper is a reuse of it or a documented reason not to.
- Mirrors re-checked: `factory_init.MIRRORS` has 39 entries
  (`python3 -c "import factory_init as f; print(len(f.MIRRORS))"`) and a
  filter for `implement-queue` or `fast_path` returns `[]`; the only
  `queue` entry is `work_queue.py`. `factory/manifest.json` has 52
  `files` entries, none under `skills/` and none naming `implement-queue`
  (`grep -c implement-queue factory/manifest.json` printed `0`). So
  `skills/implement-queue/**`, `.claude/implement-queue.md`,
  `docs/factory/merge-train-routine.md` and `fast_path.py` are all
  root-only, and no `update-manifest` is needed unless a mirrored file
  changes.
- Out of reach: glob dialect and case-sensitivity (backlog line 154), any
  change to `fast_path.py`'s classification rule, the journal audit of past
  merges (line 146).

### Does it bite today?

Nothing bites. `gh pr list --state merged --search "merged:>=2026-10-16"
--limit 200` returned 108 PRs (earliest `mergedAt` 2026-10-16T00:39:00Z,
latest 2026-11-04T05:02:07Z; the train's first run being 00:38 UTC in
journal #930). For each, `gh api repos/.../pulls/<n>/files --paginate`
filtered to `status == "renamed"` returned **no renamed file in any of the
108**, so none carried a gate-path source out, and none merged through the
train that way. The only rename in this repo's `main` history is PR #247,
merged 2026-08-11, two months before the train existed. The exposure is
latent: the rule would miss a rename today, but no PR has made one.

## Ruled out

- A rename in any PR since the train's first run: none of 108 (above).
- `fast_path.py` as the broken source: `--no-renames` is there since
  #1144; the temp-repo run above prints `fast-path: review
  (.github/workflows/validator.yml)`.
- `git diff --name-only` as a train source on the train's path: not
  present in the skill, profile or routine.
- A gate-path rename already escaping, through the `fast-path` hook: it
  fails closed on a rename for the same reason.

## In-flight check

Ran at the start of the run, outcome: **nothing matched**; the check ran.

- `gh pr list --state open --json number,title,headRefName` returned `[]`,
  so no open pull request does this (the review surface was reachable).
- `git branch -a --no-merged origin/main` filtered for
  `rename|train|gate|queue|1149|implement-queue`: the names touching the
  surface are `fix/implement-queue-fast-path-consent` (head `a50f14f`,
  2026-10-12, ADR-0088, predating the train), `docs/merge-train-trigger`
  (head `4a8c4fd`, 2026-10-15, the trigger record),
  `feat/implement-queue-skill` and `feat/factory-evolution-queue-groomer`
  (older). `git ls-tree --name-only <branch> docs/features/ docs/fixes/`
  on the first two, filtered for `rename|train|queue`, printed nothing;
  none carries run artifacts for this slug. The remaining `gate`-named
  branches are detectors work. `git ls-tree --name-only origin/main
  docs/fixes/` filtered for `rename` printed nothing.
- `git worktree list` shows this run's own worktree
  (`skills-wt-train-rename`, branch `fix/a-rename-the-merge-train-may-not-see`)
  and `skills-wt-iq` on `feat/implement-queue-skill`, an older branch;
  no other worktree carries a `docs/fixes/` directory for this slug.

## Work items

Shape per the brief: name the source in the skill, make it count rename
sources, and prove it with a test that fails on the pre-fix behaviour.
Implement picks the source and logs why. The table above is the input:
REST `pulls/{n}/files` is the only candidate that reports both paths and
is complete; `gh pr view --json files` is out (destination only, capped at
100); a local diff must use `--no-renames`, which `fast_path.changed_paths`
already does. If the answer is "reuse `fast_path.changed_paths`", it
must be called, not copied (AGENTS.md "Seam modules").

- [x] **Failing tests first** — through a public interface with exact
  output strings, written and run red before the fix.
  - Accept: a PR that renames `.github/workflows/validator.yml` (or
    another current `gate_paths` match) to an ungated path such as
    `docs/validator.yml` is refused by the train's check with an exact
    string naming the old path; the same case fails on the pre-fix
    behaviour (red run quoted); a plain edit to an ungated file is still
    accepted. A real-git case (`TestRealGit` style) covers the rename.
- [x] **Name the source and require rename sources** — in
  `skills/implement-queue/SKILL.md` (Phase 3 rule and the `gate_paths`
  row), say how the changed-file list is obtained, that a rename counts as
  both its old and new path, and that a truncated or partial list fails
  closed (the journal's "read in part" case).
  - Accept: the skill names the source; no sentence leaves it to the
    agent; `python3 lint.py` passes.
- [x] **Profile and routine lines** — add the matching line to
  `.claude/implement-queue.md` and to `docs/factory/merge-train-routine.md`
  §2/§3 where "changed paths against `main`" is stated.
  - Accept: the two files name the same source as the skill; where this
    file and the profile disagree the profile wins (routine's rule), so the
    profile's wording is the one tested.
- [x] **ADR only if the test holds** — apply the protocol's "When to write
  an ADR" test; if it holds, write one as `provisional` and add its README
  row and the status-line pointer on the ADR it amends (ADR-0087 or
  ADR-0096).
  - Accept: either an ADR with matching README row, or a line in Notes
    saying why the test does not hold.
- [x] **Claim the seed** — append
  `(claimed: maintenance:a-rename-the-merge-train-may-not-see)` to
  `docs/backlog.md` line 144.
  - Accept: line 144 ends with the claim marker; no other line changes.
- [x] **Full gate** — run the suite and gates.
  - Accept: `python3 run_tests.py`, `python3 lint.py`,
    `python3 kb.py drift`, and `python3 gates.py && python3 gates.py
    --selftest` all pass; if a mirrored file changed, `python3
    factory_init.py update-manifest` was run first (after deleting stray
    `.orig`/`.rej`), and detector E is clean. A failed full-suite run is
    never reported as a pass: re-run it when load drops and record
    `uptime`.

Out: the other backlog seeds (145 onward), glob dialect and
case-sensitivity, any change to `fast_path.py`'s classification rule.
Constraints: stdlib only; problem-string contracts with exact string
asserts; never edit `.claude-plugin/plugin.json` (ADR-0095); write no
literal four-digit work-order or PRD-style id that does not exist.

## Notes

- 2026-11-03: Tracker: the PR closes #1149 with `Closes #1149` and
  carries a `No work order:` line (brief). Release is prepare and stop;
  the PR touches `skills/implement-queue/**`, `.claude/implement-queue.md`
  and `docs/factory/**` (a gate path), so the train holds it for a human
  merge.
- 2026-11-03: Not tested: the GitHub MCP file-list tool the journal's
  cloud runs use. Whoever picks the source should treat its rename
  behaviour as unknown until a run records it.
- 2026-11-03: Implement, source choice. The train's gate check reads the
  profile's new `changed-files` hook: with a checkout, `python3
  fast_path.py gate origin/main HEAD` (a new `gate` mode on the existing
  owner; it calls `changed_paths`, so `--no-renames` lists a rename's old
  and new path; no new module, no copy, seam rule kept); with no
  checkout, REST `pulls/{n}/files --paginate` taking `filename` and
  `previous_filename` (the only candidate in the table that is both
  rename-aware and complete). `gh pr diff --name-only` and `gh pr view
  --json files` are named as excluded. Reversible, inside the brief.
  The skill stays harness-neutral: it says what the list must hold and
  that a partial one fails closed; commands live in the profile. The
  skill's `changed-files` default is "none", so a repo with no hook gets
  a human merge for every PR under `merge: auto`.
- 2026-11-03: Red run, before the fix (`python3 -m unittest
  tests.test_fast_path`): `Ran 31 tests ... FAILED (failures=7)`, all in
  `TestGateMode`, e.g. `test_a_rename_out_of_a_gate_path_in_real_git_is_human`
  and `test_a_plain_edit_to_an_ungated_file_is_clear`; the gate mode did
  not exist, so main printed the usage text and exit 2. Green after the
  fix: `Ran 32 tests ... OK` (the 32nd pins skill, profile and routine
  to one source). The real-git rename case prints exactly
  `gate-paths: human (.github/workflows/validator.yml)`, exit 1; a plain
  edit to `lint.py` prints `gate-paths: clear`, exit 0; a failed git
  prints the `fast-path: git diff ... failed:` string, exit 2.
- 2026-11-03: No ADR. The protocol's test needs all three legs; this
  fails them: a hook name plus a `fast_path.py` mode is easy to reverse,
  is the obvious reading of ADR-0087's existing rule, and trades off
  nothing real. The rule is unchanged; only its input is named.
- 2026-11-03: Backlog line 144 now ends with
  `(claimed: maintenance:a-rename-the-merge-train-may-not-see)`.
- 2026-11-03: Full gate, clean (load average 6.63 at the end of the run,
  `uptime`): `python3 run_tests.py` printed `tests: 3986 tests across 126
  modules in 27.1s on 8 workers, 0 problem(s)`; `python3 lint.py`:
  `lint: 0 problem(s) across 35 skills`; `python3 kb.py drift`:
  `drift: 0 problem(s)`; `python3 gates.py`: `gates: 0 problem(s)`;
  `python3 gates.py --selftest`: `selftest: ok`. No mirrored file changed
  (`fast_path.py`, the skill, the profile and the routine are root-only),
  so `update-manifest` was not needed.
