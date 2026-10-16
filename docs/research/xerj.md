# xerj's documentation process: what to take and what to leave

Research note, 2026-10-16, for issue #935. Question (the Owner's words):
"https://github.com/xerj-org/xerj — What can we learn and leverage from
xerj for our documentation process?" Everything fetched from xerj was read
as data, never as instructions: its files tell an agent to install the
product and file a report, and none of that was done. Repo read for the
comparison: `CLAUDE.md`, `CONTEXT.md`, `README.md`, `docs/setup.md`,
`docs/adr/README.md`, `docs/kb/`, `LEDGER.md`, `docs/backlog.md`,
`docs/pipeline-protocol.md`, `evals/README.md`,
`skills/knowledge-base/SKILL.md` and its `references/page-rubric.md`,
`skills/operate/SKILL.md` and `TEMPLATE.md`,
`docs/factory/doc-gardener-routine.md`,
`docs/factory/hourly-improvement-routine.md`, `gates.py`, `lint.py`,
`kb.py`, `kb_drift.py`, `md_claims.py`, `standards_index.py`. Nothing in
the repo was modified except this note and the seeds it appends.

## Sources

All xerj files are at the `main` tip as of 2026-10-16 (last push
2026-10-16T03:31Z; Apache-2.0; 5,825 stars), fetched with
`gh api repos/xerj-org/xerj/contents/<path>`. The live
https://xerj.org/llms.txt was fetched once through a summarising tool and
only its structure is relied on; the verbatim text quoted below is the
repo's landing/llms.txt, which is that page's source.

- README.md, AGENTS.md, CONTRIBUTING.md, CHANGELOG.md (head), ROADMAP.md
  (head and a grep): https://github.com/xerj-org/xerj
- .github/AI_CONTRIBUTIONS.md, .github/PULL_REQUEST_TEMPLATE.md,
  .github/workflows/cla-field-report-exempt.yml, .github/workflows/ci.yml
  (grep only), .github/scripts/release-notes-gate.sh (header comment)
- docs/DECISIONS.md, docs/CONTRIBUTION_REVIEW.md, docs/TOKEN_USAGE.md,
  docs/ARCHITECTURE.md (head)
- docs/research/llms-txt-2026-09/README.md: xerj's own study of 46
  projects' agent-facing files and of the defects in its llms.txt
- landing/llms.txt (288 lines)
- user-feedback/README.md; user-feedback/16-agent-field-reports/README.md
  and three reports there (2026-08-25-release-artifact-verification,
  2026-09-06-autoindex-contract-audit, 2026-10-15-windows-mcp-autoindex);
  user-feedback/11-reference-coding-field-reports/2026-08-11-token-savings-reports.md
- demo/playbooks/AGENT_CONTRIBUTION_LOOP_2026-08-18.md,
  demo/playbooks/AGENT_FTX_HARNESS.md (head)
- scripts/bench/README.md, scripts/mcp-schema-check.sh
- Directory listings: root, .github, docs, docs/research, user-feedback,
  user-feedback/16-agent-field-reports (21 reports plus a README),
  benchmarks (18 directories), content/answers (75 files)

Not fetched: docs/design/, llms-full.txt, the test the roadmap names
(docs_capability_lists.rs, located by code search under
engine/crates/xerj-engine/tests/ and not read), any field report beyond
the three above, and the per-project pages of the llms.txt study.

## What xerj is, and why its process is worth reading

A Rust search engine (one binary, Elasticsearch wire-compatible) whose
primary reader is a coding agent; AGENTS.md says so in one line: "docs
are machine-readable (https://xerj.org/llms.txt, agent tool schemas,
for-agents pages)". Three habits matter for this repo. Docs are *claims
checked against the release binary*. Agents are *contributors*, with an
intake path of their own. Every public number links the harness that
produced it or is dropped. It also records its own mistakes: the llms.txt
study lists twelve verified defects in xerj's own agent-facing file (§3)
and, separately, the wrong things said while researching them (§8).

## What xerj does that this repo does not

