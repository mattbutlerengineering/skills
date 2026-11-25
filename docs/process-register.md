# Process register

Every process this repo runs on itself, the ADR-0135 metric it protects,
and the last evidence that it caught something real. ADR-0135's sunset rule
reads this table: a process with no real catch for 60 days is a sunset
candidate, and the weekly metrics run flags it for removal by one PR (with a
superseding ADR where an ADR exists). **Adding a process requires a row
here**, naming its metric.

How to read it:

- **A real catch** is a genuine defect the process flagged that someone then
  fixed: a CI failure on a PR that was corrected before merge, a routine's
  issue that led to a merged fix, a review or gate finding that changed the
  PR. A fix to the process's own code is not a catch.
- **Metric** is the register's reading of which ADR-0135 metric the process
  could move (speed, quality, autonomy, overhead). "none stated" means it
  guards only overhead artifacts (ADRs, breakdowns, ledgers, labels) or PR
  traceability, which no ADR-0135 metric measures.
- **Status** is `keep` when the last catch is within 60 days of 2026-11-25
  (on or after 2026-09-26), `sunset-candidate` otherwise. "none found"
  means the search came up empty, not that the process is useless; a
  process added inside the window is still listed as a candidate.
- Evidence was searched on 2026-11-25: the logs of all 225 failed
  `validator` runs (2026-07-12 to 2026-11-25), the journal issues #181,
  #925, #930, #586, #587, #590, #294 and #178, issues labelled
  `source:sweep`, `wo:failed` or `wo:blocked`, and PR and issue search.

