---
stage: architect
run: maintenance:one-guarded-file-read
date: 2026-10-04
assumptions:
  - "prd.md absent: this is a maintenance run, whose predecessor is defect.md (ADR-0025). The condition brief and autorun-brief.md are the design source; no PRD requirement tracing applies. Every success criterion in the brief is traced in the Traceability section instead."
  - "No ux: echo. The template echoes ux only when a PRD skipped UX Design; a maintenance run has no PRD and no user-facing surface (internal tooling and CI detectors), and the deepening-cli-seams precedent omits the line."
  - "Trade-off 1, decided without live operator input: label_sync.load_labels is hand-fixed, not adopted. The replay the operator saw had no JSON null cell. Adopting with kind=object changes its null cell from 'must be a non-empty JSON array of label entries' to 'is null' (replayed below). Under the rule 'a wording change beyond the two named means hand-fix', its decode error moves by hand to the JSON arm. Its decided pin change (cannot read to is not valid JSON) still happens, and no other cell of it changes. Detector K is hand-fixed for the same reason."
  - "Trade-off 2, decided without live operator input: read_file's existence check sits inside its OSError guard, because Path.is_file raises PermissionError under an unsearchable parent on Python 3.12 (CI's version, measured), which would break 'never raises'. On 3.14 the same cell reads as absent, so that cell is not pinned by an exact-string test."
  - "Trade-off 3, decided without live operator input: factory_config.object_problems and lint.object_problems are deleted in the commit that removes their last caller (both become orphans of the dict kind). TestObjectProblems' two tests die with the first; the second has no direct test."
  - "Trade-off 4, decided without live operator input: reader-level tests die only where the function they test dies. Every other reader-level test stays, even where read_file's own matrix now asserts the same cell. This is the brief's 'when in doubt it stays'."
  - "read_file's final text is the Architect's: the decided prototype with the existence check moved inside the guard and the docstring rewritten. The null problem wording for kind=object is '<shown> is null', as in the prototype."
  - "Unreadable cells are built with chmod 000 and skipped when running as root (os.geteuid() == 0), because root reads a mode-000 file. Existing reader tests that pin unreadable by patching Path.read_text stay as they are."
---

# Architecture: one owner for the guarded local-file read

## Approach

