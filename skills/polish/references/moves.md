# The moves

Nine named moves. The names matter: "make it better" cannot be checked,
and "pare this screen" can. Each move says when it applies, what to do,
and when it is done.

The idea of a shared vocabulary of design moves, and of writing down the
tells of a generated interface, is Impeccable's
([pbakaus/impeccable](https://github.com/pbakaus/impeccable), copyright
2025 Paul Bakaus, Apache-2.0), which grew out of Anthropic's
frontend-design skill. This is a compact restatement of those ideas in
this pipeline's terms, not a copy of its text. For the full tool —
deterministic detector rules, live iteration in the browser, platform
references — use Impeccable itself.

Two moves judge and seven change. When you are unsure which changing
move a surface needs, run a judging move first.

## critique — judge before touching

**When.** The ask is for an opinion, or no move was named.

**Do.**

- Look at the rendered surface before reading its code.
- Trace the eye. What does it land on first, second, third? Is that the
  order of importance for the person using it?
- Count the primary actions in each view. More than one is a finding.
- Ask what the user has to remember, against what the screen shows them.
- Find what competes: two things shouting, three type sizes doing one
  job, colour used for meaning and for decoration at once.
- Note what works and should survive any change.

**Hand back.** Five to eight findings, ranked by what they cost the
user. Each says what the person experiences, where on the surface, and
which move would fix it. Then what to keep.

**Done when.** Every finding names an element and its effect on the
user, and none is a preference in disguise. Nothing was edited.

### Heuristic score

When the ask wants a number, or the surface is a whole flow, score it
against Nielsen's ten usability heuristics (Nielsen Norman Group, 1994,
reviewed 2024), 0 to 4 each:

1. Visibility of system status
2. Match between the system and the real world
3. User control and freedom
4. Consistency and standards
5. Error prevention
6. Recognition rather than recall
7. Flexibility and efficiency of use
8. Aesthetic and minimalist design
9. Help users recognise, diagnose, and recover from errors
10. Help and documentation

0 is absent or broken, 2 is present with real gaps, 4 is nothing to
fix. A heuristic the surface gives no chance to judge is marked n/a,
and the total is scaled to the maximum that remains. **Calibrate:** most
working interfaces land between 20 and 32 of 40 (Impeccable's
calibration note); a 4 needs evidence you looked for a failure and found
none, and a total near 40 means the scoring was not strict. Every score
below 4 points at a finding above it. With `docs/ux-patterns.md` in the
project, heuristic 4 is scored against its rules.

### Persona red flags

Walk the primary task twice more, as two people the surface fails
first:

- **The first-timer** — never seen it, came for one thing. Red flags:
  a term they must already know, an action they must remember from a
  previous screen, a blank state with no way in, a choice with no
  default.
- **The expert** — here daily, in a hurry. Red flags: no keyboard path,
  a confirmation on every routine action, a setting reset on each
  visit, a common task three levels deep.

Add one persona from the product's own audience when `prd.md` or the
README names one. A red flag is a finding like any other: element,
effect, move.

## inspect — measure the technical quality

**When.** The ask is whether it holds up: accessibility, small screens,
dark mode, speed.

**Do.**

- **Accessibility.** Compute contrast: 4.5 to 1 for body text, 3 to 1
  for large text and for the boundaries of controls. Tab through it:
  every control reachable, focus always visible, the order matching the
  visual order. Every control has a name; every meaningful image has a
  text alternative; headings descend in order. Motion has a
  reduced-motion path. Pointer targets are at least 24 by 24 CSS pixels,
  and comfortably larger on touch screens.
- **Small and large screens.** A narrow phone width, a tablet width, a
  wide desktop width. No horizontal scrolling, no clipped text, no
  control that only works on hover.
- **Theming.** Every colour comes through the theme. A hard-coded value
  is how one panel stays white in dark mode.
- **Rendering cost.** Layout that jumps as content arrives, images far
  larger than their box, fonts that flash or block, animation of
  properties that force layout.

**Hand back.** Findings with the measured value beside the threshold it
missed, ranked by who is locked out.

**Done when.** Every claim has a number or an observed behaviour behind
it. Nothing was edited unless that was asked for.

## refine — the final pass

**When.** The design is right and the execution is loose. This is the
move the word "polish" usually means.

**Do.**

- Spacing from the scale, not from the nearest number that looked fine.
- Edges that should align, aligned. Baselines that share a line, sharing
  it.
