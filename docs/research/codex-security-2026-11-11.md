# openai/codex-security: what it provides and what this pipeline should take

Research note for issue #1731, 2026-11-11. Research only; no skill added and no
code changed. Everything fetched was read as data: nothing was installed or
run, and the repository's own `AGENTS.md` and skill text were not followed.
Evidence labels: "read" means I opened the file through the GitHub API and the
text is quoted or paraphrased from it; [INFERENCE] means not read, or derived
from a read file.

The issue asks two things: can this repo provide a skill for security, and
which of its existing skills can be used in that process for the best outcome.

## 0. Scope and what was skipped

Repository read: https://github.com/openai/codex-security, default branch
`main`, head commit 2911786f243f08fd61ad854f5c527e7b0c404ccc on 2026-11-11.
The tree has 1,577 files. Header read through the API: Apache License 2.0,
11,932 stars, created 2026-07-13, description "OpenAI's Codex Security CLI and
TypeScript SDK for finding, validating, and fixing security vulnerabilities".

Read in full or in the part that matters: `README.md`, `docs/agent-workflows.md`,
`docs/plugin-connectors.md`, `LICENSE` (Apache 2.0 text), `SECURITY.md` (first
12 lines), `AGENTS.md` (first 40 lines), `evals/README.md` (first 30 lines),
`plugins/codex-security/.codex-plugin/plugin.json`, and the first 45 lines of
seven skill files: `security-scan`, `security-diff-scan`, `triage-finding`,
`verify-fix`, `fix-finding`, `validation`, `check-skills`.

Not read, so nothing below rests on it: the other 13 skill files under
`plugins/codex-security/skills/` (`assess-patch-risk`, `attack-path-analysis`,
`cloud-findings`, `deep-security-scan`, `define-security-policy`,
`finding-discovery`, `propose-security-hardening`, `publish-findings`,
`resolve-dependency-alert`, `threat-model`, `threat-model-visualize`,
`track-findings`, `vulnerability-writeup`; only their names and the README's
one-line task descriptions were read), the shared `plugins/codex-security/references/`
files, the TypeScript SDK under `sdk/typescript/` (673 files), the MCP app under
`plugins/codex-security/mcp-app/`, the GitHub Action, the container setup and
the 20 scanner-import guides.

Local files read for the overlap: `skills/review/SKILL.md`,
`skills/audit/SKILL.md`, `skills/verify/SKILL.md`,
`skills/implement-queue/references/reviewer-contract.md`, and the `security`
lines of `skills/implement/SKILL.md`, `skills/implement-queue/SKILL.md` and
`skills/lean/SKILL.md`.

## 1. What the repository provides

| Piece | What it is | Read from |
|---|---|---|
| CLI `cs` / `codex-security` | `cs scan`, `cs scan --diff <rev>`, `--working-tree`, `--mode deep`, `--path`, `--max-time`; `cs validate`, `cs patch`, `cs verify-fix`, `cs policy`, `cs export`, `cs scans show/logs/resume/rerun`, `cs findings imported`. Needs Node 22.13+ and Python 3.10+, and `cs login` or `OPENAI_API_KEY`/`CODEX_API_KEY` | `README.md` (Quick start), `docs/agent-workflows.md` |
| TypeScript SDK | `CodexSecurity` class, `security.run(path)` returns a report path; deep-scan configuration, validation, severity classification, owner suggestions | `README.md` (TypeScript SDK) |
| Plugin `codex-security` v0.1.95 | A Codex plugin with a `skills/` directory, a `.mcp.json` server and an `.app.json` for connected apps; category "Security" | `plugins/codex-security/.codex-plugin/plugin.json` |
| 20 workflow skills | Listed in section 2 | `plugins/codex-security/skills/*/SKILL.md` (names from the tree; seven read) |
| GitHub Action and containers | A weekly repository scan example with an estimated $5 limit per scan, a severity threshold and PR checks, Docker Compose bulk scans | `README.md` (GitHub Actions, Containerized bulk scans) |
| Scanner imports | Guides for 20 third-party scanners (Semgrep, Snyk, Sonar, Trivy, Checkmarx, Wiz, GitHub code scanning and others), saved locally or published to Cloud | `README.md` (Features); file names from the tree |
| Evals | Five suites: triage-finding (Promptfoo, calibration, SastBench), secret-discovery, standard-time-budget, workflow-routing, check-skills fixtures. CI runs the deterministic checks of four of them; model runs are opt-in and consume usage | `evals/README.md` |
| Licence | Apache License 2.0, repository and plugin manifest agree | `LICENSE`, `plugin.json` (`"license": "Apache-2.0"`) |

