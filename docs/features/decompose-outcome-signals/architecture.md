---
stage: architect
run: feature:decompose-outcome-signals
date: 2026-10-18
ux: skipped — CLI measurement tool with text output only; no screens or flows.
assumptions:
  - "No live interview: every PRD open question was settled from autorun-brief.md, idea.md, prd.md, the code and a throwaway prototype run against this clone's refs (scratchpad only, nothing committed), taking the recommended default each time. Nothing here is expensive to reverse before the first record lands. Both ADRs are provisional."
  - "Recommended default taken (ref set): the tool reads every ref the clone holds except refs/stash, and it is not configurable. The output names each namespace read with its count, plus a digest of the ref tips. A stash commit snapshots uncommitted work, so it could pass for an inferred boundary. A --refs option has no caller (YAGNI). Measured 2026-10-18: 1086 refs besides refs/stash, 488 of them under refs/remotes/pr."
  - "Recommended default taken (subject-match strictness, ADR-0109): a boundary is observed when the subject reads `docs(<any scope>): <stage>` with the stage as a whole word, and the commit changes that stage's artifact in this run's directory. The scope is not compared with the slug, and the em dash is not required. There is no third label. Measured: slug-equal plus em dash finds observed decompose boundaries for 2 runs. The path-anchored rule finds 4, adding software-factory (scope `factory`) and the-reviewer-token-runs-agent-code (scope `reviewer-token`)."
  - "Recommended default taken (work-item key): a work item's key is its row's leading label (a WO token, or a short label like A1 or I2 at the start of the bold span), else the bold text, else the row text up to the first ` — `. A split or merge is detected only by citation: a row outside its `blocked by:` clause names the work items it became, or the ones it absorbed. first-live-dispatch's superseded row is the measured case. Duplicate keys in one version make that run's re-plan signal unmeasurable. Amended 2026-10-18: this default first made identity key-first, and claimed that title-match renames handled codex-style-standards-enforcement's renumbering. They did not (breakdown.md Notes, S13), because keys 0051 to 0058 sit in both versions under different titles. Identity is now Owner decision 6 (title first, key fallback; autorun-brief.md), taken live, so it is not an assumption. The defaults below fill in its details."
  - "Recommended default taken (title matching, under Owner decision 6): only a title that is non-empty and appears once in its version can be matched. Two rows with the same normalized title in one version are ambiguous, so neither is matched by title, and both fall back to the key. Pairing them in row order was rejected as a guess. Measured 2026-10-18: no breakdown version at any run's D or I repeats a title, so today this rule never applies."
  - "Recommended default taken (what `renamed` counts): a pair matched by title whose keys differ. A pair matched by key fallback whose titles differ is the same item retitled. It counts as kept, and in no field, which is what the shipped rule already does for a key match. No RunRecord field is added."
  - "Recommended default taken (citations once keys can be reused): a token in an I-version row names an I-version item first. A dropped key that some I-version item still uses is not citable, so it can never count toward a split or a merge. Under key-first a dropped key was absent from I by definition, so this case could not arise before. Reading the token as the dropped item would count a renumbered dependency as a split."
  - "Recommended default taken (duplicate keys): `duplicate work-item key <key> at <sha7>` stays unmeasurable and is checked before matching. Keys are still the fallback identity and the citation targets, and decision 6 does not touch this rule. Measured 2026-10-18: no run is unmeasurable for this reason today. All 6 unmeasurable re-plan runs give the already-checks reason."
  - "No ADR for the identity rule. It fails the hard-to-reverse leg: no record has been committed (S13 is open), and the rule lives in one function behind a pinned test. ADR-0109's decision covers boundaries, not identity, and ADR-0110's covers imports, so neither one is amended. ADR-0109's statement that the work-item keys at the first tick equal those at the implement commit is about keys, and it still holds."
  - "Recommended default taken (inferred design gaps): when a run has no observed decompose boundary, the design-gap signal is read from the `## Design gaps found` section that Decompose's TEMPLATE.md requires, in the breakdown version at the decompose boundary. A section whose first word is `none` gives 0. Any other content gives 1 route. A missing section makes the signal unmeasurable. The alternative was a later commit touching architecture.md, and the prototype found 6 such commits inside an inferred window. By subject, every one was a batch landing, a closure or a feature commit, not a route back to Architect."
  - "Recommended default taken (what a finding is): a heading of level 2 to 4, outside fences, whose text (emphasis stripped) starts with a severity word (critical, major, minor, low, medium, high) or an ordinal label (F1, Finding 1, 1.). A finding names a work item when its block holds one of the current breakdown's item keys as a whole token. The prototype found 184 findings in 34 review.md files, 32 of them naming an item: design evidence only, not the baseline."
  - "Recommended default taken (review-traced labelling): review-traced reads the committed review.md and breakdown.md and no boundary, so every measured run is observed for it. Its inferred population always prints as 0 run(s), so the line keeps the same shape as the other two signals."
  - "Recommended default taken (record location): `evals/results/decompose-signals-<date>[-N].json`, written by `--record` through eval_schema.write_snapshot as a third snapshot kind. eval_schema already owns that append-only naming grammar, and charter replays set the precedent for factory evidence that is never LEDGER evidence. A new directory would need a second owner of the -N grammar."
  - "Codebase default taken (unmeasurable is per signal): a run can be unmeasurable on re-plan and still measured on review-traced. Each per-run line gives the reason for each unmeasurable signal, and that signal's aggregate leaves the run out (the fail-closed roll-up: unknown never counts as zero)."
  - "Amended 2026-10-18. This assumption first kept Owner decision 3 as written (the inferred implement boundary is the first commit that ticks a row) and said the two implement windows agree, because the work-item keys at the first tick equalled those at the implement commit on 3 runs. Review falsified that on this run's own row: inferred at the first tick it read `re-plan 0 of 13`, and observed at the implement commit `re-plan 2 of 13 … ; design gaps 1 observed`. Keys agreeing at the first tick never showed the windows agree. The inferred implement boundary is now Owner decision 7 (the commit that checks the last row; autorun-brief.md), taken live, so it is not an assumption. ADR-0111 records it and supersedes that part of ADR-0109. The defaults below fill in its details."
  - "Recommended default taken (what the last tick is, under Owner decision 7): the earliest commit after D, in walk order, whose breakdown version has at least one row and checks every row. Measured 2026-10-18 on the 4 runs with an observed implement boundary: in all 4, the observed implement commit is exactly this commit. The alternative, the commit after which every row stays checked, was rejected. Across every ref, later waves add unchecked rows on 6 runs (fail-closed-roll-up goes from 7 of 7 to 7 of 12), so on 5 inferred runs it would move I onto a later wave."
  - "Recommended default taken (a breakdown never fully checked): no implement boundary, reason `no implement boundary: no later commit checks every row`, which replaces `… checks a row`. The fail-closed reading, since the protocol counts Implement done only when every checkbox is checked. The alternative, the latest commit that checks a row, guesses an end for an Implement that has not finished. Measured: 1 run (faster-sdlc, 9 of 11 checked) becomes unmeasurable. It would read `re-plan 0 of 11` under the latest tick."
  - "Recommended default taken (rows unchecked or added later): they do not move I. The boundary is the first time every row is checked, as the observed boundary is the earliest implement commit after D. A version with no rows is never fully checked."
  - "Recommended default taken (records): the rule sentence (`RULE`) gains the inferred rule, so a record shows which rule it was taken under. The first record stays unedited, and Implement takes a second dated record under the new rule (Owner decision 7). eval_schema names it `decompose-signals-<date>[-N].json`, which on 2026-10-18 is `-2`."
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
    `breakdown.md`. Inferred I (Owner decision 7, ADR-0111): the
    earliest commit after D whose version has at least one row and every
    row done (`knowledge_plane.breakdown_rows`, field `done`). That is the
    first time Implement was complete, so it marks the end of Implement,
    as the observed I does. Rows that are later unchecked, or added
    unchecked later, do not move it. A run whose breakdown is never fully
    checked on the refs read has no I.
  - Amended 2026-10-18, on a major that Review routed to the Owner. The
    shipped inferred I was the first commit after D with any done row,
    the start of Implement, and its window ended almost at once.
  - The artifact for each stage comes from `protocol.STAGE_ARTIFACTS`.
