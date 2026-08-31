---
stage: verify
run: maintenance:a-broken-taxonomy-passes-the-gate
date: 2026-08-30
---

# Verification — a broken taxonomy passes the gate

Branched from `origin/main` at `622e7c0`, whose battery is `lint: 0`,
`gates: 0`, `selftest: ok`, `Ran 1344 tests ... OK`.

## 1. The regression, demonstrated in a real stamped repo

`scratchpad/repro_taxonomy.py` stamps a product repo with
`factory_init.stamp` and writes each broken taxonomy into the curated
`.github/labels.json` the stamp installs. On `origin/main`:

```
stamp: clean
taxonomy                   load_labels problems                         detector J   offline gates
(the stamped taxonomy)     -                                            0 problem(s) gates: 0 problem(s)
corrupt JSON               L: .github/labels.json is not valid JSON: .. 0 problem(s) gates: 0 problem(s)
not a list                 L: .github/labels.json must be a non-empty.. 0 problem(s) gates: 0 problem(s)
empty array                L: .github/labels.json must be a non-empty.. 0 problem(s) gates: 0 problem(s)
every entry malformed      L: .github/labels.json[0] entry lacks colo.. 0 problem(s) gates: 0 problem(s)
duplicate label name       L: .github/labels.json[28] duplicate label.. 0 problem(s) gates: 0 problem(s)
```

The same script on this branch:

```
stamp: clean
taxonomy                   load_labels problems                         detector J   offline gates
(the stamped taxonomy)     -                                            0 problem(s) gates: 0 problem(s)
corrupt JSON               L: .github/labels.json is not valid JSON: .. 1 problem(s) L: .github/labels.json is not valid JSON: Expecting property name enclosed in double quotes: line 1 column 3 (char 2)
gates: 1 problem(s)
not a list                 L: .github/labels.json must be a non-empty.. 1 problem(s) L: .github/labels.json must be a non-empty JSON array of label entries
gates: 1 problem(s)
empty array                L: .github/labels.json must be a non-empty.. 1 problem(s) L: .github/labels.json must be a non-empty JSON array of label entries
gates: 1 problem(s)
every entry malformed      L: .github/labels.json[0] entry lacks colo.. 2 problem(s) L: .github/labels.json[0] entry lacks color, description
L: .github/labels.json[1] entry lacks name, color, description
gates: 2 problem(s)
duplicate label name       L: .github/labels.json[28] duplicate label.. 1 problem(s) L: .github/labels.json[28] duplicate label name wo:draft
gates: 1 problem(s)
```

Five broken taxonomies reported, the valid one still silent. The
last-column strings are the stamped repo's own
`python3 tools/factory/gates.py` stdout, captured by subprocess — not
this checkout's.

**Result: PASS** (brief criterion 1).

## 2. `make check` in the stamped repo stops at the gate

Same stamped tree, driven through the product Makefile:

```
$ make check
python3 tools/factory/gates.py
gates: 0 problem(s)
python3 tools/factory/gates.py --selftest

$ printf '{ not json' > .github/labels.json
$ make check
python3 tools/factory/gates.py
L: .github/labels.json is not valid JSON: Expecting property name enclosed in double quotes: line 1 column 3 (char 2)
gates: 1 problem(s)
make: *** [check] Error 1
```

Exit code, taken directly from the gate rather than through make:

```
$ python3 tools/factory/gates.py; echo "exit=$?"
L: .github/labels.json is not valid JSON: Expecting property name enclosed in double quotes: line 1 column 3 (char 2)
gates: 1 problem(s)
exit=1
```

**NOT RUN:** `make check` to completion in that tree. Its third step is
`python3 -m unittest discover -q tests`, and a freshly stamped empty
repo has no `tests/` directory yet — `ImportError: Start directory is
not importable: 'tests'`. That is a property of stamping into a bare
tree, not of this change, and it is why the repo's own acceptance test
(`test_stamped_repo_passes_its_own_gates`) runs `gates.py` directly. The
demonstration above is therefore of the gate steps only, which are the
steps this run touches, and the corrupt run never reaches step three
because step one already failed.

**Result: PASS** (brief criterion 1).

## 3. An absent taxonomy is still silent

The gates selftest fixture asserts this on a tree with no taxonomy
anywhere (`expect_clean("J unstamped", ...)`), and
`tests/test_gates.py::TestLabelWiring::test_a_tree_with_no_taxonomy_is_silent`
asserts it through the public checker. Both pass — see §5 and §6.

The distinction is drawn by `label_sync.taxonomy_path`, and the point of
extracting it rather than re-walking the candidates in `gates.py` is
pinned directly:

```
test_load_labels_reports_against_the_path_it_resolves (tests.test_label_sync.TestTaxonomyPath.test_load_labels_reports_against_the_path_it_resolves)
The two must never name different files. Asserted through ... ok
```

**Result: PASS** (brief criterion 2).

## 4. One malformed entry among good ones reports both halves

`test_one_malformed_entry_does_not_switch_the_detector_off` kept its
original assertion (the wiring finding still fires) and gained the
second half — that the malformed entry is itself named. Without it the
operator is told "add `wo:merged` to `.github/labels.json`" about a
label that is already in the file, just missing its colour.

The fixture's taxonomy drops `wo:merged` and appends a name-only entry;
what the detector now returns for it:

```
L: .github/labels.json[10] entry lacks color, description
J: Makefile:2 names wo:merged but the taxonomy has no such label (add it to .github/labels.json, or the flip fails when CI runs it)
J: human_gates.py names wo:merged but the taxonomy has no such label (add it to .github/labels.json, or the flip fails when CI runs it)
```

