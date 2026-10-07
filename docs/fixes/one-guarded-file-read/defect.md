---
stage: capture
run: maintenance:one-guarded-file-read
date: 2026-10-04
re-entry: architect
assumptions:
  - "Root-cause hypothesis: the brief attributes it to the orchestrating session, not to the operator, who was not asked. It is carried below as a hypothesis with that attribution."
  - "Since when: the brief says not established and forbids asserting a date, so the Blast radius section states none."
  - "The brief's evidence was recorded at 661ffc7. This worktree is at 1d5e7c8, which adds only autorun-brief.md over 661ffc7, so every re-run below is against the same source. Counts and cells matched the brief; the one place the brief's wording needed care is noted under Notes."
  - "Work in flight: the brief records a check of 11 open pull requests on 2026-10-04. Capture re-ran it itself and got the same 11 (#585 to #608); the outcome is stated below as the re-run's, not the brief's."
  - "The six earlier fix runs the brief names were each read (title and first section) and all six are the same class, so none was dropped."
---

# Condition: reading a local file has no owner

## Defect (or Condition)

"Read a local file and turn every way that can fail into a problem
string" has no owner. The repo's contract is that checkers and loaders
return label-prefixed problem strings and never raise for a bad local
file. Each reader types its own guard, the guards differ, and what each
one forgot to catch is a traceback where the contract promises a
problem string. Nothing in the tree states the rule once; it is
re-derived, slightly differently, at every site.

Two earlier reviews looked at exactly this and declined a shared seam:
PR #410's review, and
`docs/fixes/a-utf8-fix-that-stopped-at-the-mirror/review.md` item 3.
Their argument was that the differing exception spellings are
"principled rather than accidental" and that a new seam needs a
decision record. This run reopens that with evidence they did not have,
the behaviour matrix below. It does not treat their conclusion as an
oversight: item 3 itself says the count "is exactly the 'observed
divergence between copies' clause" and leaves the seam to a third run.

**Target state that ends this run.** One owner for the guarded read at
the cli seam: a single `read_file(path, shown, kind)` function beside
`cli.read_event`, returning `(value, problem)`, `(None, None)` when the
file is absent, and never raising for a local-file failure. Every
in-scope reader (a guarded read with a cell that raises today) is
either a thin caller of it or a named hand-written exception with its
reason recorded in `architecture.md`. The decided shape, not reopened by
this run: three required parameters (`kind` is `str`, `dict`, `list` or
`object` so the shape check cannot be skipped); absence is the
caller's, who keeps its own meaning for it; the problem is unlabelled
and the caller prefixes its own label (ADR-0051); a reader with custom
shape wording asks for `object` and keeps its own check; bytes that are
not UTF-8 read as "is not valid JSON" for the JSON kinds and "cannot
read" for text. Dependency category: local filesystem, in-process, so no
port and no adapter. No new module, so no new `MIRRORS` entry. The
Architect owns the final text and the adopt-or-hand-fix call per
reader.

## Reproduction / Evidence

All of it re-run in this worktree on 2026-10-04 and quoted from that
run. The scratch tools that drove it live under the session scratchpad
and are not durable; the facts are stated here.

**The sweep.** An AST sweep over every root module's `read_text` /
`read_bytes` / `open` sites, excluding `tests/`, found:

    sites 67 | guarded 28 | unguarded 39 | open() among them 2

A "guarded" site sits inside a `try` that catches something. The 28
guarded sites spell the guard five ways: `OSError` alone; decode and
JSON errors with no `OSError`; `OSError` and decode; all three; and
`JSONDecodeError` alone (`lint.py:98`).

**The matrix.** 18 readers each run through their public interface
against 8 kinds of file in scratch trees (absent, unreadable by mode
000, not UTF-8, not JSON, empty, a JSON array, a JSON object, a JSON
string): 144 cells. Re-recorded against the checked-in baseline, the
diff reads:

    cells 144 | identical 125 | fixed 0 | wording changed 0
      | still raising 19 | newly raising 0

