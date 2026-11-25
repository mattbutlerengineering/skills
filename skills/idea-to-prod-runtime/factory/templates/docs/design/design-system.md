---
stage: design
run: product
date: YYYY-MM-DD
---

# Design system

The starter design-system seed a stamped repo receives: a minimal, neutral set
of design tokens for a new product's web surface. Replace the placeholder
values with the product's own; keep the token names so screens in `design.md`
can reference them stably.

Tokens are expressed as CSS custom properties — the single source of truth a
web app reads. Light and dark are both defined; a surface must be legible in
either (the web-quality job checks contrast).

## Color

```css
:root {
  --color-bg: #ffffff;
  --color-surface: #f5f5f5;
  --color-text: #1a1a1a;
  --color-text-muted: #5c5c5c;
  --color-primary: #2563eb;
  --color-primary-text: #ffffff;
  --color-border: #d4d4d4;
  --color-danger: #dc2626;
  --color-success: #16a34a;
}

:root[data-theme="dark"] {
  --color-bg: #0f0f0f;
  --color-surface: #1a1a1a;
  --color-text: #f5f5f5;
  --color-text-muted: #a3a3a3;
  --color-primary: #60a5fa;
  --color-primary-text: #0f0f0f;
  --color-border: #333333;
  --color-danger: #f87171;
  --color-success: #4ade80;
}
```

## Spacing

An 8px base scale. Use the tokens, not raw pixels.

```css
:root {
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 32px;
  --space-6: 48px;
}
```

## Typography

```css
:root {
  --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.25rem;
  --text-xl: 1.75rem;
  --leading-body: 1.5;
  --leading-heading: 1.2;
}
```

## Radius and elevation

```css
:root {
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-full: 9999px;
  --shadow-1: 0 1px 2px rgba(0, 0, 0, 0.08);
  --shadow-2: 0 4px 12px rgba(0, 0, 0, 0.12);
}
```

## Components

Name the components this system defines and where they live once built
(button, input, card, dialog, ...). Keep the list in step with the code — a
component here with no implementation, or one implemented but undocumented, is
drift.

- Button — `<path once built>`
- Input — `<path once built>`
- Card — `<path once built>`
