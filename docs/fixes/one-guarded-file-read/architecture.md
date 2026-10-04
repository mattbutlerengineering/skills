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
  - "Amendment 2026-10-04, option (a): dropping the object kind follows review.md's recommended option (a). It is taken as the default because the operator re-invoked autorun without naming an option (autorun-brief.md, 'Resume, 2026-10-04'). This is the orchestrating session's reading, not the operator's words."
  - "Amendment 2026-10-04, the ValueError message, decided without live operator input: the unknown-kind message is 'read_file kind must be str, dict or list, not <repr>', not review.md's suggested 'read_file: unknown kind <repr>'. It names the three kinds so that a string passed where the type was meant reads as the mistake it is, and it carries no 'label:' prefix that could pass for a problem string."
  - "Amendment 2026-10-04, the RecursionError trade-off, decided without live operator input: read_file catches RecursionError from the parse although the exception names no cause, so a document that tips a caller already deep in recursion over the limit is reported as not valid JSON. Accepted because no caller recurses (deepest seen across the suite: 21 frames of 1000) and the alternative keeps a document that makes read_file raise. MemoryError is left to propagate, stated and not probed."
  - "Amendment 2026-10-04, the scope fence, decided without live operator input: the brief fences the hand-written JSON readers out of Minor 1. The replay found a group the brief does not name, the readers that adopted with kind str and parse each line themselves (cost_ledger.load, and so read, and dashboard._corrections). They are treated as inside the same fence and still raise on those two documents, as at 661ffc7. ADR-0075 decision 5's closing gains one sentence saying the wider parse guard is read_file's alone, which is an edit beyond the four the orchestrating session listed."
  - "Amendment 2026-10-04, the eight comments, decided without live operator input: the wording of the eight Minor 5 comments is the Architect's. For lint.check_output_evals' problems_for the reason given is not a null wording of its own (with dict its null cell reads the same words) but the stem line it reports beside the shape problem and the directory it words 'cannot read'. ADR-0075 decision 5's first bullet is reworded to match, and its new alternative names five readers where review.md counted four, because the first pass's counterfactual also changed sweeps.load_payload's null cell."
  - "Amendment 2026-10-04, the test pins, decided without live operator input: the two Minor 1 documents are pinned at read_file's own tests only, the integer by its exact string (the same on 3.12 and 3.14) and the nesting by prefix (the text differs by version), with 1,000,000 balanced arrays rather than 200,000 (the first nesting that raises on 3.14 here is about 116,000). No reader-level test is added for them."
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

*Amended 2026-10-04: the interface as it stands is under `## Amendments`, at the end of this file.*

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

## Amendments

Appended after review (`review.md`: one major, six minors), on the
resume `autorun-brief.md` records. The body above is the first pass and
stays as the record of what was designed first. Where an entry below
contradicts it, the entry is the design, and each entry names what it
supersedes. The dated entries are the decisions. The sections after
them hold the final text, the comments, the tests and the proof.

- **2026-10-04 — three kinds, not four (review Major, option (a)).**
  `read_file` takes `str`, `dict` or `list`. The `object` kind and its
  `<shown> is null` branch go. The reason is the review's evidence. The
  fourth kind was approved for two named callers, `label_sync` and
  detector K, which were to keep their own shape check behind it. The
  first pass's counterfactual showed it changing the `null` cell of
  every reader it was tried on, so each of those became hand-written,
  and no adopter asks for it: an AST sweep at HEAD finds eleven callers,
  three passing `str`, seven `dict`, one `list` (*Proof 1*). A kind
  with no caller is anticipated reuse, which CLAUDE.md's bar for shared
  code excludes. The first pass kept the kind as "the honest one for a
  future caller". That was argued before the replay took the kind's
  callers away, and it is withdrawn. The hand-written readers still
  cannot adopt with three kinds, which is now measured, not argued
  (*Proof 7*). What the drop costs: nothing recorded. No caller passes
  the kind, and the 144-cell matrix is byte-identical (*Proof 2*). The
  cells that do move outside the matrix belong to the parse guard
  below, not to the drop (*Proof 3*).
  Superseded in the body: the fourth kind on the interface's *Input*
  and *Output* lines, the last row of its failure table, the
  `kind=object` and `null` bullet under *Dual-home and special shapes*
  (which argued for keeping the kind), the `object` halves of *Why each
  hand-fix is one*, the `object` rows of the test plan, and the
  frontmatter assumption that words the `object` null problem.

- **2026-10-04 — an unknown `kind` is a `ValueError` at the call
  (Minor 2).** The check is the function's first statement. It runs
  before `Path(path)`, so the file is not touched, and it raises
  whether or not the file is there (*Proof 4*). The exact message is
  `read_file kind must be str, dict or list, not <repr of the kind>`.
  The review suggested `read_file: unknown kind <repr>`. This one names
  the three kinds because the slip Minor 2 describes is a string where
  the type was meant, and `unknown kind 'dict'` reads as a
  contradiction where `must be str, dict or list, not 'dict'` shows the
  quotes are the mistake. It also carries no `label:` prefix, so it
  cannot pass for a problem string.
  This does not break "never raises for a local-file failure". A wrong
  kind is a slip in the calling code, and it shows the first time the
  call runs under any test, whatever the file holds. The codebase
  already treats a literal-only argument this way:
  `factory_config.artifact_paths` says "call sites pass literals, so a
  typo is a KeyError at test time, not a runtime state". Before the
  amendment a wrong kind skipped the shape check and said nothing.

