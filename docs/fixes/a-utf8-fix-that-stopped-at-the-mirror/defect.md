---
stage: diagnose
run: maintenance:a-utf8-fix-that-stopped-at-the-mirror
date: 2026-08-31
assumptions: []
---

# Defect: the UTF-8 read fix stopped at the mirror boundary

## What happens

The run `json-that-is-not-utf8` (PR #410) established the remedy for a
real defect class: `UnicodeDecodeError` and `json.JSONDecodeError` are
siblings under `ValueError`, neither a subclass of the other, so a
handler naming only the latter lets an undecodable file escape as a
traceback. `UnicodeDecodeError` is likewise **not** an `OSError`, so the
other handler shape in use here misses it too.

That run fixed five modules. Every one of them is mirrored into the
template payload:

```
cli.py              factory_config.py   gates.py (x2)   label_sync.py
```

Four modules carry the identical defect and are **root-only** — absent
from `factory/templates/tools/factory/`, so a sweep that walked the
payload never saw them. Six sites, all reproduced raising:

```
lint.check_manifest      RAISED UnicodeDecodeError: 'utf-8' codec can't
                                decode byte 0xff in position 0
lint.check_pi_package    RAISED UnicodeDecodeError: 'utf-8' codec can't
                                decode byte 0xff in position 0
lint.check_output_evals  RAISED UnicodeDecodeError: 'utf-8' codec can't
                                decode byte 0xff in position 0
eval_schema.load_case_set RAISED UnicodeDecodeError: 'utf-8' codec can't
                                decode byte 0xff in position 0
dashboard.repo_set       RAISED UnicodeDecodeError: 'utf-8' codec can't
                                decode byte 0xff in position 0
charter_replay.main      RAISED UnicodeDecodeError: 'utf-8' codec can't
                                decode byte 0xff in position 0
```

## Why the sweep stopped where it did

This is the interesting half. The parent run did not fix "the modules
with this bug" — it fixed "the payload tools with this bug". The mirror
set is a *packaging* boundary; the defect class does not respect it.
Nothing about `lint.py` makes it less exposed than `gates.py`, and the
`one_owner.py` pre-pass cannot see the omission either, because a
missing handler is not a duplicated fact.

## Why each site matters

| site | catches | contract it breaks |
|---|---|---|
| `lint.py:29` `check_manifest` | `JSONDecodeError` | checker must return problem strings |
| `lint.py:46` `check_pi_package` | `JSONDecodeError` | same; ADR-0027 pairs it with `check_manifest` |
| `lint.py:483` `check_output_evals` | `JSONDecodeError` | walks a directory — one bad file kills the walk |
| `eval_schema.py:131` `load_case_set` | `JSONDecodeError` | `(values, problems)` seam contract |
| `dashboard.py:96` `repo_set` | `OSError`, `JSONDecodeError` | its docstring promises to report an unreadable config |
| `charter_replay.py:471` `main` | `OSError`, `JSONDecodeError` | its handler message is literally `cannot read` |

The three `lint.py` sites are the sharpest: `lint`'s whole contract is
that checkers return label-prefixed problem strings and the caller
prints and exits nonzero. A traceback means CI reports a crash rather
than `lint: N problem(s)` — the same contract `gates` detector F has,
which the parent run judged worth fixing.

`dashboard.repo_set` and `charter_replay.main` are the clearest
statements of intent: both already mean to report cleanly, and say so in
their own text. The encoding case just falls through the arm meant to
catch it.

## How it was found

An AST sweep over every git-tracked Python file for `try` blocks whose
body calls `read_text`/`read_bytes` and whose handlers name neither
`UnicodeDecodeError` nor a bare `except`. It reported 16 sites; 10 are
the parent run's (5 root + 5 payload mirrors), 6 are these.

## Scope

None of the four modules is in `factory_init.MIRRORS`, so there is no
payload mirror to update and no manifest to regenerate. The fix is
six handler tuples and nothing else.
