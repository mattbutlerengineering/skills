---
stage: decompose
run: feature:readme-skill-map
date: 2026-10-07
assumptions:
  - "The cut was not reviewed live (skill step 5): the autorun brief names no work items, so the milestone boundaries and sizes are this stage's reading of architecture.md — three milestones (the check pinned, the two surfaces drawn, the check live and the branch verified) and S/M/L by how much surface each row must get exactly right: the figure L (eighteen boxes, twelve connectors, two themes, the scaffold's hand-edits), the tests and the README table M, the checker, its registration and the close-out S."
  - "The checker function and its registration into lint.CHECKERS land in different rows (0092 and 0095) with the figure and the README between them, so python3 lint.py on the branch prints 0 problems at every row boundary — a registered checker with no figure on disk would print a missing-figure problem from row 0092 until row 0094. The tests land first (row 0091) against a fixture figure, red because the function does not exist yet, which is the architecture's own test plan."
  - "The PRD's self-containment check — grep -E 'http|<script|@import|@font-face' finding nothing — is read by intent: every SVG root carries an xmlns attribute naming http://www.w3.org/2000/svg (the diagram skill's own scaffold does, line 1), an XML namespace identifier no renderer fetches, so the figure row allows that one line and nothing else. Verify applies the same reading when it runs the PRD's check; neither the PRD nor the architecture is rewritten."
  - "The hand-edits the figure needs beyond the scaffold (the root width and height, the text tiers raised to 10px, anything else met in drawing) are logged under Notes in this file, dated, by the figure row, so Verify's Provenance record copies them from one place. The PRD puts that record in verification.md and the architecture names the first two; neither says where Implement leaves them."
  - "Implement's check-offs follow this repo's owner-session ledger policy (docs/features/process-dashboard/breakdown.md, 2026-08-13 note; docs/features/pocock-1-3-takeaways/breakdown.md Notes, 2026-10-06; ADR-0069 Context): detector G reads a checked row as a merged work order owed a docs/factory/costs.jsonl line, and this run's rows are worked interactively with no dispatched agent, so each check-off appends one honest zero-cost row via budget_guard record. The brief and the architecture are silent on the ledger."
---

# Breakdown: README skill map

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met. Rows follow the house grammar: a
repo-global work-order id (continuing from 0090), size class, blocking
edges, and the PRD citation. No tracker mirror for this run (the brief
rules out any tracker interaction; the checkboxes are the state,
ADR-0026). Reconciled against `architecture.md` on 2026-10-07: every
component it names lands in a row below, and every PRD-0008 success
criterion is covered by at least one Accept paragraph; the Coverage
section at the end says which. The checker's tests are written before the
checker, and the checker is registered only after the figure and the
README embed exist, so every commit on the branch stays lint-green.

## Milestone 1: The roster check exists and is pinned

