---
stage: decompose
run: feature:docs-audit
date: 2026-10-10
assumptions:
  - "The cut was not reviewed live (skill step 5): the autorun brief names no work items, so the milestone boundaries and sizes are this stage's reading of architecture.md — three milestones (the record exists, every doc audited and corrected, the set organized and closed out), one row per doc or doc group in PRD-0010's order, and S/M/L by how many lines and pinned surfaces a row must get right: the protocol, the CLAUDE.md/AGENTS.md pair and the four routine playbooks L, the other per-doc rows M except LEDGER.md S, the scaffold and the close-out S."
  - "Work-order ids start at number 0114. The highest work-order number in any docs/**/breakdown.md on main, feat/grok-harness and this branch is 0096, but the unmerged local branch feat/launch-demo (and its worktree) already declares numbers 0097 through 0113, and detector C cross-checks ids repo-wide once branches merge — the same rule PRD-0010's own id assignment followed. No tracker mirror (the brief rules out any tracker interaction beyond #616; ADR-0026's opt-in export is off)."
  - "Implement's check-offs follow this repo's owner-session ledger policy (docs/features/process-dashboard/breakdown.md, 2026-08-13 note; docs/features/pocock-1-3-takeaways/breakdown.md and docs/features/readme-skill-map/breakdown.md Notes): detector G reads a checked row as a merged work order owed a docs/factory/costs.jsonl line, so each check-off appends one honest zero-cost row via budget_guard record. PRD-0010's 'In place, in scope' criterion lists the files the diff may touch and does not name docs/factory/costs.jsonl, while its 'Battery' criterion needs gates.py green, which a checked row with no ledger line breaks; the two cannot both hold literally. This breakdown reads 'In place, in scope' by intent — it guards the docs' scope, and the ledger is gate bookkeeping — and admits docs/factory/costs.jsonl as one extra M line carrying only appended owner-session rows, one per checked row. Verify applies the same reading; PRD-0010 is not rewritten. Taken without user input; the owner can reverse it at merge by asking for the ledger rows to be dropped and the rows left unchecked."
  - "The claims.md row-id prefixes the architecture leaves open (it gives README-7, PROTO-31, ROUT-GARD-4 as examples) are fixed here: README, CONTEXT, LEDGER, CLAUDE, AGENTS, SETUP, PROTO, OEVAL (docs/output-evals.md), ROUT-GARD, ROUT-IMPR, ROUT-GROOM, ROUT-RETRO (the four routine playbooks), EVALS (evals/README.md); follow-ups are F-1, F-2, and so on. Taken without user input."
  - "The Jobs table is drafted whole in the scaffold row (row 0114) so the thirteen lines are written side by side and can be kept pairwise distinct; each per-doc row may revise its own doc's line after reading the doc in full (architecture per-doc pass, step 1), and row 0123 settles the final thirteen. Taken without user input."
  - "A LEDGER.md maturity cell found false is reported as a follow-up, never corrected in this run: maturity graduates or changes only through a real run (CLAUDE.md Eval honesty; ADR-0012, ADR-0019), and this run produces no eval evidence. Taken without user input, from the repo's non-negotiable eval-honesty rule."
---

