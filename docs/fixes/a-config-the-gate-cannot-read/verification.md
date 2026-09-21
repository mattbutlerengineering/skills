---
stage: verify
run: maintenance:a-config-the-gate-cannot-read
date: 2026-08-27
assumptions: []
---

# Verification: a config the gate cannot read

## 1. `factory_config.load` degrades instead of raising — PASS

A valid-JSON, invalid-UTF-8 config now returns a `config:`-prefixed
problem string.

```
$ python3 -c "... print(factory_config.load(tmp)[1][0])"
config: cannot read .github/factory.json: 'utf-8' codec can't decode byte 0xe9
```

## 2. `label_sync.load_labels` degrades instead of raising — PASS

The same shape under the module's own `L:` prefix.

```
$ python3 -c "... print(label_sync.load_labels(tmp)[1][0])"
L: cannot read .github/labels.json: 'utf-8' codec can't decode byte 0xe9 in po
```

## 3. Malformed JSON is still reported exactly as before — PASS

The existing catch is unchanged: splitting decode from parse did not
reword or reclassify the JSON problem.

```
$ python3 -c "... print(factory_config.load(tmp)[1][0])"
config: .github/factory.json is not valid JSON: Expecting value: line 1 column
```

## 4. Full battery green, payload mirrored — PASS

1344 tests on the merge base, 1346 here: the two added above. Both
edited modules are in `factory_init.MIRRORS`, so `update-manifest` ran
and the payload copies carry the fix.

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ python3 -m unittest discover tests
Ran 1346 tests in 16.251s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

## 5. The detector-F half is NOT fixed — recorded, not claimed

`gates.check_config_shape` reads the same file through its own
`json.loads(path.read_text(...))` at `gates.py:878` and still raises on
the same input. This is stated as an open finding, not verified away:

```
$ python3 -c "... gates.check_config_shape(tmp)"
detector F: still raises UnicodeDecodeError (gates.py:878)
```

`gates.py` is claimed by PR #320. Fixing it from this branch would
collide with that PR, so the gap is carried into `review.md` as a
finding for a later run.

## Not verified

No OSError path was exercised: `read_text` failing for permissions or
I/O is now caught by the same clause as the decode failure, but
simulating it portably needs the technique PR #353 is introducing, and
this run did not reach for it. The decode half is what the tests pin.
