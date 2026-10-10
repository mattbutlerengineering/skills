---
stage: architect
run: feature:readme-skill-map
date: 2026-10-07
ux: skipped — static document; the figure's visual design is the architect's and implementer's concern, not a flow or screen
assumptions:
  - "The skill's trade-off read-out (step 6) was not held live; every decision that could have gone another way is recorded under Decisions & alternatives with the option that lost, per the autorun brief. The seven questions PRD-0008 routed here are answered there, lettered (a)-(g)."
  - "The group cut is this stage's — idea.md's hunch supplied six moments (before a run exists, while driving one, around a pull request, installing the factory, reshaping a codebase, drawing pictures) and the brief named no members, so which skill sits in which card, the card titles, and the placement of lean and polish (both join 'Reshaping what's built') are taken without user input, from each skill's own description."
  - "The figure carries skill slugs and the six card titles only; the one-line why per utility skill lives in the README table alone (PRD-0008 left a figure why-line to this stage under idea.md's density risk)."
  - "The figure's path (docs/assets/skill-map.svg), the checker's name (check_readme_figure), its problem strings and its visible-text reading rule are this stage's wording, following the sibling check_readme_skills; the brief and PRD fix the roster and the one-roster rule, not the names."
  - "The README embeds the figure as a plain markdown image and the SVG root carries intrinsic width and height beside its viewBox; neither the brief nor the diagram skill states an embed form, and this one needs no HTML in the README."
  - "No ADR (architect skill step 7, offer sparingly) — the checker is a sibling in an established lint pattern whose earlier members (check_readme_no_orphans, check_plugin_skills) got none, and the figure is packaging. The pull request still lands through the human gate because it carries this file (ADR-0036, clause 3), which is already the brief's plan."
---

# Architecture: README skill map

## Approach

One committed, self-contained SVG at `docs/assets/skill-map.svg`, drawn
with the plugin's own `architecture-diagram` skill — still, warm-paper
light with the family's dark palette behind one `prefers-color-scheme`
block — replaces the mermaid chain at the top of README.md. The pipeline
is drawn as a closed loop (idea through operate and back) with the router
inside it as the one accented element and `capture` entering from
outside; the thirteen utility skills are not thirteen more boxes but text
rows inside six **moment cards** ("Before a run exists", "Driving a run",
…), so the figure has two layers — the loop and the cards — and stays one
picture at README width. Under `## Stages` the sixty lines of utility
prose become a table whose rows carry the same moment labels, one row per
`protocol.UTILITY_SKILLS` entry. One new lint checker,
`check_readme_figure`, holds the figure's visible text to the roster
`check_readme_skills` already reads (`ALL_SKILLS + extra_skills(root)`,
matched by `names_slug`) and holds README.md to embedding that file — one
roster, one path constant, no second slug list. The alternative shape —
two figures (an overview and a detail) as the diagram skill's complexity
budget would have it — loses because it splits the thirty-second read
across two pictures and doubles the surface the roster check must cover;
the brief and PRD-0008 fix one figure. The other alternative — drawing it
with `animated-diagram` — loses below under (a).

```tree-claims
# What this design edits or reads, as it stands in this worktree on 2026-10-07.
exists: README.md
exists: lint.py
exists: protocol.py
exists: cli.py
exists: tests/test_lint.py
exists: skills/architecture-diagram/SKILL.md
exists: skills/architecture-diagram/assets/boilerplate.svg
exists: skills/architecture-diagram/references/design-system.md
exists: docs/features/readme-skill-map/prd.md
```

## Components

### The figure (`docs/assets/skill-map.svg`)

- Responsibility: the one picture a newcomer reads first. It shows what
  the mermaid chain shows today — the router, the ten ordered stages, the
  UX conditional, the operate-to-idea loop — plus `capture` (which the
  chain omits today but `ALL_SKILLS` registers) and every utility skill
  placed in a titled moment card. Model, in the diagram skill's terms:
  - Nodes: `idea`, `prd`, `ux-design`, `architect`, `decompose`,
    `implement`, `verify`, `review`, `ship`, `operate` (solid treatment,
    name = the slug, mono sublabel = the stage artifact as the mermaid
    shows it today); `next` (the focal element — the only accent — sitting
    inside the loop, sublabel naming it as the router); `capture` (solid,
    outside the loop, sublabel `defect.md`); six cards (one node-like
    container each, title = the moment, mono rows = member slugs).
  - Edges: ten solid connectors closing the loop idea→prd→ux-design→
    architect→decompose→implement→verify→review→ship→operate→idea (the
    closing edge labelled as the retro seeding the idea); one dashed
    skip prd→architect labelled for the no-UI case; one dashed re-entry
    capture→architect or capture→implement — the two depths
    `defect.md` records; the implementer takes whichever runs straight.
    Twelve connectors, the budget's ceiling. The router has no arrow:
    sitting inside the loop says it can hand off to any stage, and the
    mermaid's single arrow into idea was always a stand-in.
  - Zones: none; the cards are nodes, not zones.