- **2026-10-04 — the parse guard takes `ValueError` and
  `RecursionError` (Minor 1).** `except json.JSONDecodeError` becomes
  `except (ValueError, RecursionError)`, worded `<shown> is not valid
  JSON: <err>` like every other parse failure. `JSONDecodeError` is a
  `ValueError` subclass, so the old arm is inside the new one. An
  integer literal past the interpreter's digit limit and nesting past
  its recursion limit now return that problem string where they raised
  (*Proof 4*).
  The trade-off: a `RecursionError` names no cause. Raised by the
  parse, it means the document's nesting used up what was left of the
  interpreter's limit, and how much was left depends on how deep the
  caller already was. So a document can be blamed for how far down its
  caller is. Measured (*Proof 6*): plain Python recursion never does
  this, and a caller 300 levels down through C calls does, for a
  document nested within about ten percent of the limit.
  Decided: catch it.
  - No caller recurses. Across the whole suite the deepest a caller sat
    when it reached `read_file` was 21 frames, against a limit of 1000.
  - The misreport measured needs a document nested more than 9,000
    levels deep. The JSON files the adopters read nest two or three.
  - The problem string carries the interpreter's own words, and they
    name recursion, so the cause is still on the page.
  - Every adopter treats a problem as a failure, so a wrong cause never
    turns a failure into a pass. (`check_plugin_skills` discards the
    problem, as it discards every problem, because `check_manifest`
    reports the same file.)
  - The alternative is to catch `ValueError` alone and keep a document
    that makes `read_file` raise, which is the false claim Minor 1
    found. Telling the two causes apart by the message would hang the
    design on interpreter wording that already differs between 3.12
    and 3.14.

  A limit of the claim, stated and not probed: a file too large for
  memory raises `MemoryError`, which is left to propagate. That is the
  process running out, not a fact about the file that a problem string
  could be trusted to carry.
  Superseded in the body: the failure table's "not JSON, or an empty
  file" row now also covers these two documents.

- **2026-10-04 — two JSON readers keep `cannot read` (Minor 4).**
  ADR-0075 decision 2 states the wording rule for bytes that are not
  UTF-8 as if every JSON reader followed it. Two do not, and the record
  now says so in one sentence: `cli.read_event` and
  `dashboard.repo_set` keep `cannot read` for such bytes, under
  decision 4, because neither has a raising cell and so both stay as
  they are. Checked in the matrix recorded for *Proof 2*: neither has
  a raising cell, and for those bytes they read `cannot read
  GITHUB_EVENT_PATH <path>: ...` and `dashboard: cannot read <path>:
  ...`. No code changes.

