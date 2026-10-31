# Design system — light editorial, theme-aware, still

The source for every visual value. `assets/boilerplate.svg`'s `<style>`
mirrors the tokens below — change a color in one place and match it in
the other. The dark palette is the family's shared canvas (the
`animated-diagram` and `interactive-architecture-diagram` skills), so a
figure that flips dark reads as the same system.

The look is **a designed document figure, not a screen**: warm paper,
ink strokes, hairlines, no shadows, no glow. Node *types* are told apart
by ink-at-opacity treatments, never by a palette of hues; the one accent
color goes on the one or two elements the reader should find first.

## Contents

- [Tokens](#tokens--theme-aware) · [Typography](#typography)
- [Node treatments](#node-treatments--ink-not-hue) · [Shapes](#shapes)
- [Connector grammar](#connector-grammar--five-rules) — the load-bearing section
- [Spacing](#spacing--8px-grid) · [Complexity budget](#complexity-budget)
- [Legend](#legend) · [Assumed markers](#assumed-markers)
- [Theme mechanics](#theme-mechanics)

## Tokens — theme-aware

Every value is a CSS custom property on `:root` inside the SVG's
`<style>`; the dark block overrides only the properties. Nothing in the
document body names a hex directly.

| Token | Light (default) | Dark |
|-------|-----------------|------|
| `--paper` (background, masks) | `#f6f5f1` | `#0d1117` |
| `--raised` (solid node fill) | `#ffffff` | `#161b22` |
| `--ink` (names, primary strokes) | `#262a33` | `#e6edf3` |
| `--muted` (sublabels, connectors) | `#5b6472` | `#8b949e` |
| `--soft` (eyebrows, edge labels, legend) | `#878e9c` | `#6e7681` |
| `--rule` (hairlines, zone strokes) | `rgba(38,42,51,0.12)` | `rgba(230,237,243,0.12)` |
| `--accent` (focal — 1–2 elements max) | `#d9622b` | `#f0925e` |
| `--accent-tint` (focal fill) | `rgba(217,98,43,0.08)` | `rgba(240,146,94,0.10)` |
| `--assumed` (assumed markers) | `#9a6700` | `#d29922` |

**Inversion rule:** any `rgba(38,42,51, X)` in light becomes
`rgba(230,237,243, X)` in dark — same opacity, ink flipped. The accent
shifts slightly brighter so it reads on the dark paper.

## Typography

System stacks only — the file makes no external requests, and GitHub's
image proxy would strip them anyway.

| Role | Family | Size / weight | Use |
|------|--------|---------------|-----|
| Title | `Georgia, 'Times New Roman', serif` | 20 / 400 | the figure's one serif line |
| Eyebrow | mono | 8 / 500, uppercase, `letter-spacing 0.14em` | kicker above the title, zone labels |
| Subtitle | sans | 11 / 400 | one line under the title |
| Node name | sans | 13 / 600 | human-readable labels |
| Sublabel | mono | 10 / 400 | tech, ports, protocols — technical content only |
| Edge label | mono | 9 / 400, uppercase, `letter-spacing 0.06em` | ≤14 chars |
| Legend | sans | 9 / 500, uppercase, `letter-spacing 0.04em` | legend rows |

Sans: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` ·
Mono: `ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace`

The serif title is load-bearing contrast — it is what makes the figure
read as editorial rather than as a tool screenshot. Mono is for
*technical* content; names always go in sans.

## Node treatments — ink, not hue

Type is carried by fill/stroke *treatment* and by what the label says,
never by a color-per-type palette. Six treatments cover the
architecture vocabulary:

| Treatment | Types it carries | Fill | Stroke |
|-----------|------------------|------|--------|
| focal (1–2 max) | the story's protagonist | `--accent-tint` | `--accent`, width 1.2 |
| solid | service, gateway, worker | `--raised` | `--ink`, width 1 |
| store | data, storage | ink @ 0.05 | `--muted`, width 1 |
| external | client, third-party, SaaS | ink @ 0.03 | ink @ 0.30, width 1 |
| async-infra | queue, bus, topic | ink @ 0.02 | ink @ 0.20, width 1, `stroke-dasharray="4 3"` |
| security | auth, secrets, trust | accent @ 0.05 | accent @ 0.50, width 1, `stroke-dasharray="4 4"` |

When two same-treatment nodes must be told apart at a glance (a gateway
beside a service), add a **type tag**: a small rectangular chip
(`rx=2`, not a pill) in the node's top-left — `rect` at `x+8, y+6`,
height 12, hairline stroke, with 7px uppercase mono text (`GW`, `SVC`,
`DB`). Otherwise let the sublabel do the telling.

If you are tempted to give types their own hues, you have left this
design system. One accent; everything else is ink at an opacity.

## Shapes

- **Node** — rounded rect `rx=6`, no shadow, no glow. Draw an opaque
  `--paper` mask rect first, then the styled rect over it, so
  connectors pass under translucent fills cleanly. Name centered at
  `y+24` (height 56) or `y+20` (height 48); sublabel 16–18 below it.
- **Zone / boundary** — rounded rect `rx=8`, fill ink @ 0.02, stroke
  `--rule` width 0.8. Any stronger fill competes with the nodes. Label
  top-left in eyebrow style, with ≥16px between the label's baseline
  and the first enclosed node. Max 3 zones; more reads as a swimlane.
- **Connector** — a `<path>`, `fill="none"`, stroke `--muted` width
  1.2, `marker-end`. Sync calls are solid; async/passive/return flows
  are `stroke-dasharray="4 3"` at width 1 — dash communicates weight,
  never a different routing grammar. Endpoints stop 4px short of node
  edges so the arrowhead breathes.
- **Arrowhead** — one shared `<marker>` (8×6 polygon) whose polygon is
  class-styled `fill: var(--muted)`, plus an accent variant for a
  focal edge. Class-styling is what lets the marker flip with the
  theme.

## Connector grammar — five rules

Non-negotiable; the verify step walks them. Draw connectors **before**
nodes so z-order puts lines behind boxes.

**1. Orthogonal elbows only.** Never a diagonal line between nodes that
don't share an x or y. Every bend is a quarter-arc, radius 8. The
two-bend elbow, right-and-down (flip signs for other quadrants):

```svg
<!-- from (x1,y1) to (x2,y2), mid = (x1+x2)/2 -->
<path d="M x1,y1 H mid-8 Q mid,y1 mid,y1+8 V y2-8 Q mid,y2 mid+8,y2 H x2"/>
```

A plain `M … H` / `M … V` line is for endpoints that share an axis —
and that is the layout to prefer: align nodes so most runs are
straight, and spend elbows where the graph genuinely turns.

**2. Ports follow the travel direction.** A mainly-vertical run exits
the source's top/bottom edge and enters the destination's top/bottom
edge (single-bend L-path); left/right edges serve mainly-horizontal
runs. A vertical arrival at a side port looks like it punctures the
node face.

**3. Labels keep a visible gap.** An edge label sits above a horizontal
segment (or beside a vertical one) with **6–10px clear** between its
opaque `--paper` mask rect and the stroke — the mask stops
bleed-through, the gap keeps the line traceable. A label sitting on
its line is a hard fail. ≤14 characters, uppercase, centered on the
segment's midpoint.

**4. No two connectors merge.** Crossings get a hop on the less
important line — `a 8,8 0 0,1 16,0` mid-segment (an 8px semicircular
bridge; `a 8,8 0 0,0 0,16` for a vertical hop) — and the other line
runs unbroken. Parallel runs stay ≥16px apart end-to-end. When N
connectors share one node edge of length L, fan them: attach point *k*
sits at `L·k/(N+1)` from the corner, snapped to the grid, ≥16px
between neighbors. Two arrows sharing one attach point is a hard fail.

**5. No transit behind a non-endpoint node.** Reroute around
intervening boxes. The one exception — a box geometrically unavoidable
on the only orthogonal path — demands a dashed stroke (transit, not
interaction), the label at the visible end, and the arrowhead landing
only on the true destination. When in doubt, reroute.

## Spacing — 8px grid

Node and zone geometry (x, y, width, height), gaps, and attach points
snap to 8. Connector endpoints derive from node edges ±4px breathing
room, so path coordinates land on 4s. Text baselines are free.

Node height 56 (48 compact). Minimum gap 48 horizontal, 40 vertical.
Zone padding 24. Legend hairline ≥24 below the lowest content.
`viewBox` = content bounds + 32 margin.

## Complexity budget

| Limit | Rule |
|-------|------|
| Nodes | ≤ 9 |
| Connectors | ≤ 12 |
| Zones | ≤ 3 |
| Accent elements | ≤ 2 |

Over budget means the diagram is two diagrams: an overview figure and a
detail figure. Density is the first thing that reads as generated
output — a figure earns each element or drops it (the remove test in
the verify step).

## Legend

A horizontal strip below a full-width hairline (`--rule`, width 0.8),
never inside the diagram area. Rows are exactly the treatments and
line kinds the figure uses — nothing extra: a 12×12 `rx=3` swatch per
node treatment, a 40px line sample per connector kind, 9px legend text.
One row may name two types that share a treatment (`service · gateway`).

## Assumed markers

Any detail not verified against the real system is visibly provisional:
the node's styled rect gets `stroke-dasharray="4 3"` plus an `assumed`
tag (7px mono, `--assumed`) in its top-right; an assumed edge label is
prefixed `assumed:` in `--assumed`. Whenever any marker is used the
legend gains the row `dashed = assumed, confirm before publishing`.

## Theme mechanics

- The dark palette lives in one block:
  `@media (prefers-color-scheme: dark) { :root { … } }`. Because every
  painted element resolves a token, the whole figure flips at once —
  masks included.
- Inside `<img>` embeds (GitHub READMEs included) the query answers to
  the reader's OS/browser preference. A GitHub theme set *opposite* the
  OS won't match — the accepted trade for a single committed file. When
  a site needs exact control, emit two forced copies (`-light` /
  `-dark` suffixes, media query replaced by the fixed palette) and
  reference them with `<picture>` sources or GitHub's
  `#gh-dark-mode-only` fragment convention.
- The file stays self-contained: no scripts, no external fonts, no
  external images, no animation. Anything that moves belongs to
  `animated-diagram`.
