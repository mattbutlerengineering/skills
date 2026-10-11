---
stage: capture
run: maintenance:one-fence-rule
date: 2026-10-10
re-entry: architect
origin:
  - "deepen review 2026-10-10 at 25c0182, candidate 3 (Collapse gates.py's two fence walkers into one), widened during decompose's soft-gate backfill to take in validator._unquoted"
assumptions:
  - "Section set: like docs/fixes/one-fact-one-owner/defect.md, the repo's precedent for a re-entry: architect brief, this brief adds a design question, a scope and success criteria after the template's own sections. None of the template's sections is dropped or reordered."
  - "Work already in flight: checked 2026-10-10. The one open PR (#647, retiring beads) and the worktree branches do not touch fence handling. Nothing matches."
---

# Condition: one fence rule

## Defect (or Condition)

Three walkers decide which lines of a markdown document sit inside a
fenced code block. Each detector or gate that uses one treats fenced
content as quoted, not asserted. The three apply three different rules:

| Walker | Location | Closing rule | Callers |
|---|---|---|---|
| strict | `gates._fence_open` / `_fence_closes` (gates.py:1043-1061; `FENCE_OPEN`/`FENCE_CLOSE` :200-201) | same character, length ≥ opener (CommonMark) | `_walk_sections` (H, M), `_unfenced` (N, O) |
| D's | `ARCH_FENCE` (gates.py:278), walked inline in `_architecture_drift` (:535-557) | any ```` ``` ```` or `~~~` line closes any fence | detector D |
| validator's | `validator.FENCES` / `_unquoted` (validator.py:372-411) | a line starting with the opener's 3-character prefix | `run_lifecycle`'s uncited-skip gate |

Two of the three are wrong, in different ways. Detector D and the
validator's skip gate can both read quoted material as a live claim.

**Target state:** one fence rule, the CommonMark one the strict walker
already implements, owned in one place, with D and the validator reading
through it. Then the three call sites cannot disagree about what is
fenced.

## Reproduction / Evidence

Run against `main` at 25c0182 through the public entry points, read-only
on source, in scratch temp trees.

**Detector D**, `gates.check_blueprint_drift(root)` on a feature run whose
`architecture.md` is:

~~~text
# A

````markdown
```
`present.py` exists here
```
````
~~~

returns `D: docs/features/x/architecture.md:5 says present.py exists, but
it does not (architecture.md is stale)`. The same holds with a `~~~` line
nested in a ```` ``` ```` block. The same claim in a plain ```` ``` ````
block returns `[]`, and in prose it fails as designed. So D treats the
claim as inert only when no inner marker closes its fence early.

**validator**, `validator._unquoted(body)` on a body that quotes a markdown
example inside a four-backtick fence:

~~~text
````markdown
```
Closes WO-0001
```
````
after
~~~

keeps `['Closes WO-0001', 'after']`. `gates._unfenced` on the same lines
keeps `['after']`. `_unquoted`'s own comment states the intended rule,
*"Inside a fence, only its OWN marker closes it"*, but the opener is
stored as its 3-character `FENCES` prefix, so ```` ``` ```` matches a
```` ```` ```` opener.

**Incidence today: zero.** An awk scan of every tracked
`docs/**/architecture.md` found no nested mixed marker. No merged PR body
is known to have tripped the validator. This is a latent condition, not a
live outage.

## Root-cause hypothesis

Hypothesis: three authors, three dates, no shared owner. D's walker
(c25fcaa, #148) and the strict walker (fb33432, #128) both landed on
2026-07-12 in separate PRs. Neither references the other. The validator's
walker (c9c26d6, #333, 2026-09-19) was written for ADR-0064's "a quoted
token is not a claim" without reusing gates' walker, although
`validator.py` already imports `gates` (validator.py:83). No ADR, review
or fix run records a choice to differ.

## Blast radius

- **Detector D** fails `make check` on an honest `architecture.md` that
  quotes markdown in a fence. The cost is a false-red gate, and the
  workaround is rewording the doc.
- **The validator's skip gate** reads a quoted `Closes WO-####` as a
  claim. Under `--uncited skip` that turns an intended silent no-op into
  a "no Closes" problem string, or the reverse when the token resolves.
  The cost is a wrong lifecycle-label outcome on one PR.
- **Both modules are mirrored** (`factory_init.MIRRORS`), so every
  stamped product repo carries both walkers and runs them in CI.
- **Since:** 2026-07-12 for D and 2026-09-19 for the validator. No known
  occurrence.

## Ruled out

- **A deliberate difference.** Checked ADR-0064 (provisional), the
  `quoted-token-is-not-a-claim` fix run, and #148/#128. None chooses a
  different closing rule. `_unquoted`'s comment states the CommonMark
  rule and its code misses it.
- **Strict walker defects.** It handles both repros correctly, and the
  CommonMark backtick-info rule (gates.py:1049-1051) is already in it.
- **Detectors C and I's lack of fence skipping.** Whether a quoted ADR or
  PRD token is a claim is a policy question (ADR-0064 is about WO tokens
  only). It is not a closing-rule bug, so it is out of scope (see Scope).

## The design question — Architect's to answer, not capture's

Where does the one fence rule live, and what is its interface? `gates`
and `validator` already share two candidate homes:
- `gates` itself, which validator already imports;
- `knowledge_plane`, which both import, and which owns `WO_TOKEN` and
  `CLOSES_TOKEN`, the tokens whose quotedness the rule decides.

D also needs a hook the other callers do not: its ```` ```tree-claims ````
fence is read, not skipped.

## Scope

- **In:** one owner for the fence rule. Detector D and
  `validator._unquoted` read through it. The strict walker's callers
  (H, M, N, O) keep their behaviour unchanged. Payload twins and the
  manifest are regenerated.
- **Out:** fence skipping for detectors C and I and for D's citation
  scan (policy, ADR-0064's territory). Blockquote handling in
  `_unquoted`, which stays as it is. `protocol.py`'s frontmatter fence (a
  different construct; deepen candidate 4).

## Success criteria

- Both repros above produce no problem: D returns `[]` and `_unquoted`
  drops the quoted `Closes` line.
- One definition of the fence rule exists. A grep for the fence-marker
  regexes and `FENCES` finds a single owner.
- Every existing test for H, M, N, O, D and `run_lifecycle` passes
  unchanged. `python3 -m unittest discover tests`, `python3 lint.py` and
  `python3 gates.py && python3 gates.py --selftest` are green.

## Notes

- 2026-10-10: the deepen report's candidates 1 (gate-timeline read) and 2
  (work-order block) were withdrawn as a run seed during the soft-gate
  backfill. Candidate 1's `rejection_mining` refusal gap is a recorded
  deferral (`docs/fixes/a-malformed-timestamp-is-silently-dropped/release.md`,
  *Follow-up recorded, not actioned*, item 1). Candidate 2's two row
  slices serve two recorded purposes (`docs/features/software-factory/review.md:134`;
  `orientation_pack.orientation_pack` scans `wo_block` only for
  citations).
