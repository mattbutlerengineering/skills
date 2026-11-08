---
stage: prd
run: feature:kb-from-knowledge-work-plugins
id: PRD-0022
date: 2026-11-08
ux: not-applicable
ux-reason: "Skill text and two stdlib CLI tools (kb.py, kb_harvest.py) whose output an agent reads; no user-facing surface."
assumptions:
  - "No live interview: every answer comes from autorun-brief.md, collected from the Owner on 2026-11-08. Actors, user stories, success criteria, scope and open questions were derived from the brief and idea.md."
  - "Owner scope ruling (autorun-brief.md, 'Owner scope decision after the first PRD (2026-11-08)'): shown the first draft (commit 307adf8), which kept items 1 and 2, deferred item 3 and cut items 4 to 8, the Owner answered \"Reinstate all 8\". All eight of the brief's items are in scope. The first draft's bar (a failure observed in this repo) is withdrawn as a reason to cut: evidence strength is recorded per item and kept honest, never used to drop one. Items 1 and 2 are observed here; item 3 is one session's anecdote; items 4 to 8 are external practice, unmeasured here."
  - "The orchestrator's six rejected candidates stay rejected, per the same ruling; no new evidence was found to reopen any. The Moonshot rung (running a page's check from lint or on a schedule) stays out, per the same ruling."
  - "Item 4's rubric-level suggestion (when three or more pages share a cause, propose one class page) is the orchestrator's, not the Owner's. It is recorded as an open question for Architect, not as a requirement; the requirement states only the behaviour."
  - "Carriers are not decided here. For items 4, 5, 7 and 8, whose carrier could be skill and rubric text or tooling, each success criterion is written to pin whichever carrier Architect picks: a test asserting the text over the shipped skill and rubric files if the carrier is text, a fixture test if it is tooling. Item 6 is an agent-led setup step, so its criterion is a text assertion by nature. Items 1, 2 and 3 already name kb.py or kb_harvest.py behaviour in the brief's solution hunch, so their criteria are fixture tests."
  - "Item 3's precision cannot be measured offline: a fixture only confirms whatever heuristic it was written for. Its false-positive risk stays a stated risk, and its precision criterion is NOT RUN for the Owner, a hand count over real interactive transcripts on the Owner's machine. No precision figure is claimed."
  - "Reshaping this repo's five other docs/kb pages to the new shapes (items 5, 7, 8) is out of scope: the brief's In list names only main-unprotected.md, as the first user of item 1, and promoting into docs/kb is a human's call."
  - "PRD-0022 is the id the brief reserved (the highest on main and on unmerged branches is PRD-0021)."
  - "ux: not-applicable is the brief's reading, adopted unchanged: the deliverable is skill text and two stdlib CLI tools whose output an agent reads."
  - "idea.md's cheapest kill test was applied by file name only, from names idea.md already cites; no memory file was read. Beyond the three duplicates, idea.md names four memory-only gotchas that are repo-scoped and non-inferable by name, so item 2 has a payload. Of the six docs/kb pages, main-unprotected.md is the only one whose claim is about an outside system; item 1 is kept because the page rubric invites external-system facts in every repo that installs the skill and lint can check none of them."
  - "idea.md's The demo is prose, not a numbered script; it is copied as the steps of the 'demo runs as written' criterion. Its last steps (the skill classifying memory candidates as NOOP, CONFLICT or ADD against the real memory directory) need a model session on the Owner's machine, so the criterion is NOT RUN for the Owner. The demo is unchanged by the ruling: it shows items 1 and 2, and items 3 to 8 carry their own criteria."
  - "Success criteria use fixture directories and fixture transcripts with text written for the tests; fixture memory files may reuse the three duplicate file names idea.md cites, never the real files' contents."
  - "No [NEEDS CLARIFICATION] marker was left in the draft, so the bounded clarify pass had nothing to ask."
---

# PRD: Teach the knowledge base what it cannot see yet

