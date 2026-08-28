---
stage: capture
run: maintenance:the-placeholder-that-is-a-real-handle
date: 2026-08-28
re-entry: implement
assumptions:
  - The placeholder token is `@<owner>` rather than a plausible-looking
    handle such as `@YOUR-HANDLE` — angle brackets are not legal in a
    GitHub handle, so the token can never be squatted by a real account,
    and GitHub surfaces it as a CODEOWNERS syntax error instead of
    silently ignoring one unknown name. Loud is the whole point, since
    silence is the bug.
  - The product-repo header names the three-human-gates decision instead
    of numbering it. The root header cites `ADR-0033`, which is this
    repo's numbering, while the seeded blueprint files the same decision
    as `0005`. Naming it avoids both a dangling citation in the stamped
    repo and a second owner of the seed's numbering in `factory_init.py`.
---

# Defect: the stamped placeholder is a real GitHub handle

## Defect

`factory_init.MIRRORS` mirrors `.github/CODEOWNERS` into the template
payload through the `identity` transform:

```
    (".github/CODEOWNERS", ".github/CODEOWNERS", identity),
```

justified by the comment above the table:

```
# .github/CODEOWNERS is the
# human-gate surface (ADR-0033), identical in both repos, so it mirrors
# verbatim like the workflows.
```

It is not identical in both repos. It names *this* repo's code owner, and
`factory-init stamp` installs it at `.github/CODEOWNERS` in the target —
`payload_copies` resolves an install destination for every manifest key,
and `templates/.github/CODEOWNERS` is not one of the `PRISTINE_PREFIXES`
that stay factory-owned.

Five other surfaces in this same repo state the opposite — that what
lands is a *placeholder*:

- the seeded blueprint, `factory/templates/docs/adr/0005-three-human-gates.md`:

  > `.github/CODEOWNERS` is load-bearing. If its handle is not a
  > collaborator on this repo, GitHub ignores the entry and gate 3
  > silently goes inert — substitute the stamped placeholder before
  > trusting the gate.

- `gates.py`, explaining why CODEOWNERS is deliberately *outside* the
  pristine set detector E compares:

  > `.github/CODEOWNERS` ships a placeholder owner that SHOULD be
  > substituted

