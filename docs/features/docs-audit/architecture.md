---
stage: architect
run: feature:docs-audit
date: 2026-10-10
ux: skipped — static documentation; no flows or screens
assumptions:
  - "The skill's trade-off read-out (step 6) was not held live; every decision that could have gone another way is recorded under Decisions & alternatives with the option that lost, per the autorun brief. PRD-0010's four open questions are answered there, lettered (a)-(d); the fourth (re-running on a moved base) stays the owner's, and this design only fixes what Verify records."
  - "A checkable claim is one the tree can falsify (a path, a command or flag, a module, function or checker name, a count, an ADR status, a skill roster). Claims about remote state — a cloud trigger id, a GitHub issue's open/closed state, a label on GitHub — are not tree claims and are not inventoried; claims.md names that exclusion once in its preamble. Taken without user input, from PRD-0010's own list of claim kinds."
  - "Text inside the generated Beads blocks of CLAUDE.md and AGENTS.md (between the BEGIN/END BEADS markers) is not edited: `bd setup` owns and regenerates it, so an edit there would be overwritten. A false claim found inside one is a follow-up, not a fix. Taken without user input."
  - "A false claim whose disposition is a follow-up and which therefore stays in the doc (the protocol behaviour-change case PRD-0010 sanctions in its 'Every false or stale claim is resolved' criterion) is excluded from the Verify re-run count and listed by row id in verification.md; otherwise that criterion and 'The corrected docs pass their own checks' could not both hold. Taken without user input."
  - "AGENTS.md is kept as a deliberate duplicate of CLAUDE.md's non-Beads content (its reader is a non-Claude harness agent that auto-loads AGENTS.md and does not follow a link), and is brought back into agreement with CLAUDE.md rather than collapsed to a pointer. Taken without user input; see decision (e)."
  - "No permanent lint or gate check is added in this run: every candidate needs an edit to lint.py or gates.py plus tests/, and PRD-0010's 'In place, in scope' criterion admits only the thirteen docs and this run directory. The two candidates the survey found are recorded as follow-ups for Operate to seed. Taken without user input, under PRD-0010's own rule that a check touching an out-of-scope path becomes a backlog seed."
---

# Architecture: documentation audit

## Approach

The audit is carried out by hand, doc by doc, and recorded in one
supporting file in the run directory, `claims.md`, which is the single
place every finding, its evidence and its disposition live. Each
checkable claim gets one row whose **Check** is a literal command, run
from the repo root, that exits 0 if and only if the claim as written is
true of the tree — so the evidence is reproducible by construction, and
Verify's re-run is mechanical: extract the commands, run them, count the
non-zero exits. Duplicates and follow-ups are tables in the same file, so
a reviewer reads one record, not three. Link integrity reuses the link
grammar detector I already owns (`gates.MD_LINK`, `gates.URL_TARGET`)
through a one-line stdlib scan over exactly the thirteen files, because
detector I's own walk covers twelve of them and misses `evals/README.md`.
No lint or gate checker is added: any would touch `lint.py` or
`gates.py` and `tests/`, outside the diff PRD-0010 permits, so the drift
classes worth pinning become follow-ups. The other shape considered — a
committed scratch script in the run directory that extracts and checks
claims automatically — loses because claim extraction is a reading job
(a sentence like "lint runs both on every push" has no token to grep),
a `.py` file in a run directory is a stranger the repo's tracked-Python
sweeps would start reading, and a script's output would still need a
human verdict per row; the per-row command gives the same
reproducibility without the extractor.

```tree-claims
# What this design reads or relies on, as it stands in this worktree on 2026-10-10.
exists: README.md
exists: CONTEXT.md
exists: LEDGER.md
exists: AGENTS.md
exists: CLAUDE.md
exists: docs/setup.md
exists: docs/pipeline-protocol.md
exists: docs/output-evals.md
exists: docs/factory/doc-gardener-routine.md
exists: docs/factory/improvement-routine.md
exists: docs/factory/queue-groomer-routine.md
exists: docs/factory/retro-reflect-routine.md
exists: evals/README.md
exists: gates.py
exists: lint.py
exists: protocol.py
exists: orientation_pack.py
exists: tests/test_lint.py
exists: tests/test_protocol_conformance.py
exists: docs/adr/README.md
exists: docs/features/docs-audit/prd.md
```

## Components

### The claim inventory (`docs/features/docs-audit/claims.md`)

- Responsibility: the one record of the audit — what each in-scope doc
  claims, how each claim was checked, what the check said, the verdict,
  and what was done about it. Every other artifact of this run
  (breakdown rows, verification.md, review.md) cites rows here by id
  instead of restating findings.
- Shape: a supporting file beside `autorun-brief.md`, not a protocol
  artifact — no stage owns it and the router never reads it, so it
  carries no stage frontmatter (as the brief does not). Implement creates
  it; Verify appends its re-run; nothing else writes it.
