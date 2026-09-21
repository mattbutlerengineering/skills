# AI review & CI automation: survey and shortlist

Research note, 2026-09-20/21. Question: what review-automation and
merge-queue mechanisms (CodeRabbit-class bots, merge queues, other
agentic-CI review tooling) best pre-chew a human merge gate, and which
would strengthen gate 3 (ADR-0033, amended by ADR-0036) and the reviewer
charter (`factory/charters/reviewer/CHARTER.md`)? Primary sources: GitHub's
own docs, Mergify's docs, DORA's metrics guide, and independent benchmark
reporting on AI review tools (not vendor marketing pages, where avoidable).

## What the factory already has

Gate 3 (PR merge) is a **review gate an agent may satisfy**, not an
unconditional human-hands-on-merge gate (ADR-0036, amending ADR-0033). An
agent may merge only when required status checks are green **on the
merge-result commit**, an independent non-authoring reviewer's pass is
recorded on the PR, and the PR is not itself a gate change (`docs/adr/**`,
`prd.md`, `architecture.md`, `docs/design/**` stay human-merged). The
reviewer charter's central, hard-won rule is **re-execution over reading**:
"Take every claim the PR, the breakdown row, or `verification.md` makes
about having verified something, and drive it yourself against the code on
the branch. Paste the literal, unedited output you got — not the author's.
A claim you did not re-run is a claim you did not review." Findings are
confidence-filtered before they're reported. A class of work order may
graduate to auto-merge only on evidence (≥20 merged PRs, ≥90% acceptance,
zero defect escapes, churn ≤10%), and one escape auto-revokes the class.

## GitHub native merge queue

**What it is.** GitHub's built-in queued-merge mechanism for branches with
required status checks. Source:
<https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue>,
<https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/merging-a-pull-request-with-a-merge-queue>.

**Core mechanism.** GitHub builds a **speculative merge commit** combining
the target branch, every PR already ahead in the queue, and the new PR, and
runs CI against *that* — not against main alone. Concretely: with PRs A, B,
C queued in order, "it tests A against main, B against main+A, and C
against main+A+B" — each PR validated against the state the branch will
actually be in when it lands. `GITHUB_ACTIONS`-based required checks must
add `merge_group` as a trigger or they never run inside the queue. A check
failure at any position **pulls that PR from the queue and restarts every
PR behind it** with a fresh speculative commit, because their base just
changed.

## Mergify

**What it is.** A third-party GitHub App/service layering configurable
merge automation over branch protections and merge queues. Source:
<https://docs.mergify.com/configuration/conditions/>,
<https://docs.mergify.com/merge-queue/rules/>.

**Core mechanism.** Mergify reads a repo's branch protections/rulesets and
**auto-injects them as merge conditions** — e.g. a required-approvals rule
becomes `#approved-reviews-by >= 1` — configurable per-repo in
`.mergify.yml`, with an injection mode choosing whether protections apply
at queue-time, merge-time, or both.

## CodeRabbit-class AI review bots

**What it is.** LLM-plus-static-analysis PR review bots (CodeRabbit named
specifically; the class also includes similar tools). Source: 2026
independent benchmark reporting summarized via search (Martian's Code
Review Bench methodology and a separate 309-PR independent benchmark);
treat as secondary reporting, not the vendor's own claims, and see
"Couldn't verify" for what wasn't traced to primary sources.

**Core mechanism and honestly-reported limits.** CodeRabbit combines AST
evaluation, static application security testing, and generative feedback,
and is reported at "approximately 46% accuracy in detecting runtime bugs,
with an F1 score of 51.2%" on one benchmark — "the highest of any AI code
review tool tested" there, which is itself a statement about the class, not
just this one tool. The same reporting scores it "1 out of 5 on
completeness and 2 out of 5 on depth" in an independent 309-PR benchmark:
"reliably catching syntax errors, security vulnerabilities, and style
violations, but frequently missing intent mismatches, performance
implications, and cross-service dependencies." The consistent framing
across sources is that these tools work "most effective when combined with
human review rather than as a standalone solution" — first-pass filtering
of the obvious stuff, not a substitute for judgment.

## DORA: change failure rate vs. defect escape rate

**What it is.** Two related but distinct delivery-quality metrics. Source:
<https://dora.dev/guides/dora-metrics/>, secondary reporting cross-checked
across two independent glossaries.

