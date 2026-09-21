---
stage: verify
run: maintenance:the-placeholder-that-is-a-real-handle
date: 2026-08-28
assumptions: []
---

# Verification

Every criterion below was run on `agent/the-placeholder-that-is-a-real-handle`
against `origin/main` at 622e7c0. Output is quoted, not summarised.

## 1. The regression reproduces before the fix — PASS

The two real-tree pins run against the unfixed payload. One fails on the
attribute that does not exist yet; the other fails on the bytes, which is
the defect itself:

```
FAIL: test_no_root_handle_survives_into_the_payload
  (TestTheShippedPayloadNamesNoOwner) (handle='@mattbutlerengineering')
AssertionError: '@mattbutlerengineering' unexpectedly found in
'# Human gates (ADR-0033): required code-owner review makes the merged PR
...
* @mattbutlerengineering
docs/adr/ @mattbutlerengineering
docs/features/ @mattbutlerengineering
docs/design/ @mattbutlerengineering
' : the payload CODEOWNERS names this repo's code owner — a stamp would
install it as the target's

Ran 61 tests in 2.422s
FAILED (failures=1, errors=10)
```

The non-vacuity pin passed in that same red run: the root file does name
a handle, so the assertion above compared against something real.

## 2. The regression passes after the fix — PASS

```
$ python3 -m unittest tests.test_factory_init.TestProductCodeowners \
      tests.test_factory_init.TestTheShippedPayloadNamesNoOwner
...
Ran 10 tests

OK
```

The tenth is `test_a_comment_below_the_rules_survives`, added after the
review's Finding 1 — the first implementation dropped every comment line
rather than only the root's leading header block.

## 3. The defect's reproduction no longer reproduces — PASS

The original reproduction was a stamp into a clean target. Re-run on the
fix, the installed `.github/CODEOWNERS` is the placeholder:

```
$ python3 factory_init.py stamp <target>
factory-init: 0 problem(s)

$ cat <target>/.github/CODEOWNERS
# Code owners — stamped by factory-init. SUBSTITUTE THE PLACEHOLDER:
# replace every `@<owner>` below with a GitHub handle or team that is a
# collaborator on THIS repo.
#
# Until you do, the merge gate is inert. Required code-owner review is what
# makes the merged PR the approval record (the three-human-gates decision,
# in docs/adr/). GitHub ignores a CODEOWNERS entry naming someone who is
# not a collaborator here, and it does not tell you that it did.
#
# The explicit doc paths are the first two gates' surfaces; the fallback
# keeps every merge owner-reviewed.
* @<owner>
docs/adr/ @<owner>
docs/features/ @<owner>
docs/design/ @<owner>
```

## 4. The factory's owner handle appears nowhere in a stamped target — PASS

Not just in CODEOWNERS — anywhere in the whole stamped tree:

```
$ grep -rl "mattbutlerengineering" <target> > /dev/null 2>&1; echo $?
1
```

(`1` is grep's no-match exit. Before the fix the same command exited `0`
and listed `<target>/.github/CODEOWNERS` and its payload mirror.)

## 5. The stamped repo's own detectors stay green — PASS

The fix changes what a stamped repo is handed, so the stamped repo's own
gate is the thing that must not regress:

```
$ cd <target> && git init -q . && python3 tools/factory/gates.py
gates: 0 problem(s)
```

## 6. Full battery — PASS

```
$ python3 -m unittest discover tests
Ran 1354 tests in 21.631s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

Baseline on `origin/main` is 1344; the ten added tests are the seven in
`TestProductCodeowners` and the three in `TestTheShippedPayloadNamesNoOwner`.
The rewritten twin test was renamed, not added, so it moves no count.

## 7. Payload, root and manifest stay consistent — PASS

Detector E (manifest ↔ payload) and `TestRealTreeMirrors`
(payload ↔ `transform(root)`) both pass inside criterion 6. Exactly one
checksum moved, which is the one file whose transform changed:

```
$ git diff --stat
 docs/backlog.md                      |   2 +-
 factory/manifest.json                |   2 +-
 factory/templates/.github/CODEOWNERS |  23 ++++--
 factory_init.py                      |  86 ++++++++++++++++++--
 tests/test_factory_init.py           | 150 +++++++++++++++++++++++++++++--
 5 files changed, 240 insertions(+), 23 deletions(-)
```

## 8. The one-owner pre-pass is unchanged — PASS

Not a gate; run because a new module-level constant is exactly what it
would flag. Still nine, the same nine as before the change:

```
$ python3 one_owner.py
...
one-owner: 9 problem(s)
```

## 9. The claimed backlog seed is well-formed — PASS

The run started from `docs/backlog.md`'s existing seed, claimed in place
per the protocol's seed-backlog rule. Parsed back through the protocol's
own grammar rather than eyeballed:

```
$ python3 -c "... protocol.parse_backlog(...) ..."
line: 14
origin: feature:software-factory
claimed: maintenance:the-placeholder-that-is-a-real-handle
```

## Not verified

- **GitHub's actual behaviour.** The failure this fix addresses — GitHub
  silently ignoring a CODEOWNERS entry that names a non-collaborator, and
  reporting a syntactically invalid owner as an error — was not exercised
  against a real repository. It is asserted by the seeded blueprint,
  `docs/setup.md`, `skills/doctor/SKILL.md` and GitHub's documentation,
  and this run took it as given. Nothing here proves the gate was inert
  in any specific repo; what is proven is that the stamp lands a handle
  belonging to someone who is, in general, not the target's collaborator.
- **Repos already stamped.** No stamped repo was inspected or migrated.
  `update` leaves an existing `.github/CODEOWNERS` alone (it is not
  `is_factory_owned`), so an already-stamped repo keeps whatever it has —
  substituted or not — and this fix reaches only future stamps and
  updates into a tree with no CODEOWNERS yet.
- **The `ADR-0033` citation in already-stamped repos.** Fixed going
  forward by the new header; not backfilled anywhere.
- **`skills/doctor/SKILL.md` was not changed**, so doctor's step 8 still
  describes the check in prose rather than naming the `@<owner>` token it
  could now match mechanically. Deliberate scope call, recorded in the
  review.