- Collaborators: the thirteen docs (read), the tree (checked against),
  `git diff <base>...HEAD` (dispositions point at hunks), Verify (re-runs
  the Check column).

### The per-doc pass (Implement's procedure, one doc at a time)

- Responsibility: turn one doc into its `claims.md` section and its
  hunks. In order: (1) state the doc's job in one line; (2) read the doc
  top to bottom and enter one row per checkable claim — a sentence
  carrying several claims gets several rows, a token repeated in the
  same claim gets one; (3) run each Check and record the exit code and
  the decisive output line; (4) give each row a verdict — `true`,
  `false` (the tree says otherwise), or `stale` (PRD-0010's operational
  definition: names something the tree no longer has or does); (5) for
  each false or stale row choose exactly one disposition and make the
  hunk; (6) note any passage the doc shares with another in-scope doc
  for the duplicates table. Checks are written from what the tree says,
  never from memory, and a claim that cannot be given a command is
  recorded with a file-read check (`grep -n` of the line that bears it
  out) rather than skipped.
- Collaborators: the claim inventory; the prose pins listed under
  Interfaces (they must still hold after each hunk).

### The link scan

- Responsibility: prove PRD-0010's "Links resolve" criterion over exactly
  the thirteen files, including `evals/README.md`, which detector I's
  `_scannable_files` walk does not reach (evals/ is not in it; verified
  2026-10-10 with a call to `gates._scannable_files`).
- Shape: one stdlib `python3 -c` command, recorded verbatim in
  `claims.md`, that imports `gates` and applies `MD_LINK` and
  `URL_TARGET` the way `check_staleness` does — same skip rules (URLs and
  pure `#` anchors), same resolution (relative to the doc's directory,
  or to the root for a leading `/`), fragment stripped. It prints one
  line per missing target and exits nonzero if any. Survey baseline:
  59 relative links across the thirteen files, 0 missing; the docs use
  neither reference-style link definitions nor HTML `href`/`src`, so
  `MD_LINK` is the whole link grammar these files need.
- Collaborators: `gates.MD_LINK`, `gates.URL_TARGET` (the link grammar's
  one owner — reused, not copied); Implement runs it after the last
  hunk, Verify re-runs it.

### The follow-up register (a section of `claims.md`)

- Responsibility: hold every finding this run must not fix — a stale
  claim in an ADR body or a run artifact, a protocol finding that would
  change what a skill must do, a false line inside a generated Beads
  block, and every proposed permanent check. Each row names the file,
  the finding, the evidence (a row id or a command), the reason it is
  not fixed here, and the suggested carrier. Operate's retro reads this
  register and turns the rows it judges worth it into `docs/backlog.md`
  seeds; this run's diff never touches the backlog and opens no issue.
- Seeded by the survey with two proposed checks (decision (b)).
- Collaborators: Operate (consumer); the PR body's merge-danger section
  (cites the register so the owner sees what was deliberately left).

## Data model

One Markdown file, `claims.md`, chosen from the reads the PRD requires:
Verify must re-run every check (so checks are cells, not prose), Review
must walk false/stale rows against the diff (so dispositions name a
hunk), and the "one job per doc" check must compare thirteen lines
pairwise (so jobs sit together). Sections, in order:

1. **Preamble** — base commit audited (`git rev-parse` of the base), the
   verdict vocabulary, the checkable-claim definition and its remote-state
   exclusion, and the Check contract (below).
2. **Jobs** — a thirteen-row table: doc, its one-line job. Pairwise
   distinct by construction; Review reads it once.
3. **One section per doc**, in the PRD's order, each a table:

   | Id | Line | Claim | Kind | Check | Result | Verdict | Disposition |
   |---|---|---|---|---|---|---|---|

   - **Id** — a doc prefix plus a number (`README-7`, `PROTO-31`,
     `ROUT-GARD-4`); stable once written, the key every other artifact
     cites.
   - **Line** — the line number in the doc as audited at the base.
   - **Claim** — the claim, quoted or tightly paraphrased.
   - **Kind** — one of `path`, `command`, `name`, `count`, `adr-status`,
     `roster`.
   - **Check** — a backticked command (contract below).
   - **Result** — exit code and the one decisive output line.
   - **Verdict** — `true`, `false` or `stale`.
   - **Disposition** — blank for `true`; for `false`/`stale` exactly one
     of `corrected → <new text>; check <command>`, `removed`, or
     `follow-up F-n`.
4. **Duplicates** — a table: passage (short label), the docs carrying it,
   disposition `collapsed → owner <doc>, link from <doc>` or `deliberate
   → <reader it serves>`.
5. **Follow-ups** — a table: `F-n`, file, finding, evidence, reason not
   fixed, suggested carrier.
