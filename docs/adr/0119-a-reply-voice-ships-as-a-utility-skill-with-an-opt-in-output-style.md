# A reply voice ships as a utility skill with an opt-in output style, never forced

- Status: provisional
- Date: 2026-10-25

Recorded by the `house-voice` feature run (`docs/features/house-voice/`),
unattended, so it is provisional. It follows ADR-0023 (utility skills),
ADR-0008 (self-contained skills), ADR-0081 (the plugin-eval tree) and
ADR-0114 (an offline scorer beside a harness suite).

A voice for the agent's replies has to hold on every turn, but this plugin
ships to every user, most of whom never asked for one. The fetched Claude
Code docs (`docs/research/house-voice-sources-2026-10-25.md`) give four
ways to make it hold: a skill, which stays in context once invoked but does
not start itself in a new session; a plugin output style, sent with every
request once a user selects it; the same style with `force-for-plugin:
true`, which applies to every user and overrides their own `outputStyle`;
and plugin hooks, which is how both community voices (ponytail, caveman)
auto-start. A CLAUDE.md line cannot be shipped by a plugin (a plugin-root
CLAUDE.md is not loaded). Two things outlive the commit. A style name, once
users put it in their settings, breaks their setup if renamed. And whether
the voice is forced is the difference between a tool a user turns on and a
behaviour change pushed to everyone.

## Decision

- The voice is the utility skill `house-voice`. Its rules, conflict table
  and exemptions live in `skills/house-voice/SKILL.md`.
- The plugin also ships `output-styles/house-voice.md` at its root (the
  default scan location, so `plugin.json` gains no field). It sets
  `keep-coding-instructions: true` and does not set `force-for-plugin`. Its
  body is a byte-for-byte copy of the skill's rules block, pinned by a test.
  The skill is the one owner, and the style is a pinned copy.
- A user opts in once, with `/output-style house-voice` or `outputStyle` in
  `~/.claude/settings.json`. Without that step the skill holds for the rest
  of a session once invoked. No hook and no shipped CLAUDE.md text.
- The voice governs the agent's own conversational replies only. Persisted
  artifacts, interviews, interface strings and any output whose form a
  loaded skill or instruction file prescribes keep their own rules.
- The offline grader `voice_grade.py` is root-only, like `decompose_grade`.
  It joins the root-only importers of `cli.py` (guarded `read_file`,
  `report`), so the dual-membership pin gains the pair
  (`voice_grade`, `cli`).

## Rejected alternatives

- **Skill alone.** It holds within a session but not across sessions, which
  is half the problem the run exists for.
- **A forced style or a hook.** It changes every user's replies on install,
  overrides a style they picked, and a hook needs a runtime that a
  harness-neutral skill (ADR-0023) cannot assume.
- **A CLAUDE.md line.** The plugin cannot ship one. A line a user adds that
  names the skill reaches the rules only if Claude decides to invoke it.
  That makes it a hint, not an activation.

## Consequences

- The style name `house-voice` is a public setting value from the first
  release. Renaming it needs a new ADR and a migration note.
- Two copies of the rules exist on disk, held equal by a test. The style
  cannot link to the skill: a style is a standalone file.
- Inside `claude plugin eval` the user's settings are absent, so the style
  cannot be measured there. The harness suite measures the skill only, and
  whether the style holds past the first turn is the Owner's hand check.
- Whether a plugin style appears under a namespaced name in `/output-style`
  is not documented on the pages fetched. The Owner's hand session confirms
  the exact name to type, and the skill text is corrected to match before
  release if it differs.
- oh-my-pi and Grok users get the skill without the style, because output
  styles are a Claude Code feature.
