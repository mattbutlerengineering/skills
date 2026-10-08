---
stage: review
run: feature:readme-skill-map
date: 2026-10-07
assumptions:
  - "No live severity arbitration: the skill's draft-then-arbitrate loop (steps 4 to 6) ran without the user, so the severities below are this stage's ranking on the scale the pocock-1-3-takeaways review used (critical means wrong behaviour, a lie in an artifact, or a broken contract). The fix-before-ship rule came from the autorun orchestrator — fix a critical or a major here, fix a minor or a nit only when the fix is one line and clearly safe, otherwise defer with a reason — so the fixes below were made on the branch rather than routed to Implement."
  - "docs/standards.json was read (four MUST statements). stdlib-only applies to the lint.py change and holds (xml.etree.ElementTree is standard library); adr0004 and adr0032 are untouched (no typed id moved, no tracker issue exists); eval-honesty is untouched (no eval evidence in the diff). No finding cites a statement."
  - "The screenshot finding was ranked major, not critical, because nothing in it is wrong or untrue — the cost is permanent repository weight for every plugin install after a squash merge — and it was fixed by cropping rather than by dropping the files, because PRD-0008's Figure criterion names screenshots in verification.md and rewriting a PRD criterion is not this stage's call."
  - "The stale-rationale finding was fixed here although it spans three passages rather than one line: the orchestrator asked this stage to decide, and a docstring that now misdescribes the structure of the file its checker reads is this change's own orphan under CLAUDE.md's surgical-change rule. Comments and docstrings only; no code, no test string."
  - "Two mutations were applied to git-archive copies of the branch tip under the session scratchpad, never the worktree; the mutated line was grepped before each run and both copies were deleted afterwards. one_owner.py was run on main through a temporary detached worktree under the scratchpad, removed afterwards; no git stash was used."
---

# Review: README skill map

## Scope

The whole branch against `main` (`e64e7de`): the eleven run commits
`708fc16..07ff88a` plus the three review fixes below, 13 files,
+2072/−82 before the fixes. Deliverables examined line by line:
`lint.py` (`README_FIGURE`, `check_readme_figure`, the `CHECKERS`
registration, the `xml.etree.ElementTree` import), `tests/test_lint.py`
(`make_clean_tree`'s figure and embed-line fixtures, `TestReadmeFigure`'s
eleven tests), `README.md` (the embed line and alt text, the `## Stages`
lead-in, the thirteen-row utility table against each skill's
`description:`), `docs/assets/skill-map.svg` (every element, the token
block, the accessibility attributes, the old mermaid from `git show
main:README.md` beside it), the two github.com screenshots (read as
images), the six ledger rows, and the run artifacts (`idea.md`,
`autorun-brief.md`, `prd.md`, `architecture.md`, `breakdown.md`,
`verification.md`) for process honesty.

Checks run from the worktree, outputs in the session scratchpad:

```
$ python3 -m unittest discover tests     -> Ran 1944 tests ... OK
$ python3 lint.py                        -> lint: 0 problem(s) across 25 skills
$ python3 gates.py && python3 gates.py --selftest
                                         -> gates: 0 problem(s) / selftest: ok
$ python3 one_owner.py                   -> 6 problem(s), byte-identical to main's
                                            (none in a file this diff touches)

# mutation 1, scratch copy: names_slug(visible, slug) -> slug in visible
  grep confirms line 700 mutated; TestReadmeFigure: FAILED (failures=1)
  test_a_slug_nested_in_a_longer_one_is_still_required
# mutation 2, scratch copy: tag.rpartition("}")[2] == "text" -> tag == "text"
  grep confirms line 697 mutated; TestReadmeFigure: FAILED (failures=8)
  (the namespaced fixture then has no <text> at all; clean-fixture, drop,
  tspan, rogue-dir and ordering tests all go red)

$ grep -inE '<script|<foreignObject|href|javascript:|on[a-z]+=|url\(|@import|<!ENTITY|<!DOCTYPE' docs/assets/skill-map.svg
  twelve hits, every one marker-end="url(#arrow)" — an internal reference
$ token coverage (python, stdlib): 14 tokens in :root, 14 in the dark
  block, 0 defined on one side only, 0 var() uses of an undefined token,
  0 literal colours and 0 fill=/stroke= attributes below </style>
$ xml.etree.ElementTree on scratch strings: an external SYSTEM entity
  raises ParseError "undefined entity" (expat does not resolve it); an
  internal entity expands; an XML declaration in a str parses; tail text
  after a <tspan> is joined by itertext
```

Verify's quoted outputs were re-read against the branch; the battery
lines, the roster-check one-liners and the `mkdir skills/lean` proof
match what `verification.md` records.

## Findings