- Collaborators: the history adapter, for the versions it must inspect.
  It is pure over (commits, version reader).

### Work-item diff (`item_keys`, `replan`)

- Responsibility: the key and normalized title of each work item in one
  breakdown version, and the D→I diff as added, dropped, split, merged
  and renamed counts.
  - Key: see the work-item key assumption. If a key repeats within a
    version, that run's re-plan signal is unmeasurable
    (`duplicate work-item key <key> at <sha7>`). This is checked first,
    before any matching.
  - Title: `knowledge_plane.row_title` for WO rows (else the text after
    the token up to the first ` — `), the text after the label for label
    rows (`**` removed, cut at the first ` — `, and leading or trailing
    ` —-:` stripped), and otherwise the key itself.
  - Normalized title: the title with backticks removed, lowercased,
    whitespace runs collapsed to one space, ends trimmed, and any
    trailing `.` and `:` characters stripped (the shipped `_normal`). Case, code marks, spacing and a closing
    stop are not part of identity.
  - Identity, Owner decision 6 (title first, key fallback), in two
    passes, each one-to-one:
    1. Title pass. A D item and an I item are the same item when their
       normalized titles are equal, non-empty, and each appears only
       once in its version. A repeated title matches nothing in this
       pass.
    2. Key pass. A D item and an I item still unmatched that share a
       key are the same item, retitled.
    Every D item still unmatched is dropped, and every I item still
    unmatched is added. After the key pass no key is both added and
    dropped, so the two sets are disjoint.
  - Rename: a title-pass pair whose keys differ. `renamed` counts these
    pairs. A key-pass pair is kept and counted nowhere.
  - Split: a matched item whose I-version row cites at least 2 added
    keys, or a dropped item cited by at least 2 added rows.
  - Merge: one added row that cites at least 2 dropped items.
  - Citations are read from the row line with its `blocked by:` clause
    removed (`knowledge_plane.BLOCKED_BY`), so a dependency is never read
    as a split. The citable keys are the added keys, plus the dropped
    keys that no I-version item uses. A token in an I-version row names
    the I-version item first.
  - Re-plan count = added + dropped + splits + merges. Renames count 0.
    The rate's denominator is the number of work items at D.
  - Pinned case: a renumbering that keeps every title gives
    `re-plan 0 of <n> (added 0, dropped 0, split 0, merged 0; renamed <r>)`,
    where `<r>` is the number of items whose key changed. On
    codex-style-standards-enforcement (ebe8b2a → 5f30760, WO-0045..0058
    renumbered to WO-0051..0064) that is `re-plan 0 of 14 (…; renamed 14)`.
  - Amended 2026-10-18, on a design gap that Implement routed back at
    S13. The shipped rule was key first, with a title match only between
    leftover dropped and added items.
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
  - `decompose-signals: boundary rule — <ADR-0109 rule, one sentence>`.
    After ADR-0111 the sentence reads: `a boundary is observed when its
    commit subject reads docs(<any scope>): <stage>, the stage a whole
    word, and the commit changes that stage's artifact in the run's own
    directory; any other boundary is inferred: decompose at the commit
    that first adds breakdown.md, implement at the first later commit that
    checks every row (ADR-0109, ADR-0111)`
  - one line per run, for example
    `decompose-signals: feature:<slug> — decompose observed <sha7>, implement inferred <sha7>; re-plan 1 of 9 (added 1, dropped 0, split 0, merged 0; renamed 0) inferred; design gaps 0 inferred; review-traced 3 of 12 findings name an item`
  - an unmeasurable signal prints `<signal> unmeasurable — <reason>`.
    The reasons are fixed strings:
    - `no commit on the refs read changes <path>`
    - `the first version (<sha7>) already checks <n> of <m> rows`
    - `no implement boundary: no later commit checks every row`
      (ADR-0111; it replaces `no implement boundary: no later commit
      checks a row`)
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
  splits. Title-first identity, the next decision, handles that case.
