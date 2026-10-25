---
stage: decompose
run: maintenance:one-frontmatter-end
date: 2026-10-24
assumptions:
  - "The cut was not reviewed live: this run is driven from autorun-brief.md, which supplies no milestone boundaries or sizes. The milestones, sizes and order below are read out of architecture.md's Components, Interfaces & contracts and Test strategy sections. A mis-sized row is a note for Implement to log, not a design change."
  - "Rows are lettered and carry a size class (ADR-0034 vocabulary, S/M/L), as docs/fixes/one-fact-one-owner/breakdown.md does. No row mints a WO-#### id and no row carries a (tracker: #N) reference: this maintenance run has no PRD for detector A to pair a work order with, and the brief files one plain type:defect issue for the whole run at Ship. These checkboxes are the whole state (ADR-0026)."
  - "Payload twins and the manifest are served inside each item that edits a mirrored file (protocol.py, gates.py, knowledge_plane.py), not in one late item. tests/test_factory_init.py pins payload to root and detector E pins manifest to payload, so a twin left stale until a later item would leave the tree red at an item boundary. The closing item re-checks all three twins and the manifest once. Precedent: docs/fixes/one-fence-rule/breakdown.md."
  - "Detector M's and _rollup_applies' reproductions land in A2, not B1, although they live in tests/test_gates.py. Their divergence comes from parse_frontmatter's exact-fence regex, so they are red against today's code and turn green when parse_frontmatter moves onto the owner (A2). Under B1 they would already be green and prove nothing."
  - "B1's caller-agreement test cannot be written red: the owner takes gates' rule as it stands (architecture.md, Approach), so _skip_frontmatter already gives the owner's answer on every shape. It lands as a characterization pin, green before and after the swap, and the item's commit message says so. Every other caller item is red-first."
  - "The dual-membership pin pair (launch_demo, protocol) lands in B2, the same commit as the new import, because tests/test_dual_membership.py fails the moment the edge exists without it. Adding a pair an ADR records is the pin's designed change (architecture.md's assumptions), not editing a test to make it pass."
  - "The old-against-new sweep over every tracked *.md is run in C2 as an Implement pre-check so a surprise surfaces before Verify. architecture.md names Verify as its owner, so Verify re-runs it and records the evidence in verification.md; C2 only logs the count under Notes."
  - "docs/factory/decompose-lessons.jsonl does not exist in this repo, so no lessons were weighed (skill step 3)."
  - "(Implement, 2026-10-25) C1's detector is wider than its Accept line words it, so a launch_demo-style copy is caught: a fence definition is an re.* pattern that finds a three-dash fence (alone, inside text, or as a two-fence block) but not the same probe with two dashes, or a string constant stripping to `---` passed to a method call or on either side of ==, !=, in or not in (alone or in a tuple, list or set literal). Under it gates.SETEXT_UNDERLINE (it takes `--` too), charter_replay's delimiters and frontmatter writers count zero, pinned by a test; lint.py's table-separator membership test counts one and is pinned as a known non-owner. The Accept's 'each at its current count' reads as these counts. Blind spots kept: a fence built at run time (concatenation, a variable), a fence regex loose enough to take `--` too (such as `^-{2,}\\s*$`, which the two-dash probe reads as a dash-run rule), and receivers other than the bare name `re` (`import re as r`)."
---

# Breakdown: one owner of where frontmatter ends

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Source: `architecture.md` in this directory
(2026-10-24) and ADR-0118 (provisional). Rows carry an item letter, a size
class and blocking edges; they carry no work-order id and no tracker
reference.

**Test first, every item.** Each item writes its cases before the code that
turns them green, watches them fail on today's code, and says so in its
commit message. The one exception is B1, recorded under assumptions. No
existing test is edited, except that `tests/test_dual_membership.py`'s
`ROOT_ONLY_IMPORTS_MIRRORED` gains the one pair ADR-0118 records (B2).

