---
stage: architect
run: feature:pipeline-board
date: 2026-08-25
---

# Architecture: Pipeline board

## Approach

Split the board along the fact/taste seam. The facts — which runs are
active, which stage each sits on, its full ladder, Implement progress —
are stated once, by a new thin root tool `board.py` that composes the
seams that already own them (`knowledge_plane.run_dirs` for discovery,
`protocol.py` for orientation) and emits one JSON board model. The taste
— the swimlane figure ux.md sketches — lives in a new `pipeline-board`
utility skill that renders that JSON verbatim into a single theme-aware
`.svg`, built exactly like its sibling `architecture-diagram` (scaffold
asset + references, shared design tokens). The alternative shape — a
prose-only skill re-deriving orientation from the protocol doc each
invocation — loses because it makes placement parity untestable and
creates a second live deriver of a fact `protocol.py` owns (ADR-0062).
`dashboard.gather` already proves the composition (`run_dirs` +
`next_stage` → runs list); `board.py` is its offline, ladder-deep,
network-free sibling.

## Components

### protocol.py (seam extension — three public accessors)

- Responsibility: remains the one owner of orientation; newly exposes
  what it already knows: `stage_states(run_dir)` (the full per-stage
  ladder its `next_stage` walk derives internally), `checkbox_progress(
  path)` (counts from the checkbox grammar it owns), and `run_ref(root,
  run_dir)` (the run-ref vocabulary its own backlog grammar already
  parses — lifted from `dashboard._run_ref`, which becomes a caller).
- Collaborators: none new inward; `board.py`, `dashboard.py`, tests
  outward.

### board.py (new root tool, thin caller)

- Responsibility: state the board's facts once — discover runs, filter
  to active, orient each via `stage_states`, attach Implement progress,
  catch per-run orientation failures into an attention list, sort
  furthest-along-first, stamp the snapshot time, emit JSON.
- Collaborators: `knowledge_plane.run_dirs`, `protocol.py` accessors.
  Deletion test: remove it and the feature is gone — nothing else
  composes ladders, progress, attention, and order.

### skills/pipeline-board/ (new utility skill — the humble renderer)

- Responsibility: turn the JSON model into the ux.md swimlane figure —
  one self-contained `.svg`, warm-paper light with `prefers-color-scheme`
  dark, written to a temporary location and opened, never committed. It
  derives no placement: `board.py`'s output is the only fact source, and
  a tool failure stops the render (ADR-0062).
- Collaborators: `board.py` (invoked relative to the skill's base
  directory), `assets/boilerplate.svg` (board scaffold: header, lane
  grid, capture-span, attention strip, legend — sibling pattern),
  `references/board-grammar.md` (lane geometry, glyphs, JSON key
  reference), and `../architecture-diagram/references/design-system.md`
  as the one owner of the family's visual tokens.

### Registration surfaces (existing checkers, new rows)

- Responsibility: make the skill exist for lint and users:
  `protocol.UTILITY_SKILLS` entry, README and LEDGER rows
  (`check_readme_skills` / `check_ledger` enforce), plugin description,
  and a plugin version bump (the vendored cache is version-gated;
  unchanged versions ship stale skills).

## Data model

One entity: the board model, serialized JSON, rebuilt from scratch every
invocation (access pattern: one full read of run state per invocation;
consistency: point-in-time snapshot — the header timestamp is the
staleness contract, so no coordination is needed).

```json
{
  "generated": "2026-08-25T09:47:00-07:00",
  "repo": "skills",
  "runs": [
    {
      "ref": "maintenance:one-labels-walk",
      "kind": "maintenance",
      "slug": "one-labels-walk",
      "dir": "docs/fixes/one-labels-walk",
      "ladder": [
        {"stage": "capture", "state": "done"},
        {"stage": "architect", "state": "done"},
        {"stage": "implement", "state": "done"},
        {"stage": "verify", "state": "done"},
        {"stage": "review", "state": "done"},
        {"stage": "ship", "state": "done"},
        {"stage": "operate", "state": "current"}
      ],
      "progress": null
    }
  ],
  "attention": [
    {"dir": "docs/fixes/broken-run",
     "reason": "defect.md has no re-entry: field"}
  ]
}
```