| Process | What it is | Metric | Last real catch | Status |
|---|---|---|---|---|
| gates A WO-CITATION | Every breakdown work-order row cites a PRD id | none stated | none found | sunset-candidate |
| gates B PR-TRACEABILITY | The PR body carries a work-order id or waiver, plus `Closes #N` | none stated | 2026-11-19, [#2071](https://github.com/mattbutlerengineering/skills/pull/2071): no `Closes` link, body fixed, then green | keep |
| gates C LINK-INTEGRITY | Every PRD/ADR/work-order token in the repo resolves | none stated | 2026-08-28, [#367](https://github.com/mattbutlerengineering/skills/pull/367): a dangling work-order token in a verification file, amended before merge | sunset-candidate |
| gates D BLUEPRINT-DRIFT | ADRs read, carry a known status and match the ADR index | none stated | 2026-10-11, [#675](https://github.com/mattbutlerengineering/skills/pull/675): two unknown ADR statuses, fixed in the PR | keep |
| gates E SCAFFOLD-SYNC | Manifest checksums match the template payload and stamped files | quality | none found | sunset-candidate |
| gates F CONFIG-SHAPE | `factory.json` parses and every field is a valid token | none stated | none found | sunset-candidate |
| gates G COST-LEDGER | Cost-ledger lines carry the ADR-0034 fields | none stated | none found (fired on #175, 2026-07-28, which closed unmerged) | sunset-candidate |
| gates H EVIDENCE-HONESTY | A verification verdict shows fenced output or discloses NOT RUN | none stated | 2026-08-31, [#420](https://github.com/mattbutlerengineering/skills/pull/420): verification with no evidence, fixed on the next push | sunset-candidate |
| gates I STALENESS | No knowledge-plane doc links a missing path | none stated | none found | sunset-candidate |
| gates J LABEL-WIRING | Every label the tools name exists in the taxonomy | none stated | none found | sunset-candidate |
| gates K STANDARDS-DRIFT | `docs/standards.json` matches a fresh regen | none stated | none found | sunset-candidate |
| gates M CAPTURE-COMPLETENESS | Every `defect.md` has the capture template's sections | none stated | none found | sunset-candidate |
| gates N NEEDS-CLARIFICATION | No PRD or architecture keeps an unresolved clarification marker | none stated | none found | sunset-candidate |
| gates O PRD-COVERAGE | Every PRD section is cited by a breakdown row or waived | none stated | none found | sunset-candidate |
| gates P EVAL-APPEND-ONLY | A PR rewrites no existing eval record (added 2026-11-24, #2332) | quality | none found | sunset-candidate |
| `gates.py --selftest` | Runs the detectors against fixture trees | none stated | none found (anything it catches is a fix to the detectors) | sunset-candidate |
| L LABEL-SYNC (`tools/label_sync.py`, sweeps) | Live repo labels match the label taxonomy | none stated | 2026-08-22, [#173](https://github.com/mattbutlerengineering/skills/issues/173): three label descriptions drifted, synced | sunset-candidate |
| `tools/lint.py` | Skill, plugin and protocol structure checks | quality | none found (only failure, on #1611, was an intermediate push fixed by a commit already pushed 28 s later) | sunset-candidate |
| `tools/kb.py drift` | Instruction-file drift in CLAUDE.md, AGENTS.md and rules | none stated | none found | sunset-candidate |
| CI test suite (`tools/run_tests.py`) | The full unittest suite on every PR | quality | 2026-11-09, [#1611](https://github.com/mattbutlerengineering/skills/pull/1611): the npx bundle test failed, fixed by a follow-up commit in the PR | keep |
| `validator.yml` check job | Runs suite, lint, kb drift and gates on every PR and main push | quality | 2026-11-19, [#2071](https://github.com/mattbutlerengineering/skills/pull/2071) (via detector B) | keep |
| `validator.yml` review job | Posts the factory review comment from a distinct reviewer account | quality | none found (its failures were 403s and missing payloads) | sunset-candidate |
| `tools/validator.py` lifecycle jobs | Needs-review and merged label flips; checks which work order a PR implements | none stated | 2026-11-24, [#2328](https://github.com/mattbutlerengineering/skills/pull/2328): body cited work orders it did not implement, rewritten, then green | keep |
| PR-body preflight hook (`tools/pr_body_preflight.py`) | Local `gh pr create` hook applying detector B before the PR exists | none stated | none found (blocks leave no record; its issues are fixes to itself) | sunset-candidate |
| `assembler.yml` / `tools/assembler.py` | Dispatches a ready work order to an agent run | autonomy | none found (recent runs skipped) | sunset-candidate |
| `charter-replay.yml` | Manual real-model charter replays | quality | none found (no runs listed) | sunset-candidate |
| `cost-report.yml` | Weekly cost report and monthly cap breaker | none stated | none found (pause step never fired) | sunset-candidate |
| `design.yml` | Web-quality checks on PRs touching `docs/design/` | quality | none found (no runs listed) | sunset-candidate |
| `gate-digest.yml` | Daily gate-queue digest and gate latency rows | none stated | none found | sunset-candidate |
| `npx-branch.yml` | Rebuilds the `npx` install branch on release | none stated | none found (publishes; not a check) | sunset-candidate |
| `pages.yml` | Publishes the assembly line page | none stated | none found (publishes; not a check) | sunset-candidate |
| `sweeps.yml` reconcile | Files plane-drift intake between breakdown rows and issues | none stated | 2026-11-09, [#1142](https://github.com/mattbutlerengineering/skills/issues/1142): eleven mirror labels out of step, reconciled | keep |
| `toolsmith-mine.yml` | Weekly rejection mining into #294 | none stated | none found (#294 last updated 2026-08-21) | sunset-candidate |
| Daily improvement routine | One evidenced process fix a day (journal #181) | none stated | 2026-11-18, [#2054](https://github.com/mattbutlerengineering/skills/issues/2054) filed, fixed by [#2055](https://github.com/mattbutlerengineering/skills/pull/2055) | keep |
| Hourly improvement routine | One S-sized fix per hour, issue to merge (journal #925) | none stated | 2026-11-22, [#2321](https://github.com/mattbutlerengineering/skills/pull/2321): a kb page misdescribed detector B, corrected | keep |
| Merge-train routine | Phase 0 verdicts and a serial merge train every 4 hours (journal #930) | speed | none found (its holds repeat detector failures; no finding of its own) | sunset-candidate |
| Queue-groomer routine | Weekly backlog and claim hygiene (journal #590) | none stated | 2026-10-07, [#589](https://github.com/mattbutlerengineering/skills/pull/589): 8 resolved seeds still open in the backlog | keep |
| Doc-gardener routine | Weekly doc-rot fix (journal #586) | none stated | 2026-11-13, [#1769](https://github.com/mattbutlerengineering/skills/pull/1769): CLAUDE.md's routine-trigger list was false | keep |
| implement-queue review gate | A distinct reviewer scores each queue PR (`tools/reviewer_verdict.py`) | quality | 2026-11-15, findings on #1829 filed as [#1833](https://github.com/mattbutlerengineering/skills/issues/1833), fixed by [#1847](https://github.com/mattbutlerengineering/skills/pull/1847) | keep |
| Post-wave regression review | An independent agent reviews a wave's merges | quality | 2026-11-21, [#2268](https://github.com/mattbutlerengineering/skills/issues/2268): two regressions, fixed by [#2269](https://github.com/mattbutlerengineering/skills/pull/2269) | keep |
| Pairwise merge test | merge-tree chain simulation before merging a wave (`docs/kb/cross-pr-merge-hazards.md`) | quality | none found (the kb page cites 2026-10-07 without a PR or issue link) | sunset-candidate |
| Human gates (`tools/human_gates.py`) | PRD, blueprint and merge gates on work-order labels | quality | none found (no issue ever carried a rejection label) | sunset-candidate |
| CODEOWNERS | Owner review on every path | quality | none found (no PR has a changes-requested review) | sunset-candidate |
| kb page re-verification | A stale kb page is re-read against its sources | none stated | 2026-11-22, [#2321](https://github.com/mattbutlerengineering/skills/pull/2321): a wrong claim about which gate strips fences, corrected | keep |

## Retired

- 2026-11-25, Retro/reflect routine (journal #587): no real catch in 60
  days, all 9 runs propose-only (#2359).