The rule "read a local file and turn every way that can fail into an
unlabelled problem string" moves into one function, `cli.read_file(path,
shown, kind)`, beside `read_event`. It is the deepest point available to
it: three arguments cover the whole failure vocabulary (absent,
unreadable, undecodable, unparsable, wrong top-level shape), and every
caller keeps the two things that are really its own: what absence means
to it, and its label. Readers adopt it where doing so changes no
wording, which the replay below checks cell by cell rather than
predicts. Readers it cannot serve without a fourth parameter get the
missing exception arm by hand and are named here with the reason. The
two shapes compared before this one are in *Decisions & alternatives*:
a classifier that lets each caller word the failure (loses because a
caller can still omit a kind, which is the defect), and a shared module
wording every decode failure "cannot read" (loses because eight pins
change, not two).

The shape follows the one the cli seam already has. `read_event`
returns `(value, problem)` with `(None, None)` for absence, and its
callers prefix their own labels (ADR-0051). `read_file` is the same
contract for an arbitrary repo file.

## Components

### `cli.read_file` (new, in a mirrored seam module)

- Responsibility: the guarded read and parse of one local file,
  including the top-level shape check for `dict` and `list`. It owns the
  failure vocabulary and its wording.
- Collaborators: `pathlib` and `json` only. `cli.py` imports no sibling
  module (lines 37 to 47 are stdlib), so a new edge into it cannot form
  a cycle.
- Deletion test: deleting it puts the five-way guard back into every
  adopter, which is the condition this run exists to end.

### Adopters (thin callers after this run)

Milestone one: `factory_config.load`, detector E
(`gates.check_scaffold_sync`), detector F (`gates.check_config_shape`),
`standards_index.foreign_entries`, `cost_ledger.load` (and `read`, which
is thin over it and does not change), `lint.check_manifest`,
`lint.check_plugin_skills`, `eval_schema.load_case_set`.

Later milestone: `lint.check_pi_package`, `dashboard._corrections`,
`dashboard._backlog`.

### Hand-written exceptions (missing arm added, wording kept)

Milestone one: `label_sync.load_labels`, detector K
(`gates.check_standards_drift`).

Later milestone: `lint.check_output_evals`' inner `problems_for`,
`lint.check_backlog`, `cli.read_execution`, `sweeps.load_payload`,
`dashboard.respond`, `dashboard.respond_post`, `validator.run_review`.

### Untouched

`cli.read_event`, `dashboard.repo_set`, `one_owner.source_files`,
`orientation_pack` (two sites), `knowledge_plane.parse_run`'s
verification read, `charter_replay.main`: none has a raising cell.
`trigger_eval.print_metrics`: deferred, a shape defect after a
successful read. The 39 unguarded reads are out of scope.

## Data model

None. No persisted shape changes. `factory/manifest.json` is rewritten
by `update-manifest` because mirrored files change, which is its normal
job and not a schema change. The cost ledger's line grammar (ADR-0049)
and `cost_ledger.load`'s return shape are untouched.

## Interfaces & contracts

### `cli.read_file(path, shown, kind)`

- Input: `path` (str or `Path`); `shown`, the name the problem uses
  (a repo-relative string, or a `Path` that formats as one); `kind`, one
  of `str`, `dict`, `list`, `object`. All three are required. There is
  no fourth parameter; a reader that would need one is a hand-fix.
- Output: `(value, problem)`.
  - `(None, None)`: no regular file is at `path`. A directory in its
    place counts as absent (`is_file` is false), as it already does for
    every adopter, each of which checked `is_file` first.
  - `(value, None)`: `value` is the text (`str`), or the parsed
    document, an instance of `kind` (`object`: anything but null).
  - `(None, problem)`: exactly one unlabelled string. The caller
    prefixes its own label (ADR-0051).
- Failure modes, in full:

| failure | `kind` | problem |
|---|---|---|
| any `OSError` (permissions, an unsearchable parent on 3.12) | any | `cannot read {shown}: {err}` |
| bytes that are not UTF-8 | `str` | `cannot read {shown}: {err}` |
| bytes that are not UTF-8 | `dict`, `list`, `object` | `{shown} is not valid JSON: {err}` |
| not JSON, or an empty file | JSON kinds | `{shown} is not valid JSON: {err}` |
| top level not an object (null included) | `dict` | `{shown} is not a JSON object` |
| top level not an array (null included) | `list` | `{shown} is not a JSON array` |
| a JSON `null` document | `object` | `{shown} is null` |

- It never raises for a local-file failure. It is in-process and local,
  so there is no timeout, and a retry is safe but pointless (the file
  has not changed).
- Final text (the Architect owns it; Implement copies it, then tests
  it):

```python
def read_file(path, shown, kind):
    """(value, problem) for one local file — the guarded read every
    reader of a repo file shares (ADR-0075). kind is what the caller
    needs back: str (the text), dict (a JSON object), list (a JSON
    array), or object (any JSON document except null).

    (None, None) when no regular file is at path: absence is a fact, not
    an error, and each caller keeps its own meaning for it (a "missing"
    problem, an empty result, a skip) — read_event's convention.
    Otherwise exactly one of the pair is None: value is an instance of
    kind, or problem is one unlabelled string naming the file as
    `shown`, which the caller prefixes with its own label (ADR-0051):

      cannot read <shown>: <err>        any OSError; bytes that are not
                                        UTF-8, when kind is str
      <shown> is not valid JSON: <err>  a parse failure; bytes that are
                                        not UTF-8, when kind is JSON
      <shown> is not a JSON object      kind dict, any other top level
      <shown> is not a JSON array       kind list, any other top level
      <shown> is null                   kind object, a null document —
                                        (None, None) already means absent

    Never raises for a local-file failure: the existence check sits
    inside the guard because Path.is_file raises PermissionError under
    an unsearchable parent before Python 3.14. A reader whose shape
    wording is its own asks for object and keeps its own check."""
    path = Path(path)
    try:
        if not path.is_file():
            return None, None
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        return None, f"cannot read {shown}: {err}"
    except UnicodeDecodeError as err:
        if kind is str:
            return None, f"cannot read {shown}: {err}"
        return None, f"{shown} is not valid JSON: {err}"
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

`cli.py`'s module docstring gains one sentence naming `read_file` among
the harness-IO conventions, citing ADR-0075.

### Per-reader disposition

