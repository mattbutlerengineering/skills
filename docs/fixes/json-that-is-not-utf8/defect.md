---
stage: diagnose
run: maintenance:json-that-is-not-utf8
date: 2026-08-30
assumptions: []
---

# Defect: a JSON file whose bytes are not UTF-8 crashes five readers

## What happens

Every JSON reader in the shipped payload guards `json.JSONDecodeError`.
`UnicodeDecodeError` is not one — the two are siblings under
`ValueError`, neither a subclass of the other:

```
>>> issubclass(json.JSONDecodeError, UnicodeDecodeError)
False
```

So a JSON file whose bytes will not decode as UTF-8 escapes the guard
and takes the process out:

```
factory_config.load     RAISED: UnicodeDecodeError 'utf-8' codec can't
                                decode byte 0xe9 in position 31
label_sync.load_labels  RAISED: UnicodeDecodeError 'utf-8' codec can't
                                decode byte 0xe9 in position 31
```

Fixture: `'{"routing": {"mechanical": "café"}}'.encode("latin-1")` —
what an editor set to latin-1 writes when someone types an accented
character into a config value.

## Why it matters

Four of the five sites ship in the payload and read files a downstream
repo owner hand-edits:

| Site | Reads | Consequence |
|---|---|---|
| `factory_config.load` | `.github/factory.json` | every dispatch path dies |
| `label_sync.load_labels` | `.github/labels.json` | label sync dies |
| `gates.check_config_shape` (F) | `.github/factory.json` | **the whole gate run dies — detectors A–J, not just F** |
| `gates.check_scaffold_sync` (E) | `factory/manifest.json` | same |
| `cli.read_event` | `GITHUB_EVENT_PATH` | the caller's judgment never runs |

The two gate sites are the worst. Both are inside a detector that is
supposed to *report* a problem; instead one bad byte aborts `gates.py`
and takes the other nine detectors with it. A traceback in CI is not a
gate verdict — a human reads "the gate crashed" and has no idea whether
anything else was wrong.

`cli.read_event`'s docstring is directly falsified by this:

> An unreadable, unparsable, or non-object payload is an error string
> the caller labels.

An undecodable payload is unreadable, and it was not an error string.

## Why it was not caught

The repo already knows about this failure mode — it guards it correctly
in the two places that read *text*:

```
gates.py:1080     except (OSError, UnicodeDecodeError) as err:   # detector H
one_owner.py:223  except (OSError, UnicodeDecodeError) as err:
```

The JSON readers diverged because "malformed JSON" was read as meaning
`JSONDecodeError`, and a decode failure happens one layer below, in
`read_text`, before `json.loads` is ever called. Nothing states the
rule in one place, so eleven sites each guessed, producing three
different except clauses for the same verdict.

## The fix, and why the message does not change

RFC 8259 §8.1 requires JSON text exchanged between systems to be
encoded in UTF-8. A file whose bytes are not UTF-8 therefore **is not
valid JSON** — the existing message is already correct and already the
right one for this case. Only the guard was too narrow. So the fix is
five identical widenings and no new vocabulary:

```python
except (json.JSONDecodeError, UnicodeDecodeError) as err:
```

That matters: the alternative — a second message like "is not valid
UTF-8" — would split one verdict across two strings, and every caller
that matches on the problem text would have to learn both.

## Blast radius left open, deliberately

Six more sites have the same guard but are repo-internal, not shipped,
and read files no downstream user touches: `eval_schema.py:131`,
`lint.py:29/46/483`, `dashboard.py:98/331`, `charter_replay.py:471`.
They are listed in the tracking issue rather than fixed here, because
the reachability argument that justifies this run — a hand-edited file
in a stamped repo — does not apply to them, and a fix run that touches
eight files while the PR queue is 44 deep buys conflicts it does not
need.
