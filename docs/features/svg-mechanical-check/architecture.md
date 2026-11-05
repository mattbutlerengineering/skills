---
stage: architect
run: feature:svg-mechanical-check
date: 2026-11-04
ux: skipped — Skill text and a stdlib check with text output only; no screens or flows.
assumptions:
  - "Interview answered from the autorun brief, prd.md and the codebase; the skill's trade-off read-out (step 6) was not held live. The decisions that could have gone another way are recorded, with the option that lost, under Decisions & alternatives."
  - "The check is a root-only module, svg_check.py, run as python3 -I <skill directory>/../../svg_check.py. The brief ('Architect's call') and the PRD (open question 2) left inline snippet versus shipped script open; the skill offers no default. Taken from the codebase's own pattern for a skill that runs a tool (pipeline-board runs board.py, house-voice's grader is voice_grade.py), not from the Owner."
  - "The embed width defaults to 830 CSS px and is overridable with --embed-width. The brief names no width and the PRD asked for one to be defined; 830 is the value the readme-skill-map run recorded as GitHub's README column (docs/features/readme-skill-map/breakdown.md, Verify of the figure: 'an 830px column (GitHub's README width)'). It is repo data from an earlier run, not an Owner answer and not re-measured here."
  - "Smallest text is reported, never a failure. PRD open question 3 asked whether a floor is wanted; the seed says 'read', the PRD treats it as a report, and the brief records no Owner floor, so none is set. The text floor the design systems carry is a separate seed (backlog line 91's text-tier half), outside the PRD's criteria."
  - "The animated-diagram scaffold is fixed here, not seeded. PRD criterion 11 allows either; both scaffolds carry a viewBox and no root width/height (read from the two files at this stage), the fix is the same one attribute pair, and the animated skill is in scope."
  - "No ADR. The root-versus-asset placement, the refusal of every DOCTYPE and the report-only reading are each cheap to reverse (move a file, loosen a handler, add a flag) and none is surprising to a reader of the code, so none passes the protocol's three-leg test; each keeps its one-line record below."
---

# Architecture: A mechanical SVG check for the diagram skills

## Approach

One new root module, `svg_check.py`, stdlib only, and two edited skills.
The module exposes one deep function, `check(data, embed_width)`, that
hides everything a caller would otherwise have to know to be safe: it
refuses a DTD or entity before any parse that could expand it, reads
ids, references and text sizes from the parsed tree, and returns the
defects as label-prefixed problem strings plus the text reading. A thin
`main` prints them and sets the exit code. Both diagram skills' step 7
tell the generator to run it (`python3 -I`) over the file it produced
and say what each exit code means; the by-eye checks stay for what a
parser cannot see (themes, contrast, layout). The `architecture-diagram`
and `animated-diagram` `.svg` scaffolds get a root `width` and `height`
so they pass the check unmodified.

The shape that lost is an inline `python3 -c` snippet in each SKILL.md:
about a hundred lines of XML handling pasted twice, with nothing to
test. A script inside the skill directory lost too (Decisions below).

## Components

### svg_check.py (root-only module)

- Responsibility: given one SVG's bytes, say whether it is refused,
  which of the five properties are defective, and what the smallest text
  is at the embed width. Owns the refusal rule, the reference grammar
  (what counts as an id reference, where) and the text-size reading
  rule. Nothing else in the repo restates them.
- Collaborators: Python standard library only (`xml.parsers.expat`,
  `xml.etree.ElementTree`, `re`, `argparse`, `sys`). Imports no sibling
  root module, so it adds no row to ADR-0091's dual-membership pin and
  is not in `factory_init.MIRRORS`: nothing in the payload imports it, so
  it ships in the plugin as a root file like `voice_grade.py` and the
  factory manifest does not change.

### tests/test_svg_check.py with tests/fixtures/svg-check/*.svg

