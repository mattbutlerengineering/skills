# `claude plugin eval` is an on-demand harness with its own tree

- Status: accepted
- Date: 2026-10-10

Amends no record. ADR-0012 and ADR-0019 stand: a skill graduates past
draft only via a real run, and evals never graduate maturity. ADR-0024
stands: `eval_schema.py` owns `evals/results/` and its naming grammar.
This adds a third eval harness beside `trigger_eval.py` and
`charter_replay.py` and decides where it lives.

## Context

Issue #633 asked whether "jev | claude codemods" had anything for this
repo. The research (`docs/research/jev-codemods-and-plugin-eval.md`)
found that the useful thing was neither. It was `claude plugin eval`
(Claude Code v2.1.269+). The command runs a plugin's eval cases in
isolated `claude -p` sessions and grades each run. Graders are `regex`,
`tool_used`, `tool_order` and `file_exists`, which are free, plus `llm`
and `baseline`, which call a judge. It repeats every case with no plugin
loaded and reports `WITH`, `W/OUT` and their delta, `Δ`. Neither of the
repo's harnesses measures that delta. `trigger_eval.py` measures which
skill fires, and `charter_replay.py` replays role charters. The owner's
decision on #633 was "Adopt plugin eval".

The installed CLI (2.1.296; `claude plugin eval --help`) was read
before deciding. The hazard is its default directory. Cases are read
from `<plugin>/evals/**`, and results go to `<plugin>/evals/results/<timestamp>/`
unless `--eval-dir` or the manifest's `experimental.evals` says
otherwise. That default is this repo's append-only results tree. Its
names follow a grammar `eval_schema.py` owns (ADR-0024). A bare
`claude plugin eval .` would write timestamp directories into it that
the grammar does not describe.

## Decision

1. **The suite lives in `plugin-evals/`, and the manifest says so.**
   `.claude-plugin/plugin.json` carries
   `"experimental": {"evals": "plugin-evals"}`, so a bare
   `claude plugin eval .` and a bare `claude plugin eval init` both use
   it, and a forgotten flag cannot reach `evals/`. Cases are grouped by
   skill (`plugin-evals/<skill>/<case>/`), each case tagged with the
   skill's slug so `--tag <skill>` runs one suite. The first three
   suites are `lean`, `next` and `implement`.
2. **`evals/results/` is not touched.** ADR-0024's grammar is not
   widened for this harness. Its output is a timestamp directory holding
   an HTML report and a JSON document whose schema the CLI owns (camelCase,
   `schemaVersion: 1`), not a record this repo writes. So
   `plugin-evals/results/` is gitignored scratch. A run that is cited
   anywhere, in a PR, an issue or LEDGER.md, has its
   `aggregate-result.json` copied unedited to
   `plugin-evals/records/<YYYY-MM-DD>[-N].json` and committed.
   `-N` distinguishes same-day runs, as in `evals/results/`. That
   directory is append-only, under the same honesty policy as
   `evals/results/`. No code reads it yet. If a second caller appears,
   the grammar moves into `eval_schema.py` under ADR-0024's bar, and
   not before.
3. **On demand only, never CI.** Every run and every judge call is a
   real model call billed to the operator. It joins the repo's other
   paid harnesses (CLAUDE.md, "On demand only"). No workflow invokes
   it, and none may.
4. **Every cited run pins its models and caps its cost.** The
   documented command passes `--model` and `--judge-model` explicitly,
   so a model rollout is not mistaken for a skill regression. It also
   passes `--max-cost-usd`, `--no-publish`, and the grants the cases
   need: `--scaffold` and
   `--allow-tools Write Edit "Bash(python3 *)" "Bash(git *)"`. Both are
   safe here because the cases and scaffold scripts are this repo's
   own. A run that hits the ceiling exits 2 with `partial: true`. Such
   a run is never cited as a result, and neither is a run whose judge
   graders were skipped (`skippedPaidGraders`).
5. **What a result may and may not claim in LEDGER.md.** A plugin-eval
   record is eval evidence. Under ADR-0019 it never graduates maturity.
   `draft` → `used-once` still takes a real pipeline run. A record may
   be cited beside a skill's row as supporting evidence about that
   skill, such as "with/without Δ +0.40 on `lean`, n=3 per arm". It may
   be cited only when all of these hold. The record came from a run
   that actually executed and was committed under `plugin-evals/records/`
   unedited. It is not partial. Its model pins are visible in the file.
   The claim quotes the `WITH`/`W/OUT`/`Δ` figures the file holds and
   nothing derived beyond them. A hand-written, edited or projected
   result is fabricated evidence (CLAUDE.md, "Eval honesty").
6. **The case definitions follow the trigger-eval rule.** A failing case
   is never edited to pass. A case changes only when its expectation
   proves ambiguous or non-discriminating, and the commit message says
   so. A case where `WITH` and `W/OUT` are both 1.0 is
   non-discriminating. It shows the plugin is not what made the case
   pass, and that is grounds to sharpen the case, not to cite it.

## Rejected alternatives

- **Jev (TypeSafe's decision model) and the community mods built on it**
  (Jev Model Router, Jev Skill Suggestion, cc-mod-jev, claude-code-jev).
  TypeSafe paused new signups in late September 2026. Each mod needs a
  second API key and bill. Mods run unsandboxed with the user's full
  permissions. No independent benchmark of the claimed savings exists.
  Skill suggestion would also stand in for the description routing that
  `next` and `trigger_eval.py` measure, which would make future trigger
  results non-comparable with the recorded ones.
- **A first-party Claude Code mod for the pipeline** (for example a
  band above the prompt showing the active run and stage). A mod is a
  JS/TS `register` module. That breaks the stdlib-only Python convention
  and has no omp equivalent, so harness parity (ADR-0031, ADR-0076)
  would break. It would also ship unsandboxed code to every consumer
  while the mods rollout is still unsettled. Deferred, not adopted.
- **Codemod.com AI codemods** (`codemod learn`, jssg/ast-grep
  transforms). These are aimed at JS/TS framework migrations. This repo
  is stdlib Python and markdown, and has no mechanical migration that
  needs them.
- **Writing plugin-eval output into `evals/results/`.** That would mean
  either widening ADR-0024's grammar to timestamp directories and a
  CLI-owned JSON schema, or renaming the CLI's output on the way in. The
  first gives `eval_schema.py` knowledge it cannot validate. The second
  is a hand step that could alter a record. A separate tree keeps both
  records honest at the cost of one more directory.
- **Running it in CI.** The repo's rule for paid harnesses is on demand
  only. A threshold gate would also turn the noise of a 3-run sample
  into red builds.

## Consequences

- `plugin-evals/` holds five cases: `lean/stdlib-first`,
  `lean/cut-list`, `next/no-run`, `next/idea-exists` and
  `implement/one-item-test-first`. At 3 runs per arm that is 30 agent
  runs plus judge calls for each full suite.
- No detector or lint check reads `plugin-evals/`. Its markdown sits
  outside the trees detectors C, D and I scan, so the fixture artifacts
  inside scaffold scripts cannot be read as this repo's own run state.
- No plugin-eval record exists yet. The first cited run lands its record
  in its own PR.