So the matrix reproduces exactly: **19 cells raise a traceback**.

| reader | cells that raise |
|---|---|
| `standards_index.foreign_entries` | not UTF-8 |
| `gates.check_standards_drift` (K) | not UTF-8 |
| `gates.check_scaffold_sync` (E) | unreadable (`PermissionError`); JSON array, JSON string (`AttributeError`) |
| `gates.check_config_shape` (F) | unreadable |
| `lint.check_manifest` | unreadable |
| `lint.check_plugin_skills` | unreadable; not UTF-8 |
| `lint.check_pi_package` | unreadable |
| `lint.check_backlog` | not UTF-8 |
| `eval_schema.load_case_set` | unreadable |
| `cli.read_execution` | not UTF-8 |
| `sweeps.load_payload` | not UTF-8 |
| `cost_ledger.load` (label `G`) | not UTF-8 |
| `cost_ledger.read` | not UTF-8 |
| `trigger_eval.print_metrics` | JSON array, JSON string (`AttributeError`); JSON object (`KeyError`) |

All the not-UTF-8 cells raise `UnicodeDecodeError: 'utf-8' codec can't
decode byte 0xff in position 0: invalid start byte`. Readers in the
matrix with no raising cell: `factory_config.load`,
`label_sync.load_labels`, `cli.read_event`, `dashboard.repo_set`.

**Six more sites, outside the matrix.** Each run once in a scratch tree
against the one kind of file its guard does not catch (one cell each,
not all eight). All six raise. Line numbers confirmed against the
source here:

| site | catches | measured |
|---|---|---|
| `dashboard.py:322` `_corrections` | `OSError` | not UTF-8 raises `UnicodeDecodeError` |
| `dashboard.py:466` `_backlog` | `OSError` | not UTF-8 raises `UnicodeDecodeError` |
| `dashboard.py:516` `respond` (page file) | `OSError` | not UTF-8 raises `UnicodeDecodeError` |
| `dashboard.py:572` `respond_post` | `OSError` | not UTF-8 raises `UnicodeDecodeError` |
| `validator.py:324` `run_review` (findings file) | `OSError` | not UTF-8 raises `UnicodeDecodeError` (zero `gh` calls made before the read) |
| `lint.py:809` `problems_for` (output evals) | decode, JSON | unreadable raises `PermissionError` |

In the same run, the cell each of these guards does catch behaves: an
unreadable `corrections.jsonl` returns a `dashboard: cannot read ...`
problem, and a non-UTF-8 `evals/output/idea.json` returns
`evals/output/idea.json is not valid JSON: 'utf-8' codec can't decode
byte 0xff ...`.

**A promise the code does not keep.** `cost_ledger.read` raises on a
ledger that is not UTF-8, and three callers inherit the raise:
`cost_report.py:118` (the monthly cap check), `budget_guard.py:194` and
`work_queue.py:220`. Re-probed in a scratch tree outside the repo whose
`docs/factory/costs.jsonl` begins with bytes `ff fe 00`:

    cost_ledger.read         -> RAISES UnicodeDecodeError 'utf-8' codec
                                can't decode byte 0xff in position 0
    cost_report.guard        -> RAISES UnicodeDecodeError (same)
    budget_guard.record      -> RAISES UnicodeDecodeError (same)
    work_queue.month_to_date -> RAISES UnicodeDecodeError (same)

`cost_report.guard`'s docstring says "FAILS CLOSED: any read or
resolution problem decides PAUSE", and `budget_guard.record`'s says it
"Fails CLOSED on an unreadable or unparseable ledger" and returns
`bg:` problems. Both have a fail-closed path (`PAUSE` with `cr:
unreadable ledger`, and a `bg: refusing to record` list), but neither
reaches it, because `cost_ledger.load` catches only `OSError`
(cost_ledger.py:247) and the decode error is not one. Driven for both
guards; `work_queue.month_to_date` is a third caller that raises for the
same reason.