### Major: the two github.com screenshots were full-page 2× captures, 1.88 MB together — the first binaries this repository tracks

- Scenario: `docs/features/readme-skill-map/github-light.png` (934 KB)
  and `github-dark.png` (942 KB), 2400 × 4400 each, took the tracked
  tree from 7.24 MB to 9.24 MB; `git ls-tree -r main` has no image at
  all. The project's merge is a squash (ADR-0033 gate 3), after which
  the blobs sit in `main`'s history for good, and `/plugin marketplace
  add mattbutlerengineering/skills` clones that history for every
  adopter — 1.9 MB per install for two pieces of Verify evidence. The
  evidence does not need the page: a pixel-exact crop to the README
  content column (columns 660–2399, rows 0–2249, so 1740 × 2250) keeps
  every claim `verification.md` makes — the signed-out header, the
  branch commit `14d04c5` in the commit bar, the Preview toolbar, the
  whole figure — at 358 KB each; a crop to the figure alone would be
  196 KB but would no longer show that the page is github.com, which is
  the point of the PRD's "not a local preview".
- Standard: none
- Decision: fixed — both files replaced by the content-column crops
  (`sips --cropOffset 0 660 -c 2250 1740` on copies of the captures),
  verified pixel-exact against the originals over 2,004 sampled
  coordinates including the four `verification.md` quotes (`#f6f5f1`,
  `#f3e9e1`, `#0d1117`, `#231e1e` reappear at x−660). One dated bullet
  under the Figure evidence in `verification.md:309-320` records the
  crop and the offset so the quoted coordinates stay followable. The
  uncropped blobs remain reachable in the branch's own history (commit
  `07ff88a`) until the branch is deleted after the squash merge; `main`
  never carries them — provided the merge is the squash the project
  uses, not a merge commit or a rebase.
- Fixed in a67fdd2.

### Minor: `lint.py`'s Stages-section rationale described a prose paragraph the README no longer has

- Scenario: the comment above `STAGES_HEADING` (`lint.py:570-577`), the
  `readme_stage_mentions` docstring (`lint.py:605-608`) and the
  `check_readme_no_orphans` docstring (`lint.py:639-643`) said utility
  skills "have no table row of their own" and are introduced "one by
  one" in "the paragraph right below" the stage table. Since row 0094
  the section is the stage table, a two-sentence lead-in and a
  thirteen-row utility table. A maintainer deciding whether a new
  backtick token is safe inside `## Stages` would be reasoning from a
  structure that is gone. Behaviour and scope are unchanged — both
  tables' first cells are slugs, the lead-in backticks nothing, and the
  orphan scan reads tokens, not structure — so no test or problem string
  moved. The breakdown's Notes flagged this for Review as stale
  rationale, not a defect; that reading is right.
  `tests/test_lint.py:786-788` describes the historical #502 scenario
  ("has no table row") and its fixture appends a prose sentence, which
  is still a valid case; left as history.
- Standard: none
- Decision: fixed — the three passages reworded to the two-table shape
  with the paragraph recorded as the pre-0094 history; comments and
  docstrings only. `lint.py` is not in `factory_init.MIRRORS`, so no
  manifest moved.
- Fixed in 1fdc9f9.

### Minor: three artifact sublabels satisfy the roster line for their own stage, so the figure can lose the `idea`, `prd` or `review` name without lint noticing

- Scenario: `check_readme_figure` joins every `<text>` element and asks
  `names_slug` (`lint.py:695-700`); a dot is a slug boundary, so the
  sublabels at `docs/assets/skill-map.svg:124` (`idea.md`), `:130`
  (`prd.md`) and `:166` (`review.md`) each match their stage's slug on
  their own. A redraw that drops the `idea` name label — or
  display-cases it to "Idea" — while keeping its filename sublabel
  leaves `python3 lint.py` green with a box whose only lowercase slug is
  a filename. The other twenty-two slugs have no stand-in
  (`architecture.md` does not name `architect`, `verification.md` does
  not name `verify`, and so on; Verify checked all twenty-nine non-slug
  elements). Verify raised this as an observation; the breakdown's row
  0093 forbids whole-slug matches in the title, subtitle, eyebrow, edge
  labels and legend only, and those five hold.
