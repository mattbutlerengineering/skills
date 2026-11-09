---
stage: architect
run: feature:kb-from-knowledge-work-plugins
date: 2026-11-08
ux: skipped — Skill text and two stdlib CLI tools (kb.py, kb_harvest.py) whose output an agent reads; no user-facing surface.
assumptions:
  - "No live interview: every answer comes from autorun-brief.md. The brief is silent on every carrier and every open question the PRD assigns to Architect, so each call below is the draft-first recommendation, with the rejected alternative recorded under Decisions & alternatives."
  - "Memory file format (this repo documents none; no real memory file was read). Assumed: one Markdown file per entry, flat in the memory directory, opening with a `---` frontmatter block that holds `name`, `description` and a `type` of user, feedback, project or reference, either as a top-level `type:` line or nested under a `metadata:` key. The directory's index file is `MEMORY.md`. The parser fails safe against this assumption: a file with no frontmatter block, no `type`, more than one distinct `type` value, a value outside the four, or bytes that cannot be read is skipped and counted, never listed; `type: user` is excluded and counted, and no text from it is printed."
  - "Repo scope means type feedback, project or reference; user scope means type user. Feedback entries are listed because the PRD's known duplicates and memory-only gotchas are repo lessons whatever their type, and the ingest rubric plus human promotion filter out personal working preferences."
  - "The memory directory is `memory/` inside the main checkout's transcript project directory (the first directory harvest already resolves). Worktree project directories are not searched for memory."
  - "Transcript shape for human turns, beyond what the existing fixtures model: a human text turn is a `type: user` record whose content is a string or a list of text items with no tool_result; harness-injected turns carry `isMeta: true` or begin with a `<tag>`; subagent transcripts are files named `agent-*` or records with `isSidechain: true`; a question-tool answer is the tool_result of an `AskUserQuestion` tool_use. Anything outside this shape yields no human-turn candidate."
  - "Human-turn candidates are on by default, under their own `human_turns` key. Rejected alternative: an opt-in flag. Flagged for the Owner, who decides whether they stay on once the NOT RUN precision count exists (PRD open question)."
  - "Memory is read only on request (`kb.py harvest --memory`). Rejected alternative: on every harvest, which would re-list the same entries on every run, since the harvest watermark is rejected."
  - "Class-page threshold: three or more pages or candidates sharing one cause, the orchestrator's suggestion, adopted. Rejected alternative: two, the repo's rule-graduation count, because two look-alike pages cost one extra index line and folding them loses each one's specifics."
  - "max-age for docs/kb/main-unprotected.md is 30d: the page's claim was checked by hand on 2026-10-10 and again on 2026-11-08 (the brief), about monthly. Its `checked:` is the date Implement re-runs the page's two gh api commands, or 2026-11-08, the date the brief records the claim holding, if Implement cannot run them."
  - "Memory-to-page pairing uses file-name tokens only, at two or more shared tokens. A pairing is a hint: an unpaired memory that duplicates a page under another name is still caught by ingest's existing dedupe step."
  - "ADR written unattended, so ADR-0125 is provisional, and ADR-0078's status line and index row say it is amended."
  - "Re-run of Architect, unattended, 2026-11-08, to resolve Implement's K12 stop (breakdown.md Notes): `kb_harvest._block` defined the frontmatter fence a second time, failing ADR-0118's one-owner pin (`tests.test_protocol_frontmatter.TestOneFenceDefinition.test_the_exact_count_map`), because this file had said `kb_harvest.py` imports nothing beyond `cli`. Resolved by Implement's recommended option (a), the draft-first call: `kb_harvest.py` imports `protocol` and calls `frontmatter_end`, recorded by provisional ADR-0126, which adds the pair (kb_harvest, protocol) to ADR-0091's pinned set. Option (b), kb.py parsing memory frontmatter, is logged under Decisions & alternatives. Only the Candidate miner's collaborators, the memory interfaces, Stack & dependencies, Decisions & alternatives and ADRs changed; no requirement or other design moved."
---

# Architecture: Teach the knowledge base what it cannot see yet

## Approach