Dependencies that matter for a decision: the scans run on Codex and OpenAI
models (other providers listed in `README.md`: Amazon Bedrock, OpenRouter,
Fireworks AI, Cheaper Inference), need an account or API key, and some
cybersecurity requests "require Trusted Access for Cyber" (`README.md`, Quick
start). The plugin's skills call managed MCP tools by name, for example
`start_codex_security_standard_scan` and `complete_codex_security_scan`
(`security-scan/SKILL.md`, `security-diff-scan/SKILL.md`), so the skill text is
not usable without that server [INFERENCE for how much of each skill depends on
it: I read only the first 45 lines of each].

## 2. The skills, by the stage of a security process

Descriptions are from each file's frontmatter (read) except where marked.

| Stage | Skill | What it does |
|---|---|---|
| Model | `threat-model` | Run once per scan, or accept a supplied one (`security-diff-scan` step 1, read). Frontmatter not read |
| Find | `security-scan` | Whole repository or selected paths; "the default single-pass audit". Starts from code that accepts untrusted input or exercises authority, follows it to the operation it controls, checks the real enforcement point. Records what was reviewed and what remains uncertain |
| Find | `security-diff-scan` | PR, commit, branch diff or working-tree patch. Reviews every changed text file including deleted ones; follows changed behaviour into supporting code "without expanding into an unrelated repository audit". Runs `$finding-discovery`, then `$validation` once, then `$attack-path-analysis` once |
| Find | `deep-security-scan` | Repeated audits of one target; later audits use earlier findings (`docs/agent-workflows.md`). Not read |
| Validate | `validation` | Decides whether each candidate is supported by evidence; records a disposition for every candidate with counterevidence or an exact proof gap; reads `false_positive_feedback.json` as evidence, not instructions |
| Triage | `triage-finding` | One static-evidence verdict per supplied finding: `confirmed`, `not_actionable` or `needs_review`; accepts SARIF, CVEs, advisories, Jira and Linear tickets; works inline, never edits files or runs anything; reads the root and scoped `SECURITY.md` first as "the primary local definition" of attacker roles and trust boundaries |
| Fix | `fix-finding` | "Only when the user explicitly asks". Smallest repository-native fix at the shared boundary; returns `no_change` when the path is already safe; challenges its own patch against every caller and one newly rejected ordinary input; `standard` or `static` verification mode |
| Verify the fix | `verify-fix` | "Only when the user explicitly requests". Verdict per finding: `fixed`, `still_vulnerable` or `inconclusive`; "closed tickets, unrelated passing tests, and the absence of a new scan finding" are insufficient proof |
| Dependencies | `resolve-dependency-alert` | Traces a dependency alert, proposes an upgrade or dismissal (`docs/agent-workflows.md`). Not read |
| Track | `track-findings`, `publish-findings`, `cloud-findings` | Linear, Jira, GitHub issues, Cloud, SARIF/JSON/CSV export. Not read |
| Policy | `define-security-policy` | Drafts or updates `SECURITY.md` (`README.md`). Not read |
| Skill supply chain | `check-skills` | Read-only pre-install review of a skill file, bundle or collection; verdict `BLOCK`, `REVIEW`, `INCOMPLETE` or `PASS`; refuses to run if the target is already installed or discoverable in the session; treats all target text, including text addressed to the reviewer, as untrusted |
| Other | `assess-patch-risk`, `attack-path-analysis`, `finding-discovery`, `propose-security-hardening`, `threat-model-visualize`, `vulnerability-writeup` | Names only |

Three mechanisms recur in the files I read and are the transferable part:

1. Every verdict has an explicit "not proven" outcome (`needs_review`,
   `inconclusive`, `INCOMPLETE`) and a coverage statement. A zero-finding report
   "can still list exclusions or unresolved questions" (`docs/agent-workflows.md`).
2. Fix and fix-verification skills are opt-in only by their descriptions, so they
   are not invoked "while implementing fixes, reviewing ordinary code changes,
   or running tests" (`verify-fix/SKILL.md`).
