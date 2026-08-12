---
name: architecture-diagram
description: Generate a static architecture diagram as one self-contained theme-aware .svg file — a designed system figure in a light editorial style (warm paper, ink strokes, a single accent on the focal node) that flips to the family's dark palette via prefers-color-scheme, embeds directly in GitHub READMEs, docs pages, and design docs as an image, and makes no external requests. Use when the user wants a polished, committed architecture picture — services, infrastructure, data flow, topology — with no motion and no interactivity. A diagram that moves on its own is animated-diagram; a narrated step-through HTML demo is interactive-architecture-diagram; a quick diagram pasted into markdown as text is mermaid.
---

# Architecture Diagram

Produce a single `.svg` file that renders a designed, still architecture
figure — warm paper, ink strokes, one accent — and adapts itself to the
reader's light or dark preference. No scripts, no external assets or
requests: it embeds anywhere an image does, `<img>` tag or markdown
image syntax, GitHub READMEs included.

Two resources, loaded when reached:

- **`references/design-system.md`** — theme-aware tokens, typography,
  node treatments, the connector grammar (elbows, ports, label gaps,
  hops, fanning), spacing, complexity budget, legend and assumed-marker
  specs. Every visual value comes from here.
- **`assets/boilerplate.svg`** — the working scaffold: theme-aware
  styles, arrow marker, and a complete sample system (order intake)
  demonstrating every pattern — header block, a zone, straight and
  elbowed connectors, masked edge labels, a focal node, the legend
  strip. Copy it to the destination and replace the sample; never edit
  the asset itself.

Work these steps in order.

## 1. Model the system

Name every **node** and its **type** (service, data, storage, gateway,
queue, external, security), every **edge** (sync / async) with its
source and target, and every **boundary** (VPC, region, trust zone)
with the nodes it holds. Give each node a short id and each edge an id
(`e1`, `e2`, ...).

Fill a genuine gap by asking, not guessing. A detail guessed to keep
moving is recorded and marked assumed per the design system.

Done when: each node has one type and an id, each edge has both ends
and a kind, each boundary lists its members, and every guess is on an
assumed list.

## 2. Budget the figure

Pick the **focal element** — the one or two nodes or edges the reader
should find first; only they get the accent. Then hold the model
against the complexity budget (≤9 nodes, ≤12 connectors, ≤3 zones): a
model over budget is two figures — an overview and a detail — not one
denser figure. If a table or a paragraph would carry the content as
well as a picture, say so instead of drawing.

Done when: the focal choice is made, the model fits the budget (or has
been split), and the figure has a one-line story you could use as its
subtitle.

## 3. Start from the scaffold

Copy `assets/boilerplate.svg` to the destination filename. The shell —
theme-aware `<style>` tokens, arrow marker, header block, legend
hairline — always comes from it; only the SVG content and the title
text change.

Done when: the copy opens in a browser as the themed sample, and
flipping the OS (or DevTools) color scheme flips the whole figure.

## 4. Lay out on the 8px grid

Snap node and zone geometry to 8. The main request path reads left to
right; fan-outs stack vertically; async spurs sit below the main line.
**Prefer layouts where connected nodes share an axis** — a straight
line beats an elbow the grammar would otherwise demand. Hold ≥48px
horizontal and ≥40px vertical between nodes, 24px zone padding,
`viewBox` = content + 32px margin, legend hairline ≥24px below the
lowest content.

Z-order is fixed: background → zones → connectors → edge labels →
nodes → legend.

Done when: no two shapes overlap, every gap meets the minimum, nothing
is clipped, and most connectors run straight.

## 5. Route the connectors

Apply the five connector rules from the design system, in force for
every edge: orthogonal elbows (r=8) for off-axis runs — never a
diagonal; ports chosen by travel direction (vertical runs use
top/bottom edges); labels masked with a visible 6–10px gap off the
stroke; no two connectors merging — hop the less important line at a
crossing, keep parallels ≥16px apart, fan shared-edge attach points;
no transit behind a non-endpoint node. Endpoints stop 4px short of
node edges. Async edges are dashed at width 1; dash is semantic
weight, not a different routing grammar.

Done when: every off-axis run is an elbow, every crossing has one hop,
no attach point is shared, and every connector is traceable end to end
at a glance.

## 6. Label, accent, legend

Style each node from its type's treatment row — ink at opacity, not a
hue per type; the accent appears only on the focal element(s) chosen
in step 2. Label an edge only where its meaning isn't obvious from the
style, ≤14 uppercase characters. Legend rows for exactly the
treatments and connector kinds present, below the hairline. Mark any
assumed detail per the design system.

Done when: accent elements number ≤2, every label earns its place, and
the legend lists exactly what the figure uses.

## 7. Verify both themes

Open the file in a browser. Confirm: it is one self-contained `.svg`
(no scripts, no external requests), light mode reads as a designed
document figure, and emulating `prefers-color-scheme: dark` (DevTools →
Rendering) flips every element — no stranded light-mode color, masks
included. Embed it as an image (`<img src>` or markdown `![]()`) and
confirm it renders identically. Then run the remove test: any node,
edge, or label whose removal loses nothing gets removed.

Note for GitHub: inside `<img>` embeds the theme follows the reader's
OS/browser preference, not GitHub's own theme setting; when exact
control matters, emit forced `-light`/`-dark` copies per the design
system's theme mechanics.

Done when: both themes render clean standalone and embedded, and the
remove test deleted nothing — or what it deleted is gone.
