---
stage: architect
run: feature:decompose-outcome-signals
date: 2026-10-18
ux: skipped — CLI measurement tool with text output only; no screens or flows.
assumptions:
  - "No live interview: every PRD open question was settled from autorun-brief.md, idea.md, prd.md, the code and a throwaway prototype run against this clone's refs (scratchpad only, nothing committed), taking the recommended default each time. Nothing here is expensive to reverse before the first record lands. Both ADRs are provisional."
  - "Recommended default taken (ref set): the tool reads every ref the clone holds except refs/stash, and it is not configurable. The output names each namespace read with its count, plus a digest of the ref tips. A stash commit snapshots uncommitted work, so it could pass for an inferred boundary. A --refs option has no caller (YAGNI). Measured 2026-10-18: 1086 refs besides refs/stash, 488 of them under refs/remotes/pr."
  - "Recommended default taken (subject-match strictness, ADR-0109): a boundary is observed when the subject reads `docs(<any scope>): <stage>` with the stage as a whole word, and the commit changes that stage's artifact in this run's directory. The scope is not compared with the slug, and the em dash is not required. There is no third label. Measured: slug-equal plus em dash finds observed decompose boundaries for 2 runs. The path-anchored rule finds 4, adding software-factory (scope `factory`) and the-reviewer-token-runs-agent-code (scope `reviewer-token`)."
  - "Recommended default taken (work-item identity): a work item's key is its row's leading label (a WO token, or a short label like A1 or I2 at the start of the bold span), else the bold text, else the row text up to the first ` — `. When a dropped item and an added item have the same title, the item was renamed, which is not a re-plan; codex-style-standards-enforcement's WO renumbering is the measured case. A split or merge is detected only by citation: a row outside its `blocked by:` clause names the work items it became, or the ones it absorbed. first-live-dispatch's superseded row is the measured case. Duplicate keys in one version make that run's re-plan signal unmeasurable."
  - "Recommended default taken (inferred design gaps): when a run has no observed decompose boundary, the design-gap signal is read from the `## Design gaps found` section that Decompose's TEMPLATE.md requires, in the breakdown version at the decompose boundary. A section whose first word is `none` gives 0. Any other content gives 1 route. A missing section makes the signal unmeasurable. The alternative was a later commit touching architecture.md, and the prototype found 6 such commits inside an inferred window. By subject, every one was a batch landing, a closure or a feature commit, not a route back to Architect."
  - "Recommended default taken (what a finding is): a heading of level 2 to 4, outside fences, whose text (emphasis stripped) starts with a severity word (critical, major, minor, low, medium, high) or an ordinal label (F1, Finding 1, 1.). A finding names a work item when its block holds one of the current breakdown's item keys as a whole token. The prototype found 184 findings in 34 review.md files, 32 of them naming an item: design evidence only, not the baseline."
  - "Recommended default taken (review-traced labelling): review-traced reads the committed review.md and breakdown.md and no boundary, so every measured run is observed for it. Its inferred population always prints as 0 run(s), so the line keeps the same shape as the other two signals."
  - "Recommended default taken (record location): `evals/results/decompose-signals-<date>[-N].json`, written by `--record` through eval_schema.write_snapshot as a third snapshot kind. eval_schema already owns that append-only naming grammar, and charter replays set the precedent for factory evidence that is never LEDGER evidence. A new directory would need a second owner of the -N grammar."
  - "Codebase default taken (unmeasurable is per signal): a run can be unmeasurable on re-plan and still measured on review-traced. Each per-run line gives the reason for each unmeasurable signal, and that signal's aggregate leaves the run out (the fail-closed roll-up: unknown never counts as zero)."
  - "Owner decision 3 kept as written: the inferred implement boundary is the first commit that ticks a row, which is the start of Implement. The observed one is the protocol's `implement` commit, which is the end of it. Measured on the 3 runs with an observed implement boundary: the work-item keys at the first tick equal the keys at the implement commit in all 3, so today the two windows agree. The aggregate splits the populations anyway, and the gap is recorded under Consequences in ADR-0109."
---

# Architecture: Decompose outcome signals from git history

## Approach

