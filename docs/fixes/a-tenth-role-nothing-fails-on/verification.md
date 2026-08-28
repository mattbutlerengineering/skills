---
stage: verify
run: maintenance:a-tenth-role-nothing-fails-on
date: 2026-08-27
assumptions: []
---

# Verification: a tenth role nothing fails on

Seven criteria, each with the command run and its actual output.

## 1. The gap reproduces — PASS

A dispatchable stub for a role outside the vocabulary, carrying an
undefined band, a hardcoded model id, and no charter. The full battery
with that file present:

```
$ python3 -m unittest discover tests
Ran 1344 tests in 18.723s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

## 2. The band it names is not one the config defines — PASS

So the stub is not merely undocumented; it is wrong in a way the factory
has a check for:

```
$ python3 -c "import factory_config; c,p=factory_config.load('.'); print('routing bands:', sorted(c['routing'])); print('opus_deep defined:', 'opus_deep' in c['routing'])"
routing bands: ['architecture_review', 'implementation', 'mechanical']
opus_deep defined: False
```

## 3. Ten existing checks would have caught it — PASS

The same file, unchanged, with only its `ROLES` membership patched before
the suite imports:

```
$ python3 asif.py
Ran 19 tests in 0.010s
FAILED (failures=6, errors=5)
  FAILS: test_no_stub_hardcodes_a_model
  FAILS: test_route_names_a_band_the_factory_config_defines
  FAILS: test_the_index_band_column_matches_each_stubs_route
  FAILS: test_charter_file_exists
  FAILS: test_index_lists_every_role_and_both_of_its_files
  FAILS: test_charter_and_stub_agree_on_the_band
  FAILS: test_charter_has_must_never_and_escalation_sections
  FAILS: test_charter_states_its_gate_obligation
  FAILS: test_merge_authority_tracks_the_amendment
  FAILS: test_no_charter_file_names_a_model_id
```

This is the criterion that makes the finding a domain problem rather than
a coverage problem: the checks are correct and working.

## 4. Each of the three new assertions fires — PASS

Drift injected in all three places at once — a stray stub, a stray
charter directory, and a stray row in the index table:

```
$ python3 -m unittest tests.test_factory_charters.TestTheVocabularyIsTheWholeDomain -v
  ... (stub='factory-securityreviewer.md') ... FAIL
  ... (charter='securityreviewer') ... FAIL
  ... (role='securityreviewer') ... FAIL
  ... (role='securityreviewer') ... FAIL
AssertionError: 'securityreviewer' not found in ('pm', 'architect', 'ux', 'planner', 'swe', 'qa', 'reviewer', 'support', 'toolsmith') : factory-securityreviewer.md is dispatchable but names no role in factory_roles.ROLES
AssertionError: 'securityreviewer' not found in (...) : factory/charters/securityreviewer/ names no role in factory_roles.ROLES
AssertionError: 'securityreviewer' not found in (...) : CHARTERS.md still lists 'securityreviewer', which factory_roles.ROLES does not name
Ran 3 tests in 0.001s
FAILED (failures=4)
```

Three tests, four failures: the index test fires once per path column, so
a row is caught whichever column still names the dropped role.

## 5. The injected drift was removed before commit — PASS

```
$ rm -f factory/agents/factory-securityreviewer.md
$ rm -rf factory/charters/securityreviewer
$ git checkout -- factory/CHARTERS.md
$ git status --short
 M tests/test_factory_charters.py
```

One modified file. `CHARTERS.md` was restored from git rather than
hand-edited, so no stray whitespace survives the demonstration.

## 6. The clean battery is green — PASS

```
$ python3 -m unittest discover tests
Ran 1347 tests in 17.547s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

1347 = the 1344 on `origin/main` plus this run's three.

## 7. No payload byte moved — PASS

`tests/test_factory_charters.py` is not mirrored, and no production
module changed:

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ git status --short
 M tests/test_factory_charters.py
```

`update-manifest` left the manifest and every template file untouched.

## Not verified

- **These three tests do not go red on `origin/main`.** They are pins,
  not reproductions: the repo is currently clean, so all three pass
  before the change as well as after. There is no red-to-green transition
  in this run, and criterion 4 above is the honest substitute — drift
  injected on purpose, each assertion shown to fire, the drift removed.
- **The one-owner pre-pass is unchanged at nine findings**, none of which
  names `tests/test_factory_charters.py` — but that is not evidence:
  `one_owner.py`'s `EXCLUDED` tuple skips `tests/` entirely, so it
  structurally cannot see anything in this diff. Recorded so the clean
  number is not read as coverage.
- **`factory/agents/` and `factory/charters/` were not audited for the
  reverse problem** — a role in `ROLES` whose files are subtly wrong in
  ways no existing check covers. That direction is what the ten checks
  already do; this run closed the other one and made no claim about the
  depth of the first.
- **Nothing was dispatched.** That a stub outside `ROLES` is genuinely
  dispatchable rests on the documented registry behaviour (agents are
  keyed by frontmatter `name:`), not on an observed dispatch in this run.