Each of the eight items gets the cheapest carrier that meets its PRD
criteria. Three items change tool behaviour, because a person cannot
see what they describe without a tool: lint ages a page's declared
outside check (item 1, `kb.py`), and harvest lists human turns and
memory entries as two new candidate kinds (items 3 and 2, both in
`kb_harvest.py`). Item 8 is a field of item 1's declaration, so it rides
the same frontmatter change. Items 4, 5, 6 and 7 are writing and
interviewing guidance with no mechanical test that would not misfire,
so they are skill and rubric text, pinned by text assertions. Every new
candidate goes through ingest's unchanged verbs and human promotion;
every new page element is optional, so the six current pages lint as
before. The other shape compared was a tool-heavy one: lint checks for
symptom-first summaries and wrong/right pairs, a new `kb_memory.py`
module, and a "shared cause" detector for class pages. It loses because
none of those checks can tell a gotcha page or a shared cause from text
without misfiring, the PRD forbids new lint failures for items 5 and 7,
and a new module adds a dual-membership pair (below) for one caller.

## Components

### Page contract and lint — `kb.py`

- Responsibility: owns the page format and every lint problem about a
  page. Gains three optional frontmatter fields (`checked-against`,
  `checked`, `max-age`) and the offline age check over them (ADR-0125).
  Owns the `docs/kb/` layout and hands it to harvest.
- Collaborators: `protocol.parse_frontmatter` (existing),
  `kb_harvest.main` (passes `KB_DIR`), the injected git runner
  (existing, staleness only; the age check never touches it).

### Candidate miner — `kb_harvest.py`

- Responsibility: the deterministic half of harvest. Keeps its two
  transcript kinds (`arcs`, `recurring_errors`) byte-for-byte, and adds
  two sources: human turns from top-level transcripts (always), and
  auto-memory entries paired with pages (on `--memory`). Read-only.
- Collaborators: `cli.read_file` and `cli.json_lines` (existing
  imports), `protocol.frontmatter_end` (new import, ADR-0126: the one
  owner of where a memory file's frontmatter block ends, per ADR-0118;
  it adds the pinned root-only to mirrored pair `kb_harvest` to
  `protocol`), the page slugs under the `kb_dir` that `kb.py` passes.

### Skill body — `skills/knowledge-base/SKILL.md`

- Responsibility: the agent's process. Setup gains the tribal-knowledge
  question (item 6) and the flow table a row to run it on its own; step
  2a names the two new candidate kinds and `--memory` without a harness
  path (items 2, 3); step 3 handles the age and malformed-declaration
  problems and names a class page as an over-budget remedy (items 1, 4);
  "The tool" lists `--memory`; one paragraph credits
  anthropics/knowledge-work-plugins. The frontmatter `description` is
  not touched.
- Collaborators: `kb.py` (runs it), `references/ingest.md`,
  `references/page-rubric.md`.

### Page rubric — `references/page-rubric.md`

- Responsibility: what a page may hold and how it is shaped. Gains the
  three optional fields and when to declare them (items 1, 8), class
  pages under Admit (item 4), the symptom-first rule for a gotcha
  summary inside the 200-byte cap (item 5), and one optional wrong/right
  pair under Shape (item 7). "Exactly these fields" becomes "these four
  fields, plus three optional ones".

### Ingest rules — `references/ingest.md`

- Responsibility: turning a candidate into proposals. The harvest
  section gains how to judge a human-turn candidate, a memory candidate
  (paired: NOOP, CONFLICT or UPDATE; unpaired: ADD or NOOP) and a setup
  answer, all through the unchanged verb table and human promotion; a
  "One rule over many instances" paragraph beside "Related is not the
  same" (item 4); and the rule that harvest-sourced items name their
  kind so the Promoter can decline a kind wholesale (user story 7).

### First user — `docs/kb/main-unprotected.md`

- Responsibility: item 1's first real page. Declares
  `checked-against`, `checked` and `max-age: 30d`; keeps its two `gh
  api` commands as how to re-check; loses the "Re-check … nothing in
  the repo records the setting" paragraph. Summary, sources, verified
  and related are unchanged, so the index block is unchanged.

### Tests

- `tests/test_kb.py`: age flagged and not flagged around the boundary,
  each malformed declaration, offline proof, and fixture pages for items
  4, 5, 7 and 8 linting clean both ways.
- `tests/test_kb_harvest.py`: human turns (correction, text answer,
  question-tool answer, approvals and instructions not listed,
  autonomous and subagent transcripts yield none) and memory (three
  pairs, one unpaired, user scope and the index file absent from output,
  each skip reason counted, read-only), all over fixture trees under a
  temporary projects directory.
