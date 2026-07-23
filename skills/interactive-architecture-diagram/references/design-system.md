# Design system — professional dark, interactive

The source for every visual value. `assets/boilerplate.html`'s `:root` and CSS
classes mirror the palette below; change a color in one place and match it in
the other.

The look is **flat and precise**: restrained accents on a deep slate canvas,
one soft shadow for lift, no neon glow. Color earns its place by encoding a
node's **type**, never for decoration.

## Contents

- [Canvas](#canvas) · [Text tiers](#text--three-tiers) · [Node types](#node-types--color-is-the-type)
- [Shapes](#shapes) · [Spacing](#spacing--8px-grid)
- [Interaction states](#interaction-states-presenter-mode) — dimming, pulses, live edges
- [Assumed markers](#assumed-markers) — flagging unverified detail
- [Presenter chrome](#presenter-chrome) — deck, panel, keyboard

## Canvas

| Role | Value |
|------|-------|
| Background | `#0d1117` |
| Dot grid | `#1c2128` |
| Node surface (mask) | `#161b22` |
| Default border | `#30363d` |
| Edge / connector | `#6e7681` |
| Edge, emphasis | `#8b949e` |

## Text — three tiers

| Tier | Value | Use |
|------|-------|-----|
| Primary | `#e6edf3` | node titles — 13px / 600 sans |
| Secondary | `#8b949e` | sublabels, edge labels — 11px sans / 10px mono |
| Tertiary | `#6e7681` | annotations, boundary + tier labels — 9px / 500, uppercase, `letter-spacing 0.04em` |

Sans: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`
Mono: `ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace`

System stacks keep the file self-contained and rasterize correctly on PNG
export. A pinned web font is the one allowed exception.

## Node types — color *is* the type

Each node draws with its type's stroke and fill. The fill is a hint (~0.10–0.12
alpha); the stroke carries the meaning.

| Type | Meaning | Stroke | Fill |
|------|---------|--------|------|
| service | app / compute / API | `#4493f8` | `rgba(68,147,248,0.12)` |
| data | database / store of record | `#a371f7` | `rgba(163,113,247,0.12)` |
| storage | cache / object / block store | `#39c5cf` | `rgba(57,197,207,0.10)` |
| gateway | load balancer / gateway / edge | `#3fb950` | `rgba(63,185,80,0.12)` |
| queue | event / message bus | `#d29922` | `rgba(210,153,34,0.12)` |
| external | third-party / SaaS | `#8b949e` | `rgba(139,148,158,0.10)` |
| security | auth / secrets / trust zone | `#e5606a` | `rgba(229,96,106,0.12)` |

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
