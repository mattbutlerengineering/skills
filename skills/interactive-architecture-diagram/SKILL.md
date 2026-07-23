---
name: interactive-architecture-diagram
description: Generate an interactive architecture demo as one self-contained dark-mode HTML file — an SVG system diagram with a step-through presenter mode (narrated stages, keyboard controls), animated flow pulses along active edges, click-to-inspect detail panels, and PNG/SVG export. Use when the user wants to demonstrate or present how a system works, or asks for an interactive, animated, or step-through diagram of services, infrastructure, pipelines, or data flow.
---

# Interactive Architecture Diagram

Produce a single `.html` file that renders a dark, professional architecture
diagram in inline SVG and plays it back as a narrated, step-through demo — no
build step, no external assets or requests, opens in any browser, presentable
on a projector.

Two resources, loaded when reached:

- **`references/design-system.md`** — palette (exact hex), type scale, shape
  specs, spacing, interaction states (dimming, pulses), assumed-marker specs,
  and presenter chrome. Every visual value comes from here.
- **`assets/boilerplate.html`** — the working scaffold: themed canvas, export
  toolbar, presenter deck, inspect panel, all interaction JS, and a complete
  sample system (order pipeline) demonstrating every pattern. Copy it to the
  destination and replace the sample; never edit the asset itself.

Work these steps in order.

## 1. Model the system

Name every **node** and its **type** (service, data, storage, gateway, queue,
external, security), every **edge** (sync / async / auth) with its source and
target, and every **boundary** (VPC, region, trust zone) with the nodes it
holds. Give each node a short `data-id` and each edge an id (`e1`, `e2`, ...).

Fill a genuine gap by asking, not guessing. When a detail must be guessed to
keep moving (a trigger mechanism, an exact tool set, a deployment location),
record it as **assumed** — it gets a visible marker in step 6.

Done when: each node has one type and an id, each edge has both ends and a
kind, each boundary lists its members, and every guess is on an assumed list.

## 2. Script the story

Write the `STAGES` array before drawing — the narration drives the layout.
Stage 0 is the overview (nothing dimmed). Each later stage is one beat of the
story: a title (`1 · A request arrives`), a caption (one spoken-style sentence
a presenter could read aloud), the active node ids, and the active edge ids.

Aim for 4–7 stages. A stage may reuse nodes from earlier stages (the hub of a
pipeline stays active in most beats).

Done when: every node and edge appears in at least one stage, and the captions
read in order as a coherent 30-second narration.

## 3. Start from the scaffold

Copy `assets/boilerplate.html` to the destination filename. The shell —
canvas, grid, defs, toolbar, deck, panel, and all `<script>` machinery —
always comes from it; only the SVG content, `STAGES`, `NODE_INFO`, and the
heading/title text change.

Done when: the copy opens in a browser as the themed sample diagram and the
sample's Prev/Next stepping works.

## 4. Style from the design system

Draw each node from its **type**'s row in `references/design-system.md`: that
row is the source of its stroke and fill — color *is* the type. Text sits in
the three-tier scale.

Done when: every node's stroke and fill match its type row and every label is
in a named tier.

## 5. Lay out on the 8px grid

Snap every x/y to 8. Hold ≥40px vertical and ≥48px horizontal between nodes,
24px boundary padding. Size the `viewBox` to the content plus a 32px margin.
Behind each node, keep the opaque mask rect so edges pass under it cleanly.

Structural requirements the interactivity depends on:

- Every edge is a `<path>` with an `id` — pulses ride paths via `mpath`;
  `<line>` breaks them.
- Each edge plus its labels and pulses lives in `<g class="edgeg" data-edge="...">`;
  each node in `<g class="nodeg" data-id="...">`; each boundary in
  `<g class="boundaryg">` — the ids must match `STAGES`/`NODE_INFO`.

Done when: no two shapes overlap, every gap meets the minimum, nothing is
clipped by the viewBox, and every group carries its matching id.

## 6. Wire the interactivity

Replace the sample `STAGES` and `NODE_INFO` with the step-2 story and a panel
entry per node (name, type line, one-paragraph body, `assumed` string or
null). Add pulses per the design system: two offset pulses on short edges, one
slow pulse on long arcs. Mark every assumed detail with the assumed-marker
specs (dashed border + amber tags + panel block) and include the assumed
legend row when any is used.

Done when: each stage highlights exactly its nodes and edges with pulses
flowing, and every unverified detail is visibly amber/dashed.

## 7. Legend and edge labels

Place the legend clear of every boundary, ≥24px below the lowest, one row per
type actually used. Label an edge wherever its kind is not obvious from its
style.

Done when: the legend lists exactly the types present and touches no boundary.

## 8. Verify the render

Open the file in a browser. Confirm: it is one self-contained `.html` (no
external requests), stepping traverses every stage forward and back (buttons
and `→`/`←`), each node click opens the correct panel, the console shows no
errors, and PNG export downloads a correct image.

Capture caveat: CDP-based screenshot tools can hang on the infinite pulse
animations. For programmatic screenshots use headless Chrome directly
(`chrome --headless=new --screenshot=out.png <file-url>`), or call
`document.getElementById('diagram').pauseAnimations()` first. To capture a
mid-story state, screenshot a throwaway copy with `<script>setStage(N)</script>`
appended before `</body>`.

Done when: it renders standalone, the full story plays, and PNG export
produces the right image.
