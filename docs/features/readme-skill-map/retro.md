---
stage: operate
run: feature:readme-skill-map
date: 2026-10-08
assumptions:
  - "No live interview: every outcome below is read from the run's seven artifacts and from autorun-brief.md's 'Feedback on hand at Operate (2026-10-08)' section, the only owner feedback on record. The owner's two choices at the gate — 'I've looked; squash-merge #615' and 'Run the retro now' — are the only owner words and are graded as anecdote."
  - "Step 3 (let it breathe) was answered by the owner: this retro is written about one day after the release, with outside signal absent, because the owner chose to run it now rather than return once there is usage. The skill's own recommendation would have been to wait; the owner's choice overrides it, and every outcome that needs usage is recorded as absence, never as a finding either way."
  - "The thirty-second test is not re-run here on a person: a human reader is an evidentiary question with no default and nobody on hand, so it is carried as a seed, not scored."
  - "Signal strength uses the TEMPLATE's three labels — anecdote (one reader or one owner judgement), pattern (the same signal from independent sources), measured (a command's literal output quoted in an artifact) — and the word 'absence' where the brief records nothing, which is not a fourth strength but the lack of one."
  - "The 36-assumption count is the sum of the assumptions: entries in the six unattended artifacts' frontmatter — prd.md 4, architecture.md 6, breakdown.md 5, verification.md 8, review.md 5, release.md 8 — counted on 2026-10-08; idea.md, the one stage run interactively, logged none."
  - "Every carrier in the Environment table is a proposal: this stage edited nothing in lint.py, gates.py, budget_guard.py, the workflows, the skills or CLAUDE.md. The next free detector letter, P, is taken from gates.py's own module docstring."
---

# Retro: README skill map (PRD-0008)

