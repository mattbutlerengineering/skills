---
stage: capture
run: maintenance:tool-duplicates-that-drifted
date: 2026-10-25
re-entry: implement
---

# Condition: root tools hold second copies of one fact, and several have drifted

## Defect (or Condition)

The 2026-10-25 consolidation audit found that several root tools state the
same fact or run the same logic in two or more places, and some copies
already disagree. The cases below are the ones that meet CLAUDE.md's bar
for a shared function: multiple real callers, and observed divergence.

- **Is this token a repo path?** `kb_drift.path_token`, `md_claims._is_path`
  and `gates.ARCH_PLAIN_PATH` disagree on `@`, the extension list, `:N:M`
  against `:N-M`, fragments, and bare top-level directories.
- **The digest and miner issue upsert.**
  - `gate_digest._post_digest` and `rejection_mining._post_queue` are the
    same create-or-update-and-pin, differing only in label and title.
  - Their list-and-timelines startup is copied, and their `LIST_ARGS` and
    `ISSUE_ARGS` state the same value.
  - `LIST_WINDOW = 1000` is restated in five modules, though each comment
    says `cli.gh_read` owns it.
- **Reading JSON lines.** Seven readers catch different errors:
  `dashboard.py` misses `RecursionError`, and `conductor_close.py` and
  `kb_harvest.py` catch only `ValueError`.
- **The active-run walk.** `dashboard.py` lacks `board.py`'s per-run
  exception guard, so one broken run aborts the dashboard's gather.
- **Month-to-date spend** is computed in `work_queue.month_to_date`
  (unrounded) and in `cost_report.aggregate` (rounded to cents).
- **The PR-closes-issue join** in `dashboard.py` skips the fork guard that
  `assembler.py` applies (`isCrossRepository`).
- **Coincidences `one_owner.py` reports as one fact** (same literal or keys,
  different meaning) carry no `# one-owner:` marker (ADR-0061).

Target state: each fact has one owner and its callers import it.
`python3 one_owner.py` prints `one-owner: 0 problem(s)`. Every behaviour
change a consolidation makes is deliberate and shown as a before/after
diff.

## Reproduction / Evidence

`python3 one_owner.py` on `origin/main` (`f905d53`):

```
one-owner: budget_guard.py:55 CONTINUE and cost_report.py:44 CONTINUE state the same value — one fact, one owner
one-owner: conductor_consent.py:112 standing_problems and factory_config.py:315 _standing_problems read the same payload keys (enabled, tier_labels) — one fact, one owner
one-owner: conductor_merge.py:75 COSTS and cost_ledger.py:29 COST_LEDGER state the same value — one fact, one owner
one-owner: conductor_plan.py:506 payload_version and factory_init.py:378 tools_only_manifest read the same payload keys (plugin, version) — one fact, one owner
one-owner: cost_ledger.py:50 AT_DATE and trace.py:61 DAY state the same value — one fact, one owner
one-owner: dashboard.py:152 _pr_by_issue, gate_digest.py:185 run_daily and rejection_mining.py:301 run_mine read the same payload keys (body, number, state) — one fact, one owner
one-owner: eval_schema.py:294 validate and trigger_eval.py:408 score_case read the same payload keys (expected, id, kind, query) — one fact, one owner
one-owner: gate_digest.py:123 LIST_ARGS and rejection_mining.py:72 ISSUE_ARGS state the same value — one fact, one owner
one-owner: gates.py:332 ARCH_PLAIN_PATH and md_claims.py:61 PATH_CHARS state the same value — one fact, one owner
one-owner: 9 problem(s)
```

