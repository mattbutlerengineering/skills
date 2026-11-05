# Interface pass

A deleted `aria-label` or focus style is invisible in the post-change
state: the file that remains looks fine, and lint, types and tests pass.
This pass reads what the diff took away. It applies to component files
(`*.tsx`, `*.jsx`, `*.vue`, `*.svelte`), stylesheets and server-side
templates; the table in [domain-reviewers.md](domain-reviewers.md) lists
the extensions. Follow the shared contract there.

The pass reads the diff and the changed files only. It never renders
anything and runs no browser. Whether a rendered surface works (contrast,
layout, motion) is `polish`'s judgment, not this pass's.

## The signals

Each is something a diff can delete with no test noticing:

1. `aria-label`: the accessible name of a control.
2. `alt=`: the text alternative of an image.
3. `:focus-visible` or `outline`: the visible focus indicator.
4. `tabindex`: the keyboard order and reachability.
5. `prefers-reduced-motion`: the opt-out from animation.
6. Logical properties (`margin-inline`, `padding-block`, `inset-inline-start`
   and kin) replaced by physical ones (`margin-left`, `right`), which
   breaks right-to-left layouts.
7. `lang=` or `dir=`: the language and direction of the document or a span.
8. A design token (`var(--space-4)`, a theme key) swapped for a literal
   (`16px`, `#1a1a1a`).

## How to run it

1. **Find.** Read the removed side of every hunk in the selected paths:
   `git diff -U0 -M <base>...HEAD -- <selected paths>`, then take the
   `-` lines. `-M` reads a rename as a move, not a deleted file plus an
   added one. A `-` line that carries a signal is a candidate. Drop it
   when the diff deletes its whole element or rule: the signal left with
   its owner.
2. **Clear.** A candidate is cleared when an equivalent replacement is on
   the added side for the same element or selector:
   - `outline` removed, and a `box-shadow`, a `border` or another
     `outline` value added on the same selector and state. A `:focus`
     rule rewritten as `:focus-visible` counts.
   - `aria-label` removed, and `aria-labelledby`, a `<label>` or visible
     text added that names the same element.
   - `alt=` removed and `alt` added back, or the image named by
     `aria-label` or `aria-labelledby`.
   - `tabindex` removed from an element that is natively focusable
     (`button`, `a[href]`, `input`).
   - `lang=` or `dir=` removed and set on an ancestor that the diff or
     the changed file shows.
   - A `prefers-reduced-motion` block moved, where the same animations are
     still covered. Read it; do not assume.
   - A token swapped for a literal where the changed file defines that
     token.

   A replacement on a different selector or element never clears. It is a
   finding. When a replacement may live elsewhere and you cannot read it,
   report a suspicion with what would settle it (shared contract:
   evidence or silence).
3. **Status and severity.** What is left gets one status, by cause. Put it
   in the heading: `### Major: interface — regression — <one-line
   statement>`.
   - **Regression**: the diff removes a signal from an element or rule
     that stays, with no equivalent.
   - **Introduced**: the added side carries the bad form of a listed
     signal. Three forms only: `outline: none` or `outline: 0` with no
     ring on the same selector, a positive `tabindex`, a literal where the
     surrounding code uses a token. Other added-side defects are not this
     pass's.
   - **Pre-existing**: the defect sits on a line the diff does not touch,
     in a changed file or in an unchanged consumer of a changed token.
     Report at most three, after the other two, so the cap never hides a
     regression.

   Severity is the skill's, set by the scenario, never by the status.
   Regression and Introduced are **critical** only where the scenario
   names a task a keyboard or assistive-technology user can no longer
   complete (the only accessible name of an icon-only control removed, the
   only focus indicator of a control removed). Otherwise they are
   **major**, except a token swapped for a literal, which is **minor**
   unless the file shows the theme or contrast failure it causes.
   Pre-existing is **minor** and never blocks. There is no new severity
   and the fix loop does not change.

## Worked examples

- **A bare deletion reports.** A diff removes `aria-label="Close"` from a
  `<button>` that holds only an icon, and adds nothing that names it. The
  element stays and the control now has no accessible name. Report
  `### Critical: interface — regression — close button has no accessible
  name`.
- **A same-selector swap is silent.** A diff changes `.btn:focus {
  outline: none }` to `.btn:focus-visible { box-shadow: 0 0 0 2px
  var(--ring) }`. The ring is on the same selector and state, so the
  candidate clears. Report nothing.
- **A different-selector swap reports.** A diff removes the `outline` from
  `.btn:focus-visible` and adds a `box-shadow` to `.card:hover`.
  The replacement is on another selector, so `.btn` lost its only focus
  indicator. Report `### Critical: interface — regression — .btn has no
  focus indicator` when `.btn` is a control with no other.

## Limits

- A UI written in plain `.js` or `.ts` (styled-components, template
  literals) is not selected. Widening to those extensions would select
  most diffs and teach readers to skip the pass.
- Generated output (`*.min.css`, built bundles) matches an extension and
  is skipped with a one-line note: its removed side holds no author's
  intent.
- A hunk too large to read in full is read in the selected paths only, and
  the rest is named as not read under "Passes with no findings". Never
  report it clean.
- A signal that is neither cleared nor confirmed gets a suspicion line,
  not a finding.
- No rendered or browser check. Use `polish` for that.

## What this pass does not do

- Audit the added side for every accessibility defect. That is `polish`'s
  work on a live surface.
- Grade style, coverage or ADR compliance. The other passes own those.
- Edit anything. It reads and reports.