## Problem statement

<!-- coverage-waiver: this run mirrors no tracker (autorun-brief.md, Tracker: reference #1274 only), so no breakdown row carries a work-order id for detector O to match; breakdown.md's items cite the PRD success criteria by number in its Criterion trace instead -->

An agent in a repo with a knowledge base trusts a page whose claim has
stopped being true outside the repo, because `kb.py lint` prints
`kb: 0 problem(s)`. Lint calls a page stale only when a cited repo file
changes after its `verified:` commit. A claim about an outside system (a
GitHub setting, a tool's behaviour) cites no file that would ever change.
This repo's `docs/kb/main-unprotected.md` shows it: it claims a GitHub
setting and carries a hand-written note to re-check two commands, because
nothing else will. Lint passes over it forever. A page also cannot say
what its claim was checked against (local zsh or Linux CI, which tool
version), so a reader cannot tell where it holds.

Lessons the Owner and the agent have already learned sit where the
knowledge base never reads them. The Owner's auto-memory for this repo
holds 39 memory files (counts from the brief). Three duplicate existing
pages, and gotchas such as `gh-pr-edit-broken-use-rest` and
`gate-exit-masked-by-tail` live only in memory, which the cloud routines
and fresh worktree agents never see. `kb_harvest.py` reads transcripts
for two candidate kinds only, fail-edit-pass arcs and recurring errors,
so the human's corrections and answers in an interactive session are
lost too. Setup seeds pages only from the repo's own record and never
asks the human what newcomers get wrong. So those agents learn the same
lessons again the hard way.

The page rubric also leaves out shapes other knowledge bases use: one
page stating a rule over many instances, a summary that leads with what
the agent sees when the gotcha bites, and a wrong/right pair. These are
external practice, with no failure observed here.

## Solution

<!-- coverage-waiver: this run mirrors no tracker (autorun-brief.md, Tracker: reference #1274 only), so no breakdown row carries a work-order id for detector O to match; breakdown.md's items cite the PRD success criteria by number in its Criterion trace instead -->

When this ships, the knowledge base sees eight things it does not today.
Each carries its evidence label, which the Owner's ruling keeps honest
but does not use to cut.

1. **External-fact age** (observed here). A page whose claim is about an
   outside system can say which system it was checked against, when, and
   how long that check holds. Lint reports the page once it is past that
   age. Lint stays offline. This repo's `main-unprotected.md` is the
   first page to declare it, in place of its hand-written note.
2. **Auto-memory as a harvest source** (observed here). Harvest can read
   the repo's auto-memory and list each repo-scoped entry as a candidate,
   beside the existing page it likely duplicates. User-scoped memory is
   never listed, and the skill text names no harness-specific path.
3. **Human corrections and answered questions** (one session's anecdote).
   Harvest can also list the turns in an interactive transcript where the
   human corrected the agent or answered its question, as a candidate
   kind of its own. Its false positives cost the Promoter's attention;
   that risk is stated, and its precision is not measured here.
4. **Class pages** (external practice, unmeasured here). When several
   pages or candidates share one cause, the Ingesting agent can propose
   one page stating the rule with its instances, rather than one page per
   instance.
5. **Symptom-first gotcha summaries** (external practice, unmeasured
   here). A gotcha page's summary leads with what the agent sees when the
   gotcha bites (an error text, a wrong result), then the cause and fix.
6. **Setup asks the human for tribal knowledge** (external practice,
   unmeasured here). Setup asks the human, one question at a time with a
   recommendation, what mistakes newcomers make in this repo, and treats
   the answers as candidates under the same propose-and-promote rule.
7. **An optional wrong/right pair** (external practice, unmeasured here).
   A gotcha page may carry one short pair: the wrong action and the right
   one.
8. **A verified-against line** (external practice, unmeasured here). A
   page may say what its claim was verified against and what it was not
   (an environment, a tool version), beside the commit `verified:`
   already records.

Every new candidate (items 2, 3, 6) goes through ingest's unchanged
NOOP, CONFLICT, UPDATE, DELETE and ADD table, and a human still promotes
every one. Every new page element (items 1, 5, 7, 8) is optional: a page
without it lints exactly as today. Harvest stays read-only.

## Actors

<!-- coverage-waiver: this run mirrors no tracker (autorun-brief.md, Tracker: reference #1274 only), so no breakdown row carries a work-order id for detector O to match; breakdown.md's items cite the PRD success criteria by number in its Criterion trace instead -->

- **Reading agent**: any agent that reads `docs/kb/` before acting. This
  covers interactive sessions, the cloud routines (hourly improvement,
  merge-train) and fresh worktree agents, here and in any repo that
  installs the skill.
- **Ingesting agent**: the agent running the knowledge-base skill's
  ingest, which turns harvest candidates into itemised proposals.
- **Setup agent**: the agent running the skill's setup on a repo with no
  `docs/kb/` yet.
- **Interactive human**: the person in an interactive session who
  corrects the agent, answers its questions, or answers setup's questions
  (the Owner, in this repo).
- **Promoter**: the human who rules on proposals and promotes them into
  `docs/kb/` (the Owner, in this repo).

## User stories

<!-- coverage-waiver: this run mirrors no tracker (autorun-brief.md, Tracker: reference #1274 only), so no breakdown row carries a work-order id for detector O to match; breakdown.md's items cite the PRD success criteria by number in its Criterion trace instead -->

Item 1, external-fact age:

1. As a Reading agent, I want lint to report an external-fact page that is
   past its declared age, so that I re-check the claim before trusting it.
2. As a Promoter, I want an external-fact page to state the outside system
   it was checked against, the date and how long the check holds, so that
   the re-check rule lives in a declaration lint reads, not in a note
   nothing reads.

Item 2, auto-memory as a harvest source:

3. As an Ingesting agent, I want harvest to list this repo's memory
   entries as candidates, each beside the page it likely duplicates, so
   that I can propose NOOP, CONFLICT, UPDATE or ADD without the Promoter
   cross-reading memory against `docs/kb/` by hand.
4. As a Promoter, I want user-scoped memory never to appear as a
   candidate, so that nothing personal is ever proposed into the repo.
5. As a Reading agent in a cloud routine, I want a repo lesson that lives
   only in memory to reach `docs/kb/` once a Promoter promotes it, so that
   I do not learn it again by failing.

Item 3, human corrections and answered questions:

6. As an Ingesting agent, I want harvest to list the turns where the
   Interactive human corrected the agent or answered its question, so
   that a lesson the human had to say out loud is proposed instead of
   lost.
7. As a Promoter, I want those candidates kept apart from arcs and
   recurring errors, so that I can judge or skip them as a kind when they
   prove noisy.

Item 4, class pages:

8. As an Ingesting agent, I want guidance on when several pages or
   candidates share one cause, so that I propose one page stating the
   rule with its instances instead of one page per instance.
9. As a Reading agent, I want one rule in place of many look-alike pages,
   so that I recognise a new instance the knowledge base has not listed.

Item 5, symptom-first gotcha summaries:

10. As a Reading agent, I want a gotcha page's summary to lead with the
    symptom I would see when it bites, so that I connect the error in
    front of me to the page in the index.

Item 6, setup asks for tribal knowledge:

11. As a Setup agent, I want setup to ask the Interactive human what
    mistakes newcomers make in this repo, so that knowledge that lives
    only in their head becomes candidate pages.
12. As an Interactive human, I want those questions asked one at a time,
    each with a recommendation, so that answering them is quick.

Item 7, optional wrong/right pair:

13. As a Reading agent, I want a gotcha page to be allowed one short
    wrong/right pair, so that I can see the exact action to avoid and the
    one to take.

Item 8, verified-against line:

14. As a Reading agent, I want a page to say what its claim was verified
    against and what it was not, so that I know whether it holds in my
    environment (local shell or CI, this tool version).

## Success criteria

<!-- coverage-waiver: this run mirrors no tracker (autorun-brief.md, Tracker: reference #1274 only), so no breakdown row carries a work-order id for detector O to match; breakdown.md's items cite the PRD success criteria by number in its Criterion trace instead -->

All criteria are checkable offline (stdlib tests, fixture directories
and fixture transcripts, an injected "today", never the real `~/.claude`)
except the three marked NOT RUN. Where a criterion says "pinned by a
test", the test is a text assertion over the shipped skill and rubric
files if Architect carries the item as text, or a fixture test if as
tooling.

### Item 1, external-fact age (observed here)

- [ ] **Age is flagged.** In a fixture `docs/kb/`, a page that declares an
      outside source, a check date and a maximum age is reported by
      `kb.py lint` as one problem string naming the page and saying it is
      past its declared age, when the injected today is after date plus
      age. The same page is not reported when today is within the age.
- [ ] **Lint stays offline.** The age check runs no command and opens no
      network connection. A test proves it with the command runner
      replaced by one that fails on any call.
- [ ] **Malformed declarations are reported.** A page whose declared date
      or age cannot be read gets a problem string naming the page and the
      field. It is never silently treated as fresh.
- [ ] **This repo's page uses it.** `docs/kb/main-unprotected.md`
      declares its outside source (the GitHub API), its check date and a
      maximum age, and its hand-written "Re-check … nothing in the repo
      records the setting" note is gone. `python3 kb.py lint` over this
      repo exits 0 on the day it ships.

### Item 2, auto-memory as a harvest source (observed here)

- [ ] **Memory duplicates are paired.** Over a fixture memory directory
      holding files named `cross-pr-hazard-pairwise-merge-test`,
      `manifest-regen-stray-patch-files` and `pr-body-no-work-order-waiver`
      (fixture text), beside a fixture `docs/kb/` holding
      `cross-pr-merge-hazards`, `manifest-regen` and `pr-body-contract`,
      harvest's output lists each memory candidate paired with its page.
- [ ] **A memory-only gotcha is unpaired.** A fixture memory file with no
      matching page appears in harvest's output as a candidate with no
      page beside it.
- [ ] **User scope is excluded.** A fixture memory file marked as
      user-scoped appears nowhere in harvest's output, and no text from
      it does either. The memory directory's own index file is not listed
      as a candidate.
- [ ] **Harness-neutral skill text.** `skills/knowledge-base/SKILL.md` and
      its `references/` contain no harness-specific path (no `~/.claude`,
      no `projects/<slug>/memory`). A test or grep checks this.

### Item 3, human corrections and answered questions (one session's anecdote)

- [ ] **A correction is listed.** A fixture interactive transcript in
      which a human turn corrects the agent's preceding action yields one
      candidate of the new kind, carrying a capped excerpt of the human
      turn and the agent turn it answers.
- [ ] **An answered question is listed.** A fixture transcript in which
      the agent asks a question and the next human turn answers it yields
      one candidate of the new kind.
- [ ] **Plain turns are not listed.** A fixture transcript whose human
      turns only give instructions or approve ("go ahead", a new task)
      yields no candidate of the new kind, and a fixture autonomous
      transcript with no human turn after the first yields none.
- [ ] **The kind is separate.** In harvest's output the new candidates
      sit under their own key or label, apart from arcs and recurring
      errors, whose output over the existing fixtures is unchanged.
- [ ] **Precision is measured.** NOT RUN for the Owner: no offline check
      can measure it, because a fixture only confirms the heuristic it was
      written for. Procedure: on the Owner's machine, run the shipped
      harvest over the last N days of this repo's interactive transcripts
      and hand-label each new-kind candidate as a real correction or
      answered question, or not. The count of each is recorded; no
      threshold is set here (an open question for the Owner).

### Item 4, class pages (external practice, unmeasured here)

- [ ] **Guidance exists.** The skill tells the Ingesting agent when to
      propose one class page over one page per instance, and the
      over-budget advice names a class page as an alternative to merging
      or deleting. Pinned by a test.
- [ ] **Class pages are valid pages.** A fixture class page (one rule,
      several cited instances) lints clean under `kb.py lint`.

### Item 5, symptom-first gotcha summaries (external practice, unmeasured here)

- [ ] **Guidance exists.** The page rubric tells the writer that a gotcha
      page's summary leads with the symptom an agent sees when it bites
      (an error text or wrong result), then the cause and fix, within the
      existing summary cap. Pinned by a test.
- [ ] **No new failure.** A fixture page whose summary does not lead with
      a symptom still lints clean: the rule guides writing, and lint
      reports nothing new about existing summaries.

### Item 6, setup asks for tribal knowledge (external practice, unmeasured here)

- [ ] **Setup asks.** The setup section of `skills/knowledge-base/SKILL.md`
      tells the Setup agent to ask the Interactive human what mistakes
      newcomers make in this repo, one question at a time, each with a
      recommendation. A test asserts the text.
- [ ] **Answers are candidates.** The same section says the answers are
      candidates under the existing propose-and-promote rule and the
      existing cap on pages proposed at setup, never written unpromoted.
      A test asserts the text.
- [ ] **No human, no question.** The same section says that with no human
      present (an autonomous run) the question is skipped and the skip is
      said. A test asserts the text.

### Item 7, optional wrong/right pair (external practice, unmeasured here)

- [ ] **Shape allows it.** The rubric's Shape section allows a gotcha
      page one optional short wrong/right pair. Pinned by a test.
- [ ] **Optional both ways.** A fixture page carrying one pair and a
      fixture page with none both lint clean.

### Item 8, verified-against line (external practice, unmeasured here)

- [ ] **A page can say it.** The rubric tells the writer how a page states
      what its claim was verified against and what it was not. Pinned by a
      test.
- [ ] **Optional both ways.** A fixture page carrying the line and one
      without it both lint clean. If Architect makes it a declaration
      lint reads, a malformed one gets a problem string naming the page.

### Whole run

- [ ] **Existing pages are unaffected.** No new element is required of a
      page. The existing `kb.py` and `kb_harvest.py` tests pass unchanged,
      and the six current `docs/kb/` pages lint as before.
- [ ] **Harvest stays read-only.** After a harvest over the memory and
      transcript fixtures, every fixture file and the fixture `docs/kb/`
      are byte-identical to before. Memory and correction excerpts in the
      output are capped, as transcript excerpts already are.
- [ ] **Fixtures only.** Every new test points harvest at a fixture
      directory. None reads the real memory directory, real transcripts
      or `~/.claude`.
- [ ] **Human still promotes.** `references/ingest.md` routes memory,
      correction and setup-answer candidates through the same NOOP,
      CONFLICT, UPDATE, DELETE and ADD table and the same rule that a
      human promotes. No new path writes to `docs/kb/`.
- [ ] **Source credited.** The skill text that adopts items 1 to 8 credits
      anthropics/knowledge-work-plugins (Apache-2.0), restated in this
      repo's words and never copied, the way `polish` credits Impeccable.
      A test asserts the credit is present.
- [ ] **Routing unchanged.** The knowledge-base skill's frontmatter
      `description` is unchanged (checked by diff against `main`). If a
      later stage changes it, the routing eval is owed and recorded NOT
      RUN with the command `python3 trigger_eval.py`.
- [ ] **The battery passes.** `python3 run_tests.py`, `python3 lint.py`,
      `python3 kb.py drift` and `python3 gates.py && python3 gates.py
      --selftest` each exit 0. If a mirrored file changed, the manifest
      was regenerated after stray `.orig`/`.rej` files were deleted.
- [ ] **The demo runs as written.** NOT RUN for the Owner: the last steps
      need a model session against the real memory directory, on the
      Owner's machine.
      1. Before: `kb.py lint` prints `kb: 0 problem(s)` over a page whose
         GitHub claim nothing re-checks, and the lessons in memory are
         invisible to harvest.
      2. After: lint flags that page as past its declared age (shown by
         setting its check date or age so that it is past).
      3. Harvest lists the three duplicated memories beside their pages,
         and the skill proposes them as NOOP or CONFLICT.
      4. Harvest lists a memory-only gotcha with no page, and the skill
         proposes it as an ADD candidate, each still waiting for a human
         to promote it.
- [ ] **LEDGER untouched.** The knowledge-base skill's maturity in
      `LEDGER.md` does not move. Its Graduation rule needs a real run,
      and none is made here.

## Out of scope
<!-- coverage-waiver: exclusions build nothing; no work order implements an absence -->

- Running a page's declared check (such as `gh api`) from lint or on a
  schedule. That puts network and credentials inside an offline gate,
  and it is the Moonshot rung idea.md seeded to the backlog; the Owner's
  ruling keeps it out.
- Writing or editing the Owner's auto-memory, and promoting any candidate
  into `docs/kb/` (a human promotes, per the skill).
- Reshaping this repo's five other `docs/kb/` pages to the new shapes;
  only `main-unprotected.md` changes, as item 1's first user.
- Connectors, MCP search, a search engine over the knowledge base, a
  digest.
- Confirmed rejected, per the Owner's ruling: usage-based demotion,
  glossary decoding of shorthand, confidence scores and weighted source
  ranking, enterprise search and digest, a harvest watermark, a per-page
  cold-reader test.
- Any paid model run, and any LEDGER maturity change.

## Open questions

<!-- coverage-waiver: this run mirrors no tracker (autorun-brief.md, Tracker: reference #1274 only), so no breakdown row carries a work-order id for detector O to match; breakdown.md's items cite the PRD success criteria by number in its Criterion trace instead -->

- How a page declares its outside source, check date and maximum age
  (frontmatter fields or another form), and whether a page with an outside
  source but no age gets a default or a lint problem. Answered by:
  Architect.
- Whether item 8's verified-against line and item 1's outside-source
  declaration are one declaration or two, and whether item 8 is rubric
  text, a field lint reads, or both. Answered by: Architect.
- Whether the declared age, or a symptom-first summary, changes what the
  compressed index line must hold, given the 2,048-byte budget. Answered
  by: Architect.
- How harvest finds the memory directory (beside the transcript
  directory it already resolves, an explicit flag, or both), and whether
  memory is read on every harvest or only on request. Answered by:
  Architect, within harness neutrality.
- How a memory file is paired with a page (file name, summary text, cited
  sources) and how a memory file's user scope is read from the harness's
  memory format. Answered by: Architect, from the format's documentation
  and fixture files, never the real directory.
- What signal marks a human turn as a correction or an answer (position
  after an agent action or question, wording, a following edit), and
  whether correction candidates are on by default or opt-in given their
  false-positive risk. Answered by: Architect.
- What precision makes correction candidates worth keeping on by default,
  once the NOT RUN hand count exists. Answered by: the Owner.
- Item 4's carrier: rubric or ingest text, tooling that notices pages or
  candidates sharing a cause, or both, and whether to adopt the
  orchestrator's suggested threshold (three or more pages sharing a
  cause). The suggestion is the orchestrator's, not the Owner's. Answered
  by: Architect.
- Items 5 and 7's carrier: rubric text alone, or also a lint check, and
  how a symptom-first summary fits the existing summary cap. Answered by:
  Architect.
- How setup's tribal-knowledge question is worded, what its
  recommendation is drawn from (for example a candidate already found in
  the repo's record), and whether a repo that already has `docs/kb/` can
  run that step on its own. Answered by: Architect.
- How harvest's new candidates and the skill text credit
  knowledge-work-plugins, restated and never copied. Answered by:
  Architect.