`{err}` below is Python's exception text, for example `[Errno 13]
Permission denied: '<path>'` or `'utf-8' codec can't decode byte 0xff in
position 0: invalid start byte`. "Absence" is what the caller does with
`(None, None)`.

#### Milestone one

| reader | disposition | call | absence | raising cell, new string |
|---|---|---|---|---|
| `factory_config.load` | adopt | `read_file(path, path.relative_to(root).as_posix(), dict)` per home | next home; after the last, `config: missing factory.json (<homes>)` | none (decided pin: not UTF-8 becomes `config: .github/factory.json is not valid JSON: {err}`) |
| `label_sync.load_labels` | hand-fix | none | unchanged (`taxonomy_path`) | none (decided pin: not UTF-8 becomes `L: .github/labels.json is not valid JSON: {err}`) |
| E `check_scaffold_sync` | adopt | `read_file(root / "factory" / "manifest.json", "factory/manifest.json", dict)` | `E: missing factory/manifest.json` | unreadable: `E: cannot read factory/manifest.json: {err}`; JSON array, string (and null, number, bool, which also raise today): `E: factory/manifest.json is not a JSON object` |
| F `check_config_shape` | adopt | `read_file(path, rel, dict)` per home, every home | skip that home (`continue`) | unreadable: `F: cannot read factory/templates/factory.json: {err}` (or `.github/factory.json`) |
| K `check_standards_drift` | hand-fix | none | unchanged (`[]`) | not UTF-8: `K: docs/standards.json is not valid JSON: {err}` |
| `standards_index.foreign_entries` | adopt | `read_file(Path(root) / STANDARDS_PATH, STANDARDS_PATH, list)` | `([], [])` | not UTF-8: `docs/standards.json is not valid JSON: {err}` (`update` prefixes `standards-index: `) |
| `cost_ledger.load` | adopt | `read_file(path, COST_LEDGER, str)` | `(None, [])` | not UTF-8: `{label}: cannot read docs/factory/costs.jsonl: {err}` |
| `cost_ledger.read` | unchanged code, inherits | through `load(root, "ledger", ...)` | `([], [])` | not UTF-8: `ledger: cannot read docs/factory/costs.jsonl: {err}` |
| `lint.check_manifest` | adopt | `read_file(root / ".claude-plugin" / "plugin.json", "plugin.json", dict)` | `missing .claude-plugin/plugin.json` | unreadable: `cannot read plugin.json: {err}` |
| `lint.check_plugin_skills` | adopt, problem discarded | `data, _ = read_file(<same>, "plugin.json", dict)` | `[]` | unreadable, not UTF-8: `[]` (`check_manifest` reports the file once) |
| `eval_schema.load_case_set` | adopt | `read_file(path, label, dict)` | `missing {label}` | unreadable: `cannot read {label}: {err}` |

#### Later milestone

| reader | disposition | call | absence | raising cell, new string |
|---|---|---|---|---|
| `lint.check_pi_package` | adopt | `read_file(root / "package.json", "package.json", dict)` | `missing package.json` | unreadable: `cannot read package.json: {err}` |
| `lint.check_output_evals` (`problems_for`) | hand-fix | none | n/a (globbed) | unreadable (and a directory named `*.json`): `cannot read evals/output/<name>.json: {err}` |
| `lint.check_backlog` | hand-fix | none | `[]` | not UTF-8: `backlog: docs/backlog.md is unreadable: {err}` |
| `dashboard._corrections` | adopt | `read_file(root / CORRECTIONS, CORRECTIONS, str)` | `{}` | not UTF-8: problems gain `dashboard: cannot read docs/factory/corrections.jsonl: {err}`, returns `{}` |
| `dashboard._backlog` | adopt | `read_file(root / BACKLOG, BACKLOG, str)` | `None` | not UTF-8: problems gain `dashboard: cannot read docs/backlog.md: {err}`, returns `None` |
| `dashboard.respond` (`/`) | hand-fix | none | unchanged (the `OSError` text) | not UTF-8: `500, {"problems": ["dashboard: cannot read dashboard.html: {err}"]}` |
| `dashboard.respond_post` | hand-fix | none | unchanged (the `OSError` text) | not UTF-8: `500, {"problems": ["dashboard: cannot read docs/backlog.md: {err}"]}` |
| `validator.run_review` | hand-fix | none | unchanged (the `OSError` text) | not UTF-8: `V: cannot read findings file {findings}: {err}` |
| `cli.read_execution` | hand-fix | none | unchanged (the `OSError` text) | not UTF-8: `execution file {path} is not valid JSON: {err}` |
| `sweeps.load_payload` | hand-fix | none | unchanged (the `OSError` text) | not UTF-8 (file or stdin): `sweeps: payload is not valid JSON: {err}` |

#### Why each hand-fix is one, and which arm the decode error joins

- **`label_sync.load_labels`** (JSON): with `object`, a `null` document
  reads `L: .github/labels.json is null` instead of `L:
  .github/labels.json must be a non-empty JSON array of label entries`.
  With `list`, `{}` would read `is not a JSON array`, against the pins
  at `tests/test_label_sync.py:125` and `tests/test_gates.py:1131`. The
  fix splits `except (OSError, UnicodeDecodeError)` in two. `OSError`
  keeps `L: cannot read {rel}: {err}`, and `UnicodeDecodeError` joins
  the JSON arm's wording, `L: {rel} is not valid JSON: {err}`. Its
  comment `# Decode before parse, guarded separately: see
  factory_config.load.` points at a comment this run deletes. Replace it
  with one naming the ADR-0075 wording rule.
- **Detector K** (JSON): with `object`, `null` reads `K:
  docs/standards.json is null` instead of `K: docs/standards.json must
  be a JSON array`. With `list`, `{}` breaks the pin at
  `tests/test_gates.py:687`. The fix adds `except UnicodeDecodeError` to
  the read's `try`, which joins the JSON arm's wording.
- **`problems_for`** (JSON): with `object`, `null` reads
  `evals/output/idea.json is null` instead of `... is not a JSON
  object`. With `dict`, a non-object file under a non-skill stem loses
  its `stem is not a skill slug` line. The fix adds `except OSError` →
  `cannot read {label}: {err}`. The decode error already sits on the
  JSON arm.
- **`lint.check_backlog`** (text): read_file says `cannot read`, and the
  pinned phrase (`tests/test_lint.py:1274`) is `is unreadable`. Decode
  joins the `OSError` arm: `except (OSError, UnicodeDecodeError)`.
- **`cli.read_execution`** (JSON): an absent file is an `OSError` message
  today (`tests/test_cli.py:775`), and `(None, None)` cannot reproduce
  `[Errno 2] ...`. With `object`, `null` would also read `is null`
  instead of `has no result entry`. Decode joins the JSON arm through a
  separate `except UnicodeDecodeError` clause, worded `execution file
  {path} is not valid JSON: {err}`.
- **`sweeps.load_payload`** (JSON): the same absence reason
  (`tests/test_sweeps.py:876`). It also reads stdin, which `read_file`
  does not, and today it returns `(None, [])` for a `null` payload.
  Decode joins the JSON arm: a separate `except UnicodeDecodeError`
  clause in the read's `try`, worded `sweeps: payload is not valid JSON:
  {err}`. The clause covers the stdin decode too.
- **`dashboard.respond`, `dashboard.respond_post`,
  `validator.run_review`** (text): an absent file is an `OSError`
  message today (`tests/test_dashboard.py:736`, `:1086`,
  `tests/test_validator.py:433`). Decode joins the `OSError` arm as a
  tuple: `except (OSError, UnicodeDecodeError)`.

### Dual-home and special shapes

- **`factory_config.load`, first home wins (ADR-0048).** It walks
  `artifact_paths` in its installed-first order. The first candidate
  for which `read_file` returns a value or a problem decides the
  result. An installed copy that is present but broken is reported and
  never falls through to the payload copy. That is today's behaviour:
  today `next(... if p.is_file())` picks it, then its read fails. Only
  `(None, None)` moves to the next home.
- **Detector F, every home (ADR-0048).** It walks `reversed(artifact_paths)`
  (payload first, its pinned report order). `(None, None)` means
  `continue`; a problem is appended and the walk continues. So which
  homes are checked, and the order lines are reported in, are both
  unchanged. Pinned at `tests/test_gates.py:1453`. `kind=dict` makes
  `null` read `F: <rel> is not a JSON object`, which is the pinned
  string at `:1436`. That is why F and `load` use `dict` and not
  `object`.
- **`cost_ledger.load` (ADR-0049).** The signature, `(None, [])` for
  absent, the `{label}:` prefix and `parse(text)`'s per-line grammar are
  unchanged. It delegates only the read:

```python
    path = Path(ledger_path) if ledger_path else Path(root) / COST_LEDGER
    text, problem = read_file(path, COST_LEDGER, str)
    if problem:
        return None, [f"{label}: {problem}"]
    if text is None:
        return None, []
    rows = ...  # unchanged