One root-only, stdlib module, `decompose_signals.py`, with a pure core
and one git adapter. A single `git log` walk over every ref, restricted to
run artifact paths, gives each run's commits in author-date order, with
subject and changed files. Boundary policy finds the decompose (D) and
implement (I) boundaries in that list and labels each one observed or
inferred (ADR-0109). Blob reads fetch only the versions the policy asks
for. Three pure signal functions then take text and return counts or an
unmeasurable reason: work-item diff D→I, design-gap routes, and
review-traced findings. A renderer turns the result into per-run lines and
an aggregate in the problem-string / count contract. `--record` writes the
same result through `eval_schema.write_snapshot`. Run enumeration, the row
grammar, fences, the stage→artifact table and the run-ref come from
`knowledge_plane.py` and `protocol.py` and are never retyped.

The other shape compared was a per-run tool: `git log --follow` per
breakdown, with `git show` for every version. It loses on cost and on
one-owner grounds. The prototype's per-path walk, which read every
version with `git show`, took 9.6 s. One pathspec walk over the same 1086
refs found the same 481 commits in 0.35 s, before any blob read. The
per-run shape would also rebuild the run walk that
`knowledge_plane.breakdown_files` already owns.

Where each PRD success criterion is met:

| PRD success criterion | Where |
|---|---|
| One invocation, per-run lines plus an aggregate | Report and front door |
| Observed/inferred labels, and populations in the aggregate | Boundary policy (ADR-0109), Report |
| Unmeasurable runs named, kept out of aggregates | each signal's unmeasurable reason, Report |
| Refs read and the rule applied are named | History adapter's ref listing, Report header |
| No network; git only, through `cli.py` | History adapter |
| Five fixture cases, exact strings | real temp git repos (Decisions) |
| No `review.md` versus findings that name no item | Review tracer's three shapes |
| First numbers recorded append-only and reproducible | `--record` through eval_schema; `refs_digest` |
| The five repo checks pass | ADR-0110 and the dual-membership pin, plus the `factory.py` verb row |

## Components

### History adapter (`read_history`, `read_version`)

- Responsibility: the only code that talks to git. It lists refs
  (`for-each-ref`, minus `refs/stash`), walks them once
  (`log --stdin --author-date-order --reverse --name-only` over
  `:(glob)docs/*/*/{breakdown,architecture}.md` and the product-run
  paths), and reads one blob (`show <sha>:<path>`). It turns
  `cli.CLI_FAILURES` into `decompose-signals:` problem strings. It never
  runs `fetch`, `ls-remote`, `pull` or `remote`.
- Collaborators: `cli.runner("git", timeout=…)`, injected as `run`. There
  is no module-level `git_runner` alias, because one would join
  one_owner's ADR-0061 alias group. Tests drive it against real temp git
  repos plus a failing fake, which makes two adapters.

### Boundary policy (`boundaries`)

- Responsibility: from one run's ordered commits, pick D and I and label
  each one (ADR-0109), or name why the run has none.
  - Observed D: the earliest commit whose subject matches
    `docs(<scope>): decompose` and which changes the run's
    `breakdown.md`. Inferred D: the earliest commit that changes it.
  - Observed I: the earliest commit after D whose subject matches
    `docs(<scope>): implement` and which changes the run's
    `breakdown.md`. Inferred I: the earliest commit after D whose version
    has a done row (`knowledge_plane.breakdown_rows`, field `done`).
  - The artifact for each stage comes from `protocol.STAGE_ARTIFACTS`.
- Collaborators: the history adapter, for the versions it must inspect.
  It is pure over (commits, version reader).

### Work-item diff (`item_keys`, `replan`)

- Responsibility: the key of each work item in one breakdown version, and
  the D→I diff as added, dropped, split, merged and renamed counts.
  - Rename: an unmatched dropped/added pair with equal normalized
    titles. Titles come from `knowledge_plane.row_title` for WO rows and
    from the text after the label for label rows.
  - Split: one old work item whose I-version row cites at least 2 added
    keys, or a dropped item cited by at least 2 added rows.
  - Merge: one added row that cites at least 2 dropped items.
  - Citations are read from the row line with its `blocked by:` clause
    removed (`knowledge_plane.BLOCKED_BY`), so a dependency is never read
    as a split.
  - Re-plan count = added + dropped + splits + merges. Renames count 0.
    The rate's denominator is the number of work items at D.
- Collaborators: `knowledge_plane.parse_row` / `breakdown_rows`,
  `WO_TOKEN`, `BLOCKED_BY`. It is pure over two lists of lines.

### Design-gap count (`design_gaps`)

- Responsibility: route events back to Architect inside (D, I].
  - With D observed: the number of commits in the window whose subject
    matches `docs(<scope>): architect` and which change the run's
    `architecture.md`. Labelled observed when I is observed, else
    inferred.
  - With D inferred: read the `## Design gaps found` section of the D
    version. First word `none` gives 0, other content gives 1, and a
    missing section gives unmeasurable. Labelled inferred.