- `factory_init.py` itself, twice — the module docstring for `update`
  ("leave every other existing file alone — budgets, the code-owner
  handle and the doc seeds are the repo's") and the `FACTORY_OWNED`
  comment ("Everything else the stamp lands is the product repo's to
  edit — budgets, the code-owner handle, the doc seeds").

- `docs/setup.md`'s post-stamp verify checklist, which even counts them:

  > **`.github/CODEOWNERS` owner substituted.** The template ships a
  > placeholder handle on four paths. If it is not a collaborator on the
  > target, GitHub silently ignores the entry and the code-owner gate
  > goes inert.

- `skills/doctor/SKILL.md` step 8 — the diagnostic whose whole job is
  catching this:

  > **CODEOWNERS is substituted.** The template ships a placeholder owner
  > on every path. If it still names the template's owner and that handle
  > is not a collaborator here, GitHub silently ignores the entry and the
  > code-owner gate goes inert — replace it with this repo's actual owner
  > or team.

So the repo has decided, in six places, that the code-owner handle
belongs to the product repo. Doctor's step 8 is the sharpest of them: it
knows the exact failure mode, and without a distinguishable placeholder
token its check can only ever be a human squinting at a handle and asking
whether it is theirs or the factory's. The transform that produces the file did not
get the message, and the stamped artifact carries no marker of any kind —
nothing a reader, a reviewer, or a grep can catch.

## Why it matters

Gate 3 is the merge gate. Under ADR-0036 it is no longer a
human-hands-on-merge gate, which makes the *code-owner review requirement*
the one physical control still standing on the merge path — the ADR says
so plainly: "The independent-review requirement is now load-bearing, so
its integrity ... is a security property, not a nicety."

In a stamped repo owned by anyone else, `@mattbutlerengineering` is not a
collaborator. GitHub ignores a CODEOWNERS entry naming a non-collaborator.
There is no error, no annotation, no failing check: required code-owner
review simply never triggers, and every PR in that repo is mergeable by
its author. The repo's own blueprint tells its reader the gate is
enforced. Its own `make check` is green. The seeded ADR names this exact
failure — "gate 3 silently goes inert" — as the thing the placeholder
exists to prevent, and then the stamp does not ship one.

It also leaks this repo's owner handle into every repo the factory
scaffolds, which is wrong even where nobody is trusting the gate.

## Reproduction

Stamped a clean target from `origin/main` (622e7c0):

```
$ python3 factory_init.py stamp /tmp/.../stamp-target
factory-init: 0 problem(s)
stamp exit=0

$ cat /tmp/.../stamp-target/.github/CODEOWNERS
# Human gates (ADR-0033): required code-owner review makes the merged PR
# the approval record. The explicit doc paths are the gate-1/gate-2
# surfaces; the fallback keeps every merge owner-reviewed until classes
# graduate to auto-merge on data.
* @mattbutlerengineering
docs/adr/ @mattbutlerengineering
docs/features/ @mattbutlerengineering
docs/design/ @mattbutlerengineering
```

The target's own blueprint, landed by the same stamp, is the file that
calls this a placeholder:

```
$ grep -rl placeholder /tmp/.../stamp-target | sed 's|.*stamp-target|<target>|'
<target>/tools/factory/gates.py
<target>/docs/design/design-system.md
<target>/docs/adr/0005-three-human-gates.md
<target>/factory/templates/tools/factory/gates.py
<target>/factory/templates/docs/design/design-system.md
<target>/factory/templates/docs/adr/0005-three-human-gates.md
```

A second, smaller symptom of the same verbatim mirror: the stamped
header cites `ADR-0033`, a number the stamped repo does not have — its
blueprint files that decision as `0005`. Nothing catches that either:
detector C's dangling-token scan walks `_scannable_files`, which is
`docs/**/*.md` plus `CONTEXT.md`, so `.github/` is outside its universe.
`tests/test_factory_init.py::TestSeededADRs` states the rule the header
breaks — "cite upstream decisions by name or link, never by bare token" —
and enforces it only inside the ADR seed directory.

`update` does not re-introduce the handle into a repo that already
substituted it (`.github/CODEOWNERS` is not `is_factory_owned`, so an
existing copy is kept and reported). The defect enters at `stamp`, and at
`update` into a tree that has no CODEOWNERS yet.

## Why the tests did not catch it

`tests/test_factory_init.py` pins the mirror in two places, and both pin
the wrong question:

- `test_every_mirror_lands_as_its_transform_of_the_root_file` asserts
  `payload == transform(root)` for every entry. It is a *staleness* pin —
  it catches a root edit that never reached the payload — and it is
  satisfied by whatever the transform happens to be, including the wrong
  one.
- `test_codeowners_lands_verbatim_and_the_makefile_in_product_form`
  asserts the payload CODEOWNERS is byte-identical to the root's. That
  test does not merely miss the defect; it *encodes* it as the
  requirement.

Neither test, and nothing else in the suite, ever asks whether the bytes
that land are right *for the target repo*. The four surfaces that say
"placeholder" are prose, and no test reads prose. Detector E is
deliberately blind here too — `PRISTINE_PREFIXES` excludes CODEOWNERS
precisely because it is expected to be edited downstream, so the one
mechanism that compares stamped bytes is switched off for this file by
design.

## Fix

Give `.github/CODEOWNERS` a real MIRRORS transform, symmetric with the
Makefile's: `product_codeowners` swaps the root's header comment for a
product-repo one that names the substitution, and rewrites every `@handle`
on a rule line to the placeholder `@<owner>`. The root file stays correct
for this repo; the payload becomes an artifact that cannot be mistaken for
finished.

## Breakdown

- [x] A test asserting the payload CODEOWNERS names no handle from the
      root and carries a substitution instruction — RED against
      `identity`.
- [x] `PRODUCT_CODEOWNERS_HEADER` + `product_codeowners`, and the MIRRORS
      entry switched to it.
- [x] Regenerate the payload and manifest via
      `python3 factory_init.py update-manifest`.
- [x] Replace the byte-identity twin assertion with the transform's real
      contract, keeping the generic `payload == transform(root)` pin.

## Notes

- **Origin: a backlog seed**, found after the diagnosis was already
  written and independently confirming it — `docs/backlog.md`:
  "The CODEOWNERS template hardcodes `* @mattbutlerengineering` and
  factory-init stamps it byte-for-byte, so in a repo where that handle is
  not a collaborator GitHub ignores the entry and the ADR-0033 code-owner
  gate goes inert — factory-init needs an owner-handle substitution
  (from: feature:software-factory)". Claimed in place for this run.

- Checked and dropped: adding a detector that fires in a stamped repo
  whose CODEOWNERS still names the factory's owner. It is the strongest
  remedy — the stamped repo's own `make check` would go red until the
  handle is substituted — but it lives in `gates.py`, contended by open
  PRs #320 and #328. Recorded for a later run rather than built here.
- Checked and dropped: `factory/templates/docs/adr/0005-three-human-gates.md`
  states the pre-ADR-0036 rule ("No agent merges its own work", gate 3 as
  an unconditionally human gate) and teaches the class-graduation
  relaxation path that ADR-0036 says was *not* how the decision was
  actually made. That is a genuine question about what a seeded blueprint
  should default to — a conservative human-merge default in a fresh repo
  is defensible — and it is a governance call, not a defect. Left alone;
  it is also a `docs/adr/**`-class question and so a human gate-2 matter.
- Observed, not fixed: `tests/test_factory_charters.py`'s stale-merge-
  phrase pin covers `factory/CHARTERS.md`, the charters and the agent
  stubs, but not `factory/skills/<role>/SKILL.md` — historically the same
  surface carried the same pre-amendment shorthands. The live skills are
  clean, so this is a pin gap, not a live defect.