```

  `shown` stays `COST_LEDGER` even when `ledger_path` overrides the
  path, as today. Its docstring's "one OSError-to-problem translation"
  becomes "one guarded read (cli.read_file)".
- **`lint.check_plugin_skills`** discards the problem on purpose, as
  `data, _ = read_file(...)`. A missing, unreadable, undecodable,
  unparsable or non-object manifest all return `[]`, and
  `check_manifest` reports the file once. Replayed: its unreadable and
  not-UTF-8 cells go from a traceback to `[]`.
- **`kind=object` and `null`.** Only the hand-fixed `label_sync` and K
  would have used `object`, and the replay below shows `null` changing
  both. So in this run no adopter asks for `object`. The kind stays in
  the interface because it is the decided shape and the honest one for
  a future caller with its own shape wording and no `null` cell. Its
  only cost is one branch and one test row.

### Fail-closed, observably (success criterion 4)

When the ledger at `docs/factory/costs.jsonl` begins with bytes
`ff fe 00`, measured on the scratch prototype:

- `cost_report.guard(root)` returns a `GuardResult` with `verdict ==
  PAUSE`, `reason == "cr: unreadable ledger — failing closed"`, `cap is
  None`, both `totals` and `month_totals` all zero, and `problems ==
  ["ledger: cannot read docs/factory/costs.jsonl: 'utf-8' codec can't
  decode byte 0xff in position 0: invalid start byte"]`.
  Before the change it raised `UnicodeDecodeError`.
- `budget_guard.record(root, <wo>, ...)` returns exactly one problem,
  `bg: refusing to record <wo>: ledger: cannot read
  docs/factory/costs.jsonl: <err>`, and the ledger's bytes are
  unchanged: no line is appended. Before the change it raised.
- `work_queue.month_to_date` returns `(0, [<the same ledger: problem>])`
  where it raised. The brief names only the first two; a third test is
  cheap and recommended.

### Import edges and the payload

New edges: `factory_config → cli`, `eval_schema → cli`, `cost_ledger →
cli`. `cli` imports only the standard library, so none of the three can
close a cycle. `gates`, `standards_index`, `lint` and `dashboard`
already import `cli` and only widen their `from cli import ...` line.
`factory_config` loses `import json`, its only use being the old
`load`. The scratch copy ran the full suite with it removed.

Root files in `factory_init.MIRRORS` that this run edits:

- milestone one: `cli.py`, `factory_config.py`, `gates.py`,
  `standards_index.py`, `cost_ledger.py`, `label_sync.py`;
- later milestone: `cli.py` (the `read_execution` arm) and
  `validator.py`.

`eval_schema.py`, `lint.py`, `dashboard.py` and `sweeps.py` are not
mirrored. No payload tool imports them, and the new edges point only
at `cli`, which already ships. So `TestPayloadToolsImport` stays green
without a new `MIRRORS` row.

The payload sequence, read from `factory_init.update_manifest`
(lines 284 to 308). It writes every `MIRRORS` entry's transform of the
root file into `factory/templates/<rel>`, then rewrites
`factory/manifest.json` from `gates.manifest_files`, which hashes
everything under `factory/templates/`. All these entries are
`identity`. In every commit that edits a mirrored root file:

1. edit the root file only (never the payload copy by hand);
2. delete any `*.orig` or `*.rej` under `factory/templates/`, because
   `manifest_files` would pin them;
3. run `python3 factory_init.py update-manifest` (it prints
   `factory-init: 0 problem(s)`);
4. stage the root file, `factory/templates/tools/factory/<file>` and
   `factory/manifest.json` together;
5. check with `python3 gates.py` (detector E) and `python3 -m unittest
   tests.test_factory_init`
   (`TestRealTreeMirrors.test_every_mirrored_root_file_matches_its_payload_copy`).

PR #602 also regenerates `factory/manifest.json`. On a conflict, take
either side and run step 3 again (Ship's concern).

## Replay: the proposal proven against the code

The scratch tools are under the session scratchpad, `ogfr/`.
`proto/apply_design.py` applies this design to a `git archive` copy of
the tree, never to the repo. Every edit is an exact-once replacement in
the real function bodies, not a wrapper. Then the recorder and the
probes were run against the copy and against this worktree.

The 144-cell matrix against `baseline-661ffc7.json`, both milestones:

```
cells 144 | identical 123 | fixed 16 | wording changed 2 | still raising 3 | newly raising 0
  CHANGED  factory_config.load / not utf-8
  CHANGED  label_sync.load_labels / not utf-8
  STILL RAISES  trigger_eval.print_metrics / json array: RAISES AttributeError
  STILL RAISES  trigger_eval.print_metrics / json object: RAISES KeyError
  STILL RAISES  trigger_eval.print_metrics / json string: RAISES AttributeError
```

Milestone one alone (`apply_design.py --m1-only`): `cells 144 |
identical 123 | fixed 12 | wording changed 2 | still raising 7 | newly
raising 0`. The four extra raising cells are the later milestone's
`check_pi_package`, `check_backlog`, `read_execution` and
`load_payload`.

The brief's `design_h` prototype, re-run with `proto/check_design.py`:
`design_h: readers 11 | cells identical 74 | raise today, problem string
after 12 | wording changed 2 | still raising 0`.

Cells the matrix does not record (`proto/extra_cells.py`: JSON null,
number, `true`, `[]`, `{}`, and a directory in place of the file, for
17 readers), before against after:

```
cells 102 | identical 97 | fixed 5 | wording changed 0 | still raising 0 | newly raising 0
  FIXED    gates E check_scaffold_sync / json null, json number, json true, empty array
             now: ['E: factory/manifest.json is not a JSON object']
  FIXED    lint.check_output_evals / a directory
             now: ["cannot read evals/output/idea.json: [Errno 21] Is a directory: '<path>'"]
```

The six sites outside the matrix (`proto/probe_six_full.py`: absent,
unreadable and not UTF-8 for each):

```
cells 18 | identical 12 | fixed 6 | wording changed 0 | still raising 0 | newly raising 0
```

**Counterfactual, which is why the hand-fixes are hand-fixes.**
`proto/apply_counterfactual.py` swaps each hand-fix for the adoption it
would have been. It changes wording in 7 matrix cells (the 2 decided,
plus `check_backlog` unreadable and `read_execution`/`load_payload`
absent, not JSON and empty). It also changes 7 extra cells: `null` for
`label_sync`, K, `check_output_evals`, `read_execution` and
`load_payload`, and a directory for `read_execution` and
`load_payload`. And it changes 3 of the six-site cells: absent for
`respond`, `respond_post` and `run_review`. For example:

```
  CHANGED  label_sync.load_labels / json null
             was: ([], ['L: .github/labels.json must be a non-empty JSON array of label entries'])
             now: ([], ['L: .github/labels.json is null'])
  CHANGED  gates K check_standards_drift / json null
             was: ['K: docs/standards.json must be a JSON array']
             now: ['K: docs/standards.json is null']
  CHANGED  validator.run_review / absent
             was: ["V: cannot read findings file <path>: [Errno 2] No such file or directory: '<path>'"]
             now: ['V: missing findings file <path>']
```

**The whole suite, unmodified, against the patched copy:** `Ran 1793
tests`, and exactly two failures, the two decided pins:
`test_factory_config.TestObjectProblems.test_a_config_that_is_not_utf8_is_a_problem`
and
`test_label_sync.TestLoadLabels.test_a_taxonomy_that_is_not_utf8_is_flagged`.
A third failure, `test_shadowed_definitions`, came from the copy having
no git index. It passed once the copy's files were tracked. On the copy
after `update-manifest`: `gates: 0 problem(s)`, `selftest: ok`, `lint: 0
problem(s) across 25 skills`.

**The disposition changed from the brief's expectation for one reader:**
`label_sync.load_labels` was listed to adopt. It is a hand-fix, because
of its `null` cell. Its decided pin change survives. Detector K was
already a `kind=object` adopter in `design_h` and is a hand-fix for the
same reason. Everything else lands where the brief placed it, or (for
the later milestone, which the brief left to the Architect) as tabled
above.

## Test plan

### `read_file`'s own matrix

`tests/test_cli.py`, new class `TestReadFile`, beside `TestReadEvent`.
It is written first and lands with the function. For each of `str`,
`dict`, `list` and `object`, against real temp files
(`tempfile.TemporaryDirectory`), it asserts the exact pair for: absent;
a directory in place; unreadable (chmod 000, `skipIf(os.geteuid() ==
0)`); bytes `b"\xff\xfe"` that are not UTF-8; not JSON; empty; a JSON
object; a JSON array; a JSON string; `null`; a number; `true`; `false`.
It also covers the eight non-object top levels the dying
`TestObjectProblems` covered (`None, [], ["a"], "factory", 5, 0.5, True,
False`) under `dict`. `shown` must be echoed verbatim, including as a
`Path`. One test runs under an unsearchable parent and asserts only
that the function does not raise and that `value is None`. It pins no
exact string, because the outcome depends on the Python version.

### Per reader

"Pinned" lists the existing `def test_` line per cell. "Net" tests are
added in one commit before any reader moves, and pass against today's
code. "Raising" tests are added with the reader's adoption or
hand-fix, watched failing first with the traceback.

| reader | already pinned | net (before any reader moves) | raising (with the change) | dies |
|---|---|---|---|---|
| `factory_config.load` | absent `test_factory_config.py:76`; not JSON `:82`; non-object `:91`, `:104`; object `:62`, `:67`; not UTF-8 `:134` (edited) | unreadable; empty; a broken installed copy is reported, never skipped for the payload | none | `TestObjectProblems.test_an_object_is_clean` `:123`, `test_every_other_json_top_level_is_one_problem` `:127`, with `object_problems` |
| `label_sync.load_labels` | absent `test_label_sync.py:96`; not JSON `:102`, `:204`; `{}`/`[]` `:125`; valid `:71`, `:82`; not UTF-8 `:114` (edited); J `test_gates.py:1131` | unreadable; empty; JSON string and `null` read `must be a non-empty JSON array of label entries` | none | none |
| E | absent `test_gates.py:993`; not JSON `:998`; not UTF-8 `:1010`; object `:978`, `:983` | empty; `{}` reads `E: factory/manifest.json has no files map` | unreadable; array, string, `null` | none |
| F | not UTF-8 `test_gates.py:1227`; non-object `:1436`; both homes `:1453`; object `:1401`, `:1409`, `:1424` | absent (both homes) is `[]`; not JSON and empty, exact; a not-JSON installed home is reported beside a clean payload home | unreadable, per home | none |
| K | absent `test_gates.py:583`; not JSON `:679`; object `:687`; array `:588` | unreadable; empty; JSON string and `null` read `K: docs/standards.json must be a JSON array` | not UTF-8 | none |
| `foreign_entries` | absent `test_standards_index.py:221`; array `:225`; not JSON `:239`; object `:249`; `update` `:260`, `:328` | unreadable; empty; string and `null` read `docs/standards.json is not a JSON array` | not UTF-8 (and through `update`, which refuses to write) | none |
| `cost_ledger.load`/`read` | `load` absent `test_cost_ledger.py:323`, empty `:329`, unreadable `:350`; `read` absent `:379`; guard `test_cost_report.py:277`; record `test_budget_guard.py:440`; month `test_work_queue.py:290` | `read` unreadable reads `ledger: cannot read ...`; `read` empty is `([], [])` | not UTF-8 at `load` and `read`; `cost_report.guard` and `budget_guard.record` fail closed (criterion 4); `work_queue.month_to_date` | none |
| `lint.check_manifest` | absent `test_lint.py:837`; not UTF-8 `:177`; non-object `:207`, `:216`; object `:199`, `:192` | not JSON, exact (`:847` asserts only the count); empty | unreadable | none |
| `lint.check_plugin_skills` | absent `:837`; not JSON `:847`; object `:798` | array and string are `[]` | unreadable and not UTF-8 are `[]` | none |
| `eval_schema.load_case_set` | absent `test_eval_schema.py:150`; not JSON `:155`; not UTF-8 `:170`; non-object `:577`, `:609`, `:618`; object `:144`, `:163`, `:630` | empty | unreadable | none |
| `lint.check_pi_package` | absent `test_lint.py:232`; not JSON `:237`; non-object `:245`; not UTF-8 `:253`; object `:263`, `:270`, `:277` | empty | unreadable | none (`lint.object_problems` has no direct test) |
| `check_output_evals` | not UTF-8 `test_lint.py:1239`; object `:1201`, `:1215`, `:1229` | not JSON; `null` reads `evals/output/idea.json is not a JSON object` | unreadable | none |
| `lint.check_backlog` | absent `test_lint.py:192`; unreadable `:1274`; text `:1257`, `:1266` | empty | not UTF-8 | none |
| `dashboard._corrections` | absent `test_dashboard.py:612`; text `:626`, `:649` | unreadable, through `gather` (the `:612` fixture) | not UTF-8 | none |
| `dashboard._backlog` | absent `test_dashboard.py:1018`; text `:1005` | unreadable, through `gather` | not UTF-8 | none |
| `dashboard.respond` | absent `test_dashboard.py:736`; text `:730` | unreadable (`PAGE` swapped) | not UTF-8 | none |
| `dashboard.respond_post` | absent `test_dashboard.py:1086`; text `:1046`, `:1062`, `:1074` | unreadable | not UTF-8 | none |
| `validator.run_review` | absent `test_validator.py:433`; text `:316` | unreadable | not UTF-8 | none |
| `cli.read_execution` | absent `test_cli.py:775`; not JSON `:783`; arrays `:764`, `:769`, `:792`, `:799`, `:807`; via `record_run` `test_budget_guard.py:505`, `:558`, `:598` | unreadable; empty; `null` reads `has no result entry`; a directory | not UTF-8 | none |
| `sweeps.load_payload` | absent `test_sweeps.py:876`; not JSON `:885`; array `:868`; CLI `:984` | unreadable; empty; `null` is `(None, [])` | not UTF-8 | none |

In total, **2 tests die**:
`tests/test_factory_config.py:123` `TestObjectProblems.test_an_object_is_clean`
and `:127`
`TestObjectProblems.test_every_other_json_top_level_is_one_problem`.
They die in the commit that removes `factory_config.object_problems`,
which is the second of `load` and F to adopt. Their cells move to
`TestReadFile`'s `dict` rows. The wiring stays at
`test_factory_config.py:91` (load) and `test_gates.py:1436` (F). The
not-UTF-8 test at `:134` lives inside `TestObjectProblems` today. It is
edited to the new pin and moved to `TestLoad` in the commit that adopts
`load`, so the class can go. The `label_sync` pin at
`test_label_sync.py:114` is edited in the `label_sync` hand-fix commit.
Each of the two pin edits happens there and nowhere else.

## Stack & dependencies

- Python 3 standard library only (`pathlib`, `json`): CLAUDE.md's
  stdlib rule (`stdlib-only`).
- No new module and no new `MIRRORS` entry. `cli.py` already ships in
  the payload.

## Docs that describe the seam (work items for Implement)

- **`CLAUDE.md`, the "Seam modules" bullet:** yes, one phrase, landed in
  the commit that adds the function. Replace

  > `cli.py` external-CLI + harness-IO conventions,

  with

  > `cli.py` external-CLI + harness-IO conventions and the guarded
  > local-file read (`read_file`, ADR-0075),

- **`CONTEXT.md`:** no line. It holds the domain vocabulary (run,
  stage, artifact, work order, gate), and no seam module is defined
  there. `read_file` adds a function, not a term. So Ship has no new
  glossary term to flag.
- **`cli.py`'s module docstring:** one sentence, as noted under the
  interface.

## Traceability to the brief's success criteria

1. `cli.read_file`, three parameters, own matrix: *Interfaces*,
   `TestReadFile`.
2. Every raising in-scope cell gets a pinned string: the disposition
   tables plus the "raising" column.
3. Exactly 2 wording changes, 0 newly raising, only the three
   `print_metrics` cells still raising: *Replay*, the first block.
4. Fail-closed: *Fail-closed, observably*.
5. One owner by grep: every reader not in the adopter list is named
   under *Hand-written exceptions*, each with its reason.
6. Battery green: replayed on the copy; Verify re-runs it on the
   branch.
7. Payload and manifest level: the five-step sequence.
8. Test ordering: *Test plan*, net then raising-with-change then deaths.
9. ADR-0075 exists, indexed, provisional, passing detector D.

## Decisions & alternatives

- **One function in `cli.py`** over a classifier the caller words (it
  fixes no cell, because a caller can still omit a kind), over a new
  shipped module with "cannot read" for every decode failure (eight
  pins, plus a `MIRRORS` entry), and over two functions with required
  shape and absence arguments (the same result at six parameters).
  These are the three that lost in the brief; ADR-0075 records them.
  `stdlib-only`.
- **No port, no injected opener** over an adapter seam: one adapter is a
  hypothetical seam, and the suite already builds real temp trees.
- **Hand-fix `label_sync` and K** over adopting them with `object`: the
  replay shows their `null` cell changing. Over adopting with `list`:
  that breaks pinned `must be a ... JSON array` strings.
- **Existence check inside the guard** over the prototype's check
  outside it: on CI's Python 3.12 an unsearchable parent makes
  `is_file` raise, which would break the one promise the function
  makes.
- **`dict` for `factory_config.load` and F** over `object` plus
  `object_problems`: with `object`, `null` would read `is null` against
  the pins at `test_factory_config.py:91` and `test_gates.py:1436`.
- **Delete `factory_config.object_problems` and `lint.object_problems`
  once orphaned** over keeping them: once both their callers adopt
  `dict`, the rule they state lives in `read_file`. A function kept only
  for its own test is a second owner. `eval_schema.object_problems`
  stays, because its validators use it.
- **Keep every reader-level test except the two that test a deleted
  function** over pruning the ones `TestReadFile` duplicates: the
  brief's "when in doubt it stays".
- **`shown` stays `COST_LEDGER` under a `ledger_path` override** over
  showing the real path: today's wording, and ADR-0049 keeps the read's
  interface.
- **`check_plugin_skills` discards the problem** over reporting it: one
  broken file, one problem string (`check_manifest` owns it).

## ADRs

- `docs/adr/0075-the-guarded-file-read-joins-the-cli-seam.md` (ADR-0075,
  provisional). It records the function joining the cli seam, why two
  earlier reviews declined and what evidence changed, the non-UTF-8
  wording rule and its two reversals of `json-that-is-not-utf8`, the
  adoption rule and the readers that stay hand-written, and the three
  designs that lost. It amends no other record, so no other status line
  changes.
