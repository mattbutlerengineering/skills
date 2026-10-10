# Research: #624 (UX writing skill) and #627 (next-level UX/UI, per-project patterns)

Date: 2026-10-10. Read-only research; nothing in the repo was changed.

## 0. What already exists here (the ground the proposals must build on)

- **`ux-design`** (stage, main): interviews one flow at a time and writes `ux.md`:
  flows, ASCII screens, empty/loading/error states. It deliberately makes **no
  visual decisions**. Step 3 asks "What existing UI conventions must this
  match?" Today nothing written down answers that question.
- **`polish`** (utility, branch `feat/lean-and-polish-skills`, PR #632, about to merge):
  - Step 1 reads what is already decided: audience, existing design system
    ("its existing screens are the system, written down or not"), user direction.
  - Step 2 names the surface's job: convince / work / read.
  - Step 3 offers 9 named moves, one per pass: critique, inspect, refine,
    pare, amplify, calm, states, **copy**, motion (`references/moves.md`).
  - Step 4 checks `references/tells.md`, which lists defaults nobody chose and
    includes a **Copy** tells section (claim words, "Get started/Learn more",
    exclamation and greeting on every screen, invented proof).
  - Steps 6 and 7: render and look twice then stop, report, hand off (flow
    problem → ux-design, code defect → review, later work → backlog seed or
    capture).
  - Credits Impeccable (Apache-2.0) as the source of the moves and tells idea.
    Polish restates those ideas; it does not copy Impeccable's text.
- **Overlap already on the table:** polish's `copy` move is about 8 bullets that
  cover a **single surface**: outcome-named buttons, visible labels, errors
  that say what to do, one name per concept, no claim adjectives, one
  capitalisation style, locale formatting, no invented facts. Polish's
  `critique` has no heuristic scoring, and nothing persists a project's
  decisions between passes.
- **Repo constraints a new skill inherits:**
  - Stdlib only.
  - Utility skills own no **run** artifact and are never routed to
    (ADR-0023). Each new one must be added to `protocol.py` `UTILITY_SKILLS`,
    the README table, LEDGER (draft), and `evals/routing.json` discrimination
    cases.
  - The branch name is literally *lean*-and-polish, so skill sprawl has a
    cost. A per-project file written outside a run (`docs/ux-patterns.md`) is
    a new kind of thing for this repo, and it probably needs an ADR (see
    question 3 in section 4).

## 1. Sources

### Agent skills (prior art)

- **Impeccable**, https://github.com/pbakaus/impeccable (Apache-2.0).
  - One skill with 24 commands: init, document, extract, craft, shape,
    critique, audit, polish, bolder, quieter, distill, harden, onboard,
    animate, colorize, typeset, layout, delight, overdrive, **clarify**,
    adapt, optimize, live, generate.
  - **Per-project files:**
    - `PRODUCT.md`: durable product truth. Users, purpose, positioning,
      operating context, terminology, brand commitments, "evidence on hand",
      and absences that must not be fabricated. Init interviews for it and
      never asks aesthetic questions.
    - `DESIGN.md`: the visual system, in the Google Labs DESIGN.md spec. YAML
      token frontmatter plus 8 canonical sections ending in "Do's and Don'ts".
      Its `document` command extracts it from code (CSS vars, Tailwind config,
      theme files, components, computed styles) and **asks the human only
      for the qualitative language**.
    - `.impeccable/surfaces/*.md`: per-route direction contracts.
    - `.impeccable/critique/*.md`: persisted critique snapshots.
  - **Detector:** 59 deterministic rules (`npx impeccable detect`, `--json`
    for CI, a hook on Claude Code). Ignores go in config or in
    `impeccable-disable` comments.
  - **`critique`** (806 lines) scores **Nielsen's 10 heuristics** 0–4 each
    into a "Design Health Score" out of 40. It renormalises to the applicable
    maximum when it scores a heuristic n/a, and it notes that most real
    interfaces score 20–32. It adds:
    - a "Design Specificity Verdict" (authored, or interchangeable with the
      rest of its category?);
    - P0–P3 priority issues, each with a suggested command;
    - **persona red flags** (Alex the power user, Jordan the first-timer,
      plus 1–2 project personas);
    - a cognitive-load checklist with 8 named violations: Wall of Options,
      Memory Bridge, Hidden Navigation, Jargon Barrier, Visual Noise Floor,
      Inconsistent Pattern, Multi-Task Demand, Context Switch.
  - **`clarify`** (94 lines, its UX-copy command). It:
    - audits the *whole interaction path*, not isolated strings;
    - sets a message hierarchy per state: the one fact needed now → the next
      action → context that changes the decision → tone;
    - rewrites by function: actions/navigation, forms, errors/permissions,
      loading/empty/success, help text;
    - covers voice versus tone, accessibility, and localisation: no
      concatenated fragments, structured variables, room for expansion;
    - keeps a terminology glossary;
    - verifies at 200% zoom and with long names and plurals.
  - **`harden`**: text overflow, i18n, error handling, edge cases, input
    validation, accessibility resilience.
  - Source files read from
    `cursor-plugin/skills/impeccable/reference/{clarify,init,document,critique,harden}.md`.
- **Anthropic frontend-design**,
  https://github.com/anthropics/skills/tree/main/skills/frontend-design:
  - grounds the design in the subject matter;
  - lists 5 named "clusters" of AI-generated design (cream + terracotta,
    near-black + acid accent, broadsheet hairlines, the SaaS-card kit,
    template chrome such as ALL-CAPS eyebrows, "A · B · C" and an appended
    "→");
  - plans tokens → reviews the plan against the brief → builds → self-
    critiques from screenshots; "spend your boldness in one place".

  This is visual work, and polish already covers its ground.
- **content-designer/ux-writing-skill**,
  https://github.com/content-designer/ux-writing-skill (MIT). The closest
  prior art for #624. It ships `references/content-usability-checklist.md`,
  `voice-chart-template.md`, `accessibility-guidelines.md` and
  `patterns-detailed.md`, plus templates for error messages, empty states
  and onboarding.
  - **Four standards: purposeful, concise, conversational, clear**
    (Podmajersky's). Each is applied as a pass, in order. The checklist rates
    each criterion 0–10.
  - **Benchmarks:**
    - lines of 40–60 characters;
    - buttons of 2–4 words, 6 at most;
    - errors of 12–18 words including the fix;
    - about 85% active voice;
    - grade 7 reading level for a general audience, grade 10 for a
      professional one;
    - comprehension falls from about 100% at 8 words or fewer to about 90% at
      14.

    These numbers come from the skill and were not traced to primary studies
    here. Present them as guidance, not as law.
- **petekp/claude-code-setup `ux-writing`**,
  https://skills.sh/petekp/claude-code-setup/ux-writing. It has a "Copy
  Audit" output format with a voice check and suggested adjustments.
- **Owl-Listener/designer-skills `ux-writing`**,
  https://openskillindex.com/skills/owl-listener-designer-skills-ux-writing.
  Microcopy, buttons and form labels.
- **interface-design (Dammyjay93)**,
  https://github.com/Dammyjay93/interface-design. It **saves decisions to
  `.interface-design/system.md` and reloads them every run**, for example
  "Button: 36px, Card: 16px pad, spacing on a 4/8/12/16 grid". This is the
  clearest prior art for #627's "for each project, define patterns":
  **persist decisions so they do not drift between sessions**.
- **Vercel web-interface-guidelines**,
  https://github.com/vercel-labs/web-interface-guidelines. A large, concrete,
  checkable list of behaviour rules, with `AGENTS.md` and `command.md` for
  agents. Examples:
  - keyboard works everywhere; focus is visible and never covered;
  - hit targets of at least 24px (44px on mobile); never block paste;
  - loading buttons keep their label; a spinner gets a minimum duration of
    150–300ms before it shows and stays visible 300–500ms;
  - URL as state, deep-link everything;
  - optimistic updates with rollback or undo;
  - an ellipsis on "Rename…" and "Saving…";
  - confirm destructive actions or offer undo;
  - links are `<a>`; async updates are announced with `aria-live`.

  This is the best model for **behaviour** rules, as distinct from visual
  ones.
- **ui-ux-pro-max**, https://github.com/nextlevelbuilder/ui-ux-pro-max-skill:
  67 styles, 161 palettes, 57 font pairings, 99 UX guidelines, and a BM25
  search script. Breadth over judgement. It is not a model for this repo,
  which is stdlib-only, judgement-led and lean.
- Roundup (secondary source):
  https://pasqualepillitteri.it/en/news/576/claude-code-skills-design-uiux-guide

### UX writing and heuristics canon

- **NN/g, 10 Usability Heuristics**,
  https://www.nngroup.com/articles/ten-usability-heuristics/ (1994, reviewed
  2024).
- **NN/g, Error-Message Guidelines**,
  https://www.nngroup.com/articles/error-message-guidelines/. Its
  visibility / communication / efficiency checklist:
  - place the message next to the cause, and not only in colour;
  - match severity to the display method; don't fire validation early;
  - plain language, a specific problem, a remedy, no blame, no humour;
  - preserve input; offer one-click fixes.
- **Torrey Podmajersky, *Strategic Writing for UX***, O'Reilly, 2nd ed. July
  2025, https://www.oreilly.com/library/view/strategic-writing-for/9781098174323/.
  It covers the voice chart (concepts → voice traits → do/don't examples) and
  the purposeful / concise / conversational / clear tests. The 2nd edition
  adds AI-generated UX content.
  - Verified only through listings and the content-designer skill. The
    chapters themselves were not read.
- **Mailchimp Content Style Guide**, https://styleguide.mailchimp.com/
  (voice and tone, word list, writing for accessibility and translation).
  - From the accessibility page: no directional language ("in the right
    sidebar"), descriptive link text rather than "click here" or "learn
    more", plain language, explain abbreviations on first use.
- **GOV.UK writing standards**,
  https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/
  (clear language, front-loading, an A to Z style guide). The pages are
  index-only through fetch, so the specifics come from general knowledge:
  plain English, about a 9-year-old reading age, short sentences, and words
  to avoid.
- **Apple HIG, Writing**,
  https://developer.apple.com/design/human-interface-guidelines/writing.
  The page renders with JavaScript, so its content was not verified. In
  general it says: alerts get a title stating what happened; buttons are
  specific verbs, never "OK", "Yes" or "No"; one term per concept.
- **Material 3 content design**,
  https://m3.material.io/foundations/content-design/style-guide/ux-writing-best-practices
  (JavaScript-rendered, unverified).
- **Shopify Polaris content guidelines** (actionable language, verb + noun
  buttons, a word list). The old `polaris.shopify.com/content/*` URLs now
  redirect to https://shopify.dev/docs/api/polaris, so get a live URL before
  citing it in a skill.

### What makes these skills effective (cross-cutting)

1. **Named, checkable units.** Impeccable's commands, polish's moves,
   Vercel's bold-led rules: "make it better" can't be verified; "pare" and
   "Loading buttons keep their label" can.
2. **Named anti-patterns, with the test written next to each.** Polish's
   tells add "was this chosen?", which avoids the ban-list failure mode.
3. **A persisted per-project file.**
   - It is read first on every run and written by extraction-then-confirm,
     never by a blank interview: Impeccable `document`, interface-design
     `system.md`.
   - The human supplies only the qualitative judgement.
4. **Scored rubrics with calibration notes** ("most interfaces score
   20–32/40"), so the agent doesn't grade everything 4/4.
5. **Benchmarks as numbers**: words per button, characters per line,
   contrast ratios, hit sizes, durations.
6. **Function-scoped rewrite rules**, one set for each of errors, empty
   states, confirmations, forms and loading. Generic "be clear" advice is
   not enough.

## 2. #624: a UX writing skill (concrete design)

**Name: `ux-writing`** (utility skill). An alternative is `content-design`, but
"ux-writing" is the owner's own phrase, and it is also what people type.

**Why it is a separate skill and not just polish's `copy` move.** Polish's
`copy` is one move, on one surface, in one pass, and it lives among visual
moves. #624 asks for an **audit of user-facing strings** across the product:
an inventory, consistency *across* surfaces (one name per concept is a
product-wide property), a voice that has been written down, and i18n
mechanics. Those need their own inventory step and their own reference files.
Polish's `copy` move should stay as is and point at this skill's rubric for
the depth.

**Trigger description (draft, in strict-YAML-safe shape):**

> Use when the words in a product's interface need auditing or rewriting — "audit our copy", "our error messages are useless", "make the microcopy consistent", "write the empty states", "what should this button say", "do we call it a workspace or a project", "set up a voice and tone guide", "check the strings before we translate". Finds the user-facing strings in the code, grades them against a UX-writing rubric and the project's own voice and terminology, proposes rewrites as a reviewable table, and applies only the ones approved. It changes wording, never facts, and never invents product claims. A visual pass on one screen is polish, whose copy move is the light version of this; designing flows and screens is ux-design; reviewing code is review. Owns no run artifact and is never routed to.

**Flow:**

1. **Find what is already decided.**
   - Read the project's voice and terminology if they exist (see #627's
     `docs/ux-patterns.md` § Voice & terms).
   - Read the README and product copy for audience, and `prd.md` / `ux.md`
     inside a run.
   - If there is no voice yet, offer to draft a **voice chart**
     (Podmajersky): 3 concepts → traits → do/don't examples. Draft it from
     existing copy, then confirm one question at a time, recommendation
     first, as this owner prefers.
2. **Find the strings (inventory).** Do it mechanically, not by reading
   around:
   - i18n catalogs: `*.json`, `*.po`, `*.ftl`, `*.strings`, `*.arb`,
     `messages/*`;
   - JSX/TSX text nodes, and the `aria-label`, `title`, `placeholder` and
     `alt` attributes;
   - toast and notify calls, `throw new Error` messages that reach the UI,
     validation schemas (zod/yup messages), email templates.
   - Output an inventory grouped by **function**: action, label, helper,
     error, empty, loading, success, confirmation, notification, nav, a11y
     name.
   - Scope it to a surface or a flow when asked. A repo-wide inventory is
     capped and sampled.
3. **Audit against the rubric**, in two layers:
   - **(a) Per string:** the four standards (purposeful, concise,
     conversational, clear) plus the function-specific checks in
     `references/patterns.md`.
   - **(b) Across strings:** the terminology glossary (one concept, one
     word, every surface), capitalisation, punctuation, person ("you"
     versus "we", "my" versus "your"), and the tone matched to the stakes
     (payment, deletion, access loss: warm, never jokey).
   - Each finding names the string, its file:line, the rule broken, and the
     cost to the user. Then rank the findings. The tells (claim words,
     "Get started" everywhere, invented proof) come from polish's
     `tells.md` § Copy; link to it rather than duplicate it.
4. **Propose rewrites.** Write a table: location | function | current |
   proposed | rule | note. Read each string **in context**, along the
   interaction path: heading + body + button read together, as clarify
   does.
   - Flag anything that touches facts, legal meaning, pricing, or a domain
     term as **needs-owner**. Never rewrite those silently.
   - Glossary changes are proposed as one decision ("Workspace →
     Project, 23 occurrences"), not 23 edits.
5. **Apply the approved rewrites.**
   - Edit the catalog or source.
   - Keep interpolation variables intact and translator-safe: whole
     sentences, no concatenated fragments, plurals through the i18n
     library.
   - Update tests that assert on strings. Update the glossary and voice
     section if a decision was made.
6. **Look at it.** Same rule as polish: render the changed surfaces and check
   long values, 200% zoom, and a narrow width. If they can't be rendered, say
   so first.
7. **Report and hand off.**
   - What changed and why, in the user's terms; what was left alone
     (needs-owner items).
   - A flow problem goes to `ux-design`; a missing state (no empty state at
     all) goes to polish `states`; a code defect goes to `review`. Later
     work becomes a backlog seed via the existing carriers.

**Modes** (one per pass, like polish): `audit` (read-only findings),
`rewrite` (propose and apply), `voice` (create or update the voice chart and
glossary), `write` (draft strings for a new state or flow from `ux.md`).

**References** (about 4 files, each under 200 lines):

- `references/rubric.md`
  - The four standards as ordered passes, each with check questions.
  - Benchmarks, labelled as guidance: buttons 2–4 words, errors 12–18 words
    including the fix, 40–60 characters per line, about 85% active voice,
    grade 7 reading level for a general audience and 10 for a professional
    one.
  - Calibration: score findings, don't score everything.
- `references/patterns.md`, rewrite rules by function (sources: clarify,
  NN/g, HIG, Vercel):
  - **Buttons:** verb + object, the outcome and not the gesture, no
    "OK"/"Yes"/"Submit", ellipsis when more input follows.
  - **Errors:** what failed → why, if known and useful → how to recover;
    next to the cause; input preserved; no codes as the primary message; no
    blame, no humour.
  - **Empty states:** split first use / no results / filtered / no
    permission / failed.
  - **Confirmations:** name the object and the consequence, and prefer undo.
  - **Forms:** persistent labels, requirements before submit.
  - **Loading:** name the real operation and never fake progress.
  - **Success:** brief.
  - **Links:** make sense out of context.
  - **Notifications.**
- `references/voice-and-terms.md`, the template for the project section
  (voice chart plus glossary plus mechanics: capitalisation, person,
  numbers and dates). The written file itself lives in the project, not in
  the skill.
- `references/i18n-a11y.md`:
  - no concatenation; ICU plurals; room for about 30% expansion; RTL;
  - accessible names match visible labels; alt text versus empty alt;
  - no directional language; nothing carried by colour, icon or
    punctuation alone.
- `references/tells.md` is **not** duplicated. Point at
  `../polish/references/tells.md` § Copy, or move the copy tells into this
  skill and have polish point here. Pick one owner, in line with the repo's
  one-owner discipline.

**Borrow from Impeccable `clarify`:** the message hierarchy per state, the
"whole interaction path" read, the function-scoped rewrite rules, the
glossary, and the verify list (200% zoom, plurals, dynamic values). Credit it
the way polish does: restate, never copy. **Borrow from content-designer:**
the four ordered passes, the benchmarks, and the voice chart template (MIT).
**New here:** the mechanical string inventory, the cross-surface consistency
audit, the needs-owner fact guard, and the approved-only apply step.

## 3. #627: making any UX/UI "next level", per-project patterns

Polish (visual) and ux-design (flows) already exist. The gaps:

1. Nothing persists a project's decisions.
2. Nothing covers **behavioural** consistency (how we confirm, undo,
   paginate, validate, load, notify).
3. Critique has no scored usability heuristic.
4. There is no persona walk-through.

### Option A: `ux-patterns`, a per-project "design system for behaviour" plus a conformance audit (new utility skill)

- **Writes `docs/ux-patterns.md`.** It extracts first, then confirms only the
  judgements (Impeccable `document` and interface-design `system.md` are the
  prior art). Sections:
  - **Surface jobs**: which routes are convince, work or read (polish's
    taxonomy).
  - **Interaction patterns**: one rule each for destructive action (undo or
    confirm, and which), forms and validation timing, loading (skeleton or
    spinner, the delay thresholds), empty states, errors (inline, banner or
    modal by severity), notifications and toasts, navigation and deep
    linking, tables and lists (pagination or infinite scroll, bulk actions),
    search and filter, modals versus pages, keyboard shortcuts.
  - **States checklist** for every new surface.
  - **Accessibility floor and targets** (taken from polish).
  - **Voice & terms** (the voice chart and glossary, owned by `ux-writing`).
  - **Visual system pointer**: tokens live in code or DESIGN.md, and this
    file references them rather than duplicating them.
  - **Decisions log**: a dated "we chose X over Y because…".
- **Audits conformance.** It sweeps surfaces against the file and reports
  each deviation as either a fix or a candidate new rule. Behaviour
  inconsistency is the "Consistency and standards" heuristic, made checkable.
- **Consumers:**
  - ux-design step 3 ("what conventions must this match?") reads the file
    instead of re-asking;
  - polish step 1 reads it as "the system";
  - ux-writing reads and writes § Voice & terms;
  - implement and review could cite it.
- **Pros:**
  - Directly answers "for each project, define ux patterns and optimise for
    consistency".
  - Compounds over time.
  - Behaviour rules are checkable (in the Vercel style).
- **Cons:**
  - One more skill.
  - A new kind of project-level, non-run file, which needs an ADR (who owns
    it, and when it goes stale).
  - Risk of a template nobody fills in, so it must extract, not interview
    from blank.

### Option B: extend polish (no new skill)

- **Step 1 gains a persisted system file.** Polish reads
  `docs/ux-patterns.md` if present and offers to write it after a critique.
- **Critique gains** a Nielsen 10 score (0–4, renormalised for n/a,
  calibrated at "20–32 is typical"), 2–3 persona walk-throughs, and the
  cognitive-load violations.
- **New moves:**
  - `harden`: overflow, i18n, edge cases. This partly overlaps `states`, so
    fold it into `states`.
  - `onboard`: first-run and activation.
  - `conform`: align the surface with the project's patterns.
- **Pros:** no skill sprawl, so it fits the "lean" branch, and one entry
  point for "make it better".
- **Cons:**
  - Polish is visual-first and already has 9 moves plus 2 references.
    Adding project-level pattern authorship blurs its single-surface,
    one-move-per-pass contract.
  - Pattern authorship is product-wide, not per surface.

### Option C: `heuristic-eval`, a standalone scored usability evaluation

- **What it does:**
  - Nielsen 10 at 0–4, with severity on NN/g's 0–4 scale.
  - Persona and task walk-throughs (a cognitive walkthrough of the primary
    task).
  - A cognitive-load checklist.
  - Findings route to polish moves, ux-writing, ux-design (flow), or
    ux-patterns (a missing rule).
  - Read-only, like `audit`/`deepen`.
- **Pros:** a crisp, read-only, evaluable output.
- **Cons:**
  - Heavy overlap with polish `critique` and `inspect`.
  - It produces findings but does not create the persisted consistency that
    #627 explicitly asks for.

### Recommendation: Option A (`ux-patterns`) plus a small slice of B; not C

- **A.** #627's distinctive ask is "for each project, define ux patterns
  and optimise for usability and consistency", and that is a *persisted,
  product-wide* artifact, which no existing skill owns. Polish is deliberately
  per-surface and one move per pass. Ux-design is per-run and flow-scoped.
  Impeccable and interface-design both found that the persisted file is what
  stops drift between sessions.
- **B.** Fold the heuristic scoring and persona red flags into polish
  **critique** as a section in `moves.md`, about 30 lines. Heuristic
  evaluation is a critique lens, not a separate job. That makes C redundant.
- **One file, three owners of sections.** `docs/ux-patterns.md` is shared:
  - `ux-patterns` owns the behaviour sections;
  - `ux-writing` (#624) owns § Voice & terms;
  - polish and ux-design read it.

  One per-project file is better than PRODUCT.md + DESIGN.md + glossary +
  voice chart: fewer files, and one place to look. It needs an ADR: a
  project-level reference file, not a run artifact, and not under
  `docs/features`.
- **Build order:**
  1. #624 `ux-writing` first. It is the smaller, most concrete piece, and it
     defines § Voice & terms.
  2. Then `ux-patterns`, plus polish's critique scoring.
- **Alternative if sprawl is the overriding concern:** a single `ux-system`
  skill with two modes (`patterns` and `writing`). Not recommended: the
  trigger phrases differ ("audit our copy" against "make our UX
  consistent"), and routing evals discriminate better between two
  focused descriptions.

## 4. Borrow from Impeccable, and what overlaps polish

| Impeccable piece | Status here | Action |
|---|---|---|
| critique / audit / polish / bolder / quieter / distill / animate | **Covered**: polish critique, inspect, refine, amplify, calm, pare, motion | none |
| anti-pattern list ("slop") | **Covered**: polish `tells.md` | none |
| `clarify` (UX copy) | Partly covered by polish `copy` (single surface) | **Borrow** the hierarchy per state, function-scoped rules, glossary, and verify list into `ux-writing` |
| `harden` (overflow, i18n, edge cases) | Mostly polish `states` | Copy-side i18n goes to ux-writing's `i18n-a11y.md`; maybe add overflow/i18n bullets to `states` |
| `onboard` (first run, activation) | Gap | Candidate polish move, or a section of the ux-patterns file; low priority |
| `PRODUCT.md` (init) | Partly covered by `prd.md` / `idea.md` inside a run; gap outside one | The "Evidence on hand / absences that must not be fabricated" idea is worth adding to ux-patterns, because it backs polish's no-invented-facts rule |
| `DESIGN.md` (document: extract tokens, confirm the qualitative) | Polish reads "existing screens are the system" but persists nothing | **Borrow the extract-then-confirm method** for `docs/ux-patterns.md`; point at tokens and don't duplicate them |
| Nielsen 10 scored, persona red flags, cognitive-load violations | Gap in polish critique | **Borrow** into polish critique (Option B slice) |
| 59-rule deterministic detector, `live` browser mode, image-gen comps | Out of scope (Node tooling; this repo is stdlib-only) | Polish already says "for the full tool, use Impeccable itself"; keep that stance |
| `.impeccable/critique/*.md` snapshots | Gap | Optional: ux-patterns' decisions log covers the durable part, and snapshots are noise |

Attribution: Impeccable is Apache-2.0. Follow polish's precedent of restating
the ideas in the pipeline's terms, with a credit line, and copying no text. If
any content-designer material (MIT) is used closely, such as the voice-chart
template, credit it too.

**Open questions for the owner** (ask one at a time):

1. Should the copy tells move to ux-writing, or stay in polish?
   Recommendation: keep them in polish and link to them from ux-writing.
   Fewer moving parts while PR #632 lands.
2. File location: `docs/ux-patterns.md`, or `docs/ux/patterns.md` plus
   `docs/ux/voice.md`? Recommendation: one file, so there is one place to
   look.
3. Does the per-project file need an ADR extending ADR-0023 (a utility skill
   writing a non-run, project-level reference doc)? Recommendation: yes,
   because it is a new artifact class.