- Collaborators: the boundary result and `knowledge_plane.unfenced`.

### Review tracer (`review_findings`)

- Responsibility: the findings in the run's working-tree `review.md` (the
  grammar is in the assumptions above), and how many of them name a key of
  the working-tree breakdown. It returns one of three shapes:
  - no `review.md`;
  - a `review.md` with no heading the grammar reads;
  - N findings, of which M name an item.
- Collaborators: `cli.read_file(path, shown, str)` and
  `knowledge_plane.unfenced`. It is pure over two texts.

### Report and front door (`measure`, `render`, `main`)

- Responsibility: enumerate runs with `knowledge_plane.breakdown_files`
  and label them with `protocol.run_ref`, assemble each run's record, the
  aggregate and the header, print through `cli.report`, and with
  `--record` write the snapshot. A `factory.py` `VERBS` row
  `decompose-signals` is required by `tests/test_factory_cli.py`.
- Collaborators: every component above, plus `eval_schema.write_snapshot`.

## Data model

Access patterns: (1) one invocation reads every run and prints every line
once; (2) #987 reads the recorded JSON and compares populations;
(3) a rerun on the same refs must reproduce it. That is why the record is
one immutable document per invocation, with nothing stored between runs.

```
Commit      {sha, author_time, subject, files[]}         # order = walk order
Boundary    {sha, label: observed|inferred} | {unmeasurable: reason}
RunRecord   {run: "feature:<slug>", path,
             decompose: Boundary, implement: Boundary,
             replan:  {label, items_at_d, added, dropped, split, merged,
                       renamed, count} | {unmeasurable: reason},
             design_gaps: {label, routes, source: subjects|section}
                          | {unmeasurable: reason},
             review: {label: observed, findings, named}
                     | {findings: 0, reason: "no finding heading"}
                     | {unmeasurable: "no review.md"}}
Aggregate   per signal × {observed, inferred, combined}:
             {runs, numerator, denominator}
Snapshot    {date, head, refs: {namespace: count}, refs_digest,
             rule: <boundary rule sentence>, runs: [RunRecord],
             aggregate: Aggregate}
```

Invariants and who owns them: boundary labels belong to the boundary
policy, and a signal's label is observed only when every boundary it read
is observed. Unmeasurable never reaches an aggregate, a rule the
aggregate owns. `refs_digest` is the sha256 of the sorted
`refname sha` lines, so two records can show they read the same refs.
Ordering is by run path, which keeps output deterministic.

## Interfaces & contracts

### `python3 decompose_signals.py [--record]` (also `python3 factory.py decompose-signals`)

- Input: the clone's refs and working tree, read-only. No network.
  Fetching PR heads is the documented manual step,
  `git fetch origin '+refs/pull/*/head:refs/remotes/pr/*'`, which goes in
  the module docstring and the CLAUDE.md on-demand bullet.
- Output, stdout, in this order. Implement pins the exact strings in
  tests:
  - `decompose-signals: refs read — <ns> (<n>), …; refs/stash skipped; digest <12 hex>`
  - `decompose-signals: boundary rule — <ADR-0109 rule, one sentence>`
  - one line per run, for example
    `decompose-signals: feature:<slug> — decompose observed <sha7>, implement inferred <sha7>; re-plan 1 of 9 (added 1, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 3 of 12 findings name an item`
  - an unmeasurable signal prints `<signal> unmeasurable — <reason>`.
    The reasons are fixed strings:
    - `no commit on the refs read changes <path>`
    - `the first version (<sha7>) already checks <n> of <m> rows`
    - `no implement boundary: no later commit checks a row`
    - `duplicate work-item key <key> at <sha7>`
    - `no "Design gaps found" section at the decompose boundary`
    - `no review.md`
  - A `review.md` with no heading the grammar reads prints
    `review-traced 0 findings — review.md has no finding heading`, which
    is distinct from `0 of N findings name an item`.
  - three aggregate lines, one per signal:
    `decompose-signals: aggregate <signal> — observed <num>/<den> over <r> run(s); inferred …; combined …; unmeasurable <u> run(s)`
  - the `cli.report` summary,
    `decompose-signals: <R> run(s), <P> problem(s)`. The prefix is
    computed, never typed by hand.
  - with `--record`: `decompose-signals: recorded evals/results/decompose-signals-<date>[-N].json`.