- [x] **WO-0091** Pin check_readme_figure with tests, red — size:M, blocked by: — (PRD-0008 §Success criteria)
  - Accept: `tests/test_lint.py` gains, in `make_clean_tree`, a figure at `docs/assets/skill-map.svg` under the fixture root — a minimal SVG whose root carries the SVG `xmlns` and whose body holds one `<text>` element per `ALL_SKILLS` slug, one element per line so a test can drop one by string replacement as the README fixture's one-slug-per-line form already allows — and one markdown image line referencing `docs/assets/skill-map.svg` in the fixture README above its `## Stages` heading; and a new `TestReadmeFigure(CheckerTreeTest)` that, through the public `lint.check_readme_figure(root)` alone, asserts the exact strings `architecture.md` fixes: the clean fixture yields `[]`; the figure with its `ship` element removed yields `["docs/assets/skill-map.svg never names skill 'ship'"]`; a figure whose only `ship` sits in an `id` attribute, an XML comment and a `<style>` rule yields that same one string (the visible-text rule); the figure with its `architect` element removed yields `["docs/assets/skill-map.svg never names skill 'architect'"]` while `architecture-diagram` and `interactive-architecture-diagram` stay present (whole-slug matching); a slug split across a `<tspan>` inside one `<text>` element is not reported missing (tspans are included); a `skills/rogue` directory with a `SKILL.md` beside the taxonomy yields `["docs/assets/skill-map.svg never names skill 'rogue'"]`; the figure with `ship` and `audit` removed and the fixture README's image line removed yields exactly three strings in this order — `ship`, `audit`, then `README.md never embeds 'docs/assets/skill-map.svg'` (roster order, embed last); the figure deleted yields exactly `["missing docs/assets/skill-map.svg"]` with no roster fan-out; a figure whose bytes are not UTF-8 yields one string starting `cannot read docs/assets/skill-map.svg:`; a figure that is not well-formed XML yields one string starting `docs/assets/skill-map.svg is not valid SVG:`; and the fixture README deleted yields `[]` from this checker (`check_readme_skills` owns that absence). Observed red: against the tree before the function exists, every `TestReadmeFigure` test errors with `AttributeError` and every other test in the suite passes — `TestCleanTree` and `TestReadmeNoOrphans` included, because the image line carries no backtick token and sits outside the section (write `python3 -m unittest discover tests` output to a file and grep it for `AttributeError` and `FAILED`). `lint.py` is not touched in this row.
