# Plan 017: First real maintenance run — fix the stamped-CODEOWNERS gate bug through the pipeline itself

> **Executor instructions**: This is a **dogfood/spike plan**, not a
> mechanical fix plan. It is best driven by the repo owner (or an agent
> session the owner supervises), because its purpose is twofold: land the
> fix AND exercise the never-yet-used maintenance run scale, recording
> what the skills get wrong. If you are an unattended executor with no
> ability to run the pipeline skills interactively, STOP — execute only
> the "Fix specification" section below as a normal change, and say in
> your report that the dogfood half was skipped.
>
> **Drift check (run first)**: `git diff --stat 2e63a04..HEAD -- factory_init.py factory/templates/.github/CODEOWNERS tests/test_factory_init.py LEDGER.md docs/backlog.md`
> On any mismatch with the excerpts below, compare before proceeding;
> a conflicting change to the CODEOWNERS handling is a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M–L (the run is the work; the fix itself is S)
- **Risk**: LOW (a real run either works or produces findings — both are
  the point)
- **Depends on**: plans/016-stamp-path-constraints.md (same file —
  `factory_init.py`; land 016 first, rebase this on it)
- **Category**: direction (dogfood) + security (the fix it carries)
- **Planned at**: commit `2e63a04`, 2026-08-02

## Why this matters

Two birds, deliberately one stone:

1. **The defect is real and gate-critical.** The template payload ships
   `.github/CODEOWNERS` hardcoding `* @mattbutlerengineering`, and
   `factory_init.py stamp` installs it byte-for-byte. ADR-0033's three
   human gates ARE "CODEOWNERS + required code-owner review" — in a
   stamped repo where that handle isn't a collaborator, GitHub silently
   ignores the entry and all three gates stop binding while everything
   reports green. The repo's own backlog already captured this
   (`docs/backlog.md`, last seed).
2. **The maintenance run scale has never happened.** ADR-0025 defines
   it, `docs/pipeline-protocol.md` gives it a full orientation table,
   `capture` ships as a skill — and `LEDGER.md` shows `capture` at
   **draft** with no evidence, no `docs/fixes/` run exists anywhere, and
   the router's maintenance routing case fails its trigger eval.
   Running this defect through capture → … → operate produces the first
   real maintenance run, legitimately graduates `capture` past draft
   (LEDGER graduates ONLY via real runs — never fabricate), and
   stress-tests the weakest routing path with a real case.

## Current state

- `factory/templates/.github/CODEOWNERS`:

  ```
  # Human gates (ADR-0033): required code-owner review makes the merged PR
  # the approval record. ...
  * @mattbutlerengineering
  docs/adr/ @mattbutlerengineering
  docs/features/ @mattbutlerengineering
  docs/design/ @mattbutlerengineering
  ```

- `factory_init.py stamp(source, target)` — installs every manifest
  entry; **no substitution step exists**; also
  `clashes` refuses ANY existing destination file, so a repo that
  already has a correct CODEOWNERS cannot be stamped at all.
- Pipeline facts (from `docs/pipeline-protocol.md`): a maintenance run
  lives in `docs/fixes/<slug>/`, seeded by `defect.md` with
  `re-entry: implement` (scoped fix; breakdown inline as checkboxes in
  defect.md) or `re-entry: architect`. Verify is **never skippable** —
  the regression test is the point. The backlog seed is claimed by
  appending `(claimed: maintenance:<slug>)` to its line, never
  rewriting it.
- `LEDGER.md` row: `| capture | draft | — | — |` — update only from the
  run's reality.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Full local gate | `make check` | exit 0 |
| This suite | `python3 -m unittest tests.test_factory_init -v` | all pass |
| Skill entry | invoke the `capture` skill (or `/next` and let it route) | interview starts |

## The run protocol (the dogfood half)

1. **Capture.** Invoke `capture` with this defect. Slug suggestion:
   `codeowners-owner-substitution`. Expect a defect brief at
   `docs/fixes/codeowners-owner-substitution/defect.md` with
   `re-entry: implement` (this is a scoped fix — no architecture
   change) and the inline checkbox breakdown. Claim the backlog seed:
   append `(claimed: maintenance:codeowners-owner-substitution)` to its
   line in `docs/backlog.md`.
2. **Implement** the checkboxes per the Fix specification below.
3. **Verify.** `verification.md` with literal command output as
   evidence — detector H gates exactly this artifact; every verdict
   needs its output shown. The regression test (step 2 of the fix spec)
   is the non-negotiable center.
4. **Review / Ship / Operate** scaled to blast radius per the protocol
   (small: this is one tool + one template). Operate's `retro.md`
   closes the run — record in it every place a skill's instructions
   were wrong, ambiguous, or fought the maintenance scale. That list is
   this plan's second deliverable.
5. **LEDGER.** Graduate `capture` to `used-once` citing this run.
   If other exercised skills were already `used-once`, extend their
   evidence only if this run genuinely exercised them.