**Mirrored files.** `protocol.py`, `gates.py` and `knowledge_plane.py` are
identity mirrors (`factory_init.MIRRORS`). Every item that edits one copies it
byte for byte to `factory/templates/tools/factory/<name>.py`, deletes any
stray `.orig`/`.rej` files (docs/kb/manifest-regen.md), runs
`python3 factory_init.py update-manifest`, and commits the manifest in the
same commit. `launch_demo.py` is not mirrored and stays root-only.

**The battery is green at every item boundary:** `python3 run_tests.py`,
`python3 lint.py` (`lint: 0 problem(s)`), `python3 kb.py drift`
(`drift: 0 problem(s)`) and `python3 gates.py && python3 gates.py --selftest`
(`gates: 0 problem(s)`).

**Out of scope** (defect.md): the `key: value` field grammar inside the block,
frontmatter writers (`trigger_eval`), the Setext and code-fence rules, and
the region of `gates.py` that open PR #1079 edits.

## Milestone A: the owner exists and protocol reads through it

Demonstrable at the close: `protocol.frontmatter_end` answers every shape in
the shared table, `parse_frontmatter` agrees with it, and detector M's
reproduction from defect.md gives one answer for a `---` and a `--- ` opener.

- [x] **A1** the shape table, the owner test and the protocol frontmatter fence (`protocol.frontmatter_end`) — size:S, blocked by: —
  - Accept: `tests/frontmatter_shapes.py` exists with `SHAPES`, a tuple of `(name, text, expected end)` rows covering all nine rows of architecture.md's rule table (LF exact fences 2, CRLF 2, opener with trailing whitespace 2, closer with trailing whitespace 2, unterminated opener None, no frontmatter None, empty block 1, closer at end of file with no newline 2, opener with leading whitespace None) plus the extra shapes it names: an empty block followed by a later `---` line (1), an indented closer, a tab after the opener, a lone `\r` file, empty text (None) and a file that is a single `---` (None).
  - Accept: `tests/test_protocol_frontmatter.py` asserts, one `subTest` per row, that `frontmatter_end(text.splitlines())` and `frontmatter_end(text.splitlines(keepends=True))` both equal the row's expected end. It is written first and fails on today's code with an import error, recorded in the commit message.
  - Accept: `protocol.frontmatter_end(lines)` exists, holds the one fence regex `^---\s*$`, returns an int of at least 1 or None, and raises on no input in `SHAPES`. The test above passes. `protocol._FRONTMATTER` is still present (A2 removes it). The payload twin of `protocol.py` is byte-identical (`cmp` exits 0) and the manifest is regenerated; the battery is green.
- [x] **A2** `protocol.parse_frontmatter` / `read_frontmatter` read through the owner — size:S, blocked by: A1
  - Accept: a caller-agreement test in `tests/test_protocol_frontmatter.py` iterates `SHAPES`: `parse_frontmatter(text)` is None exactly when the row's end is None, and otherwise equals the fields of `lines[1:end]` (`{}` for the empty block, `{'status': 'ok'}` where the block holds it). It is written first and fails on today's code for the trailing-space, empty-block and end-of-file rows.
  - Accept: two reproductions from defect.md land in `tests/test_gates.py`, written first and red on today's code: `gates.check_capture_completeness(root)` over a temp tree holding one `docs/fixes/old/defect.md` dated `2026-01-01` with none of the required sections returns `[]` for both a `---` and a `--- ` opener, and `gates._rollup_applies(text)` on a verification.md dated `2026-01-01` returns `False` for both openers.
  - Accept: `parse_frontmatter` splits with `splitlines()`, asks `frontmatter_end`, and parses `lines[1:end]`; `protocol._FRONTMATTER` and the CRLF `replace` step are deleted (`grep -n "_FRONTMATTER" protocol.py` prints nothing). Every existing protocol test passes unedited, including `test_fieldless_block_returns_empty_dict` and the CRLF parse test. The `protocol.py` twin is synced, the manifest regenerated, and the battery is green.

## Milestone B: every other owner becomes a thin caller

Demonstrable at the close: gates, launch_demo and knowledge_plane each give
the owner's answer on every row of `SHAPES`, and none of them holds a fence
rule of its own. B1, B2 and B3 are independent of each other once A2 lands.

