# Autorun brief: one-guarded-file-read

Collected 2026-10-04 (UTC) from the operator. This is not a run artifact:
it carries no frontmatter, never counts toward orientation or active-run
discovery, and is the source of interview answers for every stage.

## What the operator decided, and how

The operator ran a deepening review (`deepen`) on 2026-10-03, chose its
first candidate for exploration, and was shown three independent
interface designs replayed against today's recorded behaviour, plus a
recommended hybrid. On 2026-10-04 the orchestrating session asked one
question:

> Should autorun drive the guarded-file-read deepening as a new
> maintenance run, and how far may it go with git?

The operator chose **"Run it, local commits (Recommended)"**, whose text
was:

> New maintenance run one-guarded-file-read, entering at Architect, in
> the empty worktree on branch refactor/one-guarded-file-read. Design:
> the hybrid, one read_file function in cli.py, two pinned strings
> change. Scope: every reader that crashes today, with the ones beyond
> the eleven you saw replayed as a separate milestone. Writes a
> provisional [decision record 0075]. Commits locally per work item so
> the tests-first order is checkable. Ship prepares and stops. No push,
> no pull request, no issue, no paid tool.

The bracketed words replace the option's ADR token for that number.
Detector C reads the token as a dangling citation until the file
exists, so this brief spells it "decision record 0075" throughout.

The options not chosen were: the same run with no commits; the same run
ending in a pushed branch and a draft pull request; a different run.

Everything else in this brief is the evidence and the design the
operator was shown, written down so the stages can read it. Where the
brief goes beyond what the operator was shown, it says so, and the stage
that leans on it logs it under `assumptions:`.

## Run

- Scale: **maintenance run**. Slug `one-guarded-file-read`. Artifacts at
  `docs/fixes/one-guarded-file-read/`.
- Variant: **condition brief** (something degraded, plus the defect
  class it produces). The filename is still `defect.md`.
- Re-entry depth: **architect**. The run adds an entry point to a seam
  module, changes two pinned problem strings, and needs a decision
  record. `defect.md` therefore carries no work items.
- Worktree `/Users/mbutler/github/skills/.claude/worktrees/one-guarded-file-read`,
  branch `refactor/one-guarded-file-read`, cut from `origin/main` at
  `661ffc7`. Every stage works in that worktree and nowhere else.
- Artifact dates are UTC (`date -u +%F`).
- Precedent for artifact depth and ship mechanics:
  `docs/fixes/deepening-tool-seams/` and `docs/fixes/deepening-cli-seams/`.
