---
stage: review
run: feature:factory-evolution-v1
date: 2026-10-04
assumptions:
  - "date: 2026-10-04 is the UTC date of this Review pass (`date -u +%F` read 2026-10-04 at 01:27Z; the local PDT clock read 2026-10-03). This run dates its artifacts in UTC, as verification.md's first assumption records."
  - "Severity rubric, taken from the most recent autorun review's precedent (feature:first-live-dispatch, draft PR #606) because the skill names no rubric and no user is live to arbitrate: CRITICAL — a reproducible path by which a principal other than the owner bypasses a human gate, lands code on main, or reaches a long-lived credential, with no owner action between cause and effect. MAJOR — a PRD success criterion or architecture/ADR contract not met, or a defect with a concrete scenario that corrupts the run's evidence or a safety property the docs claim, where an owner action or a further condition sits between cause and effect. MINOR — record or doc drift, or a bounded defect with no evidence or safety consequence."
  - "Decision vocabulary, per the orchestrator's standing rules: every major is recorded 'open — needs owner decision' with a suggested routing; minors are deferred with a logged reason. No critical was found, so nothing was fixed and this stage's only write is this file."
  - "Scope is the set of PRs and commits that breakdown.md's rows and Notes and verification.md's evidence cite as this run's work (listed under Scope), each confirmed with `git log origin/main` and read-only `gh pr view --json files`, not the whole repo diff since 2026-09-21."
  - "Standards: the skill's step 5 path resolves to the plugin cache's `docs/standards.json`; this pass read the worktree's `docs/standards.json` as the authority and confirmed with `cmp` that the cache copy is byte-identical. Four statements, all `status: advisory`; filtered to the domains the diff touches (factory, eval, pipeline) — all four survive the filter. No finding matches a statement's text, so no finding cites a slug and the enforced-statement must-fix trigger does not fire."
  - "verification.md's second assumption asked Review to confirm reading PRD-0006 criteria 1 and 6 on their literal text. Confirmed: PRD-0006's own Solution section frames each 'serves autonomy-per-human-hour' clause as traceability ('Every one of the seven items is traceable ... to why it serves'), not as a pass condition. The same reading, applied to criterion 3, is what major finding 1 turns on."
  - "The queue-groomer trigger's live configuration and run history are unobserved by this pass: the trigger API is forbidden to it, and the orchestrator's two attempts returned HTTP 401. Findings 2 to 4 rest on the orchestrator's capture of issue #590 (re-fetched read-only here, unchanged) and on read-only `gh` reads; none asserts what the trigger's configuration is, only what its observed runs report."
---

# Review: Factory evolution backlog seed

## Scope

The run's change is spread over two weeks and seven landings, so the
diff reviewed is the set of PRs and commits the run's own artifacts
cite, each confirmed with `git log origin/main` and `gh pr view <n>
--json files` before it was counted.

Code-bearing, examined in depth (line by line, with probes):

- **#527** (`40ac3dd`) — WO-0066 and WO-0067 (PRD-0006 §Success
  criteria): detectors N (NEEDS-CLARIFICATION) and O (PRD-COVERAGE) in
  `gates.py` with selftest fixtures, `knowledge_plane.parse_run`'s new
  `prd`/`prd_date` fields, the payload mirrors and manifest, the marker
  comment in `skills/prd/TEMPLATE.md` and `skills/architect/TEMPLATE.md`,
  and the PRD skill's bounded clarify step (`skills/prd/SKILL.md` step
  5). No later commit on `origin/main` touches `check_prd_coverage` or
  `check_needs_clarification` (`git log -L` over the function returns
  nothing after `40ac3dd`).
- **#525** (`90432bf`) — WO-0068 (PRD-0006 §Success criteria):
  `skill_metrics`, `metrics_report`, `print_metrics` and the
  `--metrics/--kind` flags in `trigger_eval.py`; `tests/test_trigger_eval_metrics.py`;
  the backlog seed's new number.

