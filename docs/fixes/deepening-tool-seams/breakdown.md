---
stage: decompose
run: maintenance:deepening-tool-seams
date: 2026-08-18
assumptions:
  - "The cut was not reviewed live — this run is driven from autorun-brief.md, so the milestone lines, the item sizes and the ordering below are read out of architecture.md's four items and its Tests section rather than from the operator's judgment. A mis-sized row is a note to log at implement time, not a design change."
  - "No closing milestone for the payload mirror. The design says one update-manifest run covers the change, and one commit per item is what this run does; detector E and tests/test_factory_init.py's payload-vs-root pin both fire the moment a mirrored root file changes without a regenerated payload and manifest. So the regeneration lives inside every item that touches a factory_init.MIRRORS entry, and no item defers it — a deferred manifest is a red battery at that commit."
  - "A1 pairs the new suite with the seam in one item. architecture.md's Tests section states that TestGhRead cannot pass before cli.gh_read exists and lands red on the same commit as it, so the ordering rule is served inside the item — the suite is written and watched to fail first — with the eight existing per-caller suites as the net that must pass unchanged across every later move. B1, B2 and D1 do land their pins against today's code as items of their own."
  - "mirror_map's test ordering is not stated in the design's Tests section. B2 and B6 apply the same rule the other three items carry — pin it at the intended interface against today's code first, move it second, and delete the superseded case in the same change that moves it."
---

# Breakdown: one owner each, four times

Progress lives in the checkboxes below. Source is `architecture.md` in this
directory, which designed four items against evidence walked at commit
`fbfa3c3`. Rows carry an item id, a size class (ADR-0034 vocabulary) and
blocking edges; they carry no work-order id and no tracker reference — the
brief rules out tracker interaction for this run, so these checkboxes are
the whole state (ADR-0026).

**The ordering rule, which decides the cut.** New tests at the intended
interface land FIRST, against today's code — they will be awkward, and that
awkwardness is the measurement. The deepening happens next, with those
tests as the net. The superseded shallow-module tests die LAST, in the same
change that deepens, with the diff saying which coverage moved where. So
every pin item precedes its move item, and no deletion of superseded tests
is a cleanup item of its own — read `A1 → A6`, `B1 → B5`, `B2 → B6`,
`D1 → D2` and the single red-to-green inside `C1` as that rule in the
commit history.

**The battery is green at every item.** `python3 -m unittest discover
tests`, `python3 lint.py` (`lint: 0 problem(s)`) and `python3 gates.py &&
python3 gates.py --selftest` (`gates: 0 problem(s)`, `selftest: ok`). Where
an item touches a `factory_init.MIRRORS` entry, `python3 factory_init.py
update-manifest` runs and the regenerated payload plus manifest are part of
that same commit — otherwise detector E fires on the manifest and
`tests/test_factory_init.py` fires on the payload twin, and the item cannot
close.

**The one thing that must not happen.** Every existing exact-string
assertion passes unchanged across these moves, with one stated exception
(B4). An exact-string test that needs editing anywhere else is the signal
to revert the move, not to edit the test.

## Milestone A: the gh-listing ritual has one owner (fourteen call sites, one entry point; the limit sent and the limit checked are the same number by construction)

Item 1 of the design. `cli.gh_json` (cli.py:315) and `cli.full_window`
(cli.py:337) are two shallow halves of one operation, so the composition —
window constant, matching `--limit`, failure catch, full-window check,
label prefix — is retyped at fourteen sites in eight modules, and
`LIST_WINDOW` is declared seven times. `cli.gh_read` absorbs both halves;
per-tool window values stay per-tool and travel as `window=`. Seven of the
nine touched modules are MIRRORS entries (`cli.py`, `label_sync.py`,
`validator.py`, `assembler.py`, `gate_digest.py`, `rejection_mining.py`,
`work_queue.py`); `dashboard.py` and `sweeps.py` mirror nothing.

- [x] **A1** land `cli.gh_read` beside the halves it will replace — size:M, blocked by: —
  - Accept: `TestGhRead` in tests/test_cli.py covers the contract's five failure modes (gh failed, unparseable JSON, wrong shape, full window, clean read), `label=None` leaving problems unprefixed, `window` reaching gh as a trailing `--limit <window>` asserted on the exact argv the fake runner receives, `truncated` true only on a full window, and `full_note` replacing the shared sentence. Each case is written and watched to fail against today's code before the seam is written. `gh_json`, `full_window`, `TestGhJson` (tests/test_cli.py:129) and `TestFullWindow` (:156) are untouched and green; no caller changes in this item. `cli.py` is a MIRRORS entry, so the payload twin and the manifest are regenerated in the same commit and detector E is green.
