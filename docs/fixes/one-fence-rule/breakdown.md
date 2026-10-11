---
stage: decompose
run: maintenance:one-fence-rule
date: 2026-10-10
---

# Breakdown: one fence rule

Progress lives in the checkboxes below. Implement checks items off as
their acceptance criteria are met. Source: `architecture.md` in this
directory (2026-10-10). Cut reviewed and accepted by the owner,
2026-10-10.

`knowledge_plane.py`, `gates.py` and `validator.py` are all identity
mirrors (`factory_init.MIRRORS`). Every item that edits one copies it to
its `factory/templates/tools/factory/` twin and runs
`python3 factory_init.py update-manifest` in the same commit
(docs/kb/manifest-regen.md: delete stray `.orig`/`.rej` files first).

## Milestone 1: the fence rule has one owner (no behaviour change)

- [ ] **Move the strict walker into knowledge_plane** — `FENCE_OPEN`, `FENCE_CLOSE`, `fence_open`, `fence_closes` and `unfenced` become public in `knowledge_plane.py`; gates' `_walk_sections` (H, M) and N/O import them, and gates no longer defines them
  - Accept: a new `TestFences` in `tests/test_knowledge_plane.py` passes. It covers `~~~` nested in a backtick fence, a three-backtick line nested in a four-backtick fence, a closer at least as long as the opener closing it, the backtick-info rule, leading whitespace, and an unterminated fence swallowing the rest of the input. `TestEvidenceHonesty`, `TestCaptureCompleteness`, `TestNeedsClarification` and `TestPrdCoverage` in `tests/test_gates.py` pass with no edits. The twins are synced, the manifest is regenerated, and `python3 gates.py && python3 gates.py --selftest` is green.
  - Blocked by: —

## Milestone 2: detector D stops reading quoted claims

- [ ] **D tracks fences through `fence_open`/`fence_closes`** — `_architecture_drift` keeps `ARCH_CLAIMS_FENCE` to recognise the tree-claims block and deletes `ARCH_FENCE`
  - Accept: two new `TestArchitectureDrift` cases are written first and watched fail on today's code: a quoted `exists here` claim after a `~~~` line inside a three-backtick fence, and the same claim inside a four-backtick fence that quotes a three-backtick block (`defect.md`'s repro). Both return no D problem after the change. The existing tree-claims, prose and plain-fence cases pass with no edits. The twin is synced and the manifest regenerated.
  - Blocked by: Move the strict walker into knowledge_plane

## Milestone 3: the validator's skip gate stops reading quoted claims

- [ ] **`_unquoted` tracks fences through `fence_open`/`fence_closes`** — blockquote stripping stays local, and `validator.FENCES` is deleted
  - Accept: a new `TestRunLifecycle` case is written first and watched fail on today's code: a body whose only `Closes` work-order line sits after an inner three-backtick line inside a four-backtick fence is a silent no-op under `uncited="skip"` (`problems == []`, no gh calls). The existing tilde-fence, blockquote, unterminated-fence and inline-backtick cases pass with no edits. The twin is synced and the manifest regenerated.
  - Blocked by: Move the strict walker into knowledge_plane

## Closure

- [ ] **Prove one owner** — confirm the condition is gone, not just the three items checked off
  - Accept: `grep -nE '^(FENCE_OPEN|FENCE_CLOSE|ARCH_FENCE|FENCES) *=' *.py` lists definitions in `knowledge_plane.py` only. Both `defect.md` repros, re-run against the changed tree, print no problem. `python3 -m unittest discover tests`, `python3 lint.py`, `python3 gates.py` and `python3 gates.py --selftest` are all green.
  - Blocked by: D tracks fences through `fence_open`/`fence_closes`; `_unquoted` tracks fences through `fence_open`/`fence_closes`

## Design gaps found

None.

## Notes

- No test dies. No test calls the private walkers (`_fence_open`, `_fence_closes`, `_unfenced`, `_unquoted`) directly; checked by grepping `tests/` on 2026-10-10. Coverage moves only by addition: `TestFences` at the new interface, plus one red-first case each for D and the validator.
- Milestones 2 and 3 are independent of each other and can land as separate PRs once milestone 1 merges. Each is a revertible behaviour change on its own.
- Out of scope, per `defect.md`: fence skipping for detectors C and I and for D's citation scan (ADR-0064 policy), and `protocol.py`'s frontmatter fence.
