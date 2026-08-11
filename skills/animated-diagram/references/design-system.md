# Design system — professional dark, ambient motion

The source for every visual and timing value. `assets/boilerplate.html`'s
`:root` and CSS classes mirror the palette below; change a color in one
place and match it in the other. The palette is shared with the
`interactive-architecture-diagram` skill so the two families of diagram
read as one system.

The look is **flat and precise**: restrained accents on a deep slate
canvas, one soft shadow for lift, no neon glow. Color earns its place by
encoding a node's **type**; motion earns its place by encoding
**direction** — anything that moves must mean "this way".

## Contents

- [Canvas](#canvas) · [Text tiers](#text--three-tiers)
- [Node types](#node-types--color-is-the-type) · [Shapes](#shapes)
- [Spacing](#spacing--8px-grid) · [The two modes](#the-two-modes)
- [Animation contract](#animation-contract) — dashes, dots, timing
- [Pause and reduced motion](#pause-and-reduced-motion)
- [Assumed markers](#assumed-markers)

## Canvas

| Role | Value |
|------|-------|
| Background | `#0d1117` |
| Dot grid | `#1c2128` |
| Node surface (mask) | `#161b22` |
| Default border | `#30363d` |
| Connector | `#6e7681` |
| Dot (traveling) | node-type accent of its destination, else `#4493f8` |

## Text — three tiers

| Tier | Value | Use |
|------|-------|-----|
| Primary | `#e6edf3` | node titles — 13px / 600 sans |
| Secondary | `#8b949e` | sublabels, edge labels — 11px sans / 10px mono |
| Tertiary | `#6e7681` | annotations, boundary + legend labels — 9px / 500, uppercase, `letter-spacing 0.04em` |

Sans: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`
Mono: `ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace`

System stacks keep the file self-contained. A pinned web font is the one
allowed exception.

## Node types — color *is* the type

Each node draws with its type's stroke and fill. The fill is a hint
(~0.10–0.12 alpha); the stroke carries the meaning.

**Architecture mode:**

| Type | Meaning | Stroke | Fill |
|------|---------|--------|------|
| service | app / compute / API | `#4493f8` | `rgba(68,147,248,0.12)` |
| data | database / store of record | `#a371f7` | `rgba(163,113,247,0.12)` |
| storage | cache / object / block store | `#39c5cf` | `rgba(57,197,207,0.10)` |
| gateway | load balancer / gateway / edge | `#3fb950` | `rgba(63,185,80,0.12)` |
| queue | event / message bus | `#d29922` | `rgba(210,153,34,0.12)` |
| external | third-party / SaaS / client | `#8b949e` | `rgba(139,148,158,0.10)` |
| security | auth / secrets / trust zone | `#e5606a` | `rgba(229,96,106,0.12)` |

**Flow mode:**

| Type | Meaning | Stroke | Fill |
|------|---------|--------|------|
| start | entry pill | `#3fb950` | `rgba(63,185,80,0.12)` |
| step | process box | `#4493f8` | `rgba(68,147,248,0.12)` |
| decision | branch diamond | `#d29922` | `rgba(210,153,34,0.12)` |
| end | exit pill | `#a371f7` | `rgba(163,113,247,0.12)` |

## Shapes

- **Node** — rounded rect `rx=8`, `stroke-width=1.5`,
  `filter=url(#soft-shadow)`. Draw an opaque `#161b22` mask rect first,
  then the styled rect over it, so connectors and dots pass under the node
  cleanly.
- **Pill** (flow `start`/`end`) — height 40, `rx=20` (rx = height/2).
- **Decision** — a rotated square (`transform="rotate(45 …)"`, side ≈ 64)
  or an `rx=8` rect when the label is long; the amber stroke carries the
  meaning either way. Label its outgoing edges (`yes` / `no`).
- **Boundary** — rounded rect `rx=12`, fill `rgba(255,255,255,0.015)`,
  stroke `#30363d` width `1.25`, `stroke-dasharray="6 4"` — boundaries do
  **not** animate; only connectors flow. Label top-left, tertiary tier.
- **Connector** — a `<path>` with an `id`, `fill="none"` (a filled path
  renders as a black blob — this is the classic defect), stroke `#6e7681`
  width `1.5`, `marker-end=url(#arrow)`, authored **source → target**,
  endpoints stopping 4px short of node edges.

## Spacing — 8px grid

Snap every coordinate to 8. Node height 56 (48 for compact steps, 40 for
pills). Minimum gap 40 vertical, 48 horizontal. Boundary padding 24.
Legend ≥24 below the lowest content. `viewBox` = content bounds + 32
margin.

## The two modes

- **Flow mode** — top-to-bottom (left-to-right when wide and shallow).
  One `start` pill, one `end` pill where the process genuinely ends.
  Branches leave a `decision` with labeled edges; merges rejoin before a
  shared step. Every path from start reaches an end.
- **Architecture mode** — left-to-right along the main request path
  (client → edge → services → stores), with fan-outs stacked vertically
  and async spurs (queues, workers) below the main line. Boundaries group
  deployment or trust zones.

## Animation contract

Motion is CSS `stroke-dashoffset` for connectors and SMIL `animateMotion`
for dots. Both loop indefinitely; both must loop **seamlessly**.

**Flowing connectors (sync):**

- `stroke-dasharray: 6 6` — period 12.
- `@keyframes dashflow { to { stroke-dashoffset: -12; } }` — the offset
  delta MUST equal one full dash period (here 6+6=12) or the loop snaps
  visibly at each cycle.
- Negative offset flows in the path's drawing direction — which is why
  every connector `d` is authored source → target.
- `animation: dashflow 0.8s linear infinite`. 0.6–0.9s reads as current
  flowing; slower than 1.5s reads as broken.

**Async connectors:**

- `stroke-dasharray: 2 5` — period 7; offset delta `-7`.
- `animation-duration: 1.2s` — visibly lazier than the sync lines.

**Traveling dots:**

- `<circle class="dot" r="3">` +
  `<animateMotion dur="2.4s" repeatCount="indefinite"><mpath href="#e1"/></animateMotion>`
  — the `mpath` reuses the connector's path verbatim, so the dot cannot
  drift from its line.
- 3–6 dots per diagram, total. Place them only where direction is
  informative: the main request path, a fan-out, a merge. More reads as
  confetti.
- Stagger with `begin` offsets (`begin="-1.2s"` starts mid-cycle — no
  dead first cycle). Two dots on one path ride at half-period spacing.
- `dur` scales with path length: ~2s for a short hop, up to ~3.5s for a
  long arc, so dots on different paths move at comparable speed.

## Pause and reduced motion

Non-negotiable accessibility, wired in the boilerplate — reuse, don't
reinvent:

- All CSS animation lives inside
  `@media (prefers-reduced-motion: no-preference)` — with reduced motion
  set, the dashes are simply static.
- SMIL ignores that media query, so the script calls
  `svg.pauseAnimations()` when `matchMedia('(prefers-reduced-motion: reduce)')`
  matches at load.
- The pause button toggles both worlds at once: `svg.pauseAnimations()` /
  `svg.unpauseAnimations()` plus a `paused` class on `<body>` that sets
  `animation-play-state: paused` and hides the dots (`.paused .dot
  { opacity: 0 }`) — a paused diagram reads as a clean static diagram,
  not a freeze-frame with stranded dots.

## Assumed markers

Any detail not verified against the real system must be visibly
provisional: node gets class `assumed` (dashed border
`stroke-dasharray: 4 3`) plus an amber `assumed` tag top-right; an
assumed edge label is amber `#d29922` prefixed `assumed:`; and the legend
gains the row `dashed = assumed, confirm before publishing` whenever any
marker is used.