- [x] **WO-0092** Add check_readme_figure to lint.py, unregistered — size:S, blocked by: WO-0091 (PRD-0008 §Success criteria)
  - Accept: `lint.py` gains the module constant `README_FIGURE = "docs/assets/skill-map.svg"` beside `STAGES_HEADING` and the checker `check_readme_figure(root)` directly after `check_readme_no_orphans`, which reads `root / README_FIGURE` through `cli.read_file(path, README_FIGURE, str)` (ADR-0075), returning `[f"missing {README_FIGURE}"]` on `(None, None)` and the read problem alone on a read failure; parses the text with `xml.etree.ElementTree`, returning `[f"{README_FIGURE} is not valid SVG: {err}"]` alone on `ParseError`; joins the text content of every element whose local name is `text` (the SVG namespace stripped, `<tspan>` children included, elements separated by whitespace so no two fuse into one token); reports `f"{README_FIGURE} never names skill {slug!r}"` for each slug in `ALL_SKILLS + extra_skills(root)` that `names_slug` does not find in that text, in that order; then `f"README.md never embeds {README_FIGURE!r}"` when `README.md` exists and its text does not contain the constant, and nothing for a missing README.md. It keeps no slug list of its own (check: read the function — its only literals are the constant and the four problem wordings) and never raises for a local-file failure. `CHECKERS` is not touched in this row: `python3 lint.py` on the real tree still prints `lint: 0 problem(s)` though no figure exists on disk yet; `python3 -m unittest tests.test_lint` prints `OK` with every `TestReadmeFigure` test green and no test edited (`git diff --stat main -- tests/` shows only row 0091's additions).

## Milestone 2: The figure is drawn and the README shows it

- [x] **WO-0093** Draw docs/assets/skill-map.svg with the architecture-diagram skill — size:L, blocked by: WO-0092 (PRD-0008 §Success criteria)
  - Accept: `docs/assets/skill-map.svg` exists, made by working `skills/architecture-diagram/SKILL.md`'s seven steps in order from a copy of its `assets/boilerplate.svg` with the model `architecture.md` fixes under The figure and The six moment cards: stage-side nodes `idea`, `prd`, `ux-design`, `architect`, `decompose`, `implement`, `verify`, `review`, `ship`, `operate` (solid, mono sublabel the stage artifact the mermaid shows today), `next` (the one accented focal node, inside the loop, sublabel naming it the router) and `capture` (solid, outside the loop, sublabel `defect.md`); six cards titled verbatim "Before a run exists", "Reshaping what's built", "Driving a run", "Around a pull request", "Drawing pictures", "Installing the factory", each holding as mono rows exactly the members the card table lists today (thirteen rows in all; neither `lean` nor `polish`), placed as the table's Sits-by column says where the grid allows; exactly twelve connectors — ten solid closing the loop idea→prd→ux-design→architect→decompose→implement→verify→review→ship→operate→idea with the closing edge labelled as the retro seeding the idea, one dashed prd→architect labelled for the no-UI case, one dashed capture→architect or capture→implement (whichever routes straight), and none into or out of `next`. Every slug is literal `<text>` content, bare and lowercase (no leading slash, no display casing); the title, subtitle, eyebrow, edge labels and legend contain no whole-slug match for any roster slug (check: read those elements); no count of anything appears in the figure; the root `viewBox` is 880 wide and the root carries `width` and `height` attributes equal to its size; no text class is below 10px (`grep -E 'font-size: *[0-9]px' docs/assets/skill-map.svg` prints nothing); `grep -c 'prefers-color-scheme: dark' docs/assets/skill-map.svg` prints `1` and the body paints only tokens (`awk '/<\/style>/{p=1;next} p' docs/assets/skill-map.svg | grep -E '#[0-9a-fA-F]{3,6}\b'` prints nothing); `grep -E 'http|<script|@import|@font-face' docs/assets/skill-map.svg` prints the root's `xmlns` line and nothing else; `python3 -c "import lint, pathlib; print(lint.check_readme_figure(pathlib.Path('.')))"` prints exactly `["README.md never embeds 'docs/assets/skill-map.svg'"]` (every roster slug found; the embed is the next row's); `git diff --stat main -- skills/` is empty (the asset is copied, never edited); and a dated Notes entry below lists every hand-edit the scaffold needed (the root size attributes and the raised text tiers at least), the node and connector counts against the skill's budget, and which of step 7's checks (both themes standalone, both themes embedded as an image, the remove test) ran, each with its outcome — a check that did not run is written as not run, never as passed.
- [x] **WO-0094** README: the embed and the utility table — size:M, blocked by: WO-0093 (PRD-0008 §Success criteria)
  - Accept: in `README.md` the mermaid fence at the top and everything inside it are gone (``grep -c '^```mermaid' README.md`` prints `0`) and in their place stands one markdown image line referencing `docs/assets/skill-map.svg` whose alt text says in one sentence what the figure shows; the `## Stages` heading and the stage table under it are byte-identical to main (`diff <(git show main:README.md | sed -n '/^## Stages/,/^## Development/p' | grep '^|') <(sed -n '/^## Stages/,/^## Development/p' README.md | grep '^|' | head -14)` prints nothing); the utility-skill prose paragraph below the stage table is replaced by a short lead-in that keeps the existing ADR-0023 link (relative path `docs/adr/0023-utility-skills.md`, as main has it) and points up at the figure, then a table with the header `| Skill | Moment | Why it matters |` and exactly one body row per `protocol.UTILITY_SKILLS` entry, rows grouped in card order — Before a run exists: `audit`, `automate`; Reshaping what's built: `deepen`; Driving a run: `autorun`, `work-queue`; Around a pull request: `address-pr-review`; Drawing pictures: `mermaid`, `architecture-diagram`, `animated-diagram`, `interactive-architecture-diagram`, `pipeline-board`; Installing the factory: `factory-init`, `doctor` — the Skill cell the bare slug in backticks, the Moment cell the card title verbatim as plain text, the Why cell one line distilled from that skill's `description:`; the closing sentence linking `docs/pipeline-protocol.md` stays. Neither `lean` nor `polish` appears anywhere in README.md (`grep -c -E '\blean\b|\bpolish\b' README.md` prints `0`); inside `## Stages` every slug-shaped backtick token is a registered skill (`python3 -c "import lint, pathlib; print(lint.readme_stage_mentions(pathlib.Path('README.md').read_text()) - set(lint.ALL_SKILLS))"` prints `set()`) and the utility table has thirteen body rows, one per `UTILITY_SKILLS` slug with none repeated (count the `| `-prefixed lines after the second table header whose first cell is a backticked slug; the set equals `set(protocol.UTILITY_SKILLS)`); `python3 lint.py` prints `lint: 0 problem(s)` (`check_readme_skills` and `check_readme_no_orphans` both pass, unchanged) and `python3 -c "import lint, pathlib; print(lint.check_readme_figure(pathlib.Path('.')))"` prints `[]`; Install, Usage, Development and License are byte-identical to main (`diff <(git show main:README.md | sed -n '/^## Install/,/^## Stages/p') <(sed -n '/^## Install/,/^## Stages/p' README.md)` and the same pair with `/^## Development/,$p` both print nothing); `.claude-plugin/plugin.json` is untouched.

## Milestone 3: The check is live and the branch is verified

- [x] **WO-0095** Register check_readme_figure in CHECKERS and prove it bites — size:S, blocked by: WO-0094 (PRD-0008 §Success criteria)
  - Accept: `lint.CHECKERS` lists `check_readme_figure` directly after `check_readme_no_orphans` and before `check_protocol` (`python3 -c "import lint; print([c.__name__ for c in lint.CHECKERS])"` shows the order); `python3 lint.py` prints `lint: 0 problem(s)`; `python3 -m unittest tests.test_lint` prints `OK` with `TestCleanTree` now exercising the checker on the fixture figure and no test edited; and the PRD's Room-for-lean-and-polish check passes in a scratch copy of the tree made outside the repo (`cp -R` to a temporary directory, never the checkout): `mkdir skills/lean` there, then `python3 lint.py` prints `LINT: docs/assets/skill-map.svg never names skill 'lean'` beside the existing `LINT: README.md never names skill 'lean'` among its problems; the scratch copy is deleted afterwards and `git status` in the checkout is clean.
- [ ] **WO-0096** Full battery and untouched surfaces — size:S, blocked by: WO-0091, WO-0092, WO-0093, WO-0094, WO-0095 (PRD-0008 §Success criteria)
  - Accept: on the branch tip, `python3 -m unittest discover tests` prints `OK`, `python3 lint.py` prints `lint: 0 problem(s)`, and `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)` and `selftest: ok` (each output written to a file and grepped, per the brief's zsh note); `git diff --stat main -- skills/ .claude-plugin/plugin.json evals/ LEDGER.md` prints nothing; `git diff --stat main` lists only `README.md`, `docs/assets/skill-map.svg`, `lint.py`, `tests/test_lint.py`, this run's artifacts under `docs/features/readme-skill-map/` and `docs/factory/costs.jsonl` (the ledger rows the Notes policy owes), nothing else; the README's Install, Usage, Development and License sections are byte-identical to main (row 0094's two `diff` commands print nothing); and every row above is checked.

## Coverage

Architecture components to rows, by milestone: `lint.check_readme_figure`
(the constant, the checker, its contract and its tests) is Milestone 1
(rows 0091 and 0092) and goes live in Milestone 3 (row 0095); the figure
and the six moment cards are row 0093; README.md's embed and the `## Stages`
table, with the Moment column carrying the six card titles, are row 0094;
the README-embed-to-GitHub-render seam has no row — its verification plan
(the real github.com page, one screenshot per appearance setting) is
Verify's. Every file in the architecture's tree-claims block is read or
edited by a row: `README.md` (0094), `lint.py` (0092, 0095),
`tests/test_lint.py` (0091), `protocol.py` and `cli.py` (read by 0092),
the diagram skill's `SKILL.md`, `assets/boilerplate.svg` and
`references/design-system.md` (read by 0093), `prd.md` (cited by every
row).

PRD-0008 Success criteria to Accept paragraphs:

- Thirty-second test — rows 0093 (the loop, the router inside it, the six
  titled cards) and 0094 (the table's Moment column) build what the
  stand-in reader is shown; the test itself is Verify's and enters the
  record as anecdote — no implement-side row can pass it.
- Roster check — row 0091 (the exact strings, red before the function
  exists), row 0092 (one roster through `ALL_SKILLS + extra_skills` and
  `names_slug`, no literal slug list, stdlib only), row 0095 (live in
  `CHECKERS`); the table rides on `check_readme_skills` unchanged (row
  0094's lint run).
- Figure — row 0093 (mermaid's content reproduced, self-contained, literal
  `<text>` slugs, intrinsic size, both themes) and row 0094 (the mermaid
  block gone, the image embed in its place); the two github.com
  screenshots are Verify's.
- Table and section — row 0094.
- Provenance — row 0093 (drawn by the skill's seven steps from its
  scaffold, hand-edits logged under Notes); `architecture.md` already
  records which skill and why (decision (a)); Verify copies the Notes
  entry into `verification.md`.
- Room for lean and polish — rows 0093 and 0094 (neither name appears) and
  row 0095 (the scratch `mkdir skills/lean` check shows the figure problem
  firing beside the README one).
- Battery and untouched surfaces — row 0096, with the per-row lint runs
  along the way.

## Design gaps found

None. The one wording defect met in decomposition — the PRD's
self-containment grep matches every SVG root's `xmlns` attribute — is a
check that cannot be run literally, not a missing contract; it is read by
intent in row 0093 and logged under `assumptions:`, and Verify applies the
same reading.

## Notes

- 2026-10-07: the merge is gate 3 (ADR-0033, the PR merge: required
  status checks plus code-owner review). The pull request carries this
  run's `prd.md` and `architecture.md`, so ADR-0036 clause 3 makes it a
  human code-owner merge — the brief's plan: Ship opens the one tracking
  issue, opens the pull request, and stops; the owner judges the rendered
  figure on github.com and merges.
- 2026-10-07: owner-session ledger policy — detector G reads a checked
  row as a merged work order owed a `docs/factory/costs.jsonl` line, and
  this run's rows are worked interactively with no dispatched agent, so
  each check-off appends one honest zero-cost row via `budget_guard
  record` (`run_id` of the form `session-YYYY-MM-DD-wo-NNNN`, the
  session's model, `tokens: 0`, `cost: 0.0`, `outcome:
  owner-session:unmetered`), as the last twelve ledger rows do. The rows'
  Accept text assumes `gates: 0 problem(s)` follows from the edits; the
  ledger row is what makes it so.
- 2026-10-07: `lint.py`'s comment block above `STAGES_HEADING` and the
  docstrings of `readme_stage_mentions`, `check_readme_no_orphans` and
  `TestReadmeNoOrphans` describe the utility-skill mentions as a prose
  paragraph introducing skills one by one; after row 0094 the section
  holds a short lead-in and a table. The checkers' behaviour and the
  section scope are unchanged, so no row rewords them; flagged for Review
  as stale rationale, not a defect.
- 2026-10-07: the lean-and-polish worktree's uncommitted README edit
  touches the same prose block row 0094 replaces. Whichever branch lands
  second rebases; from then on the roster check demands `lean` and
  `polish` as one row each in the "Reshaping what's built" card and one
  table row each (architecture card table, Joins-once column) — a node
  in an existing card and a table row, not a re-layout.
- 2026-10-07: if Verify's github.com check finds the dark flip does not
  happen inside the image embed, the recorded fallback (architecture.md
  decision (d): a forced-dark copy, a `<picture>` element, `README_FIGURE`
  widened to both files) is new work and gets its own row then, not now.
- 2026-10-07: the figure exceeds the diagram skill's node budget (twelve
  stage-side boxes plus six cards against a ceiling of nine) by the
  architecture's decision (c); row 0093's Notes entry records the counts
  so Verify reports the overage as the fit between a system-figure skill
  and a roster map, not as a surprise.
- 2026-10-07 (row 0093, the figure's provenance record): drawn by
  working `skills/architecture-diagram/SKILL.md`'s seven steps in order
  from a `cp` of its `assets/boilerplate.svg`; the asset is unchanged
  (`git diff --stat main -- skills/` is empty). Hand-edits the scaffold
  needed beyond replacing the sample content and the title/desc text,
  each a departure the skill's own text does not sanction:
  (1) root `width="880" height="688"` beside the `viewBox` — the
  scaffold carries only a `viewBox`, and an SVG with no intrinsic size
  is fitted to 300×150 inside `<img>`; (2) the `.eyebrow` tier raised
  8→10px, `.elabel` 9→10px and `.legend-t` 9→10px, so no text in the
  figure is below 10px at README width; (3) one added class, `.row`
  (mono via the existing `.mono`, 11px, `--ink`), for a card's member
  slugs — the design system has no list-row tier, and its 10px muted
  sublabel is too faint for the one thing a reader came to find;
  (4) the edge-label mask is 14px tall (the scaffold's is 12) to clear
  the raised label; (5) the six "moment cards" are a composition the
  design system does not define — its `node-ext` treatment with a
  left-aligned `.name` title and `.row` members — used as node-like
  containers per `architecture.md` decision (c). Counts against the
  skill's budget: 18 nodes (12 stage-side boxes plus 6 cards) against a
  ceiling of 9 — the overage decision (c) records; 12 connectors against
  12; 0 zones against 3; 1 accent element against 2. Step 7's checks,
  each with its outcome: both themes standalone — ran, headless Chrome
  (`--blink-settings=preferredColorScheme=1` for light, `=0` for dark;
  `rsvg-convert` is not installed) at 2× device scale, both PNGs
  inspected: every element flips, no stranded light colour, the
  label mask included — pass; both themes embedded as an image — ran,
  a scratch HTML page with `<img src>` in an 830px column (GitHub's
  README width) under both schemes: renders identically at intrinsic
  size scaled to the column, the dark paper matching GitHub's
  `#0d1117` — pass; the remove test — ran, nothing removed: the stage
  sublabels carry "artifacts are the state", `the router` names the
  focal node, `no ui surface`, `retro seeds` and `re-entry` each
  explain the one edge whose meaning its style does not, and the five
  legend rows are exactly the treatments and line kinds drawn. Not
  run: the real github.com page in either appearance setting (Verify's
  check, by the architecture's verification plan). Three drawing
  iterations: v1 placed "Installing the factory" in a 256-wide card
  with a blank right half and top-aligned the cards to the 56-tall
  nodes; v2 made that card 176 wide under the review–verify columns
  (bottom-band gaps 120/128) and centred every card on its row's
  centre line; v3 reworded the subtitle and `<desc>`, which had said
  "Ten" and "Six", to carry no count.
- 2026-10-07 (row 0095, the check bites): in a `cp -R` of the tree
  under the session scratchpad, never the checkout, `mkdir skills/lean`
  with a minimal `SKILL.md`, then `python3 lint.py` printed, in this
  order: `LINT: skills/lean is not in the skill taxonomy (protocol.py
  ALL_SKILLS)`, `LINT: README.md never names skill 'lean'`, `LINT:
  docs/assets/skill-map.svg never names skill 'lean'`, `LINT: LEDGER.md
  has no row for skill 'lean'`, `lint: 4 problem(s) across 26 skills`.
  In a second fresh copy, the one `<text>` element holding
  `address-pr-review` deleted from the figure, `python3 lint.py`
  printed `LINT: docs/assets/skill-map.svg never names skill
  'address-pr-review'` and `lint: 1 problem(s) across 25 skills`, exit
  1. Both copies deleted afterwards; `git status` in the checkout shows
  only this row's `lint.py` edit. The registration is pinned the way
  every checker's is — `TestCleanTree` walks `lint.CHECKERS` against
  the fixture figure — with no test edited (`git diff --stat main --
  tests/` is row 0091's addition alone).
