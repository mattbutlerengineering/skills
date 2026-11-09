---
stage: operate
run: feature:svg-mechanical-check
date: 2026-11-09
users-observed: 0
signal-source: "Scan of the Owner's agent session transcripts (Claude Code project directories and the omp session directory), 2026-11-05 06:22Z (the merge of #1161) to 2026-11-09T20:42Z, the newest event found: 354 transcript files touched in the window. 29 mention the check; 3 hold a shell command that runs it (5 command lines), and all 3 are this repo's own checkouts (pipeline runs, a retro, maintenance), not an adopter generating a diagram. The 3 files from other projects only mention the name; none shows a run, an error or a complaint. The check logs nothing when it runs, so a use that left no trace here is not counted."
---

# Retro: A mechanical SVG check for the diagram skills

The release is four days old (merged 2026-11-05), so this retro reflects
days of use, not a steady state. The check ships to users of the two
draft diagram skills; the Owner's transcripts show no one generating a
diagram with them outside this repo's own work. The count is 0 and every
outcome below is `unobserved`: state, not use. A scan limit is not a
finding that nobody used it.

## Outcomes vs. intent

### Success in one sentence: on an SVG with a missing root width/height, a duplicate id, a dangling `url(#...)` and an external `href` the check fails and names each; on a clean SVG it passes and reports the smallest text size at embed width

- What happened: the state is shipped on main. `svg_check.py`, its `factory.py` verb, 37 tests and 14 committed fixtures exist; `verification.md` records 16 of 16 PRD criteria passing, the all-four fixture printing one line per defect with exit 1, and the clean fixture printing a pass with `8.3px at 830px embed width`. No generator has been seen running it on a user's diagram.
- Signal strength: unobserved. The verification is the run's own fixtures, not a user's file.

### Step 7 of both diagram skills tells the generator to run it, and the scaffolds pass their own check

- What happened: `verification.md` (PRD 9, 10, 11) records both skills' step 7 text and both boilerplates exiting 0 (`7.5px` and `8.5px` smallest text). The three in-window command runs of the tool are this repo's own work.
- Signal strength: unobserved for users; the scaffolds passing is measured by the run's own commands.

### The check never becomes an attack vector (the Idea's named riskiest piece)

- What happened: a DTD or entity is refused before parsing; two payload fixtures (billion-laughs, external entity) refuse with exit 2 and the test proves the sentinel file is never read. `review.md` ran 20,000 byte-level mutations and found one crash, an unknown `encoding=` (fixed in `3be7ab1`). No hostile file has been seen in use.
- Signal strength: unobserved in use; the fuzz and fixtures are the run's own evidence, not a population.

### Users' defects get caught before shipping (the problem the Idea named)

- What happened: not measurable. Nothing counts how often users of the two skills hit the four defects, and nothing records a defect the check caught for them.
- Signal strength: unobserved.

## Open debt

- #1160 — the run's own feature issue, filed by Ship before the merge and closed by it. Counts toward nothing.
- `review.md` Minors, deferred with reasons and no issue filed: a root with no `xmlns` reads "root element is svg, not svg"; `xml:id` and `aria-labelledby` are unread; file content is echoed verbatim; "no text" prints beside a defect list; a pathological style sheet costs quadratic time; ADR-0062's narrowness against a second tool-running skill.
- `backlog.md`: the text-floor half of the scaffold seed, appended open by this run.

## Run retrospective

- Keep: the Idea's refusal-before-parse spike became the fixtures and the test, so the named riskiest piece was closed first. The reviewer's mutation fuzz found a real crash that Verify's 16 passes could not, and the fix landed with its test before Ship.
- Change: the run asked "does it work on these fixtures" and never "will a user run it". Nothing measures adoption, so Operate has nothing to count; a later run should say in the PRD what trace a use leaves. Ship's release.md also ended with a body that contradicts its own frontmatter (below).
- Stop: nothing identified. No stage was skipped or backfilled.

## Environment

| Mistake | Evidence | Class | Proposed carrier |
|---|---|---|---|
| `release.md` frontmatter reads `outcome: released` with `released-at: 2026-11-05`, while its `## Outcome` body still says "Prepared and stopped — waiting on ... pull request" and "The run stays at Ship". Frontmatter is the truth (the PR merged 2026-11-05T06:22Z); the body went stale after the write-back | `release.md` §Outcome against its frontmatter | mechanical | a `gates.py` detector in the artifact-consistency family (the one that checks `verification.md`'s Summary against its body): flag a `release.md` whose body says prepared while `outcome:` is `released`; already seeded by a sibling retro (polish), so no second seed here |
| The PRD of a run with no tracker mirror failed `gates.py` detector O and needed seven hand-written `coverage-waiver` comments, added at Implement | `breakdown.md` §Notes, 2026-11-04 | mechanical | `gates.py` detector O, which already fired; the exemption for a no-work-order run is already seeded by the `review-interface-pass` retro, so no second seed |
| `tests/test_factory_cli.py` required a `factory.py` verb the architecture did not name; found at Implement | `breakdown.md` §Notes, design gap | mechanical | `tests/test_factory_cli.py`, which caught it; no new check owed |
| An unknown `encoding=` declaration crashed `check()` with a traceback and exit 1, contradicting "never raises on file content" | `review.md` §Major | mechanical | `tests/test_svg_check.py`: the reviewer's 20,000-mutation fuzz found it but was never committed (first seed below) |
| A first batch of edits landed in the main checkout, not the worktree, and was moved by patch | `breakdown.md` §Notes, Edit-tool paths | judgement | none in the repo: it is an editing-tool path resolution, caught only by the implementer reading `git status`; recorded as a finding, no seed |
| The PRD says the check "names only that defect" while the architecture prints a "no text" report line, so Verify had to flag it | `verification.md` §Not verified; `review.md` §Minor | judgement | the PRD criterion text itself; only a reader could see the two specs differ |
| ADR-0062's "deliberately narrow" tool precedent is stretched by a second tool-running skill and `architecture.md` records no ADR | `review.md` §Minor | judgement | `docs/adr/0062` and `docs/standards.json`; an Owner decision, see below |

## Idea seeds

- Keep the reviewer's 20,000-mutation fuzz of svg_check.py as a seeded test so the never-raises contract and the 0/1/2 exit split are held by a deterministic check, not one reviewer's probe (from: feature:svg-mechanical-check)
- Re-scan Owner transcripts two weeks after 2026-11-09 for runs of svg_check.py outside this repo's own work, counting sessions, exit 1 and exit 2 outcomes and any step 7 where the generator skipped the check (from: feature:svg-mechanical-check)
- Extend svg_check.py to count xml:id as an id and to flag an aria-labelledby that names an absent id, with a fixture each, and reword the no-xmlns message so it names the missing namespace (from: feature:svg-mechanical-check)

## Run complete

2026-11-09. The seeds above are the input to the next Idea-stage run.
