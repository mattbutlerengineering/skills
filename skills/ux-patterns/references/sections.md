# The sections, where to look, and a starter rule for each

Each section says what question it settles, where in the code the
current answer usually lives, and one **checkable starter rule**. A
starter rule is a default to propose, not to impose: adopt it only when
the code already agrees with it or the owner chooses it.

The rule style — short, specific, testable against one screen — follows
Vercel's [web-interface-guidelines](https://github.com/vercel-labs/web-interface-guidelines).
Its figures (hit sizes, durations) are that project's guidance, and the
accessibility thresholds are WCAG 2.2's; neither is a universal law.

## Surface jobs

- **Settles:** which routes are *convince* (landing, pricing), *work*
  (app screens, settings) or *read* (docs, help) — the taxonomy the
  polish skill uses. Rules below may differ by job.
- **Look in:** the router or page directory.
- **Starter:** "Every route is listed under exactly one job."

## Feedback and loading

- **Settles:** skeleton or spinner, when either appears, what a busy
  button does, optimistic updates.
- **Look in:** spinner, skeleton and progress components; `isLoading`,
  `pending`, `Suspense` boundaries; mutation hooks.
- **Starter:** "A wait under about 300 ms shows nothing; a longer one
  shows a skeleton shaped like the content. A busy button keeps its
  label, disables, and shows progress inside itself."

## Errors

- **Settles:** where an error appears by severity, what is kept, how it
  is announced.
- **Look in:** error boundaries, toast and alert calls in `catch`
  blocks, form error components, API error mappers.
- **Starter:** "A field error appears inline under its field; a
  page-level failure in a banner at the top of the content; only an
  error that blocks all further work uses a dialog. Input is never
  cleared by an error."

## Empty states

- **Settles:** what each kind of empty shows — first use, no results,
  filtered out, no permission, failed to load.
- **Look in:** list and table components; `length === 0` branches;
  empty-state components.
- **Starter:** "Every list has a designed first-use empty state with one
  action that adds the first item; a no-results state offers to clear
  the search."

## Destructive actions and undo

- **Settles:** confirm or undo, and which actions get which.
- **Look in:** `confirm(` calls, confirmation dialogs, delete and
  archive handlers, soft-delete columns, toast actions.
- **Starter:** "A reversible destructive action happens at once and
  offers undo in a toast; an irreversible one confirms in a dialog that
  names the object and whose confirm button repeats the verb."

## Forms and validation

- **Settles:** when validation runs, where messages show, required and
  optional marking, what submit does.
- **Look in:** the form library, validation schemas, input components.
- **Starter:** "Fields validate on blur and on submit, never on each
  keystroke before the first blur. Submit is never disabled to signal
  invalid input; it runs validation and focuses the first error. Paste
  is never blocked."

## Notifications

- **Settles:** what is a toast, a banner, an inline message, or nothing;
  how long a toast stays; where it appears.
- **Look in:** toast and notify calls, notification centre components.
- **Starter:** "Toasts confirm an action the person just took and stay
  long enough to read and act on; anything that needs action later is
  not a toast. Toasts are announced through a live region."

## Navigation and URL state

- **Settles:** what is in the URL, what back does, how deep links work,
  links versus buttons.
- **Look in:** router configuration, `Link` versus `onClick` navigation,
  search-param usage, tab and filter state.
- **Starter:** "Filters, tabs, sort order and pagination live in the
  URL, so back and a shared link restore them. Anything that navigates
  is a link; anything that acts is a button."

## Tables, lists, search and filter

- **Settles:** pagination or infinite scroll, bulk actions, default
  sort, what a search matches.
- **Look in:** table and list components, query hooks with `page` or
  `cursor`.
- **Starter:** "Lists people return to use pagination with the page in
  the URL; feeds use infinite scroll. Bulk actions appear only after a
  selection and say how many items they affect."

## Modals and pages

- **Settles:** what deserves a dialog, a drawer, or its own page.
- **Look in:** dialog, drawer and sheet components and what opens them.
- **Starter:** "A dialog holds one short task and nothing that needs its
  own URL; anything longer or linkable is a page. Escape closes a dialog
  and focus returns to what opened it."

## Focus and keyboard

- **Settles:** focus visibility, focus movement after actions, keyboard
  shortcuts.
- **Look in:** focus styles, `tabIndex`, `autoFocus`, key handlers,
  shortcut registries.
- **Starter:** "Everything a pointer can do, a keyboard can do. Focus is
  always visible and never hidden behind a sticky header. After a dialog
  closes or an item is deleted, focus moves somewhere predictable and
  named in this rule."

## Hit targets and input

- **Settles:** minimum target sizes, hover-only behaviour, touch.
- **Look in:** icon buttons, dense tables, row actions.
- **Starter:** "Pointer targets are at least 24 by 24 CSS pixels, and 44
  on touch layouts. Nothing is reachable only on hover."

## Accessibility floor

- **Settles:** the floor every screen keeps, whatever else changes.
- **Look in:** lint configuration for accessibility, existing audits.
- **Starter:** "Body text meets 4.5 to 1 contrast and large text 3 to 1;
  every control has an accessible name containing its visible label;
  motion has a reduced-motion path."

## Not here

- **Visual tokens** — colour, type scale, spacing, radius. Point at
  where they live.
- **Wording** — the Voice & terms section, owned by ux-writing.
