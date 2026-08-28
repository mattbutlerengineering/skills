---
stage: capture
run: maintenance:a-tenth-role-nothing-fails-on
date: 2026-08-27
re-entry: implement
assumptions: []
---

# Defect: the checks are right, the domain is wrong

## Defect

Every role check in the factory runs in one direction. Each iterates
`factory_roles.ROLES` and asks whether the files on disk honour it:

```
    def test_agent_file_exists(self):
        for role in ROLES:
```

Nothing asks the inverse — whether the files hold anything `ROLES` does
not name. Even the scan that is written over *files* rather than roles
has a `ROLES`-shaped domain, because the file list is derived from the
vocabulary:

```
def charter_files():
    """Every file a charter is written in, index included."""
    return ([agent_path(role) for role in ROLES]
            + [charter_path(role) for role in ROLES]
            + [CHARTERS_INDEX])
```

So an agent stub at `factory/agents/factory-<x>.md` whose `x` is not in
`ROLES` is dispatchable and checked by nothing.

## Why it matters

`factory_roles.py` exists for exactly this. Its own docstring:

> Before this seam the role set had four homes that never imported each
> other [...] Adding a tenth role touched all of them, and nothing failed
> when they disagreed.

The seam made the nine agree. It did not make a tenth fail. And a tenth
is not hypothetical the way a missing file is: the subagent registry keys
agents by frontmatter `name:`, not by the filename and not by `ROLES`, so
a stub dropped into `factory/agents/` is *live* — dispatchable the moment
it exists, with none of the guarantees the other nine carry.

Concretely, such a stub may name a routing band `factory.json` does not
define, hardcode a model id (the second routing source ADR-0004 forbids
and this very suite has a test for), and have no charter at all. The
dispatch plane reads it; the test suite does not see it.

## Reproduction

A stub modelled on the real ones, for a role the vocabulary does not
name. It carries all three faults on purpose:

```
$ cat factory/agents/factory-securityreviewer.md
---
name: factory-securityreviewer
description: Independent security review of a work order's diff.
tools: Read, Grep, Bash
route: opus_deep
model: claude-opus-5
---

Load `factory/charters/securityreviewer/CHARTER.md` and follow it.
```

`opus_deep` is not a band the config defines, `model:` is the forbidden
second routing source, and `factory/charters/securityreviewer/` does not
exist. The full battery, with that file sitting in the repo:

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
$ python3 -c "import factory_config; c,_=factory_config.load('.'); print('opus_deep' in c['routing'])"
False
```

Green, all of it.

The sharp version of the finding is what happens when the same file is
brought inside the vocabulary. Patching `factory_roles.ROLES` to include
the role before importing the suite — the file unchanged, only its
membership — turns up **ten** existing checks that catch it:

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

Ten checks, all correct, all working. None of them ever looks at the
file, because all ten iterate `ROLES` and the file is not in `ROLES`.

## Why the tests did not catch it

They are the right tests pointed at the wrong domain. This is not a
coverage hole in the ordinary sense — the assertions exist and are good.
The suite treats `ROLES` as *the* enumeration, which is correct for
asking "is each chartered role properly encoded?" and silently wrong for
asking "is everything encoded here a chartered role?". The second
question was never asked, in any of the three places a role is spelled:
the stub directory, the charter directory, or the index table.

`factory/CHARTERS.md` is the same shape in the other direction:
`test_index_lists_every_role_and_both_of_its_files` walks `ROLES` and
asserts each appears in the index, so a row that survives a role's
removal from the vocabulary lingers with nothing to notice it.

## Fix

Three assertions in `tests/test_factory_charters.py`, one per place, all
saying the same thing from the file's side rather than the vocabulary's:

- every `*.md` in `factory/agents/` is `factory-<role>.md` for a role in
  `ROLES` (and the `factory-` prefix is required, so a stub that skips
  the naming convention is not silently exempt);
- every directory in `factory/charters/` is a role in `ROLES`;
- every role named by either path column in the `CHARTERS.md` table is a
  role in `ROLES`.

With those, the vocabulary is closed in both directions and the ten
existing checks regain the domain they were always meant to cover: a new
stub either joins `ROLES` — and faces all ten — or fails immediately.

No production change. The seam is right; only its domain was open. An
on-disk enumeration in `factory_roles.py` would have exactly one caller,
and this repo's bar for a shared definition is multiple real callers plus
observed divergence between their copies.

## Breakdown

- [x] Reproduce: a stray stub with three faults, full battery still green.
- [x] Demonstrate the checks are correct by patching `ROLES` and counting
      the ten that fire.
- [x] Add the three inverse-direction assertions.
- [x] Show each of the three fires against injected drift in its own
      place, then remove the drift.
- [x] Clean battery green; no manifest movement.

## Notes

- 2026-08-27: these three tests are **pins, not reproductions** — they
  pass on `origin/main`, because the repo is currently clean. Nothing on
  `origin/main` goes red. The RED evidence is the injected drift, run
  three times in three places and then removed; `verification.md` records
  it that way rather than claiming a red-to-green transition the run did
  not have.
- 2026-08-27: the injected stray files were removed before commit —
  `git status` confirmed a single modified file — and `CHARTERS.md` was
  restored with `git checkout --` rather than by hand-editing the row out.
