---
stage: architect
run: feature:pocock-1-3-takeaways
date: 2026-10-06
ux: skipped — no UI surface; deliverables are skill and protocol text plus a lint rule
assumptions:
  - "The skill's trade-off read-out (step 6) was not held live; the decisions that could have gone another way are recorded under Decisions & alternatives with the option that lost, per the autorun brief."
  - "The lint rule's exact problem strings are this stage's wording: the brief asked for an exact string asserted through the public function but supplied no words, so they follow the sibling strings already in skill_frontmatter_problems."
  - "The protocol section is titled 'Pull request body' and sits after 'Artifact frontmatter', before 'Harness neutrality'; the brief named its content, not its heading or position."
  - "The hand-off decision is adopt-with-neutral-wording: omp's docs/skills.md settled that omp has no skill tool, which rules out the literal borrowing but not the lesson; the neutral sentence is this stage's wording."
  - "The retro Environment table sits between Run retrospective and Idea seeds with the brief's four columns; its position and the new step's number (operate step 6, later steps renumbered) are this stage's choice."
---

# Architecture: Pocock 1.3 takeaways

## Approach

Five independent borrowings from mattpocock/skills v1.3.0 and v1.3.1 land
as edits to text that already exists, plus one rule in the seam that
already owns skill-frontmatter facts. The shape is "one owner per fact,
everyone else points": the description contract lives in
`protocol.skill_frontmatter_problems` (ADR-0052) and lint and the
trigger-eval loader stay thin callers; the pull-request-body shape lives in
one protocol section and the three places that write bodies cite it; the
environment retrospective is produced by operate and read by automate
through one named template section; the hand-off decision is recorded once
in the protocol and `next` is worded to match. No new module, no new skill,
nothing runs in a target repo that did not run before. The alternative
shape, a dedicated checker in `lint.py` plus `pr` and `retro` skills of our
own, loses: it gives frontmatter facts a second owner (the divergence
ADR-0052 was written to end) and adds two skills PRD-0007 puts out of scope.

```tree-claims
# The files this design edits, as they stand in this worktree on 2026-10-06.
exists: protocol.py
exists: lint.py
exists: trigger_eval.py
exists: factory/templates/tools/factory/protocol.py
exists: factory/manifest.json
exists: tests/test_protocol_frontmatter.py
exists: tests/test_factory_init.py
exists: docs/pipeline-protocol.md
exists: docs/factory/improvement-routine.md
exists: skills/next/SKILL.md
exists: skills/work-queue/SKILL.md
exists: skills/ship/SKILL.md
exists: skills/ship/TEMPLATE.md
exists: skills/operate/SKILL.md
exists: skills/operate/TEMPLATE.md
exists: skills/automate/SKILL.md
exists: skills/audit/SKILL.md
exists: skills/deepen/SKILL.md
exists: .claude-plugin/plugin.json
```

## Components

### Description contract (`protocol.py`)

- Responsibility: the one statement of what a skill `description:` may be:
  present, within Pi's 1024 chars (today), and a bare YAML scalar (added),
  meaning the value `read_frontmatter`'s plain `key: value` splitter hands
  back is the value a strict YAML loader would. Three substring tests, no
  YAML parser. The six descriptions (audit, automate, deepen, doctor,
  pipeline-board, work-queue) each lose their single `: `, every site a
  colon joining two clauses that a semicolon or full stop replaces without
  touching a trigger phrase; they land before the rule so each commit is
  green and the trigger-eval loader never refuses a skill.
- Collaborators: `lint.check_skills` and `trigger_eval`'s loader call the
  function unchanged. `tests/test_protocol_frontmatter.py` pins the strings.
  `factory/templates/tools/factory/protocol.py` is the identity mirror
  (`factory_init.MIRRORS`), so `python3 factory_init.py update-manifest`
  follows the edit and `factory/manifest.json` ships with it (detector E;
  `tests/test_factory_init.py` pins payload to root). `evals/routing.json`
  is not edited and the eval is not re-run; PRD-0007 accepts that exposure.

### Pull request body (`docs/pipeline-protocol.md`)

- Responsibility: owner of what a pull request body says about its merge:
  the smallest visual that shows the change (pseudocode, call tree, file
  tree, diagram or diff), before-and-after evidence, and a merge-danger
  call under one fixed heading, `## Merge danger`, naming one-way or
  two-way door and blast radius. Detector B's lines stay, and the section
  says so: `Closes #N`, and a work-order id or the `No work order:` waiver. Credits
  mattpocock/skills `pr` and Dex Horthy's `show-me` (Humanlayer);
  structure restated, no text copied.
- Collaborators: three writers point at the section by name and restate
  nothing: the work-queue step 4 worker brief (a new numbered item), ship
  step 3 and `skills/ship/TEMPLATE.md` (door and blast radius beside the
  rollback steps, so `release.md` and the PR body agree), and the
  improvement routine's §5 skeleton (`## Merge danger` after
  `## Verification`, first two lines untouched).