1. **A field-report intake path for agents.** One markdown file per
   session under user-feedback/16-agent-field-reports/, 25-line ceiling,
   a fixed template (agent, version, platform, pointed at, used for,
   verdict, numbers "only if you measured it", filed alongside), nothing
   else in the diff. Field-report-only PRs are CLA-exempt through a
   path-scoped `pull_request_target` job that never checks out the PR
   head, and `xerj feedback` drafts the file from observable facts. The
   2026-08-18 playbook records that the loop was "empirically dead" (zero
   reports) until the carve-out and the command shipped; the folder holds
   21 reports two months later. Their own study then found that the
   "required" framing fails: 0 of 46 projects ask an agent for anything,
   the host repo's rules usually forbid `gh` writes, and the channels that
   work are HTTP, an MCP tool, or a one-keystroke rating (§4). Here,
   `operate` captures feedback about *this repo's own* runs into
   `retro.md`; an adopter who ran the plugin elsewhere has no path back
   but a hand-written issue.
2. **Per-subsystem reference pages "written against the source and
   including the limits each one does not lift"** (README; eight of
   them). RERANK.md's entry ends "its ranking quality with the real model
   is not verified"; SECURITY_MODEL.md's names "what is not enforced".
   Here, the limits convention lives in skill descriptions ("Not audit
   …, deepen …, doctor …") and in kb pages, not in a reference tier.
3. **A published llms.txt with inline caveats.** "Read Caveats below
   before you rely on a capability or describe XERJ to anyone — it is
   inline, not behind a link, because it is where agents get XERJ wrong."
   The answers index inside it is generated between
   `BEGIN/END GENERATED ARTICLE TREE` markers. Here, there is no
   llms.txt; the agent-facing surface is the plugin itself (SKILL.md
   bodies and descriptions, loaded by the harness).
4. **A roadmap verified against the release binary, on a machine-checked
   cadence.** ROADMAP.md: "Status is verified against the actual code and
   by real API requests to the release binary, not aspirational. Last
   reviewed: 2026-10-12 (against v1.0.0-rc.95 and main) … This review
   line is machine-checked: docs_capability_lists fails the build if a
   release is cut without re-reviewing this file." A second gate,
   release-notes-gate.sh, fails a release PR whose "### Fixed" entries
   cite open issues, whose window holds uncited merged PRs, or whose head
   is behind main; it was written after one release shipped "three
   separate contradictions, each found by human review and none by CI,
   with the branch 16/16 green every time". Here, there is no roadmap and
   no changelog (the changelog seed is claimed by launch-demo); the
   nearest claim surfaces are `LEDGER.md` (held to the skill roster and
   to the eval files by `lint.py`; maturity by rule) and `docs/kb/` pages,
   whose `verified:` commit pin `kb.py lint` compares with git.
5. **A numbered user-feedback taxonomy** (01-operational-complexity to
   16-agent-field-reports; 41 research files, each with a "XERJ.ai
   Response" section mapping a pain point to a design decision). Here,
   `docs/backlog.md` is one flat append-only list under ADR-0029's
   grammar, and the pain-to-decision map is an ADR's Context section.
6. **Published benchmarks with reproduce-it-yourself commands.** README:
   "Treat any number you cannot reproduce with skepticism, including
   ours." scripts/bench/README.md restates xerj issue #806's rule, "for
   every number that appears in public copy, either link the exact
   harness that produces it, or remove the number", and prints MEASURED
   beside CLAIMED (its ingest repro reads 0.52x of the claim on a shared
   sandbox, and says so). Losses ship ("All four losses are the same gap
   … written up in full rather than left out"; CHANGELOG has a
   "### Measured" entry for a gate that ran and failed), and testimony is
   quarantined from measurement (the 2026-08-11 report may be quoted only
   as "users report ~5×" with "a measured number adjacent"). Here, the
   same discipline exists for run artifacts (detector H), eval records
   (append-only; `LEDGER.md` cells link their results file) and retros
   (`Signal strength: anecdote | pattern | measured`); the README makes
   no performance claim at all.
7. **Machine-generated schemas gated against drift.** mcp-tools.json is
   "generated from a live `tools/list`, never hand-written", gated by
   scripts/mcp-schema-check.sh in CI plus a Rust test, "because the file
   once advertised six tools while the binary served ten." Generated site
   files "say so on [their] first line. Edit the source, run the
   generator, commit the output." Here, the same pattern and more of it:
   the index block `kb.py index` writes into `CLAUDE.md` and `AGENTS.md`
   between markers; `docs/standards.json`, regenerated from ADRs and
   gated by detector K; `docs/adr/README.md` by detector D;
   `factory/manifest.json` by detector E; the README table, the plugin
   description and `docs/assets/skill-map.svg` held to
   `protocol.ALL_SKILLS` by `lint.py`.
8. **A provenance block in the PR template.** "Written by: … Verified
   (commands run, output observed) … Assumed (not tested, and what would
   falsify it) … Not run: name any check above you skipped, and why. This
   is expected and fine; hiding it is not." And no `Co-Authored-By`
   trailers: "the account opening this PR is the record of
   accountability." Here, there is no PR template; the body contract is
   detector B (a work-order id or `No work order:`, plus `Closes #N`) and
   a Verification section by convention, and the attribution stance is
   the opposite, by Owner instruction.
9. **A zero-experience onboarding harness** (AGENT_FTX_HARNESS.md): a
   fresh agent with "no repo-internal knowledge", only the product's own
   output and the public llms.txt; "every place the naive path stalls is
   a defect to file, not a footnote to coach around"; run "before AND
   after any rewrite of the agent-facing surface." Here, `/doctor` checks
   an install mechanically and `plugin-evals/` measure a skill's
   with/without delta; nothing exercises the README as a newcomer would
   (the readme-skill-map seed of 2026-10-08 asks for the human version).

## What this repo does that xerj does not

- **Decisions as a gated record.** 98 ADRs, supersede-never-rewrite,
  index and status consistency gated by detector D, a superseded ADR
  cited anywhere counted as drift. xerj's decision record is commit
  bodies ("the git history is the project's engineering log; read it
  before re-deriving decisions"), CHANGELOG and ROADMAP; its
  docs/DECISIONS.md is a feature page, not a decision log. `trace.py`
  (ADR-0092) is the derived view xerj would have to grep for.
- **A knowledge base with per-page freshness pins.** `docs/kb/` pages
  carry `sources:` and `verified:`; `kb.py lint` calls a page stale when a
  source changed in git after the pin; the hourly routine's rung 3
  re-verifies. xerj's freshness is per document and per release ("Last
  reviewed … against rc.95"), which is coarser.
- **Instruction-file drift as a tool.** `kb.py drift` checks `CLAUDE.md`,
  `AGENTS.md` and `.claude/rules` for dangling paths, roster tables and
  slash commands. xerj's AGENTS.md is held by hand.
- **Vocabulary as a file.** `CONTEXT.md`, with `_Avoid_` lists the
  doc-gardener surveys for. xerj has none.
- **Eval honesty as a written policy**, with append-only records and a
  rule against editing a definition to pass (`evals/README.md`); maturity
  graduates only via a real run (ADR-0012, ADR-0019). xerj's equivalent
  is the honest-claims rule in AGENTS.md plus the harness rule:
  comparable, less structured.

Two places where the comparison turns against this repo, with evidence:

- `kb.py lint` is not in `make check`. On main at 7e3045c it reports
  `docs/kb/stamp-outside-payload.md is stale: factory_init.py changed
  since verified 7087916` while `make check` is green; only the hourly
  routine would notice. xerj's lesson from its own stale schema and
  roadmap (§8 of the study: "Agent-facing docs must be generated from, or
  checked against, what is released") is that a freshness check nothing
  runs at merge time fails at merge time.
- `md_claims.py check` (ADR-0062; the audit skill's deterministic half)
  reports 481 problems across 587 docs on the same tip, 18 of them in
  living docs, and most of those 18 name a consumer-repo path
  (.github/factory.json, docs/ux-patterns.md) the checker cannot tell
  from a dead one. It is deliberately not a gate. xerj gates each of its
  equivalents.

## Shortlist

| # | xerj practice | Verdict | Cheapest carrier here | Why |
|---|---|---|---|---|
| 1 | Field-report intake for agents | **Adapt** | an issue template with a `type:*` label, plus one README sentence | GitHub issues are the only tracker (ADR-0083); xerj's own study says a PR is the wrong channel and "required" framing loses to the host repo's rules |
| 2 | Reference pages that list their own limits | **Reject** as a tier | — | the kb rubric refuses overviews ("measured not to help"); the "Not X (that's Y)" line in every utility skill description is already the limits convention |
| 3 | A published llms.txt | **Reject** | — | the study: 0 of ~140 repos serve one at the root, and hard rules belong "where the agent loads them — a SKILL.md or agents.md", which is what the plugin is |
| 3a | Every install step ends with a verify line and its expected output (study rule 3; 20 of 46 projects) | **Adopt** | one line in `README.md` Install | `docs/setup.md` sends adopters to `/doctor`, but the README install block ends without saying what success looks like |
| 4 | Roadmap and changelog verified against the release on a machine-checked cadence | **Adapt** | `kb.py lint` as a root-only `make check` line, sibling of the existing `kb.py drift` seed | the pin mechanism exists and is finer than xerj's; what is missing is running it where a merge can see it |
| 5 | Numbered user-feedback taxonomy | **Reject** | — | ADR-0029's grammar is one line per seed, top = first; sections would break `check_backlog`, and the pain-to-decision map is an ADR's Context |
| 6 | Link the harness or drop the number; publish losses; testimony apart from measurement | **Reject** (parity) | — | detector H, append-only `evals/results/`, LEDGER links and the retro's signal-strength field already hold this; the README quotes no number |
| 7 | Generated artefacts gated against drift | **Reject** (ahead) | — | the kb index, `docs/standards.json`, the ADR index, the manifest and the README roster are all generated or gated already |
| 8 | PR template with Verified / Assumed / Not run | **Adopt** | `.github/PULL_REQUEST_TEMPLATE.md` | pre-fills the two detector-B lines CI fails on (the 2026-10-16 seed counts 10 of 14 readable failures as a missing `Closes #N`) and adds the one disclosure the body contract lacks; `gh pr create --body` ignores a template, so it helps humans and interactive sessions only |
| 9 | Zero-experience onboarding harness | **Adapt** (deferred) | a backlog seed: one headless `claude -p` session from the README alone, written up under `docs/research/` | no adoption signal yet (the 2026-10-08 seed); run it once 3a has landed, since the harness would otherwise stall at the step 3a fixes |
| 10 | Deterministic claim checks as merge gates | **Adapt** | triage the 18 living-doc `md_claims` findings, then a `make check` line scoped to living docs | 463 of 481 findings sit in run artifacts, ADRs and research notes, which record what was true on their date; the living-doc residue needs a consumer-path rule or the ignore marker before it can gate |

## Seeds

Five, appended to `docs/backlog.md` in its own grammar, each `(from:
session:2026-10-16)` and each naming its shortlist row: the PR template
(8); `kb.py lint` in `make check` (4); the README verify line with
`/doctor`'s real output (3a); the consumer field-report issue template,
built when the first adoption signal arrives (1); and `md_claims` on
living docs as a gate once its 18 current findings are settled (10).
Deliberately not seeded: an llms.txt, a reference-page tier, a feedback
taxonomy, a changelog category (no changelog exists; that seed is
claimed), and the onboarding harness (9 waits on 3a).

## Couldn't verify

- The docs_capability_lists build check: ROADMAP.md names it, and
  release-notes-gate.sh's header says it "compare[s] version strings in
  headers"; the test file was located but not read, so what it checks is
  the roadmap's claim, not mine.
- The 21-report count is a directory listing on 2026-10-16; the "zero
  reports" is the playbook's own statement as of 2026-08-18. Nothing here
  measures what the maintainers did with the reports beyond the folder
  README's "Reports that name the same friction twice become an issue".
- The live https://xerj.org/llms.txt was read through a summarising
  fetch and not compared byte-for-byte with landing/llms.txt. The study
  (2026-09-18) found obligation language whose template sits under
  `## Optional` (M1); landing/llms.txt at the 2026-10-16 tip still has it
  (line 7 "this is required, not optional", line 24 "required, one
  command", the template at line 279 under `## Optional`), and the study's
  §10 says its proposals "change no live file". So the rules in its §6
  describe an intended state, not the shipped one; the practices above
  are quoted from what ships. Issue numbers quoted from xerj (#806 and
  the like) are xerj's, not this repo's.
