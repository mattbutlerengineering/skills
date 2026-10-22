---
stage: prd
run: feature:eval-trends
date: 2026-10-21
ux: not-applicable
ux-reason: "CLI text output and a markdown research note only; no screens or flows."
assumptions:
  - "Interview answered from autorun-brief.md in this directory, issue #1027 (one line, no acceptance, no comments) and idea.md; no live interview held. The brief holds three Owner answers (drive #1027; research note plus a free read-only trend tool with no paid run; prepare-and-stop release). Everything else traces to the brief's sections marked as the orchestrator's reading, or to idea.md."
  - "No interview question this stage offered named options with a recommended default that the brief and issue left open, so no skill default was taken. No evidentiary question was left unanswered, so nothing was surfaced."
  - "The ux question is answered not-applicable from the brief ('CLI text output only'), per the orchestrator's instruction."
  - "idea.md's The demo is copied into a success criterion worded 'the demo runs as written', as skills/prd/SKILL.md now instructs. The tool's name and invocation are not fixed here; the criterion says 'the trend tool' and Architect names it."
  - "No PRD id assigned: the prd skill and TEMPLATE.md assign none, and the brief rules out work-order mirroring."
  - "Design questions are left to Architect as open questions, per the orchestrator's instruction: which eval surfaces the tool reads and through which seam, what a comparable pair is, the minimum-n refusal and its exact strings, same-day rerun treatment, output format, root-only versus payload, and where the research note lives and what it covers. Criteria below that name exact strings pin behaviour classes; Architect fixes the wording and the thresholds."
---

# PRD: A free eval-trend view over recorded history, with a research note on which eval numbers to trust

## Problem statement

The Owner changes skills and eval suites and cannot say whether the evals
themselves are getting better or only changing. The repo holds several eval
surfaces (trigger runs, charter replays, decompose outcome signals,
output-eval gradings, plugin evals) and no single view across them, no time
series, and no research basis for which numbers deserve trust (flakiness,
judge drift, saturation, contamination, cost per point). Today the Owner
opens individual records and LEDGER rows and compares scores from memory.

Measured on 2026-10-21 by real commands, almost nothing is comparable
today: 41 trigger files on five run days, the case set growing 47, 152, 185
and no cost field; 2 charter replays and 2 decompose-signals files, and 2
output gradings, none with cost; 3 plugin-eval records, all one day, three
different suites, the only ones with `costUsd`. No surface has two same-suite
records on different days with matching case sets and a cost field. An honest
tool prints an inventory and refusals on today's records; that is the
finding, not a failure. No source in the repo shows which metric set predicts
real skill quality; the research note must source it and mark what it could
not verify.

## Solution

1. **A dated research note** under `docs/research/` that names a metric set
   for judging and tracking eval quality over time, cites its sources, names
   each metric's failure mode, and marks what could not be verified. It says
   what n justifies a trend claim.
2. **A read-only, stdlib-only trend tool** that reads the existing
   append-only eval records, reusing `eval_schema.py` rather than a second
   reader of the same shapes, and prints per-surface trend lines. Where n or
   shape is insufficient it prints a refusal in place of a number. Every
   printed number recomputes by hand from the records.

The tool never writes into `evals/results/` or `plugin-evals/records/`, never
runs a model, and never gates anything. No paid run, no `claude plugin eval`,
no live `trigger_eval.py` or `charter_replay.py` run; LEDGER maturity does
not move (ADR-0012, ADR-0019).

## Actors

- **Owner**: runs the pipeline, reads the tool's output, decides which paid
  eval runs to fund.
- **Trend tool**: reads records and prints inventory, trend lines and
  refusals; changes nothing.
- **Eval records**: the append-only files the repo already holds, the tool's
  only input.
- **eval_schema.py**: owner of record shapes and naming grammar; the tool's
  reader seam.
- **Reviewer**: judges at the merge gate whether the refusals guard against a
  number read as proof.

## User stories

