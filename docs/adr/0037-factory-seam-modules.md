# Factory seam modules: knowledge_plane, cli, factory_config, cost_ledger

- Status: amended by ADR-0039
- Date: 2026-07-20

Amends the "two seam modules" convention (ADR-0021 protocol.py, ADR-0022
eval_schema.py) for the factory tools. That convention's bar — multiple
real callers AND observed divergence — has now been met four times over
inside the factory plane, where the seams had silently accreted in
gates.py and assembler.py instead of getting homes of their own:

- **Typed-ID grammar and run-artifact walk.** gates.py owned PRD/ADR/WO
  token regexes, the closing-keyword grammar, `run_dirs`, and `repo_root`;
  validator.py, assembler.py, and orientation_pack.py all imported the
  detector module for them, and label_sync.py carried its own copied
  `repo_root`. The knowledge plane's shared grammar is CONTEXT.md
  vocabulary, not a detector concern.
- **CLI adapter.** label_sync.py (gh) and budget_guard.py (git) each
  hand-rolled the same runner/failure-tuple/stderr-detail triple —
  observed divergence in the copies' drift, two real callers.
- **Factory config.** assembler.py owned load_config + resolve_model;
  budget_guard.py and cost_report.py each grew a sibling resolve_* and
  imported the DISPATCHER to read a config file.
- **Cost ledger.** budget_guard.py wrote lines, detector G validated them
  in full, and cost_report.read_ledger hand-rolled a partial re-validation
  whose own docstring admitted it could diverge from G.

## Decision

Four seam modules join protocol.py and eval_schema.py as the factory's
shared-seam set, each mirrored into stamped repos like any other tool:

- **knowledge_plane.py** — the knowledge plane's shared grammar: typed-ID
  token regexes (PRD/ADR/WO, closing keywords), `run_dirs`, `repo_root`.
- **cli.py** — the one subprocess adapter: `runner(binary)`,
  `CLI_FAILURES`, `detail(err)`. Callers alias to their own names
  (GH_FAILURES, GIT_FAILURES) so their problem strings read unchanged.
- **factory_config.py** — the one reader of factory.json (`load`) and its
  fail-closed accessors (`resolve_model`, `resolve_budget`,
  `resolve_cap`). factory.json stays the single routing source of truth
  (ADR-0004); detector F remains the CI gate over the whole shape.
- **cost_ledger.py** — the append-only cost ledger's shape (ADR-0034):
  path, field set, line grammar (`parse`/`line_problems`), `entry`,
  `append`, and the report's `read`. Detector G layers its breakdown
  cross-checks on top of the same grammar.

Shared modules own their problem prefixes (`config:`, `ledger:`), the
same way validator.py surfaces label_sync's `L:` strings under its own
CLI — a caller's label names the caller, a seam's label names the seam.
Message bodies were preserved; only prefixes changed.

What deliberately did NOT move:

- **gates.pr_event stays in gates.py** — a dispatch-plane event reader
  with a documented second caller, not knowledge-plane grammar.
- **assembler.write_outputs stays in assembler.py** — cost_report's
  import of it is a known remaining wart, one caller short of the bar.
- **Problem strings stay strings.** A structured-findings layer behind
  the problem-string seam was considered and rejected: the only re-parse
  sites in the tree are two test-local string splits, no production
  caller re-parses, and the label-prefixed problem-string contract is a
  hard convention (CLAUDE.md) with exact-string tests as its evidence.
  Re-suggesting it needs a production caller that actually re-parses.
- **The ROW/TRACKER breakdown-row regexes remain per-file**
  (assembler.py, orientation_pack.py, validator.py) — same grammar, but
  each file reads a different slice through it; fold them into
  knowledge_plane only when a real divergence is observed.

`handoff.post_handoff` was deleted by the same review (a pass-through
that failed the deletion test — `post(text)` with extra steps);
`hard_stop` calls its injected `post` directly.

## Consequences

- gates.py is detectors-only; budget_guard.py and cost_report.py no
  longer import the dispatcher to read config.
- factory_init.py MIRRORS carries the four new modules; detector E pins
  them like every other mirrored tool.
- One detector-G ordering change: a ledger line's field-shape problems
  now print before its wo-has-no-breakdown-row cross-check (the seam
  yields shape problems first). Strings are byte-identical; only the
  order moved.
- factory.json's `wip_cap` is validated by detector F but read by no
  runtime code — surfaced here for honesty, left alone (YAGNI until a
  WIP-limit consumer exists).