6. **Optional (owner's call):** bank the finished run tree as the first
   maintenance-scale eval fixture under `evals/fixtures/` following the
   existing fixture layout (`ls evals/fixtures/` to see the pattern —
   all current ones are feature-scale).

## Fix specification (the implement step's content)

1. **Templatize the owner.** In
   `factory/templates/.github/CODEOWNERS`, replace all four
   `@mattbutlerengineering` occurrences with the placeholder
   `@FACTORY_OWNER` (keep the comment block).
2. **Substitute at stamp time.** In `factory_init.py`:
   - `stamp(source, target, owner=None)` — new required-for-CLI owner:
     the CLI form becomes `stamp <target> --owner <github-login>`;
     a missing/empty owner is a `factory-init:` problem, not a default.
   - When installing the CODEOWNERS file (and ONLY that file —
     substitution is not a general template mechanism), write it with
     `@FACTORY_OWNER` replaced by `@<owner>`. The **pristine mirror**
     copy under `factory/<rel>` keeps the placeholder (it must stay
     byte-identical to the manifest checksum); only the **installed**
     copy at `.github/CODEOWNERS` is substituted.
   - Refuse to finish if any installed file still contains
     `@FACTORY_OWNER` (belt and braces: catches a second placeholder
     file appearing later).
   - Note: this repo's own root has no `.github/CODEOWNERS` from the
     payload (this repo is the factory, not a stamped product) — the
     template's placeholder is the only copy to touch.
3. **Regression tests** in `tests/test_factory_init.py`:
   - stamp with `owner="someone"` → installed `.github/CODEOWNERS`
     contains `* @someone` and **no** `@FACTORY_OWNER`, while
     `factory/templates/.github/CODEOWNERS` in the stamped mirror still
     carries the placeholder.
   - stamp with no owner → exact problem string, nothing written.
   - a test asserting no literal `@mattbutlerengineering` exists
     anywhere under `factory/templates/` (pins the defect closed).
4. **Manifest.** The template edit changes payload bytes:
   `python3 factory_init.py update-manifest`, commit the manifest with
   the change (detector E).
5. `README.md`/docs: if any doc describes the stamp CLI's usage line,
   update it to show `--owner` (grep `stamp <target>` across
   `README.md docs/`).

## Scope

**In scope**: `factory/templates/.github/CODEOWNERS`, `factory_init.py`,
`tests/test_factory_init.py`, `factory/manifest.json` (via
update-manifest), the run's own artifacts under
`docs/fixes/codeowners-owner-substitution/`, `docs/backlog.md` (claim
line only), `LEDGER.md` (evidence rows only), `plans/README.md`.

**Out of scope**: relaxing the no-overwrite stamp rule for repos that
already have a CODEOWNERS (real, but a separate decision — record it in
the retro as a seed if it bites); any upgrade-leg work for already-
stamped repos; all other backlog seeds.

## Git workflow

- Branch: `advisor/017-codeowners-maintenance-run` (or the branch the
  pipeline skills choose — the run's convention wins; record which).
- Conventional commits; the run's artifacts commit alongside the code
  per the pipeline's own guidance.
- Do NOT push or open a PR unless the operator instructed it.

## Done criteria

- [ ] `make check` exits 0
- [ ] `grep -rn "mattbutlerengineering" factory/templates/` → no matches
- [ ] Stamp-with-owner and stamp-without-owner tests pass
- [ ] `docs/fixes/codeowners-owner-substitution/` contains `defect.md`,
      `verification.md`, `review.md`, `release.md`, `retro.md` (the
      maintenance orientation table, complete)
- [ ] `LEDGER.md` `capture` row is `used-once` citing this run
- [ ] The backlog seed line carries the `(claimed:)` marker
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- Plan 016 has not landed (this plan edits the same `stamp` code).
- The pipeline skills route the defect somewhere that contradicts
  `docs/pipeline-protocol.md`'s maintenance table — that IS a finding;
  record it in the retro and stop rather than forcing artifacts into
  the wrong shape.
- The fix turns out to require `re-entry: architect` (it should not —
  if it does, the capture interview learned something this plan missed;
  report before proceeding).
- Anything tempts you to edit `LEDGER.md` beyond what the run actually
  evidenced — eval honesty is non-negotiable.

## Maintenance notes

- The retro's list of skill frictions is input to the wayfinder
  factory-evolution map's decisions — hand it to the owner rather than
  fixing skills inline (surgical-change discipline).
- Follow-up seeds this run may generate: stamp-onto-existing-CODEOWNERS
  policy; a `factory_init upgrade` leg (already surfaced as an
  unplanned direction finding in `plans/README.md`).
- Reviewer should scrutinize: the pristine-mirror copy keeps the
  placeholder (checksum integrity) while only the installed copy is
  substituted — the two copies *should* differ after a stamp, which is
  new behavior worth a comment in `stamp`.