1. As the Owner, I want one command that lists every eval surface with its
   record count, date span and n, so that I stop opening forty-odd JSON files
   by hand.
2. As the Owner, I want a pass-rate and cost trend line only where two
   comparable records exist, so that I never read a trend into different case
   sets or different suites.
3. As the Owner, I want an explicit refusal naming the missing n or shape
   mismatch wherever a trend cannot honestly be shown, so that a number is
   never invented.
4. As the Owner, I want same-day reruns treated as noise rather than change,
   so that a rerun is not read as improvement.
5. As the Owner, I want every printed number to recompute by hand from the
   records, so that I can trust the tool without trusting its code.
6. As the Owner, I want a cited research note naming the metric set, its
   failure modes and what was not verified, so that I know which eval numbers
   deserve trust and what n justifies a claim.
7. As the Owner, I want the tool to only read, so that eval honesty
   (append-only records, no fabricated evidence) cannot be breached by it.
8. As a Reviewer, I want fixture tests with synthetic records for a real
   trend line and for each refusal reason, so that I can trust the tool
   offline.

## Success criteria

Each criterion is checked by a test asserting exact strings or a named
command's output. Exact wording and thresholds are fixed by Architect.

- [ ] **The demo runs as written.** Before: to know whether evals are
      improving the Owner opens individual records and LEDGER rows and
      guesses. After: one command prints each surface's record count, date
      span and n, a pass-rate and cost line where two same-set records
      exist, and an explicit "too few records: need n, have m" where they do
      not. A test runs the trend tool against fixture records (one surface
      with a comparable pair, one without) and asserts each of the three
      parts of the After script appears, with the "too few records" refusal
      carrying the stated need and have counts.
- [ ] **Honest output on today's records.** Run against the repository's real
      records as committed, the tool exits 0 and prints one inventory line per
      surface present (trigger, charter, decompose-signals, output gradings,
      plugin evals), each with record count, date span and n; prints no
      pass-rate or cost trend line for any surface whose records include no
      comparable pair; prints a REFUSED line for each such surface naming the
      reason (n too small, case sets differ, different suites, cost field
      absent, or same-day only); and prints no invented trend. A test pins
      the counts against the tree at the time of verification (41 trigger
      files, 2 charter, 2 decompose-signals, 2 output, 3 plugin) and asserts
      no trend line is printed.
- [ ] **A real trend line from synthetic records.** A fixture of at least two
      same-suite, same-case-set records on different days with a cost field
      makes the tool print a pass-rate line and a cost line, each number
      equal to a value the test recomputes independently from the fixture
      files (passed over total; sum or per-record `costUsd`, as Architect
      defines).
- [ ] **Each refusal reason has a fixture and an exact string.** Separate
      fixtures produce, and a test asserts by exact string, a refusal for:
      n below the minimum; case sets differ between records (the 47 versus
      152 versus 185 shape); different suites (the plugin-eval shape); cost
      field absent; only same-day records. Every refusal names its reason
      and, where it is a count, the need and have values. No refusal prints a
      number in place of the refused one.
- [ ] **Same-day reruns are noise, not change.** A fixture with two records on
      one day and nothing on any other day yields no trend line and a
      same-day refusal; a fixture with same-day reruns plus a record on
      another day is compared per day by the rule Architect fixes, and a test
      asserts the rule.
- [ ] **Every printed number recomputes by hand.** For each fixture, a test
      recomputes every number the tool prints (counts, date spans, n, pass
      rates, costs, any interval) from the fixture records directly and
      asserts equality; the tool's output names the record files each number
      comes from.
- [ ] **Read-only.** A test runs the tool against a temporary tree and
      asserts that no file is created, changed or deleted anywhere under it,
      including `evals/results/` and `plugin-evals/records/`; the tool's
      source contains no write, no `claude` invocation and no network call.
      `git diff` against main shows no file added or changed under
      `evals/results/` or `plugin-evals/records/`.