Written on 2026-10-08, about one day after the squash merge (`15caaa9`,
pull request #615, merged 2026-10-07 local), by the owner's choice to run
the retro now rather than let it breathe. Outside signal is absent — 0
stars, 0 forks, 0 watchers, no issue opened, no comment beyond the factory
review, the repository public for about a day — so this reflects the run,
the owner's gate judgement and the shipped mechanism, not accumulated
usage; the adoption signal is a seed below, to be revisited.

## Outcomes vs. intent

### idea.md's success sentence: a newcomer reads the figure in thirty seconds, and a mechanical check keeps it naming every skill

- What happened: the mechanical half holds — `check_readme_figure` is
  live in `lint.CHECKERS` on `main`, `python3 lint.py` prints 0 problems
  there, and the check fired in two scratch copies (one `<text>` element
  deleted; `mkdir skills/lean`). The newcomer half is unobserved: the
  only readers so far are a fresh model subagent (3 of 3 answers, 4
  seconds, [verification.md](verification.md)) and the owner at the gate
  (approved the rendered page, no change requested), neither of whom is a
  newcomer. Nobody outside has opened the page that anyone knows of.
- Signal strength: measured (the roster check); anecdote (the two
  readers); absence (a newcomer).

### Thirty-second test

- What happened: PASS on a stand-in reader — one fresh Claude subagent
  given only the light github.com screenshot answered what the pipeline
  does, that utility skills surround it grouped by moment, and named
  `audit` and `architecture-diagram` for two situations taken from the
  card titles; 4 seconds, answers verbatim in verification.md, labelled
  anecdote there. The reader was a model, not a person (Verify's
  assumption, PRD-0008 having left the choice open). The owner's gate look
  is the second reader and the first human one: approval, no words about
  the figure itself.
- Signal strength: anecdote, twice over — and neither reader is the
  adopter the criterion describes.

### Roster check

- What happened: shipped and registered directly after
  `check_readme_no_orphans`; eleven tests pin its strings through the
  public function; the red-then-green record used `git archive` trees;
  Review's two mutations each went red on the existing tests. On `main`
  after the merge: `lint: 0 problem(s) across 25 skills`. Two bounded gaps
  were deferred with reasons ([review.md](review.md): the `idea.md`,
  `prd.md` and `review.md` sublabels satisfy `names_slug` for their own
  stage; the README-embed half is a substring test). Its first real catch
  is still ahead: `skills/lean` and `skills/polish` do not exist on `main`
  today, and the lean-and-polish worktree (`661ffc7`, uncommitted) will
  meet the check on rebase.
- Signal strength: measured (lint output, the mutation runs); the live
  catch is absence.

### Figure

- What happened: the mermaid fence is gone; one committed SVG with one
  `grep` hit (the root `xmlns`), every one of 25 slugs the whole content
  of a `<text>` element, root `width`/`height` beside the `viewBox`; both
  appearance settings proven on the real github.com blob view by pixel
  sample (`#f6f5f1` paper and `#f3e9e1` router fill in light; `#0d1117`
  and `#231e1e` in dark), the flip happening inside a plain `<img>` so
  architecture decision (d) held and the `<picture>` fallback row was
  never opened. After the merge the orchestrator saw the figure on the
  repository home page at full README width in light (1280px window,
  1x): loop, six cards and legend legible. Dark was not re-captured on
  the home page. On the record and still true: in the blob view the
  figure got 781 CSS px, so the 10px tier rendered at about 8.9 CSS px —
  the slugs and card titles read, the legend and edge labels are small.
- Signal strength: measured (grep, parse, pixel samples); anecdote (the
  home-page look); absence (the home page in dark).

### Table and section

- What happened: `## Stages` and its stage table byte-identical to the
  pre-merge `main`; thirteen body rows equal to `len(UTILITY_SKILLS)`
  with no duplicate; no orphan token inside the section; both README
  checkers return `[]`. Review fixed two wording nits (one British
  spelling, one lead-in sentence). Whether the owner now scans the table
  instead of searching sixty lines of prose — the owner story — is
  unobserved: the owner has not re-read the roster since the merge on any
  record.
- Signal strength: measured (conformance); absence (use).

### Provenance

- What happened: drawn with `architecture-diagram` by its seven steps
  from a copy of its scaffold; `git diff --stat main -- skills/` empty.
  Five hand-edits and an 18-against-9 node overage are written down in
  breakdown.md's row 0093 note and copied into verification.md, so the
  front page's dogfooding claim is honest about exactly what the skill
  did not supply. Two of the five (the root size attributes; the 8–9px
  text tiers) are scaffold defects for any README embed; three (the
  `.row` tier, the taller label mask, the six moment cards) are the fit
  between a system-figure skill and a roster map.
- Signal strength: measured (the empty diff, the dated note).

### Room for lean and polish

- What happened: neither name anywhere in README.md or the figure; in a
  scratch copy `mkdir skills/lean` produced four lint lines including
  `docs/assets/skill-map.svg never names skill 'lean'`; architecture.md's
  card table names "Reshaping what's built" for both. The live event has
  not happened — the branch that adds them has not rebased.
- Signal strength: measured (the scratch proof); the real rebase is
  absence.

### Battery and untouched surfaces

- What happened: 1944 tests `OK` on Python 3.14 and 3.12 at `1fed0ce`,
  again on 3.14 at `dccc351`, and on CI for the pull-request event and
  for `main` at `15caaa9`; `lint: 0 problem(s)`, `gates: 0 problem(s)`,
  `selftest: ok` throughout; `skills/`, `evals/`, `LEDGER.md` and the
  plugin manifest untouched; `plugin.json` stays `0.3.0`. The known
  consequence of the last point: every installed `0.3.0` copy still shows
  the mermaid chain and has no `docs/assets/` until the next bump
  re-copies the cache, so the public page and the install disagree for
  now — by the PRD's own out-of-scope, not a criterion failure.
- Signal strength: measured.

## Run retrospective

- Keep: unattended stages that log every decision under `assumptions:` —
  36 across the six unattended artifacts, each traceable to the brief,
  idea.md or a skill default, and none contradicted at the gate. Reading
  them back, one would plausibly have gone differently in a live
  interview: Verify's choice of a model as the stand-in reader (the owner
  or a named person would have been asked for). The group cut, the figure
  path, the checker's name, the ledger policy, the fix-before-ship rule
  and the date rule were all defaults a live owner would have waved
  through — the rendered result got exactly that wave at the gate.
- Keep: the breakdown's sequencing — tests first and red (row 0091), the
  function unregistered (row 0092), the figure and the README (rows
  0093–0094), then the registration (row 0095) — which kept `python3
  lint.py` green at every row boundary on the branch and let Verify prove
  red-then-green from two `git archive` trees without moving HEAD.
- Keep: skipping UX Design by PRD decision (`ux: not-applicable`, reason
  recorded, echoed in architecture.md). The figure's visual design did
  need a process, and it had two — the architect's lettered decisions
  (one figure in two layers, cards as text rows, the router without an
  arrow) and the diagram skill's own seven steps. A `ux.md` would have
  restated architecture.md's figure model; the owner's approval of the
  render is the evidence the call was right.
