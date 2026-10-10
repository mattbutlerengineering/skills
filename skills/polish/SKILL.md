---
name: polish
description: Use when a user-facing interface is built, or being built, and it should look and feel considered rather than generated — "this looks generic", "it looks AI-made", "critique this screen", "polish the settings page before we ship", "make it bolder", "tone it down", "too busy, strip it back", "check the contrast and how it holds up on a phone", "fix the empty and error states", "tighten the copy". It first establishes who the surface is for and what the existing design system already decided, then applies one named move — critique, inspect, refine, pare, amplify, calm, states, copy, motion — and looks at the rendered result instead of reasoning about it. The user's stated direction and the existing design system outrank its taste. It does not design flows or screens from a PRD, which is ux-design, and it does not review code for defects, which is review. Owns no run artifact and is never routed to.
---

# Polish

Take a user-facing interface from working to considered.

Left alone, a model designs the average of everything it has seen: a
competent, familiar interface that belongs to no product in particular,
and that people now recognise on sight. Nothing in it is wrong. Nothing
in it was chosen. This skill replaces defaults with decisions — and
checks them by looking at the result, not by reasoning about the code.

This is not a stage in the lifecycle pipeline and it owns no run
artifact. The pipeline's UX Design stage settles flows and screens and
deliberately stops short of visual decisions; this skill starts where
that one stops, and it works just as well in a repo that has never heard
of the pipeline.

## Process

### 1. Find out what is already decided

Three things outrank this skill's taste. Read them before forming an
opinion.

- **Who the surface is for.** The people using it, what they came to do,
  and the situation they are in when they do it. Inside a run that is
  `prd.md` and `ux.md`. Outside one it is the README, the product's own
  copy, and the user. Ask only for what you cannot find, one question at
  a time; if you must go on without an answer, state the assumption in
  the report's first lines.
- **The design system that exists.** Tokens, theme, component library,
  the screens beside this one. Read the code and look at the neighbours.
  A project with no design document is not a blank canvas: its existing
  screens are the system, written down or not.
- **The direction the user gave.** A stated aesthetic, era, palette, or
  typeface is honoured even where
  [`references/tells.md`](references/tells.md) would warn against it.
  Steering a clear brief toward your own taste is a failure, not a
  refinement.

### 2. Name the surface's job

One product has surfaces with different jobs, and what counts as good
differs between them. Decide which this is from the surface, not from
the product:

| Job | Typical surfaces | What good looks like |
|---|---|---|
| **Convince** | Landing page, pricing, campaign | One message, one action. Expression is the point, and sameness is the risk |
| **Work** | App screens, dashboards, forms, settings, admin | Scanning, density, consistency, predictability. Character lives in the precise details |
| **Read** | Docs, articles, help, changelogs | A comfortable measure, clear hierarchy, steady rhythm. The interface recedes |

A tool's landing page is still **convince**. A fashion brand's help
centre is still **read**.

### 3. Choose the move

One move per pass. [`references/moves.md`](references/moves.md) has each
in full: when it applies, what to do, and when it is done.

| Move | What it is for |
|---|---|
| **critique** | Judge before touching: hierarchy, clarity, load. Findings, no edits |
| **inspect** | Measured technical quality: accessibility, small screens, theming, rendering cost. Findings, no edits |
| **refine** | The final pass: alignment, spacing, consistency with the system |
| **pare** | Too much on the screen: remove until removing more would cost the user something |
| **amplify** | Timid and bland: commit to one strong idea |
| **calm** | Shouting: one emphasis, not six |
| **states** | Empty, loading, error, long, and partial states, designed rather than left to chance |
| **copy** | The words in the interface: labels, buttons, errors, empty states |
| **motion** | Motion that explains a change, and none that only decorates |

When the ask names no move, run **critique** first and propose the one
or two moves it supports. Do not run them all: nine passes over one
screen is how a design loses the thing that was good about it.

### 4. Read the tells — before and after

[`references/tells.md`](references/tells.md) lists the defaults that
mark an interface as nobody's: the font that is on everything, the
purple gradient, the card inside the card. Check the surface against it
before editing, and check your own work against it afterwards.

It is not a ban-list to match patterns against. The test for every entry
is the same: *was this chosen for this product, and can you say why?* A
default the brief asks for, or one the existing system uses on purpose,
is not a tell.

### 5. Change it inside the system

- **Refining keeps the identity.** Tokens, components, behaviour, and
  factual copy outside the scope of the ask stay as they are. Replace
  the look only when a redesign was asked for.
- **Values come from the system.** A colour, size, or radius the system
  lacks is added to the system, not typed inline where it will drift.
- **Invent no facts.** No made-up testimonials, customer logos, metrics,
  or claims. Placeholder content is marked as placeholder, where the
  user will see the mark.
- **The accessibility floor is not a style choice.** Text contrast,
  visible focus, keyboard reachability, labelled controls, a
  reduced-motion path, and targets big enough to hit survive every move
  — including the ones that make things bolder or quieter.

### 6. Look at it — twice, then stop

Reasoning about a stylesheet is how a screen ends up correct on paper
and wrong on the glass.

- **Render it and look.** At a narrow width and a wide one. In each
  theme the product ships. With real-length content: the long name, the
  empty list, the error. With the keyboard alone.
- **Measure what you claim.** A contrast ratio is computed, not
  eyeballed. A size is read from the rendered element, not from the
  stylesheet you meant to apply.
- **Two looks.** Make the whole change, then look. Fix what that look
  shows as one batch, look a second time to confirm, and stop. A third
  look is the user's decision: an agent inspecting its own work in a
  loop buys less with every pass.
- **If it cannot be rendered, say so first.** No browser, an app that
  will not start, a native target with no simulator: the report's first
  line says the surface was not seen, and everything after it is a
  reading of the code. A critique of an interface nobody looked at,
  presented as one that was, is worse than no critique.

### 7. Report, and hand off what is not yours

Say what changed and why, in terms of the person using the surface; what
was deliberately left alone; and what could not be verified.

- **A flow problem** — a missing step, the wrong screen, a journey that
  does not hold together — is not polish. Inside a run it routes back to
  `ux-design`; this skill does not redraw a flow on its own authority.
- **A defect in the code behind the interface** goes to `review`.
- **Polish the breakdown does not cover** is logged under the
  breakdown's Notes, or raised with the user, rather than slipped into
  an unrelated item.
- **With no run open,** work worth doing later is a seed for the
  backlog, or a maintenance run via `capture`. This skill never writes
  the backlog itself.

## Rules

- The brief wins, then the existing system, then this skill's taste. In
  that order.
- One move per pass, and name it. "Make it better" gets a critique
  first.
- Critique and inspect are read-only. They produce findings; they do not
  edit.
- Never invent a fact to fill a layout.
- The accessibility floor survives every move.
- Look at the rendered result. If you could not, say so before anything
  else.
- Two looks, then stop.
- A tell is a default nobody chose, not a pattern that is forbidden.
