---
name: ux-writing
description: Use when the words in a product's interface need auditing, rewriting or writing — "audit our copy", "our error messages are useless", "make the microcopy consistent", "write the empty states", "what should this button say", "do we call it a workspace or a project", "set up a voice and tone guide", "check the strings before we translate". It finds the user-facing strings in the code, grades them against a UX-writing rubric and the project's own voice and terms, proposes rewrites as a reviewable table, and applies only the ones approved. It changes wording, never facts, and never invents product claims. A visual pass on one screen is polish, whose copy move is the light version of this; designing flows and screens is ux-design; behaviour patterns such as how the product confirms, loads or validates are ux-patterns; reviewing code for defects is review. Owns no run artifact and is never routed to.
---

# UX Writing

Make the words in an interface do their job: tell people where they are,
what will happen, what went wrong and what to do next — in one voice,
with one name for each thing, across every screen.

Left alone, interface copy is written one string at a time by whoever
built the screen. Each string is defensible; together they call one
thing three names, apologise in four tones, and end half the buttons in
"Submit". This skill works on the strings as a set, which is why it
inventories them before it judges any of them.

This is not a stage in the lifecycle pipeline and it owns no run
artifact. It may write one project-level file section — **Voice & terms**
in `docs/ux-patterns.md` — which the `ux-patterns` skill shares and
whose other sections it owns. It works in a repo that has never heard of
the pipeline.

| Mode | The ask | What it does |
|---|---|---|
| **audit** | "Audit our copy", "are these errors any good" | Steps 1 to 3. Findings only, nothing edited |
| **rewrite** | "Fix the error messages", "make it consistent" | Steps 1 to 7 |
| **voice** | "Set up a voice guide", "workspace or project?" | Steps 1 and 2, then writes Voice & terms |
| **write** | "Write the empty states for this flow" | Steps 1, 4 to 7, drafting strings that do not exist yet |

One mode per pass. When the ask names none, run **audit** and propose
the next mode it supports.

## Process

### 1. Find what is already decided

- **Voice and terms.** If `docs/ux-patterns.md` exists, read its
  **Voice & terms** section: the voice chart, the glossary, the
  mechanics (capitalisation, person, numbers and dates). Those decisions
  outrank this skill's taste.
- **Audience and stakes.** Inside a run, `prd.md` and `ux.md`. Outside
  one, the README and the product's own copy.
- **No voice written down?** In **voice** mode, or when the audit needs
  one, draft a voice chart from the copy that already exists, using
  [`references/voice-and-terms.md`](references/voice-and-terms.md). Ask
  only for the judgement calls the copy cannot answer, one question at a
  time, with your recommendation first. In other modes, state the voice
  you inferred in the report's first lines and go on.

### 2. Inventory the strings

Find them mechanically — a search, not a stroll through the screens you
happen to open:

- i18n catalogues: `*.json` message files, `*.po`, `*.ftl`, `*.strings`,
  `*.arb`, `messages/`, `locales/`.
- Text in templates and components: JSX/TSX text nodes, and the
  `aria-label`, `title`, `placeholder` and `alt` attributes.
- Toast, notify and alert calls; error messages that reach the screen;
  validation-schema messages; email and notification templates.

Group what you find by **job**: action, label, helper, error, empty,
loading, success, confirmation, notification, navigation, accessible
name. Keep the file and line of each. Scope to a surface or a flow when
the ask names one; a whole-repo inventory is capped and sampled, and the
report says so.

### 3. Audit against the rubric

Two layers, in this order:

- **Each string** against the four standards — purposeful, concise,
  conversational, clear — and the checks for its job, in
  [`references/rubric.md`](references/rubric.md) and
  [`references/patterns.md`](references/patterns.md). A message about
  a state reads in this order: **the fact the person needs now, the next
  action, then any context that changes their decision.**
- **Across strings**: one name per concept on every surface, one
  capitalisation style, one person ("you" or "we"), and a tone matched
  to the stakes — payment, deletion and lost access are never jokey.

Read each string **in place**, with its heading, body and buttons
together; a button is judged by the question above it. Each finding
names the string, its file and line, the rule it breaks, and what it
costs the person reading it. Rank by that cost.

Interface tells such as claim adjectives, "Get started" on every button
and invented proof are listed in the **Copy** section of the polish
skill's tells; check them there rather than restating them here.

### 4. Propose rewrites

A table, so the owner can approve line by line:

| Location | Job | Current | Proposed | Rule | Note |
|---|---|---|---|---|---|

- **Facts are not wording.** Anything touching a product claim, legal
  meaning, pricing, a number, or a domain term is marked
  **needs-owner** and left as it is. Never rewrite it silently.
- **A glossary change is one decision**, not many edits: "Workspace →
  Project, 23 occurrences", approved once.
- In **write** mode the Current column is empty, and the state each
  string serves comes from `ux.md` or the user.

### 5. Apply only what was approved

- Edit the catalogue or the source, wherever the string lives.
- Keep it safe to translate: whole sentences, interpolation variables
  intact, plurals through the i18n library, no fragments glued together
  — [`references/i18n-a11y.md`](references/i18n-a11y.md).
- Update tests that assert on the old wording.
- If a decision was made — a term, a capitalisation rule, a voice
  trait — write it into **Voice & terms** in `docs/ux-patterns.md`.
  Create the file with only that section if it does not exist yet;
  never edit its other sections, which belong to `ux-patterns`.

### 6. Look at it

Render the changed surfaces and read them there: a long name in every
variable, the plural and the singular, a narrow width, 200% zoom. A
rewrite that is right in the catalogue and clipped on the screen is not
done. If the surface cannot be rendered, the report's first line says
so, and everything after it is a reading of the code.

### 7. Report, and hand off what is not yours

What changed and why, in the reader's terms; what was left as
**needs-owner**; what could not be verified.

- **A flow problem** — the copy is confusing because the step is in the
  wrong place — goes to `ux-design` inside a run, or to the user.
- **A missing state** — no empty state exists to write for — is polish's
  `states` move.
- **A behaviour inconsistency** — one screen confirms deletion, another
  offers undo — is `ux-patterns`.
- **A defect in the code** goes to `review`. Later work becomes a
  backlog seed or a maintenance run via `capture`; this skill never
  writes the backlog itself.

## Rules

- The project's written voice and terms win, then the user's direction,
  then this skill's taste.
- Inventory before judging. One string at a time is how the drift got
  there.
- Change wording, never facts. Claims, legal meaning, prices and numbers
  are **needs-owner**.
- Nothing is applied without approval; **audit** edits nothing.
- Translator-safe or not at all: no concatenated fragments, no
  hand-rolled plurals.
- Look at the rendered result. If you could not, say so before anything
  else.
- Only the **Voice & terms** section of `docs/ux-patterns.md` is this
  skill's to write.

The four standards and the voice chart are Torrey Podmajersky's, from
*Strategic Writing for UX*; the error-message checks follow Nielsen
Norman Group. The message order for states, the read along the whole
interaction path, and the verify list restate ideas from Impeccable's
`clarify` command ([pbakaus/impeccable](https://github.com/pbakaus/impeccable),
Apache-2.0) in this pipeline's terms, without copying its text. Each
reference file names its sources.
