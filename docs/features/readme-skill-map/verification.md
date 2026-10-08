---
stage: verify
run: feature:readme-skill-map
date: 2026-10-07
assumptions:
  - "No live interview: the soft gate was read from breakdown.md (six rows, all checked) and the criteria list was built from PRD-0008's seven Success criteria plus the one breakdown Accept no PRD criterion covers (the close-out ledger rows), without asking the user which subset to verify."
  - "The stand-in reader for the thirty-second test is a model, not a person: one fresh Claude subagent given only the path of the light github.com screenshot and the three questions, told to answer from the image alone. PRD-0008 left that choice to Verify. Its elapsed time is self-reported, from a `date +%s` before its Read of the image to one after. The record is anecdote."
  - "The thirty-second test's third question took its situations from two of the figure's own card titles (a codebase with no run yet, and drawing a system diagram) rather than the PRD's example of a pull request; the three questions were fixed verbatim by the autorun orchestrator's instructions and asked once, never re-asked."
  - "github.com's appearance for an anonymous visitor was taken as following the browser's `prefers-color-scheme`, which is what was observed: headless Chrome's `--blink-settings=preferredColorScheme=1` (light) and `=0` (dark) flipped both the page chrome and the figure inside the `<img>`. The architecture's plan toggles the OS appearance under a signed-in account set to sync; no account was signed in, so the browser preference stood in for the OS and GitHub's own appearance setting was not exercised."
  - "The branch was pushed by name (`git push -u origin feat/readme-skill-map`) before the screenshots, because github.com cannot render an unpushed branch; the autorun brief's Release authorization covers that push. Nothing else was done on GitHub: no issue, no pull request, no merge."
  - "The PRD's self-containment grep is read by intent, as the breakdown's assumption records: the SVG root's `xmlns` attribute names `http://www.w3.org/2000/svg`, an XML namespace identifier no renderer fetches, and it is the grep's only hit."
  - "The PRD's red-then-green check was done by extracting the row 0091 commit (tests, no function) and the row 0092 commit (function added) into scratch trees with `git archive`, because the brief forbids moving HEAD; in a `git archive` tree two unrelated tests that need a git checkout fail, and they are recorded as scratch artifacts, not as findings."
  - "The figure on github.com is served from the same-origin `/raw/` path rather than through the camo proxy (a relative image path in a public repository); the camo-URL fallback the orchestrator described was therefore not needed and was not run."
---

# Verification: README skill map

## Summary

7 PASS, 0 FAIL across PRD-0008's seven success criteria, plus one PASS for
the breakdown's close-out acceptance no PRD criterion covers (all six rows
checked, one honest zero-cost ledger row per row). The battery is green on
Python 3.14 and 3.12; the figure renders on the real github.com README page
in both appearance settings and the dark flip happens inside the plain
`<img>`, so architecture decision (d) holds and the `<picture>` fallback row
is not needed; the roster check fires in a scratch copy for a deleted slug
and for a new `skills/lean` directory; the stand-in reader answered all
three questions correctly in four seconds. Two observations for Review,
neither a criterion failure: the stage sublabels `idea.md`, `prd.md` and
`review.md` satisfy `names_slug` for their stage's slug on their own, and
the 10px text tier renders at about 8.9 CSS px at the width github.com's
blob view gave the figure. Next stage: Review.