- New `tests/test_knowledge_base_shape.py`: text assertions over the
  shipped skill, rubric and ingest files for items 4 to 8, the credit,
  the ingest routing, and harness neutrality (the `polish` shape-test
  pattern).

## Data model

Two shapes change: page frontmatter, and harvest's JSON output. Access
patterns: lint reads every page's frontmatter once per run; harvest
reads transcripts once and, on request, every memory file once, and
prints one JSON object an agent reads. Nothing is stored; no
consistency question arises beyond "harvest writes nothing".

### Page frontmatter (owned by `kb.py`, ADR-0125)

```
---
summary: <unchanged, the one owner of the index line>
sources: <unchanged>
verified: <unchanged>
related: <unchanged>
checked-against: <free text: what the claims were checked against, and what they were not>   # optional
checked: YYYY-MM-DD   # optional; pairs with max-age
max-age: <N>d         # optional; N >= 1; pairs with checked
---
```

Invariants, owned by `kb.py`'s age check:

- `checked` and `max-age` appear together, and either one requires a
  non-empty `checked-against`.
- `checked-against` alone is valid and never ages (item 8 on a
  repo-only claim).
- A page is past its age when today is after `checked` + N days; on the
  due date itself it is still fresh.
- No default age. The rendered index line never includes any of the
  three fields.

### Harvest output (owned by `kb_harvest.py`)

```
{
  "scanned": {"transcripts", "skipped_lines", "dirs"},     # unchanged
  "arcs": [...],                                           # unchanged
  "recurring_errors": [...],                               # unchanged
  "human_turns": [                                         # new, always present
    {"kind": "correction" | "answer",
     "signal": "correction-wording" | "after-agent-question" | "question-tool",
     "human": "<excerpt, <= 160 chars>",
     "agent": "<excerpt of the agent turn it follows, <= 160 chars>",
     "session": "<session id>", "at": "<timestamp>"}],
  "memory": {                                              # new, only with --memory
    "dir": "<memory directory>",
    "listed": N, "user_scoped": N, "skipped": N,
    "candidates": [
      {"file": "<file name>", "name": "<name, or the stem>",
       "type": "feedback" | "project" | "reference",
       "description": "<excerpt, <= 160 chars>",
       "page": "docs/kb/<slug>.md" | null,
       "shared": ["<token>", ...]}]}
}
```

Rules, owned by `kb_harvest.py`:

- **Human turns.** Mined only from top-level transcripts (file name not
  `agent-*`, record not `isSidechain`). A human turn counts only when an
  agent turn precedes it in the session, and the agent turn it follows
  is consumed, so two human turns in a row yield at most one candidate.
  Skipped outright: `isMeta` records, text opening with `<`, and the
  existing `NOT_ERRORS` prefixes (rejections, interrupts). A turn is a
  **correction** when its opening words match the `CORRECTION` pattern
  (no, nope, don't, do not, stop, wait, actually, wrong, that's
  not/wrong, not that, instead, undo, revert, why did you, you
  should/shouldn't/didn't/forgot, never, double-check). Otherwise it is
  an **answer** when the agent turn it follows is text whose last
  non-empty line ends with `?` and the human turn, lowercased and
  stripped of punctuation, is not in `APPROVALS` (yes, y, ok, okay, go
  ahead, sure, do it, continue, proceed, lgtm, sounds good, yep, please
  do). A non-error tool_result of an `AskUserQuestion` tool_use is an
  **answer** with signal `question-tool`. The `agent` excerpt is the
  agent text's last non-empty line, or `<tool>: <check_key(command) or
  edited path>` for a tool action.
- **Memory.** Every regular `*.md` directly in the memory directory
  except `MEMORY.md`. The type is read by `memory_type`: every `type:`
  value at any indentation inside the frontmatter block; exactly one
  distinct value among feedback, project, reference is listed; `user` is
  counted under `user_scoped` and nothing else about it is kept; anything
  else (no block, no type, conflicting types, an unknown value, an
  unreadable file) is counted under `skipped`. `listed + user_scoped +
  skipped` equals the files examined.
- **Pairing.** Tokens of a file stem or page slug: split on
  non-alphanumerics, lowercased, stopwords dropped (a, an, and, the, of,
  to, in, on, for, is, by, with, no, not, only), one trailing `s` cut
  from a token longer than three characters. A memory file pairs with
  the page sharing the most tokens, when that is at least `PAIR_MIN = 2`;
  ties go to the first slug in sorted order. Below that, `page` is null
  and `shared` is empty. Worked over the PRD's fixtures:
  `cross-pr-hazard-pairwise-merge-test` shares cross, pr, merge, hazard
  with `cross-pr-merge-hazards`; `manifest-regen-stray-patch-files`
  shares manifest, regen with `manifest-regen`;
  `pr-body-no-work-order-waiver` shares pr, body with
  `pr-body-contract`; `gh-pr-edit-broken-use-rest` shares only pr with
  any page, so it is unpaired.

## Interfaces & contracts

### `kb.lint(root, git=_git, today=None)`

- Input: repo root; the git runner (existing); `today` as a
  `datetime.date`, defaulting to the local date when None.
- Output: the existing problem strings, plus per page with frontmatter
  the strings of `age_problems`. Order: field problems, then link and
  age problems per page, then index, then staleness (as today).
- Failure modes: unchanged for git. The age check cannot fail on the
  environment, because it reads only the parsed fields and `today`.

### `kb.age_problems(page, today)`

- Input: one page dict as `pages()` yields it (fields not None); a date.
- Output: a list of `kb:`-prefixed strings, empty when the page declares
  none of the three fields or a fresh check. Exact forms:
  - `kb: <path> declares an outside check but is missing field '<field>'`
    (one per missing field of the three, when `checked` or `max-age` is
    present)
  - `kb: <path> has an empty 'checked-against'`
  - `kb: <path> checked '<value>' is not a YYYY-MM-DD date`
  - `kb: <path> checked <date> is after today (<today>)`
  - `kb: <path> max-age '<value>' is not a whole number of days like 30d`
  - `kb: <path> is past its declared age: checked <date>, max-age <N>d, due <due> — re-check it`
- Failure modes: none raised. A malformed value is a problem string,
  never treated as fresh. It runs no command and opens no connection;
  a test calls it with `cli.runner` and `socket.socket` patched to fail
  on any call.

### `kb.main(argv)`

- `harvest` now dispatches `kb_harvest.main(argv[1:], KB_DIR)`, so the
  page layout keeps one owner. Usage text gains `[--memory]`.

### `kb_harvest.harvest(root, projects=None, days=None, session=None, now=None, memory=False, kb_dir=None)`

- Input: as today, plus `memory` (read the memory source) and `kb_dir`
  (the page directory relative to root; pairing reads slugs under it).
- Output: `(result, problems)` with the data model above. `human_turns`
  is always present (empty when none); `memory` appears only when
  `memory` is true; `scanned.dirs` unchanged.
- Failure modes: existing problems unchanged. With `memory` true and no
  directory at `<first project dir>/memory`: one problem,
  `harvest: no memory directory at <path>`, and, as with every harvest
  problem, no JSON is printed. A missing or empty `kb_dir` is not a
  problem: every memory candidate is unpaired. A memory file that cannot
  be read or parsed is counted, never a problem and never listed.
  Nothing is written anywhere.

### `kb_harvest.human_turns(records)`, `kb_harvest.memory_type(text)`, `kb_harvest.pair(stem, slugs)`, `kb_harvest.memory_candidates(memory_dir, slugs)`

- `human_turns`: records of one top-level transcript → candidate list.
  `mine(paths)` calls it for each path not named `agent-*` and adds
  `human_turns` to its result; `arcs` and `recurring_errors` are
  computed exactly as now.
- `memory_type`: file text → one of the three listed types, `"user"`, or
  None (skip). The frontmatter block is the lines `protocol.frontmatter_end(
  text.splitlines())` bounds (ADR-0118, ADR-0126); None from it means no
  block, a skip. `kb_harvest.py` defines no fence of its own, and
  `memory_candidates` reads `name` and `description` from the same block.
- `pair`: a stem and the page slugs → `(slug or None, shared tokens)`.
- `memory_candidates`: directory and slugs → the `memory` object above.

### `kb.py harvest [root] [--days N] [--session ID] [--projects-dir DIR] [--memory]`

- `--memory` takes no value. Every other flag and the exit codes are
  unchanged (0 JSON, 1 problems, 2 usage).

### Skill text contracts (pinned by `tests/test_knowledge_base_shape.py`)

- Setup (item 6): after finding record-of-pain candidates, the Setup
  agent asks the human, one question per turn and at most three, "What
  mistake do people new to this repo make that the code would not warn
  them about?", each with a recommendation drawn from the strongest
  candidate it already found (its one line and source). Answers are
  candidates under the same propose-and-promote rule and inside the
  same five-page cap; nothing is written unpromoted. With no human
  present the step is skipped and the skip is said. A repo that already
  has `docs/kb/` runs the same step through a flow-table row, its
  answers going through step 2.
- Ingest (items 2, 3, 6): a candidate is a lead, never a claim; the
  lesson is re-derived from the repo and cites a repo path, never a
  memory file or a transcript; a setup answer with no repo file to cite
  becomes a proposed always-loaded guardrail or a NOOP; memory text and
  human words are restated, never pasted; a user-scoped or personal fact
  is never proposed.
- Rubric (items 1, 4, 5, 7, 8): the three fields and when to declare
  them; a class page states one rule, lists its instances, and cites
  each instance's source, proposed when three or more pages or
  candidates share one cause; a gotcha summary leads with the symptom
  (error text or wrong result), then cause and fix, inside the 200-byte
  cap; a gotcha page may carry one `Wrong:` / `Right:` pair.
- Neutrality: no file under `skills/knowledge-base/` contains `~/.claude`,
  `.claude/projects`, `CLAUDE_CONFIG_DIR`, `MEMORY.md` or a
  `/memory/` path segment. Harvest's memory source is described as "the
  harness's auto-memory for this repo, where the harness keeps one".
- Credit: SKILL.md credits anthropics/knowledge-work-plugins
  (Apache-2.0) for the practices behind items 1 to 8, restated in this
  repo's words and not copied, as `polish` and `ux-patterns` credit
  Impeccable. `kb_harvest.py`'s docstring carries the same one-line
  credit for the two new sources.

### Accepted behaviour changes

- A page that declares `checked` and `max-age` can go from clean to
  failing lint with no commit, once its due date passes. Pages without
  the fields lint identically.
- Harvest output always carries a `human_turns` key (possibly empty).
  Over the existing fixtures `arcs`, `recurring_errors` and `scanned`
  are unchanged; only the new key is added.
- The rubric no longer says a page opens with exactly four fields.

## Stack & dependencies

- Python 3 standard library only (`datetime`, `re`, `pathlib`), no new
  dependency — standard `stdlib-only`.
- No new module. `kb.py` keeps `cli`, `protocol` and `knowledge_plane`.
  `kb_harvest.py` keeps `cli` and gains one import, `protocol`, to call
  `frontmatter_end` (ADR-0126). That adds the pair `kb_harvest` to
  `protocol` to the dual-membership pin in
  `tests/test_dual_membership.py` (ADR-0091): its `protocol.py` row gains
  `kb_harvest`, 61 pairs to 62. `protocol` imports no caller, so no
  cycle; `kb_harvest` is not mirrored, so no payload change.
- `LEDGER.md` is untouched: the knowledge-base row stays at draft,
  and the knowledge-base skill's frontmatter `description` is not
  edited, so no routing eval is owed.
- Neither `kb.py` nor `kb_harvest.py` is in `factory_init.MIRRORS`
  (ADR-0078 decision 7), so no payload mirror changes and no manifest
  regeneration is owed. The npx bundle carries every root `*.py`
  already.

## Decisions & alternatives

- **Item 1 carrier: optional frontmatter fields that lint ages offline**
  (ADR-0125) over running the page's check from lint (network and
  credentials in an offline tool; ruled out by the Owner) and over a
  default age for every page (a policy number with no evidence, failing
  pages git already watches).
- **A page with an outside source but no age gets no default and no
  problem**: `checked-against` alone records where a claim was verified
  and never ages; the rubric tells an external-fact writer to declare
  all three. Over a default age (as above) and over a required age
  (impossible to tell an outside-source page from an environment note
  when one field serves both).
- **Item 8 is the same `checked-against` field as item 1's outside
  source, one declaration, read by lint only for emptiness** (ADR-0125),
  over a separate `verified-against` field (two owners of "what was this
  checked against") and over body text (lint could not see a page's
  first-user declaration).
- **`max-age` written `<N>d`** over a bare integer (unit ambiguous) and
  over a single `recheck-by:` date (the PRD's criterion is date plus
  age, and the age is the part a writer reasons about).
- **The index line stays the summary alone**: the age is never rendered
  and a symptom-first summary fits the existing 200-byte cap. Over
  appending a due date to index lines (bytes paid on every turn by every
  page, for a fact lint already reports).
- **Item 2 carrier: harvest reads memory, in `kb_harvest.py`, on
  `--memory`** over a new `kb_memory.py` (one caller, and a new root-only
  importer of `cli` adds a dual-membership pair that ADR-0091's pin
  records by ADR; it would have needed `protocol` too, so two pairs and a
  module against `kb_harvest`'s one pair) and over reading memory on
  every harvest (re-lists the same entries each run, with the watermark
  rejected).
- **A memory file's frontmatter block is found by
  `protocol.frontmatter_end`, which `kb_harvest.py` imports** (ADR-0126;
  added on the Architect re-run that resolved Implement's K12 stop), over
  `kb.py` parsing each memory file and passing the fields or a parser in
  (the page-contract owner would read harness memory files, the
  `memory_type(text)` and `memory_candidates` interfaces would change,
  and `protocol.parse_frontmatter` keeps only the last value of a
  repeated key, so a file with `type: user` and a nested `type: project`
  would read as `project` and `kb_harvest` would still scan the block's
  lines for the fail-safe distinct-type rule) and over a disguised copy
  of the fence literal (it hides a second fence rule from ADR-0118's
  detector without removing it). The cost is one pinned pair, as
  `launch_demo` (ADR-0118) and `assembly_line` (ADR-0124) paid.
- **The memory directory is found beside the transcripts it already
  resolves, with `--projects-dir` as the test seam**, over a
  `--memory-dir DIR` flag (a second path flag for a location the tool
  already derives; no other harness has auto-memory for it to point at).
- **User scope read from the entry's own `type`, failing safe** (skip and
  count anything untyped, conflicting or unreadable) over reading the
  memory index file (it is excluded by the PRD, and a one-line hook says
  nothing reliable about scope) and over listing everything for the
  agent to filter (a personal fact would reach the output).
- **Pairing by file-name tokens, at least two shared** over pairing by
  description or summary text (more words, more false pairs, and a
  heuristic only a fixture could confirm) and over cited sources (memory
  files cite none). A miss is cheap: ingest's dedupe step still greps.
- **Item 3 signals: position after an agent turn, plus opening wording
  for a correction, plus a trailing question mark or the question tool
  for an answer**, over a following-edit signal (needs a second pass and
  a window size with nothing to calibrate it) and over any wording-only
  rule (every instruction would read as a correction).
- **Human turns on by default, under their own key**, over an opt-in
  flag: the Promoter skips the kind wholesale (user story 7), autonomous
  transcripts yield none, and the Owner's precision count decides
  whether they stay on. Flagged in the run's report.
- **Item 4 carrier: rubric and ingest text, threshold three**, over a
  tool that notices a shared cause (no offline signal for "same cause"
  that would not misfire) and over a threshold of two (see
  assumptions).
- **Items 5 and 7 carrier: rubric text alone** over lint checks (lint
  cannot tell a gotcha page or a symptom from text, and the PRD forbids
  new failures on existing summaries and pages).
- **Item 6: a setup step plus a flow-table row to run it alone**, with
  the recommendation drawn from the strongest record-of-pain candidate,
  over a new flow of its own (it is ingest with a human as the source)
  and over an unrecommended open question (the Owner's stated style is
  one question at a time with a recommendation).
- **Credit as one paragraph in SKILL.md plus a docstring line**, over a
  credit in harvest's JSON output (output an agent reads, not a place a
  reader looks for provenance).
- **Text assertions in a new `tests/test_knowledge_base_shape.py`** over
  adding them to `tests/test_kb.py` (that module tests the tool; shape
  tests for skills live in their own modules, as `polish`'s do).

## ADRs

- [ADR-0125](../../adr/0125-a-kb-page-declares-its-outside-check-and-lint-ages-it-offline.md)
  — A knowledge-base page declares its outside check, and lint ages it
  offline (provisional; amends ADR-0078 decisions 2 and 6).
- [ADR-0126](../../adr/0126-kb-harvest-reads-memory-frontmatter-through-protocol-and-joins-its-root-only-importers.md)
  — `kb_harvest` reads a memory file's frontmatter through
  `protocol.frontmatter_end` and joins the root-only importers of
  `protocol.py` (provisional; written on the Architect re-run for K12).