# Breakdown: documentation audit

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met. Rows follow the house grammar: a
repo-global work-order id (continuing from 0113, the highest declared
on any local branch), size class, blocking edges, and the PRD citation.
No tracker mirror for this run (ADR-0026; the brief allows no tracker
interaction beyond #616). Reconciled against `architecture.md` on
2026-10-10: every component it names lands in a row below, and every
PRD-0010 success criterion is covered by at least one Accept paragraph;
the Coverage section at the end says which.

## Shared terms the rows use

Defined once here so every row can be checked the same way; each row
still states its own doc-specific criteria in full.

- **The base** — `feat/grok-harness` (at `a0f7553` when this breakdown
  was written), or `main` once #618 has merged and the pull request is
  retargeted. Every `git diff` below is taken as `git diff
  feat/grok-harness...HEAD` (substitute `main` after a retarget).
- **The record** — `docs/features/docs-audit/claims.md`, laid out exactly
  as `architecture.md` § Data model fixes: Preamble, Jobs, one section
  per doc in PRD-0010's order, Duplicates, Follow-ups, Link scan, and
  (Verify's) Verify re-run.
- **A complete doc section** — the doc's section in the record has one
  row per checkable claim, each row carrying all eight columns (Id,
  Line, Claim, Kind, Check, Result, Verdict, Disposition); every Check is
  a single backticked command obeying the architecture's Check contract
  (runnable from the repo root in zsh, stdlib and repo only, read-only,
  exits 0 iff the claim as written holds; no `gh`, no network, no
  `trigger_eval.py` or `charter_replay.py` run — their flags are checked
  by grepping their argument parsers); every Result names an exit code
  and one decisive output line; every Verdict is `true`, `false` or
  `stale`; every `true` row's Check exits 0 when re-run; every `false` or
  `stale` row carries exactly one disposition — `corrected` (with the new
  text and the new Check, which exits 0 on the edited tree), `removed`,
  or `follow-up F-n` (with a register row); and no Result or evidence
  cell says "from memory" or is blank.
- **The battery** — `python3 -m unittest discover tests` prints `OK`,
  `python3 lint.py` prints `lint: 0 problem(s)`, and `python3 gates.py &&
  python3 gates.py --selftest` prints `gates: 0 problem(s)` and
  `selftest: ok`. Write each output to a file in the session scratchpad
  and grep it (zsh; never a variable named `status`). Run after every
  doc row, not once at the end.
- **In scope for the row** — `git diff --name-status feat/grok-harness...HEAD`
  after the row shows only `M` lines for the row's own doc(s) and the
  docs edited by earlier rows, files under `docs/features/docs-audit/`,
  and `docs/factory/costs.jsonl` (appended owner-session rows only, per
  the third assumption).

## Milestone 1: The record exists

- [x] **WO-0114** Create claims.md with its preamble, jobs, empty doc sections, follow-up seeds and the link-scan baseline — size:S, blocked by: — (PRD-0010 §Success criteria)
  - Accept: `docs/features/docs-audit/claims.md` exists with no stage frontmatter (a supporting file, like `autorun-brief.md`) and its seven sections in the architecture's order. The Preamble records the base commit audited (the output of `git rev-parse feat/grok-harness`), the verdict vocabulary with PRD-0010's operational definition of `stale`, the checkable-claim definition and its remote-state exclusion (cloud trigger ids, GitHub issue open/closed states and labels on GitHub are not inventoried), the Check contract, the rule that text between the `BEGIN BEADS` and `END BEADS` markers of `CLAUDE.md` and `AGENTS.md` is never edited (a false line there is a follow-up), and the row-id prefixes named in this breakdown's fourth assumption. The Jobs table has exactly thirteen rows, one per PRD-0010 in-scope file, each a one-line job, no two lines the same. Each of the thirteen docs has a section heading with an empty eight-column table (`grep -c` of the table header line prints `13`). The Follow-ups table holds F-1 (widen detector I's `_scannable_files` to reach `evals/`, evidence: `python3 -c "import gates, pathlib; print([p.name for p in gates._scannable_files(pathlib.Path('.').resolve()) if 'evals' in p.parts])"` prints `[]`) and F-2 (a parity check holding `AGENTS.md`'s non-Beads text to `CLAUDE.md`'s), each with reason "needs `lint.py`/`gates.py` and `tests/` edits, outside PRD-0010's permitted diff" and carrier "Operate seeds `docs/backlog.md`", per architecture decision (b). The Link scan section holds one `python3 -c` command that imports `gates` and applies `gates.MD_LINK` and `gates.URL_TARGET` (no link regex of its own: the command contains no `re.compile`) to exactly the thirteen files with detector I's skip and resolution rules (URLs and pure `#` anchors skipped, fragment stripped, targets resolved against the doc's directory or the root for a leading `/`), printing one line per missing target and exiting nonzero if any; its baseline run's output and exit code are recorded beside it (the architecture's survey found 59 relative links, 0 missing; the recorded numbers are what the command printed, not the survey's). No in-scope doc is edited in this row (`git diff --name-status feat/grok-harness...HEAD` lists only files under `docs/features/docs-audit/` and, once checked, `docs/factory/costs.jsonl`); the battery passes.