- **2026-10-04 — ADR-0075 is corrected in place.** It is provisional,
  written by this run and unmerged, so it is corrected, not superseded.
  Its title, status and index row do not change. Besides the Minor 4
  sentence:
  - Decision 1 names three kinds, says an unknown kind is a
    `ValueError` at the call, and says what the parse guard takes, with
    the trade-off in two sentences.
  - Decision 5's first bullet explained four hand-written readers by
    what asking for `object` would do. It now gives the reason that
    holds with three kinds: each judges the parsed document's top level
    its own way, and `read_file` has no kind that parses without its
    own shape wording. Its closing sentence gains the scope fence
    below.
  - *Alternatives that lost* gains the fourth kind, with the
    measurement that removed it, so a later review does not suggest it
    again. It names five readers where the review counted four,
    because the first pass's counterfactual also changed
    `sweeps.load_payload`'s `null` cell, from no problem to `sweeps:
    payload <path> is null`.

- **2026-10-04 — eight comments say why (Minor 5).** ADR-0075's last
  consequence says "a reader that cannot use it says why".
  `label_sync.load_labels` already does, at `label_sync.py:60`, and
  that comment stays as it is: its reason, a shape wording of its own
  that covers `null`, holds with three kinds. Each of the other eight
  hand-written readers gets one comment in the same style, written out
  under *The eight comments*. They change no behaviour.

- **2026-10-04 — scope fence.** Stated so the run does not widen.
  - The wider parse guard is `read_file`'s alone. The hand-written
    JSON readers are not given it: `label_sync.load_labels`, detector
    K, `lint.check_output_evals`' `problems_for`, `cli.read_execution`,
    `sweeps.load_payload`, and the untouched `cli.read_event` and
    `dashboard.repo_set`. On the two documents each raises the same
    exception as at `661ffc7` (*Proof 3*).
  - The replay found a group the brief does not name.
    `cost_ledger.load` (and `read`, thin over it) and
    `dashboard._corrections` adopted with `str` and then parse each
    line themselves, catching `JSONDecodeError` alone. They are inside
    the same fence and raise as at `661ffc7`. So a ledger line holding
    such an integer still makes the monthly cap check raise where it
    promises to fail closed (*Proof 3*). That is Minor 1's class one
    step further in. It is a seed for the retro, not this run's work.
  - Minor 3 stays deferred, as `review.md` decided. Minor 6 is one
    test-only line and needs no design. `docs/backlog.md` is not
    touched.
  - No pinned problem string changes, and there is still no fourth
    parameter.

- **2026-10-04 — scratch proof.** Each claim above was run in scratch
  on Python 3.14.6 and Python 3.12.13, and the output is quoted under
  *Scratch proof* below. In short:
  1. No caller passes `object`: eleven callers, all `str`, `dict` or
     `list`.
  2. The 144-cell matrix still ends `cells 144 | identical 123 | fixed
     16 | wording changed 2 | still raising 3 | newly raising 0` and is
     byte-identical to `after-implement.json`. The six outside sites do
     not raise.
  3. Outside the matrix, the only cells that move are the two Minor 1
     documents for the eight readers that adopted with a JSON kind.
     They go from a traceback to `... is not valid JSON: ...` (to
     `[]` for `check_plugin_skills`, which discards the problem). Ten
     other readers raise the same exception as at `661ffc7`.
  4. The amended function raises `ValueError` for an unknown kind
     before touching the file, returns a problem string for both
     documents, and leaves the interpreter usable.
  5. The existing suite fails in 14 rows, all of them `object` rows of
     `TestReadFile`. `lint.py`, `gates.py` and the selftest are clean.
  6. The trade-off of catching `RecursionError` is measured.
  7. With three kinds, adopting the four hand-written JSON readers
     breaks nine pinned tests.

### Final text (2026-10-04)

Implement copies this verbatim. It replaces the final text in the body.
Its longest line is 72 columns.

```python
def read_file(path, shown, kind):
    """(value, problem) for one local file — the guarded read every
    reader of a repo file shares (ADR-0075). kind is what the caller
    needs back: str (the text), dict (a JSON object) or list (a JSON
    array). Any other kind is a ValueError at the call, before the file
    is touched: a slip in the caller, never a failure of the file.

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

    Never raises for a local-file failure: the existence check sits
    inside the guard because Path.is_file raises PermissionError under
    an unsearchable parent before Python 3.14, and the parse guard takes
    ValueError and RecursionError, not JSONDecodeError alone, because an
    integer literal past the interpreter's digit limit and nesting past
    its recursion limit raise those. A reader whose shape wording or
    null wording is its own does not adopt: it gets its missing arm by
    hand (ADR-0075 decision 5)."""
    if kind not in (str, dict, list):
        raise ValueError(
            f"read_file kind must be str, dict or list, not {kind!r}")
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
    except (ValueError, RecursionError) as err:
        return None, f"{shown} is not valid JSON: {err}"
    if kind is dict and not isinstance(value, dict):
        return None, f"{shown} is not a JSON object"
    if kind is list and not isinstance(value, list):
        return None, f"{shown} is not a JSON array"
    return value, None
```

`cli.py`'s module docstring sentence about `read_file` stays as it is:
"unreadable, undecodable, unparsable, or the wrong top-level shape" is
still the whole failure vocabulary. `CLAUDE.md`'s seam line stays too.

### The eight comments

Each goes directly above the `try:` of its reader's read. Lines are
HEAD's, `c1b3cd5`. Placing an earlier comment in the same file moves
the later line, and `cli.py:344` becomes 348 once `read_file` takes its
amended text.

`gates.py:1457`, detector K (`check_standards_drift`):

```python
    # Hand-written rather than cli.read_file (ADR-0075): the shape
    # wording below is K's own and covers null. Bytes that are not
    # UTF-8 join the parse failure's wording, by that record's rule.
```

`lint.py:771`, `problems_for` inside `check_output_evals`:

```python
        # Hand-written rather than cli.read_file (ADR-0075): the shape
        # check is validate_output's, reported beside the stem line, and
        # a directory the glob matched is "cannot read", not absent.
```

`lint.py:874`, `check_backlog`:

```python
    # Hand-written rather than cli.read_file (ADR-0075): this checker's
    # phrase is "is unreadable", where read_file says "cannot read".
```

`cli.py:344`, `read_execution`:

```python
    # Hand-written rather than read_file (ADR-0075): an absent file is
    # an OSError message here, where read_file gives (None, None), and
    # the log may be an array or one object, so neither JSON kind fits.
```

`sweeps.py:470`, `load_payload`:

```python
    # Hand-written rather than cli.read_file (ADR-0075): an absent file
    # is an OSError message here, where read_file gives (None, None),
    # and this read also takes stdin.
```

`dashboard.py:509`, `respond` (inside `if url.path == "/":`):

```python
        # Hand-written rather than cli.read_file (ADR-0075): an absent
        # page is an OSError message here, where read_file gives
        # (None, None).
