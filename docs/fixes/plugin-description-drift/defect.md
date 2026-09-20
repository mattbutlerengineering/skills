---
stage: capture
run: maintenance:plugin-description-drift
date: 2026-08-23
re-entry: implement
assumptions: ["Scoped to the utility-skill list only — the description's stage prose names stages in title case rather than by slug, and restyling it is a wording decision nobody asked for", "The checker belongs in lint.py beside check_readme_skills and check_ledger rather than in gates.py — lint already owns plugin.json (check_manifest) and already owns holding docs to the taxonomy", "Completeness is the bar, not exact formatting: the checker asserts each slug appears somewhere in the description, the same substring test check_readme_skills applies to README.md"]
---

# Defect: the plugin description's utility-skill list is wrong and unchecked

Origin: backlog seed `docs/backlog.md:31` (from: session:2026-08-19),
claimed as `(claimed: maintenance:plugin-description-drift)`.

## Defect

`.claude-plugin/plugin.json`'s `description` enumerates the plugin's
utility skills in a parenthetical. It names **nine**:

    address-pr-review, audit, automate, autorun, deepen, doctor,
    factory-init, mermaid, work-queue

`protocol.UTILITY_SKILLS` holds **twelve**. Three are missing:

    animated-diagram, architecture-diagram, interactive-architecture-diagram

Expected: the description names every utility skill the taxonomy declares,
and a checker fails when it stops doing so. Observed: it names nine, and
no checker looks.

## Reproduction / Evidence

Measured against the tree at `622e7c0`:

```
=== protocol.UTILITY_SKILLS:
12 ['address-pr-review', 'animated-diagram', 'architecture-diagram', 'audit', 'automate', 'autorun', 'deepen', 'doctor', 'factory-init', 'interactive-architecture-diagram', 'mermaid', 'work-queue']
=== plugin.json description:
"...plus a /next router and utility skills (address-pr-review, audit, automate, autorun, deepen, doctor, factory-init, mermaid, work-queue)."
```

The missing-detector half, same tree — every `plugin.json` mention in the
two checker modules:

```
lint.py:24:    path = root / ".claude-plugin" / "plugin.json"
lint.py:26:        return ["missing .claude-plugin/plugin.json"]
lint.py:30:        return [f"plugin.json is not valid JSON: {err}"]
lint.py:31:    return [f"plugin.json missing field: {field}"
```

All four are inside `check_manifest`, which asserts only that `name`,
`description` and `version` are non-empty. `gates.py` never reads the file.

The battery is green on this tree — `lint: 0 problem(s) across 24 skills`
— which is the defect: the drift is real and every check passes.

## Root-cause hypothesis

**Hypothesis, not a finding.** The description was written once, by hand,
when the utility category held nine members, and the three diagram skills
joined the taxonomy later. `check_readme_skills` exists precisely because
this already happened on another surface — its own docstring records that
`interactive-architecture-diagram` "shipped undocumented" — but the fix
was applied to README.md and LEDGER.md and never to the plugin manifest.
So the likely cause is that the earlier repair was scoped to the surfaces
that were noticed, not to the class.

## Blast radius

Small, entirely user-facing, and long-standing.

- **Who:** anyone reading the plugin's description before installing —
  a marketplace listing, `claude plugin` output, or the manifest itself.
- **What:** three shipped skills are invisible on the surface a user reads
  first. Nothing malfunctions; discovery is the whole of the damage.
- **Since:** whenever the diagram skills joined `UTILITY_SKILLS`; the
  description has not been updated since it was authored.
- **Not affected:** skill resolution, routing, evals, the omp `pi.skills`
  manifest (guarded by `check_pi_package`), README.md and LEDGER.md
  (guarded by `check_readme_skills` and `check_ledger`).

Scale follows: a scoped fix, a light Review, no migration, no rollback
beyond a revert.

## Ruled out

- **Not a taxonomy bug.** `protocol.UTILITY_SKILLS` is correct at twelve
  and matches the directories under `skills/` — the ADR-0023 category is
  fine; only its restatement in the manifest is stale.
- **Not the omp manifest.** `check_pi_package` already guards the second
  packaging surface, so this is not the dual-packaging drift of ADR-0027.
- **Not a `gates.py` gap.** Detectors A/C/D read `docs/**/*.md` plus
  `CONTEXT.md` and no `.py` or `.json` file, so no detector could have
  caught this; the checker belongs in lint.
- **Not a length problem.** The description is 331 characters today, so
  naming three more skills is nowhere near any manifest limit.

## Work items

- [x] **W1** a lint checker holds the plugin description to the utility taxonomy — size:S, blocked by: —
  - Accept: a new `check_plugin_skills` in `lint.py`, wired into the checker list beside `check_readme_skills`, returns one problem string per `protocol.UTILITY_SKILLS` slug the description does not name; a test asserts the exact strings through the public interface and is watched failing on today's description (naming the three missing slugs) before any manifest edit.
- [x] **W2** the description names every utility skill — size:S, blocked by: W1
  - Accept: `.claude-plugin/plugin.json`'s description names all twelve slugs in `protocol.UTILITY_SKILLS`; `check_plugin_skills` returns zero problems; `python3 lint.py` reports `lint: 0 problem(s) across 24 skills`; the full battery stays green.

## Notes

**2026-08-23 — W1 and W2 landed in one commit, not one per item.** The
implement stage commits at item boundaries, but W1 alone is a deliberately
red tree: the checker's whole purpose is to fail on the description W2
fixes, so committing it separately would put a red `python3 lint.py` on
main between the two. The item boundary is preserved in the work above and
in the verification evidence, which records the W1 red before the W2 green.

Capture chose `re-entry: implement` over `architect`: the checker's home
is not open (lint.py already owns `plugin.json` via `check_manifest` and
already owns holding docs to the taxonomy via `check_readme_skills` and
`check_ledger`), and its shape is the established one. No contract
between components changes, so there is nothing for `architecture.md` to
decide.
