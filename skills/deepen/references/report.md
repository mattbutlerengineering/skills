# The review report

One self-contained HTML file, written to the OS temp directory — never
into the repo. Resolve the temp dir from `$TMPDIR`, falling back to
`/tmp` (`%TEMP%` on Windows), and write
`<tmpdir>/deepen-<repo>-<timestamp>.html` so each run gets its own file
and no run overwrites the last one's evidence. Open it (`open` on macOS,
`xdg-open` on Linux, `start` on Windows) and print the absolute path.

## Self-contained means no network

No CDN, no remote font, no remote script, no remote stylesheet. Write the
CSS by hand and draw the diagrams as inline SVG.

This is not a preference. A report that fetches Tailwind and Mermaid at
open time is a report that renders differently on a plane, blank behind a
strict content-security policy, and differently again the week a CDN
moves a major version — and it fails *silently*, as an unstyled page or a
missing diagram, which is exactly how an unreliable check looks when it
has stopped checking. Everything the file needs is in the file.

A hand-written stylesheet is also less work than it sounds here: the
report is a header, a stack of cards, and diagrams. That is a hundred
lines of CSS, and it costs nothing at open time.

Make it theme-aware — `@media (prefers-color-scheme: dark)` — and let
wide content scroll inside its own container rather than the page.

## Shape

Header: repo name, the commit the review was taken at, the date, and a
compact legend (solid box = module, dashed line = seam, red edge =
leakage, heavy box = deep module). No introduction. Straight into the
candidates.

Then one `<article>` per candidate, then a top-recommendation card, then
the coverage note.

## The card

- **Title** — names the deepening, imperative: "Collapse the order
  intake pipeline".
- **Badges** — recommendation strength (`Strong`, `Worth exploring`,
  `Speculative`) and the dependency category (`in-process`,
  `local-substitutable`, `ports & adapters`, `mock`).
- **Evidence** — monospaced, and it is not decoration: the files and line
  ranges, the number of call sites the deletion test actually walked, and
  the interface as it reads today. A card whose evidence block says
  "several places" is a card that was not checked.
- **Before / after** — two columns, side by side. The diagram carries the
  argument; see the patterns below.
- **Problem** — one sentence. What hurts, in glossary terms.
- **Solution** — one sentence. What changes.
- **Wins** — bullets, six words or fewer, each naming leverage,
  locality, or a test that gets simpler. "Easier to maintain" is not a
  win; it is a feeling.
- **Cost** — the other half, and never omitted: which tests must be
  written first, which existing tests die, how many call sites move, and
  what gets harder. A card with wins and no cost has not been thought
  through.
- **Decision callout** — when the candidate touches a recorded decision,
  one line naming it and its status (see `SKILL.md` step 1).

If a diagram needs a paragraph to be understood, redraw the diagram.

## Diagram patterns

Pick per candidate; vary them. All inline SVG or styled divs.

- **Boxes and arrows** — modules as bordered boxes, arrows as SVG paths.
  The workhorse for "A calls B calls C, and look where pricing leaks".
  Dash the seam lines; colour only the leaking edge.
- **Cross-section** — stacked horizontal bands for layered shallowness.
  Before: six thin layers each doing nothing. After: one thick band with
  the consolidated responsibility named.
- **Mass diagram** — two rectangles per module, interface surface against
  implementation. Shallow: nearly equal heights. Deep: short interface,
  tall implementation. The most direct rendering of depth there is.
- **Call-graph collapse** — before, a tree of nested boxes; after, one
  box with the now-internal calls faded inside it.

Keep them around 320px tall so before and after sit side by side without
scrolling. Module labels read as schematic — small, uppercase, tracked.

## Style

Editorial, not dashboard. Generous whitespace, one accent colour, red
reserved for leakage and amber for decision callouts. Prose sparse and
plain, but every architectural noun comes from
[`language.md`](language.md) — concision is not licence to drift into
"component", "service", or "boundary".

Phrasings that fit:

- "Order intake is shallow — the interface nearly matches the implementation."
- "Pricing leaks across the seam."
- "Two adapters justify the seam: HTTP in production, in-memory in tests."
- "Deepen: one interface, one place to test."

No hedging, no throat-clearing. If a sentence could be a bullet, make it
one; if a bullet could be cut, cut it.

## The coverage note

Last section, and it is not optional: what this review did **not** look
at — the directories the sweep never reached, the categories of friction
not examined, and the candidates considered and dropped, with one line
each. A report that lists only what it found reads as a complete survey
of the codebase, and it is never that.
