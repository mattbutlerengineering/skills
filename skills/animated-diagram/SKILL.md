---
name: animated-diagram
description: Generate an ambient animated diagram as one self-contained dark-mode HTML file — an inline-SVG flow or architecture picture whose dashed connectors stream in the direction of execution and whose traveling dots trace the request path, looping forever, with a pause control and reduced-motion support. Use when the user wants a diagram that moves on its own — animated, flowing, alive — for a README, docs page, or landing page, or wants an existing mermaid flowchart or state diagram turned into an animated version. Narrated step-through presenting is interactive-architecture-diagram; a static markdown-embeddable diagram is mermaid.
---

# Animated Diagram

Produce a single `.html` file that renders a dark, professional diagram in
inline SVG and animates it ambiently — dashed connectors visibly streaming
from source to target, a few dots traveling the paths a request takes — with
no build step, no external assets or requests, looping seamlessly forever.
It is scenery, not a presentation: nothing to click, nothing to narrate,
embeddable wherever an `<iframe>` or a browser tab fits.

Two resources, loaded when reached:

- **`references/design-system.md`** — palette (exact hex), type scale, shape
  specs, spacing, the two mode layouts, and the animation contract: dash
  periods, offset arithmetic, dot counts and staggering, pause and
  reduced-motion behavior. Every visual and timing value comes from here.
- **`assets/boilerplate.html`** — the working scaffold: themed canvas, pause
  toggle, reduced-motion wiring, and a complete sample system (order intake)
  demonstrating every pattern — flowing sync connectors, a dotted async
  branch, staggered traveling dots, a boundary, a legend. Copy it to the
  destination and replace the sample; never edit the asset itself.

Work these steps in order.

## 1. Pick the mode

- **Flow mode** — a process: workflow, pipeline, state machine. Reads
  START → END through branches and merges; execution direction is the story.
- **Architecture mode** — a system: services, infrastructure, topology.
  Composition is the story; animation shows the journey a request takes
  through it.

Mermaid input routes the same way: `flowchart`/`graph` and
`stateDiagram-v2` sources describe flow mode unless the nodes are plainly
components (services, databases, gateways), in which case they describe
architecture mode. Other mermaid types are out of scope — say so rather
than approximating.

Done when: one mode is chosen and, for mermaid input, the source parses in
your head — you can list its nodes, edges, and subgraphs.

## 2. Model the graph

Name every **node** with a type — flow mode: `start`, `step`, `decision`,
`end`; architecture mode: `service`, `data`, `storage`, `gateway`, `queue`,
`external`, `security`. Name every **edge** with source, target, kind
(sync / async), and optional label. Name every **boundary** (subgraph, VPC,
trust zone) with the nodes it holds. Give each node a short id and each
edge an id (`e1`, `e2`, ...).

**Mermaid fidelity is non-negotiable:** every node label, every edge and
edge label, every subgraph and its containment, and every edge kind
(`-->` sync, `-.->` async/dotted) from the source appears in the model —
verbatim labels, nothing invented, nothing dropped. Layout and color are
yours to recompute; content is not.

Fill a genuine gap by asking, not guessing; a detail guessed to keep moving
is recorded and marked assumed per the design system.

Done when: each node has one type, each edge has ends and a kind, each
boundary lists its members, and (for mermaid input) a source-to-model
walkthrough finds nothing missing.

## 3. Start from the scaffold

Copy `assets/boilerplate.html` to the destination filename. The shell —
canvas, grid, defs, pause button, reduced-motion script — always comes from
it; only the SVG content and the heading/title text change.

Done when: the copy opens in a browser as the themed sample with its
connectors flowing, and the pause button freezes it.

## 4. Lay out on the 8px grid

Snap every x/y to 8. Flow mode reads top-to-bottom (or left-to-right when
wide and shallow); architecture mode reads left-to-right along the request
path. Hold ≥40px vertical and ≥48px horizontal between nodes, 24px boundary
padding, `viewBox` = content + 32px margin. Author every connector `d` from
**source to target** — the animation contract depends on path direction —
and stop it 4px short of the node edge so the arrowhead breathes. Behind
each node, keep the opaque mask rect so connectors and dots pass under it
cleanly.

Z-order is fixed: grid → boundaries → connectors → dots → nodes → labels →
legend.

Done when: no two shapes overlap, every gap meets the minimum, nothing is
clipped, and every connector's `d` runs source → target.

## 5. Animate per the contract

Style each node from its type's row and each connector from its kind's row
in `references/design-system.md`, then apply the animation contract:

- Sync connectors carry the flowing-dash animation — the offset delta must
  equal one full dash period or the loop visibly snaps.
- Async connectors are dotted and slower.
- Place 3–6 traveling dots total, only where direction is informative — the
  main request path, a fan-out, a merge. Each dot's `animateMotion` reuses
  its connector's `d` verbatim; stagger starts with `begin` offsets
  (negative offsets fill the first cycle).

Done when: every connector streams toward its arrowhead, the loop has no
visible seam, and the dots read as traffic rather than confetti.

## 6. Legend and labels

Legend rows for exactly the node types present plus the connector kinds
used (flowing = sync, dotted = async), placed clear of every boundary.
Label an edge only where its meaning isn't obvious from the style; mark any
assumed detail per the design system's assumed specs.

Done when: the legend lists exactly what the diagram uses and touches
nothing.

## 7. Verify the render

Open the file in a browser. Confirm: it is one self-contained `.html` (no
external requests), the motion loops seamlessly, the pause button freezes
and resumes it, and the console shows no errors. Check reduced-motion by
emulating `prefers-reduced-motion: reduce` (DevTools → Rendering) and
reloading — the diagram must come up still. For mermaid input, re-walk the
source against the render: every node, edge, edge label, and subgraph
present, verbatim.

Capture caveat: CDP-based screenshot tools can hang on the infinite
animations. For programmatic screenshots use headless Chrome directly
(`chrome --headless=new --screenshot=out.png <file-url>`), or call
`document.getElementById('diagram').pauseAnimations()` first.

Done when: it renders standalone, loops clean, pauses, respects reduced
motion, and (for mermaid input) the fidelity walkthrough passes.