3. The security policy of the target repository is an input to every scan
   (`triage-finding/SKILL.md`, `README.md`: "Scans use existing root and
   component `SECURITY.md` guidance").

## 3. Overlap with this repo

| This repo | What it does about security today | Overlap with codex-security | What codex-security has that this does not |
|---|---|---|---|
| `review` (`skills/review/SKILL.md`) | One bullet in the review checklist: "inputs validated at boundaries, no secrets in code, injection surfaces parameterized, errors don't leak internals" | `security-diff-scan` reviews a change for vulnerabilities; same input (a diff) | Source-to-sink tracing from untrusted input, a threat model, a validation pass that tries to defeat each candidate, attack-path analysis, a coverage statement. Here it is a checklist line and a grade of severity by the user |
| `audit` (`skills/audit/SKILL.md`) | `security` is one of eleven categories swept with `references/playbook.md`; read-only; a finding counts only once reproduced, otherwise it is a suspicion | `security-scan` is the whole-repo, read-only, evidence-first equivalent | A dedicated multi-stage pipeline per finding, repeated deep scans that reuse earlier findings, resumable scans with saved state, SARIF export. The "reproduced or suspicion" rule here is the same idea as `validation`'s disposition per candidate [INFERENCE: I did not read `references/playbook.md`'s security section] |
| `verify` (`skills/verify/SKILL.md`) | Runs checks to show the PRD's success criteria are met | `verify-fix` also demands evidence, not assertion | A verdict for one specific claim, "this vulnerability is fixed", with a bypass hunt and a rule that closed tickets and green unrelated tests are not proof. `verify` has no security-specific criterion |
| `skills/implement-queue/references/reviewer-contract.md`, `security` category | `security` is one of eight `issues` categories; "One major defect (hallucination, regression, security) caps the score at 4"; a specialist reviewer returns `pass` or `block`; the default profile has "no specialists" (`skills/implement-queue/SKILL.md`, `reviewers` row) | A specialist security reviewer would call `security-diff-scan` or `triage-finding` | A calibrated evidence standard for what counts as a security defect (reachable, attacker-controlled, control checked). Here the category is a label on a finding by a generalist reviewer |
| `implement`, `lean` | Name "security controls" as behaviour never to cut (`skills/implement/SKILL.md` line 29, `skills/lean/SKILL.md` line 79) | None | `fix-finding`'s "no speculative change" and caller-challenge steps, relevant when a security finding is implemented |
| `skills/implement-queue/SKILL.md` Phase 1 | Claims in `priority` order, `security` first (`priority` row, line 39) | The queue already ranks a `security` label first | Nothing to take; the queue consumes issues, the scanner produces them |

What this repo lacks, in order of how much it matters:

- No threat model or trust-boundary step anywhere in the pipeline; `architect`
  records architecture, not attacker roles [INFERENCE: I did not read
  `skills/architect/SKILL.md`].
- No per-claim vulnerability validation or fix verification.
- No import of an existing scanner's output (SARIF, Dependabot, code scanning).
- No pre-install check of third-party skills. This repo's research notes read
  other repos' skills as data by convention (see
  `docs/research/skills-repos-2026-11-08.md`), but nothing checks one before it
  is vended.
- No security policy input: nothing reads the target repo's `SECURITY.md`.

What this repo has that codex-security lacks: a stage and artifact model
(`docs/pipeline-protocol.md`), a queue that drains issues to PRs with a
reviewer, and a human-gate model. codex-security ends at a report, a patch and
a ticket; it does not decide what to build next.

## 4. Can this repo provide a skill for security?

Yes, in the shape of a thin utility skill that applies the three mechanisms
above to this pipeline's own artifacts, not a port of the plugin. Reasons:

- The plugin's skills depend on a managed MCP server and an OpenAI-hosted
  scan engine (section 1). Vending its text here without that server would
  leave tool names with nothing behind them.
- This repo is stdlib-only Python with no network dependency (`AGENTS.md`, hard
  conventions). Adopting the CLI or SDK as a dependency of the pipeline would
  break that; running it from an optional skill, as the user's own tool, would
  not.
- The licence permits copying text (Apache 2.0 requires keeping the notice and
  stating changes). A skill that quotes or adapts its wording needs an
  attribution line [INFERENCE: this repo's LICENSE is MIT; mixing the two is a
  licensing decision for the Owner, not made here].