```

`dashboard.py:565`, `respond_post`:

```python
    # Hand-written rather than cli.read_file (ADR-0075): an absent
    # backlog is an OSError message here, where read_file gives
    # (None, None).
```

`validator.py:323`, `run_review`:

```python
    # Hand-written rather than cli.read_file (ADR-0075): an absent
    # findings file is an OSError message here, where read_file gives
    # (None, None).
```

Each was read against its code:

- K's `must be a JSON array` check takes `null`, and its
  `UnicodeDecodeError` arm words `is not valid JSON`.
- `problems_for` returns the stem line beside `validate_output`'s
  problems, and words any `OSError` as `cannot read`.
- `check_backlog` says `is unreadable`.
- `read_execution` words `OSError` as `cannot read execution file ...`
  and wraps a log that is not a list as one entry.
- `load_payload` reads stdin when the path is `None` or `-`.
- `respond`, `respond_post` and `run_review` word `OSError` as `cannot
  read ...: {err}`.

For `problems_for` the comment does not say "its `null` wording is its
own", because that is no longer its reason: under `dict` its `null`
cell reads the same words (*Proof 7*).

`gates.py`, `cli.py` and `validator.py` are mirrored, so the payload
rule in the body applies to the commit that places these. `lint.py`,
`sweeps.py` and `dashboard.py` are not mirrored. Placed in a scratch
copy with the manifest regenerated (`place_comments.py`, which prints
each `try:` line as it finds it, after the comments above it are in):

```
gates.py:1457  check_standards_drift (detector K)  (`try:` line; comment of 3 lines, widest 68)
lint.py:771  check_output_evals.problems_for  (`try:` line; comment of 3 lines, widest 72)
lint.py:877  check_backlog  (`try:` line; comment of 2 lines, widest 71)
cli.py:348  read_execution  (`try:` line; comment of 3 lines, widest 71)
sweeps.py:470  load_payload  (`try:` line; comment of 3 lines, widest 71)
dashboard.py:509  respond  (`try:` line; comment of 3 lines, widest 70)
dashboard.py:568  respond_post  (`try:` line; comment of 3 lines, widest 66)
validator.py:323  run_review  (`try:` line; comment of 3 lines, widest 69)
3.14: Ran 1874 tests | FAILED (errors=14) | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
3.12: Ran 1874 tests | FAILED (errors=14) | lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
```

The 14 errors are the `object` rows of the next section and nothing
else.

### Tests: the rows that go and the rows that come

For Decompose. This says what the tests are, not their order.

**Rows that go.** The existing suite, unedited, against the amended
function:

```
3.14 HEAD:    Ran 1874 tests | OK
3.14 amended: Ran 1874 tests | FAILED (errors=14)
3.12 HEAD:    Ran 1874 tests | OK
3.12 amended: Ran 1874 tests | FAILED (errors=14)
```

The 14 errors are the same 14 on both Pythons. Each is the
`kind='object'` sub-test of one `test_cli.TestReadFile` method, and each
is `ValueError: read_file kind must be str, dict or list, not <class 'object'>`:

```
ERROR: test_a_directory_in_its_place_counts_as_absent (test_cli.TestReadFile.test_a_directory_in_its_place_counts_as_absent) (kind='object')
ERROR: test_a_json_array (test_cli.TestReadFile.test_a_json_array) (kind='object')
ERROR: test_a_json_null (test_cli.TestReadFile.test_a_json_null) (kind='object')
ERROR: test_a_json_number (test_cli.TestReadFile.test_a_json_number) (kind='object')
ERROR: test_a_json_object (test_cli.TestReadFile.test_a_json_object) (kind='object')
ERROR: test_a_json_string (test_cli.TestReadFile.test_a_json_string) (kind='object')
ERROR: test_an_absent_file_is_none_none_for_every_kind (test_cli.TestReadFile.test_an_absent_file_is_none_none_for_every_kind) (kind='object')
ERROR: test_an_empty_file (test_cli.TestReadFile.test_an_empty_file) (kind='object')
ERROR: test_an_unreadable_file_is_cannot_read_for_every_kind (test_cli.TestReadFile.test_an_unreadable_file_is_cannot_read_for_every_kind) (kind='object')
ERROR: test_an_unsearchable_parent_never_raises (test_cli.TestReadFile.test_an_unsearchable_parent_never_raises) (kind='object')
ERROR: test_bytes_that_are_not_utf8 (test_cli.TestReadFile.test_bytes_that_are_not_utf8) (kind='object')
ERROR: test_json_false (test_cli.TestReadFile.test_json_false) (kind='object')
ERROR: test_json_true (test_cli.TestReadFile.test_json_true) (kind='object')
ERROR: test_text_that_is_not_json (test_cli.TestReadFile.test_text_that_is_not_json) (kind='object')
```

No method dies whole: each keeps its `str`, `dict` and `list` rows.
What goes with the kind:

- `object` in `TestReadFile.KINDS`;
- the `object:` entry of the ten `assert_pairs` mappings (the other
  four methods loop over `KINDS`);
- `test_a_json_null`'s docstring, which is about the `object` kind
  alone.

The two methods with no `object` row pass untouched:
`test_every_non_object_top_level_is_one_problem_under_dict` and
`test_shown_is_echoed_verbatim`. Nothing outside `TestReadFile` fails.

**Rows that come,** all in `TestReadFile`. Each fails today for the
reason given, measured at HEAD on both Pythons (`probe_amended.py
head`).

- **An unknown kind raises.** For `object`, `"dict"` and `int`:
  `ValueError` with the exact message, with the file present, with it
  absent, and with a path that raises if it is touched. Today nothing
  raises: a value or `(None, None)` comes back.
- **A 5,000-digit integer literal.** `dict` and `list`: the exact pair
  `(None, "docs/thing.json is not valid JSON: Exceeds the limit (4300
  digits) for integer string conversion: value has 5000 digits; use
  sys.set_int_max_str_digits() to increase the limit")`. `str`: the
  text. The problem is the same on both Pythons, so it is pinned
  exactly, like `NOT_JSON` and `EMPTY`. It embeds the interpreter's
  default digit limit. Nothing in the suite or the workflows sets
  `PYTHONINTMAXSTRDIGITS`. Today: `ValueError`, a traceback.
