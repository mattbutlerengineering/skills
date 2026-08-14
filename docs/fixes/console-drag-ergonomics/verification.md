---
stage: verify
run: maintenance:console-drag-ergonomics
date: 2026-08-14
---

# Verification: console-drag-ergonomics

The brief's reproduction evidence was "no reorder ever landed from the
browser" — so the regression check is exactly that flow, run by a human,
plus automated pins for the new controls. 5/5 PASS.

## 1. Controls render with the claimed/edge rules — PASS

`test_backlog_rows_carry_move_buttons` pins: ▲/▼ buttons on unclaimed
rows only (4 `data-move=` occurrences for the fixture's 2 unclaimed
rows), claimed rows unmovable, top row's ▲ and bottom row's ▼ disabled.
`test_backlog_move_button_edges_follow_list_position` pins the deviation
logged in the brief: edges are absolute list positions, so a mid-list
unclaimed row above a claimed tail keeps ▼ enabled.

## 2. Click path ≡ drag path — PASS

`test_nudge_click_moves_match_drag_moves`: `nudge` swaps with the
adjacent slot ([4,3,5] / [3,5,4] from [3,4,5]), no-ops at both edges and
on an unknown line. The wiring feeds `nudge` into the same
`state.orders`/`dirty`/save path the drop handler uses — one save
contract for both input methods.

## 3. Full battery — PASS

```
Ran 1194 tests ... OK
lint: 0 problem(s) across 23 skills
gates: 0 problem(s)
selftest: ok
```

## 4. A reorder landed from the page — PASS

The one flow the process-dashboard run shipped unverified, now observed
end-to-end: the operator moved a seed with the new controls and saved;
`docs/backlog.md` rewrote. The diff is a pure permutation — the
`next-maintenance-1` seed moved down two slots, no line edited:

```
-- The `next-maintenance-1` routing case under-triggers ... (from: session:2026-07-05)
 - omp near-miss under-triggering: ... (from: session:2026-07-05)
 - omp cannot traverse `skill://` references ... (from: session:2026-07-05)
+- The `next-maintenance-1` routing case under-triggers ... (from: session:2026-07-05)
```

Post-save gather: `problems: []`, 15 seeds parsed, the run's own
`(claimed: maintenance:console-drag-ergonomics)` marker intact.

## 5. Operator confirms the flow — PASS (qualified)

Verdict, same session: "good enough for now". Usable — the defect's
"can't tell whether it worked" is gone (the reorder demonstrably
landed) — but not polished; the residue is recorded as a retro seed,
not silently dropped.

## Not verified

- Drag-and-drop itself remains as rough as the brief describes — out of
  scope by the brief's own assumption (click-to-move is the fix, drag
  untouched).