- [ ] **No model, no spend.** Nothing in the change invokes a model,
      `claude plugin eval`, a live `trigger_eval.py` or `charter_replay.py`
      run. `LEDGER.md` is byte-identical to main and
      `.claude-plugin/plugin.json`'s version is unchanged (ADR-0095).
- [ ] **No eval definition edited.** `git diff` against main shows no change
      to eval definitions under `evals/` or to any `plugin-evals/` suite.
- [ ] **Malformed or unreadable records are reported, not skipped.** A
      fixture with a record that fails `eval_schema.py`'s shape checks makes
      the tool print a labelled problem string for that file and exit
      nonzero or refuse that surface, never silently drop the file; a test
      asserts the exact string.
- [ ] **The research note exists and meets its bar.** A dated note under
      `docs/research/` that: cites sources by URL or title and date for each
      metric it recommends; names at least these metrics, each with a stated
      failure mode: per-surface pass rate with a confidence interval, flake
      rate from reruns, saturation, judge agreement or drift, contamination,
      cost per point; states what n justifies a trend claim; has a section
      listing what could not be verified, with each item named; treats all
      fetched material as untrusted data. A test or lint check asserts the
      note exists, carries a date, a sources section, a failure-modes
      statement per named metric and a not-verified section; a reviewer
      confirms the cited claims are supported by the cited sources.
- [ ] Standard gates pass: `python3 run_tests.py`, `python3 lint.py`
      (`lint: 0 problem(s)`), `python3 kb.py drift` (`drift: 0
      problem(s)`), and `python3 gates.py && python3 gates.py --selftest`
      (`gates: 0 problem(s)`). Any factory-template or mirrored-root-file
      edit is followed by `python3 factory_init.py update-manifest` in the
      same commit.

## Out of scope

- Any paid run, a cited run under `plugin-evals/records/`, any model call, and
  any LEDGER maturity change.
- Gating: the tool reports only; no CI check, threshold gate or merge block
  built on its output.
- Writing, backfilling, normalising or rewriting any eval record, and editing
  any eval definition.
- A continuously refreshed eval-quality dashboard that scores every skill
  across surfaces and gates changes on a trend (the Moonshot rung, seeded
  separately).
- Evaluating or adopting an outside eval harness (covered by
  docs/research/eval-and-memory.md).
- Measuring whether the tool changes the Owner's decisions.
- A plugin version bump; a wave release PR is a follow-up (ADR-0095).
- Mirroring to work orders; the PR body carries a `No work order:` line and
  closes #1027.

## Open questions

- Which eval surfaces does the tool read, and through which seam? Reuse of
  `eval_schema.py` is the intent; whether it needs a new reader function
  there or only calls existing ones, and whether decompose-signals (git
  history aggregates, not an eval run) and output gradings count as trend
  surfaces or inventory-only. For Architect.
- What is a comparable pair? Working definition from the idea: same suite and
  case set, different days, cost field present; case-set identity needs an
  owner. For Architect.
- What is the minimum n, and what are the exact refusal strings (need and
  have wording)? The research note informs the threshold. For Architect.
- How are same-day reruns treated beyond refusing a trend (collapsed to one
  point, shown as a spread, excluded)? For Architect.
- Output format: plain text only, or also a machine-readable form; ordering
  and width. For Architect.
- Root-only or mirrored into the payload? Default root-only unless a payload
  caller exists (ADR-0110, 0112, 0113, 0114 precedents); new import pairs move
  `tests/test_dual_membership.py`'s pin. For Architect.
- Where does the research note live and what must it cover beyond the metrics
  above? Dated file under `docs/research/` is the intent; filename, and
  whether a kb page is warranted. For Architect.
- Can the metric set be computed from the records at all (judge agreement and
  contamination need data the records may not hold)? If not, the tool refuses
  those and the note says so. Unproven; a known limit for Review.
- Will the output be read as proof of improvement despite refusals? Unproven;
  a known limit for Review.