- **Arrays nested past the limit.** `dict` and `list`: `value is None`,
  and the problem starts with `docs/thing.json is not valid JSON: `.
  Only the prefix is pinned, because the rest is the interpreter's and
  differs by version (*Proof 4*). `str`: the text. A further read in
  the same test returns its value, which pins that the interpreter is
  usable afterwards. Today: `RecursionError`, a traceback.
  The document is 1,000,000 balanced arrays, not 200,000. On 3.14 the
  limit is the C stack's size, so the first nesting that raises depends
  on the machine. Here, with what the row costs:

  ```
  python 3.14.6 | first depth that raises RecursionError: 116,213
  python 3.12.13 | first depth that raises RecursionError: 9,998
  python 3.14.6
    depth   200,000:    6.7 ms, value is None: True, problem starts 'docs/thing.json is not valid JSON: ': True
    depth 1,000,000:    5.8 ms, value is None: True, problem starts 'docs/thing.json is not valid JSON: ': True
  python 3.12.13
    depth   200,000:    0.7 ms, value is None: True, problem starts 'docs/thing.json is not valid JSON: ': True
    depth 1,000,000:    1.0 ms, value is None: True, problem starts 'docs/thing.json is not valid JSON: ': True
  ```

  200,000 clears the 3.14 figure by less than twice, and 1,000,000 by
  more than eight times, for a few milliseconds.

No reader-level test is added for the two documents. An adopter adds
nothing to them but its label, which its existing tests pin.

### Scratch proof

Everything quoted in this section and the two before it was run for
this amendment, on Python 3.14.6 (`python3`) and Python 3.12.13
(`python3.12`), in `git archive` copies under the session scratchpad
(`ogfr/amend/`), never in the worktree. `base/` is `661ffc7` and
`head/` is HEAD `c1b3cd5`. `amended/` is HEAD with the final text
patched into `cli.py` and the payload brought level by
`factory_init.py update-manifest`. `placed/` is `amended/` plus the
eight comments. `run_all.sh` rebuilds them from the archives and
regenerates every output quoted.

**Proof 1: no caller passes `object`.** `callers.py head`, an AST sweep
for every call of `read_file`. Eleven in the root modules, each passing
its kind as a bare name:

```
cost_ledger.py:245  load  kind=str (Name)
dashboard.py:318  _corrections  kind=str (Name)
dashboard.py:459  _backlog  kind=str (Name)
eval_schema.py:182  load_case_set  kind=dict (Name)
factory_config.py:74  load  kind=dict (Name)
gates.py:843  check_scaffold_sync  kind=dict (Name)
gates.py:999  check_config_shape  kind=dict (Name)
lint.py:27  check_manifest  kind=dict (Name)
lint.py:67  check_plugin_skills  kind=dict (Name)
lint.py:81  check_pi_package  kind=dict (Name)
standards_index.py:248  foreign_entries  kind=list (Name)
```

The five calls in the payload copies pass the same kinds. The only
other calls are `TestReadFile`'s own.

**Proof 2: the 144-cell matrix and the six outside sites do not
move.** `matrix.py` on `amended/`, then `diff_matrix.py`:

```
3.14 against baseline-661ffc7.json:
cells 144 | identical 123 | fixed 16 | wording changed 2 | still raising 3 | newly raising 0
3.14 against after-implement.json:
cells 144 | identical 141 | fixed 0 | wording changed 0 | still raising 3 | newly raising 0
cmp: byte-identical to after-implement.json
3.12 against baseline-661ffc7.json:
cells 144 | identical 123 | fixed 16 | wording changed 2 | still raising 3 | newly raising 0
3.12 against after-implement.json:
cells 144 | identical 141 | fixed 0 | wording changed 0 | still raising 3 | newly raising 0
cmp: byte-identical to after-implement.json
```