**The class has been fixed one instance at a time before.** Six earlier
maintenance runs, each read (title and opening section) and confirmed to
be the same class, a reader guarding some but not all of the ways a
local file read-and-parse can fail:

- `json-that-is-not-utf8` (2026-08-30): "a JSON file whose bytes are not
  UTF-8 crashes five readers".
- `a-utf8-fix-that-stopped-at-the-mirror` (2026-08-31): the same fix
  stopped at the mirror boundary; its review item 3 is the declined seam.
- `a-config-that-is-not-an-object` (2026-08-30):
  `factory_config.load` guards the parse and hands any parsed value to
  callers.
- `a-manifest-that-is-not-an-object` (2026-08-27): both manifest readers
  catch a parse failure and assume a dict.
- `a-config-the-gate-cannot-read` (2026-08-27): both config loaders
  decode before they parse and guard only the parse.
- `eval-validators-raise-on-non-object-files` (2026-08-27): every
  `eval_schema` validator assumes a dict.

Each repaired the instances in front of it. Today's matrix shows
instances the six did not reach.

## Root-cause hypothesis

**Hypothesis, not a finding, and not the operator's.** The brief
attributes it to the orchestrating session; the operator was not asked.
With no owner for the read, each reader copied its guard from whichever
sibling its author had open, and each earlier fix run repaired the
instances in front of it without enumerating the class. The five
spellings of the guard and the six runs above are consistent with that;
neither proves it. It is the sentence to correct if it is wrong.

## Blast radius

- **Internal tooling, CI detectors, and the mirrored payload stamped
  into product repos. No user-facing surface, no data migration, no
  external contract.**
- **Who suffers today:** the operator and dispatched agents, who get a
  traceback where a problem string was promised; and the monthly cap
  check, which raises where it promises to fail closed
  (`cost_report.guard`, `budget_guard.record`).
- **How badly:** a bad local file (non-UTF-8 bytes, a mode-000 file, a
  JSON array where an object is expected) crashes the checker or tool
  instead of reporting. Detectors E, F and K are in that list, so a bad
  file takes down a CI detector rather than failing it with a message.
- **Wording change:** two problem strings change, both for non-UTF-8
  bytes: `factory_config.load` (pinned at
  `tests/test_factory_config.py:145`) and `label_sync.load_labels`
  (pinned at `tests/test_label_sync.py:123`), from "cannot read ..." to
  "is not valid JSON: ...". `json-that-is-not-utf8` set those two to
  "cannot read" on purpose, so the decision record must say this run
  reverses that, and why.
- **Where the risk concentrates:** `gates.py`, because the detectors are
  the CI suite; and the payload. `cli`, `cost_ledger`, `factory_config`,
  `gates`, `label_sync`, `standards_index` and `validator` are mirrored,
  so any edit needs the payload copy levelled and
  `python3 factory_init.py update-manifest` in the same commit, or
  detector E fails.
- **Gate:** any `docs/adr/**` change makes the eventual pull request a
  human gate-2 merge (ADR-0036 clause 3).
- **Since when:** not established, and no date is asserted.

Scale: small-to-medium. The code change is one function, three new
imports (`factory_config`, `eval_schema` and `cost_ledger` gain an import
of `cli`; none creates a cycle) and about a dozen reader edits; the
weight is in the pinned strings and the payload.

## Ruled out

Each closed for a stated reason; none to be reopened inside this run.

- **A module that classifies the failure and lets each caller word it.**
  Changes no string and fixes no cell, because a caller can still omit
  a failure kind.
- **One function in a new shipped module, with "cannot read" for every
  decode failure.** Changes 8 pinned strings and costs a `MIRRORS`
  entry.
- **Two functions with required shape and absence arguments.** The same
  result as the decided function at six parameters.