- One radius family, one shadow family, one border weight, used
  consistently.
- Type sizes and weights from the scale, in fewer combinations than you
  started with.
- Icons optically centred against their labels and sized as a set.
- Hover, focus, active, and disabled states on every interactive
  element.
- Every one-off value traced to a token or removed.

**Done when.** Every value on the screen traces to the system or to a
stated exception.

## pare — remove until it would hurt

**When.** The screen is busy and the user has to hunt.

**Do.**

- Name the one thing this view is for. Everything else justifies itself
  against it.
- One primary action. Demote the rest, or move them behind a menu.
- Delete containers that only decorate: the border around a group that
  spacing already groups.
- Remove the label that repeats its heading, the caption that repeats
  its chart, the icon that repeats its word.
- Move what is rarely needed behind disclosure, rather than deleting
  what some users rely on.

**Done when.** Removing any remaining element would cost the user
something they need.

If the clutter is in the code rather than on the screen, that is the
`lean` skill's question, not this one's.

## amplify — commit to one idea

**When.** Correct, tidy, and forgettable.

**Do.**

- Choose one thing to be bold about: scale, colour, type, imagery, or
  layout. One.
- Make the important thing much larger than feels safe, and the
  supporting text quieter.
- One saturated colour used rarely beats five used everywhere.
- A typeface with a point of view for display, and a plain one to carry
  the reading.
- Break the grid once, on purpose.
- Real imagery or real data in place of abstract decoration.

On a **work** surface, boldness lives in the details — the density, the
emphasis on the number that matters — not in a hero treatment bolted
onto a settings page.

**Done when.** Someone could describe the screen from memory by its one
strong idea.

## calm — one emphasis, not six

**When.** Everything is emphasised, so nothing is.

**Do.**

- Pick the single element that deserves emphasis and take it away from
  the others.
- Fewer colours carrying meaning, with neutrals doing the rest.
- Fewer weights and sizes. Space in place of borders and backgrounds,
  wherever space will do.
- Remove motion that draws the eye to something unimportant.
- Let a dense area breathe before reaching for a divider.

**Done when.** The eye has one place to start and an obvious place to go
next.

## states — design what is not the happy path

**When.** Worth a pass before anything ships, and essential when the ask
mentions empty, loading, or error.

**Do.** Walk each state and decide it on purpose.

- **Empty.** Says what will live here and how to put the first thing in.
- **Loading.** Holds the layout still: a skeleton shaped like the
  content, or nothing at all when the wait is short.
- **Error.** What happened, in the user's words; what to do next; their
  input preserved.
- **Partial and stale.** Some of it loaded, some of it is old. Say
  which.
- **Zero, one, many.** The list with one item, and the list with ten
  thousand.
- **Long content.** The sixty-character name, the three-line title, the
  nine-digit number.
- **Translated.** Text a third longer, and right-to-left if the product
  supports it.
- **Denied and offline.** No permission, no connection: explained, not
  blank.

**Done when.** No state on the surface is whatever the framework
happened to render.

## copy — the words in the interface

**When.** Labels are vague, errors are unhelpful, or the page sounds
like a brochure.

**Do.**

- A button names its outcome: "Save changes", not "Submit".
- A visible label, not a placeholder standing in for one.
- An error says what to do, not only what went wrong.
- One name per concept, everywhere it appears.
- Cut the adjectives that claim rather than describe: seamless,
  powerful, effortless.
- One capitalisation style, held throughout.
- Numbers, dates, and currency formatted for the reader's locale.
- Change wording, never facts. A claim the product has not made is not
  yours to add.

**Done when.** Each string could be read aloud to the user without
embarrassment, and each action says what it will do.

This move is one surface, one pass. Copy across the whole product — an
inventory of every string, a glossary, a written voice — is the
`ux-writing` skill.

## motion — explain a change

**When.** Changes on screen are abrupt and confusing, or motion is
everywhere and means nothing.

**Do.**

- Animate to explain: where something came from, where it went, that an
  action registered.
- Keep interface transitions short, roughly 150 to 250 milliseconds, and
  decelerate what enters.
- Animate opacity and transform, not properties that force layout.
- Honour the reduced-motion preference with a real alternative, not a
  faster version of the same thing.
- Never make the user wait for an animation before they can act.
- One orchestrated moment is worth more than a dozen scattered ones.

**Done when.** Removing any animation would make a change harder to
follow.