The two changed cells are the two decided pins, and the three still
raising are `trigger_eval.print_metrics`'s. Both recordings are
byte-identical to `after-implement.json`: no matrix cell moves.

`probe_six.py` on `amended/`: no line of either Python's output holds
`RAISES`, the 3.12 output is identical to the 3.14 output, and both are
identical to `six.out` as recorded after Implement. Its first probe:

```
dashboard._corrections / not utf-8
    ({}, ["dashboard: cannot read docs/factory/corrections.jsonl: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte"])
```

**Proof 3: the cells outside the matrix.** The review's replay
(`review/extra2.py`, unedited: 17 readers, 12 conditions, 204 cells) at
`661ffc7`, HEAD and amended. The 3.14 recordings of `661ffc7` and HEAD
are byte-identical to the review's `x-base.json` and `x-head.json`.

```
3.14  661ffc7 to HEAD:  cells 204 | identical 181 | fixed 8 | wording changed 0 | still raising 15 | newly raising 0
3.14  HEAD to amended:  cells 204 | identical 189 | fixed 8 | wording changed 0 | still raising 7 | newly raising 0
3.12  661ffc7 to HEAD:  cells 204 | identical 166 | fixed 8 | wording changed 0 | still raising 30 | newly raising 0
3.12  HEAD to amended:  cells 204 | identical 174 | fixed 16 | wording changed 0 | still raising 14 | newly raising 0
```

No wording changes and nothing newly raises, on either Python. On 3.14
eight cells move, all of them the 5,000-digit integer (`bigint`), and
seven keep raising:

```
  FIXED    factory_config.load / bigint
             now: (None, ['config: .github/factory.json is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit'])
  STILL RAISES  label_sync.load_labels / bigint: RAISES ValueError
  FIXED    standards_index.foreign_entries / bigint
             now: ([], ['docs/standards.json is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit'])
  STILL RAISES  gates K check_standards_drift / bigint: RAISES ValueError
  FIXED    gates E check_scaffold_sync / bigint
             now: ['E: factory/manifest.json is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit']
  FIXED    gates F check_config_shape / bigint
             now: ['F: factory/templates/factory.json is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit']
  FIXED    lint.check_manifest / bigint
             now: ['plugin.json is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit']
  FIXED    lint.check_plugin_skills / bigint
             now: []
  FIXED    lint.check_pi_package / bigint
             now: ['package.json is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit']
  STILL RAISES  lint.check_output_evals / bigint: RAISES ValueError
  FIXED    eval_schema.load_case_set / bigint
             now: ([], ['evals/routing.json is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit'])
  STILL RAISES  cli.read_execution / bigint: RAISES ValueError
  STILL RAISES  sweeps.load_payload / bigint: RAISES ValueError
  STILL RAISES  cost_ledger.load (label G) / bigint: RAISES ValueError
  STILL RAISES  dashboard._corrections / bigint: RAISES ValueError
```

On 3.12 sixteen move and fourteen keep raising: the same readers, on
`bigint` and on the review's `deep` cell. That document is 100,000
unclosed brackets. 3.14 parses it as far as the missing value, which is
a `JSONDecodeError` and already a string. 3.12 refuses it with
`RecursionError`. The review recorded on 3.14 only, so its "15 cells
still raising at HEAD" is 30 on 3.12.

`extra3.py` puts the two documents through all 20 readers: the 17
above and the three the 204 leave out (`cost_ledger.read`,
`cli.read_event`, `dashboard.repo_set`). Its conditions are the
integer, the review's 100,000 unclosed brackets, and 200,000 balanced
arrays, which raises on both Pythons.

```
3.14  661ffc7 to HEAD:  cells 60 | identical 24 | fixed 0 | wording changed 0 | still raising 36 | newly raising 0
3.14  HEAD to amended:  cells 60 | identical 24 | fixed 16 | wording changed 0 | still raising 20 | newly raising 0
3.12  661ffc7 to HEAD:  cells 60 | identical 6 | fixed 0 | wording changed 0 | still raising 54 | newly raising 0
3.12  HEAD to amended:  cells 60 | identical 6 | fixed 24 | wording changed 0 | still raising 30 | newly raising 0
```

Reader by reader, the same on both Pythons:

| group | readers | at `661ffc7` and HEAD | amended |
|---|---|---|---|
| adopted with a JSON kind | `factory_config.load`, detector E, detector F, `lint.check_manifest`, `lint.check_pi_package`, `eval_schema.load_case_set` (all `dict`), `standards_index.foreign_entries` (`list`) | raises `ValueError` or `RecursionError` | the reader's label, then `<shown> is not valid JSON: <err>` |
| adopted with `dict`, problem discarded | `lint.check_plugin_skills` | raises the same | `[]` (`check_manifest` reports the file) |
| hand-written JSON readers | `label_sync.load_labels`, detector K, `lint.check_output_evals`, `cli.read_execution`, `sweeps.load_payload`, `cli.read_event`, `dashboard.repo_set` | raises | raises the same exception |
| adopted with `str`, each line parsed by the reader | `cost_ledger.load`, `cost_ledger.read`, `dashboard._corrections` | raises | raises the same exception |
| text readers, no parse | `lint.check_backlog`, `dashboard._backlog` | no problem | no problem |