- [ ] **A2** the two single-site callers: validator and assembler — size:S, blocked by: A1
  - Accept: validator.py:323 reads through `cli.gh_read` with `expect=dict` and no window; assembler.py:259 reads through it with `window=` its own `LIST_WINDOW` (assembler.py:60), and neither module embeds a window in a `--limit` argument any more. assembler's copied drift-warning comment (assembler.py:57-59) goes with the coupling it warned about. tests/test_validator.py and tests/test_assembler.py pass UNCHANGED. Manifest regenerated in the same commit; detector E green.
- [ ] **A3** label_sync and sweeps, including the one caller that changes shape — size:M, blocked by: A1
  - Accept: `label_sync.live_labels` (label_sync.py:99) returns `(None, [suffix])` instead of raising `CLI_FAILURES`, and its docstring stops promising the raise; the three `try/except` blocks its callers own — label_sync.py:126, sweeps.py:403, sweeps.py:538 — are deleted, each keeping the `[f"<label>: {suffix}" for suffix in suffixes]` line it already has. sweeps.py:337 keeps refusing on `truncated` and sweeps.py:465 keeps its own pinned sentence, now passed as `full_note`. Every resulting problem string is byte-identical: tests/test_label_sync.py and tests/test_sweeps.py pass UNCHANGED. `label_sync.py` is mirrored and `sweeps.py` is not, so one payload twin plus the manifest are regenerated in the same commit; detector E green.
