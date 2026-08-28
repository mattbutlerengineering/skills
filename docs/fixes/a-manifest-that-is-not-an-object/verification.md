---
stage: verify
run: maintenance:a-manifest-that-is-not-an-object
date: 2026-08-27
assumptions: []
---

# Verification: a manifest that is not an object

Baseline on `origin/main` (622e7c0) is 1344 tests. This run adds three.

## 1 — the reported reproduction no longer reproduces

The exact five shapes from `defect.md`, through both readers:

```
$ python3 -c "
import tempfile
from pathlib import Path
import lint
for shape in ('null', '42', '\"text\"', '[\"a\"]', 'true'):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp); (root / '.claude-plugin').mkdir()
        (root / '.claude-plugin' / 'plugin.json').write_text(shape)
        (root / 'package.json').write_text(shape)
        print(f'  {shape:8} {lint.check_manifest(root)}'
              f' {lint.check_pi_package(root)}')
"
  null     ['plugin.json is not a JSON object'] ['package.json is not a JSON object']
  42       ['plugin.json is not a JSON object'] ['package.json is not a JSON object']
  "text"   ['plugin.json is not a JSON object'] ['package.json is not a JSON object']
  ["a"]    ['plugin.json is not a JSON object'] ['package.json is not a JSON object']
  true     ['plugin.json is not a JSON object'] ['package.json is not a JSON object']
```

Ten raises became ten problem strings. PASS.

## 2 — the regression tests fail on the unfixed code

All three new tests are RED against `origin/main`'s `lint.py`, as
errors rather than failures, which is the shape of the defect:

```
   5 ERROR: test_a_manifest_that_is_not_an_object_names_its_shape
   5 ERROR: test_a_package_that_is_not_an_object_names_its_shape
   1 ERROR: test_a_non_object_manifest_does_not_stop_the_gate
   1 FAIL:  test_a_non_object_manifest_does_not_stop_the_gate
```

(The five-per-test counts are the subTests, one per JSON shape.) PASS.

## 3 — the gate completes instead of dying at its first checker

`check_manifest` is `CHECKERS[0]`, so the consequence being fixed is not
a thinner report but no report. `test_a_non_object_manifest_does_not_
stop_the_gate` walks every entry in `CHECKERS` over a tree whose
`plugin.json` is `null` and asserts the whole walk completes with
exactly the one problem:

```
$ python3 -m unittest tests.test_lint.TestManifest
Ran 3 tests in 0.028s

OK
```

PASS.

## 4 — the existing behaviour is unchanged

The clean-tree test (every checker returns zero problems), both
missing-file tests, both invalid-JSON tests and all four field tests are
untouched and still pass:

```
$ python3 -m unittest tests.test_lint
Ran 77 tests in 0.801s

OK
```

PASS.

## 5 — full battery

```
$ python3 -m unittest discover tests
Ran 1347 tests in 16.359s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

1347 = 1344 + 3. PASS.

## Not verified

- **`check_output_evals` still raises on a non-object** and is
  deliberately not fixed here — see `defect.md`'s "A third instance".
  The reproduction for it is recorded there and re-run above; it is an
  open finding, not a verified criterion.
- **No live install is exercised.** The readers are checked over fixture
  trees, the seam every other lint test uses; nothing installs the
  plugin or runs `omp`.
- **`one_owner.py` is unchanged at 9 findings**, so the new shared
  helper did not create a second owner of anything the pre-pass can see.