## Milestone 2: Every doc audited and corrected

Rows are listed in PRD-0010's order and Implement works them in that
order on one branch. Each is blocked only by the scaffold: the docs do not
depend on one another's corrections, and cross-doc overlap is settled in
Milestone 3, not here. A passage a row finds shared with another in-scope
doc is noted in the Duplicates table with no disposition yet.

- [x] **WO-0115** Audit and correct README.md — size:M, blocked by: WO-0114 (PRD-0010 §Success criteria)
  - Accept: the `README.md` section of the record is a complete doc section, covering paths, commands, install steps, the skill table and the figure embed; the Grok/harness wording added by #618 is inventoried for truth against the tree like any other claim (e.g. the `.claude-plugin` manifests it names exist) and is not reworded on ADR-0076's merits. Every `false`/`stale` row is resolved by a hunk in `git diff feat/grok-harness...HEAD -- README.md` touching that row's line, or by a follow-up row. The three README prose pins still hold: `python3 -c "import lint, pathlib; r = pathlib.Path('.'); print(lint.check_readme_skills(r) + lint.check_readme_no_orphans(r) + lint.check_readme_figure(r))"` prints `[]`. In scope for the row; the battery passes.
- [x] **WO-0116** Audit and correct CONTEXT.md — size:M, blocked by: WO-0114 (PRD-0010 §Success criteria)
  - Accept: the `CONTEXT.md` section of the record is a complete doc section in which every defined term that names a module, function, file or ADR has a row checking that it exists, and every ADR it presents as standing has an `adr-status` row whose Check reads that ADR's status from `docs/adr/README.md`'s index (a superseded ADR presented as standing is `stale`). Definitions are left as written unless a row falsifies them. Every `false`/`stale` row is resolved by a hunk in `git diff feat/grok-harness...HEAD -- CONTEXT.md` or a follow-up row. Because `orientation_pack.py` reads `CONTEXT.md` whole into every work order's orientation pack, the diff removes no term that a `grep -n` over `*.py` and `skills/**/SKILL.md` still uses (any removed term is listed in the row's Disposition with that grep's empty output). In scope for the row; the battery passes.
- [x] **WO-0117** Audit and correct LEDGER.md — size:S, blocked by: WO-0114 (PRD-0010 §Success criteria)
  - Accept: the `LEDGER.md` section of the record is a complete doc section covering its skill roster and every evidence link and dated-snapshot claim, each checked against `evals/results/` filenames only (no eval is run). No maturity cell changes in the diff (`git diff feat/grok-harness...HEAD -- LEDGER.md` touches no maturity value); a maturity claim the tree does not bear out is a follow-up row, per this breakdown's sixth assumption. `lint.check_ledger`, `lint.check_ledger_no_orphans` and `lint.check_ledger_links` all return `[]` (`python3 -c "import lint, pathlib; r = pathlib.Path('.'); print(lint.check_ledger(r) + lint.check_ledger_no_orphans(r) + lint.check_ledger_links(r))"` prints `[]`). No file under `evals/` other than `evals/README.md` is touched. In scope for the row; the battery passes.
