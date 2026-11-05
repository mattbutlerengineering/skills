---
stage: decompose
run: feature:svg-mechanical-check
date: 2026-11-04
assumptions:
  - "Interview answered from the autorun brief, prd.md and architecture.md; no live cut review was held (step 6), so the milestone boundaries are the drafter's, checked against step 5 only. The Owner can move them at the merge gate."
  - "No tracker mirror: the brief (Tracker) says Decompose mirrors no work-order issues and no issue seeds this run, so no item carries a (tracker: #N) reference and no row carries a WO id. Every Blocked by names an item by its exact title."
  - "docs/factory/decompose-lessons.jsonl does not exist in this repo, so step 3 had nothing to read and the draft is unchanged by it."
  - "Test first: each code item states its tests before its module changes, in line with the brief's constraint ('Test first where behaviour is testable'). The skill and scaffold items are text edits and are checked by the tests that read the scaffolds in place, plus lint."
  - "The battery (run_tests.py, lint.py, kb.py drift, gates.py and its selftest) is run by Implement once at the end of the last milestone and again by Verify, not per item, because the brief's parallel runs share the CPU. Items below carry narrower checks."
---

# Breakdown: A mechanical SVG check for the diagram skills

Progress lives in the checkboxes below — Implement checks items off as their
acceptance criteria are met.

Component names and contract spellings are the architecture's
(`architecture.md`): `svg_check.py`, `check(data, embed_width)`, `Report`,
and the problem strings under "Interfaces & contracts". PRD criteria are
cited as `PRD n`, counting the success-criteria checkboxes top to bottom.

## Milestone 1: the check refuses unsafe files and names the four defects, offline

Demonstrable: `python3 -I svg_check.py <file>` exits 2 on a DTD or entity
without expanding it, and exits 1 naming every missing root size,
duplicate id, dangling reference and external link on a defective file,
with `python3 run_tests.py` covering it.

- [x] **Refusal pass, CLI and exit codes** — create `svg_check.py` with `check`, `Report` and `main`: the expat pass that refuses any DOCTYPE or entity declaration, the not-well-formed refusal, the unreadable-file and bad-usage paths, and the 0/1/2 exit split; create `tests/test_svg_check.py` first, with the two refusal fixtures under `tests/fixtures/svg-check/`.
  - Accept: `tests/test_svg_check.py` is written before the module and fails without it; with it, `entity-expansion.svg` and `external-entity.svg` each make `check` return a `refusal` beginning `refused: the file declares a DTD or an entity` and `main` exit 2 with one `svg-check: <file>: ...` line; the test creates a sentinel file named by `external-entity.svg` and asserts its contents never appear in the output; a truncated file gives `not well-formed: ...` and exit 2; a missing path gives `cannot read: ...` and exit 2; `check(b"<svg/>", 0)` raises `ValueError`. Covers PRD 4, PRD 8 (the module is picked up by `python3 run_tests.py`, offline) and the refusal half of PRD 7.
  - Blocked by: —
- [x] **Root size, duplicate ids, references and external links** — add to `check` the root-element test, root `width`/`height` rule, id collection, the four reference places (`url(#id)` in attributes, `style` attributes and `<style>` text; `href`/`xlink:href`; SMIL `begin`/`end` items), and the external rule, each as the exact problem strings in the architecture; add fixtures `clean.svg`, `no-size.svg`, `dup-id.svg`, `dangling-url.svg`, `external-href.svg`, `all-four.svg` and `same-doc-href.svg`, tests first.
  - Accept: each of the four single-defect fixtures makes `main` exit 1 and print exactly one defect line, and it is that fixture's defect (`root width missing`, `duplicate id "<id>" on <n> elements`, `dangling url(#<id>) in <element> <attribute>`, `external href "<value>" on <element>`), with the offending id or value in the line; `all-four.svg` exits 1 with one line per defect, four lines, not only the first; `same-doc-href.svg` (only `#id` hrefs, all defined) exits 0; a root `width="100%"` gives `root width "100%" is not a px length`; a root `<html>` gives `root element is html, not svg`; `clean.svg` exits 0. Covers PRD 1, 2 and 6.
  - Blocked by: **Refusal pass, CLI and exit codes**
- [x] **Animated reference forms read as references, not misread** — pin and, where the first pass misreads, fix the timing-item parser: `begin="<id>.end"`, `repeat(n)`, a named event, a `;` list, a trailing offset, and clock values (`-1.6s`, `indefinite`) never read as ids; `<mpath href>` and `<use href>` checked; CSS `animation` and `@keyframes` names not read as ids; add `smil-clean.svg`, `css-clean.svg` and a dangling variant of each, tests first.
  - Accept: `smil-clean.svg` (uses `begin="<id>.end"` and `<use href="#id">`) and `css-clean.svg` (uses `animation` and `url(#...)` in a style) each exit 0; each dangling variant, with one referenced id removed, exits 1 naming `dangling timing reference "<id>" in <element> begin` or `dangling url(#<id>) in <element> <attribute>` or `dangling href "#<id>" on <element>` as that variant's case requires; a `begin="1.6s; 0s; indefinite"` fixture line produces no problem. Covers PRD 5.
  - Blocked by: **Root size, duplicate ids, references and external links**

