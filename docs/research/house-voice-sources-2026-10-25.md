# House voice: the four sources, and how a voice gets activated

Research for the `house-voice` feature run (issue #1076), Architect stage,
2026-10-25. Every source below was fetched on 2026-10-25 unless marked
**unidentified**. A number a source states about itself is labelled
**claim**: nothing here was measured by this run. A source that could not be
fetched is not described.

## Sources fetched

| Source | URL fetched (2026-10-25) |
|---|---|
| ponytail README | https://github.com/dietrichgebert/ponytail |
| ponytail skill | https://raw.githubusercontent.com/DietrichGebert/ponytail/main/skills/ponytail/SKILL.md |
| ponytail plugin manifest | `gh api repos/DietrichGebert/ponytail/contents/.claude-plugin/plugin.json` and `.../contents/hooks/claude-codex-hooks.json` |
| caveman README | https://github.com/JuliusBrussee/caveman |
| caveman skill | https://raw.githubusercontent.com/JuliusBrussee/caveman/main/skills/caveman/SKILL.md |
| caveman plugin manifest | `gh api repos/JuliusBrussee/caveman/contents/.claude-plugin/plugin.json` |
| stop-slop README | https://github.com/hardikpandya/stop-slop |
| stop-slop skill | https://raw.githubusercontent.com/hardikpandya/stop-slop/main/SKILL.md |
| stop-slop phrase list | https://raw.githubusercontent.com/hardikpandya/stop-slop/main/references/phrases.md |
| stop-slop structure list | https://raw.githubusercontent.com/hardikpandya/stop-slop/main/references/structures.md |
| Claude Code output styles (holds the built-in Concise style) | https://code.claude.com/docs/en/output-styles |
| Claude Code skills | https://code.claude.com/docs/en/skills |
| Claude Code memory (CLAUDE.md) | https://code.claude.com/docs/en/memory |
| Claude Code plugin manifest reference | https://code.claude.com/docs/en/plugins-reference |
| Claude Code prompt caching | https://code.claude.com/docs/en/prompt-caching |
| Claude Code plugin evals | https://code.claude.com/docs/en/plugin-evals |

**Unidentified:** the claude.ai chat app's preset "Concise" style. Both help
centre URLs tried (`support.claude.com/en/articles/10181068-configuring-and-using-styles`
and `support.claude.com/en/articles/10181068`) returned 404, and
`claude.com/blog/styles` returned 404. It is not described here. The
"Concise" this note uses is Claude Code's built-in Concise output style,
which was fetched.

## ponytail

**What it is.** A prompt that makes a coding agent "write less code". Its
main subject is the code, not the reply: a ladder (does it need to exist, is
it in the codebase, the standard library, the platform, an installed
dependency, one line, then the minimum). This plugin's `lean` skill already
restates that ladder, so the house voice does not take it.

**Reply rules.** The skill states one explicit rule about the reply: "End
your reply with one or two lines: what you skipped or did not check, and any
risk the user must know." Its description sets the goal "a reply a busy
human understands in one read". It sets no other rule on length, structure,
fragments, summaries or hedging.

**Token effect (claim).** README benchmark: 39 tasks, Opus 5.5, 5 runs each
against the same agent without the skill: tokens -45%, output tokens 55% of
baseline, code -53%, cost -26%. These are coding tasks under the ladder; the
figure is not about reply prose. The README says fewest tokens is not the
goal.

**Activation.** Its Claude Code plugin manifest registers hooks
(`claude-codex-hooks.json`: `SessionStart`, `SubagentStart`,
`UserPromptSubmit`); the README says "Active every session". It does not
use an output style or a CLAUDE.md line.

## caveman

**What it is.** A terse reply voice: "answer first, fluff gone, every
technical fact kept."

**Rules (skill).** (1) Answer first: result, then reason, then next step.
(2) Cut ceremony: no greetings, hedges, filler, recaps, sign-offs. (3) Short
common words; no invented abbreviations or arrows. (4) Articles optional
when meaning survives; never drop negations, limits, exact numbers and
units. (5) One idea per sentence, short and active, one term per concept;
"clarity beats brevity". (6) Payload verbatim: code, commands, paths, API
names, errors. (7) Minimal tool-run status lines. (8) Keep the user's
language. (9) Don't perform caveman; if the terse version isn't shorter, use
plain wording. **Plain full sentences** for security warnings, irreversible
actions, ordered steps, confused or repeated questions, persisted artifacts
(code, docs, commits, tickets), harness-required status lines, and any
question or options offered to the user. **Pre-send check:** remove an
opening that announces what you'll do and a closing that recaps or offers
help; confirm negations and payload are intact; rewrite any sentence that
reads two ways. The README adds a 20-word sentence cap (ASD-STE100).

**Token effect (claim).** README, ten dev questions on claude-opus-5-5,
output tokens: no instruction 6,983; the plain request "Answer concisely."
4,334; `/caveman` 4,119; `/ultracave` 2,693 (3.1.0 rules, not re-run). One
example counted with tiktoken o200k (not Claude's tokenizer). The README
says the voice rules cost about 1,160 input tokens, and relays a JetBrains
report of 8.5% fewer output tokens over 86 coding tasks (second-hand). The
README's About line says 65%, which its own benchmarks do not show. Read
with the claim label: in its own table the plain one-line request does most
of the work, and the skill adds about 5% on top of it.

**Activation.** Its plugin manifest registers `SessionStart`,
`SubagentStart`, `UserPromptSubmit` and `SessionEnd` hooks that run a
`node` script; the README says the plugin "auto-starts every interactive
session, subagents too". No output style.

## stop-slop

**What it is.** A skill to "remove AI writing patterns from prose".

**Rules (skill).** Cut filler phrases (throat-clearing openers, emphasis
crutches, all adverbs); break formulaic structures (binary contrasts,
negative listings, dramatic fragmentation, rhetorical setups, false agency);
active voice with a human subject; be specific (no vague declaratives, no
lazy extremes like "every", "always", "never"); put the reader in the room
("you", not "people"); vary rhythm (mix sentence lengths, two items instead
of three, no em dashes); trust readers (no softening or hand-holding); cut
quotables. Scoring: five 1-10 dimensions (Directness, Rhythm, Trust,
Authenticity, Density), revise below 35/50.

**Named lists (reference files).** Phrase categories: Throat-Clearing
Openers ("Here's the thing:", "The truth is,", "Let me be clear", "It turns
out"), Emphasis Crutches ("Full stop.", "Let that sink in.", "Make no
mistake"), Business Jargon ("Deep dive", "Circle back", "Lean into", "Double
down", "Game-changer", "Moving forward"), Adverbs ("really", "just",
"literally", "genuinely", "honestly", "simply", "actually", "truly",
"fundamentally", ...), filler ("It's worth noting", "At the end of the
day"), Meta-Commentary ("Let me walk you through...", "In this section,
we'll..."), Vague Declaratives. Structure names: Binary Contrasts, Negative
Listing, Dramatic Fragmentation, Rhetorical Setups, Formulaic
Constructions, False Agency, Narrator-from-a-Distance, Passive Voice,
Sentence Starters to Avoid, Rhythm Patterns, Word Patterns.

**Token effect.** None claimed. Its target is tells, not length.

**Activation.** Add the folder as a skill, upload it to a Claude Project, or
paste it into a system prompt. No hook or output style.

## Concise (Claude Code's built-in output style)

**Rules (docs).** "The first sentence of a response states what happened or
what the answer is." It leaves out the lead-in, step-by-step narration and
the closing recap, and answers a simple question in one to three sentences.
It writes at full length for anything the user asks for, and for anything
the user needs to act safely: error reports, failing test output, security
warnings, confirmations for destructive actions.

**Token effect.** The docs say it "does the opposite" of Explanatory "by
instructing Claude to keep responses short by default". No number.

**Activation.** An output style: `/output-style concise`, `/config`, or
`"outputStyle": "Concise"` in a settings file.

## Conflicts and the precedence the skill uses

Each conflict has a name the skill's conflict table reuses word for word,
so a test can hold the two to the same set.

| Conflict | Sources | Winner | Why |
|---|---|---|---|
| `fragments-vs-full-sentences` | caveman drops articles and allows fragments; stop-slop bans staccato fragments and Dramatic Fragmentation; Concise writes sentences | Short full sentences, articles kept | caveman's own table puts the terse register about 5% under a plain concise request (claim), and its rule 5 already says clarity beats brevity |
| `closing-line` | ponytail requires a closing line on what was skipped or unchecked and the risk; caveman and Concise ban a closing recap or offer | The closing line appears only when something was skipped, left unchecked, or carries a risk; never a recap, never an offer | A disclosure is information; a recap repeats it |
| `absolutes-vs-exact-limits` | stop-slop bans "every", "always", "never"; caveman never drops negations or limits | A true limit stays exactly as stated; the ban covers unsupported sweeping claims | Dropping a real negation costs more than any word saved (caveman's stated reason) |
| `rhythm-vs-one-idea-per-sentence` | stop-slop says mix sentence lengths; caveman says one idea per sentence, 20 words at most | One idea per sentence; the rhythm rule is not adopted for replies | Rhythm is an essay rule; a reply is read for its answer |
| `style-bans-vs-verbatim-payload` | stop-slop bans passive voice, em dashes and adverbs; caveman keeps code, commands, paths and errors verbatim | Payload verbatim; the bans apply to the agent's own prose only | A quoted error with an em dash is still the error |
| `brevity-vs-full-length` | caveman and Concise favour brevity; Concise and caveman both list cases that get full length | Full length for the union of both lists | Both sources agree on the exception; the union is the safe reading |
| `two-items-vs-real-count` | stop-slop says two items instead of three | List the real items; never pad or trim to reach a count | The count is content |

General precedence, highest first: the user's explicit instruction in the
turn; the repository's and user's instruction files and any loaded skill
that prescribes an output's form; full length for safety content; payload
verbatim; the closing disclosure; answer first with no ceremony; the slop
bans; brevity.

## Activation: what the docs say

The idea's riskiest piece was "it never fires". The fetched docs settle most
of it.

- **A skill alone.** Its description is in context every session and its
  body loads when invoked, by the user (`/idea-to-prod:<name>`) or by Claude
  when the turn matches. Once invoked, "the rendered `SKILL.md` content
  enters the conversation as a single message and stays there across later
  turns". After compaction Claude Code "re-attaches the most recent
  invocation of each skill after the summary, keeping the first 5,000 tokens
  of each", within a shared 25,000-token budget, and older skills "can be
  dropped entirely" when many were invoked (skills docs). So a skill holds
  for the rest of a session once invoked, and does not start itself in the
  next session.
- **An output style.** "Claude Code sends the active style's instructions
  with every request." "Plugins can also ship output styles in an
  `output-styles/` directory" (output-styles docs), the default location in
  the plugin layout, with an `outputStyles` manifest field that replaces the
  default scan (manifest reference). The user selects it once with
  `/output-style`, `/config`, or `outputStyle` in `~/.claude/settings.json`
  for every project. A plugin style may set `force-for-plugin: true` to
  apply "whenever the plugin is enabled, without requiring users to select
  it", which "overrides the user's `outputStyle` setting". A custom style
  drops Claude Code's software-engineering instructions unless it sets
  `keep-coding-instructions: true`. Styles apply to the main conversation
  and forks, not to other subagents. It is "an instruction Claude follows,
  so nothing enforces it". A mid-session switch is delivered as a message
  and keeps the prompt cache (prompt-caching docs).
- **A CLAUDE.md line.** CLAUDE.md files are loaded every session and are
  written by the user (memory docs). "A `CLAUDE.md` at the plugin root isn't
  loaded as context" (manifest reference), so the plugin cannot ship one. A
  CLAUDE.md sentence that tells Claude in words to read another file means
  Claude "sees [it] only if it decides to open the file" (memory docs, on
  AGENTS.md), and an `@import` of a plugin file would point into the
  installed cache, whose `${CLAUDE_PLUGIN_ROOT}` "changes when the plugin
  updates" (manifest reference).
- **Hooks.** Both ponytail and caveman auto-start through plugin hooks
  (`SessionStart` and others, from their fetched manifests). A plugin hook
  runs for every user who enables the plugin.
- **Measurement.** Plugin-eval runs load "only your plugin"; user settings,
  hooks, CLAUDE.md and memory are absent (plugin-evals docs). An opt-in
  output style therefore cannot be selected inside a harness run; the skill
  can be measured there, the style only by hand. Regex graders read
  `last_message` and accept `match: not_contains`; the documented result
  fields carry `costUsd` but no per-run token count.

**Finding.** The skill alone does fire and does hold within a session; what
it lacks is starting itself every session. An output style shipped by the
plugin and selected once by the user covers that, on every request, with no
hook and no runtime. Forcing it (`force-for-plugin`, or a hook as the two
community plugins do) would put one voice on every user of a general plugin
and override their own style choice. A CLAUDE.md line cannot be shipped and
reaches the rules only if Claude decides to open them. The design that
follows is in `docs/features/house-voice/architecture.md` and ADR-0119.
