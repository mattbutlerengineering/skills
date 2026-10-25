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

- [ ] **A1** the shape table, the owner test and the protocol frontmatter fence (`protocol.frontmatter_end`) — size:S, blocked by: —
  - Accept: `tests/frontmatter_shapes.py` exists with `SHAPES`, a tuple of `(name, text, expected end)` rows covering all nine rows of architecture.md's rule table (LF exact fences 2, CRLF 2, opener with trailing whitespace 2, closer with trailing whitespace 2, unterminated opener None, no frontmatter None, empty block 1, closer at end of file with no newline 2, opener with leading whitespace None) plus the extra shapes it names: an empty block followed by a later `---` line (1), an indented closer, a tab after the opener, a lone `\r` file, empty text (None) and a file that is a single `---` (None).
  - Accept: `tests/test_protocol_frontmatter.py` asserts, one `subTest` per row, that `frontmatter_end(text.splitlines())` and `frontmatter_end(text.splitlines(keepends=True))` both equal the row's expected end. It is written first and fails on today's code with an import error, recorded in the commit message.
  - Accept: `protocol.frontmatter_end(lines)` exists, holds the one fence regex `^---\s*$`, returns an int of at least 1 or None, and raises on no input in `SHAPES`. The test above passes. `protocol._FRONTMATTER` is still present (A2 removes it). The payload twin of `protocol.py` is byte-identical (`cmp` exits 0) and the manifest is regenerated; the battery is green.
- [ ] **A2** `protocol.parse_frontmatter` / `read_frontmatter` read through the owner — size:S, blocked by: A1
  - Accept: a caller-agreement test in `tests/test_protocol_frontmatter.py` iterates `SHAPES`: `parse_frontmatter(text)` is None exactly when the row's end is None, and otherwise equals the fields of `lines[1:end]` (`{}` for the empty block, `{'status': 'ok'}` where the block holds it). It is written first and fails on today's code for the trailing-space, empty-block and end-of-file rows.
  - Accept: two reproductions from defect.md land in `tests/test_gates.py`, written first and red on today's code: `gates.check_capture_completeness(root)` over a temp tree holding one `docs/fixes/old/defect.md` dated `2026-01-01` with none of the required sections returns `[]` for both a `---` and a `--- ` opener, and `gates._rollup_applies(text)` on a verification.md dated `2026-01-01` returns `False` for both openers.
  - Accept: `parse_frontmatter` splits with `splitlines()`, asks `frontmatter_end`, and parses `lines[1:end]`; `protocol._FRONTMATTER` and the CRLF `replace` step are deleted (`grep -n "_FRONTMATTER" protocol.py` prints nothing). Every existing protocol test passes unedited, including `test_fieldless_block_returns_empty_dict` and the CRLF parse test. The `protocol.py` twin is synced, the manifest regenerated, and the battery is green.

## Milestone B: every other owner becomes a thin caller

Demonstrable at the close: gates, launch_demo and knowledge_plane each give
the owner's answer on every row of `SHAPES`, and none of them holds a fence
rule of its own. B1, B2 and B3 are independent of each other once A2 lands.

- [ ] **B1** `gates._skip_frontmatter` calls the owner (detectors H and M) — size:S, blocked by: A2
  - Accept: a caller-agreement test in `tests/test_gates.py` iterates `SHAPES` and asserts `_skip_frontmatter(text.splitlines())` equals `end + 1` when the row's end is not None, else 0. It passes on today's code and after the change (a characterization pin, see assumptions), and the commit message says so.
  - Accept: `_skip_frontmatter` returns `end + 1` from `protocol.frontmatter_end`, else 0, with its signature unchanged; `gates.FRONTMATTER_FENCE` is deleted (`grep -n "FRONTMATTER_FENCE" *.py factory/templates/tools/factory/*.py` prints nothing). `TestEvidenceHonesty`, `TestCaptureCompleteness` and the A2 reproductions pass unedited. The `gates.py` twin is synced, the manifest regenerated, and the battery is green.