- [ ] **A4** the dashboard's three reads — size:S, blocked by: A1
  - Accept: dashboard.py:147 (timeline, no window), :166 and :240 (`window=` dashboard.py:70's `LIST_WINDOW`) read through `cli.gh_read`; `_timeline` still appends to the problems list it is handed and dashboard.py:171-177 still returns `None` after appending. tests/test_dashboard.py passes UNCHANGED. `dashboard.py` is not a MIRRORS entry — no payload twin, no manifest churn, and that is asserted by the item leaving `factory/` untouched.
- [ ] **A5** the digest's and the miner's five reads — size:M, blocked by: A1
  - Accept: gate_digest.py:198 and :295, and rejection_mining.py:174, :193 and :244 read through `cli.gh_read`; both modules pass their own `LIST_WINDOW` (gate_digest.py:169, rejection_mining.py:51) as `window=` and the byte-identical drift-warning comment above each is gone. `run_daily`'s `{"changed": "false"}` early return and the miner's `{}` and `[]` empties are unchanged; the two `_timelines` fetchers keep their own labels and their own local meaning, and neither moves. tests/test_gate_digest.py and tests/test_rejection_mining.py pass UNCHANGED. Both modules are mirrored: payload twins plus manifest regenerated in the same commit; detector E green.
- [ ] **A6** work_queue's read, and the halves die — size:M, blocked by: A2, A3, A4, A5
  - Accept: work_queue.py:178 reads through `cli.gh_read` with `window=100`, `ready_issue_numbers` still returning `(None, problems)` on `truncated`, and the duplicate window literal — `"100"` inside `LIST_ARGS` at work_queue.py:41 — is gone, so `grep -n '"100"' work_queue.py` finds nothing. `cli.gh_json` and `cli.full_window` are deleted in this same change, together with `TestGhJson` and `TestFullWindow`, whose unparseable / wrong-shape / full-window coverage now lives in `TestGhRead` one frame further out; the commit message says exactly that. Demonstrable at the close of this milestone: `--limit` appears in no root module but `cli.py`, and no root module, payload twin or test names `gh_json` or `full_window`. Manifest regenerated in the same commit; detector E green; the full battery green.

## Milestone B: the gate vocabulary has a home (no module reaches into a leaf tool for what a gate is; one stay walk, one spelling of the window test)

Item 2 of the design, plus the mirror map that travelled with it. `GATES`,
`label_events`, `gate_passages`, `waiting_since`, the timestamp arithmetic
and `mirror_map` live inside `gate_digest.py`, and three modules plus a CI
detector reach in — the detector positionally, at gates.py:777. The stay
walk is written twice with two spellings of the same window test, and the
invariant that joins them exists only as prose in a docstring. `human_gates.py`
is the new module (ADR-0056, provisional, already written by Architect);
`mirror_map` goes to `knowledge_plane.py`, which already owns the
tracker-mirror grammar. This is the milestone that carries the run's CI
landmine: a new file in the payload needs its MIRRORS row, `EXPECTED_RELS`,
the `docs/setup.md` counts and a regenerated manifest, all in one commit.

- [ ] **B1** pin the gate walk at the intended interface, against today's code — size:M, blocked by: —
  - Accept: `tests/test_human_gates.py` exists and is green against unmodified `gate_digest.py` and `rejection_mining.py`, importing `GATES`, `label_events`, `gate_passages` and `waiting_since` from `gate_digest` and `gate_rejections` from `rejection_mining` — the awkwardness is the measurement, and the import lines are the whole of it. It covers the passage cases (today at tests/test_gate_digest.py:95-143), the rejection cases (tests/test_rejection_mining.py:104-135), `label_events` (tests/test_gate_digest.py:81), `waiting_since` (:144), and the case neither suite has: **the partition property** — for one hand-written event history, the passages and the rejections together are exactly the completed stays, and no stay is in both. No production file changes in this item.
- [ ] **B2** pin `mirror_map` at the knowledge plane, against today's code — size:S, blocked by: —
  - Accept: a `mirror_map` case in tests/test_knowledge_plane.py builds a breakdown tree and asserts the `{tracker issue number: token}` mapping through `gate_digest.mirror_map`, where it still lives, covering a row carrying both, a row with no tracker reference, and an issue with no row. Green against unmodified sources; no production file changes.
- [ ] **B3** `human_gates.py` lands and ships — size:M, blocked by: B1
  - Accept: `human_gates.py` exists at the repo root with `Gate(name, queue, passed, heading)` rows, `gate_labels()`, `label_events`, `completed_stays`, `gate_passages`, `gate_rejections`, `waiting_since` and `waited_seconds`, importing nothing outside `datetime` and `collections`, and raising nowhere. `tests/test_human_gates.py` is re-pointed at it and green with no case edited — the pin from B1 is the net, and it is the same test. The module joins `factory_init.MIRRORS` as an identity entry, with a sentence in the MIRRORS comment block naming why it ships (the same way the four seam modules are introduced there); `EXPECTED_RELS` in tests/test_factory_init.py gains `templates/tools/factory/human_gates.py`; `docs/setup.md`'s group table and totals sentence move with the payload (`tools/factory/` 16 to 17, `factory/` 37 to 38, and the stated stamp and payload totals with them), which the three count assertions in tests/test_factory_init.py check. It does NOT join `factory_init._PRODUCT_TOOLS` — no make target invokes it. `python3 factory_init.py update-manifest` is committed with the change; detector E green and `test_stamped_repo_passes_its_own_gates` green. `gate_digest.py` and `rejection_mining.py` keep their copies in this item, and every existing suite still passes. ADR-0056 and its `docs/adr/README.md` index row land here.
- [ ] **B4** detector J stops counting tuple fields — size:S, blocked by: B3
  - Accept: `LABEL_DECLARERS` (gates.py:774) keys `human_gates` and its lambda calls `mod.gate_labels()` instead of slicing `gate[1:3]`, so the detector no longer depends on how many label fields a gate row has. This is the run's **one deliberate output change**: a pruned gate label now reports `J: human_gates.py names …` rather than `J: gate_digest.py names …`, and the two assertions at tests/test_gates.py:699 and :769 move with it — the only exact-string edits sanctioned anywhere in this run. `gates.py` is a MIRRORS entry: payload twin plus manifest regenerated in the same commit, detector E green.
- [ ] **B5** the digest, the miner and the dashboard become thin callers — size:M, blocked by: B1, B3
  - Accept: `gate_digest.py`, `rejection_mining.py` and `dashboard.py` import the gate vocabulary from `human_gates`, and `GATES`, `label_events`, `gate_passages`, `waiting_since`, `_parse_ts` and `_seconds` are deleted from `gate_digest.py` while `gate_rejections`' stay walk is deleted from `rejection_mining.py` — one spelling of the window test survives, inside `completed_stays`, and the two tools partition one list instead of agreeing by two hand-written tests. `gate_digest._queues` calls `waited_seconds`. Dying last, in this same change: the duplicated classes in tests/test_gate_digest.py and tests/test_rejection_mining.py whose subject is now the shared module, with the diff naming `tests/test_human_gates.py` as where that coverage went; each suite keeps its own tool-level tests (`run_daily`, `run_mine`, posting, dedup) untouched and green. What deliberately does NOT move: `_timelines` in both tools, `dashboard._timeline`, `_post_digest`, `_post_queue`, `compose_digest`, `compose_queue`, `_capture_latency`, the ledger writes, the marker idioms and `dashboard._age_seconds`. Two payload twins plus the manifest regenerated in the same commit; detector E green.
- [ ] **B6** `mirror_map` moves to the knowledge plane — size:S, blocked by: B2, B5
  - Accept: `knowledge_plane.mirror_map(root)` exists, built from `breakdown_files`, `row_work_order` and `row_tracker_issue`, with its behavior unchanged; `gate_digest.py`, `rejection_mining.py` and `dashboard.py` import it from there and the copy at gate_digest.py:174 is gone. B2's pin is re-pointed and green with no case edited, and the superseded case at tests/test_gate_digest.py:190 is deleted in this same change. Demonstrable at the close of this milestone: no module imports anything from `gate_digest`, and `grep -rn "from gate_digest import" *.py` finds nothing. `knowledge_plane.py`, `gate_digest.py` and `rejection_mining.py` are mirrored: payload twins plus manifest regenerated in the same commit; detector E green; the full battery green.

## Milestone C: one `product_form` (the shadow is gone, and the target it was hiding is asserted)

Item 3 of the design. tests/test_gates.py:18 imports the production
transform and tests/test_gates.py:1626 rebinds the name to a copy that
respells six tools where `factory_init._PRODUCT_TOOLS` lists seven. It has
not bitten because `toolsmith-mine` (Makefile:68) is the one factory target
with no lockstep class. `tests/` is not mirrored — the only item in this
run with no payload consequence. This is one item, not two, because the
new assertion lands genuinely RED and a red tree cannot close an item; the
red-to-green happens inside the commit and is the evidence the shadow was
a live defect rather than a tidiness complaint.

- [ ] **C1** the missing lockstep target, then the shadow — size:S, blocked by: —
  - Accept: `TOOLSMITH_MINE_TARGET = ["python3 rejection_mining.py mine"]` and three `toolsmith-mine` methods join `TestLockstep`, shaped exactly like the gate-digest trio (both Makefiles expose the target; the workflow names no command of its own; the payload workflow is a byte mirror). Run against today's code the Makefile assertion FAILS, because the shadow leaves `rejection_mining.py` unrespelled while factory/templates/Makefile:64 carries `python3 tools/factory/rejection_mining.py mine` — that failure is reproduced and recorded in the commit message before the fix. The module-level `product_form` at tests/test_gates.py:1626 is then deleted, the line-18 import becomes the only binding, and the suite goes green; the other five call sites resolve to the import with no change in outcome. `grep -n "def product_form" tests/test_gates.py` finds nothing, and the docstring at tests/test_gates.py:1649-1652 becomes true. No manifest churn.

## Milestone D: one month-to-date definition (the rule ADR-0041 decided has one implementation, and a nonzero-cost gate row is what proves it)

Item 4 of the design, at its narrow size. `cost_report.aggregate` skips
gate rows before summing; `work_queue.month_to_date` does not. The two
agree today only because `cost_ledger.gate_entry` writes every gate row
free by construction — prevention, not repair — and the number they compute
is the input to the monthly circuit breaker. Deliberately NOT taken with
it: the three month-string spellings, the `_utcnow` twins, `dashboard._spend`,
and the `>=` / `>` cap comparisons, which answer different questions.

- [ ] **D1** pin the divergence with a nonzero-cost gate row — size:S, blocked by: —
  - Accept: a case in tests/test_cost_ledger.py writes a fixture ledger containing a gate-latency row with a nonzero `cost` and nonzero `tokens` — hand-written, because `cost_ledger.gate_entry` (cost_ledger.py:64) cannot produce one, which is the whole reason the divergence is invisible — and asserts against today's code that `cost_report.aggregate`'s month total EXCLUDES that row while `work_queue.month_to_date`'s INCLUDES it, naming the two different numbers. Green against unmodified sources; no production file changes. This is the regression evidence the brief says this run owes.
- [ ] **D2** `cost_ledger.dispatched`, and the two sums agree — size:S, blocked by: D1
  - Accept: `cost_ledger.dispatched(entries, month=None)` returns the rows that count as spend — never a row `gate_wait` answers for, and when `month` is given only rows `in_month` admits — as a pure filter over already-validated rows, in the same family as `in_month`, `gate_wait`, `row_key` and `wo_token`. `cost_report.aggregate` iterates it instead of its two `continue`s (cost_report.py:70, :72), so its month total is the same row set as its token and run counts by construction; `work_queue.month_to_date` (work_queue.py:191) sums `entry["cost"]` over it and keeps its `(dollars, problems)` shape. Each caller keeps its own arithmetic and its own cap comparison — cost_report.py:100's `>=` and work_queue.py:150's `>` are untouched. D1's fixture now yields one number and the same test asserts the agreement; a `dispatched` suite covers the month filter and the gate-row exclusion directly. tests/test_cost_report.py and tests/test_work_queue.py pass unchanged, and nothing dies — no existing test asserted the gate-row-inclusive sum, which is why the divergence survived. `cost_ledger.py`, `cost_report.py` and `work_queue.py` are mirrored: three payload twins plus the manifest regenerated in the same commit; detector E green; the full battery green.

## Design gaps found

**None that need Architect.** Every interface this breakdown cuts against is
stated in `architecture.md`'s *Interfaces & contracts*, and no item required
a decision the design had not already made. Two omissions in the design's own
checklists were absorbed here rather than routed back, because neither is a
choice — both follow mechanically from authorities the design already names:

1. **`gates.py` is missing from the design's per-item mirroring list.** The
   *Mirroring consequences* section prices item 2 as `human_gates.py` (new
   row), `knowledge_plane.py` and the two tools, but detector J's
   `LABEL_DECLARERS` lives in `gates.py`, which is the first entry in
   `factory_init.MIRRORS`. Changing it changes a payload twin, so B4 carries
   the regeneration. `factory_init.MIRRORS` is the authority on what ships
   (CLAUDE.md), so this needed reading, not deciding.
2. **The design's *Tests* section says nothing about `mirror_map`'s
   ordering.** It states the rule generally and applies it to the four
   items by name; `mirror_map` travels with item 2 but gets no test
   paragraph. B2 and B6 apply the same rule by extension — pin first at the
   intended interface, move second, delete the superseded case in the same
   change — and this is logged in `assumptions:` rather than invented here.

## Notes

- **Milestone order.** A first, because it is the widest leverage and because
  three of the modules milestone B re-points are modules milestone A has
  already touched — doing A first means B's diffs are about the gate
  vocabulary and nothing else. C and D are independent of both and of each
  other; they are placed last because they are the two smallest and neither
  blocks anything.
- **Fifteen items, four milestones, and each milestone stands alone.** A
  closes with one owner for the window rule; B closes with no module
  reaching into a leaf tool; C closes with one `product_form` and the target
  it was hiding asserted; D closes with one month-to-date definition. Each is
  demonstrable by grep at its close, which is what the brief's first success
  criterion asks for.
- **Why the manifest is not a milestone of its own.** The design's one
  `update-manifest` covers the whole change, but this run commits per item
  and the battery must be green at each one. A mirrored root file edited
  without a regenerated payload fails `tests/test_factory_init.py`; a payload
  regenerated without its manifest fails detector E. So the regeneration is
  an acceptance criterion on every item that touches a MIRRORS entry —
  A1, A2, A3, A5, A6, B3, B4, B5, B6 and D2 — and on none of the others.
  A4 (dashboard) and C1 (tests) are the two items with no payload
  consequence at all, and their criteria say so.
- **ADR-0056 is provisional and already written.** It landed with the
  Architect stage, unstaged, alongside its `docs/adr/README.md` index row;
  B3 is the item it belongs to, so it should be committed there rather than
  drifting into an unrelated change. Its status stays `provisional` until
  the operator confirms at merge, matching ADR-0054's precedent.
- **The eight per-caller suites are milestone A's real net.** tests for
  label_sync, sweeps, work_queue, gate_digest, rejection_mining, assembler,
  dashboard and validator already assert the exact problem strings, and they
  must pass UNCHANGED across A2 through A6. `TestGhRead` proves the seam;
  those eight prove nothing observable moved.
- **How this run dies, restated as a check on these rows.** The gate item
  grows past its evidence and starts moving `_timelines` and the post/upsert
  epilogues too — B5's acceptance criterion names them as staying put; or an
  interface move quietly changes a tool's output and an exact-string test is
  edited to match — B4's two assertions are the only sanctioned edits, and
  any other one means revert.