- [x] **WO-0118** Audit and correct CLAUDE.md, then resync AGENTS.md to it — size:L, blocked by: WO-0114 (PRD-0010 §Success criteria)
  - Accept: the `CLAUDE.md` section of the record is a complete doc section over everything outside its Beads block — the Verify commands and their expected output lines, the on-demand tools and their flags (`--control` checked by grepping `charter_replay.py`'s parser, never by running it), every seam module and the ADR each is attributed to, the three skill kinds, the factory-template and manifest rule, and the "Where things are decided" paths. The `AGENTS.md` section is a complete doc section whose rows include one per divergence from `CLAUDE.md` outside the Beads blocks found at the base (at least the missing `--control` paragraph, the missing `one_owner.py` pass, and the missing `read_file` / `human_gates.py` / `plane_drift.py` seam text), each `stale` with disposition `corrected`. After the row, `diff <(awk '/BEGIN BEADS/{exit} {print}' CLAUDE.md) <(awk '/BEGIN BEADS/{exit} {print}' AGENTS.md)` prints nothing, or only lines recorded in the record's Duplicates table as a deliberate harness-specific difference with the reader it serves. Neither file's Beads block changes: `git diff feat/grok-harness...HEAD -- CLAUDE.md AGENTS.md` has no hunk between a `BEGIN BEADS` and an `END BEADS` marker (any false line found there is a follow-up row naming `bd setup` as its owner). In scope for the row; the battery passes.
- [x] **WO-0119** Audit and correct docs/setup.md — size:M, blocked by: WO-0114 (PRD-0010 §Success criteria)
  - Accept: the `docs/setup.md` section of the record is a complete doc section in which every command's subcommands and flags are checked against that tool's argument parser (a `--help` grep or a `grep -n` of the parser line) and every path the doc says the stamp installs is checked against `factory_init.py` (its `MIRRORS` tuple, its manifest-pinned payload or its curated stamped-file set) or the tree. Every `false`/`stale` row is resolved by a hunk in `git diff feat/grok-harness...HEAD -- docs/setup.md` or a follow-up row. In scope for the row; the battery passes.
- [x] **WO-0120** Audit and correct docs/pipeline-protocol.md as a contract — size:L, blocked by: WO-0114 (PRD-0010 §Success criteria)
  - Accept: the `docs/pipeline-protocol.md` section of the record is a complete doc section covering its artifact and stage tables, frontmatter keys, gating rules, skill names, ADR citations and paths. Every hunk in `git diff feat/grok-harness...HEAD -- docs/pipeline-protocol.md` touches the line of a `PROTO-n` row whose disposition is `corrected` or `removed` and whose evidence is a Check against `protocol.py`, another module, or a named `skills/**/SKILL.md` line showing the tree already behaves as the new text says. Every finding that would change what a skill must do is a `follow-up F-n` row with reason "protocol behaviour change" and has no hunk. The protocol's pins still hold: `python3 -c "import lint, pathlib; r = pathlib.Path('.'); print(lint.check_protocol(r) + lint.check_protocol_tables(r))"` prints `[]` and `python3 -m unittest tests.test_protocol_conformance` prints `OK`; the orientation tables move only where `protocol.py` already says the same. In scope for the row; the battery passes.
- [x] **WO-0121** Audit and correct docs/output-evals.md and evals/README.md — size:M, blocked by: WO-0114 (PRD-0010 §Success criteria)
  - Accept: the `docs/output-evals.md` section of the record is a complete doc section in which the output-eval record shape and results-naming grammar are checked against `eval_schema.py`, and the dated pilot-lesson passages are inventoried only for claims about the current tree (history stays as history). The `evals/README.md` section is a complete doc section in which every layout claim is checked against the `evals/` tree and every eval-honesty rule against `CLAUDE.md`'s Eval honesty section and the ADRs it cites. Every `false`/`stale` row is resolved by a hunk in `git diff feat/grok-harness...HEAD -- docs/output-evals.md evals/README.md` or a follow-up row. No eval definition and nothing under `evals/results/` changes: `git diff --stat feat/grok-harness...HEAD -- evals ':!evals/README.md'` prints nothing. Because detector I does not walk `evals/`, the record's link-scan command is re-run after this row and exits 0. In scope for the row; the battery passes.
- [x] **WO-0122** Audit and correct the four routine playbooks under docs/factory — size:L, blocked by: WO-0114 (PRD-0010 §Success criteria)
  - Accept: the record has a complete doc section for each of `docs/factory/doc-gardener-routine.md`, `docs/factory/improvement-routine.md`, `docs/factory/queue-groomer-routine.md` and `docs/factory/retro-reflect-routine.md` (prefixes ROUT-GARD, ROUT-IMPR, ROUT-GROOM, ROUT-RETRO), covering each playbook's preconditions, paths, commands, label names (checked against the label taxonomy file the repo ships) and in-repo issue-template or file references; trigger ids and the open/closed state of GitHub issues are not inventoried (remote state, the Preamble's exclusion). Every `false`/`stale` row is resolved by a hunk in `git diff feat/grok-harness...HEAD -- docs/factory/*-routine.md` or a follow-up row. The shared skeleton (preconditions, orient, pick one, non-negotiables, amending) is kept in each playbook — not collapsed — per architecture decision (f); a correction to one copy of a skeleton passage that is equally false in the other three is made in all four, and the four rows cite one another. In scope for the row; the battery passes.

