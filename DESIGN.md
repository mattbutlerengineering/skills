# Design decisions

Outcome of the initial design interview (2026-07-01). Status per decision:
**locked** (explicitly confirmed) or **provisional** (recommended answer
adopted while awaiting confirmation — pivot freely).

See [CONTEXT.md](./CONTEXT.md) for the canonical vocabulary.

## Locked

1. **Spine: lifecycle pipeline.** The repo is organized as an ordered
   sequence of stages from idea to production; each stage's skill produces an
   artifact the next stage consumes. ai-tooling's COMPARISON.md inspired the
   stage taxonomy, not the table format.

2. **Stages:** Idea → PRD → UX Design (conditional) → Architect → Decompose →
   Implement → Verify → Review → Ship → Operate.
   - UX Design is conditional: skipped when the work has no user-facing
     surface; the decision depends on the feature, not the project.
   - Architect = technical design only (architecture, data model, stack,
     ADRs). Decompose = work breakdown only (milestones, issues, sequencing).
     The names deliberately avoid "design" and "plan", which are ambiguous.

3. **Two run scales.** A *product run* takes a greenfield product through the
   full pipeline; artifacts live at the target repo's docs root. A *feature
   run* is a scaled-down pass re-entering at Idea or PRD; artifacts live under
   `docs/features/<slug>/`.

4. **Artifacts are the state.** No manifest or state file. A skill orients by
   checking which artifacts exist in the run's directory. A skipped
   conditional stage is recorded in the next artifact's frontmatter
   (e.g. `ux: skipped — no UI surface`) so absence is never ambiguous.

5. **Soft gating.** When a predecessor artifact is missing, the skill names
   the gap and offers either a quick backfill interview for a minimal version
   of the missing artifact, or to proceed with assumptions logged in its own
   artifact. Never hard-blocks.

6. **Plugin from day one.** The repo is structured as an installable Claude
   Code plugin (plugin.json + skills/) — no retrofit, no sync scripts, one
   canonical location.

7. **Claude Code is the only target harness for now.** opencode/pi are
   possible later but not soon. Skill *content* stays harness-neutral;
   Claude-Code-isms are confined to the packaging layer so a future port is
   cheap.

8. **Skills are self-contained.** Pure prompts/process — no hard dependency
   on any third-party tool, MCP server, or plugin. External tools may be
   mentioned as optional enrichment ("if you have playwright…"), but every
   skill works on a bare Claude Code install.

## Provisional (recommended answers adopted, unconfirmed)

9. **Audience: you first, publishable always.** Built for personal daily use,
   but written as if a stranger installs it tomorrow — no references to a
   specific machine, repo, or private tooling.

10. **Invocation: stage skills + thin router.** Every stage is its own
    directly-invocable skill (/prd, /architect, …). A thin router skill
    (/next) reads artifact state and hands off to the right stage skill.
    Mid-stream entry stays natural; the guided journey exists for those who
    want it.

11. **Skill style: interview early, draft late.** Front-end stages (Idea,
    PRD, UX Design) interview relentlessly — the knowledge is in the user's
    head. Architect onward drafts first from upstream artifacts and the
    codebase, then asks only about genuine trade-offs.

12. **Self-evaluation: lightweight ledger.** One LEDGER.md tracking each
    skill's maturity (draft / used-once / battle-tested) with a line of
    evidence per entry. No verdict vocabulary or audit scripts until the
    ledger demonstrably drifts.

## Resolved at scaffold time (2026-07-01, provisional where noted)

13. **Plugin name: `idea-to-prod`** (provisional — picked at scaffold time;
    repo stays `skills`, marketplace name `skills`). Descriptive,
    collision-proof, matches the PRD's framing.

14. **License: MIT** — matching the adoption bar applied to others' tools.

15. **Templates: yes.** Every artifact-producing stage ships a TEMPLATE.md in
    its skill directory; downstream skills orient on template structure.

16. **Operate scope: feedback capture + retrospective + idea seeds.** No
    monitoring infrastructure. The retro artifact completes the run.

17. **Conditional-UX mechanics refined:** whether UX Design applies is
    decided at PRD time and recorded as `ux: required | not-applicable` in
    prd.md frontmatter; Architect echoes a skip into architecture.md
    frontmatter per decision 4. This keeps orientation unambiguous between
    "skipped" and "not yet done".

18. **Git bootstrap: done.** Private repo `mattbutlerengineering/skills`,
    PRD is issue #1 (`ready-for-agent`).