6. **Link scan** — the command and its output, as Implement ran it.
7. **Verify re-run** — appended by Verify: the extraction and run
   commands, the count re-checked, the failures (target zero), and the
   follow-up rows excluded under this artifact's fourth assumption.

Invariants and their owners: a row's verdict is owned by its Check's
result (a `true` row whose Check exits nonzero is a defect in the row);
a `corrected` row's new Check is what Verify runs, the original Check
having proved the old text false; ids never renumber. Consistency is
must-hold-at-Verify: claims.md is written as Implement goes and is
reconciled once, against the final tree, at Verify.

## Interfaces & contracts

### The Check contract (a row's Check cell → Verify)

- Input: one backticked shell command, runnable from the repo root in
  zsh with only the repo and Python 3 standard library — `test -e`,
  `grep -q`, `git ls-files --error-unmatch`, `python3 -c` over
  `protocol` / `gates` / `lint` imports, a `--help` grep. One claim per
  command.
- Output: exit 0 if and only if the claim as written holds. The Result
  cell records the exit code and the decisive line.
- Failure modes: a command that costs money or touches the network is
  forbidden as a Check — `trigger_eval.py` and `charter_replay.py` are
  checked by reading their argument parser (`grep -n -- '--control'
  charter_replay.py`), never by running them; a `gh` call is never a
  Check (remote state is excluded). A command that cannot express the
  claim falls back to a `grep -n` of the bearing line, whose Result is
  read by the auditor and whose verdict says so. Every Check is
  read-only and idempotent, so Verify can re-run the whole column any
  number of times.

### The prose pins (in-scope text that code reads)

Implement must keep each of these passing after every hunk; moving or
rewording the pinned text is where a reorganization turns CI red.

- `README.md` — `lint.check_readme_skills`, `check_readme_no_orphans`
  (backticked slug-shaped tokens inside `## Stages` are read as skill
  claims), `check_readme_figure` (the figure embed line).
- `docs/pipeline-protocol.md` — `lint.check_protocol` and
  `check_protocol_tables`, and `tests/test_protocol_conformance.py`
  (the orientation tables are bound to `protocol.py`). Its tables move
  only if `protocol.py` already says the same.
- `LEDGER.md` — `lint.check_ledger`, `check_ledger_no_orphans`,
  `check_ledger_links`.
- `CONTEXT.md` — read whole by `orientation_pack.py` into every
  dispatched work order's orientation pack, so its content is agent
  context in stamped repos' flows; no structural pin.
- `CLAUDE.md`, `AGENTS.md` and every in-scope doc — gates.py detector C
  (every typed-id token resolves; a moved or retyped ADR or work-order
  token dangles) and detector I (links), both already in `make check`.
- Failure mode: any of these goes red in `python3 lint.py`,
  `python3 -m unittest discover tests` or `python3 gates.py` — Implement
  runs the battery after each doc, not once at the end.

### The disposition → diff link (claims.md → Review)

- Input: a `false`/`stale` row's disposition.
- Output: for `corrected`/`removed`, a hunk in `git diff <base>...HEAD`
  on that doc touching the row's line; for `follow-up F-n`, a register
  row with a reason.
- Failure modes: a row with no disposition, or one pointing at a hunk
  that does not exist, fails PRD-0010's "Every false or stale claim is
  resolved"; a hunk in `docs/pipeline-protocol.md` with no row fails
  "Protocol stays a contract".

## Survey and per-doc approach

