---
stage: verify
run: maintenance:json-that-is-not-utf8
date: 2026-08-30
assumptions: []
---

# Verification: a JSON file whose bytes are not UTF-8

## 1. Red before green — PASS

Five of the six new tests errored with the crash itself before the fix:

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 31:
  invalid continuation byte
  test_factory_config.TestLoad.test_bytes_that_are_not_utf8_...
  test_label_sync.TestLoadLabels.test_bytes_that_are_not_utf8_...
  test_cli.TestReadEvent.test_bytes_that_are_not_utf8_are_an_error
  test_gates.TestConfigShape.test_bytes_that_are_not_utf8_...
  test_gates.TestScaffoldSync.test_a_manifest_whose_bytes_are_not_utf8_...
```

The sixth — `test_a_manifest_that_is_not_json_is_a_problem` — passed on
first run, and that is the point of writing it: detector E's malformed
case was already handled and had **no test at all**. It is pinned now.

## 2. Each site returns a problem, not a raise — PASS

All six green after the change, with the message unchanged from the
malformed-JSON case at the same site.

## 3. Detector F reports and keeps going — PASS

`check_config_shape` iterates both candidate homes. The test asserts
exactly one problem from a tree with one bad config, which is what
proves the `continue` path is intact: a broken payload copy must not
mask, or abort, the read of the installed copy.

## 4. The full battery — PASS

Base `main` is 1344 tests; this branch is 1350. Six added, none lost —
see §5 for why that arithmetic was checked rather than assumed.

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)

$ python3 -m unittest discover tests
Ran 1350 tests in 15.615s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

## 5. A hiccup worth recording: three tests silently disappeared

The first cut of the detector-E tests introduced a **second**
`class TestScaffoldSync` in `tests/test_gates.py`. Python rebinds the
name without complaint, unittest discovery only ever sees the last
binding, and the three tests in the original class stopped running.

**The suite still said `OK`.** Nothing failed. The only signal was the
count: 1344 + 6 should be 1350, and it said 1347.

Fixed by merging the two new cases into the existing class. Swept the
whole repo afterward for the same hazard — every root module and every
test module, checking top-level names and per-class method names:

```
total: 0
```

So no live instance exists today. It remains a latent hazard that a
green suite cannot report, and it is filed separately rather than
folded into this run.

## What is NOT verified

- The six repo-internal sites listed in `defect.md` still raise. That
  is a stated, deliberate scope boundary, not an oversight.
- `OSError` is still ungated at `factory_config.load`,
  `label_sync.load_labels` and both gate sites. Different failure
  class, separate in-flight work (#401, #353) — see `review.md` §3.
