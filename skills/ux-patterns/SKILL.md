---
name: ux-patterns
description: Use when a product's interface behaves differently from screen to screen and the ask is to define how it should behave, once, for the whole project — "make our UX consistent", "write down our UX patterns", "one screen confirms delete and another offers undo", "how should we handle loading, errors and empty states everywhere", "every form validates differently", "set up interaction guidelines for this app", "check these screens follow our patterns". It derives the patterns the code already uses into a project file, docs/ux-patterns.md, asking the owner only the judgement calls, then audits screens against it and reports each deviation as a fix or a candidate rule. Behaviour, not looks or words — visual polish of one screen is polish, the wording and voice of strings is ux-writing, designing a run's flows and screens is ux-design, and a code-defect sweep is audit. Owns no run artifact and is never routed to.
---

# UX Patterns

Decide how the product behaves — how it confirms, undoes, loads,
validates, fails, empties, navigates and takes the keyboard — once, for
the whole project, and then hold every screen to it.

Left alone, each screen answers those questions on its own, the way its
author did last time. Each answer is reasonable; together they teach the
person using the product that nothing can be predicted. Consistency is
the usability heuristic nobody owns, because no single screen breaks it.
This skill owns it, by writing the answers down where the next screen's
author will read them.

This is not a stage in the lifecycle pipeline and it owns no run
artifact. It writes one **project-level** file, `docs/ux-patterns.md`,
which lives outside every run and outlasts them. It owns every section
of that file except **Voice & terms**, which belongs to the
`ux-writing` skill. `polish` and `ux-design` read the file before they
work. It works in a repo that has never heard of the pipeline.

| Mode | The ask | What it does |
|---|---|---|
| **extract** | "Write down our patterns", no file yet | Steps 1 to 4: derive, confirm, write |
| **audit** | "Do these screens follow our patterns?" | Steps 1 and 5. Findings only, nothing edited |
| **decide** | "Should deletes confirm or undo?" | One section of steps 2 to 4, for one question |

One mode per pass. When there is no file yet and the ask is an audit,
**extract** first: an audit against rules nobody wrote down is a
critique of taste.

## Process

### 1. Read what exists

- `docs/ux-patterns.md`, if it exists. Its rules and its dated
  decisions outrank this skill's preferences.
- Inside a run, `prd.md` and `ux.md`. Outside one, the README and the
  product's own screens.
- The design system in code — tokens, theme, component library — so the
  file can **point** at it. Visual tokens live in code or in the
  project's own design document; this file never copies them.

### 2. Derive the patterns from the code

Extract before asking. For each section in
[`references/sections.md`](references/sections.md), find how the
product already does it:

- Search the components and call sites the section names: dialogs and
  confirm calls, toast and notify calls, spinners and skeletons, form
  libraries and validation schemas, router and link usage, focus and key
  handlers.
- Count the variants. "Delete confirms in 9 places, offers undo in 2,
  does neither in 1" is a finding and the start of a rule.
- Note where the code agrees with itself: that is a rule already, only
  unwritten.

A section the product has no instance of is left out, not invented.

### 3. Ask only the judgement calls

Where the code agrees, write the rule down and show it; do not ask.
Where it disagrees, or where the rule needs a trade-off only the owner
can make — undo or confirm, inline or on submit, pagination or infinite
scroll — ask **one question at a time**, with the variants counted, your
recommendation first, and the reason for it. A rule the owner chose
gets a dated entry in the file's decisions log.

### 4. Write the file

Use the shape in [`references/template.md`](references/template.md).

- **Rules are checkable.** "Destructive actions offer undo for 10
  seconds; only irreversible ones confirm, naming the object" can be
  checked against a screen. "Be consistent about deletion" cannot.
  [`references/sections.md`](references/sections.md) has a checkable
  starter rule for each section, modelled on Vercel's
  web-interface-guidelines; adopt one only when the code or the owner
  supports it.
- **Each rule names its evidence**: the component or call that already
  implements it, so the next author reuses it instead of rebuilding it.
- **Never touch Voice & terms.** If the section is missing, leave its
  heading with the ownership note from the template; `ux-writing` fills
  it.
- Show the owner the file, or the diff to it, before the pass ends.

### 5. Audit against it

Sweep the surfaces in scope — a flow, a route, or the whole product,
capped and sampled — against each rule.

- Each deviation names the screen, the file and line, the rule, and what
  it costs the person using it ("delete is undoable everywhere except
  here, where it is permanent and unannounced").
- Each one is classed as either a **fix** (the screen is wrong) or a
  **candidate rule** (the screen is right and the file is incomplete or
  wrong). Candidate rules go back through step 3; they are never
  written in silently.
- Look at the rendered screens where behaviour is visible only at
  runtime: focus, loading timing, what a toast says and how long it
  stays. If they cannot be rendered, the report's first line says so,
  and everything after it is a reading of the code.

The audit edits nothing. Applying fixes is a separate, approved pass.

### 6. Report, and hand off what is not yours

What the file now says and what changed in it; the deviations, ranked by
cost; the questions still open.

- **Visual inconsistency** — spacing, type, colour — is polish's
  `refine` move.
- **Wording** — a term used two ways, an error that does not say what to
  do — is `ux-writing`.
- **A flow problem** goes to `ux-design` inside a run, or to the user.
- **A code defect** goes to `review`; a repo-wide defect sweep is
  `audit`. Later work becomes a backlog seed or a maintenance run via
  `capture`; this skill never writes the backlog itself.

## Rules

- Derive from the code first. Ask only what the code cannot answer, one
  question at a time, recommendation first.
- The file's written decisions win, then the user's direction, then this
  skill's taste.
- Every rule is checkable and names the code that implements it.
- Behaviour only. Tokens are pointed at, never copied; wording belongs
  to `ux-writing`.
- **Voice & terms** is never this skill's to write.
- Audit edits nothing, and a deviation is either a fix or a candidate
  rule — never both, never silently promoted.
- A section with no instance in the product is left out, not invented.

Deriving the file from the code and asking the human only for judgement
restates the method of Impeccable's `document` command
([pbakaus/impeccable](https://github.com/pbakaus/impeccable),
Apache-2.0); persisting decisions so they survive between sessions is
the idea behind [interface-design](https://github.com/Dammyjay93/interface-design)'s
`system.md`. Neither text is copied. The checkable rule style follows
[vercel-labs/web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines).