The COSTS pair belongs to the sibling run `a-spend-row-stalls-the-merge`
(#1106).

Path-rule divergence: over every inline-code span in the repo's tracked
markdown (12,644 distinct spans), `kb_drift.path_token` and
`md_claims._is_path` disagreed on 212.

- 109 were paths only kb_drift accepted. Examples:
  `docs/factory/corrections.jsonl`, `docs/assets/skill-map.svg`,
  `CLAUDE.md#no-such-anchor`, and bare `docs/`.
- 103 were paths only md_claims accepted, for example `gates.py:777-778`.

## Root-cause hypothesis

The copies were each written correctly for their first caller, and a
second caller then copied the logic instead of importing it. This is what
`one_owner.py` (ADR-0061) was built to catch. Its first-pass findings were
left undecided in `docs/backlog.md`.

## Blast radius

Root tools and payload tools. Payload changes reach stamped repos on
`factory-init update`. The real-world effects are:

- detectors that miss dangling paths;
- a dashboard that aborts on one malformed run;
- a dashboard that maps a fork's PR to an issue;
- spend totals that disagree by rounding.

None of them corrupts data.

## Ruled out

These have no observed divergence, so they fall below CLAUDE.md's bar for
a new shared function:

- the git call wrappers in conductor_flow, conductor_run, conductor_close,
  decompose_signals, decompose_lessons, kb and trace, which differ only
  cosmetically;
- `_read_all` in decompose_grade and voice_grade;
- the batch planners' shared over-the-cap test;
- the two budget calibrators;
- each module's `LIST_WINDOW` value (see Notes);
- month-to-date spend: `work_queue.month_to_date` and
  `cost_report.aggregate` already share the row rule,
  `cost_ledger.dispatched`, and both docstrings say so. They differ only
  in rounding at display, so a third function would add an owner, not
  remove one (Notes);
- the PR-closes-issue joins: `assembler._find_pr` finds the agent's own PR
  for one issue, and its fork guard is a security control, because that
  number is dispatched to a validator that runs the PR's code.
  `dashboard._pr_by_issue` maps every issue to the PR that closed it, for
  acceptance and rework rates, ranking merged over open over closed. A
  merged fork PR did close its issue, so copying the guard would make the
  metric wrong. They are two joins, not one (Notes).

`fast_path`'s gate paths omit `.claude-plugin/plugin.json`. That is
harmless today, since only `docs/` paths are low-risk, so it is seeded,
not fixed. Merging any skill is also out: the Owner deferred that to a
backlog seed pending a routing eval.

## Work items

- [x] **One repo-path rule** — `knowledge_plane.repo_path(token,
  top_level_dirs=True)` and `knowledge_plane.PLAIN_PATH`. kb_drift and
  md_claims call it, with md_claims passing `top_level_dirs=False`, and
  `gates.ARCH_PLAIN_PATH` is `PLAIN_PATH`.
  - Accept: `TestRepoPath` passes. `kb.py drift` prints 0 problems before
    and after. md_claims' before/after diff over the same tree is
    explained.
- [x] **One issue upsert and one queue read** — upsert-and-pin and the
  marked-issue lookup in `cli.py`. The list-and-timelines startup goes in
  `human_gates.py` as `read_gate_issues`.
  - Accept: the gate_digest and rejection_mining suites pass unchanged in
    their asserted strings, and `one_owner.py` no longer names
    LIST_ARGS/ISSUE_ARGS or the body/number/state group for those two.
- [x] **One JSON-lines reader** — `cli.json_lines(text)` yields `(lineno,
  value, error)` under the ADR-0075 guard, and each caller keeps its own
  policy. The callers are cost_ledger.parse, conductor.parse,
  conductor_close.history, kb_harvest and dashboard._corrections.
  - Accept: a `RecursionError` line is an error for every reader. Tests pin
    the three that raised before: conductor_close, dashboard and
    kb_harvest.
- [x] **One active-run walk** — `knowledge_plane.active_runs(root)`, next to
  the `run_dirs` it walks. It is not in `protocol`, which must not import
  knowledge_plane. dashboard and board call it, and dashboard reports a
  broken run instead of aborting.
  - Accept: a fixture with one unreadable run renders the rest, and the
    problem is named.
- [x] **Mark the coincidences** — paired `# one-owner:` markers for the four
  pairs that are not one fact. Three cite ADR-0061, and eval_schema against
  trigger_eval cites ADR-0022. The fifth pair, the manifest's
  `plugin`/`version` keys, turned out in review to be one fact. It is
  folded into `gates.MANIFEST_PAYLOAD_KEYS` instead of being marked.
  - Accept: `python3 one_owner.py` prints `one-owner: 0 problem(s)` once
    #1106 is merged in.
- [x] **Backlog** — claim the one-owner seed in `docs/backlog.md`, and seed
  the `fast_path` gate-path gap and the deferred skill merge.
  - Accept: the seed lines carry `(claimed: maintenance:...)` and the new
    seeds follow the protocol's grammar.
- [x] **Payload and checks** — `update-manifest`, then the four CI commands.
  - Accept: each prints 0 problems and the selftest prints ok.

## Notes

- 2026-10-25, Implement: `LIST_WINDOW` stays per module. It is 100 in
  work_queue, 500 in sweeps and 1000 in five others. `cli.gh_read` owns
  the window mechanism (the limit sent equals the limit the truncation
  check tests), and each caller owns its own value. Folding the five
  1000s together would merge five policies, not one fact. Moved to Ruled
  out.
- 2026-10-25, Implement: `decompose_lessons._parse` keeps its own loop. It
  reads its own file, where a blank line is a defect, not a separator, so
  `json_lines`' blank-line skip would change its contract.
- 2026-10-25, Implement: two of the audit's items fell on reading the
  code. The audit had listed month-to-date spend and the PR-closes-issue
  join as duplicates. One already has a single owner for its rule, and the
  other is two different questions. Both moved to Ruled out instead of
  being built, so the run adds no owner that the code did not need.
- 2026-10-25, Review: the shared upsert and gate-issue read (item 2) meet
  CLAUDE.md's bar on one_owner's evidence: the LIST_ARGS/ISSUE_ARGS pair
  and the body/number/state key group were already flagged as two owners.
  The two posting functions themselves had not yet diverged beyond their
  label and title. `conductor.numbered` still states the "non-blank
  line" rule beside `cli.json_lines`, and is left as a small second owner
  for its line-number callers.
- 2026-10-25, Review: the path rule's whitelist reads some tokens kb_drift
  used to accept as paths differently, and the reverse.
  - Now refused: `%`, `!`, `&`, `;` and `^` in a path. `+` is allowed again,
    after review, for SvelteKit's `+page.ts`.
  - Now checked: a mid-path `@`, an uppercase extension, a `#fragment` span
    and a `:12-20` range.
  - kb drift prints 0 problems before and after on this repo, and kb_drift
    is root-only (not in MIRRORS), so stamped repos are unaffected.
- 2026-10-25: Run B of the Owner-approved consolidation wave. Scope: tool
  duplicates that have drifted, with no skill merges. Sibling runs:
  `a-spend-row-stalls-the-merge` (#1106) and
  `one-owner-for-copied-skill-text` (#1108).
