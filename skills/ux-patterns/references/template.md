# docs/ux-patterns.md — the shape

One file per project, at the target repo's `docs/` root, outside every
run. It is read before UX work starts (by `polish`, `ux-design`,
`ux-writing`, and whoever builds the next screen) and written by two
skills that each own their own sections:

- **ux-patterns** owns every section except Voice & terms.
- **ux-writing** owns `## Voice & terms`.

Neither skill edits the other's sections. The heading `## Voice & terms`
is the contract between them: keep it spelled exactly so.

Leave out any behaviour section the product has no instance of. A
section that exists only because the template had it is noise the next
reader has to discount.

## The template

```markdown
# UX patterns

How this product behaves, decided once. Read before designing or
building a screen. Visual tokens live in <path to theme or design doc>;
this file does not repeat them.

<!-- Sections below are owned by the ux-patterns skill, except
     "Voice & terms", which is owned by ux-writing. -->

## Surface jobs

| Job | Routes |
|---|---|
| Convince | |
| Work | |
| Read | |

## <Behaviour section, e.g. Destructive actions and undo>

- **Rule.** <one checkable sentence>
- **Implemented by.** <component or helper, with its path>
- **Exceptions.** <named screens, and why — or "none">

<!-- one block per section the product has: feedback and loading,
     errors, empty states, destructive actions and undo, forms and
     validation, notifications, navigation and URL state, tables and
     lists, modals and pages, focus and keyboard, hit targets,
     accessibility floor -->

## States checklist

Every new surface decides each of these on purpose: empty (each kind),
loading, error, partial or stale, one item and many, long content,
translated, no permission, offline.

## Voice & terms

<!-- Owned by ux-writing. ux-patterns leaves this section alone. -->

## Decisions

- YYYY-MM-DD — <rule>: chose <X> over <Y> because <reason>. <who decided>
```

## Keeping it true

- A rule that the code no longer follows is either a fix or a stale
  rule. An audit says which; the file is changed only by a decision.
- The decisions log is append-only. A reversed decision gets a new
  dated line saying what it replaces.
- Date the file's last review in the decisions log when an audit finds
  nothing to change, so a reader can tell a quiet file from an abandoned
  one.
