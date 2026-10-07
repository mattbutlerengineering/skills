# The guarded local-file read joins the cli seam

- Status: provisional
- Date: 2026-10-04

Amends no record. It adds one entry point to the cli seam (ADR-0037,
ADR-0042, ADR-0051) and leaves every decision there standing:
caller-side prefixing (ADR-0051), the dual-home read order (ADR-0048),
`cost_ledger.load` as the labelled read (ADR-0049), and
`protocol.read_frontmatter`'s own move (ADR-0065).

## Context

The rule "read a local file and turn every way that can fail into a
problem string" had no owner. Each reader typed its own guard. An AST
sweep at `661ffc7` found 67 file-read sites in the root modules: 28
guarded, in five different exception spellings, and 39 unguarded. What
each guard forgot to catch is a traceback where the problem-string
contract promises a string. Driven through their public interfaces
against eight kinds of bad file, 18 readers gave 144 cells, and 19 of
them raised. Six more guarded sites outside that matrix raised on the
one kind of file their guard did not name. Among the 19: the monthly
cap check (`cost_report.guard`) and `budget_guard.record` crashed on a
ledger that is not UTF-8, although both promise to fail closed.

Two earlier reviews declined a shared seam for this: PR #410's review,
and item 3 of `docs/fixes/a-utf8-fix-that-stopped-at-the-mirror/review.md`.
They argued that the differing exception spellings were "principled
rather than accidental", and that a new seam needs a decision record.
That reading was fair on the evidence they had, which was a count of
spellings. The behaviour matrix is the evidence they did not have. It
shows that the spellings did not differ by principle. Each one left a
different failure unguarded, and each left exactly one. Six earlier
maintenance runs (`json-that-is-not-utf8`,
`a-utf8-fix-that-stopped-at-the-mirror`,
`a-config-that-is-not-an-object`, `a-manifest-that-is-not-an-object`,
`a-config-the-gate-cannot-read`,
`eval-validators-raise-on-non-object-files`) each repaired the instances
in front of them, and the matrix still found instances none of them
reached. That meets CLAUDE.md's bar for shared code: multiple real
callers, and observed divergence between their copies.

## Decision

1. **One function, `cli.read_file(path, shown, kind)`, beside
   `read_event`.** It returns `(value, problem)`. It returns `(None,
   None)` when no regular file is at `path`, because absence is the
   caller's to interpret, as it already is for `read_event`. Otherwise
   exactly one of the two is `None`. `kind` is required and is one of
   `str`, `dict` or `list`. Any other `kind` is a `ValueError` at the
   call, before the file is touched: a programming error, not a file
   failure. The problem is unlabelled; the caller prefixes its own
   label (ADR-0051). The function never raises for a local-file
   failure. Its existence check sits inside the guard, because
   `Path.is_file` raises `PermissionError` under an unsearchable parent
   on Python 3.12. Its parse guard takes `ValueError` and
   `RecursionError`, not `JSONDecodeError` alone, because an integer
   literal past the interpreter's digit limit and nesting past its
   recursion limit raise those. Both are worded as a parse failure.
   A `RecursionError` names no cause, so a document that tips a caller
   already deep in recursion over the limit is reported as the
   document's defect. No caller recurses, and this record accepts
   that. There are three parameters and no fourth. There is no new
   module, no new `MIRRORS` entry, and no port: the dependency is the
   local filesystem in-process, and one adapter does not make a seam.
2. **The wording rule for bytes that are not UTF-8.** For the JSON
   kinds the problem reads `<shown> is not valid JSON: <err>`; for `str`
   it reads `cannot read <shown>: <err>`. JSON exchanged between systems
   must be UTF-8 (RFC 8259 §8.1), so for a JSON reader the bytes are a
   defect in the document. Seven JSON readers already worded it this
   way. A text reader has no grammar to blame, so the failure is a read
   failure. That is `cost_ledger.load`'s phrasing, which the rule keeps.
   `cli.read_event` and `dashboard.repo_set` keep `cannot read` for
   bytes that are not UTF-8, under 4: neither has a raising cell, so
   both stay as they are.