The counts agree with the table. On 3.14 the eight adopters move on two
documents (16 cells) and ten readers keep raising on two (20). On 3.12
all three documents raise, so it is 24 and 30. No other cell moves.

The fourth group reaches the monthly cap check. `guard_probe.py`, on a
ledger whose one line is the 5,000-digit integer, reads the same at
`661ffc7`, HEAD and amended, on both Pythons:

```
cost_ledger.read: RAISES ValueError: Exceeds the limit (4300 digits) for integer string conversio...
cost_report.guard: RAISES ValueError: Exceeds the limit (4300 digits) for integer string conversio...
```

**Proof 4: the amended function, probed directly.** `probe_amended.py
amended`. An unknown kind, the same output on both Pythons:

```
kind=object, file present
    -> RAISES ValueError: read_file kind must be str, dict or list, not <class 'object'>
kind=object, file absent
    -> RAISES ValueError: read_file kind must be str, dict or list, not <class 'object'>
kind="dict" (a string), file present
    -> RAISES ValueError: read_file kind must be str, dict or list, not 'dict'
kind="dict" (a string), file absent
    -> RAISES ValueError: read_file kind must be str, dict or list, not 'dict'
kind=int, file present
    -> RAISES ValueError: read_file kind must be str, dict or list, not <class 'int'>
kind=int, file absent
    -> RAISES ValueError: read_file kind must be str, dict or list, not <class 'int'>
kind=object, a path that raises if touched
    -> RAISES ValueError: read_file kind must be str, dict or list, not <class 'object'>
kind=dict, the same path (control: a known kind does touch it)
    -> RAISES AssertionError: the path was touched
```

The last pair proves "before the file is touched": a path object that
raises when asked for itself raises nothing under an unknown kind, and
does raise under a known one. At HEAD (`probe_amended.py head`) the
same three hand back the document and say nothing, `object` because it
was a kind and the other two because nothing checked:

```
kind=object, file present
    -> ({'a': 1}, None)
kind="dict" (a string), file present
    -> ({'a': 1}, None)
kind=int, file present
    -> ({'a': 1}, None)
```

The 5,000-digit integer, the same output on both Pythons:

```
kind=dict
    -> (None, 'docs/thing.json is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit')
kind=list
    -> (None, 'docs/thing.json is not valid JSON: Exceeds the limit (4300 digits) for integer string conversion: value has 5000 digits; use sys.set_int_max_str_digits() to increase the limit')
kind=str
    -> text of 5000 chars, problem None
```

1,000,000 balanced arrays. The 200,000 rows read the same, line for
line, on each Python:

```
Python 3.14.6
depth 1,000,000, kind=dict
    -> (None, 'docs/thing.json is not valid JSON: Stack overflow (used 16352 kB) while decoding a JSON array from a unicode string')
depth 1,000,000, kind=list
    -> (None, 'docs/thing.json is not valid JSON: Stack overflow (used 16352 kB) while decoding a JSON array from a unicode string')
depth 1,000,000, kind=str
    -> text of 2,000,000 chars, problem None
    and the next read still works
    -> ({'a': 1}, None)
Python 3.12.13
depth 1,000,000, kind=dict
    -> (None, 'docs/thing.json is not valid JSON: maximum recursion depth exceeded while decoding a JSON array from a unicode string')
depth 1,000,000, kind=list
    -> (None, 'docs/thing.json is not valid JSON: maximum recursion depth exceeded while decoding a JSON array from a unicode string')
depth 1,000,000, kind=str
    -> text of 2,000,000 chars, problem None
    and the next read still works
    -> ({'a': 1}, None)
```

So the two problem strings to pin are:

- the integer, exactly, on both Pythons: `docs/thing.json is not valid
  JSON: Exceeds the limit (4300 digits) for integer string conversion:
  value has 5000 digits; use sys.set_int_max_str_digits() to increase
  the limit`;
- the nesting, by its prefix `docs/thing.json is not valid JSON: `. The
  rest is `maximum recursion depth exceeded while decoding a JSON array
  from a unicode string` on 3.12 and `Stack overflow (used 16352 kB)
  while decoding a JSON array from a unicode string` on 3.14, where the
  figure is this machine's stack.

The `str` kind does not parse, so both documents come back as text.

**Proof 5: the suite and the battery.** The suite's result is under
*Tests* above: 14 errors, all `object` rows, on both Pythons. The other
three battery commands on `amended/`:

```
3.14: lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
3.12: lint: 0 problem(s) across 25 skills | gates: 0 problem(s) | selftest: ok
```

**Proof 6: the trade-off, measured.** `deep_caller.py` reads a valid,
shallow document from 900 to 1000 plain Python frames down. The three
result lines are identical on 3.12:

```
python 3.14.6 | recursion limit 1000
  dive depth 900..988 (89 depths): value
  dive depth 989..1000 (12 depths): raises RecursionError (maximum recursion depth exceeded)
  after it all: ({'a': 1}, None)
```

A valid document is never turned into a problem by plain Python
recursion. From 989 frames down the call raises `RecursionError`,
uncaught: it is
raised before the parse, by the path and the read, which need more
frames than the parse and sit outside its guard. So the function has
not become a way to swallow a caller's own overflow.

`deep_caller2.py` finds the shallowest balanced nesting that
`read_file` reports as a problem, for three callers:

```
3.14.6
  called from the top: first nesting reported as a problem: 116,213
  900 plain Python frames down: first nesting reported as a problem: 116,213
  300 frames down, each through C (sorted's key): first nesting reported as a problem: 102,413
3.12.13
  called from the top: first nesting reported as a problem: 9,998
  900 plain Python frames down: first nesting reported as a problem: 9,998
  300 frames down, each through C (sorted's key): first nesting reported as a problem: 9,098
```

Plain Python recursion does not move the line. Recursion that passes
through C does: a document nested between the two figures parses from
the top and is reported as not valid JSON from that caller. That is the
misreport, and it is real.

How far down callers are, over the whole suite (`depth_run.py`, a
wrapper put in before any reader imports the function):

```
python 3.14.6 | recursion limit 1000
tests run 1874, errors 14, failures 0
read_file calls seen through the wrapper: 634
deepest caller: 21 Python frames from the interpreter's entry to the caller
```

Five of the 21 frames are the tool's own, from `budget_guard.main` down
to `cost_ledger.load`. The rest are the test and unittest.

How deep the adopters' JSON files nest (`nesting.py head`):

```
factory/templates/factory.json: nested 2 deep
factory/manifest.json: nested 2 deep
.claude-plugin/plugin.json: nested 2 deep
package.json: nested 3 deep
docs/standards.json: nested 2 deep
evals/routing.json: nested 3 deep
```

**Proof 7: the hand-written readers with three kinds.** The first pass
gave each of them two reasons, one about `object` and one about the
nearest shape kind. The first goes with the kind. The second was argued
from pins and is measured here. `counterfactual3.py` makes
`label_sync.load_labels` and detector K adopt with `list`,
`problems_for` with `dict` and `cli.read_execution` with `list`, on a
copy of `amended/` (3.14):

```
144-cell matrix, amended against the counterfactual:
cells 144 | identical 134 | fixed 0 | wording changed 7 | still raising 3 | newly raising 0
the review's 204 cells, the same way:
cells 204 | identical 175 | fixed 4 | wording changed 22 | still raising 3 | newly raising 0
the suite on the counterfactual copy:
Ran 1874 tests in 21.062s
FAILED (failures=11, errors=14)
```

The 14 errors are the `object` rows. The 11 failures are nine pinned
tests, at least one for each of the four readers:

- `label_sync` with `list`:
  `test_label_sync.TestLoadLabels.test_a_string_and_a_null_are_flagged_the_same_way`
  (both rows), `...test_non_array_and_empty_array_are_flagged`, and
  `test_gates.TestLabelWiring.test_an_unreadable_taxonomy_is_reported_not_a_traceback`.
  `L: .github/labels.json must be a non-empty JSON array of label
  entries` becomes `L: .github/labels.json is not a JSON array`.
- K with `list`:
  `test_gates.TestStandardsDrift.test_a_non_array_committed_index_is_a_problem`
  and `...test_a_string_or_null_committed_index_is_the_same_problem`
  (both rows). `K: docs/standards.json must be a JSON array` becomes
  `K: docs/standards.json is not a JSON array`.
- `problems_for` with `dict`:
  `test_lint.TestOutputEvals.test_a_directory_named_like_a_record_file_is_a_problem`.
  A directory the glob matched goes from `cannot read
  evals/output/prd.json: [Errno 21] Is a directory: ...` to nothing,
  because `read_file` calls it absent. Its `null` cell does not move:
  under `dict` it reads the same words. One cell that no test pins
  also moves, the stem line beside the shape problem (`stem_probe.py`):

  ```
  amended:
    null  -> ['evals/output/not-a-skill.json stem is not a skill slug', 'evals/output/not-a-skill.json is not a JSON object']
  counterfactual:
    null  -> ['evals/output/not-a-skill.json is not a JSON object']
  ```
- `cli.read_execution` with `list`:
  `test_cli.TestReadExecution.test_a_null_log_has_no_result_entry`,
  `...test_an_unreadable_path_is_an_error` and
  `...test_a_directory_in_its_place_is_an_error`. A `null` or a single
  object goes from `has no result entry` to `is not a JSON array`, and
  an absent file loses its `OSError` text.

The four `fixed` cells in the 204 are those readers' 5,000-digit
integer cell, which adoption would bring under the wider parse guard.
That does not outweigh the pins.