- Keep: Review as a fixing stage under the orchestrator's rule (fix a
  critical or a major; fix a minor only when one line and safe; otherwise
  defer with a reason). It found the one major of the run and three
  commits later the battery was green again; the mutation runs proved
  the new tests bite before the verdict was written.
- Change: Verify's evidence weight. Review found and fixed a major that
  Verify had created — 1.88 MB of full-page 2x captures for a claim that
  needs the README content column — and nothing mechanical looked at
  the added bytes between the Verify commit and the Review read. The
  crop belongs at capture time, and the guard belongs in `make check`
  (Environment table, row 1). The stage order worked; the environment
  did not.
- Change: the figure's drawing cost — three iterations and five hand-edits
  beyond the scaffold — splits two ways and only one is expected. The
  scaffold's missing intrinsic size and its sub-10px tiers are weaknesses
  of the `architecture-diagram` skill that every README embed will hit
  (seed below, for the skill itself). The `.row` tier, the mask height
  and the card composition are what drawing a 25-slug roster map with a
  nine-node system-figure skill costs, and architecture decision (c) took
  that cost with reasons; the three iterations (a mis-sized card, card
  alignment, a count in the subtitle) are ordinary drawing, not a skill
  gap.
- Change: a criterion about a human reader names the reader kind. PRD-0008
  left "who is the stand-in reader" to Verify and Verify, unattended,
  chose the reader it could reach; the owner's own look at the gate was
  the only human read and it was not timed or asked the three questions.
- Stop: committing full-page captures as evidence. The claim was "the real
  github.com page, not a local preview"; the content column with the
  signed-out header and the commit bar proves it at 358 KB, and the page
  below the figure proves nothing.

## Environment

The repo's own check command has a guardrail: `make check` (lint, gates,
selftest, unittest) runs in `.github/workflows/validator.yml`'s `check`
job on every push and every pull request, and the branch's push-event and
pull-request runs are quoted in [release.md](release.md). No local hook
runs it (`.claude/settings.json` holds only a session-start hook), which is
why every mechanical carrier below is placed inside `make check` rather
than beside it: a check there ran on the branch at every push.

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| Two full-page 2x screenshots, 1.88 MB together — the first binaries this repository tracks — committed at Verify and caught only by Review reading the diff stat | `review.md` §Findings, the one major; `verification.md` §Figure, the dated crop note | mechanical | `gates.py` — a new offline detector (next free letter P per the module docstring) that fails on any file under `docs/` above a byte threshold read from `factory.json` through `factory_config.py`, so it runs in `make check` locally and in `validator.yml`'s `check` job; the push-event run at `1fed0ce` would have gone red before Review opened. Not a CI-only step (would not run locally) and not a `CLAUDE.md` line (the files already slipped past every reader until the diff stat). |
| `lint.py`'s Stages-section comment and two docstrings went on describing a prose paragraph after row 0094 replaced it with a table | `review.md` §Findings, minor (stale rationale); `breakdown.md` §Notes, flagged at Decompose and deferred to Review | judgement | `CLAUDE.md` "Hard conventions" — a line: a work item that reshapes a file another module's docstring describes rewords that docstring in the same item; Decompose saw the staleness and routed it to Review instead of giving row 0094 the sentence. No checker can tell a docstring's prose is stale. |
| The six ledger rows carry `at: 2026-10-08` (UTC, stamped by `budget_guard`) beside `session-2026-10-07-…` run ids (local date, typed by the session) | `review.md` §Repository hygiene; `breakdown.md` §Notes, the owner-session ledger policy | mechanical | `budget_guard.py` `record` — derive a `session-` run id's date from the same UTC clock that stamps `at` instead of taking it from the caller, and let detector G (`check_cost_ledger`, `gates.py`) pin that a `session-YYYY-MM-DD-` run id's date equals its row's `at`. Two clocks for one row is a writer defect, not a reader's. |
| `gh pr merge --delete-branch` could not delete the local branch because it was checked out in `.claude/worktrees/readme-skill-map`; the remote branch was deleted by hand | `autorun-brief.md` §Feedback on hand at Operate, process observations | judgement | `CLAUDE.md` — a line stating the layout and the order: a run's branch lives in `.claude/worktrees/<slug>`, so merge from `main`, `git worktree remove` the run's worktree, then delete the branch. `skills/ship/SKILL.md` step 4 (record each action and its result as it happens) is what caught it and stays as is. |
| The orchestrator's first home-page capture after the merge missed the README: the file list pushed it below an 1800px window, and the frame read as "no figure" | `autorun-brief.md` §Feedback on hand at Operate, home page at full README width | mechanical | `skills/ship/TEMPLATE.md` §Post-release checks — the check names the element to assert, not the page to look at: the figure's `<img>` path in the fetched page HTML and a pixel sample inside the figure (`verification.md`'s own method under §Figure), so a frame without the figure fails instead of passing by silence. |
| The thirty-second test's stand-in reader was a model, and the criterion describes a newcomer | `verification.md` frontmatter assumptions (the second) and §Not verified, "A human reader" | judgement | `skills/prd/SKILL.md` — its rule that a criterion must be checkable by a person or a test gains the half it lacks: a criterion about a human names the reader kind, and a proxy of another kind is labelled as such in `verification.md` (which this run's Verify did, honestly). |
| Two bounded gaps in the new checker, deferred: the `idea.md`, `prd.md` and `review.md` sublabels satisfy the roster line for their own stage; the README-embed check is a substring test | `review.md` §Findings, the second and third minors; `verification.md` §Roster check, the observation for Review | mechanical | `lint.py` `check_readme_figure` itself, with `tests/test_lint.py` `TestReadmeFigure` pinning the new strings: on the next redraw, match a slug against whole-`<text>` content or drop the `.md` sublabels from the join, and match the embed as a markdown image line or an `src=`. A drift detector's gap is closed in the detector. |
| PRD-0008's self-containment check (`grep -E 'http\|<script\|@import\|@font-face'` finds nothing) cannot run literally — every SVG root's `xmlns` names `http://www.w3.org/2000/svg` — and was read by intent at Decompose and Verify | `breakdown.md` §Design gaps and its third assumption; `verification.md` §Figure | judgement | `skills/prd/SKILL.md` — the same checkable-criterion rule, extended: a check line quoted in a criterion is run once against a known-good sample before it is written, so the wording cannot be unrunnable as written. |

