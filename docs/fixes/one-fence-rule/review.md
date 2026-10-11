---
stage: review
run: maintenance:one-fence-rule
date: 2026-10-10
assumptions:
  - "Severity arbitration: the owner set the goal 'complete the remaining work' and was not asked about each finding. All four findings are minor. Two were fixed in place, and the other two are deferred with reasons below."
  - "Standards filtered to domain factory (the diff touches root tools and factory/**): adr0032-one-way-mirror and stdlib-only. Neither is touched; the only import added is from an existing stdlib-only module."
---

# Review: one fence rule

## Scope

`git diff 008dd34..HEAD`: `knowledge_plane.py`, `gates.py` and
`validator.py`, their `factory/templates/tools/factory/` twins,
`factory/manifest.json`, and additions to `tests/test_knowledge_plane.py`,
`tests/test_gates.py` and `tests/test_validator.py`. The run's own
artifacts were read but not reviewed as code. I also ran
`python3 one_owner.py`. Its one hit near this diff (`READY_LABEL` in
`validator.py:96`) predates the run and is outside its scope.

## Findings

### Minor: the moved comment told a lie in its new home

- Scenario: the fence-rule comment, carried over verbatim from `gates.py`,
  ended "and an unclosed fence is reported". In `knowledge_plane.py`
  nothing reports anything; `unfenced` silently swallows the rest of the
  input. A reader of the seam would expect a report that only detector
  H's `_walk_sections` makes.
- Standard: none
- Decision: fixed. The comment now reads "(an unclosed fence is H's to
  report)".

### Minor: knowledge_plane's stated ownership list omitted its new fact

- Scenario: the module docstring lists what the module owns ("the
  typed-ID token grammar, the run-directory layout, and where a factory
  tool finds the repo root"). After the move it also owns the fence rule,
  so a reader looking for that rule would not find it in the list. A
  list like this goes stale silently.
- Standard: none
- Decision: fixed. The docstring names the fence rule.

### Minor: D's fence handling changed beyond the two repros

- Scenario: two inputs now behave differently, both following CommonMark.
  A `~~~` line inside a ```` ```tree-claims ```` block is no longer a
  closer; it is read as a claim line and reported as an unreadable tree
  claim. And a ```` ```lang ```` line inside a plain backtick fence no
  longer closes it. `architecture.md`'s *Accepted behaviour change* entry
  names only the validator's backtick-info change, not D's.
- Standard: none
- Decision: deferred, with no code change. Neither input was ever valid
  markdown: no renderer closes a backtick fence with `~~~` or with a
  marker that has an info string. On this repo's tree `python3 gates.py`
  reports 0 problems, so no committed `architecture.md` relies on the
  old behaviour. This entry is the record.

### Minor: the validator's backtick-info change has no test at the validator level

- Scenario: if `_unquoted` were rewired to a looser opener in future, a
  ```` ``` `x` ```` line would open a fence again. No `TestRunLifecycle`
  case would fail, only `TestFences`, and only if the shared rule itself
  changed.
- Standard: none
- Decision: deferred. The change is a consequence of calling the shared
  rule, which `TestFences.test_backtick_info_with_a_backtick_does_not_open`
  pins. The validator is pinned to that rule by the red-first repro case.
  A second copy of the assertion would test wiring that the closure grep
  (verification.md S2) already proves.

## Passes with no findings

- **Correctness:** both new walkers match the strict rule line for line.
  D's tree-claims opener is still recognised: `fence_open` accepts
  ```` ```tree-claims ```` because the info string has no backtick, and
  `ARCH_CLAIMS_FENCE` then marks the block. The validator still biases
  toward skipping on an unterminated fence. No caller depended on the
  removed private names (`grep` over `*.py` and `tests/`).
- **Security:** pure string functions with no new I/O, no new input
  boundary, and no new dependency. The skip gate becomes stricter about
  which lines are quoted, but only toward CommonMark, and the gate
  remains one that can only skip and never mutate.

## Verdict

Ready to ship. No critical or major findings, and no finding cites an
enforced standard.