## Milestone 2: the smallest-text reading, the scaffolds and both skills use the check

Demonstrable: a clean SVG prints its smallest text size at the embed width;
both scaffolds pass the check unmodified; both skills' step 7 tell the
generator to run it.

- [x] **Smallest text at embed width** — add the embed-scale rule (`min(root width, embed width)`, `meet` scale over the viewBox, no viewBox means px, an unusable viewBox or root size leaves `smallest_px` unset with a reason) and the text-size reading (inline `style`, then `<style>` rules for `tag`, `.class`, `tag.class` and comma lists, then the `font-size` attribute, walking ancestors; `unread` and `skipped_rules` counts) to `check`, the `--embed-width` option and the pass-line spellings to `main`; tests first, with the fixtures' expected numbers worked by hand in the test, not copied from the output.
  - Accept: `clean.svg` exits 0 and prints `svg-check: <file>: pass — smallest text <N>px at 830px embed width` with N equal to the test's hand-worked figure; `--embed-width 440` changes the line to 440 and N in proportion; a root narrower than the embed width is not scaled up; a fixture whose only text size is `1.2em` prints `... (1 text elements unread)`; a fixture with a `<style>` rule of a complex selector carrying `font-size` prints `1 style rules skipped`; an SVG with no text prints `... no text`; one with no viewBox and a missing root size reports the defect and no guessed number; the counts are absent when zero. Covers PRD 3 and the stdlib half of PRD 7.
  - Blocked by: **Animated reference forms read as references, not misread**
- [x] **Both scaffolds carry a root width and height** — add unitless root `width="880" height="448"` to `skills/architecture-diagram/assets/boilerplate.svg` and `width="880" height="392"` to `skills/animated-diagram/assets/boilerplate.svg`, changing no other line; add tests that read both scaffolds in place (not copied) and assert `check` returns no problems and a readable smallest text.
  - Accept: both scaffold tests fail on the unmodified files for `root width missing` and pass after the edit; `git diff` on each scaffold shows only the root attribute change; each scaffold's `viewBox` width and height equal the new root `width` and `height`. Covers PRD 10 and 11.
  - Blocked by: **Smallest text at embed width**
- [x] **`architecture-diagram` step 7 runs the check** — edit `skills/architecture-diagram/SKILL.md` step 7 to run `python3 -I <skill directory>/../../svg_check.py <file>` first, say what exits 0, 1 and 2 mean for the file (fix each named defect and rerun until 0; exit 2 means remove the DOCTYPE or entity or repair the XML), report the printed smallest-text line, state a check that cannot run (no Python 3) rather than skipping it, and keep the by-eye theme, embed and remove tests; add to the design system's viewBox step the one sentence that the generated file also carries root `width` and `height` equal to the viewBox's. Body-only.
  - Accept: step 7 names the command, all three exits and the no-Python case; the by-eye tests remain; `git diff` shows no change between the `---` lines of the skill's frontmatter; `python3 lint.py` prints no finding for the skill, and the path in the command resolves to the real `svg_check.py` from the skill directory (checked by running the command over the scaffold from that directory and quoting the pass line). Covers PRD 9 and, with the next item, PRD 15.
  - Blocked by: **Both scaffolds carry a root width and height**
- [x] **`animated-diagram` step 7 runs the check on the `.svg` target** — the same instruction in `skills/animated-diagram/SKILL.md` step 7, scoped to the `.svg` target (the `.html` target is not checked, and the text says why), naming the two animated reference forms the check reads (`begin="<id>.end"` and `<mpath href>`) so a generator knows they are checked, and the same one-sentence root `width`/`height` instruction in the design system's viewBox step. Body-only.
  - Accept: step 7 names the command, the three exits, the `.svg`-only scope and both reference forms; `git diff` shows no change to the skill's frontmatter; the command run from the skill directory over its scaffold prints a pass line, quoted. Covers PRD 9 and 15.
  - Blocked by: **Both scaffolds carry a root width and height**

## Milestone 3: records, the skill-map read and the full battery

Demonstrable: the repo's records match what shipped, the skill map has been
read with the real tool, and the battery is green.

- [x] **Records: tool entry and backlog claim** — add one `svg_check.py` entry beside `voice_grade.py`'s in the on-demand tools list of both `AGENTS.md` and `CLAUDE.md` (free, offline, outside every gate), and mark `docs/backlog.md` line 91 (the boilerplate's missing width/height) claimed by `feature:svg-mechanical-check` in the form the file's other claims use, leaving the text-floor half of that line as an open seed.
  - Accept: the two tool-list entries are the same sentence in both files; `docs/backlog.md` line 91 carries the claim in the file's existing claim form, matched by reading two existing claimed lines; the line's text-floor half is still unclaimed. Covers PRD 12.
  - Blocked by: **Both scaffolds carry a root width and height**