- Exit: 0 when no problems, even with unmeasurable runs, because
  unmeasurable is data. 1 with problems. 2 on an unknown argument, with
  usage printed (one_owner.py's precedent).
- Failure modes:
  - git missing, not a repo, or a call exceeding its timeout (60 s per
    call, local and read-only, so a retry is safe): a problem string
    `decompose-signals: git <verb> failed: <cli.detail>`.
  - A failed `for-each-ref` or `log` prints no run lines.
  - A failed `show` makes the affected signals of that run unmeasurable
    with the reason `read failed`, plus one problem string.
  - An unreadable `review.md` or `breakdown.md` gives the `cli.read_file`
    problem, prefixed with the label.
  - `--record` refuses with a problem string, and writes nothing, when
    `git status --porcelain -- docs/` is non-empty, because a record must
    be reproducible from the refs. It also refuses when there were any
    problems.

### `eval_schema` gains a snapshot kind

- Input: `results_path(results_dir, "decompose-signals", date)` and
  `write_snapshot(output, results_dir, "decompose-signals")`.
- Output: `evals/results/decompose-signals-<date>[-N].json`, with the same
  indented-JSON serialization as the existing kinds. It is not added to
  `_RESULTS_LINK`, so it can never be LEDGER evidence, like `charter`.
- Failure modes: unchanged (`ValueError` on an unknown kind).

## Stack & dependencies

- Python 3 stdlib only (`hashlib`, `json`, `re`, `datetime`), per the
  stdlib-only rule.
- git through `cli.runner`, the only external CLI. git is stable and
  local, so it needs no seam beyond the injected `run`.
- Root-only: no payload tool imports it (ADR-0060), so there is no
  `factory_init.MIRRORS` change and no manifest regen. It adds three
  root-only → mirrored pairs (`cli`, `knowledge_plane`, `protocol`),
  recorded in ADR-0110, and `tests/test_dual_membership.py`'s pin moves
  with them. `eval_schema` is root-only and adds no pair.
- Docs touched: a CLAUDE.md "on demand, free" bullet beside
  `one_owner.py`, an `evals/README.md` results-layout line, and one
  CONTEXT.md entry, **Outcome signal**. No Makefile or CI line: this is
  a measurement, not a gate.

## Decisions & alternatives

- **Path-anchored, scope-agnostic observed rule** over slug-equal plus em
  dash: the strict rule finds 2 observed decompose boundaries and misses
  two real stage commits whose scope is not the directory name (ADR-0109).
- **Two labels** over a third `loose` label: a commit that names the stage
  and writes its artifact is the protocol's boundary commit, and a third
  population would split an already small sample (ADR-0109).
- **All refs minus refs/stash, fixed** over a `--refs` option: the output
  names the namespaces and a digest, which answers the reviewer's
  coverage question without an untested knob.
- **One pathspec walk plus lazy blob reads** over a per-run
  `log --follow`: 0.35 s for the walk against 9.6 s for the per-path
  prototype, and history under a renamed directory is an accepted miss.
- **Citation-based split/merge** over a per-commit heuristic ("one dropped
  and two added in one commit is a split"): the heuristic reads
  codex-style-standards-enforcement's six-for-six WO renumbering as six
  splits. Title-match renames handle that case.
- **Design gaps from the template's section when D is inferred** over
  architecture.md touches: all 6 touches inside an inferred window were
  noise, judged by subject.
- **Heading-led finding grammar** over the template's exact
  `### <Severity>:` only: the strict form misses the ordinal-led shapes
  (`## F1 —`, `### Finding 1 —`, `### 1.`) in 7 fixes runs' reviews, and
  the `### Major — ` shape in 2 more.
- **Record in `evals/results/` through eval_schema** over a new
  `docs/factory/` directory: one owner of the append-only naming grammar.
- **Root-only, its own module** over a `kb.py` or `gates.py` subcommand:
  gates.py is mirrored, and kb.py owns the knowledge base, not
  measurements (ADR-0110). Cites standard `stdlib-only`.
- **Real temp git repos in the fixture tests** over a fake git: a fake
  would re-implement `--author-date-order` and pathspec semantics, which
  are what is under test. A failing fake still covers the CLI-failure
  strings.

## ADRs

- [ADR-0109](../../adr/0109-an-observed-boundary-names-its-stage-and-writes-its-artifact.md)
  — an observed boundary names its stage and writes its artifact
  (provisional)
- [ADR-0110](../../adr/0110-decompose-signals-joins-the-root-only-importers.md)
  — decompose_signals joins the root-only importers of cli.py,
  knowledge_plane.py and protocol.py (provisional)