- **Title first, key fallback** for work-item identity (Owner decision 6,
  taken live) over key first. Key first matched codex-style-standards-
  enforcement's reused keys WO-0051 to WO-0058 to different items, so a
  renumbering with every title kept read as `added 6, dropped 6`. Title
  first loses only when one row takes another row's old title, which no
  measured run does. Accepted behaviour changes, from running both rules
  over all 36 runs in this clone on 2026-10-18: one run differs.
  codex-style-standards-enforcement goes from `re-plan 12 of 14 (added 6,
  dropped 6, …; renamed 0)` to `re-plan 0 of 14 (added 0, dropped 0, …;
  renamed 14)`, and the inferred re-plan aggregate goes from 19/232 to
  7/232 over 27 runs. Every other run's re-plan record is identical, and
  all 63 existing tests pass under the new rule.
- **The last tick for the inferred implement boundary** (Owner decision
  7, taken live, ADR-0111) over the first tick. The first tick marks the
  start of Implement, so its window missed this run's own re-plans and
  route back to Architect. Accepted behaviour changes, from running both
  rules over all 36 runs in this clone on 2026-10-18: 24 runs move their
  inferred I. 22 of them keep the same figures. first-live-dispatch goes
  from `re-plan 1 of 8 (added 1, …)` to `re-plan 4 of 8 (added 3,
  dropped 0, split 1, merged 0; renamed 0)`, and faster-sdlc becomes
  re-plan unmeasurable. On today's refs the inferred re-plan aggregate
  goes from 7/219 over 26 runs to 10/208 over 25 (the first record, on
  earlier refs, reads 7/232 over 27). Design gaps, review-traced and every
  observed figure are unchanged.
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
  (provisional; superseded in part by ADR-0111)
- [ADR-0111](../../adr/0111-the-inferred-implement-boundary-is-the-commit-that-checks-the-last-row.md)
  — the inferred implement boundary is the commit that checks the last
  row; supersedes ADR-0109 in part (provisional, on Owner decision 7)
- [ADR-0110](../../adr/0110-decompose-signals-joins-the-root-only-importers.md)
  — decompose_signals joins the root-only importers of cli.py,
  knowledge_plane.py and protocol.py (provisional)
