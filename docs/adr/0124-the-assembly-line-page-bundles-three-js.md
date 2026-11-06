# The assembly-line page bundles three.js

- Status: accepted
- Date: 2026-11-05

Every skill and root tool in this plugin is first-party: Python is
standard library only (`stdlib-only` in `docs/standards.json`), the
diagram skills write hand-authored SVG and HTML, and each output is one
self-contained file that makes no external requests. The assembly-line
feature (docs/features/assembly-line/) asks for an animated isometric
factory in the style of the Owner's reference illustrations: outlined
flat-shaded machines, articulated robot arms, belts that turn corners,
about 100 moving crates, and hover picking. Drawing and depth-sorting
that by hand in Canvas 2D or SVG is a large, bespoke renderer; a WebGL
library with an orthographic camera gives the exact projection,
per-face colours, edge lines and picking for free. The Owner chose the
library on 2026-11-05, knowing it is the plugin's first third-party
code.

## Decision

The assembly-line page bundles three.js. A pinned release (v0.187.0,
MIT) is vendored under `vendor/three/` with its licence file, recorded
in `NOTICE`, and carried by `npx_bundle.py` like `dashboard.html`. The
root tool `assembly_line.py` inlines the vendored build into every page
it writes, so the page stays one self-contained file with no network
request. The library is used only inside that page; no Python module
imports or reads it beyond copying its text, so `stdlib-only` is
untouched. Its interface is narrow: the scene builder, the camera, edge
lines, the raycaster and one renderer, all inside the page template.

## Consequences

- The plugin now ships third-party code. Updating it is a deliberate
  version bump of the vendored files, never a floating fetch, and a
  security fix upstream is ours to notice.
- Each page carries about 814 KB of library text before compression;
  fine for a local or Pages-hosted file, too heavy for anything that
  inlines pages repeatedly.
- The page needs WebGL. Where it is missing the page falls back to a
  plain per-station list (docs/features/assembly-line/ux.md), so the
  work stays visible, but the factory does not.
- A README cannot run it. Adopters see an exported GIF that links to
  the page, not the page itself.
- This is not a general licence for third-party code in skills: the
  next library needs its own record that it buys something no
  first-party file can.