Not in the table, on purpose: the harness's permission classifier pausing
`gh pr merge` until the owner answered — that is gate 3 (ADR-0033) doing
its job, not a mistake; and the one test in `TestReadmeFigure` that
shadows a base-class test of the same name — a review nit with two
precedents in the same file and no decision owed.

## Idea seeds

- A mechanical weight guard for additions under `docs/` — an offline
  `gates.py` detector (letter P) with a threshold from `factory.json`,
  inside `make check`, for this repo and every stamped one.
- The lean-and-polish branch absorbs the figure and the table on rebase:
  one `<text>` row each in "Reshaping what's built" and one table row
  each, or lint prints `README.md never names skill 'lean'` and
  `docs/assets/skill-map.svg never names skill 'lean'` (and the pair for
  `polish`) beside the taxonomy and LEDGER lines.
- Close `check_readme_figure`'s two deferred minors on the next redraw:
  whole-`<text>` matching or no `.md` sublabels in the join; an image-line
  or `src=` match for the embed.
- Revisit adoption after a month on the public page — stars, forks,
  watchers, README traffic, any mention of the figure — capture the home
  page in dark as well as light, and run the thirty-second test on a
  human who has not read the repo.
- Plugin-cache lag: installed `0.3.0` copies keep the mermaid until the
  next bump; decide whether a README-visible change warrants a patch
  bump, or say that the install's README may lag the public page.
- The `architecture-diagram` scaffold: root `width`/`height` beside the
  `viewBox`, a 10px floor on the text tiers, a mono list-row tier, and a
  step-2 note for a subject that is a roster map rather than a system.
- One clock for an owner-session ledger row: `budget_guard record`
  derives the `session-` run id's date from the clock that stamps `at`,
  and detector G pins the agreement.
- The worktree merge sequence (merge from `main`, remove the worktree,
  then delete the branch) as a `CLAUDE.md` line or a ship step, so the
  next autorun merge does not stop on `--delete-branch`.
- A PRD check line is run once against a known-good sample before it is
  written, so a criterion cannot be unrunnable as written (PRD-0008's
  `xmlns` grep).
- Post-release page checks name the element to assert — the `<img>` path
  in the fetched HTML and a pixel inside the figure — not a page to
  eyeball.

Each seed above was appended to [docs/backlog.md](../../backlog.md) in the
protocol's grammar with `(from: feature:readme-skill-map)`, in full
wording there; this list is the short form.

## Run complete

Closed 2026-10-08, one day after the squash merge, with outside signal
absent and recorded as absent. The seeds above are the input to the next
Idea-stage run; the first one to come due is the lean-and-polish rebase,
which the roster check is already waiting for.
