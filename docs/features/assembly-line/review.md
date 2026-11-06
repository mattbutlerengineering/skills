---
stage: review
run: feature:assembly-line
date: 2026-11-06
assumptions:
  - "The Owner's autorun brief (2026-11-06) says to continue through Ship with the four human criteria NOT RUN, so Review carries them as open and does not wait on them."
  - "The Owner confirmed ADR-0124 live on 2026-11-05 (ADR-0124 and architecture.md record the choice as the Owner's), so its status stays accepted, not provisional."
  - "Two findings were fixed in this stage because the fix loop covers a major and the second was a one-line change beside it; the remaining findings are minor and deferred under the skill's rule that minors may be deferred."
---

# Review: An animated assembly line of every run in the repo, with a history replay

## Scope

`git diff origin/main...HEAD` at the start of this stage: 32 files, +84334
-26, 19 commits from `1be1023` (idea) to `b0a0ae4` (verify). Read in full:
`assembly_line.py`, its seams in `board.py`, `protocol.py` (and the
`factory/templates/tools/factory/protocol.py` mirror), `factory.py`,
`npx_bundle.py`, `tests/test_assembly_line.py`, the touched tests, and the
page template `assembly_line.html` (every place it writes to the DOM, loads
the library, or reads the model). `vendor/three/` was checked by size,
licence and `NOTICE` entry, not read line by line. Inputs: `prd.md`
(PRD-0021), `architecture.md`, `breakdown.md`, `verification.md`.
Verification is present, so the order is the normal one.

The stage added one commit of its own, `47dba2d`, fixing findings 1 and 2.

## Findings

### Major: `assembly_line.py` raises a traceback when the target cannot be written

- Scenario: `python3 assembly_line.py <repo> --out /nonexistent/dir/x.html`
  (or `--publish` under a path that is a file) reached `target.write_text`
  and `directory.mkdir` unguarded, and died with `FileNotFoundError`
  printed as a stack trace. Every other failure in the tool is a problem
  string through `cli.report`, which is the contract AGENTS.md states for
  root tools, and the verb is run through `factory.py assembly-line` by the
  skill. Reproduced before the fix; the traceback ended in
  `FileNotFoundError: [Errno 2] No such file or directory`.
