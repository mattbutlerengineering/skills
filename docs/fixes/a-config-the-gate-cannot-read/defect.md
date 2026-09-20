---
stage: capture
run: maintenance:a-config-the-gate-cannot-read
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: a config the gate cannot read

## Defect

Both factory config loaders decode before they parse, and guard only the
parse.

```python
# factory_config.py:73
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as err:
        rel = path.relative_to(root).as_posix()
        return None, [f"config: {rel} is not valid JSON: {err}"]
```

`read_text(encoding="utf-8")` raises `UnicodeDecodeError` on a file that
is not valid UTF-8. `UnicodeDecodeError` is a `ValueError`, but it is
not a `json.JSONDecodeError`, so it escapes. `OSError` escapes too.
`label_sync.load_labels` has the same shape and the same two gaps.

The catch that IS present proves the intent: these loaders are meant to
report a malformed file, not to raise on one. A file saved in a
non-UTF-8 encoding is malformed in exactly the sense the existing catch
addresses; it simply fails one step earlier.

The peer seam loader already does this correctly:

```python
# cost_ledger.py:234
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        return None, [f"{label}: cannot read {COST_LEDGER}: {err}"]
```

## Why it matters

`factory_config` states its own contract:

> Conventions match gates.py: functions return (value, problems) with
> config:-prefixed problem strings; a field the config does not cover is
> a problem, never a silent default.

Five modules load the config through it — `assembler`,
`budget_guard`, `dashboard`, `cost_report` and `work_queue`. Each gets a
traceback where the seam promises a problem string.

Detector F, `gates.check_config_shape`, has the same gap but does NOT
reach it through this seam: it reads `factory.json` itself
(`gates.py:878`), deliberately and with its divergence documented — the
gate checks every candidate payload-first, where the seam returns the
first existing installed-first. Its own `json.loads(path.read_text(...))`
carries the identical `UnicodeDecodeError` hole, so the gate over a
malformed config crashes on one class of malformed config.

That half is NOT fixed here. `gates.py` is claimed by PR #320, and
this run does not edit it; the finding is recorded in `review.md` for a
later run. An earlier draft of this brief asserted detector F loaded
through the seam. It does not, and the claim was corrected once the test
proved otherwise.

## Reproduction

A config that is valid JSON but not valid UTF-8 — the shape an editor
saving latin-1 produces:

```
$ python3 -c "
import tempfile, pathlib, factory_config, gates
tmp = pathlib.Path(tempfile.mkdtemp()); gh = tmp / '.github'; gh.mkdir()
(gh / 'factory.json').write_bytes(b'{\"routing\": {\"mechanical\": \"caf\xe9\"}}')
print(factory_config.load(tmp))
"
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 31: invalid continuation byte
```

The gate over that same file:

```
$ python3 -c "... print(gates.check_config_shape(tmp))"
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 31: invalid continuation byte
```

And the label taxonomy loader:

```
$ python3 -c "... print(label_sync.load_labels(tmp))"
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 14: invalid continuation byte
```

## Breakdown

- [x] `factory_config.load` returns a `config:`-prefixed problem instead
      of raising when the file cannot be read or decoded. Acceptance: a
      test writes a non-UTF-8 `factory.json` and asserts a problem
      string.
- [x] `label_sync.load_labels` does the same under its `L:` prefix.
      Acceptance: a test writes a non-UTF-8 `labels.json` and asserts a
      problem string.
- [x] Full battery green, payload mirrors and manifest regenerated.

## Notes

2026-08-27 — the detector-F half of this defect was scoped OUT during
implementation, not deferred by choice of convenience. The test that
would have pinned it was written, run, and removed once it proved that
`gates.check_config_shape` reads `factory.json` through its own
`json.loads(path.read_text(...))` rather than through the seam. Fixing
that means editing `gates.py`, which PR #320 claims. The capture text
above was corrected in place to remove the claim that detector F loaded
through `factory_config`.