**The distinction, which the factory's own ADR does not currently draw.**
Change failure rate is "the percentage of deployments causing a failure in
production that require an immediate fix" (failed deploys ÷ total
deploys) — it only counts a defect if it caused an *incident*. Defect
escape rate is "defects found in production ÷ total defects" — it counts
**every** defect that got past a given testing gate, whether or not it
ever caused an incident. ADR-0033 already uses the phrase "a defect escape
attributed to agent-merge narrows or revokes it" as a load-bearing trigger
for auto-revocation, without defining which of these two the phrase means.

## Shortlist

| # | Mechanism (source) | Verdict | Own ADR? |
|---|--------------------|---------|----------|
| 1 | Batched speculative-merge queue testing (GitHub native) | **Adopt** | Yes |
| 2 | Third-party auto-injected merge conditions (Mergify) | **Reject** | — |
| 3 | Pattern-matching AI review bot as the merge-gate reviewer (CodeRabbit-class) | **Reject** | — |
| 4 | Escaped-defect vs. change-failure distinction (DORA) | **Adapt** | No — amend ADR-0033's definition when operationalized |
| 5 | Precision/recall benchmarking of the reviewer itself against a labeled defect corpus | **Adapt (deferred)** | Yes, if pursued |

### Rationales

**1. Batched speculative-merge queue — Adopt, and this is the survey's
strongest finding.** The factory already has direct, painful, first-party
evidence of the exact problem this mechanism solves: a documented sweep
found "64 contended pairs — every pair of open PRs whose diffs touch a
common file — were merged two-at-a-time in an isolated detached worktree
and the full triad run on the merged state," discovering real cases where
"two PRs each green alone, red together, invisible to both CIs" (an ADR
number collision between two independently-green PRs; a taxonomy/data split
where each PR was complete against its own base and incomplete against the
merged one). That sweep had to be done **by hand**, once, as an audit — it
does not run continuously. GitHub's merge queue is exactly this check,
automated and continuous: every queued PR is tested against the state it
will actually land into, and a failure removes it and reruns everyone
behind it. Adopting it does not replace the reviewer charter's judgment
gate — it replaces a manual pairwise-merge audit technique with a native
mechanism that runs on every merge, for the cost of `merge_group` triggers
on the required-check workflows and accepting that a mid-queue failure
cascades reruns to everyone behind it (worth flagging honestly: at the
40+-open-PR backlog volumes this repo has actually hit, that cascade cost
is real and would need its own capacity/ordering thought, not just a
config flip). One ADR: adopting the merge queue, and how it composes with
ADR-0036's agent-merge conditions (the queue enforces the check-state
condition; the reviewer charter still owns the independent-review
condition). Evidence: GitHub Docs (quoted above) vs. the cross-PR-hazard
sweep already on record in this repo.

**2. Mergify's auto-injected conditions — Reject.** The mechanism itself —
reading branch protections and turning them into explicit merge conditions
— is a config convenience the factory's reviewer charter already achieves
more precisely and more auditably: ADR-0036's three conditions
(merge-result-commit checks, independent non-authoring review recorded on
the PR, not-a-gate-change) are explicit Python-adjacent prose in a
version-controlled charter, not implicit rules inferred by a third-party
service reading branch settings. Adding a paid GitHub App to enforce logic
the repo already encodes and tests itself is a second, weaker owner of the
same rule — the one-owner principle this repo already applies to its own
code. Evidence: docs.mergify.com (quoted above) vs.
`factory/charters/reviewer/CHARTER.md`'s Merge decision section.

**3. CodeRabbit-class review bots as the merge-gate reviewer — Reject, with
strong comparative evidence.** The independently-reported numbers argue
directly against this adoption: 46% runtime-bug detection accuracy and
"1 out of 5 on completeness, 2 out of 5 on depth" is a materially weaker
bar than the reviewer charter's own re-execution discipline, which exists
*because* a real incident showed reading a claim instead of re-running it
misses exactly the kind of finding CodeRabbit-class tools are reported to
miss ("intent mismatches... cross-service dependencies"). The class's
genuine strength — reliably catching syntax errors, security
vulnerabilities, style violations, the "obvious stuff" — is not a gap the
factory has: `gates.py` and `lint.py` already catch that category
deterministically (no LLM, no probabilistic miss rate) before a reviewer
ever looks at the diff. Adopting a CodeRabbit-class bot would add a second,
strictly weaker mechanism doing what deterministic detectors already do
better, while adding nothing at the depth layer where the factory's
reviewer charter is already reported to be ahead. Evidence: 2026 benchmark
reporting (quoted above) vs. `gates.py`/`lint.py` plus the reviewer
charter's re-execution rule.