3. **Two deliberate reversals.** `json-that-is-not-utf8` (2026-08-30)
   chose "cannot read" for `factory_config.load` and
   `label_sync.load_labels`, following `cost_ledger.load`'s
   decode-is-a-read-failure split. This record reverses those two, and
   only those two, to the rule above. Those two are the files every
   tool reads, so their wording is the one the next reader copies. Both
   pins change: `tests/test_factory_config.py` and
   `tests/test_label_sync.py`. No other pinned problem string changes.
4. **The adoption rule.** A guarded read with a cell that raises today
   is in scope. It adopts `read_file` when adoption changes no wording
   in any recorded cell. Otherwise it gets the missing arm by hand and
   keeps its wording. `factory_config.load` adopts although it has no
   raising cell (the reason is in 3). A read with no raising cell stays
   as it is.
5. **Readers that stay hand-written,** each because adoption would
   change a cell's wording:
   - `label_sync.load_labels`, detector K, `lint.check_output_evals`
     and `cli.read_execution` each judge the parsed document's top
     level, a JSON `null` included, in their own way. `load_labels`
     and K word a wrong top level in their own phrase.
     `check_output_evals` reports it beside the file's stem, and words
     a directory under a globbed name `cannot read`. `read_execution`
     takes an array or a single object. `read_file` has no kind that
     parses without its own shape wording, so each keeps its own
     parse.
   - `cli.read_execution`, `sweeps.load_payload`, `dashboard.respond`,
     `dashboard.respond_post` and `validator.run_review` word an absent
     file as an `OSError` message. The absence contract cannot
     reproduce that.
   - `lint.check_backlog`'s phrase is "is unreadable".

   Each of these gets its missing exception arm, worded by the rule in
   2. None gets the wider parse guard of 1: on those two documents the
   JSON readers among them raise as they did before this record.

   Two adopters, `cost_ledger.load` and `dashboard._corrections`, read
   with `str` and parse each line themselves, so the guard of 1 never
   sees their lines. `cost_ledger.parse`, which `cost_ledger.load` and
   `read` are built on, takes the same wider parse guard as
   `read_file`, with the same trade-off, because the monthly cap check
   must fail closed: a traceback there is a pause that does not
   happen. `dashboard._corrections` keeps its `JSONDecodeError` arm, as
   the hand-written JSON readers do: on those two documents it raises
   as it did before this record, and a traceback there is a failed
   dashboard page, not a missed pause.

## Alternatives that lost

- **A module that classifies the failure and lets each caller word it.**
  It changes no string and fixes no cell, because a caller can still
  leave out a failure kind. That is the defect itself.
- **One function in a new shipped module, wording every decode failure
  "cannot read".** It changes eight pinned strings instead of two, and
  it costs a `MIRRORS` entry for no added behaviour.
- **Two functions with required shape and absence arguments.** They
  give the same result as the decision, through six parameters instead
  of three.
- **A fourth kind, `object` (any JSON document except null).** It was
  in the approved interface for two named callers, `label_sync` and
  detector K, which were to keep their own shape check behind it. The
  replay showed it changing the `null` cell of every reader it was
  tried on (`label_sync.load_labels`, detector K,
  `lint.check_output_evals`, `cli.read_execution` and
  `sweeps.load_payload`) to `<shown> is null`, because `(None, None)`
  already means absent. Those readers stayed hand-written, no adopter
  asked for the kind, and it was dropped after review: a kind with no
  caller is the anticipated reuse CLAUDE.md's bar excludes.

## Consequences

- 16 of the matrix's 19 raising cells, and all six measured sites,
  return problem strings. The three that still raise are
  `trigger_eval.print_metrics`'s shape cells, which are a different
  defect. The monthly cap check and `budget_guard.record` reach their
  fail-closed paths.
- `factory_config.object_problems` and `lint.object_problems` lose
  their last callers to the `dict` kind, and they go with the adoption
  that removes their last caller. `eval_schema.object_problems` stays,
  because its validators still use it.
- `factory_config`, `eval_schema` and `cost_ledger` gain an import of
  `cli`. `cli` imports no sibling, so no cycle is possible.
- The 39 unguarded reads are untouched. A new reader of a repo file
  starts from `read_file`; a reader that cannot use it says why.