- Responsibility: pin the contract through `check` and `main`, offline,
  with committed fixture SVGs. `run_tests.py` picks the module up by its
  name. Fixtures: `clean.svg`; four single-defect files
  (`no-size.svg`, `dup-id.svg`, `dangling-url.svg`, `external-href.svg`);
  `all-four.svg`; `entity-expansion.svg` and `external-entity.svg`
  (refused; the second names a sentinel file the test creates and asserts
  never appears in the output); `smil-clean.svg`, `css-clean.svg` and a
  dangling variant of each; `same-doc-href.svg`; and the repo's two
  `.svg` scaffolds read in place (not copied), so a scaffold that drifts
  fails here.
- Collaborators: `svg_check`.

### skills/architecture-diagram/SKILL.md, step 7

- Responsibility: instruct running the check first, and say what each
  outcome means for the file. Keep the by-eye theme, embed and remove
  tests. Body-only; the frontmatter `description` does not change, so no
  routing eval is owed.
- Collaborators: `svg_check.py`.

### skills/animated-diagram/SKILL.md, step 7

- Responsibility: the same instruction, scoped to the `.svg` target. The
  `.html` target is not checked (HTML is out of scope; it carries inline
  SVG, not a standalone file). Names the two animated reference forms the
  check reads as references, so a generator knows `begin="<id>.end"` and
  `<mpath href>` are checked, not misread.
- Collaborators: `svg_check.py`.

### The two `.svg` scaffolds

- Responsibility: `skills/architecture-diagram/assets/boilerplate.svg`
  and `skills/animated-diagram/assets/boilerplate.svg` each carry root
  `width` and `height` equal to the viewBox's (880x448 and 880x392),
  unitless. Both pass the check unmodified; no other line changes. The
  design systems' step-3/step-4 text that says `viewBox` = content + 32
  gains the same instruction for the generated file, one sentence each.
- Collaborators: `svg_check.py` reads both in the test above.

### Records the run updates

- Responsibility: `docs/backlog.md` line 91 marked claimed by
  `feature:svg-mechanical-check` (the width/height half); AGENTS.md and
  CLAUDE.md, which carry the same on-demand tools list, each gain one
  entry for `svg_check.py` beside `voice_grade.py`'s, stating it is free,
  offline and outside every gate; any defect the check finds in
  `docs/assets/skill-map.svg` becomes a seed, and the file is unchanged.
- Collaborators: none.

## Data model

No stored data. The in-memory shape `check` returns:

```text
Report
  refusal:      str | None     # set => nothing else is read
  problems:     list[str]      # label-prefixed, one per defect
  smallest_px:  float | None   # smallest text at embed width; None if no text
                               # or the size could not be read
  embed_px:     float          # the width the reading used
  unread:       int            # text elements whose size was not resolved
  skipped_rules: int           # <style> rules with a font-size the reader
                               # does not read (complex selector, at-rule)
```

Access patterns (the only reads and writes the PRD requires): read one
file; list defects; read one number. Nothing persists between runs.

