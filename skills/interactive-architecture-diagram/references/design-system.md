# Design system — professional dark, interactive

The source for every interactive-only visual value. The dark palette —
canvas, text tiers, font stacks and node-type colors — is not restated
here: its one owner is
`../../animated-diagram/references/design-system.md`, and its Canvas,
Text — three tiers and architecture-mode Node types sections are the
values this skill draws with. `assets/boilerplate.html`'s `:root` and CSS
classes mirror that palette plus the values this file adds.

The look is **flat and precise**: restrained accents on a deep slate canvas,
one soft shadow for lift, no neon glow. Color earns its place by encoding a
node's **type**, never for decoration.

## Contents

- [Palette](#palette--owned-by-animated-diagram) — what this skill adds to the shared one
- [Shapes](#shapes) · [Spacing](#spacing--8px-grid)
- [Interaction states](#interaction-states-presenter-mode) — dimming, pulses, live edges
- [Assumed markers](#assumed-markers) — flagging unverified detail
- [Presenter chrome](#presenter-chrome) — deck, panel, keyboard

## Palette — owned by animated-diagram

Every canvas, text-tier, font and node-type value comes from the owner
file named above. Each node draws with its type's stroke and fill from
that file's architecture-mode table — color *is* the type. What differs
here:

- **Edges** are the owner's Connector, `#6e7681`. One addition: **edge,
  emphasis** `#8b949e` (the secondary text tier's value), used for the
  live edge in presenter mode.
- **Tertiary text** labels tiers as well as boundaries.
- **Node types**: the architecture-mode table only — this skill has no
  flow mode. The owner's traveling-dot row does not apply either; the motion
  here is flow pulses (below).
- **System font stacks** also rasterize correctly on PNG export, which
  this skill offers.

## Shapes

- **Node** — rounded rect `rx=8`, `stroke-width=1.5`, `filter=url(#soft-shadow)`.
  Draw an opaque `#161b22` mask rect first, then the styled rect over it, so
  edges pass under the node cleanly. Wrap in `<g class="nodeg" data-id="...">`.
- **Boundary** — rounded rect `rx=12`, fill `rgba(255,255,255,0.015)`, stroke
  `#30363d` width `1.25`, `stroke-dasharray="6 4"`; label top-left, tertiary
  tier. Wrap in `<g class="boundaryg">` so it dims in presenter mode.
- **Edge** — a `<path>` (never `<line>`: pulses ride paths via `mpath`), stroke
  `#6e7681` width `1.5`, `marker-end=url(#arrow)`. Async: add
  `stroke-dasharray="5 4"`. Auth: stroke `#e5606a`. Wrap each edge, its labels,
  and its pulses in `<g class="edgeg" data-edge="...">` so they dim and light
  together.

## Spacing — 8px grid

Snap every coordinate to 8. Node height 56 (service) or 88–120 (grouped
component). Minimum gap 40 vertical, 48 horizontal. Boundary padding 24. Legend
≥24 below the lowest boundary. `viewBox` = content bounds + 32 margin.

## Interaction states (presenter mode)

Presenter mode tells the story by dimming everything except the active path.
The values below live in the boilerplate CSS — reuse, don't reinvent.

| State | Spec |
|-------|------|
| Dimmed node (`svg.focused .nodeg:not(.on)`) | opacity `0.22` |
| Dimmed edge (`svg.focused .edgeg:not(.live)`) | opacity `0.14` |
| Dimmed boundary (`svg.focused .boundaryg`) | opacity `0.5` |
| Live edge (`.edgeg.live .edge`) | stroke `#8b949e`, width `2` |
| Transition | `opacity 0.35s ease` |

**Flow pulses** — the animated "traffic" riding a live edge:

- `<circle class="pulse" r="4" fill="#4493f8">` with
  `<animateMotion dur="1.4s" repeatCount="indefinite"><mpath href="#edgeId"/></animateMotion>`
- Short/medium edges: two pulses, second with `begin="-0.7s"` (negative offset
  starts it mid-cycle — no dead time).
- Long arcs: one pulse, `dur="2s"`–`2.2s` so it doesn't race.
- Pulses are `opacity: 0` until their edge group gets `.live` — they only show
  for the active stage.

## Assumed markers

Any detail not verified against the real system must be visibly provisional so
nobody presents a guess as fact:

- **Node**: add class `assumed` (dashed border `stroke-dasharray: 4 3`) plus an
  amber tag `<text class="anno warn" text-anchor="end">assumed</text>` in the
  node's top-right corner.
- **Edge label**: amber text — `fill="#d29922"`, prefix `assumed:`.
- **Boundary label**: amber `anno warn` note top-right (e.g. location guesses).
- **Panel**: set the node's `assumed` field in `NODE_INFO`; renders the amber
  "Assumed — confirm" block.
- **Legend**: when any marker is used, include the row
  `dashed = assumed, confirm before presenting`.

Amber = `#d29922` (the queue color doing double duty; acceptable because the
tag text disambiguates).

## Presenter chrome

HTML outside the SVG (never exported to PNG/SVG):

- **Deck** — sticky bottom bar: Prev/Next buttons, stage title (15px/600),
  caption (14px, secondary color), progress dots (8px circles, accent
  `#4493f8` for current). Captions are narration — one spoken-style sentence.
- **Keyboard** — `→`/`Space` next, `←` prev, `Home` overview, `End` last,
  `Esc` closes the panel. Presenter-friendly: no mouse needed mid-talk.
- **Inspect panel** — fixed top-right card, 300px: name, uppercase type line,
  body paragraph, optional amber assumed block. Opens on node click; closes on
  outside click or `Esc`.
- **Toolbar** — sticky top: Copy PNG / Download PNG / Download SVG. Exports
  serialize the SVG with the stylesheet inlined so classes resolve detached.