## Milestone 3: The set is organized and the audit is closed out

- [ ] **WO-0123** Settle duplicates and the thirteen jobs — size:M, blocked by: WO-0115, WO-0116, WO-0117, WO-0118, WO-0119, WO-0120, WO-0121, WO-0122 (PRD-0010 §Success criteria)
  - Accept: the record's Jobs table has exactly thirteen rows, one per in-scope file, pairwise distinct (a `sort | uniq -d` over the job cells prints nothing), each reflecting the doc as it now reads. Every passage the per-doc rows noted as shared between two in-scope docs has a Duplicates row with exactly one disposition: `collapsed → owner X, link from Y` — the non-owner copy replaced by a relative Markdown link to the owner in `git diff feat/grok-harness...HEAD`, the link resolving — or `deliberate → reader`, naming the reader it serves. At minimum the table records `CLAUDE.md`/`AGENTS.md` as deliberate (reader: a non-Claude harness agent that auto-loads `AGENTS.md` and does not follow links; architecture decision (e)) and the four routine playbooks' shared skeleton as deliberate (reader: each cloud routine, which loads its own playbook alone; decision (f)). A collapse never moves, renames or deletes a file, never removes text a prose pin reads (`lint.py` stays at `lint: 0 problem(s)`), and never edits `docs/pipeline-protocol.md` except under a `PROTO-n` row per row 0120's rule. The link-scan command exits 0 after the last collapse. In scope for the row; the battery passes.
- [ ] **WO-0124** Close out: links, dispositions, protocol hunks, scope and the battery on the tip — size:S, blocked by: WO-0123 (PRD-0010 §Success criteria)
  - Accept: on the branch tip — (1) the record's link-scan command, re-run over exactly the thirteen files, prints no missing target and exits 0, and its output replaces the Link scan section's last run with the date; (2) a walk of every `false`/`stale` row finds one disposition each, every `corrected`/`removed` row matching a hunk in `git diff feat/grok-harness...HEAD` on that doc at that row's line, and every `follow-up F-n` matching a Follow-ups row with a reason and a suggested carrier; (3) every hunk in `git diff feat/grok-harness...HEAD -- docs/pipeline-protocol.md` maps to a `PROTO-n` row whose evidence shows the tree already behaves as the new text says; (4) `git diff --name-status feat/grok-harness...HEAD` lists only `M` lines for in-scope docs, `A`/`M` lines under `docs/features/docs-audit/` (this run's artifacts, `claims.md` among them), and the one `M` line for `docs/factory/costs.jsonl` (appended owner-session rows only: `git diff feat/grok-harness...HEAD -- docs/factory/costs.jsonl | grep '^[-+][^-+]' | grep -vc '^+{'` prints `0`); no `factory/manifest.json` change is needed because none of the thirteen is in `factory_init.MIRRORS` (`python3 -c "import factory_init; print([m[0] for m in factory_init.MIRRORS if m[0].endswith('.md')])"` prints `[]`); (5) `git diff --stat feat/grok-harness...HEAD -- docs/adr docs/fixes docs/backlog.md skills factory/templates evals ':!evals/README.md' docs/features ':!docs/features/docs-audit'` prints nothing; (6) the battery passes; (7) every row above is checked. The Verify re-run section of the record is left empty for Verify.

## Coverage

