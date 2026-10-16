# Architecture Decision Records

Decisions live here as sequentially numbered ADRs (`0001-slug.md`). An ADR
can be a single paragraph; the value is in recording the decision and its
why. Don't delete or rewrite an old ADR when a decision changes — write a new
one that supersedes it and update the old one's status line.

Statuses: **accepted** (explicitly confirmed), **provisional** (recommended
answer adopted while awaiting confirmation — pivot freely),
**superseded by ADR-NNNN** (fully retired — citing it is drift),
**superseded in part by ADR-NNNN**, and **amended by ADR-NNNN** (both
partial: the decision stays live and citable). The machine-readable
authority is `ADR_STATUS` in `knowledge_plane.py`, which also allows a
parenthesized annotation after any head.

ADRs 0001–0018 were migrated from the former `DESIGN.md`, which captured the
initial design interview (2026-07-01). See [CONTEXT.md](../../CONTEXT.md) for
the canonical vocabulary.

## Index

| ADR | Decision | Status |
|-----|----------|--------|
| [0001](0001-lifecycle-pipeline-spine.md) | Spine: lifecycle pipeline | accepted |
| [0002](0002-stage-taxonomy.md) | Stage taxonomy (Idea → … → Operate) | accepted |
| [0003](0003-two-run-scales.md) | Two run scales (product / feature) | superseded in part by ADR-0025 |
| [0004](0004-artifacts-are-the-state.md) | Artifacts are the state | accepted |
| [0005](0005-soft-gating.md) | Soft gating | accepted |
| [0006](0006-plugin-from-day-one.md) | Plugin from day one | accepted |
| [0007](0007-claude-code-only-target.md) | Claude Code only target harness | amended by ADR-0027 |
| [0008](0008-self-contained-skills.md) | Skills are self-contained | accepted |
| [0009](0009-audience-you-first-publishable-always.md) | Audience: you first, publishable always | accepted |
| [0010](0010-stage-skills-plus-thin-router.md) | Stage skills + thin router | accepted |
| [0011](0011-interview-early-draft-late.md) | Interview early, draft late | accepted |
| [0012](0012-lightweight-ledger.md) | Lightweight ledger | accepted |
| [0013](0013-plugin-name-idea-to-prod.md) | Plugin name: idea-to-prod | accepted |
| [0014](0014-mit-license.md) | License: MIT | accepted |
| [0015](0015-templates-per-stage.md) | Templates per stage | accepted |
| [0016](0016-operate-scope.md) | Operate scope | accepted |
| [0017](0017-conditional-ux-frontmatter.md) | Conditional-UX mechanics | accepted |
| [0018](0018-git-bootstrap.md) | Git bootstrap | accepted |
| [0019](0019-trigger-and-output-evals.md) | Evals: routing discrimination + on-demand output grading | accepted |
| [0020](0020-hybrid-recall-policy.md) | Hybrid recall policy for skill descriptions | accepted |
| [0021](0021-shared-protocol-module.md) | One shared protocol module alongside standalone scripts | amended by ADR-0052 |
| [0022](0022-eval-schema-module.md) | One eval-schema module beside the protocol module | accepted |
| [0023](0023-utility-skills.md) | Utility skills alongside stage skills and the router | accepted |
| [0024](0024-eval-schema-charter.md) | eval_schema's charter covers all eval knowledge, not one file's schema | accepted |
| [0025](0025-maintenance-run-scale.md) | A third run scale: the maintenance run | accepted |
| [0026](0026-tracker-mirror-one-way.md) | The issue-tracker bridge is an opt-in one-way mirror | accepted |
| [0027](0027-oh-my-pi-second-harness.md) | oh-my-pi is a supported second harness (Claude primary) | amended by ADR-0076 |
| [0028](0028-brownfield-adoption-onramp.md) | Brownfield adoption on-ramp (adopt/onboard entry) | provisional |
| [0029](0029-backlog-seed-inbox.md) | A derived, advisory backlog (seed inbox) | accepted |
| [0030](0030-incident-fastlane-and-tracker-intake.md) | Incident fast lane and tracker intake | accepted (Decision 2; Decision 1 remains provisional) |
| [0031](0031-omp-trigger-eval-adapter.md) | The trigger eval drives omp too; results are harness-marked | accepted |
| [0032](0032-factory-dispatch-plane.md) | Factory dispatch plane: issues mirror breakdown rows one-way | superseded in part by ADR-0083 (the beads clause; amended by ADR-0035) |
| [0033](0033-three-human-gates.md) | Three human gates: PRD, blueprint, merge | amended by ADR-0087 (and earlier by ADR-0036) |
| [0034](0034-work-order-budgets-and-routing.md) | Work-order budgets and model routing | amended by ADR-0084 (and earlier by ADR-0041) |
| [0035](0035-github-is-the-single-work-order-mirror.md) | GitHub issues are the single work-order tracker mirror | superseded in part by ADR-0083 (the beads carve-out) |
| [0036](0036-agent-merge-under-independent-review.md) | Agent merges permitted under independent review | amended by ADR-0085 |
| [0037](0037-factory-seam-modules.md) | Factory seam modules: knowledge_plane, cli, factory_config, cost_ledger | amended by ADR-0039 |
| [0038](0038-harness-adapter-registry.md) | One registration per harness in the trigger-eval runner | amended by ADR-0045 |
| [0039](0039-tracker-grammar-joins-the-knowledge-plane.md) | Tracker-mirror grammar joins the knowledge plane | amended by ADR-0040 (roster further amended by ADR-0058; walk widened to parse_run by ADR-0068) |
| [0040](0040-write-outputs-joins-the-cli-seam.md) | write_outputs joins the cli seam | amended by ADR-0042 |
| [0041](0041-gate-latency-rows-join-the-cost-ledger.md) | Gate-latency observations are cost-ledger rows | amended by ADR-0049 |
| [0042](0042-gh-runner-and-event-read-join-the-cli-seam.md) | gh_runner and the event read join the cli seam | amended by ADR-0051 |
| [0043](0043-pre-ledger-rows-are-annotated-in-the-knowledge-plane.md) | Pre-ledger rows are annotated in the knowledge plane | accepted |
| [0044](0044-daily-improvement-routine.md) | A daily routine drives the factory's improvement loop | superseded in part by ADR-0083 (the queue is read from GitHub issues, not the beads export) |
| [0045](0045-lifecycle-label-writers.md) | Every lifecycle label has a named writer; wo:blocked's is a human | accepted |
| [0046](0046-tools-factory-symmetry-deferred.md) | tools/factory root symmetry deferred — flat root is load-bearing | superseded in part by ADR-0091 (the blocker diagnosis; amended by ADR-0059 and ADR-0065) |
| [0047](0047-factory-roles-seam.md) | Factory roles seam: factory_roles.py owns the role vocabulary | accepted |
| [0048](0048-artifact-path-grammar-joins-factory-config.md) | The installed-vs-payload path grammar joins factory_config | accepted |
| [0049](0049-row-identity-joins-the-cost-ledger.md) | The row identity joins the cost ledger | accepted |
| [0050](0050-mirrors-carry-a-transform.md) | MIRRORS carries a transform: one authority per payload file | amended by ADR-0067 |
| [0051](0051-report-joins-the-cli-seam.md) | The report epilogue joins the cli seam | accepted |
| [0052](0052-skill-file-contract-joins-the-protocol-seam.md) | The skill-file contract joins the protocol seam; lint pins the recitals | accepted |
| [0053](0053-charter-replay-joins-the-harness-seam.md) | Charter replay joins the harness seam | accepted |
| [0054](0054-front-door-routes-humans.md) | The front door routes humans, not files | accepted |
| [0055](0055-deferred-stops-and-payload-charters.md) | The budget hook and payload charters stay deferred | accepted |
| [0056](0056-human-gates-module.md) | The three human gates get a module of their own | amended by ADR-0090 (and earlier by ADR-0074) |
| [0057](0057-lifecycle-legs-agree-about-an-uncited-pr.md) | Both lifecycle legs treat an uncited PR the same way | amended by ADR-0064 |
| [0058](0058-checkbox-regex-roster-is-two-owners.md) | The checkbox-regex roster is two owners, not three | accepted |
| [0059](0059-restructure-is-blocked-by-nine-files.md) | The tools/factory restructure is blocked by nine files, not one | superseded in part by ADR-0091 (the blocker table and the provisional note) |
| [0060](0060-one-cross-plane-drift-rule.md) | One cross-plane drift rule; the caller declares what absence means | accepted |
| [0061](0061-a-carve-out-lives-at-the-definition-site.md) | A carve-out lives at the definition site and must pay rent | provisional |
| [0062](0062-a-skill-that-states-repo-facts-runs-a-shipped-tool.md) | A skill that states repo facts runs a shipped tool | accepted |
| [0063](0063-a-terminal-verdict-requires-having-looked.md) | A terminal verdict requires having looked | provisional |
| [0064](0064-a-quoted-token-is-not-a-claim.md) | A quoted work-order token is not a claim | provisional |
| [0065](0065-the-frontmatter-split-and-what-it-unblocks.md) | The frontmatter split, and what it does and does not unblock | superseded in part by ADR-0091 (the narrowed blocker and the split as a restructure step) |
| [0066](0066-no-seam-for-ghs-silence.md) | No seam for gh's silence; the rule is shared, the meaning is local | provisional |
| [0067](0067-codeowners-mirrors-through-product-codeowners.md) | CODEOWNERS mirrors through product_codeowners, not identity | accepted |
| [0068](0068-parse-run-widens-the-knowledge-plane-walk.md) | parse_run widens the knowledge-plane walk (expand phase) | amended by ADR-0094 (every run-artifact and ADR-index read guarded, reported by D) |
| [0069](0069-autonomy-per-gate-wait-hour.md) | Autonomy per human-hour: accepted orders per gate-wait hour | superseded in part by ADR-0080 |
| [0070](0070-github-merge-queue-composes-with-agent-merge.md) | Adopt GitHub's native merge queue, composing with agent-merge | accepted |
| [0071](0071-needs-clarification-markers.md) | Inline [NEEDS CLARIFICATION] markers, CI-enforced | accepted |
| [0072](0072-prd-coverage-check.md) | Bidirectional PRD-requirement <-> work-item coverage check | accepted |
| [0073](0073-standards-index-seam-and-detector-letters-k-m.md) | Standards index as a seam module; detector letters K and M | accepted |
| [0074](0074-a-gate-stay-ends-at-its-pass-label.md) | A gate stay ends at its pass label | accepted |
| [0075](0075-the-guarded-file-read-joins-the-cli-seam.md) | The guarded local-file read joins the cli seam | provisional |
| [0076](0076-grok-supported-harness.md) | Grok is a supported harness (Claude primary) | accepted |
| [0077](0077-the-dispatched-agent-holds-no-write-credential.md) | The dispatched agent holds no write credential | provisional |
| [0078](0078-a-project-knowledge-base-indexed-inline.md) | A project knowledge base, indexed inline in the always-loaded file | accepted |
| [0079](0079-a-utility-skill-may-own-a-project-reference-file.md) | A utility skill may own a project reference file, by section | provisional |
| [0080](0080-accepted-means-a-dispatched-order-whose-mirror-merged.md) | Accepted means a dispatched order whose mirror merged | accepted |
| [0081](0081-plugin-eval-is-an-on-demand-harness.md) | `claude plugin eval` is an on-demand harness with its own tree | superseded in part by ADR-0093 (the no-detector clause and the five-case count) |
| [0082](0082-the-pipeline-writes-adrs-at-its-stages.md) | The pipeline writes ADRs at its stages, by one test | accepted |
| [0083](0083-github-issues-are-the-only-tracker.md) | GitHub issues are the only tracker; beads is retired | accepted |
| [0084](0084-the-cost-ledger-keys-a-run-by-issue-when-it-has-no-work-order.md) | The cost ledger keys a run by its issue when it has no work order | accepted |
| [0085](0085-an-owner-answer-executed-by-the-conductor-is-the-human-merge.md) | An Owner answer executed by the Conductor is the human merge | amended by ADR-0086 |
| [0086](0086-standing-consent-may-cover-a-conductor-merge.md) | Standing consent may cover a Conductor merge | accepted |
| [0087](0087-a-queue-profile-may-opt-in-to-implement-queue-auto-merge.md) | A queue profile may opt in to implement-queue auto-merge | amended by ADR-0088 |
| [0088](0088-a-fast-path-classification-is-the-review-for-auto-merge.md) | A fast-path classification is the review for auto-merge | accepted |
| [0089](0089-an-enforced-standard-may-cite-a-standing-adr.md) | An enforced standard may cite a standing ADR | accepted |
| [0090](0090-the-gate-timeline-read-and-open-queues-join-human-gates.md) | The gate timeline read and the open queues join human_gates | accepted |
| [0091](0091-the-restructure-blockers-re-measured-and-pinned.md) | The tools/factory restructure blockers, re-measured and pinned | superseded in part by ADR-0097 (the cli.py row) |
| [0092](0092-a-derived-trace-view-joins-the-knowledge-owners-over-time.md) | A derived trace view joins the knowledge owners over time | accepted (Owner, 2026-10-14) |
| [0093](0093-every-plugin-eval-case-carries-its-skill-tag.md) | Every plugin-eval case carries its skill directory as a tag | accepted (Owner, 2026-10-14) |
| [0094](0094-parse-run-reads-every-artifact-through-the-guarded-read.md) | parse_run reads every run artifact and the ADR index through the guarded read | accepted (Owner, 2026-10-14) |
| [0095](0095-the-plugin-version-moves-only-in-a-release-pr-or-at-a-conductor-merge.md) | The plugin version moves only in a release PR or at a Conductor merge | accepted (Owner, 2026-10-15) |
| [0096](0096-this-repo-opts-in-to-implement-queue-auto-merge-with-a-docs-fast-path.md) | This repo opts in to implement-queue auto-merge, with a docs fast path | accepted (Owner, 2026-10-15) |
| [0097](0097-fast-path-joins-the-root-only-importers-of-cli.md) | fast_path joins the root-only importers of cli.py | provisional |
| [0098](0098-the-reviewer-credential-never-meets-pr-code.md) | The reviewer's credential never meets the pull request's code | provisional |
| [0099](0099-a-stamp-may-be-tools-only-and-its-manifest-says-so.md) | A stamp may be tools-only, and its manifest says so | provisional |
| [0100](0100-every-stage-commits-its-artifact-at-its-boundary.md) | Every stage commits its artifact at its boundary | provisional |
| [0101](0101-ship-completes-on-the-outcome-it-recorded.md) | Ship completes on the outcome it recorded, not on release.md existing | provisional |
| [0102](0102-a-retro-counts-its-population.md) | A retro counts its population, and a run is complete once it has | provisional |
| [0103](0103-calibrate-warns-below-its-floor-and-the-floor-is-a-setting.md) | Calibrate warns below its floor, and the floor is a setting | provisional |
| [0104](0104-a-finished-runs-retry-redoes-its-bookkeeping.md) | A finished run's retry redoes its bookkeeping, and a launch re-reads its issue | provisional |
| [0105](0105-a-pull-request-merged-outside-the-batch-is-the-items-merge.md) | A pull request merged outside the batch is the item's merge | provisional |