- **A port or an injected opener.** One adapter is indirection; the
  suite already builds real temp trees (`tests/fixture_tree.py`).
- **Folding `protocol.read_frontmatter` in.** ADR-0065 (provisional)
  moves it to its own module; leave it.
- **A structured-findings layer over problem strings.** ADR-0037
  (amended by ADR-0039) rejected it; not reopened.
- **The 39 unguarded reads.** `knowledge_plane.parse_run` reads
  uncaught on purpose, and lint reads files it has just listed.
- **Readers with no raising cell.** `cli.read_event`,
  `dashboard.repo_set`, `one_owner.source_files`, `orientation_pack`
  (two sites), `knowledge_plane.parse_run`'s verification read and
  `charter_replay.main` stay as they are. The one exception is
  `factory_config.load` and `label_sync.load_labels`, which adopt anyway
  because every tool reads those two files and leaving them out keeps a
  second spelling alive for the next reader to copy.
- **Any change to `cost_ledger.load`'s signature or return shape.**
  ADR-0049 (accepted) keeps it "the labelled read"; only what it
  delegates to changes.
- **`skills/**` prose, `evals/**`, the pipeline protocol, the plugin
  version.**

## Notes

- **Variant.** A condition brief: the defect class is the symptom, the
  missing owner is the condition. The filename stays `defect.md`.
- **Re-entry is architect.** The run adds an entry point to a seam
  module, changes two pinned strings and needs a decision record
  (provisional, number 0075, the next free one: `docs/adr/` ends at
  0074). Work items live in `architecture.md` and `breakdown.md`.
- **Capture interviewed no one.** Every answer came from
  `autorun-brief.md`, collected from the operator on 2026-10-04. It is
  not a run artifact and never counts toward orientation.
- **Work already in flight: nothing matched.** The check ran.
  `gh pr list --state open --limit 60 --json number,title,headRefName,isDraft`
  succeeded and returned 11 open pull requests, #585 to #608 (the cap of
  60 was not reached). None touches these readers, adds a decision
  record, or does this run's work, judged by title and head branch: #608,
  #606, #604 are autorun artifact PRs for other runs, #602 is a
  `work_queue` blocked-by fix, #600 and #595 are `charter_replay`, #598
  `decompose`, #597 the SWE charter, #596 a research note, #589 and #585
  doc edits. The brief records #602 regenerating `factory/manifest.json`
  and #608 and #589 appending to `docs/backlog.md`; those are
  merge-order hazards for Ship, not duplicates.
- **Deferred, not part of this run:** `trigger_eval.print_metrics` raises
  on a results file whose top level is not an object or lacks keys (the
  matrix's three cells: JSON array, JSON string, JSON object). That is a
  different defect, file shape rather than the read, and not an
  unguarded read at all: it fails after a successful guarded parse.
  Recorded here as deferred. It is not appended to `docs/backlog.md`,
  because three open pull requests already append there; the retro can
  carry the seed. Success for this run therefore leaves exactly those
  three cells raising.
- **Overlap, not claimed.** The backlog seed "Repo-wide lint read_text
  error policy (decode/OS errors) instead of per-checker handling"
  (docs/backlog.md line 13) overlaps this run on lint's guarded reads
  (`check_manifest`, `check_plugin_skills`, `check_pi_package`,
  `check_backlog`, `problems_for`). This run does not close it: lint's
  unguarded `read_text` sites stay. No seed is claimed and
  `docs/backlog.md` is untouched.
- **Matrix wording.** The brief counts replay results as "74 cells
  identical" after the change; the 125 identical cells above are the
  before-change run against its own baseline, a different comparison.
- **No tracker interaction.** No issue is created, labelled or closed,
  and no intake seed exists.
- **How this run dies.** An adoption quietly changes a string and the
  pin is edited to match; the function grows parameters until it is as
  wide as the guards it replaced; the payload or manifest goes stale;
  the run widens into the unguarded reads.