- Standard: none (`stdlib-only` is not touched; the broken rule is
  AGENTS.md's problem-string contract).
- Decision: fixed in `47dba2d`. `_target` and the write now sit in one
  `try` that reports `assembly_line: cannot write the page: <error>` and
  exits 1; `test_an_unwritable_target_exits_1_with_a_problem_not_a_traceback`
  covers `--out` and `--publish`.

### Minor: a run slug or work-order title that spells a slot name corrupts the page

- Scenario: `render` replaced `__MODEL__` first and the vendor slots on the
  result, so a breakdown row titled `fix __THREE_CORE__ loading` put 2 MB
  of base64 inside that title in the JSON model. Reproduced with
  `render({"runs":[{"slug":"__THREE_CORE__"}]}, ...)`: the slug came out as
  `QUFBQQ==`. The page still ran, but the data was wrong, and this repo's
  own docs discuss these slot names.
- Standard: none.
- Decision: fixed in `47dba2d`: one regex pass over the template, so text a
  slot receives is never scanned for slots;
  `test_slot_names_inside_the_model_are_data_not_slots` pins it.

### Minor: crate hover at Operate omits "shipped, awaiting a retro"

- Scenario: hovering a crate in the Completed pile shows no state line; only
  the station hover says it. Raised by Verify's observations.
- Standard: none.
- Decision: deferred — the PRD criteria for Completed are met (verification
  PASS); the line is polish on a presentation surface, and the quality bar
  for presentation is the open human check below.

### Minor: the honesty line says order within a day is "inferred" but does not say that stage order is what it follows

- Scenario: a viewer reading the line cannot tell what the inference is
  based on. Raised by Verify's observations.
- Standard: none.
- Decision: deferred — wording only; no wrong behaviour. Revisit when the
  Owner runs the presentation check.

### Minor: hidden-headless frame rate dips to 33-40 fps late in the replay

- Scenario: Verify measured 60 fps in a visible window and 33-40 fps in a
  hidden headless tab late in a replay; the PRD's frame-rate claim rests on
  the single visible-window run.
- Standard: none.
- Decision: deferred — headless rendering has no GPU compositing to
  compare against; a second machine's measurement is on Verify's own
  unverified list and belongs to the Owner's real-use check.

## Passes with no findings

- **Correctness**: clean beyond findings 1 and 2. `board.reason`,
  `run_identity` and `run_entry` were made public by renaming and every
  caller was moved (grep finds no `_run_entry` or `_reason` left); the
  history and replay code is pinned by fixture-tree tests, and the suite
  passes.
- **Design**: the code matches `architecture.md`: a new root tool beside
  `board.py` that places runs through `board`'s own functions, the page
  deriving nothing, dates from frontmatter only. No deviation is
  undocumented. **ADR check, missing records**: the run's decisions were
  tested against "When to write an ADR". Bundling three.js passes all
  three legs and has ADR-0124. The rest (a new tool beside `board.py`,
  frontmatter dates over git, a first-party GIF encoder, publish-by-flag,
  showing the phantom product run) are each cheap to reverse, so they stay
  as one-line records in `architecture.md`'s decisions section. No passing
  decision lacks an ADR, and no existing ADR's Decision section was
  edited. **ADR-0124 against what was built**: it says three.js v0.187.0 is
  vendored under `vendor/three/` with its licence, recorded in `NOTICE`,
  carried by `npx_bundle.py`, inlined into every page, unminified at about
  2.1 MB. Built: `vendor/three/three.core.js` 1,474,799 bytes plus
  `three.module.js` 658,900 bytes (2,133,699 bytes, 2.1 MB), `LICENSE`, the
  `NOTICE` paragraph naming v0.187.0, `npx_bundle.py` taking `vendor/` and
  `assembly_line.html`, base64 inlining in `render`. It also says the root
  tool joins three rows of ADR-0091's table and gets the `assembly-line`
  verb; `tests/test_dual_membership.py` and `factory.py` carry both. It is
  consistent.
- **Security**: the page embeds repo data and was checked for injection. The
  model sits in a `type="application/json"` script block with `</` escaped
  (a test pins a `</script>` slug), and a closing tag is the only way out
  of that block. The page template has no `innerHTML`, `insertAdjacentHTML`,
  `document.write` or `eval`; model strings reach the DOM through
  `textContent` and canvas text only. The one dynamic import is the
  vendored library from a Blob URL built from the page's own base64, not
  from model data. The page makes no network request (no `fetch`,
  `XMLHttpRequest` or external `src`/`href`). The CLI takes a local path
  and writes only where the caller points it, defaulting to the system
  temp directory. No secrets in the diff.
- **Complexity**: no cut-list line confirmed. The diff adds no `lean:`
  marker. The vendored files are unminified because upstream ships no
  minified build (ADR-0124). The 1,285-line page template and the
  first-party GIF encoder are sized by the PRD's clip requirement, not by
  speculation; a module-shape concern would go to `deepen`, and there is
  none to hand over.
- **ADR compliance**: `adr_status.py` lists ADR-0124 as `active`. Checked
  the diff against ADR-0062 (facts come from a shipped tool: placement is
  `board.gather` verbatim), ADR-0075 (the hand-written file read is the
  same documented exception `dashboard.py` takes, with the reason in
  `_read`'s docstring), ADR-0091 and ADR-0097-style root-only importer rows
  (updated and test-pinned), ADR-0095 (see conventions below) and ADR-0120
  (`npx_bundle.py` carries the new files). No violation. The provisional
  ADRs the diff reaches (0075, 0097) also found none.
- **Domain passes**: Interface selected (`assembly_line.html`); the diff is
  one new file, so it deletes no accessibility signal (the removed side
  holds nothing for the page), and `lang="en"`, `aria-label` and
  `aria-pressed` on controls, an Escape handler and
  `prefers-reduced-motion` are present. Dependencies, Payments, Migrations:
  not selected (no manifest, lockfile, payment word or SQL path changed;
  `vendor/three/` is vendored source recorded by ADR-0124, not a package
  manifest).
- **Standards** (`docs/standards.json`): `stdlib-only` (advisory) is held:
  the new root script imports only the standard library and mirrored root
  modules; the library is JavaScript used inside the page.
- **Repo conventions (AGENTS.md)**: the `factory_init` manifest is current,
  because `factory/templates/tools/factory/protocol.py` and its manifest
  hash moved together with the `protocol.py` edit (`python3 gates.py` and
  `kb.py drift` report 0). `.claude-plugin/plugin.json`: the only change
  against the merge-base is the description line listing the new skill;
  the version is still `0.26.0`, untouched, per ADR-0095. Gates scan every
  markdown file and report 0 problems, so no cited id is invented.

## Verdict

**No CRITICAL finding is unfixed, and none was found.** One major and one
minor were fixed in `47dba2d`; three minors are deferred with reasons.
Nothing in this review blocks the authorized merge.

Re-run after the fixes, from the worktree:

- `python3 run_tests.py`: `tests: 4080 tests across 131 modules in 25.4s on 8 workers, 0 problem(s)`
- `python3 lint.py`: `lint: 0 problem(s) across 36 skills`
- `python3 kb.py drift`: `drift: 0 problem(s)`
- `python3 gates.py`: `gates: 0 problem(s)`
- `python3 gates.py --selftest`: `selftest: ok`

This review is not an unqualified "ready to ship". Four unknowns carry
forward from `verification.md`, and they stay NOT RUN, not passed:

1. **Style match** against the Owner's three reference images: NOT RUN.
2. **Cold-viewer test** (2 of 3 viewers name the steps and the busiest
   station within 30 seconds): NOT RUN.
3. **The Owner would show it** in a real presentation: NOT RUN.
4. **The demo runs as written**: NOT RUN.

The Owner's brief chose to continue through Ship with these open. They
are the quality bar still outstanding, and Ship and Operate (whose
`minimum-signal` is one real presentation) are where they can close. Also
unknown, from Verify's Not verified list: the GIF autoplaying inline on
github.com (rests on WO-0213's earlier note), the click-to-pin, crate lift,
dashed inferred shadow and missing-key fallback notice in a browser, and a
second frame-rate measurement. This review ran the code and the suite; it
did not render the page in a browser, so it adds no evidence on any of
them.
