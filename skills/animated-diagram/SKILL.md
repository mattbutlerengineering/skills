---
name: animated-diagram
description: Generate an ambient animated diagram as one self-contained dark-mode file — .html with a pause control, or a pure .svg whose SMIL/CSS motion plays right inside a GitHub README image embed — an inline-SVG flow or architecture picture whose dashed connectors stream in the direction of execution and whose traveling dots trace the request path, looping forever, with reduced-motion support. Use when the user wants a diagram that moves on its own — animated, flowing, alive — for a README, docs page, or landing page, or wants an existing mermaid flowchart or state diagram turned into an animated version. Narrated step-through presenting is interactive-architecture-diagram; a still, designed architecture figure is architecture-diagram; a quick markdown-source diagram is mermaid.
---

# Animated Diagram

Produce a single file — `.html` or pure `.svg` — that renders a dark,
professional diagram in inline SVG and animates it ambiently — dashed
connectors visibly streaming from source to target, a few dots traveling
the paths a request takes — with no build step, no external assets or
requests, looping seamlessly forever. It is scenery, not a presentation:
nothing to click, nothing to narrate. The `.html` form embeds wherever an
`<iframe>` or a browser tab fits; the `.svg` form embeds as a plain
markdown image, and GitHub plays its motion right in the README.

Two resources, loaded when reached:

- **`references/design-system.md`** — palette (exact hex), type scale, shape
  specs, connector routing rules, spacing, the complexity budget, the two
  mode layouts, the two output targets, and the animation contract: dash
  periods, offset arithmetic, dot counts and staggering, pause and
  reduced-motion behavior. Every visual and timing value comes from here.
- **`assets/boilerplate.html`** / **`assets/boilerplate.svg`** — the working
  scaffolds, one per output target, drawing the same sample system (order
  intake) that demonstrates every pattern — flowing sync connectors, a
  dotted async branch with an elbow, a masked edge label, staggered
  traveling dots, a boundary, a legend. The html one carries the page
  frame, pause toggle, and reduced-motion script; the svg one is
  script-free with CSS-only reduced motion. Copy one to the destination
  and replace the sample; never edit the assets themselves.

Work these steps in order.

## 1. Pick the output target and the mode

Format first, by destination: a README or any markdown page takes the
**`.svg`** target; a docs page, landing page, or anything that can host an
HTML file (or an `<iframe>`) takes **`.html`**, which brings the pause
button. Then the mode:

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

Done when: one output target and one mode are chosen and, for mermaid
input, the source parses in your head — you can list its nodes, edges,
and subgraphs.

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

Hold the model against the complexity budget (≤7 nodes, ≤10 connectors,
≤3 boundaries — motion tolerates less density than a still figure): a
model over budget is two diagrams, an overview and a detail, not one
denser diagram.

Done when: each node has one type, each edge has ends and a kind, each
boundary lists its members, the model fits the budget (or has been
split), and (for mermaid input) a source-to-model walkthrough finds
nothing missing.

## 3. Start from the scaffold

Copy the chosen scaffold — `assets/boilerplate.html` or
`assets/boilerplate.svg` — to the destination filename. The shell —
canvas, grid, defs, and (html) the pause button and reduced-motion
script, or (svg) the CSS-only reduced-motion block and `<title>`/`<desc>`
— always comes from it; only the SVG content and the heading/title text
change.

Done when: the copy opens in a browser as the themed sample with its
connectors flowing — and, for the html target, the pause button freezes
it.

## 4. Lay out on the 8px grid

Snap every x/y to 8. Flow mode reads top-to-bottom (or left-to-right when
wide and shallow); architecture mode reads left-to-right along the request
path. Hold ≥40px vertical and ≥48px horizontal between nodes, 24px boundary
padding, `viewBox` = content + 32px margin. Author every connector `d` from
**source to target** — the animation contract depends on path direction —
and stop it 4px short of the node edge so the arrowhead breathes. Route per
the design system's five connector rules: orthogonal r=8 elbows for
off-axis runs (never a diagonal), ports chosen by travel direction, labels
masked with a visible 6–10px gap off the stroke, crossings hopped and
shared attach points fanned, no transit behind a non-endpoint node. Behind
each node, keep the opaque mask rect so connectors and dots pass under it
cleanly.

Z-order is fixed: grid → boundaries → connectors → dots → nodes → labels →
legend.

Done when: no two shapes overlap, every gap meets the minimum, nothing is
clipped, every off-axis run is an elbow, and every connector's `d` runs
source → target.

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

Open the file in a browser. Confirm: it is one self-contained file (no
external requests, no scripts in the `.svg` target), the motion loops
seamlessly, and — html — the pause button freezes and resumes it with no
console errors. Check reduced-motion by emulating
`prefers-reduced-motion: reduce` (DevTools → Rendering) and reloading —
the diagram must come up still (svg: dashes static, dots gone). For the
`.svg` target, also embed it as an image (`<img src>` or markdown
`![]()`) and confirm the motion still plays there. For mermaid input,
re-walk the source against the render: every node, edge, edge label, and
subgraph present, verbatim.

Capture caveat: CDP-based screenshot tools can hang on the infinite
animations. For programmatic screenshots use headless Chrome directly
(`chrome --headless=new --screenshot=out.png <file-url>`), or call
`document.getElementById('diagram').pauseAnimations()` first.

Done when: it renders standalone (and embedded, for svg), loops clean,
pauses (html), respects reduced motion, and (for mermaid input) the
fidelity walkthrough passes.
