# tests/ — index

## Naming convention

- `test_<module>.py` — the primary suite pinning that root module's
  contract; `test_<module>_<facet>.py` when one module carries several
  suites (e.g. `test_cli_process_reaping.py` is cli.harness_run
  coverage). Suites over cross-cutting artifacts that no single module
  owns keep a descriptive name; their coverage is noted below.
- Shared helper modules carry **no** `test_` prefix — that is the
  marking: `python3 -m unittest discover tests` only collects
  `test_*.py`, so un-prefixed files are scaffolding, never suites.
- Flat directory, no subpackages: the discover invocation is pinned in
  the Makefile and CI, and helpers are imported by bare module name.

## Suites (filename → what it pins)

- `test_assembler.py` — assembler.py, the assembler workflow's brain
- `test_budget_guard.py` — budget_guard.py, the dollar-budget stop
- `test_charter_replay.py` — charter_replay.py below the model: decode,
  score, verdict
- `test_cli.py` — cli.py seam: failure vocabulary, harness IO,
  harness_run lifecycle
- `test_cli_process_reaping.py` — cli.harness_run's group-kill contract
  composed with real subprocesses (driven via trigger_eval)
- `test_cost_ledger.py` — cost_ledger.py, the cost-ledger seam
- `test_cost_report.py` — cost_report.py, weekly rollup + circuit breaker
- `test_design_pipeline.py` — cross-cutting: design.yml workflow, the
  web-quality make target, and the payload's design seed
- `test_eval_schema.py` — eval_schema.py, the eval-set/results seam
- `test_factory_charters.py` — file contract of factory/agents/ stubs +
  factory/charters/ (dispatchability fields, no second routing source)
- `test_factory_config.py` — factory_config.py reader and resolvers
- `test_factory_init.py` — factory_init.py stamping + payload↔root mirror
- `test_factory_roles.py` — factory_roles.py, the role-vocabulary seam
- `test_fixture_recorders.py` — tests/fixtures/*/record.py stay
  importable callers of the cli seam
- `test_gate_digest.py` — gate_digest.py, digest + gate-latency capture
- `test_gates.py` — gates.py drift detectors; also hosts the live-tree
  CI guards (TestLockstep, run-step invariant)
- `test_handoff.py` — handoff.py, the hard-stop handoff composer
- `test_knowledge_plane.py` — knowledge_plane.py typed-ID grammar + walk
- `test_label_sync.py` — label_sync.py (detector L)
- `test_lint.py` — lint.py checkers, exact problem strings
- `test_model_routing.py` — WO-0007 acceptance evidence across two
  modules: type label → charter band (assembler) → model id
  (factory_config), against the real factory.json and charter stubs
- `test_orientation_pack.py` — orientation_pack.py, the dispatch prompt
- `test_protocol_backlog.py` — protocol.py backlog-entry grammar
- `test_protocol_conformance.py` — protocol.py stage tables vs
  docs/pipeline-protocol.md prose
- `test_protocol_frontmatter.py` — protocol.read_frontmatter +
  skill-file contract (skill_path)
- `test_protocol_maintenance_orientation.py` — protocol.next_stage,
  maintenance rows, against tests/fixtures/maintenance-orientation/
- `test_protocol_orientation.py` — protocol.next_stage, product rows,
  against tests/fixtures/orientation/
- `test_sweeps.py` — sweeps.py, the intake sweeps
- `test_trigger_eval.py` — trigger_eval.run_single_query's per-run
  project-dir cleanup
- `test_trigger_eval_detection.py` — trigger_eval.detect_fired (claude
  stream-json events) + the live-pipe adapter replays
- `test_trigger_eval_detection_omp.py` — trigger_eval.detect_omp_fired
- `test_trigger_eval_run_eval.py` — trigger_eval.run_eval fan-out,
  claude-harness twin of harness_contract.RunEvalContract
- `test_trigger_eval_run_eval_omp.py` — trigger_eval.run_eval fan-out,
  omp-harness twin
- `test_trigger_eval_scoring.py` — trigger_eval score_case/summarize/
  record
- `test_validator.py` — validator.py, the validator workflow's brain

## Shared helpers (un-prefixed, defines no discovered tests)

- `cli_contract.py` — CliContract mixin: the tools' shared CLI contract
- `factory_fixture.py` — canonical factory-config fixture (CONFIG + writer)
- `fake_gh.py` — the one fake gh at cli.gh_runner's seam
- `fixture_tree.py` — shared temp fixture-tree builder
- `harness_contract.py` — RunEvalContract mixin for the run_eval twins
- `make_parse.py` — Makefile text extraction for the lockstep tests
- `workflow_parse.py` — workflow text extraction for the run-step tests
- `fixtures/` — committed fixture trees and recorded transcripts (each
  transcript family has its own README)