### Environment retrospective (`skills/operate` producing, `skills/automate` reading)

- Responsibility: operate gains step 6, "Retrospect on the environment",
  after step 5 "Retrospect on the run itself"; steps 6 and 7 become 7 and
  8. From the run's own record of its mistakes (`verification.md`
  failures, `review.md` findings, `breakdown.md` Notes) it names per
  mistake the check, pointer or rule that would have caught it, classifies
  it mechanical (a deterministic check: lint rule, hook, CI job, gate
  detector) or judgement (a CLAUDE.md line or a standards statement), and
  proposes the carrier. `skills/operate/TEMPLATE.md` gains an
  `## Environment` table. Operate's `description:` stays byte-identical.
- Collaborators: automate step 1's surface table gains a row reading the
  `## Environment` section of every `docs/**/retro.md`; its step 2 already
  counts "a retro naming a thing that dragged" as the strongest friction
  source, so the row is the only edit. The recital checker parses `N. `
  steps for the soft-gate and artifact filenames, which renumbering keeps.

### Router hand-off (`skills/next` step 5, protocol Harness neutrality)

- Responsibility: step 5's lead sentence tells the agent to load the stage
  skill through the harness's skill-loading mechanism instead of naming it
  in prose (wording under Interfaces); the eleven list lines keep their
  exact `- <stage> → the `<stage>` skill` shape. The protocol's Harness
  neutrality section records the decision and what was checked.
- Collaborators: `lint.check_router`'s `HANDOFF_LINE` regex reads the list
  lines for membership and order; `evals/routing.json` is untouched.

### Small borrowings and packaging

- Responsibility: `skills/audit/SKILL.md` line 30, `skills/deepen/SKILL.md`
  line 29 and automate's surface table name `GLOSSARY.md` beside
  `CONTEXT.md` where they read a target repo's vocabulary; this repo's own
  file stays `CONTEXT.md`. The work-queue step 4 brief gains two worker
  rules: confirm the branch base is the default-branch tip before writing;
  merge or rebase that tip before declaring done. `.claude-plugin/
  plugin.json` `version` (0.2.0 here) is bumped at Ship, which records
  0.3.0 or 0.3.1 by whether the lean/polish branch (0.3.0, uncommitted)
  lands first; `update-manifest` reads plugin.json, so bump and manifest
  are one step, and whichever of the four branches touching
  `factory/manifest.json` lands last regenerates it under detector E.
- Collaborators: `lint.check_manifest` requires the version field.

## Data model

Three text shapes, chosen from who reads them:

1. **Skill description scalar.** Read by lint on every check, by the
   trigger-eval loader on demand, and by two harness loaders each session.
   Invariant, owned by `protocol.py`: plain-split value equals strict-YAML
   value, enforced as three substring tests on the parsed value.
2. **Pull request body.** Read once by the merge reviewer at gate 2
   (ADR-0033) and by detector B in CI. Free-form visual and evidence, then
   `## Merge danger` carrying `Door:` (one-way or two-way) and
   `Blast radius:` (what breaks if the call is wrong). The heading is fixed
   so a reviewer finds it; the rest is prose.
3. **Retro Environment row.** `| Mistake | Evidence | Class | Proposed
   carrier |`. Evidence cites the artifact and heading or line; Class is
   `mechanical` or `judgement`; Carrier names an existing thing (a lint
   checker, a gates detector, a hook, a CI job, a CLAUDE.md line, a
   `docs/standards.json` statement). Read by automate by locating
   `## Environment` under `docs/**/retro.md`. The eight existing retro.md
   files predate the section and are not edited; a retro without it reads
   as no environment findings, not as a defect.

Every shape is a file in one tree; consistency is immediate, and the design
has no cross-process or network seam.

## Interfaces & contracts

### `protocol.skill_frontmatter_problems(root, slug)`, extended

- Input: plugin root and skill slug, as today.
- Output: the existing strings, plus, when a description is present, zero
  or more of these in this fixed order, with `<slug>` substituted:
  - `skills/<slug>/SKILL.md description is not a bare YAML scalar: contains ': '`
  - `skills/<slug>/SKILL.md description is not a bare YAML scalar: contains ' #'`
  - `skills/<slug>/SKILL.md description is not a bare YAML scalar: starts with <c>`
    where `<c>` is the description's first character rendered with Python's
    `!r` (so `'"'`, `"'"`, `'['`, `'&'`, `'*'`, `'|'`, `'>'`), fired when that
    character is in the YAML 1.2 indicator set `-?:,[]{}#&*!|>'"%@` plus
    the backtick, held as a private constant beside
    `SKILL_DESCRIPTION_LIMIT`.