Docs, read for contract drift against `architecture.md` and the ADRs:

- **#515** — ADR-0070, ADR-0071, ADR-0072, their `docs/adr/README.md`
  rows, and this run's idea, PRD-0006, architecture and breakdown.
- **#532** (`675318a`) — the three roster protocol docs under
  `docs/factory/` and the `CLAUDE.md`/`AGENTS.md` pointer.
- **#563** and **#583** (`6742c9f`) — WO-0065's hosting blocker and its
  deferral (PRD-0006 §Success criteria), and the backlog line 76 seed.

This branch's own increment, `git diff origin/main...HEAD` (10 files,
+825/−17), read line by line:

- `8ebfd12` — the queue-groomer doc's §Trigger record, the dated
  deferral line in the retro/reflect and doc-gardener docs' §Trigger,
  the `CLAUDE.md`/`AGENTS.md` roster note, four `costs.jsonl` rows
  (WO-0069 to WO-0072, all `owner-session:unmetered`, `cost: 0.0`),
  breakdown.md's four checkbox flips, four assumptions and three Notes,
  `docs/backlog.md` line 77, and `autorun-brief.md`.
- `206b72b` — `verification.md`, its 18 verdicts and six assumptions
  (reviewed under "Verify's reasoning" below).

Evidence the orchestrator captured, quoted as its capture and not this
pass's observation: the trigger API refused `get` and `list_runs` for
`trig_01W5PgiQb4G2qwMXnNVFtACx` with `HTTP 401 oauth_scope_insufficient`
at 2026-10-03T04:1xZ (`req_011CfeDGQbQGam1pPRUbRjTQ`,
`req_011CfeDGUihvDbAedZPRsaQB`) and at 2026-10-04T01:2xZ
(`req_011CfgKcdBTN4CPcybhCUvtD`, `req_011CfgKcdnAnPg3tUGTPT5fK`), and
the full comments of issue #590 fetched 2026-10-03T04:16:33Z. This pass
re-fetched #590 read-only and found the same three comments, nothing
newer:

```
$ date -u +%FT%TZ
2026-10-04T01:27:02Z
$ gh api repos/mattbutlerengineering/skills/issues/590/comments --jq '.[] | "\(.id) \(.created_at) \(.body[0:80] | gsub("\n";" "))"'
5879079505 2026-09-28T21:30:26Z <!-- queue-groomer-state last-scan=2026-09-28T21:15:00Z --> **2026-09-28 — PR**:
5912133888 2026-09-30T13:19:51Z <!-- queue-groomer-state last-scan=2026-09-30T13:19:16Z --> **2026-09-30 — propo
5912152378 2026-09-30T13:20:59Z **Correction / addendum to the comment above (issuecomment-5912133888).**  Two t
$ gh pr view 589 --json state,mergedAt,createdAt --jq '"#589 \(.state) created \(.createdAt) merged \(.mergedAt)"'
#589 OPEN created 2026-09-28T21:29:30Z merged null
$ gh variable list
FACTORY_PAUSED	false	2026-09-28T15:31:01Z
```

The 2026-09-28 entry predates the trigger (created 2026-09-29 04:11
UTC), so it is a one-off session, not a scheduled fire. The two
2026-09-30 entries are the only observed behaviour of anything the
trigger may have started.

Probes ran against fixture trees in this session's scratchpad
(`.../scratchpad/review/probe_o.py`, `probe_o_criteria.py`), importing
the worktree's `gates.py` read-only with `PYTHONDONTWRITEBYTECODE=1`;
`git status --short` was empty afterwards.

## Findings

Four major, six minor, no critical.

### Major 1: detector O checks coverage per `##` section, so it cannot catch the failure ADR-0072 and PRD-0006's criterion 3 adopt it to catch — a dropped success criterion