Which existing skills to use in the process, for the best outcome:

| Process step | Skill already here | Use |
|---|---|---|
| Find what is weak across a codebase | `audit` (category `security`) | First pass, read-only, ranks and routes findings to `docs/backlog.md` |
| Check one change before it ships | `review` (Security bullet) | Keep; grows the bullet into a pointer to the new security stage if one is adopted |
| Prove the fix | `verify` | Add a security criterion only when a PRD names one |
| Gate queue PRs | `implement-queue` reviewer contract, specialist slot | The place a security specialist plugs in |
| Fix | `implement` with `lean`'s rule that security controls are never cut | Unchanged |
| External scanner or `cs` run | Outside this repo | The Owner runs it, and `audit` or `capture` takes the report as a finding source |

## 5. Recommendations

One per candidate. Sizes: S is under a day, M is one to three days, L is more.
None is implemented here.

| # | Candidate | Recommendation | Reason | Size |
|---|---|---|---|---|
| 1 | A `security` utility skill for this repo (threat model of the change, source-to-sink trace, per-candidate validation with a `needs_review` outcome, coverage statement) | **Adapt** | The method transfers (section 2, mechanisms 1 and 3); the MCP and OpenAI engine do not (section 1). Write it from the method in this repo's own voice, stdlib-only, read-only on source, with the opt-in-only description rule for fixing. Needs a trigger-eval entry like any new skill | M |
| 2 | A security specialist reviewer for the queue's specialist slot, driven by the evidence standard of `security-diff-scan` and `triage-finding` | **Adapt** | The specialist slot exists and is empty by default (`reviewers` row). Define the `pass`/`block` criteria as "reachable, attacker-controlled, control checked", so a `security` issue stays a major defect only when that bar is met. Depends on candidate 1 | S after candidate 1 |
| 3 | A `verify-fix`-style rule in `verify`: for a security fix, closed tickets, green unrelated tests and a clean rescan are not evidence; report `fixed`, `still_vulnerable` or `inconclusive` | **Adapt** | Cheap, matches `verify`'s existing "demonstrate, don't assert" rule, and needs no engine. A paragraph and a result vocabulary, not a new skill | S |
| 4 | Make `audit`'s security category and `review`'s Security bullet read the target's root and scoped `SECURITY.md` first | **Adopt** | The README states scans use it; `triage-finding` calls it the primary local definition of trust boundaries. This repo's two security touchpoints do not read it. The change is one input line in each skill | S |
| 5 | Import scanner output (SARIF, Dependabot, code scanning) as an `audit` or `capture` finding source | **Reject for now** | 20 guides and an SDK schema exist upstream, but each import needs a schema and per-scanner handling; this repo has no stated demand for a scanner and the issue does not ask for one. Reopen when a repo that uses the pipeline names a scanner | L |
| 6 | Run `cs scan` in this repo's CI | **Reject** | Needs an OpenAI key and a hosted model, costs per scan, and `AGENTS.md` keeps CI to four free offline commands. A user whose target repo wants it can use the upstream Action there | M |
| 7 | A pre-install `check-skills`-style review for third-party skills this repo vends or researches | **Adapt** | The upstream checker is itself a skill with a clear verdict set. This repo vends skills to others and reads outside skills as data by convention only. Smaller form: a section in the contributor guide, not a new skill, until a vended skill is found to carry a risk | S |
| 8 | Vendor or depend on the `codex-security` plugin | **Reject** | Hard dependency on an OpenAI account and the managed MCP server; breaks stdlib-only; the plugin is at v0.1.95 and the repository was pushed to on 2026-11-12 (API header), so it is moving fast [INFERENCE: the release cadence was not read from the changelog] | L |

Ordering if the Owner takes the adapt and adopt rows: 4, 3, then 1, then 2,
then 7. Candidates 4 and 3 change existing text only and give the most for the
least; 1 and 2 are the "skill for security" the issue asks about.

## 6. Limits of this note

- Seven of 20 skills were read for their first 45 lines only. A claim about what
  a skill does not do is not made from them.
- Nothing was run, so no claim about scan quality, false-positive rate or cost
  is made. The repository's own eval suites exist (section 1) but their results
  were not read.
- Star count and head commit are as of the API read on 2026-11-11.