- Failure modes: never raises. A missing file, block or description returns
  its existing string and skips the new checks. Two defects yield two
  strings, the convention the sibling name-and-description test fixes.
  `lint.py` prints them verbatim; the trigger-eval loader raises them
  joined, so an offending description refuses to eval.
- Test contract (`tests/test_protocol_frontmatter.py`,
  `TestSkillFrontmatterProblems`, via its `seed` helper): one fixture per
  shape asserting the exact string; one carrying both `: ` and ` #`
  asserting both in order; a quoted description asserting the starts-with
  string; the existing conformant fixture stays green. Written first, run
  red, then green.

### Protocol section to its three pointers

- Input: none; prose read by the worker, the ship agent and the routine.
- Output: a body with the three parts, the `## Merge danger` heading and
  detector B's lines.
- Failure modes: a body missing the section is a gate-2 reading finding,
  not a CI failure; detector B is unchanged, so no existing PR goes red.

### Operate to automate

- Input (operate step 6): the run's `verification.md`, `review.md` and
  `breakdown.md` Notes. Output: `## Environment` rows in `retro.md`.
- Input (automate step 1): those rows across `docs/**/retro.md`.
- Failure modes: no section, no evidence, no finding. A `mechanical` row
  maps to automate's hooks and drift-detector categories; a `judgement`
  row to its "rules stated and unenforced" source.

### `next` step 5 hand-off

- Input: the orientation result, a stage slug. Output: the stage skill
  loaded and followed. Lead sentence: "Load the matching stage skill
  through the harness's skill-loading mechanism (a skill tool where one
  exists, otherwise a read of the skill file) and follow it; naming the
  skill in prose does not load it." The list lines below it are unchanged.
- Failure modes: a harness with neither mechanism reads
  `skills/<stage>/SKILL.md` directly, which the sentence already names.

## Stack & dependencies

- Python 3 standard library, `str` methods only, no YAML parser
  (`stdlib-only`): three substring tests are less interface than a scanner.
- Markdown prose for every other deliverable; no new tooling.
- omp's `docs/skills.md`, read once via `gh api` (read-only), as the
  research source for the hand-off decision.

## Decisions & alternatives

- **Rule in `protocol.skill_frontmatter_problems`** over a new `lint.py`
  checker: protocol.py owns frontmatter facts and both callers inherit the
  rule for free (ADR-0052; `stdlib-only`).
- **Reject quoted descriptions** over teaching `read_frontmatter` to strip
  quotes: the reader stays a plain splitter and every description is one
  bare scalar; a quote-stripping reader is a second parser rule every
  caller must know, to admit one more shape.
- **Substring tests** over a YAML scanner: three shapes, three lines.
- **One string per shape** over one generic string: the fix differs per
  shape and the string names it, as the sibling strings already do.
- **Trailing colon and `|` block scalars not special-cased**: no
  description ends in a colon or uses a block scalar. A block body holding
  `: ` would be flagged although strict YAML accepts it; telling it apart
  means re-reading the raw line the reader consumed. One clause each if
  either ever occurs.
- **Protocol section as owner** over restating the shape in work-queue,
  ship and the routine: three copies drift; one owner and pointers is the
  pattern the seed-backlog and tracker-mirror sections set.
- **`## Merge danger` as the one fixed heading** over fully free-form: the
  reviewer must find the door call; the visual and evidence vary by change.
- **Hand-off: adopt with neutral wording** over Pocock's literal "Call the
  Skill tool with X" and over leaving prose as is. omp's `docs/skills.md`
  settles it: skills are "exposed to the model as ... on-demand content via
  the `read` tool against `skill://...`", and its "Skills vs custom tools"
  section separates "documentation/workflow content loaded through prompt
  context and `read`" from "executable tool APIs callable by the model".
  omp has no skill tool, so the literal wording fails one of the two
  harnesses (ADR-0027); the lesson (name the mechanism, not just the skill)
  survives as the neutral sentence above, recorded in the protocol's
  Harness neutrality section, which already names both harnesses. This
  applies ADR-0027's pattern for neutral touchpoints rather than amending
  it, so no ADR.
- **Wording in step 5's lead sentence** over rewording each list line:
  `HANDOFF_LINE` pins the list's shape for membership and order.
- **Environment retro as an operate step** over a `retro` skill of our own:
  operate owns `retro.md`; PRD-0007 excludes new skills.
- **A table** over prose for the Environment section: automate reads it by
  heading and row, and the class column is what routes the carrier.
- **Name both glossary files** over renaming this repo's `CONTEXT.md`: the
  borrowing is about reading target repos on either convention.
- **Version decided at Ship** over fixing it here: the number depends on
  merge order the design cannot know.

## ADRs

None — no decision met the ADR bar. The hand-off decision applies
ADR-0027 rather than amending it and is recorded in
`docs/pipeline-protocol.md`'s Harness neutrality section.