Architecture components to rows: the claim inventory (`claims.md`, its
Preamble, Jobs table, per-doc tables, Duplicates, Follow-ups and Link
scan sections) is created by row 0114 and filled by row 0115 through
row 0123; the per-doc pass is rows 0115 through 0122, one row per doc or
doc group in PRD-0010's order; the link scan is recorded with its
baseline in row 0114 and re-run in row 0121 (for `evals/README.md`, which
detector I misses), row 0123 and row 0124; the follow-up register is seeded
with the architecture's two proposed checks in row 0114 and grows in every
per-doc row; the Verify re-run section is Verify's and has no row. Every
prose pin under the architecture's Interfaces is held by the row that
edits its doc: the README pins by row 0115, the protocol pins and the
conformance test by row 0120, the LEDGER pins by row 0117, `CONTEXT.md`'s
orientation-pack reader by row 0116, and detectors C and I by the battery
in every row. Every path in the architecture's tree-claims block is read
or edited by a row: the thirteen docs (rows 0115 to 0122), `gates.py`
(row 0114's link scan), `lint.py` (row 0115, row 0117, row 0120),
`protocol.py` and `tests/test_protocol_conformance.py` (row 0120),
`orientation_pack.py` (row 0116), `tests/test_lint.py` (through the
battery), `docs/adr/README.md` (row 0116's ADR-status checks) and
`prd.md` (cited by every row).

PRD-0010 Success criteria to Accept paragraphs:

- Claim inventory covers the set — row 0114 (the record and its thirteen
  sections) and rows 0115 to 0122 (each a complete doc section, no
  "from memory" evidence).
- Every false or stale claim is resolved — each per-doc row's
  disposition clause; row 0124 (2) walks them all against the diff.
- The corrected docs pass their own checks — the "complete doc section"
  term requires every `true` and every `corrected` Check to exit 0 on the
  edited tree; the Verify re-run and its count are Verify's, recorded in
  the record's last section (follow-up rows that leave a false claim in
  place are excluded and listed, per the architecture's fourth
  assumption).
- One job per doc — row 0114 (the drafted Jobs table) and row 0123 (the
  settled table and every duplicate's disposition).
- Links resolve — row 0114 (the scan and its baseline), row 0121 (the
  `evals/README.md` gap), row 0123 and row 0124 (1).
- Protocol stays a contract — row 0120 and row 0124 (3).
- In place, in scope — the "in scope for the row" term on every row,
  row 0118's Beads-block rule, row 0121's eval-definition rule, and
  row 0124 (4) and (5), read by intent for `docs/factory/costs.jsonl` per
  the third assumption.
- Battery — every row, and row 0124 (6) on the tip.

## Design gaps found

None. The one inconsistency met in decomposition is between two PRD-0010
criteria — "In place, in scope" closes the diff's file list without
`docs/factory/costs.jsonl`, while "Battery" needs detector G green, which
the repo's owner-session ledger policy makes so only by appending to that
file. It is a check that cannot be run literally, not a missing contract;
it is read by intent in row 0124 (4) and logged under `assumptions:`, and
Verify applies the same reading.

## Notes

- 2026-10-10: the merge is gate 3 (ADR-0033). The pull request carries
  this run's `prd.md` and `architecture.md`, so ADR-0036 clause 3 makes
  it a human code-owner merge — the brief's plan: Ship opens the one pull
  request against `feat/grok-harness` and stops; the owner merges.
- 2026-10-10: owner-session ledger policy — each check-off appends one
  honest zero-cost row to `docs/factory/costs.jsonl` via `budget_guard
  record` (`run_id` of the form `session-YYYY-MM-DD-wo-NNNN`, the
  session's model, `tokens: 0`, `cost: 0.0`, `outcome:
  owner-session:unmetered`), as the last rows of that ledger do. The
  rows' Accept text assumes `gates: 0 problem(s)` after a check-off; the
  ledger row is what makes it so.
- 2026-10-10: if #618 changes before it merges, the base moves under
  this branch. Verify records the base commit it checked against; whether
  the audit re-runs on a moved base is the owner's call at merge
  (PRD-0010 open question 4).