```
$ python3 -m unittest tests.test_gates.TestLabelWiring.test_one_malformed_entry_does_not_switch_the_detector_off
Ran 1 test in 0.003s

OK
```

**Result: PASS** (brief criterion 3).

## 5. Both regressions fail without the fix

`check_label_wiring`'s body only was spliced back to `origin/main`'s,
leaving every other change on this branch in place:

```
$ python3 gates.py --selftest; echo "exit=$?"
J unreadable: expected a problem containing '.github/labels.json is not valid JSON', got []
selftest: FAIL
exit=1

$ python3 -m unittest tests.test_gates.TestLabelWiring
Ran 10 tests in 0.008s
FAILED (failures=3)
```

Restoring the branch's body:

```
$ python3 gates.py --selftest
selftest: ok
$ python3 -m unittest tests.test_gates.TestLabelWiring
Ran 10 tests in 0.007s
OK
```

`tests/test_label_sync.py::TestTaxonomyPath` was written before
`taxonomy_path` existed and failed for the right reason:

```
AttributeError: module 'label_sync' has no attribute 'taxonomy_path'
Ran 5 tests in 0.003s
FAILED (errors=5)
```

**Result: PASS.**

## 6. Full battery

```
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
$ python3 -m unittest discover tests
Ran 1350 tests in 15.853s

OK
```

1344 → 1350: five for `TestTaxonomyPath`, one for
`test_a_wiring_complete_taxonomy_can_still_be_malformed`.
`test_an_unusable_taxonomy_is_silent_not_a_traceback` was replaced
in place by `test_an_unreadable_taxonomy_is_reported_not_a_traceback`,
so it is a rewrite rather than an addition.

The two label suites in full:

```
test_a_pruned_label_is_reported_against_every_site_that_names_it ... ok
test_a_pruned_tool_label_is_reported_without_any_makefile ... ok
test_a_taxonomy_carrying_every_named_label_is_silent ... ok
test_a_tree_with_no_taxonomy_is_silent ... ok
test_a_wiring_complete_taxonomy_can_still_be_malformed
The case with no wiring finding at all to lean on. ... ok
test_an_unnamed_taxonomy_label_is_not_a_finding ... ok
test_an_unreadable_taxonomy_is_reported_not_a_traceback
Two properties, and they used to be asserted as one. ... ok
test_one_malformed_entry_does_not_switch_the_detector_off ... ok
test_the_extraction_actually_finds_the_shipped_labels
A detector whose extraction silently stops matching is ... ok
test_the_shipped_taxonomy_wires_the_shipped_tools
The live pin, and the one that would have caught the gap. ... ok
test_it_falls_back_to_the_template_copy ... ok
test_it_is_none_when_no_candidate_exists ... ok
test_it_resolves_the_installed_copy_first ... ok
test_load_labels_reports_against_the_path_it_resolves
The two must never name different files. Asserted through ... ok
test_the_shipped_repo_resolves_its_payload_copy ... ok

Ran 15 tests in 0.011s

OK
```

(unittest prints a test's docstring first line under its id, which is
why five entries read as prose. The module-path prefixes are trimmed
here for width; the run above was `-v` and carried them.)

**Result: PASS** (brief criterion 4).

## 7. The payload mirror

`python3 factory_init.py update-manifest` was re-run after the source
edits and reported `factory-init: 0 problem(s)`; the changed files are
`factory/manifest.json`,
`factory/templates/tools/factory/gates.py` and
`factory/templates/tools/factory/label_sync.py`. Detector E is the
manifest↔payload pin and is green in §6;
`tests/test_factory_init.py` is the payload↔root pin and is inside the
1350.

Diffstat for the whole change:

```
 factory/manifest.json                         |  4 +-
 factory/templates/tools/factory/gates.py      | 68 ++++++++++++++++++--------
 factory/templates/tools/factory/label_sync.py | 22 +++++++--
 gates.py                                      | 68 ++++++++++++++++++--------
 label_sync.py                                 | 22 +++++++--
 tests/test_gates.py                           | 69 ++++++++++++++++++++++-----
 tests/test_label_sync.py                      | 59 +++++++++++++++++++++++
 7 files changed, 251 insertions(+), 61 deletions(-)
```

**Result: PASS.**

## 8. The secondary finding

`TestLabelWiring`'s docstring said the tools and the Makefile "name 15
labels between them". Derived from the shipped tree:

```
$ python3 -c "import pathlib, gates; print(len(gates.declared_labels(pathlib.Path('.'))))"
13
```

13 distinct labels at 15 declaring sites — `wo:merged` and
`wo:needs-review` are each named twice (a Makefile target and a
`human_gates` entry). The docstring no longer carries a count; the
per-site enumeration that IS checked lives in
`test_the_extraction_actually_finds_the_shipped_labels`, which is
unchanged.

**Result: PASS.**

## Not verified

- **Nothing was run against live GitHub.** No test in this repo touches
  a real `gh`, and this run added none. The claim that a corrupt
  taxonomy "fails in the dispatch plane" is the pre-existing docstring's
  and is not re-proven here; what is proven is that the offline gate now
  reports it first.
- **`label_sync.py`'s own CLI** (`python3 label_sync.py`) was not run —
  it makes network calls. Its offline half, `load_labels`, is covered by
  `tests/test_label_sync.py`, which is inside the 1350.
- **`sweeps.py` and `validator.py` behaviour is unchanged and was not
  re-derived.** They already forwarded the loader's problems; this run
  did not touch either, and their suites are inside the 1350.
- **`one_owner.py`** reports `one-owner: 9 problem(s)` on this branch,
  the same nine as `origin/main`. It is a review pre-pass, not a gate.
