---
stage: architect
run: maintenance:one-labels-walk
date: 2026-08-24
assumptions: ["Chosen without live interview: this run is autorun-driven, so the option comparison below is decided on the recorded decisions it touches — ADR-0037's seam charter and ADR-0060's purity claim — with both cited so the operator can overturn it by reading rather than re-deriving.", "NO ADR is offered, and that is a decision rather than an omission. The architect skill's bar is all three of hard to reverse, surprising without context, and the result of a real trade-off; this is one import and one function body, reversible by `git revert`, and it APPLIES an accepted ADR rather than changing one. The two runs before this one did file ADRs because each changed a gate an accepted ADR had written. This one does not."]
---

# Architecture: the drift rule reads names through the seam that owns them

## Approach

`plane_drift.issue_lifecycle` keeps its name, its signature and its
meaning — *the `wo:` labels one issue-listing entry carries, sorted* — and
stops walking the labels array itself. It calls `cli.label_names` and
filters the result:

```python
return sorted(name for name in label_names(issue)
              if name.startswith("wo:"))
```

Two facts, cleanly separated: *what names a gh payload carries* belongs to
the cli seam (ADR-0037), and *which of those names are lifecycle labels*
belongs here. Today one function states both, and the first of them twice.

## Components

### `plane_drift.issue_lifecycle` — the changed one

- Responsibility narrows to the `wo:` filter and the sort. Extraction
  moves to the collaborator.
- Collaborator: `cli.label_names`, imported by name, exactly as both of
  this module's callers already import it.
- **Behaviour is preserved on every reachable input**, measured in
  `defect.md`: zero mismatches over twelve label-entry shapes in every
  arrangement up to length two, every malformed `labels` value, and a
  missing key.
- **One unreachable input changes, and it widens.** `issue.get("labels")`
  raises `AttributeError` on a non-dict today; `label_names` treats a bare
  list as the labels array and any other non-dict as empty.
  `reconcile_drift` drops a non-dict entry with a `drift:` problem before
  either walk runs (plane_drift.py:68-72), so nothing can reach it. The
  change removes a crash and adds no silence.

### `cli.label_names` — unchanged

Not edited, not moved, not widened. Its docstring already claims to be
"the strictest all of them tolerate" across every caller; this run makes
that claim true rather than adjusting it.

### `plane_drift`'s module docstring — the decision, written where it is read

The docstring calls the module PURE: *"the listing arrives as data, so
neither caller's runner reaches this file, and no test here needs one"*.
Nothing recorded whether that forbids importing `cli` at all or only
forbids doing I/O. It is the second, and the docstring now says so: purity
here is about **runners and I/O**, not about the import graph.
`label_names` is a pure function, importing `cli` runs no subprocess, and
`plane_drift`'s tests still need no runner — which is the property the
sentence exists to protect.

### `tests/test_one_owner.py` — the record that goes stale

Two comments call this group live at HEAD: the fixture header
(tests/test_one_owner.py:271-277, *"still live at HEAD as this run's
acceptance fixture"*) and the miss-3 header (:786-789, *"STILL OPEN at
HEAD … this run's acceptance fixture rather than its cleanup target"*).
Both move to the closed form the miss-1 header already uses — *"Closed by
ADR-0058 at 7988962 (#312)"* — naming this run's commit instead. The
frozen fixture STRINGS do not change: they are the historical shape the
pass must keep finding, and rebasing them onto folded code would delete
the acceptance evidence.

## Data model

No change. A gh issue-listing entry stays the dict gh answers with.

## Interfaces & contracts

### `issue_lifecycle(issue) -> list[str]`

- Input: one gh issue-listing entry. Untrusted in shape, not in origin.
- Output: the `wo:`-prefixed label names it carries, sorted, deduplicated
  by nothing (a duplicate label is reported by `reconcile_drift`'s
  multiple-lifecycle-labels line and must survive to reach it).
- Failure modes: none. A malformed entry yields `[]`, which
  `reconcile_drift` renders as `no wo: label`.
- **Changed:** a non-dict `issue` returns `[]` instead of raising
  `AttributeError`. Unreachable through the only caller.

### `plane_drift`'s import graph

- Adds `from cli import label_names`. No cycle: `cli` imports no factory
  module, and both of `plane_drift`'s consumers already import both.

## Stack & dependencies

Stdlib only; no new import beyond the one seam function.
**`plane_drift.py` is not a `factory_init.MIRRORS` entry** (ADR-0060 —
neither of its callers ships), and `cli.py` is not edited, so this run
produces **no payload twin and no manifest churn**. That is deliberate:
seven PRs are open against `factory/manifest.json`, and a run that can
avoid adding an eighth should.

## Decisions & alternatives

- **`plane_drift` imports the seam** over **moving `label_names` into
  `knowledge_plane`** — the second would put the gh-payload walk beside
  the typed-ID grammar, contradicting ADR-0037's live charter with no
  evidenced friction. Relitigating an accepted decision needs evidence,
  and there is none here.
- **Import it** over **injecting a `names=` callable into
  `reconcile_drift`** — that is a seam with exactly one adapter, which
  costs indirection and returns nothing.
- **Import it** over **having each caller pre-extract names and pass
  them** — `issues` would stop being the gh listing, `reconcile_drift`
  reads `number` and `state` off the same entries, and both callers would
  do the extraction separately. That re-creates the duplication one level
  up, in two places instead of one.
- **Keep `issue_lifecycle` as a function** over **inlining it at its two
  call sites** — the `wo:` filter is its own fact and `reconcile_drift`
  asks for it twice (plane_drift.py:87 and :112). Inlining would trade one
  duplication for another.
- **Preserve the `AttributeError`** was considered and rejected: matching
  it would mean re-adding an `isinstance(issue, dict)` check whose only
  purpose is to reproduce a crash no caller can trigger.

## ADRs

**None owed.** See the frontmatter assumption: this applies ADR-0037
rather than changing it, and ADR-0060's decision — one cross-plane drift
rule, the caller declares what absence means — is untouched. The purity
clarification lives in the module docstring, which is where a reader hits
the question.