Worktree HEAD `1fed0ce`, ten commits ahead of `main` `e64e7de`;
interpreters `Python 3.14.6` (default) and `Python 3.12.13` (CI's).
Repository visibility: `PUBLIC`.

## Criteria & evidence

### Thirty-second test

- Check: one fresh Claude subagent (general-purpose, no artifact, no
  design note, no hint) was given only the path of
  [`github-light.png`](github-light.png) and the three questions below,
  verbatim; told to Read the image, answer from it alone in at most three
  sentences each, and report the wall-clock seconds between a `date +%s`
  before the Read and one after. Its report is copied below unchanged and
  graded against the figure's own labels. The reader was a fresh Claude
  subagent given only the screenshot. This is an anecdote.
- Questions, as asked:
  ```
  1. In one sentence, what does this plugin do?
  2. Besides the pipeline stages, is there anything else in it? If so, what kind of things?
  3. You have a codebase and no run yet; you want to know what to improve. Which skill would you reach for, and which one would you use to draw a system diagram for the README?
  ```
- Evidence (the reader's report, verbatim):
  ```
  START: 1791423810
  END: 1791423814
  ELAPSED: 4 seconds
  A1: It is a Claude Code plugin of lifecycle-pipeline skills that guides work from a raw idea all the way to production, where each stage writes an artifact the next stage reads and those artifacts are the pipeline's state.
  A2: Yes. Besides the pipeline stages there is a router (`next`, the orange box) and a set of utility skills grouped by the moment you reach for them: before a run exists (audit, automate), reshaping what's built (deepen), driving a run (autorun, work-queue), around a pull request (address-pr-review), drawing pictures (mermaid, architecture-diagram, animated-diagram, interactive-architecture-diagram, pipeline-board), and installing the factory (factory-init, doctor).
  A3: For a codebase with no run yet where you want to know what to improve, I would reach for `audit` (listed under "Before a run exists"). For a system diagram for the README, I would use `architecture-diagram` (listed under "Drawing pictures").
  ```
- Grading, each answer against the PRD's pass condition and the figure's
  labels:
  - (a) what the pipeline does — pass condition: ordered stages from idea
    to production. A1 names ordered stages ("each stage writes an artifact
    the next stage reads") running "from a raw idea all the way to
    production". It does not enumerate the ten stage slugs; the question
    asked for one sentence on what the plugin does, and the answer carries
    the order, both endpoints and the artifacts-are-the-state idea. PASS.
  - (b) whether anything sits around the pipeline — pass condition:
    "utility skills" or words to that effect. A2 says "utility skills
    grouped by the moment you reach for them" and recites all six card
    titles and all thirteen members exactly as the figure labels them.
    PASS.
  - (c) which skill to reach for — pass condition: a skill in the named
    group. The first situation is the "Before a run exists" card (`audit`,
    `automate`); A3 names `audit`. The second is the "Drawing pictures"
    card; A3 names `architecture-diagram`. Both in their group. PASS.
- Elapsed: 4 seconds from the reader's `date` before the Read to its
  `date` after, well inside thirty; the answers followed the second
  `date`, so the figure was read, not studied.
- Result: PASS. Three of three answers pass on the figure's own labels, no
  answer was re-asked or reworded, and the whole record above is the
  anecdote the PRD asked for.

### Roster check

- Check: run `check_readme_figure` on the real tree through the public
  function; confirm by AST that its body holds no slug literal and no
  literal list; confirm its registration in `lint.CHECKERS`; read the
  tests that pin its strings; run the new test class against the row 0091
  commit (tests, no function) and the row 0092 commit (function added),
  each extracted with `git archive` into a scratch tree; delete one slug's
  `<text>` element in a fresh `cp -R` scratch copy and run `python3
  lint.py` there, beside Implement's recorded run of the same proof.
- Evidence:
  ```
  $ python3 -c "import lint; from pathlib import Path; print(lint.check_readme_figure(Path('.')))"
  []

  $ grep -n 'README_FIGURE\|^def check_readme_figure\|^def check_readme_no_orphans\|^def check_protocol' lint.py
  586:README_FIGURE = "docs/assets/skill-map.svg"
  617:def check_readme_no_orphans(root):
  663:def check_readme_figure(root):
  666:    SVG (README_FIGURE) hand-placed by a person, so it is a second copy
  686:    text, problem = read_file(root / README_FIGURE, README_FIGURE, str)
  690:        return [f"missing {README_FIGURE}"]
  694:        return [f"{README_FIGURE} is not valid SVG: {err}"]
  698:    problems = [f"{README_FIGURE} never names skill {slug!r}"
  702:    if readme is not None and README_FIGURE not in readme:
  703:        problems.append(f"README.md never embeds {README_FIGURE!r}")
  707:def check_protocol(root):
  765:def check_protocol_tables(root):

  $ sed -n 695,700p lint.py
      visible = " ".join("".join(element.itertext())
                         for element in tree.iter()
                         if element.tag.rpartition("}")[2] == "text")
      problems = [f"{README_FIGURE} never names skill {slug!r}"
                  for slug in ALL_SKILLS + extra_skills(root)
                  if not names_slug(visible, slug)]

  $ python3 - <<'PY'   # ast walk of check_readme_figure's body, docstring excluded
  string constants in check_readme_figure body (docstring excluded): ['', ' ', ' is not valid SVG: ', ' never names skill ', 'README.md', 'README.md never embeds ', 'missing ', 'text', '}']
  any ALL_SKILLS slug as a literal: []
  literal list/tuple/set of constants in body: 0

  $ python3 -c "import lint; print([c.__name__ for c in lint.CHECKERS])"
  ['check_manifest', 'check_plugin_skills', 'check_pi_package', 'check_skills', 'check_skill_recitals', 'check_skill_assets', 'check_templates', 'check_router', 'check_router_conditionals', 'check_readme_skills', 'check_readme_no_orphans', 'check_readme_figure', 'check_protocol', 'check_protocol_tables', 'check_backlog', 'check_evals', 'check_output_evals', 'check_ledger', 'check_ledger_no_orphans', 'check_ledger_links']

  $ grep -n 'class TestReadmeFigure\|never names skill\|never embeds\|missing docs/assets\|is not valid SVG\|cannot read docs/assets' tests/test_lint.py | sed -n '5,$p'
  846:class TestReadmeFigure(CheckerTreeTest):
  871:            ["docs/assets/skill-map.svg never names skill 'ship'"])
  888:            ["docs/assets/skill-map.svg never names skill 'ship'"])
  900:            ["docs/assets/skill-map.svg never names skill 'architect'"])
  921:            ["docs/assets/skill-map.svg never names skill 'rogue'"])
  932:            ["docs/assets/skill-map.svg never names skill 'ship'",
  933:             "docs/assets/skill-map.svg never names skill 'audit'",
  934:             "README.md never embeds 'docs/assets/skill-map.svg'"])
  939:                         ["missing docs/assets/skill-map.svg"])
  948:            "cannot read docs/assets/skill-map.svg:"), problems)
  957:            "docs/assets/skill-map.svg is not valid SVG:"), problems)

  $ python3 -m unittest tests.test_lint.TestReadmeFigure
  Ran 11 tests in 0.125s
  OK

  $ git archive 4e87871 | tar -x -C scratch/pre   # the row 0091 commit: tests landed, function absent
  $ (cd scratch/pre && python3 -m unittest tests.test_lint.TestReadmeFigure)
  exit=1
  Ran 11 tests in 0.122s
  FAILED (errors=11)
  AttributeError count: 11   # every one: module 'lint' has no attribute 'check_readme_figure'

  $ git archive 23cb773 | tar -x -C scratch/post  # the row 0092 commit: function added
  $ (cd scratch/post && python3 -m unittest tests.test_lint.TestReadmeFigure)
  exit=0
  Ran 11 tests in 0.121s
  OK

  $ git diff --stat 4e87871 23cb773 -- tests/test_lint.py
  (empty: the test file is byte-identical across the function's commit)

  $ (cd scratch/pre && python3 -m unittest discover tests)   # the whole suite at the row 0091 commit
  Ran 1944 tests in 22.894s
  FAILED (failures=1, errors=12)
  TestReadmeFigure errors: 11; other: test_resolves_to_this_git_checkout (FAIL), test_no_tracked_module_shadows_a_definition (ERROR) — both need a git checkout and a git-archive tree is not one

  $ cp -R . scratch/copy-slug && cd scratch/copy-slug   # fresh scratch copy, never the worktree
  $ grep -n '>address-pr-review<' docs/assets/skill-map.svg
  222:  <text class="row mono" x="60" y="418">address-pr-review</text>
  $ python3 - (delete that one <text> element)
  elements removed: 1 -> remaining mentions: 0
  $ python3 lint.py
  LINT: docs/assets/skill-map.svg never names skill 'address-pr-review'
  lint: 1 problem(s) across 25 skills
  exit=1
  $ rm -rf scratch/copy-slug; git status --short   # in the worktree
  (empty)
  ```
- Implement's own record of the same proof, copied from breakdown.md's
  Notes (row 0095): "In a second fresh copy, the one `<text>` element
  holding `address-pr-review` deleted from the figure, `python3 lint.py`
  printed `LINT: docs/assets/skill-map.svg never names skill
  'address-pr-review'` and `lint: 1 problem(s) across 25 skills`, exit 1."
  This stage's re-run above printed the same two lines.
- Observation for Review, not a failure: the checker reads every `<text>`
  element, and the stage sublabels are artifact filenames, so
  `names_slug("idea.md", "idea")`, `names_slug("prd.md", "prd")` and
  `names_slug("review.md", "review")` are each `True` (a dot is a slug
  boundary). For those three stages the sublabel alone would satisfy the
  roster line if the name were lost. The breakdown's row 0093 forbids a
  whole-slug match in the title, subtitle, eyebrow, edge labels and legend
  only, and those five hold (checked: the twenty-nine non-slug `<text>`
  elements match no slug except those three sublabels). The other nine
  sublabels (`architecture.md` against `architect`, `verification.md`
  against `verify`, and so on) match nothing.
- Result: PASS. The checker reads the roster from `ALL_SKILLS +
  extra_skills(root)` through `names_slug` with no slug literal and no
  literal list in its body; it is registered directly after
  `check_readme_no_orphans`; the tests pin the exact strings through the
  public function, all eleven error with `AttributeError` at the commit
  before the function and pass at the commit that adds it with the test
  file unchanged; and deleting one slug's visible text makes `python3
  lint.py` print the one expected problem and exit 1.

### Figure

- Check: the mermaid fence count; the embed line; the PRD's
  self-containment grep; every `ALL_SKILLS` slug as the whole content of
  a `<text>` element, by XML parse and by per-slug grep; the root
  `width`/`height`/`viewBox`; the content the mermaid chain showed (the
  router, the ten ordered stages, the UX conditional, the operate-to-idea
  loop), read off the rendered screenshots; and the real github.com
  README page of the pushed branch, screenshotted with headless Chrome at
  2× in both colour schemes and inspected, with pixel samples inside the
  figure to prove the flip.
- Evidence:
  ```
  $ grep -c '^```mermaid' README.md
  0
  $ grep -n -o '!\[[^]]*\]\|(docs/assets/skill-map.svg)' README.md   # the one embed line, alt text and target as two fragments (a verbatim quote would read as a link from this directory, detector I)
  7:![The skill map: the pipeline stages as a closed loop with the router inside it, a maintenance run entering from outside, and the utility skills grouped in cards by the moment you reach for them.]
  7:(docs/assets/skill-map.svg)

  $ grep -nE 'http|<script|@import|@font-face' docs/assets/skill-map.svg
  1:<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 688" width="880" height="688" role="img"
  (one hit: the root's xmlns namespace identifier, which no renderer fetches — the breakdown's recorded reading)

  $ python3 -c "import xml.etree.ElementTree as ET, protocol; root = ET.parse('docs/assets/skill-map.svg').getroot(); texts = [''.join(e.itertext()) for e in root.iter() if e.tag.rpartition('}')[2] == 'text']; missing = [s for s in protocol.ALL_SKILLS if s not in texts]; print('ALL_SKILLS:', len(protocol.ALL_SKILLS), '| <text> elements:', len(texts), '| slugs present as a whole <text> content:', len(protocol.ALL_SKILLS) - len(missing), '| missing:', missing)"
  ALL_SKILLS: 25 | <text> elements: 54 | slugs present as a whole <text> content: 25 | missing: []

  $ for each slug in ALL_SKILLS: grep -c ">slug<" docs/assets/skill-map.svg
  next=1  idea=1  prd=1  ux-design=1  architect=1  decompose=1  implement=1  verify=1  review=1  ship=1  operate=1  capture=1  address-pr-review=1  animated-diagram=1  architecture-diagram=1  audit=1  automate=1  autorun=1  deepen=1  doctor=1  factory-init=1  interactive-architecture-diagram=1  mermaid=1  pipeline-board=1  work-queue=1

  $ python3 -c "import xml.etree.ElementTree as ET; r = ET.parse('docs/assets/skill-map.svg').getroot(); print({k: r.get(k) for k in ('width','height','viewBox')})"
  {'width': '880', 'height': '688', 'viewBox': '0 0 880 688'}

  $ grep -c -E 'font-size: *[0-9]px' docs/assets/skill-map.svg; grep -c 'prefers-color-scheme: dark' docs/assets/skill-map.svg; awk '/<\/style>/{p=1;next} p' docs/assets/skill-map.svg | grep -c -E '#[0-9a-fA-F]{3,6}\b'
  0
  1
  0
  $ grep -o -E 'class="conn( async)?"' docs/assets/skill-map.svg | wc -l
  14    # 12 connectors plus the two legend swatches (lines 250 and 252)

  $ gh repo view mattbutlerengineering/skills --json visibility,isPrivate
  {"isPrivate":false,"visibility":"PUBLIC"}
  $ git push -u origin feat/readme-skill-map
   * [new branch]      feat/readme-skill-map -> feat/readme-skill-map
  $ curl -sL https://github.com/mattbutlerengineering/skills/blob/feat/readme-skill-map/README.md | grep -o '<img[^>]*skill-map[^>]*>'
  <img src="/mattbutlerengineering/skills/raw/feat/readme-skill-map/docs/assets/skill-map.svg" alt="The skill map: [the README line 7 alt text, elided here]" style="max-width: 100%;">
  (served same-origin from /raw/, not through camo; curl ... | grep -o 'https://camo[^"]*' printed nothing)

  $ "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --screenshot=github-light.png --force-device-scale-factor=2 --window-size=1200,2200 --blink-settings=preferredColorScheme=1 --virtual-time-budget=10000 <url>
  $ ... --screenshot=github-dark.png ... --blink-settings=preferredColorScheme=0 ...
  (both wrote a 2400 x 4400 PNG; Chrome then hung on the page's timers and was killed — the files were complete)

  $ python3 pixel.py github-light.png      # stdlib PNG decode; coordinates in the 2x capture
  figure paper (top-left inside figure)      (800,1050) = #f6f5f1
  figure paper (between cards, mid)          (1400,1480) = #f6f5f1
  page background below figure               (1500,2270) = #ffffff
  router box fill (next)                     (1578,1540) = #f3e9e1
  $ python3 pixel.py github-dark.png
  figure paper (top-left inside figure)      (800,1050) = #0d1117
  figure paper (between cards, mid)          (1400,1480) = #0d1117
  page background below figure               (1500,2270) = #0d1117
  router box fill (next)                     (1578,1540) = #231e1e
  $ grep -n -E '\-\-paper' docs/assets/skill-map.svg
  14:    --paper: #f6f5f1;
  31:      --paper: #0d1117;

  $ python3 measure.py github-light.png     # widest run of paper-coloured pixels
  figure paper span: 1562 device px at 2x = 781 CSS px wide (x 740..2301); 610 CSS px tall (rows 1013..2233)
  scale vs the 880 viewBox: 0.887; the 10px tier renders at 8.9 CSS px, 11px rows at 9.8, 13px names at 11.5
  ```
- The two github.com screenshots, read with the image reader:
  [`github-light.png`](github-light.png) and
  [`github-dark.png`](github-dark.png). Both show the blob view of
  `README.md` on `feat/readme-skill-map`, signed out ("Sign in" / "Sign
  up" in the header), with the figure directly under the tagline
  paragraph. In both: the eyebrow "PLUGIN OVERVIEW", the title "Every
  skill, and the moment you reach for it", the ten stage boxes in loop
  order (idea → prd → ux-design → architect down the right column to
  decompose → implement, then implement → verify → review → ship along
  the bottom row, and ship → operate → idea back up the left), each with
  its artifact sublabel; `next / the router` as the one accented box
  inside the loop; `capture / defect.md` outside the loop at bottom right
  with a dashed `RE-ENTRY` arrow into implement; the dashed `NO UI
  SURFACE` arc from prd to architect over the top; `RETRO SEEDS` on the
  operate → idea edge; the six cards with their titles and members; and
  the five-item legend. Every slug and every card title is readable in
  the capture. In the dark capture the figure's paper is GitHub's own
  dark background (`#0d1117`, so the figure has no visible edge against
  the page), the ink is light, the router box carries a dark accent fill
  with a warm outline, and nothing is left in a light colour — the flip
  is complete, inside a plain markdown `<img>`, with the browser's colour
  scheme preference and no signed-in GitHub setting.
- Legibility, honestly: the blob view at a 1200px window with the file
  sidebar open gave the figure 781 CSS px, so the 10px tier (eyebrow,
  edge labels, legend) renders at about 8.9 CSS px and the 11px slug
  rows at about 9.8 CSS px. In the 2× capture every label reads; at 1×
  the legend and edge labels are small. The repository home page's
  README column is wider than the blob view's. Noted for Review; the
  slug names and card titles, which the thirty-second test is timed on,
  read without zooming.
- 2026-10-07, Review (finding 1): the committed `github-light.png` and
  `github-dark.png` are pixel-exact crops of the 2400 × 4400 captures to
  the README content column — columns 660 to 2399, rows 0 to 2249, so
  1740 × 2250 — made with `sips --cropOffset 0 660 -c 2250 1740` on a
  copy of each capture. The signed-out header, the branch commit in the
  commit bar, the Preview toolbar and the whole figure are inside the
  crop; the file sidebar and the page below the figure are not. Every
  coordinate quoted above is in the uncropped capture: subtract 660
  from x to find the same pixel in the committed file (y is unchanged);
  the four samples re-read at the shifted coordinates give the same four
  values. 934 KB and 942 KB became 358 KB each.
- Result: PASS. The mermaid block is gone and one committed SVG is
  embedded as a plain image; the file makes no external request (the
  only grep hit is the namespace identifier); every roster slug is the
  literal content of a `<text>` element; the root carries `width`,
  `height` and `viewBox`; the figure shows the router, the ten ordered
  stages, the UX conditional and the operate-to-idea loop plus every
  utility skill in a titled card; and it renders on the real github.com
  page in both appearance settings, the dark variant flipping inside the
  `<img>` — architecture decision (d) holds and the `<picture>` fallback
  row the breakdown reserved is not needed.

### Table and section

- Check: the `## Stages` heading on both sides; the stage table's lines
  diffed against `main`; every `|` line the branch changed in README.md;
  the utility table's body rows counted and their slug set compared with
  `protocol.UTILITY_SKILLS`; orphans inside `## Stages` through
  `readme_stage_mentions`; `check_readme_no_orphans` and
  `check_readme_skills` through the public functions.
- Evidence:
  ```
  $ grep -n '^## ' README.md
  9:## Install
  38:## Usage
  56:## Stages
  98:## Development
  108:## License
  $ git show main:README.md | grep -n '^## '
  34:## Install
  63:## Usage
  81:## Stages
  158:## Development
  168:## License

  $ diff <(git show main:README.md | sed -n '/^## Stages/,/^## Development/p' | grep '^|' | head -14) <(sed -n '/^## Stages/,/^## Development/p' README.md | grep '^|' | head -14)
  exit=0   # empty: the stage table is byte-identical to main

  $ git diff main -- README.md | grep -E '^[-+]\|'
  +| Skill | Moment | Why it matters |
  +|-------|--------|----------------|
  +| `audit` | Before a run exists | ...
  +| `automate` | Before a run exists | ...
  +| `deepen` | Reshaping what's built | ...
  +| `autorun` | Driving a run | ...
  +| `work-queue` | Driving a run | ...
  +| `address-pr-review` | Around a pull request | ...
  +| `mermaid` | Drawing pictures | ...
  +| `architecture-diagram` | Drawing pictures | ...
  +| `animated-diagram` | Drawing pictures | ...
  +| `interactive-architecture-diagram` | Drawing pictures | ...
  +| `pipeline-board` | Drawing pictures | ...
  +| `factory-init` | Installing the factory | ...
  +| `doctor` | Installing the factory | ...
  (why cells elided; `... | wc -l` = 15 added table lines, `grep -c -E '^-\|'` = 0 removed: the only table change is the new utility table)

  $ python3 table_rows.py   # splits the ## Stages section at blank lines, takes the table headed "| Skill | Moment | Why it matters |"
  body rows: 13 | len(UTILITY_SKILLS): 13
  set(table slugs) == set(UTILITY_SKILLS): True
  duplicates: []
  orphans in ## Stages: set()
  check_readme_no_orphans: []
  check_readme_skills: []
  ```
- Result: PASS. The heading is unchanged and the stage table under it is
  byte-identical to `main`; the utility table has exactly thirteen body
  rows, one per `UTILITY_SKILLS` entry with none repeated, each slug in
  backticks beside a moment and a one-line why; every slug-shaped
  backtick token in the section is a registered skill and both README
  checkers return `[]`.

### Provenance

- Check: `architecture.md` decision (a) for which skill drew the figure
  and why; `git diff --stat main -- skills/` to show the skill's own
  files were not edited; the figure's provenance record copied from
  breakdown.md's Notes (row 0093), which is where the breakdown's
  assumption put it.
- Evidence:
  ```
  $ git diff --stat main -- skills/
  (empty: the diagram skill, its scaffold and its design system are untouched)

  $ grep -n '(a) `architecture-diagram`' docs/features/readme-skill-map/architecture.md
  291:- **(a) `architecture-diagram`, and the figure does not move** over
  ```
- Which skill drew it: `architecture-diagram`, by architecture decision
  (a) — over `animated-diagram` because the animated skill's output is
  dark-only by its own design system (fails user story 2), its motion
  encodes execution direction where this figure is a map, and its budget
  is tighter still; the still skill is theme-aware and the family member
  that embeds in READMEs.
- Hand-edits and iterations, copied from breakdown.md's Notes (row 0093,
  the figure's provenance record): drawn by working
  `skills/architecture-diagram/SKILL.md`'s seven steps in order from a
  `cp` of its `assets/boilerplate.svg`; the asset is unchanged. Hand-edits
  the scaffold needed beyond replacing the sample content and the
  title/desc text, each a departure the skill's own text does not
  sanction: (1) root `width="880" height="688"` beside the `viewBox` —
  the scaffold carries only a `viewBox`, and an SVG with no intrinsic
  size is fitted to 300×150 inside `<img>`; (2) the `.eyebrow` tier
  raised 8→10px, `.elabel` 9→10px and `.legend-t` 9→10px, so no text in
  the figure is below 10px at README width; (3) one added class, `.row`
  (mono via the existing `.mono`, 11px, `--ink`), for a card's member
  slugs — the design system has no list-row tier, and its 10px muted
  sublabel is too faint for the one thing a reader came to find; (4) the
  edge-label mask is 14px tall (the scaffold's is 12) to clear the raised
  label; (5) the six "moment cards" are a composition the design system
  does not define — its `node-ext` treatment with a left-aligned `.name`
  title and `.row` members — used as node-like containers per
  `architecture.md` decision (c). Counts against the skill's budget: 18
  nodes (12 stage-side boxes plus 6 cards) against a ceiling of 9 — the
  overage decision (c) records; 12 connectors against 12; 0 zones against
  3; 1 accent element against 2. Step 7's checks, each with its outcome:
  both themes standalone — ran, headless Chrome at 2× device scale, both
  PNGs inspected: every element flips, no stranded light colour, the
  label mask included — pass; both themes embedded as an image — ran, a
  scratch HTML page with `<img src>` in an 830px column under both
  schemes: renders identically at intrinsic size scaled to the column,
  the dark paper matching GitHub's `#0d1117` — pass; the remove test —
  ran, nothing removed: the stage sublabels carry "artifacts are the
  state", `the router` names the focal node, `no ui surface`, `retro
  seeds` and `re-entry` each explain the one edge whose meaning its style
  does not, and the five legend rows are exactly the treatments and line
  kinds drawn. Not run at Implement: the real github.com page in either
  appearance setting — run here, under the Figure criterion. Three
  drawing iterations: v1 placed "Installing the factory" in a 256-wide
  card with a blank right half and top-aligned the cards to the 56-tall
  nodes; v2 made that card 176 wide under the review–verify columns and
  centred every card on its row's centre line; v3 reworded the subtitle
  and `<desc>`, which had said "Ten" and "Six", to carry no count.
- This stage's reading of that record: five hand-edits, two of them
  (the intrinsic size and the text tiers) findings about the scaffold
  for the diagram skill's own backlog, three of them compositions the
  roster map needed that a system figure does not; and the node budget
  overage (18 against 9) is the fit between a system-figure skill and a
  map, as decision (c) says, not a surprise. The front page's dogfooding
  claim is honest: the figure is the skill's scaffold, tokens, connector
  grammar and verify steps, with those departures named.
- Result: PASS. `architecture.md` records the skill and the reason; the
  hand-editing is recorded above, copied from Implement's dated note;
  the skill's files are unchanged; the figure was drawn by a skill in
  `skills/`, not by hand or by an outside tool.

### Room for lean and polish

- Check: grep README.md and the figure for either name; the breakdown's
  `mkdir skills/lean` proof copied from its Notes and re-run in a fresh
  `cp -R` scratch copy under the session scratchpad, never the worktree;
  the architecture's card table for where each would join.
- Evidence:
  ```
  $ grep -c -E '\blean\b|\bpolish\b' README.md docs/assets/skill-map.svg
  README.md:0
  docs/assets/skill-map.svg:0

  $ cp -R . scratch/copy-lean && cd scratch/copy-lean && mkdir skills/lean && printf -- '---\nname: lean\ndescription: a cut-list for a diff or a tree\n---\n\nbody\n' > skills/lean/SKILL.md
  $ python3 lint.py
  LINT: skills/lean is not in the skill taxonomy (protocol.py ALL_SKILLS)
  LINT: README.md never names skill 'lean'
  LINT: docs/assets/skill-map.svg never names skill 'lean'
  LINT: LEDGER.md has no row for skill 'lean'
  lint: 4 problem(s) across 26 skills
  exit=1
  $ rm -rf scratch/copy-lean; git status --short   # in the worktree
  (empty)

  $ grep -n "^| Reshaping what's built" docs/features/readme-skill-map/architecture.md
  104:| Reshaping what's built | `deepen` | `lean`, `polish` | the entry, beside the card above |
  ```
- Implement's own record of the proof, copied from breakdown.md's Notes
  (row 0095): "in a `cp -R` of the tree under the session scratchpad,
  never the checkout, `mkdir skills/lean` with a minimal `SKILL.md`, then
  `python3 lint.py` printed, in this order: `LINT: skills/lean is not in
  the skill taxonomy (protocol.py ALL_SKILLS)`, `LINT: README.md never
  names skill 'lean'`, `LINT: docs/assets/skill-map.svg never names skill
  'lean'`, `LINT: LEDGER.md has no row for skill 'lean'`, `lint: 4
  problem(s) across 26 skills`." This stage's re-run printed the same
  four problems in the same order.
- Result: PASS. Neither name appears in the figure or the README; the
  moment a `skills/lean` directory exists the figure problem naming
  `lean` is among lint's output beside the README one; and
  `architecture.md`'s card table puts both in "Reshaping what's built",
  so each arrives as a row in an existing card and a table row.

### Battery and untouched surfaces

- Check: the full battery from the worktree root on both installed
  interpreters, each output written to a scratch file and grepped; the
  guarded diff stats against `main`; the Install-through-Stages and
  Development-through-end sections diffed against `main`; the full diff
  stat.
- Evidence:
  ```
  $ python3 --version; python3.12 --version
  Python 3.14.6
  Python 3.12.13

  $ python3 -m unittest discover tests > unittest-314.txt 2>&1; echo "exit=$?"; grep -E '^(Ran |OK|FAILED)' unittest-314.txt
  exit=0
  Ran 1944 tests in 23.928s
  OK

  $ python3.12 -m unittest discover tests > unittest-312.txt 2>&1; echo "exit=$?"; grep -E '^(Ran |OK|FAILED)' unittest-312.txt
  exit=0
  Ran 1944 tests in 22.545s
  OK

  $ python3 lint.py > lint.txt 2>&1; echo "exit=$?"; grep -E '^lint:' lint.txt
  exit=0
  lint: 0 problem(s) across 25 skills
  $ python3.12 lint.py
  lint: 0 problem(s) across 25 skills

  $ (python3 gates.py && python3 gates.py --selftest) > gates.txt 2>&1; echo "exit=$?"; grep -E '^(gates:|selftest:)' gates.txt
  exit=0
  gates: 0 problem(s)
  selftest: ok
  $ (python3.12 gates.py && python3.12 gates.py --selftest)
  gates: 0 problem(s)
  selftest: ok

  $ git diff --stat main -- skills/ .claude-plugin/plugin.json evals/ LEDGER.md
  (empty)

  $ diff <(git show main:README.md | sed -n '/^## Install/,/^## Stages/p') <(sed -n '/^## Install/,/^## Stages/p' README.md); echo "exit=$?"
  exit=0   # empty: Install and Usage are byte-identical to main
  $ diff <(git show main:README.md | sed -n '/^## Development/,$p') <(sed -n '/^## Development/,$p' README.md); echo "exit=$?"
  exit=0   # empty: Development and License are byte-identical to main

  $ git diff --stat main
   README.md                                       | 100 ++----
   docs/assets/skill-map.svg                       | 254 +++++++++++++++
   docs/factory/costs.jsonl                        |   6 +
   docs/features/readme-skill-map/architecture.md  | 403 ++++++++++++++++++++++++
   docs/features/readme-skill-map/autorun-brief.md |  98 ++++++
   docs/features/readme-skill-map/breakdown.md     | 195 ++++++++++++
   docs/features/readme-skill-map/idea.md          |  95 ++++++
   docs/features/readme-skill-map/prd.md           | 197 ++++++++++++
   lint.py                                         |  53 +++-
   tests/test_lint.py                              | 137 +++++++-
   10 files changed, 1456 insertions(+), 82 deletions(-)
  ```
- Result: PASS. 1944 tests `OK` on both interpreters, `lint: 0
  problem(s)`, `gates: 0 problem(s)`, `selftest: ok`; nothing under
  `skills/`, `evals/`, the plugin manifest or `LEDGER.md` moved; the
  README's Install, Usage, Development and License sections are
  byte-identical to `main`; and the diff against `main` lists exactly the
  files the breakdown's row 0096 names — README.md, the figure, the
  ledger rows, this run's artifacts, `lint.py` and `tests/test_lint.py`
  (this stage adds `verification.md` and the two screenshots).

### Breakdown close-out (acceptance no PRD criterion covers)

- Check: every row checked; one honest ledger row per checked row, as the
  breakdown's Notes commit to (detector G reads a checked row as a merged
  work order owed a cost line).
- Evidence:
  ```
  $ grep -c '^- \[x\]' docs/features/readme-skill-map/breakdown.md; grep -c '^- \[ \]' docs/features/readme-skill-map/breakdown.md
  6
  0

  $ git diff main -- docs/factory/costs.jsonl | grep -c '^+{'
  6
  $ ... | python3 -c 'rows=[json.loads(l[1:]) ...]; print(sorted(run_id)); print({(tokens, cost, outcome)})'
  ['session-2026-10-07-wo-0091', 'session-2026-10-07-wo-0092', 'session-2026-10-07-wo-0093', 'session-2026-10-07-wo-0094', 'session-2026-10-07-wo-0095', 'session-2026-10-07-wo-0096']
  {(0, 0.0, 'owner-session:unmetered')}
  ```
- Result: PASS. Six of six rows are checked and six `$0` owner-session
  ledger rows were appended, one per row from 0091 to 0096, which is why
  `gates: 0 problem(s)` holds with detector G in the set.

## Failures

None.

## Not verified

- **A human reader.** The thirty-second test was run on a model (one
  fresh Claude subagent), not on a person new to the repo. PRD-0008 left
  the choice to Verify and labels the result anecdote either way; a
  person's read of the same page remains unobserved, and the owner's own
  judgement of the rendered figure at the merge gate is the next one.
- **GitHub's own appearance setting.** The dark flip was proved under the
  browser's `prefers-color-scheme` with no account signed in, which is
  every anonymous adopter's situation. A signed-in reader whose GitHub
  appearance is fixed to the opposite of their OS was not exercised; the
  architecture's embed seam already records that such a setting does not
  reach inside an `<img>` (the diagram skill's documented trade), and
  this stage saw nothing that changes that.
- **The figure at the repository home page's README width.** The
  screenshots are of the blob view of `README.md` on the branch (the only
  page where an unmerged branch's README renders), where the file sidebar
  narrows the content column to 781 CSS px at a 1200px window. The home
  page's wider column is what adopters meet after merge and was not
  captured, because the branch is not `main`.
- **The routing eval** (`python3 trigger_eval.py`) and
  **`charter_replay.py`** were not run: both drive the `claude` CLI and
  cost money, and nothing in this run touches a skill's description or a
  role charter (`git diff --stat main -- skills/` is empty).
- **Detector B on a live pull request event.** B skips locally without a
  PR event payload; its selftest ran (`selftest: ok`) and `gates.py` is
  unchanged against `main`. This run opens no PR; Ship does.
- **A screen reader.** The PRD's reason for literal `<text>` slugs
  includes screen readers; the roster check and the per-slug grep prove
  the text is literal, and the root carries `role="img"` with
  `aria-labelledby` pointing at the `<title>` and `<desc>`, but no screen
  reader was run against the page.