- Scenario: a PRD has three success criteria (sign-in, password reset,
  30-day session expiry) and its breakdown has one row, for sign-in,
  citing `§Success criteria`. O stays silent, so the two dropped
  criteria surface at Verify or never:
  ```
  $ PYTHONDONTWRITEBYTECODE=1 python3 $SP/review/probe_o_criteria.py "$PWD"
  3 criteria, 1 row covering only sign-in -> O: []
  ```
  This is not a corner case in this repo: every PRD writes its
  criteria as unnumbered `- [ ]` checkboxes (the PRD template's shape),
  and every section citation in every breakdown names the whole section:
  ```
  $ grep -rhoE "§ ?Success criteria[^),;]*" docs/features/*/breakdown.md docs/breakdown.md | sort | uniq -c | sort -rn
    97 §Success criteria
     1 §Success criteria bullet
  ```
  So any one row citing `§Success criteria` covers every criterion of
  every PRD O gates. ADR-0072's Consequences name exactly this failure
  ("a PRD success criterion silently dropped between PRD approval (gate
  1) and Verify"), and PRD-0006 criterion 3 says the check serves the
  metric "by catching a silently-uncovered PRD criterion at Decompose".
  O meets WO-0067's acceptance text and ADR-0072's literal Decision
  (its per-checkbox clause applies only "where a PRD numbers them", and
  no PRD does), so verification.md's PASS on row 12 is correct as
  written. What decays is the contract between the ADR's stated purpose
  and the gate that ships, and nothing records that gap: neither
  breakdown.md's 2026-09-23 note nor the gates.py comment says O cannot
  see a dropped criterion.
- Standard: none
- Decision: open — needs owner decision. Two routings: (a) accept
  section granularity and record the bound honestly (an amending ADR
  per this repo's supersede-don't-rewrite rule, since ADR-0072 is
  accepted); or (b) route to Implement for per-criterion coverage,
  which needs a citation grammar for individual criteria (numbered
  criteria in the PRD template plus a `§Success criteria N` citation
  form `_cites` already tolerates).

### Major 2: the queue-groomer pilot's observed runs contradict its protocol's environment — no `gh` CLI, so precondition §1.1 is skipped and the `FACTORY_PAUSED` kill switch (§1.2) is never checked

- Scenario: `docs/factory/queue-groomer-routine.md` §Trigger, written by
  this branch, says "Connectors: none — no MCP connectors; `gh` and
  `git` only", and §1 says a failing `gh auth status` stops the run.
  The 2026-09-30T13:19:51Z journal entry, two minutes after the
  scheduled fire, reports the opposite environment and carries on
  anyway: "this session again had no `gh` CLI and no tool that reads
  `vars.FACTORY_PAUSED`. The pause state is unverified, and since this
  run opened no PR the gap did not matter." The 2026-09-28 one-off
  session reported the same ("GitHub access was via MCP tools only")
  and did open PR #589 with the pause "unconfirmed throughout". Failure
  path: the owner sets `FACTORY_PAUSED=true` during an incident; #589
  has merged, so §1.3's no-new-PR mode no longer applies; on the next
  Wednesday the routine cannot read the variable, falls through to
  normal mode, and files a hygiene issue and a backlog PR into a paused
  factory. `FACTORY_PAUSED` reads `false` today (above), so nothing has
  gone wrong yet. The same §1.1/§1.2 text and the same "`gh` and `git`
  only" line are in `retro-reflect-routine.md` and
  `doc-gardener-routine.md`, so the two deferred triggers, which the
  brief says "follow with one command each", would inherit a dead kill
  switch. The routine has already proposed the fix twice ("a session
  that cannot read the variable defaults to propose-only"), and §8 says
  a human applies it.
- Standard: none
- Decision: open — needs owner decision. Suggested routing: a human PR
  amending §1 of all three roster docs (an unverifiable pause means
  propose-only; name the GitHub access the cloud environment actually
  provides), and correcting each §Trigger's "gh and git only" line,
  before the two deferred triggers are created.

### Major 3: two sessions ran the queue groomer for 2026-09-30, nobody can observe the trigger to explain why, and the protocol has no same-day guard

- Scenario: the 13:20:59Z comment reports "This session independently
  ran the queue-groomer routine for 2026-09-30 ... about a minute"
  after the 13:19:51Z entry, and asks "why the routine fired twice for
  the same day". Possible causes (a second trigger, a manual run-now, a
  platform double fire) cannot be told apart, because `get` and
  `list_runs` have returned 401 at both of the orchestrator's attempts.
  Since its creating session, nobody has observed the trigger behind
  the checked WO-0070 (PRD-0006 §Success criteria). The double run cost nothing in
  lane terms on 2026-09-30, because #589 held both sessions in
  no-new-PR mode. Once #589 merges, two concurrent sessions in normal
  mode each read §1.3 before either has pushed. Each then opens its own
  hygiene issue and backlog PR on the same file, which breaks the
  "Caps: one PR, one issue" non-negotiable. Every such week also
  doubles the spend the owner approved as a single-run pilot.
  Nothing in §1 to §6 stops a second run on a day whose journal
  already carries an entry. The `CLAUDE.md`/`AGENTS.md` line this branch
  writes ("only the queue groomer's trigger exists") is also an absence
  claim nobody has observed. The 2026-09-29 capture showed one trigger
  record and did not list triggers.
- Standard: none
- Decision: open — needs owner decision. Suggested routing: the owner
  re-authenticates and runs the trigger `list` and `list_runs` for
  `trig_01W5PgiQb4G2qwMXnNVFtACx` (deleting any duplicate trigger)
  before #589 is merged, and decides whether §1 gains an idempotency
  rung ("the journal already has an entry dated today → stop"). This
  review does not dispute WO-0070's check: the 13:19:51Z entry is
  indirect evidence that something fired on schedule.

### Major 4: the pilot's journal cannot show the cost the owner's decision waits on — both 2026-09-30 entries report no model spend

- Scenario: the brief's rationale ("one weekly run bounds the new spend
  while its journal shows real cost") and the unblock condition in
  `docs/backlog.md` line 77, added by this branch ("What unblocks it: a
  few groomer journal entries with spend, then the owner's approval of
  the two recurring costs"), both treat the journal's `Spend:` line as
  the cost signal. Both observed scheduled-day entries report "no
  `claude` CLI or model-API spend". A routine session cannot see its own
  model usage, so the line leaves out the run's only material cost, the
  Sonnet session itself, run twice that day. The daily routine's entries
  in #181 show the same pattern ("Estimate: low cents"). Failure path:
  after a few Wednesdays the owner reads entries that say no spend,
  takes the condition as met, and approves two more weekly triggers. The
  real weekly spend, possibly doubled by finding 3, was never in the
  journal.
- Standard: none
- Decision: open — needs owner decision. Suggested routing: amend line
  77's unblock condition, by a new append-only line since the producer
  rule forbids rewriting, to name where the real cost is read (the
  account's usage for this trigger's sessions, not the journal), or
  amend §6 to say the `Spend:` line is an estimate that excludes the
  session's own model usage.

### Minor 1: detector O grandfathers any PRD whose `date:` is quoted or non-ISO, despite its own "fail closed" comment

- Scenario: `read_frontmatter` keeps quotes, and O compares the raw
  string to `COVERAGE_ADOPTED`. `'"2026-10-03"' < "2026-09-21"` is true
  because `"` sorts before `2`, so the PRD is skipped. The same goes for
  any date starting with a character below `2` (`1 Oct 2026`,
  `10/03/2026`). The comment beside the constant says "A missing date
  is NOT grandfathered — fail closed, so omitting the date cannot dodge
  O". Omitting the date can't dodge O, but quoting it does:
  ```
  1 baseline ATX, unquoted date      : ['O: docs/features/demo/prd.md:12 PRD-0001 §Actors is cited by no breakdown row and carries no coverage waiver']
  2 same, quoted date                : []
  3 same, single-quoted date         : []
  ```
- Standard: none
- Decision: deferred. No PRD in the repo quotes its date (`grep -rlE
  "^date: [\"']" docs` returns nothing) and the template writes ISO.
  The fix (parse with `date.fromisoformat` and fail closed on anything
  unparseable) is a small maintenance run. It should be seeded by
  whoever closes this run, because this stage writes nothing else.

### Minor 2: detector O cannot see setext (`------`-underlined) sections, the #147 bypass class `gates.py` documents a few lines above `HEADING_LINE`

- Scenario: `_prd_sections` reads only ATX headings. A PRD that writes
  `Actors` underlined with `------` renders on GitHub as an h2 section,
  but O never sees it, so an uncovered, unwaived section passes:
  ```
  4 setext h2 sections, unquoted date: []
  ```
  `gates.py`'s own comment on `SETEXT_UNDERLINE` names this ("a
  splitter that reads only ATX is blind to sections a human reviewer
  plainly sees (the #147 bypass)"), and H's splitter handles it.
- Standard: none
- Decision: deferred. No PRD in the repo uses setext headings, and the
  template writes ATX. It belongs in the same maintenance run as minor 1.

### Minor 3: detector O counts any `WO-####` line in breakdown.md as a citing row, including dated Notes prose

- Scenario: a Notes line like `- 2026-10-01: WO-0001 (PRD-0001 §Actors)
  descoped the admin actor` makes `§Actors` covered, even though no work
  order row cites it:
  ```
  5 ATX, Actors cited only in a Note : []
  ```
  This matches detector A's convention (A also treats every WO-token
  line as a row, which is why this repo's Notes carry citations at
  all). It is still wider than ADR-0072's "cited by at least one
  breakdown row".
- Standard: none
- Decision: deferred. It cannot hide a gap in this run, where every
  row cites the same section. Narrowing it should follow whatever major
  1 decides about citation grammar.

### Minor 4: detector N fires on a quoted marker inside an indented code block

- Scenario: the N comment treats code spans and fenced blocks as
  quotes. CommonMark's third code form, the four-space indented block,
  is not treated that way, so documenting the syntax in an indented
  block fails CI:
  ```
  6 N on marker in indented code blk : ['N: docs/features/demo/prd.md:12 unresolved [NEEDS CLARIFICATION] marker']
  ```
- Standard: none
- Decision: deferred. It fails closed, the workaround (a fence) is
  trivial, and both templates quote the syntax in a code span.

### Minor 5: `trigger_eval.py --metrics` crashes with a traceback, not the read error it prints for an unreadable file, when given valid JSON that is not a results record

- Scenario (from reading the code; `trigger_eval.py` was not run, as
  this stage forbids): `print_metrics` catches only `OSError` and
  `ValueError`. Pointing `--metrics` at an eval set or any JSON object
  without a `results` key raises `KeyError` in `metrics_report`, and a
  JSON array raises `AttributeError` at `output.get`. The exit is
  nonzero either way, so no wrong number is ever printed.
- Standard: none
- Decision: deferred. The tool is read-only and on demand, and the
  failure is loud, not silent.

### Minor 6: breakdown.md's 2026-09-29 Note says "No `docs/backlog.md` seed was added", but the same commit adds backlog line 77

- Scenario: the Note for WO-0069 and WO-0071 (PRD-0006 §Success
  criteria) says the revisit "lives in those two lines". The same
  commit's breakdown assumption ("the orchestrator added the seed after
  the Implement pass") and verification.md's rows 14, 16 and 18 cite
  backlog line 77. A reader who trusts the run's dated history, or the
  queue groomer surveying `docs/backlog.md` for duplicates against run
  directories, gets two answers to whether a seed exists.
- Standard: none
- Decision: deferred. The assumption entry and this review both record
  the true state. Ship may append a dated correcting Note if the
  orchestrator wants the history to read cleanly, without rewriting the
  original.

## Verify's reasoning

- **The 14/4 tally holds.** Each PASS in rows 1 to 9 is backed by the
  quoted grep, gates or `gh` output in its own section. Each FAIL in
  rows 10, 14, 16 and 18 is an owner deferral, already seeded at
  backlog lines 76 and 77.
- **Assumption 2 (literal reading of criteria 1 and 6):** confirmed
  (see `assumptions:`). The same reading makes row 3 a fair PASS, and
  that is why major 1 is a contract finding and not a Verify error.
- **Assumption 3 (criterion 8 counts only `wo:*`-labelled issues):**
  sound. The five `type:chore` tracking issues were all opened after
  #515 merged the rows, so even the looser reading finds no issue
  ahead of its row (`adr0032-one-way-mirror` holds).
- **Assumption 4 (row 15 on the orchestrator's capture):** sound and
  honestly labelled. The capture is now indirectly corroborated: a
  journal entry landed two minutes after the first scheduled fire. Its
  claim that "the trigger has not run yet" was true when written and is
  out of date now. Findings 2 and 3 are about what those runs reported,
  not about whether the capture was right.
- **Assumptions 5 and 6:** sound. No Implement action clears any of the
  four failures.
- **One "Not verified" item is now closed.** Verify could not
  re-derive the backlog's near-miss micro recall, because the command
  runs `trigger_eval.py`. This pass derived it from the recorded file
  with independent code (no `trigger_eval.py` import) and got the
  same number, so the seed is not fabricated (`eval-honesty` holds):
  ```
  $ python3 - <<'PY'   # reads evals/results/trigger-omp-2026-07-05.json directly
  rpq 3
  cases whose fired counts exceed runs_per_query (multi-fire runs): 0 []
  independent near-miss micro recall: 18 / 39
  near-miss failed cases: 8 of 16
  ```
  The zero multi-fire count also confirms that `skill_metrics`'s
  `fn = sum(row) − tp` cannot count a co-fire as a miss: each run
  records exactly one fired slug.

## Passes with no findings

- **Security: clean.** The branch adds no code and no secrets. The
  trigger and environment ids in the docs are identifiers, not
  credentials. The connectors the create call attached by default were
  cleared six seconds after creation, before any run, per the capture.
  The new detectors' regexes are line-bounded and anchored. `--metrics`
  only reads a path the operator names and never writes.
- **Correctness of `skill_metrics`/`metrics_report`: clean.** The
  zero-denominator contract (None for undefined precision or recall,
  0.0 F1 only when both are 0.0) matches the docstring and the 13
  tests. `"none"` is correctly the negative class. The kind filter
  rebuilds the confusion through `summarize()`, so it reads no field
  the record lacks.
- **Design of the branch increment against `architecture.md`: clean,
  apart from findings 2 to 4.** The roster docs' journals are found by
  marker and not pinned, a deliberate departure from architecture's
  "pinned-journal reporting pattern", which each doc records with its
  reason (contended pin slots). The four ledger rows follow the
  owner-session policy detector G checks.
- **The ADRs and the README index: clean.** They compose with ADR-0036
  and ADR-0005/ADR-0011 as `architecture.md` says, and detector D
  agrees with the Status lines.

## Verdict

Not blocked by any critical finding, so the run may proceed to Ship
(prepare-and-stop) once the owner has seen the four majors. None is a
defect in this branch's own lines that a re-implementation could
clear:

- Finding 1 is a choice between amending ADR-0072 and building
  per-criterion coverage.
- Findings 2 to 4 concern a live, recurring, paid trigger that no
  session since its creator has been able to observe.

Before the two deferred triggers are approved, and before #589 is
merged, the owner should:

1. Restore trigger read access and confirm there is one trigger and
   one run per Wednesday (finding 3).
2. Amend the roster docs' pause precondition (finding 2).
3. Decide where the pilot's real cost is read (finding 4).

Ship's `release.md` should carry these as owner actions, not as
release steps.