- Standard: none
- Decision: deferred — the failure needs a redraw that loses exactly one
  of three names while keeping its filename, and a redraw that
  display-cases the names loses all twenty-five, which twenty-two lines
  of lint output would catch. The stricter rule (a slug must be the
  whole content of one `<text>`, which is Verify's own one-liner) is a
  design change against `architecture.md`'s stated "names" contract and
  would reject a legitimate one-element label such as a name with its
  role beside it; excluding sublabels by class would couple lint to the
  figure's CSS. A backlog seed if the figure is ever redrawn with
  display names: drop the `.md` sublabels from the join, or require the
  whole-content match.

### Minor: the README-embed half of the checker is a substring test, so a commented-out or quoted mention of the path passes it

- Scenario: `lint.py:702` tests `README_FIGURE not in readme`. A README
  whose embed line is wrapped in `<!-- -->` during a redesign, or that
  mentions `docs/assets/skill-map.svg` in a code fence while the image
  line is gone, keeps lint green although the page shows no figure —
  the case the embed check exists for ("lint can never pass on a stale
  file the README no longer shows", `architecture.md` decision (f)).
- Standard: none
- Decision: deferred — the substring is the contract `architecture.md`'s
  Interfaces section wrote ("its text does not contain the constant"),
  chosen so the check stays agnostic between the markdown-image form and
  the `<picture>` fallback; an HTML comment defeats a markdown-image or
  `src=` regex just the same, so the stricter form buys little; and the
  README is the one file the owner reads at the merge gate. Record, not
  rework.

### Nits

- `README.md:87` wrote "colours" — the one British spelling in a README
  that wrote "color" six times on `main` and distils a `description:`
  that says "colors". Fixed in 203dcdd.
- `README.md:76-77`: the lead-in said the moments "head the table"; they
  fill its second column, not its header. Reworded to "fill the table's
  Moment column". Fixed in 203dcdd. The lead-in otherwise still reads
  correctly: it keeps the ADR-0023 link and points up at the figure.
- `tests/test_lint.py:941`:
  `TestReadmeFigure.test_bytes_that_are_not_utf8_are_a_problem_not_a_crash`
  shadows the base-class test of the same name (`:193`, the plugin.json
  case), so that case does not run in this class. `TestPiPackage:315`
  and `TestOutputEvals:1443` set the precedent and the base case runs in
  the other eighteen subclasses; the eleven-test count Verify quotes is
  the shadowed count. No decision owed.
- `docs/assets/skill-map.svg:22-27, 64, 73-76`: the scaffold's unused
  treatments (`.zone`, `.node-store`, `.node-queue` and their four
  tokens) ship in the `<style>` block. The scaffold's own comment says
  the tokens mirror the design system and change together; harmless,
  and consistent with the dogfooding claim. Not a finding.

### Repository hygiene, not findings

- `docs/features/readme-skill-map/autorun-brief.md` is committed though
  the brief says it "is not an artifact": five earlier runs on `main`
  commit theirs (`git ls-files docs/features/*/autorun-brief.md`), so
  this is the convention, not drift. The protocol's orientation reads
  only the artifact table, so the file changes no stage outcome.
- The six ledger rows carry `"at": "2026-10-08"` beside
  `session-2026-10-07` run ids. `budget_guard.record` stamps `at` with
  `datetime.now(timezone.utc)` (`budget_guard.py:255`), and the six
  check-offs ran after 00:00 UTC; the run id carries the session's local
  date by the policy's own form. Detector G reads `wo`, never `at`, and
  the earlier owner-session rows agree only because those sessions
  closed before midnight UTC. Honest machine output.
- `python3 one_owner.py` reports six problems on this tree, byte-identical
  to `main`'s six, every one in files this diff does not touch
  (`assembler.py`/`validator.py`/`work_queue.py`,
  `budget_guard.py`/`cost_report.py`,
  `dashboard.py`/`gate_digest.py`/`rejection_mining.py`,
  `eval_schema.py`/`trigger_eval.py`,
  `gate_digest.py`/`rejection_mining.py`, `label_sync.py`/`sweeps.py`).
  A pre-pass, not a gate.

## Passes with no findings

- **Correctness of the checker.** Every arm returns a list: `read_file`'s
  own wording for an `OSError` or non-UTF-8 bytes, `missing …` for
  absence, `… is not valid SVG: <err>` for `ParseError`, then roster
  problems in `ALL_SKILLS` order followed by sorted extras, then the
  embed problem; a missing or unreadable README is left to
  `check_readme_skills`, as `check_readme_no_orphans` leaves it. The
  namespace strip (`tag.rpartition("}")[2]`) works with and without an
  `xmlns` on the root, and the default `TreeBuilder` drops comments, so
  `tag` is always a string. `itertext()` yields the element's text, its
  descendants' text and their tails, so a slug split across `<tspan>`s
  — or around one — is one label, which is how the test at
  `tests/test_lint.py:902` pins it; the real figure splits nothing, and
  the fixture (one bare `<text>` per slug, `xmlns` on the root) is the
  real figure's shape minus classes and positions. Two unrelated tspans
  with no whitespace between them would fuse and be reported missing —
  the loud direction. Registration sits directly after
  `check_readme_no_orphans` and before `check_protocol`
  (`lint.py:959-964`), and `TestCleanTree` walks `lint.CHECKERS`
  (`tests/test_lint.py:209`), so the fixture figure is exercised by
  registration, not by a hand-written call. Both mutations above went
  red on the tests that exist, with the mutation proven applied first.
- **Design.** A sibling checker in the pattern `check_plugin_skills` set:
  the same two roster functions, no slug literal (Verify's AST walk), a
  path constant beside `STAGES_HEADING`, problem strings in
  `read_file`'s grammar; `architecture.md`'s contract is implemented
  as written, decision by decision — one figure, six cards, slugs
  verbatim, router without an arrow, the `<picture>` fallback not
  needed because the dark flip happened inside the plain `<img>`.
  `docs/assets/` is outside run discovery and every gate walk, as the
  architecture said. Stdlib only.
- **Security.** The SVG carries no `<script>`, `<foreignObject>`,
  `href`, event attribute, `<image>`, `<use>`, `@import`, DOCTYPE or
  entity; the only `url()` is the internal `#arrow` marker and the only
  `http` is the `xmlns` identifier, which no renderer fetches. The
  checker parses a repo-controlled file with the stdlib expat parser,
  which does not resolve external entities (a `SYSTEM` entity is a
  `ParseError`, shown above) and does not fetch DTDs; the
  entity-expansion bombs the Python docs list are bounded by expat
  2.4.1+ and would only ever be the repository's own committed file.
  Nothing writes, nothing reaches the network, no secret is in the diff;
  the ledger rows carry no tokens or identities beyond the model name.
- **README table accuracy.** All thirteen "why" cells trace to the
  skill's own `description:`; none invents a capability. Two are
  abbreviations worth knowing: `automate` lists four of its six
  categories (plugins and drift detectors dropped), and
  `factory-init`'s parenthetical ("offline gates, dispatch workflows,
  the cost ledger") is `main`'s own prose, not the description's
  wording. `audit`'s "every finding reproduced before it is reported"
  compresses "a finding counts only once reproduced; everything else is
  reported as a suspicion". The alt text names what the figure shows
  and nothing it does not. Row count, slug set, orphan scan and both
  README checkers were re-run and match Verify.
- **The figure against the mermaid.** Every element the mermaid had is
  present: the router, the ten ordered stages with their artifact
  sublabels (`code + tests` for implement), the `no UI surface` skip
  from prd to architect, the `retro seeds` closing edge from operate to
  idea; added, `capture` with its `re-entry` edge, which `ALL_SKILLS`
  registers and the mermaid omitted. The mermaid's dashed styling of
  the ux node is carried by the dashed skip edge alone — the
  architecture's "solid treatment" for every stage node. Both
  screenshots show every label unclipped and every card title and slug
  legible; the `NO UI SURFACE`, `RETRO SEEDS` and `RE-ENTRY` labels sit
  clear of their lines; the dark capture leaves no light-coloured
  element and the figure's paper equals GitHub's page background, so
  the figure has no visible edge. `role="img"`, `<title id="ad-title">`,
  `<desc id="ad-desc">` and `aria-labelledby="ad-title ad-desc"` are
  present and the desc's "clockwise" is true of the drawn loop. The
  `prefers-color-scheme` block overrides all fourteen tokens and the
  body paints nothing but tokens. Spelling is clean.
- **Process honesty.** Every PASS in `verification.md` quotes literal
  output that the branch reproduces; the thirty-second test is labelled
  anecdote and its reader (a model, not a person) is named in
  `assumptions:` and under Not verified; the red-then-green record used
  `git archive` trees and says so; the Provenance record lists five
  hand-edits and an 18-against-9 node overage rather than hiding them.
  The breakdown's six rows are checked with one honest `$0` ledger row
  each.

## Verdict

**Ready to ship: no critical findings, none unfixed.** One major (the
1.88 MB full-page screenshots) and one minor (the stale Stages-section
rationale in `lint.py`) were fixed on the branch in a67fdd2 and 1fdc9f9,
two nits in 203dcdd, and the battery is green after the last change
(1944 tests OK; lint 0; gates 0; selftest ok). Two minors are deferred
with reasons above: the three filename sublabels that stand in for their
stage's name, and the substring form of the embed check — both bounded
gaps in a drift detector, neither reachable by the figure as drawn. For
Ship: the merge must be the project's squash (a merge commit or rebase
would carry the uncropped blobs from `07ff88a` into `main`); the door is
two-way for the README, the figure and the checker (a revert restores
the mermaid) and one-way only for the 0.72 MB of screenshots once
squashed; the blast radius is every plugin install's clone size and the
front page every adopter reads first.