**Reading rules (the answers to the PRD's open questions).**

- *Refusal.* A first pass with `xml.parsers.expat` sets
  `StartDoctypeDeclHandler` and `EntityDeclHandler` to refuse, and
  parameter-entity parsing off. Any `<!DOCTYPE` is refused, including a
  benign one, because no entity can exist without one and the refusal
  fires at the declaration, before an entity is defined or used. Only a
  file that passes this pass is handed to `xml.etree.ElementTree`, which
  then cannot expand anything but the five predefined entities.
- *Ids.* Every `id` attribute on any element. A duplicate names the id
  and the count.
- *References.* Four places, each name checked against the id set:
  `url(#id)` in any attribute value, in a `style` attribute and in
  `<style>` text; `href` and `xlink:href` on any element (`<use>`,
  `<mpath>`, `<textPath>`, `<image>`, `<a>`); SMIL `begin` and `end`
  timing items of the form `<id>.<event>` (`begin`, `end`, `repeat(n)`,
  a named event) split on `;`, with a trailing offset ignored — a clock
  value such as `-1.6s` or `indefinite` never matches and is never
  read as a reference. CSS `animation` and `@keyframes` names are not
  ids and are not read.
- *External.* An `href`/`xlink:href` value, or a `url()` target, that
  does not start with `#`. A `data:` URI counts: the PRD says "any value
  not starting with `#`", and neither scaffold embeds one. An
  `@import url(...)` in `<style>` is caught by the same `url()` rule.
- *Root size.* The root must be `<svg>` in the SVG namespace. `width` and
  `height` must each be present and a positive number, unitless or with
  `px`. A percentage, `em`, or any other unit is a defect ("not a px
  length"), because it gives an `<img>` no intrinsic size.
- *Embed scale.* Rendered width = `min(root width, embed width)`: an
  `<img>` is scaled down to the column and not scaled up. Content scale =
  `min(rendered / viewBox width, rendered x (height / width) / viewBox
  height)`, so a viewBox that does not match the root's aspect ratio
  yields the smaller (`meet`) scale rather than a refusal. No viewBox
  means user units are px. A viewBox that is not four numbers with a
  positive width and height, or a missing/invalid root size, leaves
  `smallest_px` unset with a stated reason, and never a guessed scale.
- *Text size.* For each `<text>` and `<tspan>` carrying non-blank text,
  the size is the first px or unitless `font-size` found walking from the
  element up through its ancestors, in this precedence at each element:
  inline `style`, then `<style>` rules whose selector is `tag`, `.class`,
  `tag.class` or a comma list of those (class rules beat tag rules; the
  later rule wins a tie), then the `font-size` attribute. Anything else —
  `em`, `%`, `var(...)`, `rem`, no declaration at all — leaves that
  element unresolved and counted in `unread`. `<style>` rules with a
  `font-size` under any other selector or inside an at-rule are counted
  in `skipped_rules`. Both counts are printed, so a reading that skipped
  something never looks complete. The result is the minimum resolved size
  x content scale.

## Interfaces & contracts

### `svg_check.check(data: bytes, embed_width: float = 830.0) -> Report`

- Input: the SVG file's bytes; the embed width in CSS px (positive).
- Output: a `Report`. Each defect is one problem string, the exact
  spellings the tests assert (the CLI prefixes `svg-check: <file>: `):
  - `root width missing`, `root height missing`, or `root width "<v>" is
    not a px length` (and the same for height)
  - `duplicate id "<id>" on <n> elements`
  - `dangling url(#<id>) in <element> <attribute>` (`<style>` for a
    `<style>` block)
  - `dangling href "#<id>" on <element>`
  - `dangling timing reference "<id>" in <element> <attribute>`
  - `external href "<value>" on <element>`
  - `external url(<value>) in <element> <attribute>`
  - `root element is <name>, not <svg>`
- Failure modes: never raises on file content. Not well-formed XML sets
  `refusal` to `not well-formed: <parser message>`; a DTD or entity sets
  it to `refused: the file declares a DTD or an entity (remove the
  <!DOCTYPE>; the check does not expand either)`. With `refusal` set,
  `problems` is empty and no other field is read. A defect list is never
  empty-and-green when the file could not be read. An invalid
  `embed_width` raises `ValueError`; that is a caller bug, not input.
  Retry is safe: pure function of its arguments.

### `python3 -I svg_check.py <file.svg> [--embed-width PX]`

- Input: one file path; optional embed width, default 830.
- Output on exit 0, one line:
  `svg-check: <file>: pass — smallest text <N>px at <W>px embed width
  (<k> text elements unread, <j> style rules skipped)`, or
  `... no text` when there is none, or `... smallest text not read:
  <reason>` when the scale could not be computed. The counts are printed
  only when non-zero.
- Output on exit 1: one `svg-check: <file>: <problem>` line per defect,
  then the text line when it could be read. Every defect in the file is
  named, not only the first.
- Exit 2, one `svg-check: <file>: <refusal or cannot read: ...>` line: bad
  usage, an unreadable file, a refusal. The file was not checked, so it
  is neither a pass nor a defect list; the skill text says to fix the
  file and rerun. The 0/1/2 split follows `decompose_grade.py`
  (ADR-0114).
- Failure modes: no network, no write, no model; the module does not
  enforce `-I` (the skill text passes it, and the script imports only the
  standard library so the flag costs nothing). A very large file is read
  whole; the file is the user's own and the refusal above is the
  untrusted-input defence, not a size cap.

### The step-7 instruction (both skills)

- Input: the path of the SVG the generator just wrote.
- Output: the generator runs the check, fixes each named defect in the
  file and reruns until exit 0, and reports the smallest-text line it
  printed. Exit 2 means remove the DOCTYPE/entity or repair the XML.
- Failure modes: a check that cannot run (no Python 3) is stated, never
  skipped silently; the by-eye steps still apply.

## Stack & dependencies

- Python 3 standard library only (`standards.json` slug `stdlib-only`) —
  the brief's constraint and the repo's hard convention; `defusedxml`
  would solve the entity problem but is a dependency.
- `xml.parsers.expat` for the refusal pass, `xml.etree.ElementTree` for
  the tree — the brief names `xml.etree`; expat is the stdlib parser it
  wraps and the only place the DOCTYPE and entity declarations can be
  intercepted (`ElementTree.XMLParser` has no `.parser` attribute on the Python 3.14
where this was checked).
- A root module, not a script in a skill directory — see below.

## Decisions & alternatives

- **A root-only `svg_check.py` run from both skills** over an inline
  `python3 -I -c` snippet in each skill — the snippet is a hundred lines
  pasted twice and cannot be tested, and a tool owns the rules once. Over
  a script in `skills/architecture-diagram/assets/` — lint would allow the
  second skill to name it as a sibling asset, but the repo's tools that a
  skill runs are root modules (`board.py`, `voice_grade.py`), and a
  second place for tools is a second convention. Also over a copy in each
  skill — two owners of one rule (`one_owner.py`'s whole point).
- **Refuse every DOCTYPE and entity declaration** over parsing with
  entity limits or a third-party hardened parser — `defusedxml` breaks `stdlib-only`, a
  limits-based parse still expands entities the file chose, and a
  scaffold-style SVG needs neither. Cost: a benign DOCTYPE (editors such
  as Inkscape write one) is refused until removed; the message says so.
- **Embed width an argument defaulting to 830** over a constant (the
  README is not the only embed) and over reading the width from a README
  (the check would then need a README path and a parser for it).
- **Report the smallest text, never fail on it** over a floor flag — the
  PRD treats it as a report and the Owner set no floor; a floor is the
  design systems' seed, and a flag without a value is a stub.
- **Unresolved sizes and skipped rules are counted and printed** over a
  full CSS cascade (cost out of proportion to a report) and over silent
  skipping (a green reading that skipped text is the failure ADR-0107
  names: unknown never rolls up to pass).
- **Scope the root size to px or unitless** over accepting any absolute
  unit — one fewer unit table, and the scaffolds and the skill map are
  px.
- **A `data:` URI is external** over exempting it — the PRD's literal
  rule, and no scaffold needs one.
- **Fix the animated-diagram scaffold in this run** over seeding it —
  one attribute pair, and a scaffold that fails its own step 7 ships
  broken (the brief's scope call for the other scaffold applies equally).
- **Check only the `.svg` target of `animated-diagram`** over also
  extracting the SVG from the `.html` — HTML is out of scope in the
  brief.

Traceability: stories 1-3 and criteria 1-3, 5-6 are `check` and its
fixtures; story 4 and criterion 4 are the refusal pass; criteria 7-8
are the module's stack and the test module; criterion 9 is the step-7
edits; 10-12 are the scaffolds and the backlog claim; 13 is the packaging
(a root-only module: no manifest or lint change expected, Verify runs
both); 14 is the battery, run at Verify; 15 is the unchanged
descriptions; 16 is the skill-map read.
The skill map under this reading, from a throwaway read of the file
during this stage: it has root `width`/`height` 880x688, no duplicate or
dangling id and no `href`, and its smallest declared tier is 10px, which
the design predicts reads as about 9.4px at 830px. That is a prediction
for Verify to confirm with the real tool and, if it is a finding, to
seed; it is not a result.

## ADRs

none — no decision met the ADR bar.
