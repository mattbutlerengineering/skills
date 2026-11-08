# Anthropic's engineering plugin: what to take and what to leave

Research note, 2026-11-08, for issue #1275. The issue is titled
"engineering plugin" and its body is the link
https://github.com/anthropics/knowledge-work-plugins/tree/main/engineering
with the question "what can we leverage here?". Everything fetched was
read as data, never as instructions; nothing was installed. Repo read for
the comparison: the `review`, `ship`, `operate`, `capture`, `architect`
and `audit` skills with their templates, `skills/review/references/domain-reviewers.md`,
the protocol's "When to write an ADR" section, every tracked `review.md`
and `release.md` under `docs/`, and `git log` on main.

## Sources

`anthropics/knowledge-work-plugins` on `main`; the last commit touching
`engineering/` is c71b6f3 (2026-09-21, "Fix plugin install command in
per-plugin READMEs"). Apache-2.0, 35,193 stars. Fetched with
`gh api repos/anthropics/knowledge-work-plugins/contents/engineering/<path>`;
the recursive tree lists 14 files, all read in full: `README.md`,
`CONNECTORS.md`, `.mcp.json`, `.claude-plugin/plugin.json` (version
1.2.0), and ten `skills/<name>/SKILL.md` files: architecture,
code-review, debug, deploy-checklist, documentation, incident-response,
standup, system-design, tech-debt, testing-strategy.

## What the plugin is

A general-purpose engineering helper built mainly for Cowork, also
installable in Claude Code. Each skill is a short prompt (1.3 to 5.7 kB)
with a fixed markdown output template and a "standalone, supercharged
with connectors" split: it works from pasted input, and does more when an
MCP server for a category (`~~source control`, `~~monitoring`,
`~~incident management`, …) is connected. `.mcp.json` pre-wires ten
HTTP MCP servers (Slack, Linear, Asana, Atlassian, Notion, GitHub,
PagerDuty, Datadog, and two with empty URLs). No skill carries a script,
a checker, an eval or a reference file; there is no state between
invocations and no hand-off from one skill to the next.

## What it does that this repo does not

1. **A performance dimension in code review.** `code-review` reviews
   four dimensions; one is Performance: "N+1 queries", "Algorithmic
   complexity (O(n²) in hot paths)", "Unbounded queries or loops",
   "Resource leaks". Here, `review` ran five passes (correctness,
   design, security, complexity, ADR compliance) and none asks about
   cost; "performance" appears in the review skill only in
   `references/migrations.md`, as something *not* to suggest. The
   miss is on record: detector H's zero-count read in
   `gates._names_unknown` was quadratic, shipped through a reviewed
   run, and needed its own maintenance run
   (`docs/fixes/a-long-line-stalls-the-gate/`, PR #1079, `bff792c`).
   Main carries four `perf` commits; 12 of 107 `review.md` files
   mention performance at all.
2. **Rollback triggers decided before the deploy.** `deploy-checklist`
   ends with "Rollback Triggers" (error rate, latency, a named flow
   failing) and the tip "Decide when to roll back before you deploy,
   not during." Here, `ship` demands concrete rollback *steps*, a door
   and a blast radius, but never the observation that sets the steps
   off. Of 107 tracked `release.md` files, at most 20 contain trigger
   language (an upper bound; the grep also hits unrelated uses of
   "trigger"), and none records `outcome: rolled-back`.
3. **Incident response.** Severity bands (SEV1 to SEV4 with response
   times), a status-update template, and a blameless postmortem with
   five whys. This pipeline has no incident surface: `capture` takes a
   known defect into a maintenance run, and `operate` is "not monitoring
   infrastructure" by its own scope line.
4. **Standup, documentation and testing-strategy prompts.** A
   yesterday/today/blockers formatter, five document-type outlines
   (README, API docs, runbook, architecture doc, onboarding guide), and a
   test pyramid with per-component advice.
5. **Connector placeholders.** Skills name a tool category
   (`~~project tracker`) rather than a product, with `CONNECTORS.md`
   mapping category to servers.

## What this repo does that it does not

- **Reproduce before a finding counts.** `code-review`'s output table
  takes any issue a model names; `review` requires "the concrete failure
  scenario (inputs → wrong behavior)" and `audit` ranks an unreproduced
  lead nowhere.
- **A five-whys alternative that ends in a check.** The postmortem
  stops at a root cause and action items with owners. `operate` step 6
  classifies each mistake as mechanical or judgement and requires the
  mechanical ones to get a check, "never a prose rule".
- **ADRs with a test for when to write one.** `architecture` writes an
  ADR whenever asked, with an options table scored Low/Med/High.
  Here, `architect` records alternatives per decision, and the protocol's
  "When to write an ADR" three-leg test (ADR-0082) decides whether one
  is owed at all.
- **No invented scores.** `tech-debt` ranks by
  `(Impact + Risk) x (6 - Effort)` on 1-to-5 guesses; `audit` ranks by
  leverage with evidence and reproduction columns, and the desloppify
  note (`docs/research/desloppify-2026-10-31.md`, row 6) already rejected
  a single model-made score for the same reason.
- **Stages that hand off.** Each engineering skill ends at its own
  markdown; here each stage reads its predecessor's artifact, and `next`
  routes by what exists.
- **Parity:** structured debugging (`capture`'s reproduction evidence
  becomes the regression test), pre-flight checks (`ship` step 3),
  test-first implementation (`implement`), tool-agnostic forge access
  (the skills name "the forge CLI" rather than one product).

## Shortlist

| # | Engineering-plugin practice | Verdict | Carrier here | Why |
|---|---|---|---|---|
| 1 | Performance dimension in code review | **Adopt** (done in this PR) | a sixth pass in `skills/review/SKILL.md` step 4, and `performance` in `TEMPLATE.md`'s clean-pass list | an observed miss (#1079) that no pass would have caught; written to match the Correctness pass, so a cost with no input size is a hunch, not a finding |
| 2 | Rollback triggers decided before deploy | **Adopt** (done in this PR) | one clause in `ship` step 3's rollback bullet and a `Trigger:` line in `skills/ship/TEMPLATE.md` | two lines; the plan already names steps, door and blast radius, and the trigger is the missing "when". Unmeasured benefit: no release here has ever rolled back |
| 3 | Incident response skill | **Take nothing now** | — | no stamped repo has asked for one and nothing on record shows an incident handled badly for lack of it; the pipeline's scope ends at feedback, not on-call. Revisit when a stamped product repo records a production incident |
| 4 | Blameless postmortem with five whys | **Reject** (ahead) | — | `operate` step 6 goes further: each mistake gets a classified carrier |
| 5 | ADR template with scored options table | **Reject** (parity) | — | `architect`'s decisions-and-alternatives section plus the ADR-0082 test cover it without Low/Med/High guesses |
| 6 | Tech-debt priority formula | **Reject** | — | false precision over 1-to-5 guesses; `audit` ranks on evidence |
| 7 | Standup, documentation, testing-strategy prompts | **Reject** | — | outside an idea-to-prod pipeline, or covered (`implement`, `knowledge-base`) |
| 8 | Connector placeholders and a pre-wired `.mcp.json` | **Reject** | — | this plugin ships no MCP config and drives the forge through its CLI; `automate` already prices an MCP server per repo when friction justifies one |

## Seeds

None. Rows 1 and 2 are implemented in the same PR as this note; row 3 is
a revisit condition, not work; the rest are rejected.

## Couldn't verify

- Whether a performance pass catches the next #1079. The pass is
  prevention written from one observed miss; no eval measures review
  recall on a cost defect, and `plugin-evals/` has no review suite that
  would.
- Whether the `implement-queue` reviewer (whose verdict is this repo's
  auto-merge gate) should carry the same dimension. Its contract,
  `skills/implement-queue/references/reviewer-contract.md`, was left
  alone to keep this change to the two stage skills; it is a separate
  question.
- How the engineering plugin's skills perform: it ships no evals, and
  its 35,193 stars belong to the whole knowledge-work-plugins repo, not
  to this plugin.