- Work already in flight, checked 2026-10-04 against the 11 open pull
  requests (#585 to #608): none touches these readers or adds a decision
  record. #602 regenerates `factory/manifest.json`, and #608 and #589
  append to `docs/backlog.md`; those are merge-order hazards for Ship,
  not duplicates.

## The condition

"Read a local file and turn every way that can fail into a problem
string" has no owner. Each reader types its own guard, the guards differ,
and what each one forgot to catch is a traceback where the repo's
contract promises a problem string.

Two earlier reviews looked at exactly this and declined a shared seam:
PR #410's review, and
`docs/fixes/a-utf8-fix-that-stopped-at-the-mirror/review.md` item 3. Their
argument was that the differing exception spellings are "principled
rather than accidental", and that a new seam needs a decision record.
This run reopens that with evidence they did not have: the behaviour
matrix below. It does not treat their conclusion as an oversight.

## Evidence — at `661ffc7`, each line executed or counted

**The sweep.** An AST sweep over the root modules found 67 file-read
sites: 28 sit inside a `try` that catches something (16 modules), 39 are
unguarded. The 28 guarded sites spell their guard five ways: `OSError`
alone; decode and JSON errors with no `OSError`; `OSError` and decode;
all three; and `JSONDecodeError` alone.

**The matrix.** 18 readers were each run, through their public
interface, against 8 kinds of file in scratch trees: absent, unreadable
(mode 000), not UTF-8, not JSON, empty, a JSON array, a JSON object, a
JSON string. 144 cells. **19 raise a traceback today**:

| reader | cells that raise |
|---|---|
| `standards_index.foreign_entries` | not UTF-8 |
| `gates.check_standards_drift` (K) | not UTF-8 |
| `gates.check_scaffold_sync` (E) | unreadable; JSON array; JSON string (`AttributeError`) |
| `gates.check_config_shape` (F) | unreadable |
| `lint.check_manifest` | unreadable |
| `lint.check_plugin_skills` | unreadable; not UTF-8 |
| `lint.check_pi_package` | unreadable |
| `lint.check_backlog` | not UTF-8 |
| `eval_schema.load_case_set` | unreadable |
| `cli.read_execution` | not UTF-8 |
| `sweeps.load_payload` | not UTF-8 |
| `cost_ledger.load` | not UTF-8 |
| `cost_ledger.read` | not UTF-8 |
| `trigger_eval.print_metrics` | JSON array; JSON object (`KeyError`); JSON string |

Readers in the matrix with no raising cell: `factory_config.load`,
`label_sync.load_labels`, `cli.read_event`, `dashboard.repo_set`.

**Six more sites, outside the matrix, measured 2026-10-04.** Each was
run once in a scratch tree against the one kind of file its guard does
not catch. All six raise:

| site | catches | measured |
|---|---|---|
| `dashboard.py:322` `_corrections` | `OSError` | not UTF-8 raises `UnicodeDecodeError` |
| `dashboard.py:466` `_backlog` | `OSError` | not UTF-8 raises `UnicodeDecodeError` |
| `dashboard.py:516` `respond` (page file) | `OSError` | not UTF-8 raises `UnicodeDecodeError` |
| `dashboard.py:572` `respond_post` | `OSError` | not UTF-8 raises `UnicodeDecodeError` |
| `validator.py:324` `run_review` (findings file) | `OSError` | not UTF-8 raises `UnicodeDecodeError` |
| `lint.py:809` `problems_for` (output evals) | decode, JSON | unreadable raises `PermissionError` |

These six were measured on one cell each, not on all eight. Capture
re-runs them before `defect.md` cites them.

**A promise the code does not keep.** `cost_ledger.read` raises on a
ledger that is not UTF-8, so its callers `cost_report.py:118` (the
monthly cap check), `budget_guard.py:194` and `work_queue.py:220` raise
too. Probed in a scratch tree on 2026-10-03: `cost_report.guard` and
`budget_guard.record` both raised, where their docstrings say they fail
closed.

**The class has been fixed one instance at a time before.** Earlier
maintenance runs in this neighbourhood, by slug. Capture confirms each
is the same class before citing it: `json-that-is-not-utf8`,
`a-utf8-fix-that-stopped-at-the-mirror`,
`a-config-that-is-not-an-object`, `a-manifest-that-is-not-an-object`,
`a-config-the-gate-cannot-read`,
`eval-validators-raise-on-non-object-files`.

## The decided interface

One function, in `cli.py` beside `read_event`. This is the prototype the
operator was shown, replayed in scratch. The Architect owns the final
text; the shape is decided:

```python
def read_file(path, shown, kind):
    """(value, problem). (None, None) when the file is absent. Otherwise
    value is an instance of kind and problem is None, or value is None
    and problem is one unlabelled string. kind: str (text), dict, list,
    or object (any JSON document). Never raises for a local-file
    failure."""
    path = Path(path)
    if not path.is_file():
        return None, None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        return None, f"cannot read {shown}: {err}"
    except UnicodeDecodeError as err:
        return None, (f"cannot read {shown}: {err}" if kind is str
                      else f"{shown} is not valid JSON: {err}")
    if kind is str:
        return text, None
    try:
        value = json.loads(text)
    except json.JSONDecodeError as err:
        return None, f"{shown} is not valid JSON: {err}"
    if kind is dict and not isinstance(value, dict):
        return None, f"{shown} is not a JSON object"
    if kind is list and not isinstance(value, list):
        return None, f"{shown} is not a JSON array"
    if value is None:
        return None, f"{shown} is null"
    return value, None
```

What is part of the interface besides the signature:

- **Three parameters, all required.** `kind` is required so the shape
  check cannot be skipped. A fourth parameter is a design-level
  disagreement and routes back to Architect; it is not an Implement call.
- **Absence is the caller's.** `(None, None)` means the file is not
  there. Each caller keeps its own meaning: a "missing ..." problem, an
  empty result, `None`, or a skip.
- **The problem is unlabelled.** The caller prefixes its own label
  (`E: `, `config: `, none for lint). Caller-side prefixing is the
  recorded convention (ADR-0051).
- **Custom shape wording stays with the caller.** A reader whose shape
  message is its own (`label_sync`, detector K) asks for `object` and
  keeps its check.
- **Bytes that are not UTF-8** read as "is not valid JSON" for the JSON
  kinds and "cannot read" for text.
- **Dependency category:** local filesystem, in-process. The suite
  already builds real temp trees (`tests/fixture_tree.py`). No port, no
  adapter, no injected opener: a seam with one adapter is indirection.

Home and edges: `cli.py` ships and imports no sibling. Three modules
gain an import of it: `factory_config` and `eval_schema` (both leaves
today) and `cost_ledger` (imports only `knowledge_plane`). No cycle.
No new module, so no new `MIRRORS` entry.

## What moves, by rule

**The rule.** A guarded read with a cell that raises today is in scope.
It adopts `cli.read_file` when adoption changes no pinned wording, and
otherwise gets the missing arm by hand with its wording kept. A guarded
read with no raising cell stays as it is, with the one exception below.

**Milestone one: the replayed readers, the set the operator saw.**
`factory_config.load`, `label_sync.load_labels`,
`gates.check_scaffold_sync` (E), `gates.check_config_shape` (F),
`gates.check_standards_drift` (K), `standards_index.foreign_entries`,
`cost_ledger.load` (and `read`, which is thin over it),
`lint.check_manifest`, `lint.check_plugin_skills`,
`eval_schema.load_case_set`. Replay result against the matrix: 74 cells
identical, 12 raising cells now return a problem string, 2 wordings
change, 0 still raise.

**The exception.** `factory_config.load` and `label_sync.load_labels`
have no raising cell and adopt anyway: they read the two files every
tool reads, and leaving them out keeps a second spelling alive for the
next reader to copy. Their adoption is the whole cost in pinned strings.

**The two wording changes, both for bytes that are not UTF-8:**

| reader | today | after | pinned at |
|---|---|---|---|
| `factory_config.load` | `config: cannot read .github/factory.json: ...` | `config: .github/factory.json is not valid JSON: ...` | `tests/test_factory_config.py:145` |
| `label_sync.load_labels` | `L: cannot read .github/labels.json: ...` | `L: .github/labels.json is not valid JSON: ...` | `tests/test_label_sync.py:123` |

Seven JSON readers already word it "is not valid JSON". These two were
set to "cannot read" on purpose by `json-that-is-not-utf8` (2026-08-30),
so the decision record must say this run reverses that and why.

**A later milestone: everything the operator did not see replayed.**
The operator approved the scope "every reader that crashes today" with
these as a separate milestone, so Review or the operator can cut it
without touching milestone one. No pinned wording may change here.

- Same pattern as a replayed reader: `lint.check_pi_package`,
  `lint.py:809` `problems_for`.
- The five measured text reads: `dashboard._corrections`,
  `dashboard._backlog`, `dashboard.respond`, `dashboard.respond_post`,
  `validator.run_review`. Each adopts or is fixed by hand under the rule.
- Fixed by hand, wording kept: `lint.check_backlog` (its phrase is "is
  unreadable"), `cli.read_execution` and `sweeps.load_payload` (for both,
  an absent file is an `OSError` message today, which `read_file`'s
  absence contract cannot reproduce; `load_payload` also reads stdin).

Which of these adopt and which are fixed by hand is the Architect's
call under the rule; the operator was not asked per reader.

**Left alone, no raising cell.** `cli.read_event`, `dashboard.repo_set`,
`one_owner.source_files`, `orientation_pack` (two sites),
`knowledge_plane.parse_run`'s verification read, `charter_replay.main`.

## New strings for cells that raise today (from the replay)

| reader / cell | after |
|---|---|
| E / unreadable | `E: cannot read factory/manifest.json: ...` |
| E / JSON array, JSON string | `E: factory/manifest.json is not a JSON object` |
| F / unreadable | `F: cannot read factory/templates/factory.json: ...` |
| K / not UTF-8 | `K: docs/standards.json is not valid JSON: ...` |
| `foreign_entries` / not UTF-8 | `docs/standards.json is not valid JSON: ...` |
| `cost_ledger.load` / not UTF-8 | `{label}: cannot read docs/factory/costs.jsonl: ...` |
| `lint.check_manifest` / unreadable | `cannot read plugin.json: ...` |
| `lint.check_plugin_skills` / unreadable, not UTF-8 | `[]` (`check_manifest` reports) |
| `eval_schema.load_case_set` / unreadable | `cannot read {label}: ...` |

## Test ordering — not optional

1. **`read_file`'s own tests**, the full failure matrix at the new
   function, land with the function. Nothing calls it yet.
2. **Before any reader moves:** tests through each in-scope reader's
   public interface for every cell that does not raise today and is not
   already pinned. They pass against today's code. This is the net, and
   it lands in its own commit ahead of the first adoption.
3. **Per reader:** a test for each raising cell, watched to fail for the
   right reason (the traceback), then the adoption or hand fix that turns
   it green, in one commit.
4. **Old tests die last, in the commit that adopts.** A reader-level
   test may die only when the same cell is asserted at `read_file` and
   one wiring assertion remains for that reader (label prefixed, absence
   meaning kept). When in doubt it stays. The commit message says which
   coverage moved where.

A pinned string other than the two named above that needs editing to
make an adoption pass means the adoption is wrong for that reader: fall
back to the hand fix. Never edit the pin to match.

## Constraints and recorded decisions

- **Stdlib only.** Standalone scripts, bare sibling imports.
- **Problem-string contract.** Checkers return lists of label-prefixed
  problem strings; tests assert exact strings through public interfaces.
  ADR-0037 rejected a structured-findings layer; do not reopen it.
- **New shared module bar** (CLAUDE.md): multiple real callers and
  observed divergence. Met by the matrix, and no new module is added.
- **Payload.** `cli`, `cost_ledger`, `factory_config`, `gates`,
  `label_sync`, `standards_index` and `validator` are mirrored. After
  editing any root file in `factory_init.MIRRORS`: bring the payload
  copy level through its entry's transform, delete any stray
  `.orig`/`.rej`, then `python3 factory_init.py update-manifest`, in the
  same commit.
- **Decisions, with status** (from `docs/adr/README.md`): ADR-0037
  amended by 0039 (the seams and what deliberately did not move);
  ADR-0042 amended by 0051, and ADR-0051 accepted (what joined the cli
  seam; caller-side prefixing); ADR-0048 accepted (dual-home files
  resolve through `factory_config.artifact_paths`: runtime readers take
  the first existing home, detector F checks every home); ADR-0049
  accepted (`cost_ledger.load` keeps its interface and stays "the
  labelled read"; only what it delegates to changes); ADR-0065
  provisional (`protocol.read_frontmatter` moves to its own module:
  leave it).
- **A decision record is required, and the operator approved a
  provisional decision record 0075.** It is the next free number on
  `origin/main`,
  and no open pull request adds one. It records the function joining the
  cli seam, the non-UTF-8 wording rule and the two reversals, the
  adoption rule, and the three designs that lost. Old ADRs are never
  rewritten; only a status line may change, in the grammar `gates.py`'s
  `ADR_STATUS` accepts. Any `docs/adr/**` change makes the eventual pull
  request a human gate-2 merge (ADR-0036 clause 3).
- **Glossary.** "Artifact" in `CONTEXT.md` means a stage's output. Do
  not call an arbitrary file an artifact. A new term goes into
  `CONTEXT.md` only if the design needs one, and Ship flags it in
  `release.md` for the operator to read before merge.
- **Vocabulary for the design artifacts:** module, interface,
  implementation, depth, seam, adapter, leverage, locality.
- **Detector C** scans run artifacts for work-order tokens: never write
  a `WO-` number in this run's artifacts. Run `python3 gates.py` after
  writing any file under `docs/fixes/`.

## Out of scope — do not widen into these

- `trigger_eval.print_metrics` raising on a results file whose top level
  is not an object or lacks keys: a different defect (file shape, not the
  read). `defect.md` records it as deferred. Do not append it to
  `docs/backlog.md`: three open pull requests already append there, and
  the retro can carry the seed.
- The 39 unguarded reads. `knowledge_plane.parse_run` reads uncaught on
  purpose; lint reads files it has just listed.
- `protocol.read_frontmatter` (ADR-0065).
- Any change to `cost_ledger.load`'s signature or return shape.
- `docs/backlog.md`'s seed "Repo-wide lint read_text error policy": this
  run does not close it (lint's unguarded reads stay), so do not claim
  it. `defect.md` may note the overlap.
- `skills/**` prose, `evals/**`, the pipeline protocol, the plugin
  version.

## Success criteria

1. `cli.read_file` exists with the three-parameter interface above, and
   its own tests assert every failure kind for every `kind`.
2. Every in-scope cell that raises today returns a problem string, with
   the exact string pinned by a test through the reader's public
   interface.
3. No pinned wording changes except the two named. Shown by the matrix
   replayed after the change: exactly 2 wordings changed, 0 cells newly
   raising, and the only cells still raising are
   `trigger_eval.print_metrics`'s three.
4. A ledger that is not UTF-8 makes `cost_report.guard` and
   `budget_guard.record` take their fail-closed path, shown by a test.
5. One owner, by grep: no in-scope reader still types its own
   `read_text` guard, and each one that stays hand-written is named in
   `architecture.md` with its reason.
6. The battery is green at the last commit:
   `python3 -m unittest discover tests`; `python3 lint.py` matching
   `lint: 0 problem(s)`; `python3 gates.py && python3 gates.py --selftest`
   matching `gates: 0 problem(s)` and `selftest: ok`.
7. Payload and manifest are level with the root: detector E and
   `tests/test_factory_init.py` green.
8. The test ordering above is visible in the commit history.
9. Decision record 0075 exists under `docs/adr/`, is indexed, and passes
   the ADR detectors.

## Tracker

**No tracker interaction** (the operator's answer: "no issue"). No issue
is created, labelled or closed, and work items carry no `(tracker: #N)`
reference. The breakdown is the state. The eventual pull request needs
this repo's detector-B waiver or a tracking issue; that is an operator
step, listed by Ship.

## User-facing surface

None. Internal tooling and CI detectors. Maintenance runs skip the PRD,
so no `ux:` decision arises.

## Release authorization

**Prepare and stop** (the operator's answer). Not authorized: push, pull
request, merge, tag, plugin version bump, any tracker write. Ship writes
`release.md` with the exact commands and executes none of them.

**Commits: local only, on `refactor/one-guarded-file-read`** (the
operator's answer: "Commits locally per work item so the tests-first
order is checkable"). The Implement stage commits its own items at item
boundaries. Every other stage leaves its artifact uncommitted, and the
orchestrator commits it after gating. Messages are Conventional Commits
and end with:

    Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>

## Spend

**None** (the operator's answer: "no paid tool"). `trigger_eval.py` and
`charter_replay.py` make paid model calls and are not run. No trigger,
no dispatch, no network write. A stage that would need one stops and
surfaces.

## How every stage works

- One fresh context per stage. It reads this brief, the pipeline
  protocol, its stage skill, `CLAUDE.md`, `CONTEXT.md`, and the run
  directory.
- Interview questions are answered from this brief. Where it is silent
  and the stage skill offers a recommended default, the stage takes the
  default and logs it under `assumptions:`. Where there is no default,
  or the question is about evidence, the stage stops and surfaces.
- Verification evidence is real: commands are run and their output
  quoted.
- Work stays inside this worktree: no other branch, worktree, the main
  checkout, or the stash.

## Interview answers the stages will need

- **What is degraded?** See "The condition". Target state: one owner for
  the guarded read at the cli seam; every in-scope reader a thin caller
  or a named hand-written exception.
- **Root-cause hypothesis** (the orchestrating session's, labelled as a
  hypothesis; the operator was not asked): with no owner, each reader
  copied its guard from whichever sibling its author had open, and each
  earlier fix run repaired the instances in front of it without
  enumerating the class.
- **Blast radius.** Internal tooling, CI detectors, and the mirrored
  payload stamped into product repos. Who is affected: the operator and
  dispatched agents, who get a traceback where a problem string was
  promised; and the monthly cap check, which raises where it promises to
  fail closed. Two problem strings change wording. Risk concentrates in
  `gates.py` and in the payload, where a stale manifest fails detector E.
  Since when: not established; do not assert a date.
- **Ruled out.** (a) A module that classifies the failure and lets each
  caller word it: changes no string and fixes no cell, because a caller
  can still omit a failure kind. (b) One function in a new shipped module
  with "cannot read" for every decode failure: 8 pinned strings change
  and it costs a `MIRRORS` entry. (c) Two functions with required shape
  and absence arguments: same result as the hybrid at six parameters.
  (d) A port or injected opener: one adapter. (e) Folding
  `read_frontmatter` in: ADR-0065 owns that.
- **How this dies.** An adoption quietly changes a string and the pin is
  edited to match. The function grows parameters until it is as wide as
  the guards it replaced. The payload or manifest goes stale. The run
  widens into the unguarded reads.

## Scratch tools — session-local, not durable, not part of the repo

Under
`/private/tmp/claude-501/-Users-mbutler-github-skills/ee622348-c85b-44f3-8ebf-f048e89ab1b3/scratchpad/ogfr/`.
Every fact above is stated here so nothing depends on them surviving.
Each runs from the worktree root and writes nothing inside the repo.

- `baseline-661ffc7.json` — the 144-cell matrix at `661ffc7`. Read-only.
- `matrix.py <scratch dir> <out.json>` — re-records the matrix.
- `diff_matrix.py <before.json> <after.json>` — identical, fixed,
  changed, still raising, newly raising.
- `probe_six.py <scratch dir>` — the six sites outside the matrix.
- `sites.py <out.json>` — the AST sweep of read sites.
- `proto/cli_h.py`, `proto/design_h.py` — the hybrid prototype and the
  replayed readers rewritten against it.