Sized on 2026-10-10 against this worktree (base plus #618's Grok edits):
591 backticked spans across the thirteen files, 325 of them path-shaped,
59 relative links (0 missing), 81 distinct ADR references, 2,164 lines.
Backticked spans over-count claims (one claim often carries several), so
the inventory should land in the low hundreds of rows. The per-doc
approach, by the shape of each file:

| Doc | Lines | Approach |
|---|---|---|
| `README.md` | 125 | Paths, commands and install steps; Grok wording audited for truth, not re-litigated (ADR-0076). Three lint pins. |
| `CONTEXT.md` | 137 | Vocabulary: check each defined term's named module/ADR exists and its ADR still stands; definitions stay unless falsified. |
| `LEDGER.md` | 81 | Roster and evidence links, already lint-pinned; check maturity claims against `evals/results/` filenames only. |
| `CLAUDE.md` | 159 | Dense in module, seam and ADR claims; the owner of the agent-notes text. Beads block excluded. |
| `AGENTS.md` | 160 | Survey found it a drifted copy of CLAUDE.md (missing the `--control` paragraph, the `one_owner.py` pass, and the `read_file`/`human_gates`/`plane_drift` seam text). Diff against CLAUDE.md first; every divergence outside the Beads blocks is a row. |
| `docs/setup.md` | 156 | Commands and stamp steps; check each command's flags against its parser and each stamped path against `factory_init`. |
| `docs/pipeline-protocol.md` | 314 | Normative: every hunk needs a row showing code or a `SKILL.md` already behaves as the new text says; a behaviour change is a follow-up. Two lint pins and a conformance test. |
| `docs/output-evals.md` | 112 | Record shape against `eval_schema.py`; the 2026-07-01 pilot lessons are history, audited only for claims about the current tree. |
| `docs/factory/*-routine.md` (4) | 874 | Shared skeleton (preconditions, orient, pick one, non-negotiables, amending); paths, commands, labels and issue numbers per routine. Trigger ids and issue states are remote and excluded. |
| `evals/README.md` | 46 | Layout and honesty policy against `evals/`; outside detector I, so the link scan is its only link check. |

## Stack & dependencies

- Python 3 standard library and POSIX shell only, for every Check and
  the link scan (`stdlib-only`); nothing is installed.
- `gates.MD_LINK` / `gates.URL_TARGET` — imported, not copied, so the
  scan and detector I can never disagree about what a link is.
- No new module, script or committed tool.

## Decisions & alternatives

- **(a) Inventory by hand into `claims.md`, one row per claim, each
  Check a command with an exit-code contract** over a committed
  extraction script in the run directory — extraction is reading, the
  script would still need a human verdict per row, and a tracked `.py`
  in a run directory invites the repo's tracked-Python sweeps
  (`one_owner.py`, the class-fix AST sweeps) to read it; and over prose
  evidence ("checked, fine") — not re-runnable, so Verify could not meet
  its own criterion. Over three files (inventory, duplicates,
  follow-ups) — one file is one read for the owner (user story 2).
- **(b) No permanent lint or gate check in this run** over adding one —
  both candidates need `lint.py`/`gates.py` plus `tests/` edits, which
  PRD-0010's "In place, in scope" diff check forbids, and the PRD's own
  answer for that case is a backlog seed. The survey's two candidates
  enter the follow-up register: (1) widen detector I's
  `_scannable_files` to reach `evals/` (it misses `evals/README.md`
  today — a real gap, not anticipated); (2) a parity check holding
  AGENTS.md's non-Beads text to CLAUDE.md's — the one recurring drift
  class the survey observed in the act, which by the brief's posture is
  what earns a check. Cites `stdlib-only` for either, when built.
- **(c) Link scan as a recorded one-line command reusing detector I's
  grammar** over a new lint checker (out of the permitted diff, and
  duplicating detector I) and over a throwaway script with its own
  regex (a second owner of "what is a link", which could pass a link
  detector I fails).
- **(d) Follow-ups as a register inside `claims.md`, turned into seeds
  by Operate** over appending to `docs/backlog.md` in this run (the
  brief and PRD keep the backlog out of this diff) and over GitHub
  issues (the brief forbids new issues).
- **(e) AGENTS.md kept as a synchronised duplicate of CLAUDE.md** over
  collapsing it to a pointer — its reader is an agent on another harness
  that auto-loads AGENTS.md and acts on what it says without following
  links (PRD-0010's loading agent), so a pointer would hand that agent
  less than it has today; the duplicate is recorded as deliberate with
  that reader, and its drift is what follow-up (b)(2) proposes to pin.
- **(f) The four routine playbooks' shared skeleton kept as deliberate
  duplication** over collapsing it into one owner — each cloud routine
  loads its own playbook alone, so a cross-link is a passage that
  routine never reads.
- **(g) Remote-state claims excluded from the inventory** over checking
  them with `gh` — PRD-0010 defines the audit against the tree, and a
  network-dependent Check would make Verify's re-run non-hermetic.

## ADRs

None — no decision met the ADR bar. Every choice here is reversible by
editing one run-directory file, and none surprises a reader of
PRD-0010; the one decision with lasting effect (adding a permanent
check) is deliberately deferred to a follow-up. The pull request still
lands through the human gate because it carries this file (ADR-0036,
clause 3), which is already the brief's plan.

## Requirement trace (PRD-0010 success criteria)

- Claim inventory covers the set — the claim inventory and its data
  model; the per-doc pass.
- Every false or stale claim is resolved — the Disposition column; the
  disposition → diff contract; the follow-up register.
- The corrected docs pass their own checks — the Check contract; the
  Verify re-run section; the fourth assumption's exclusion.
- One job per doc — the Jobs table; the Duplicates table; decisions (e)
  and (f).
- Links resolve — the link scan.
- Protocol stays a contract — the per-doc approach row for the protocol;
  the disposition → diff contract.
- In place, in scope — decision (b) (no checker edits), decision (d)
  (no backlog edits); only `claims.md` is added, inside the run
  directory.
- Battery — the prose pins; Implement runs it per doc.
