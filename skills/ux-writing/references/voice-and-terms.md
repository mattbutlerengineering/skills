# Voice & terms — the section template

The project's voice and vocabulary live in **one section** of a
project-level file, `docs/ux-patterns.md`, under the heading
`## Voice & terms`. This skill owns that section; the `ux-patterns`
skill owns the rest of the file. The written section belongs to the
project, not to this skill: this page is only its shape.

Write it by **extracting first**: infer the voice from the copy the
product already has, list the terms it already uses, and ask the owner
only the judgement calls the copy cannot settle — one question at a
time, with your recommendation and its reason first.

The voice chart is Torrey Podmajersky's device from *Strategic Writing
for UX*; the layout below is this skill's.

## The template

```markdown
## Voice & terms

<!-- Owned by the ux-writing skill. Other sections of this file belong
     to ux-patterns. Last reviewed: YYYY-MM-DD. -->

### Voice

| Concept | Trait | We do | We don't |
|---|---|---|---|
| <what the product stands for, one idea> | <how that sounds> | <example string> | <example string> |

Two to four concepts. Every trait has a real example from the product.

### Tone by stakes

| Situation | Tone | Example |
|---|---|---|
| Routine (saved, sent) | <brief, neutral> | |
| Something went wrong | <calm, specific> | |
| Money, data or access at risk | <plain, serious — never playful> | |
| First use | <welcoming without a greeting on every screen> | |

### Terms

| Use | Not | Meaning |
|---|---|---|
| <the one word> | <the words it replaces> | <what it refers to in this product> |

### Mechanics

- Capitalisation: <sentence case | title case> for <headings, buttons, labels>.
- Person: <"you" and "we" | "you" only>; "my" vs "your" in navigation: <choice>.
- Numbers, dates, currency: <locale-formatted by the i18n library>.
- Punctuation: <full stops on single-sentence labels? exclamation marks?>.

### Decisions

- YYYY-MM-DD — <we chose X over Y because…>
```

## Filling it honestly

- Every example in the Voice table is a string the product ships or a
  rewrite the owner approved. Never an invented one.
- The Terms table records a decision, not a wish. A term the code still
  uses inconsistently stays in the audit's findings until the rewrite
  lands.
- A decision is dated and says what it was chosen over. The next person
  to ask "workspace or project?" reads the answer instead of reopening it.
- If the file has other sections, leave them untouched.