- [ ] **B2** `launch_demo._body` calls the owner, with the dual-membership pin pair — size:S, blocked by: A2
  - Accept: a caller-agreement test in `tests/test_launch_demo.py` iterates `SHAPES` and asserts `_body(text)` equals `"".join(text.splitlines(keepends=True)[end + 1:])` when the row's end is not None, else `text` unchanged. It is written first and fails on today's code for the CRLF, trailing-space, empty-block and end-of-file rows.
  - Accept: `_body` splits with `splitlines(keepends=True)`, asks `protocol.frontmatter_end`, and returns the joined body or the text unchanged; its literal `---\n` string search is gone. `tests/test_dual_membership.py`'s `ROOT_ONLY_IMPORTS_MIRRORED` gains `("launch_demo", "protocol")` citing ADR-0118, taking the set from 55 pairs to 56, and that suite passes. Every existing `tests/test_launch_demo.py` case passes unedited. `launch_demo.py` gains no payload twin, and the battery is green.
- [ ] **B3** `knowledge_plane._declared_status` calls the owner — size:S, blocked by: A2
  - Accept: a caller-agreement test in `tests/test_knowledge_plane.py` iterates `SHAPES` with no `- Status:` line and asserts `_declared_status(text.splitlines())` reads the block's `status:` exactly when the row's end is not None, and returns `(0, None)` otherwise. It is written first and fails on today's code for the unterminated-opener and leading-space-opener rows.
  - Accept: the fallback scans only `lines[1:end]` when `protocol.frontmatter_end` finds an end and skips the fallback when it returns None; the inline `strip() == "---"` walk is deleted. Its output is unchanged whenever a `- Status:` line exists. Every existing knowledge_plane and detector D test passes unedited. The `knowledge_plane.py` twin is synced, the manifest regenerated, and the battery is green.

## Milestone C: one definition, proved

Demonstrable at the close: a counted pin fails if a second fence definition
appears anywhere in tracked Python, and the whole repo agrees old against new.

- [ ] **C1** the AST count pin for one fence definition — size:S, blocked by: B1, B2, B3
  - Accept: a test in `tests/test_protocol_frontmatter.py` walks the AST of every tracked non-test `.py` file, root and `factory/templates/tools/factory/` alike, collects each string constant that defines a frontmatter fence matcher (a `---` regex passed to `re.compile`, or a `"---"` literal compared with `==`), and asserts with `assertEqual` the exact per-module count map: one in `protocol.py`, one in its payload twin, and the known non-owners from defect.md (`gates.SETEXT_UNDERLINE` and its twin, `lint.py`'s table separator, `charter_replay.py`'s prompt delimiters) each at its current count, with zero in `gates.py`, `launch_demo.py` and `knowledge_plane.py`.
  - Accept: a mutation check re-adding `FRONTMATTER_FENCE = re.compile(r"^---\s*$")` to `gates.py` makes the pin fail, and reverting it makes it pass; both runs are recorded in the commit message. The battery is green.
- [ ] **C2** close-out: Payload twins, manifest, battery and the old-against-new sweep — size:M, blocked by: C1
  - Accept: `cmp` exits 0 for each of `protocol.py`, `gates.py` and `knowledge_plane.py` against its `factory/templates/tools/factory/` twin; `git ls-files -o --exclude-standard` lists no `.orig`/`.rej`; a fresh `python3 factory_init.py update-manifest` leaves `git status --porcelain` empty.
  - Accept: `python3 run_tests.py` exits 0, `python3 lint.py` prints `lint: 0 problem(s)`, `python3 kb.py drift` prints `drift: 0 problem(s)`, and `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)`.
  - Accept: a throwaway script outside the repo loads the four readers from `main` (via `git show main:<file>`) and from this branch, runs `parse_frontmatter`, `_skip_frontmatter`, `_body` and `_declared_status` over every file `git ls-files '*.md'` lists, and prints every file whose verdict differs between old and new, then a total. The total and any listed file are logged under Notes, dated; defect.md predicts 0. A nonzero total is not fixed here: it is reported to Verify and, if it shows a shape the rule table did not predict, routed to Architect as a design gap.

## Design gaps found

None.

## Notes

- Order: A1 → A2 → {B1, B2, B3} → C1 → C2. The three B items touch three
  different modules and three different test suites and can land in any
  order after A2.
- Open PR #1079 edits `gates.py`'s zero-count window, a different region from
  B1's. Ship chain-checks the pair with merge-tree (docs/kb/cross-pr-merge-hazards.md).