- [x] **Read the README skill map with the real tool** — run `python3 -I svg_check.py docs/assets/skill-map.svg` and quote its output into the Notes below; if it reports a defect, add one seed to `docs/backlog.md` for it, in the file's seed form; leave `docs/assets/skill-map.svg` unchanged.
  - Accept: the command's real output is quoted in Notes; `git diff --stat -- docs/assets/skill-map.svg` prints nothing; every defect line the output carries has a matching seed in `docs/backlog.md`, or the output is a pass line and no seed is added. The architecture's 9.4px figure is a prediction and is not copied in as a result. Covers PRD 16.
  - Blocked by: **Smallest text at embed width**
- [x] **Packaging and the battery** — run, from the worktree, `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`, `python3 gates.py && python3 gates.py --selftest` and `python3 factory_init.py update-manifest`; fix what the first four find that this run caused; confirm no frontmatter `description` changed.
  - Accept: the four battery commands exit 0, with their summary lines quoted; `update-manifest` leaves `git status --porcelain` with no change to the manifest (the architecture expects none, since `svg_check.py` is root-only and unmirrored; a change means that expectation was wrong and is a design gap to record, not to work around); `git diff origin/main -- skills/*/SKILL.md` shows no change to any `description:` line; no `claude plugin eval`, `trigger_eval.py`, `charter_replay.py` or `claude -p` was run. Covers PRD 13, 14 and 15.
  - Blocked by: **`architecture-diagram` step 7 runs the check**, **`animated-diagram` step 7 runs the check on the `.svg` target**, **Records: tool entry and backlog claim**, **Read the README skill map with the real tool**

## Design gaps found

none. Every architecture component (`svg_check.py`, `tests/test_svg_check.py`
with its fixtures, both step-7 edits, both scaffolds, the records) appears
in an item, and PRD criteria 1 to 16 are each cited by one. Two spots the
architecture leaves to Implement without a gap: the exact claim spelling in
`docs/backlog.md`, which the file's existing claims set, and the exact
fixture numbers, which the smallest-text item has the test work by hand.

## Notes

2026-11-04 (Implement) — deviations and evidence:

- `Report` gained one field the architecture's Data model omits: `note: str | None`, the reason `smallest_px` is unset (`no text`, or the stated reason an unusable scale gives). The architecture's contract says "unset with a stated reason" without a place to hold it; no design change.
- A non-svg root's problem names the root's full tag: `root element is html, not svg` for `<html>`, and `root element is {http://example.com/x}svg, not svg` for an `<svg>` in another namespace. Nothing else is read for a non-svg root.
- The `<style>` block's problem spelling is `... in <style>` (the whole `<element> <attribute>` phrase replaced), e.g. `dangling url(#g) in <style>`.
- Design gap, fixed here: `tests/test_factory_cli.py` requires every root module with a `__main__` guard to have a verb in `factory.py`'s `VERBS`, which the architecture did not name. Added `svg-check` there (`factory.py` is not in `factory_init.MIRRORS`, so the manifest is unchanged) and one sentence in the `AGENTS.md` and `CLAUDE.md` entry.
- Design gap, fixed here: detector O (ADR-0072) reads only work-order rows, and this run has none (brief, Tracker), so `prd.md`'s seven `##` sections carry a reasoned `<!-- coverage-waiver: ... -->` each. Decompose did not add them.
- `docs/backlog.md` line 91 is one seed holding both halves, so claiming it would claim the text-floor half too. The claim marker went on line 91 and the text-floor half was appended as a new open seed at the end of the file (the file is append-only).
- Edit-tool paths: a first batch of step-7 and design-system edits landed in the main checkout because the edit tool resolved relative paths against it. They were moved into this worktree as a patch and the main checkout's four files restored with `git checkout --`; `git status` there is clean.
- Skill map read (item "Read the README skill map with the real tool"), real output of `python3 -I svg_check.py docs/assets/skill-map.svg`: `svg-check: docs/assets/skill-map.svg: pass — smallest text 9.4px at 830px embed width`, exit 0. No defect line, so no seed was added; `git diff --stat -- docs/assets/skill-map.svg` prints nothing.
- Scaffolds, run from each skill directory as `python3 -I ../../svg_check.py assets/boilerplate.svg`: `svg-check: assets/boilerplate.svg: pass — smallest text 7.5px at 830px embed width` (architecture-diagram) and `... smallest text 8.5px at 830px embed width` (animated-diagram).
- Battery, from this worktree after the last code commit: `python3 run_tests.py -j 3` printed `tests: 4026 tests across 127 modules in 87.7s on 3 workers, 0 problem(s)`; `python3 lint.py` `lint: 0 problem(s) across 35 skills`; `python3 kb.py drift` `drift: 0 problem(s)`; `python3 gates.py` `gates: 0 problem(s)` and `python3 gates.py --selftest` `selftest: ok`; `python3 factory_init.py update-manifest` `factory-init: 0 problem(s)` and left no manifest change in `git status --porcelain`. No `description:` line changed in any SKILL.md (`git diff -U0 skills/*/SKILL.md | grep '^[-+]description'` printed nothing). No `claude plugin eval`, `trigger_eval.py`, `charter_replay.py` or `claude -p` was run.