- [x] **B1** `gates._skip_frontmatter` calls the owner (detectors H and M) — size:S, blocked by: A2
  - Accept: a caller-agreement test in `tests/test_gates.py` iterates `SHAPES` and asserts `_skip_frontmatter(text.splitlines())` equals `end + 1` when the row's end is not None, else 0. It passes on today's code and after the change (a characterization pin, see assumptions), and the commit message says so.
  - Accept: `_skip_frontmatter` returns `end + 1` from `protocol.frontmatter_end`, else 0, with its signature unchanged; `gates.FRONTMATTER_FENCE` is deleted (`grep -n "FRONTMATTER_FENCE" *.py factory/templates/tools/factory/*.py` prints nothing). `TestEvidenceHonesty`, `TestCaptureCompleteness` and the A2 reproductions pass unedited. The `gates.py` twin is synced, the manifest regenerated, and the battery is green.
- [x] **B2** `launch_demo._body` calls the owner, with the dual-membership pin pair — size:S, blocked by: A2
  - Accept: a caller-agreement test in `tests/test_launch_demo.py` iterates `SHAPES` and asserts `_body(text)` equals `"".join(text.splitlines(keepends=True)[end + 1:])` when the row's end is not None, else `text` unchanged. It is written first and fails on today's code for the CRLF, trailing-space, empty-block and end-of-file rows.
  - Accept: `_body` splits with `splitlines(keepends=True)`, asks `protocol.frontmatter_end`, and returns the joined body or the text unchanged; its literal `---\n` string search is gone. `tests/test_dual_membership.py`'s `ROOT_ONLY_IMPORTS_MIRRORED` gains `("launch_demo", "protocol")` citing ADR-0118, taking the set from 55 pairs to 56, and that suite passes. Every existing `tests/test_launch_demo.py` case passes unedited. `launch_demo.py` gains no payload twin, and the battery is green.
- [x] **B3** `knowledge_plane._declared_status` calls the owner — size:S, blocked by: A2
  - Accept: a caller-agreement test in `tests/test_knowledge_plane.py` iterates `SHAPES` with no `- Status:` line and asserts `_declared_status(text.splitlines())` reads the block's `status:` exactly when the row's end is not None, and returns `(0, None)` otherwise. It is written first and fails on today's code for the unterminated-opener and leading-space-opener rows.
  - Accept: the fallback scans only `lines[1:end]` when `protocol.frontmatter_end` finds an end and skips the fallback when it returns None; the inline `strip() == "---"` walk is deleted. Its output is unchanged whenever a `- Status:` line exists. Every existing knowledge_plane and detector D test passes unedited. The `knowledge_plane.py` twin is synced, the manifest regenerated, and the battery is green.

## Milestone C: one definition, proved

Demonstrable at the close: a counted pin fails if a second fence definition
appears anywhere in tracked Python, and the whole repo agrees old against new.

- [x] **C1** the AST count pin for one fence definition — size:S, blocked by: B1, B2, B3
  - Accept: a test in `tests/test_protocol_frontmatter.py` walks the AST of every tracked non-test `.py` file, root and `factory/templates/tools/factory/` alike, collects each string constant that defines a frontmatter fence matcher (a `---` regex passed to `re.compile`, or a `"---"` literal compared with `==`), and asserts with `assertEqual` the exact per-module count map: one in `protocol.py`, one in its payload twin, and the known non-owners from defect.md (`gates.SETEXT_UNDERLINE` and its twin, `lint.py`'s table separator, `charter_replay.py`'s prompt delimiters) each at its current count, with zero in `gates.py`, `launch_demo.py` and `knowledge_plane.py`.
  - Accept: a mutation check re-adding `FRONTMATTER_FENCE = re.compile(r"^---\s*$")` to `gates.py` makes the pin fail, and reverting it makes it pass; both runs are recorded in the commit message. The battery is green.
