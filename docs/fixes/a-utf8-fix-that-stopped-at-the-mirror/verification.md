---
stage: verify
run: maintenance:a-utf8-fix-that-stopped-at-the-mirror
date: 2026-08-31
assumptions: []
---

# Verification: the UTF-8 read fix stopped at the mirror boundary

## 1. Red before green — PASS

All six new tests errored with the crash itself before the change. The
tail of that run, literally:

```
======================================================================
ERROR: test_bytes_that_are_not_utf8_are_reported_not_raised (tests.test_charter_replay.TestTranscriptsFileIsUnreadable.test_bytes_that_are_not_utf8_are_reported_not_raised)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/mbutler/github/skills/tests/test_charter_replay.py", line 657, in test_bytes_that_are_not_utf8_are_reported_not_raised
    code = charter_replay.main(["--transcripts", str(path)])
  File "/Users/mbutler/github/skills/charter_replay.py", line 470, in main
    Path(args.transcripts).read_text(encoding="utf-8"))
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/pathlib/__init__.py", line 788, in read_text
    return f.read()
           ~~~~~~^^
  File "<frozen codecs>", line 325, in decode
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 5: invalid continuation byte

----------------------------------------------------------------------
Ran 6 tests in 0.039s

FAILED (errors=6)
```

`errors=6`, not `failures=6`: every one was the raise itself, which is
the defect, not an assertion about it.

## 2. Independent reproduction before any test existed — PASS

The defect was reproduced by calling the six functions directly, before
a line of test code was written, so the tests are pinning an observed
crash rather than defining one:

```
lint.check_manifest with a non-UTF-8 plugin.json:
  check_manifest: *** RAISED UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte

lint.check_pi_package with a non-UTF-8 package.json:
  check_pi_package: *** RAISED UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte

lint.check_output_evals with a non-UTF-8 eval file:
  check_output_evals: *** RAISED UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte
```

```
eval_schema.load_case_set, non-UTF-8:
  load_case_set: *** RAISED UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid star

dashboard.repo_set, non-UTF-8 (docstring: 'only an unreadable or misshapen config is a problem'):
  repo_set: *** RAISED UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid star

charter_replay.main --transcripts, non-UTF-8 (handler says 'cannot read'):
  main: *** RAISED UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid star
```

## 3. Each site returns a problem, not a raise — PASS

```
......
----------------------------------------------------------------------
Ran 6 tests in 0.035s

OK
```

Messages are unchanged from the malformed-JSON case at the same site,
per the parent run's decision that RFC 8259 §8.1 makes undecodable bytes
genuinely invalid JSON.

## 4. Full battery — PASS

```
Ran 1350 tests in 16.488s

OK
lint: 0 problem(s) across 24 skills
gates: 0 problem(s)
selftest: ok
```

1344 on `origin/main` + 6 new = 1350.

## 5. The sweep is now closed for root-only modules — PASS

Re-running the AST sweep on this branch leaves exactly the parent run's
ten sites and nothing else:

```
remaining sites on this branch: 10
   cli.py:236
   factory/templates/tools/factory/cli.py:236
   factory/templates/tools/factory/factory_config.py:72
   factory/templates/tools/factory/gates.py:739
   factory/templates/tools/factory/gates.py:877
   factory/templates/tools/factory/label_sync.py:44
   factory_config.py:72
   gates.py:739
   gates.py:877
   label_sync.py:44
```

Those ten are PR #410's, root and payload mirror. The two runs partition
the defect class with no overlap.

## 6. No cross-PR hazard — PASS

Every open PR was scanned for a diff touching any of this run's eight
files. None does:

```
(overlap scan done)
```

`one_owner.py` reports the same nine pre-existing problems as `main`,
unchanged by this run.

## Not verified

- **The payload half.** The ten remaining sites are PR #410's to fix and
  are deliberately untouched here. If #410 is closed unmerged, they stay
  open and need their own run.
- **Non-UTF-8 files in the wild.** No file in this repo is currently
  non-UTF-8; every case is synthetic latin-1 bytes. The defect is in the
  handler, not in any committed file.
- **Encodings other than latin-1.** The fixture uses latin-1 and utf-16
  bytes only. `UnicodeDecodeError` is raised by the codec, not by the
  fixture, so the guard is encoding-independent by construction — but
  that is an argument, not a measurement.