**4. Escaped-defect vs. change-failure distinction — Adapt, deferred.**
ADR-0033's auto-revocation trigger ("a defect escape attributed to
agent-merge") is currently undefined between two real, different
thresholds: DORA's change-failure-rate only counts a defect that actually
caused a production incident requiring an immediate fix, while
defect-escape-rate counts *any* defect that got past a testing gate
regardless of downstream impact — a much lower, much more sensitive bar.
Which one ADR-0033 means changes how trigger-happy auto-revocation is. This
repo has no production deployment surface yet (the dormant fourth gate,
ADR-0033) and no class has graduated to auto-merge yet, so there is no live
ambiguity to resolve today — but the definition should be picked
*before* the first class graduates, not discovered mid-incident. Fold into
whichever future ADR first operationalizes class graduation, rather than a
standalone amendment now. Evidence: dora.dev (quoted above) vs. ADR-0033's
undefined term.

**5. Precision/recall benchmarking of the reviewer charter itself —
Adapt, deferred.** The independent benchmarks cited above exist because
someone built a labeled corpus of real defects and scored review tools
against it (F1, completeness, depth) rather than trusting either the
tool's own claims or a single anecdote. The factory already has the
matching infrastructure pattern for a *different* charter-regression
purpose — `charter_replay.py` replays golden fixture work orders against
role charters and scores degradation — but nothing scores the reviewer
charter's actual precision/recall against a labeled defect corpus the way
this survey's own sources score CodeRabbit. Building one (planted defects
of known kind and severity, reviewer charter run against them, scored like
the WO-0011/#147 incident that originally justified ADR-0036) would turn
"the reviewer role demonstrably works" from a single cited anecdote into
an ongoing, re-runnable measurement — the same evidentiary bar ADR-0033
already demands for class graduation. Deferred: it's real infrastructure
work, not a quick win, and the existing single-incident evidence has not
yet been contradicted by anything. One ADR if pursued. Evidence: the
Martian Code Review Bench methodology (as reported) vs. `charter_replay.py`
and ADR-0036's own cited WO-0011/#147 justification.

## Couldn't verify

- **CodeRabbit's exact benchmark methodology and sample composition** —
  the "46% accuracy" and "F1 51.2%" figures and the "1/5 completeness, 2/5
  depth" scores were read from secondary search-result summarization, not
  from the primary benchmark report or CodeRabbit's own technical
  documentation; neither the "Martian" benchmark nor the "independent
  309-PR benchmark" was fetched and read directly for this survey. Treat
  the specific numbers as reported-by-secondary-source, not independently
  confirmed against a primary paper.
- **Whether GitHub's merge queue composes cleanly with a required
  independent-agent-review check** (ADR-0036's condition 2) — the fetched
  docs describe queue mechanics and required status checks generically;
  nothing was found describing how a *review* requirement (vs. a CI status
  check) interacts with queue admission specifically. Detector B,
  gate-latency capture, and the reviewer charter's own `gate:merge` label
  would need their own design pass against this before adoption, not just
  a docs read — flagged as an open question for item 1's ADR, not resolved
  here.
- **Mergify's pricing/self-hosting posture** — not investigated; the
  Reject verdict rests on the one-owner argument (item 2's rationale), not
  on cost, so this gap does not change the verdict.
- **Fetch-tool caveat.** As with the companion autonomous-agent-harnesses
  survey, quotes above came through a summarizing search/fetch pass and
  were not independently re-grepped against raw primary-source text; the
  DORA and merge-queue quotes were cross-checked against two independent
  secondary sources each for consistency, which is a lower bar than the
  spec-driven-sdlc survey's raw-file re-verification.

## Primary sources

- GitHub merge queue: <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue>,
  <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/merging-a-pull-request-with-a-merge-queue>
- Mergify: <https://docs.mergify.com/configuration/conditions/>,
  <https://docs.mergify.com/merge-queue/rules/>
- DORA metrics: <https://dora.dev/guides/dora-metrics/>
- This repo: `factory/charters/reviewer/CHARTER.md`, ADR-0033, ADR-0036,
  and the cross-PR-hazard pairwise-sweep finding already on record