- [x] **C2** close-out: Payload twins, manifest, battery and the old-against-new sweep — size:M, blocked by: C1
  - Accept: `cmp` exits 0 for each of `protocol.py`, `gates.py` and `knowledge_plane.py` against its `factory/templates/tools/factory/` twin; `git ls-files -o --exclude-standard` lists no `.orig`/`.rej`; a fresh `python3 factory_init.py update-manifest` leaves `git status --porcelain` empty.
  - Accept: `python3 run_tests.py` exits 0, `python3 lint.py` prints `lint: 0 problem(s)`, `python3 kb.py drift` prints `drift: 0 problem(s)`, and `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)`.
  - Accept: a throwaway script outside the repo loads the four readers from `main` (via `git show main:<file>`) and from this branch, runs `parse_frontmatter`, `_skip_frontmatter`, `_body` and `_declared_status` over every file `git ls-files '*.md'` lists, and prints every file whose verdict differs between old and new, then a total. The total and any listed file are logged under Notes, dated; defect.md predicts 0. A nonzero total is not fixed here: it is reported to Verify and, if it shows a shape the rule table did not predict, routed to Architect as a design gap.

## Design gaps found

- 2026-10-24 (Implement, B2): B2's Accept line cannot hold as written.
  It requires `ROOT_ONLY_IMPORTS_MIRRORED` to go from 55 pairs to 56
  and the battery to stay green with every other existing test
  unedited, but a second, unplanned pin also hard-codes the total:
  `tests/test_eval_trends.py`'s
  `TestDualMembershipPin.test_the_pin_holds_the_eval_trends_edge_and_55_pairs`
  asserts `len(test_dual_membership.ROOT_ONLY_IMPORTS_MIRRORED) == 55`
  (added by #1056). With B2's change applied, `python3 run_tests.py`
  reports 1 problem: `AssertionError: 56 != 55` in that test, while
  `tests.test_launch_demo` and `tests.test_dual_membership` pass. Making
  it pass means editing an existing test (55 to 56, or dropping the
  count since test_dual_membership owns the set), which the run's
  constraints forbid without a decision. B2 is not committed; C1 and C2,
  blocked by it, are not started. Routed back for an Owner/Architect
  decision on that pin.
- 2026-10-25 resolved (Owner, in session): asked how to treat the second
  pin, the Owner answered "Drop the count, keep assertIn". The
  `assertEqual(len(pinned), 55)` line is deleted, its `assertIn(("eval_trends",
  "cli"), pinned)` kept, and the method renamed
  `test_the_pin_holds_the_eval_trends_edge`; `tests/test_dual_membership.py`
  alone owns the set and its size. This is the run's one authorized edit
  to an existing test outside B2's planned pair. Commit 976ef33. B2 resumed.

## Notes

- Order: A1 → A2 → {B1, B2, B3} → C1 → C2. The three B items touch three
  different modules and three different test suites and can land in any
  order after A2.
- Open PR #1079 edits `gates.py`'s zero-count window, a different region from
  B1's. Ship chain-checks the pair with merge-tree (docs/kb/cross-pr-merge-hazards.md).
- 2026-10-24 (Implement) A1 checked: `tests/frontmatter_shapes.py` holds
  15 rows (the nine rule-table rows plus the six extra shapes).
  `tests.test_protocol_frontmatter` failed to import before the code
  (`ImportError: cannot import name 'frontmatter_end' from 'protocol'`),
  then ran 21 tests OK. `_FRONTMATTER` still present at A1's commit;
  twin `cmp` 0, manifest regenerated, battery green (3807 tests, 0
  problems). Commit a718d44.
- 2026-10-24 (Implement) A2 checked: the parse_frontmatter agreement
  test failed 7 of 15 shapes before the change, the three the Accept
  names plus the empty block with a later fence line, the tab after the
  opener, the lone carriage returns and the closer at end of file; the
  two gates reproductions failed for the `--- ` opener only. All green
  after; `grep -n "_FRONTMATTER" protocol.py` prints nothing; every
  existing protocol test unedited; battery green (3810 tests). Commit
  8d41d7b.
- 2026-10-24 (Implement) B1 checked: the `_skip_frontmatter` pin passed
  before and after the swap (characterization, as planned); the
  `FRONTMATTER_FENCE` grep over root and payload `.py` prints nothing;
  its rationale comment moved above `_skip_frontmatter`. Battery green
  (3811 tests). Commit 2ac2c00.
- 2026-10-24 (Implement) B3 checked: the `_declared_status` agreement
  test failed 3 of 15 shapes before the change, the two the Accept names
  plus the indented closer (knowledge_plane read `status:` before
  reaching it). Green after; existing knowledge_plane and detector D
  tests unedited; twin `cmp` 0, manifest regenerated, battery green
  (3812 tests). Commit 800b724.
- 2026-10-24 (Implement) B2 stopped: see Design gaps found. The B2
  change (launch_demo `_body` on the owner, the `TestBody` agreement
  test, which failed 8 of 15 shapes on today's code and passed after,
  and the dual-membership pair) was written and run, then reverted
  uncommitted pending the decision.
- 2026-10-24 (Implement) For C1, when it resumes: the detector as the
  Accept words it (a `---` regex passed to `re.compile`, or a `"---"`
  literal compared with `==`) does not see `launch_demo._body`'s old
  `startswith("---\n")` / `find("\n---\n")` copy, nor `lint.py:866`'s
  `in ("stage", "---")`, and `SETEXT_UNDERLINE` (`-+`) and
  `charter_replay.py`'s delimiter text count 0 under it. An AST scan
  with the worded detector on this branch after B3 finds one constant
  each in protocol.py and its twin and nothing else; widened to
  string-method arguments and membership tests it would also find
  launch_demo.py (2, until B2 lands) and lint.py (1).
- 2026-10-25 (Implement) Owner decision recorded under Design gaps found
  ("Drop the count, keep assertIn"); `tests/test_eval_trends.py` edited
  as decided, commit 976ef33.
- 2026-10-25 (Implement) B2 checked: the saved patch re-applied. RED
  re-run with only `launch_demo.py` reverted: `TestBody` failed 8 of 15
  shapes (crlf, opener and closer with trailing whitespace, empty block,
  closer at end of file, empty block with a later fence line, tab after
  the opener, lone carriage returns). GREEN after; `tests.test_launch_demo`
  and `tests.test_dual_membership` (56 pairs) pass, existing launch_demo
  cases unedited, no payload twin. Battery green (3813 tests). Commit
  76bd161.
- 2026-10-25 (Implement) C1 checked: `TestOneFenceDefinition` pins the
  exact map `{protocol.py: [^---\s*$], its twin: [^---\s*$], lint.py:
  [---]}` with the widened detector (assumptions), plus a test that it
  sees each copy shape (line regex, block regex, startswith, find, ==,
  membership) and one that the known non-owners count zero. Run over
  origin/main's sources it reports protocol `_FRONTMATTER`, gates
  `FRONTMATTER_FENCE`, launch_demo's `---\n` / `\n---\n` pair and
  knowledge_plane's two `---` comparisons. Mutation 1: adding
  `FRONTMATTER_FENCE = re.compile(r"^---\s*$")` to gates.py failed the
  pin (`'gates.py': ['^---\\s*$']`); reverted, OK. Mutation 2: adding
  `if not text.startswith("---\n"): return text` to `launch_demo._body`
  failed it (`'launch_demo.py': ['---\n']`); reverted, OK. Both re-run
  after the final detector edit. Battery green (3816 tests). Commit
  59a7c64.
- 2026-10-25 (Implement) C2 checked: `cmp` exits 0 for protocol.py,
  gates.py and knowledge_plane.py against their twins; no `.orig`/`.rej`
  listed; a fresh `python3 factory_init.py update-manifest` printed
  `factory-init: 0 problem(s)` and left `git status --porcelain` empty.
  Old-against-new sweep (old = origin/main ec8159f's root .py via
  `git archive` into the scratchpad, each side in its own `python3 -I`
  process): 1014 tracked `*.md` files, 736 with frontmatter, 0 changed
  verdicts across `parse_frontmatter`, `_skip_frontmatter`, `_body` and
  `_declared_status`, as defect.md predicts. Verify re-runs it. Battery:
  `tests: 3816 tests across 118 modules ... 0 problem(s)`, `lint: 0
  problem(s) across 34 skills`, `drift: 0 problem(s)`, `gates: 0
  problem(s)` / `selftest: ok`.