- `state` ∈ `done | current | ahead | skipped`; each run's `ladder` is
  its own (maintenance rows carry capture and honor `re-entry:`; feature
  rows honor the `ux:` conditional as `skipped`). The invariant "exactly
  one `current` per run, and it equals `next_stage`" is owned by
  `stage_states` and pinned by a test.
- `progress` is `{"done": n, "total": m}` only when `current` is
  implement, else `null`.
- `runs` is pre-sorted furthest-along-first (position of `current` in
  the run's own ladder, descending; ties by slug) — order is a fact the
  tool owns, not a renderer choice.
- A run appears in `runs` or `attention`, never both, never neither
  (active runs only; completed runs are absent by the PRD).

## Interfaces & contracts

### protocol.stage_states(run_dir)

- Input: a run directory path.
- Output: ordered list of `(stage, state)` per that run's own ladder.
- Failure modes: raises on an unreadable/undecidable run (same
  exceptions its private walk raises today); callers catch per run.
  Invariant with `next_stage` pinned by a unit test.

### protocol.checkbox_progress(path) / protocol.run_ref(root, run_dir)

- Input: a breakdown-bearing file; a repo root + run dir.
- Output: `(checked, total)` with `(0, 0)` for a missing file; a
  protocol run-ref string (`product`, `feature:<slug>`,
  `maintenance:<slug>`).
- Failure modes: none beyond OS read errors, which propagate.

### board.py CLI

- Input: optional repo root argument, default `.`. Read-only, local
  filesystem only, no network; idempotent, retry always safe.
- Output: the board model JSON on stdout; exit 0 — including with zero
  active runs (an empty board renders honestly; empty is not an error).
- Failure modes: exit 1 with a `board:`-prefixed problem string when
  the root has no `docs/` tree or it is unreadable (problem-string
  convention). Per-run failures never abort: they become `attention`
  entries with one-line reasons.

### The render contract (SKILL.md prose)

- Input: `board.py` stdout, taken verbatim; ux.md's approved sketch;
  the shared design tokens.
- Output: one self-contained `.svg` (no external requests; fonts per
  the design system's embedded/fallback rule), written outside the
  repo's tracked tree and opened for the user.
- Failure modes: nonzero `board.py` exit → surface the problem string
  and stop; never draw from guessed state. Malformed/missing JSON keys
  → same rule.

## Stack & dependencies

- Python 3 stdlib only — the repo's hard convention; no new deps.
- SVG with `prefers-color-scheme` — the still-figure family convention
  (architecture-diagram); embeds anywhere an image does.
- unittest + lint + gates — `board.py` and the protocol accessors are
  repo code like any other (ADR-0062); the one-owner pass covers them.

## Decisions & alternatives

- **Script-stated facts** over prose re-derivation — parity becomes a
  test, orientation keeps one owner (ADR-0062).
- **stage_states in protocol.py** over board.py importing the private
  completion helpers or re-walking the artifact tables — the seam's
  knowledge stays inside the seam; privates stay private.
- **SVG** over HTML — family convention, image-embeddable, and the
  aesthetic-gap risk leans on proven in-house tokens; HTML's easier text
  flow matters little when generation computes layout anyway.
- **Shared design tokens** over a board-tuned copy — one owner of the
  family look; the board's reference adds only board-specific grammar.
- **New board.py** over extending dashboard.py (the console drags in a
  server, gh, and the cost ledger; the board is offline and single-shot)
  or giving protocol.py a CLI (seam modules stay import-only).
- **Lift run_ref into protocol.py now** (dashboard folded to call it)
  over shipping a third private copy — two real callers exist at fold
  time; shipping a known duplicate the day after building the
  duplicate-finder fails the review the repo itself prescribes.
  `dashboard.gather`'s inline active-run filter is the same class but
  stays untouched this run (surgical-change discipline) — recorded here
  as a later fold candidate, not folded silently.
- **Agent-rendered SVG from a scaffold** over a Python SVG writer — a
  script renderer would make layout a second, heavier code owner of what
  the design system + boilerplate already state; the family's rendering
  convention is prose+assets, and the aesthetic checklist (Verify)
  covers output quality.

## ADRs

- [ADR-0062 — A skill that states repo facts runs a shipped tool](../../adr/0062-a-skill-that-states-repo-facts-runs-a-shipped-tool.md)
  (accepted; confirmed live at this run's architect interview).
