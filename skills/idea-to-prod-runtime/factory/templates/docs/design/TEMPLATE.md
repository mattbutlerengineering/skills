---
stage: design
run: product | feature:<slug>
date: YYYY-MM-DD
---

# Design: <title>

The visual/interaction design for a user-facing surface — the layer below UX
flows (`ux.md`) and above implementation. A pull request that touches this
directory runs the web-quality job (`.github/workflows/design.yml`):
playwright-driven UI quality, accessibility, and Core Web Vitals checks.

## Design system

Which tokens and components this surface uses. The starter set lives in
[design-system.md](design-system.md) — extend it there, don't inline values
here.

## Screens

### <Screen/surface name>

- Purpose: <the one thing the user does here>
- Layout: <grid / regions / responsive behaviour>
- Tokens used: <color / spacing / type tokens from the design system>
- States: <default, empty, loading, error, disabled>

## Accessibility

- <Contrast, focus order, keyboard paths, ARIA roles this surface must meet
  (WCAG 2.2 AA is the default target).>

## Web-quality budget

- LCP / INP / CLS targets for this surface, and any per-screen exceptions.

## Deliberately not designed

- <Deferred visual polish / out-of-scope surfaces.>