- Constraints the PRD fixes and the implementer inherits: without any
  script, web font, `@import` or remote `href`; every skill name as literal
  `<text>` content (the checker reads nothing else), the bare slug
  verbatim (no leading slash, no display-cased name — `names_slug` is
  case-sensitive and whole-slug); no slug-shaped English in the title,
  subtitle, edge labels or legend (a subtitle saying what to reach for
  "next" would satisfy the router's roster line by accident); no counts
  anywhere in the figure (a "thirteen" rots the day lean lands); viewBox
  880 wide as the family scaffold is, with no text tier below 10px so
  nothing needs zooming at README width; and `width`/`height` attributes
  on the `<svg>` root equal to the viewBox — the scaffold has only a
  viewBox, and an SVG with no intrinsic size is fitted to the browser's
  300×150 default object size inside `<img>` — a thumbnail. That attribute is a known
  hand-edit; Verify records it under the Provenance criterion as a
  finding about the scaffold, not a patch to it (out of scope).
- Collaborators: `skills/architecture-diagram` (scaffold, tokens,
  connector grammar, verify steps — followed as written); README.md (the
  embed); `check_readme_figure` (the roster).

### The six moment cards (the group cut)

| Card title | Members today | Joins once its directory exists | Sits by |
|---|---|---|---|
| Before a run exists | `audit`, `automate` | — | the loop's entry at idea |
| Reshaping what's built | `deepen` | `lean`, `polish` | the entry, beside the card above |
| Driving a run | `autorun`, `work-queue` | — | inside the loop, with the router |
| Around a pull request | `address-pr-review` | — | the review–ship stretch |
| Drawing pictures | `mermaid`, `architecture-diagram`, `animated-diagram`, `interactive-architecture-diagram`, `pipeline-board` | — | below the loop; any stage |
| Installing the factory | `factory-init`, `doctor` | — | below the loop; once per repo |

- Responsibility: carry the moment a person reaches for a skill — the
  card title says it, placement reinforces it where the grid allows. The
  cut follows each skill's own description: `audit` and `automate`
  survey a repo with no run in flight and hand off to `idea` or
  `capture`; `deepen` takes something already built and proposes a
  deeper shape, and `lean` (a cut-list for a diff or a tree) and `polish`
  (a built surface taken from working to considered) describe
  themselves against `review`, `audit`, `deepen` and `ux-design` — the
  same "what exists, made better" question — so both join that card;
  `autorun` and `work-queue` steer the loop, so they sit inside it;
  `address-pr-review` is the only skill whose situation is an open pull
  request; the five diagram makers and the two factory skills each name
  a single, self-evident moment. Thirteen members today, the sum the
  README table must also reach.
- Collaborators: the README table's Moment column uses these six titles
  verbatim, so figure and table agree without a checker.

### README.md: the embed and the `## Stages` table

- Responsibility: show the figure where the mermaid block is now and say
  why each utility skill matters. The mermaid fence is deleted and
  replaced by one markdown image line referencing
  `docs/assets/skill-map.svg` with alt text that summarises the figure in
  a sentence. Under `## Stages` the stage table stays byte-for-byte; the
  prose paragraph below it becomes a short lead-in that keeps the
  ADR-0023 link and points up at the figure, then a table with the
  columns Skill, Moment, Why it matters — exactly one row per
  `protocol.UTILITY_SKILLS` entry, rows grouped in card order, the slug
  in backticks, the moment as plain text, the why as one line distilled
  from that skill's description. The closing sentence pointing at
  `docs/pipeline-protocol.md` stays. Inside `## Stages` the only backtick
  tokens are skill slugs (and the existing filenames, which carry a dot
  and never match `SLUG_TOKEN`): no backticked `main`, `gh`, `make` or
  other slug-shaped word, because `check_readme_no_orphans` reads every
  such token as a skill claim. Nothing names `lean` or `polish` until
  their directories exist. Install, Usage, Development and License are
  untouched; `.claude-plugin/plugin.json` is untouched (README.md is not
  in `factory_init.MIRRORS`).
- Collaborators: `check_readme_skills` (every slug named somewhere — the
  table supplies the utility ones, the stage table the rest),
  `check_readme_no_orphans` (section scope), `check_readme_figure` (the
  embed line).

### `lint.check_readme_figure` (new sibling checker)

- Responsibility: fail the build when the committed figure fails to name
  any skill in the roster, or when README.md no longer embeds the file
  lint is checking. It reads the roster exactly as `check_readme_skills`
  does — `ALL_SKILLS + extra_skills(root)` through `names_slug` — and
  keeps no slug list of its own; it reads the figure through
  `cli.read_file(..., str)` (ADR-0075), parses it with
  `xml.etree.ElementTree`, and matches against the joined text content of
  every `<text>` element (tspans included), never the raw bytes: an `id`
  attribute, a comment or a `<style>` rule that happens to contain a slug
  is not a name a reader can see. The path is one module constant,
  `README_FIGURE = "docs/assets/skill-map.svg"`, beside `STAGES_HEADING`,
  the other README structural fact lint owns. Registered in `CHECKERS`
  directly after `check_readme_no_orphans`.
- Collaborators: `protocol.ALL_SKILLS` (the taxonomy owner),
  `extra_skills`, `names_slug`, `cli.read_file`; `tests/test_lint.py`
  (`make_clean_tree` gains the figure — one `<text>` per `ALL_SKILLS`
  slug — and an embed line in the fixture README, so `TestCleanTree`
  keeps passing every checker; a new `TestReadmeFigure` pins the strings
  below through the public function, including the one-skill-missing
  case the PRD names and the slug-only-in-an-attribute case that pins
  the visible-text rule). The new test fails against the pre-change
  commit because the function does not exist there.

## Data model

Three read-only text shapes, chosen from who reads them and when:

1. **The roster** — `protocol.ALL_SKILLS` plus the on-disk extras
   `extra_skills(root)` finds. Owner: `protocol.py` and the `skills/`
   tree. Read once per lint run by every roster checker; consistent by
   construction because every checker reads the same tree at the same
   moment. This is the invariant the feature exists to hold: the figure,
   the README text and the plugin description all equal the roster, each
   checked by its own thin caller of the same two functions.
2. **The figure's visible text** — the `<text>` content of
   `docs/assets/skill-map.svg`. Owner: the SVG file, hand-placed by the
   implementer under the diagram skill. Read by the checker (whole slugs)
   and by readers (whole figure). Must-be-true-at-lint-time; there is no
   later settling.
3. **The `## Stages` section** — the stage table, the lead-in, the
   utility table. Owner: README.md. Read by `readme_stage_mentions` as a
   set of backtick tokens (orphans) and by `check_readme_skills` as free
   text (coverage). The utility table's row count equalling
   `len(protocol.UTILITY_SKILLS)` is checked at Verify by counting, not
   by a lint rule: the forward and reverse checks already bound the set,
   and a duplicate row is a wording defect the review reads.

No new entity, file format or state: the figure's path is a constant, the
moment labels are prose shared by figure and table, and the roster has
one owner.

## Interfaces & contracts

### `lint.check_readme_figure(root)`

- Input: the repo root `Path`, like every checker.
- Output: a list of label-free problem strings (lint's `LINT:` prefix is
  applied at print time), empty when clean. Roster problems first, in
  roster order (`ALL_SKILLS` order, then extras sorted), then the embed
  problem:
  - `docs/assets/skill-map.svg never names skill 'lean'` — one per
    missing slug, whole-slug matched (`architecture-diagram` inside
    `interactive-architecture-diagram` is not a mention; `architect`
    inside `architecture-diagram` is not one either).
  - `README.md never embeds 'docs/assets/skill-map.svg'` — README.md
    exists and its text does not contain the constant. A missing
    README.md is skipped here, as `check_readme_no_orphans` skips it:
    `check_readme_skills` already reports it.
- Failure modes, each one string and an early return, so a broken file
  never fans out into twenty-five roster lines:
  - `missing docs/assets/skill-map.svg` — `read_file` returned
    `(None, None)`.
  - `cannot read docs/assets/skill-map.svg: <err>` — `read_file`'s own
    wording for an `OSError` or bytes that are not UTF-8, passed through.
  - `docs/assets/skill-map.svg is not valid SVG: <err>` — the
    `ElementTree.ParseError` text, worded after `read_file`'s
    `is not valid JSON` rule for a document that fails its grammar.
  Local filesystem only: no timeout, retry always safe, idempotent.

### The README embed → GitHub's render

The one seam that crosses a process boundary, and it is not ours to call:
github.com fetches `docs/assets/skill-map.svg` through its image proxy
and the reader's browser renders it as an image document.

- Input: the markdown image line in README.md; the committed SVG.
- Output: the figure at the README's content width, light or dark per the
  reader's browser/OS `prefers-color-scheme`, which is what the one
  `@media` block inside the SVG answers to — GitHub's own appearance
  setting, when set opposite the OS, does not reach inside an `<img>`
  (the diagram skill's documented trade for a single committed file).
- Failure modes and what the reader sees: a proxy that drops the file —
  a broken-image box, which is why the SVG carries no external request to
  be refused; a browser ignoring the media query inside an image document
  — the light figure in a dark page, legible but unflipped; no intrinsic
  size — a 300px-wide thumbnail, which the root `width`/`height`
  attributes prevent. Retry is a page reload; nothing is stateful.
- Verification plan (the PRD's Figure criterion): the real github.com
  README page, GitHub appearance set to sync with the system, the OS
  appearance toggled between light and dark with a reload each time, one
  screenshot per setting in `verification.md`. A local preview does not
  count. If the dark flip does not happen on github.com, the recorded
  fallback is a `<picture>` element — `<source
  media="(prefers-color-scheme: dark)">` pointing at a forced-dark copy
  made per the design system's theme mechanics (media query replaced by
  the fixed palette, nothing else changed) over the same `<img>` — with
  `README_FIGURE` widened to both files so the roster check covers both;
  its cost is a second file to keep identical in text, which is why it
  is the fallback and not the plan.

### The drawing contract (what Implement hands Verify)

- Input: the model under The figure, the card table, the diagram skill's
  seven steps and `references/design-system.md`.
- Output: one `.svg` that passes `grep -E 'http|<script|@import|@font-face'`
  with no match, names every roster slug as `<text>`, carries root
  `width`/`height`, and renders both themes standalone and embedded.
- Failure modes: a skill weakness met on the way — the node budget, the
  missing intrinsic size, any grammar rule the roster map cannot honour —
  is recorded in `verification.md` as hand-editing under the Provenance
  criterion, never patched in `skills/` (out of scope), so the front
  page's dogfooding claim stays honest.

## Stack & dependencies

- Python 3 standard library only — `xml.etree.ElementTree` for the
  figure, `re` and `pathlib` as lint already uses (`stdlib-only`).
- `skills/architecture-diagram` — scaffold, tokens, grammar and verify
  steps; the figure is its output, and the PRD's Provenance criterion
  requires exactly that.
- GitHub-flavoured markdown's image rendering and image proxy — the one
  dependency on someone else's schedule; isolated by making the SVG
  self-contained, and verified on the real page rather than assumed.

## Decisions & alternatives

- **(a) `architecture-diagram`, and the figure does not move** over
  `animated-diagram`'s pure-SVG SMIL target — the animated skill's
  output is dark-only by its own design system, so it fails user story 2
  (legible in both appearance settings) and would sit as a dark slab on a
  light README; its motion encodes execution direction, and this figure
  is a map of where things are, not a flow a request takes — the moving
  dashes would compete with the labels the thirty-second test is timed
  on and add a reduced-motion obligation for nothing; and its budget is
  tighter still (seven nodes, "motion tolerates less density than a
  still figure"). The still skill is theme-aware, image-embeddable and
  the family member whose own note says it embeds in READMEs. The PRD's
  out-of-scope already excludes an HTML animated variant; this closes
  the pure-SVG one too.
- **(b) Six moment cards, cut as the table above** over one card per
  skill kind (diagram family, factory, audit-shaped, drivers) — a
  kind-based cut answers "what is it" when the thirty-second test asks
  "which one do I reach for"; idea.md's own six moments are the cut
  (its "reshaping a codebase" retitled "Reshaping what's built" so a
  built surface fits beside built code), and each skill's description
  lands it in one. `lean` and `polish` both join
  "Reshaping what's built", so each arrives as one row in an existing
  card and one table row, not a re-layout — they are named here only,
  never in README.md before `skills/lean` and `skills/polish` exist.
- **(c) One figure in two layers — a loop plus cards — with the utility
  skills as text rows, not nodes** over a flat twenty-five-box picture
  (unreadable at 880 and the density that reads as generated output) and
  over the diagram skill's own prescription for an over-budget model, two
  figures (splits the read, doubles the roster surface; the PRD fixes one
  figure). The figure still exceeds the skill's node budget — twelve
  stage-side boxes plus six cards against a ceiling of nine — by the
  nature of a roster map; connectors land exactly on the ceiling (twelve)
  because the router carries no arrow. The overage is recorded at Verify
  as the fit between a system-figure skill and a map, not hidden.
- **(d) One SVG with the `prefers-color-scheme` block inside it,
  embedded as a plain markdown image** over a `<picture>` element with a
  light and a dark SVG — both mechanisms answer to the same browser
  preference, so the second file buys no control over GitHub's own theme
  setting and costs a second roster surface; the diagram skill's output
  is the single theme-aware file, which keeps the dogfooding claim whole;
  pipeline-board set the family precedent. The real github.com page
  decides at Verify, and the `<picture>` form is the recorded fallback
  with its cost named.
- **(e) `docs/assets/skill-map.svg`, referenced by relative path from
  README.md** over the repo root (already a tool bench), `.github/` (a
  host-specific directory for a harness-neutral artifact) or a run
  directory (run artifacts have a protocol shape; a figure is not one).
  `docs/assets/` is outside run discovery (`knowledge_plane.run_dirs`
  lists `docs/`, `docs/features/*` and `docs/fixes/*` only) and outside
  every gate walk (`gates._scannable_files` reads `*.md`), so the
  directory changes no orientation or detector outcome; README.md is not
  mirrored, so nothing in the payload moves.
- **(f) A sibling checker, `check_readme_figure`, reading visible SVG
  text** over extending `check_readme_skills` — that function's problem
  string names `README.md` and is pinned by its tests, and a checker that
  reads two files would report one with the other's name; a sibling
  reading the same roster through the same two functions is the shape
  `check_plugin_skills` already took for the plugin description. Visible
  `<text>` content over a raw-bytes `names_slug` (what the PRD's own
  evidence grep does) — the raw read passes a figure whose label says
  "Idea" and whose `id` says `idea`, which is the rotted figure the check
  exists to catch; the parse costs six lines and one worded failure mode.
  The README-embeds check joins it so lint can never pass on a stale file
  the README no longer shows. The self-containment grep stays Verify's,
  not lint's: the PRD defines the roster check and the grep separately,
  and a rule for a regression that has never happened is anticipated
  reuse.
- **(g) A three-column table (Skill, Moment, Why it matters), one row per
  `UTILITY_SKILLS` entry in card order** over a two-column table — the
  Moment column is what lets the table and the figure agree without a
  checker, and it is the column a reader scans. Slugs are the only
  backticked slug-shaped tokens in the section, by the orphan checker's
  contract; the row count is counted at Verify, not linted.
- **Slugs verbatim as node names** over display names ("UX Design",
  "/idea") — the roster check matches whole lowercase slugs, the README
  table uses bare slugs, and a leading slash is one harness's invocation
  syntax (ADR-0027).
- **The router inside the loop with no arrow** over the mermaid's dashed
  arrow into idea — one connector saved at the budget's ceiling, and the
  position says more than the arrow did.
- **Artifact filenames as stage sublabels** kept from the mermaid, subject
  to the diagram skill's remove test at Verify — "artifacts are the
  state" is the plugin's one idea, and the sublabels are where a reader
  sees it; if they cost legibility at 880 they go.
- **Why-lines in the table only** over a why-line per figure node — the
  brief's IN list puts the why in the table, and twenty-five labels is
  the figure's density floor already.
- **No ADR** — see below.

## ADRs

None — no decision met the ADR bar. The checker is reversible, sits in a
pattern two earlier checkers established without a record, and surprises
nobody who has read `check_readme_skills`; the figure and table are
packaging. The pull request carrying this run touches `architecture.md`,
so it is a human code-owner merge under ADR-0036 clause 3 — the brief's
plan already.

## Requirement trace (PRD-0008 success criteria)

- Thirty-second test — the figure (loop, router, cards with moment
  titles) and the table's Moment column; judged at Verify, anecdote.
- Roster check — `check_readme_figure` and its `TestReadmeFigure`
  pins; the table rides on `check_readme_skills` unchanged.
- Figure — the figure component's constraints; the embed seam's
  verification plan.
- Table and section — the README component.
- Provenance — decision (a), recorded here; hand-editing recorded at
  Verify.
- Room for lean and polish — the card table (joins-later column); the
  `extra_skills` half of the roster read.
- Battery and untouched surfaces — stdlib only; no edit under `skills/`,
  `evals/`, `LEDGER.md` or the plugin manifest; the README's other
  sections untouched.
