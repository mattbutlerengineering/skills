# The cut-list

What a review or a sweep hands back: a numbered list, one finding per
entry, each saying where, what goes, and what replaces it. The best
outcome for a diff under review is that it gets shorter.

The six-way split of what over-building looks like follows Ponytail's
review format; see [`ladder.md`](ladder.md) for the credit. The evidence
column is this pipeline's addition: a cut is a claim about code somebody
else may be relying on, and a claim needs its evidence on the page.

## The entry

    N. path:lines — tag: what goes. What replaces it.

Number the entries across the whole report, so the user can say "do 2
and 5". Mark a finding you could not confirm with a leading `?` and say
what would settle it.

## The six tags, and what each one owes

| Tag | What it claims | Replaced by | Evidence it owes |
|---|---|---|---|
| `dead` | Nothing reaches it: an unused function, an unreachable branch, a flag nothing sets, a feature nobody asked for | Nothing | The reference search and its result: source, tests, fixtures, configuration, strings and dynamic lookups, and the published surface |
| `stdlib` | Hand-written code the standard library ships | The named function | Any behaviour the hand-written version has that the library one lacks |
| `platform` | Code, or a dependency, doing what the platform already does | The named feature | That the platform versions the project supports ship it |
| `reuse` | A second copy of something already in this repo | The path of the first | That the existing one behaves the same for this caller's inputs |
| `speculative` | Structure with no second user: an interface with one implementation, a factory for one product, a layer with one caller, an option nobody sets | The thing inlined | The count of implementations, callers, or setters, listed |
| `shorter` | The same behaviour in fewer lines | The shorter form, shown | That a reader finds it easier, not merely denser |

## An example

    1. src/dates/picker/ (412 lines, 1 dependency) — platform: custom
       date picker. <input type="date">; both supported browsers ship it.
    2. api/cache.py:1-120 — stdlib: hand-written TTL cache with one
       caller. functools.lru_cache on fetch_rates(); nothing reads the TTL.
    3. web/lib/slug.ts:1-24 — reuse: a second slugify. shared/text.ts
       exports one with identical output on the 14 fixtures tried.
    4. orders/repository.py:30-88 — speculative: AbstractRepository has
       one implementation and no test double. Inline SqlRepository.
    5. config/flags.py:41 — dead: ENABLE_LEGACY_EXPORT. No reader in
       src/, tests/ or deploy/; absent from the settings reference.
    6. reports/totals.py:15-29 — shorter: accumulation loop.
       sum(row.amount for row in rows).
    ? 7. plugins/hooks.py:60-90 — dead: no caller in this tree, but the
       module is a documented extension point. Settle by reading the
       two plugin repos that are known to import it.

    Net: about 610 lines and 1 dependency out. 1 suspicion.

When there is nothing to cut, say so in one line and stop. A review that
invents findings to look thorough costs more than it saves.

## Where a sweep looks

- The dependency manifest against the imports: a dependency used in one
  place, or one the platform has since replaced.
- Interfaces and base classes with a single implementation.
- Wrappers that only delegate, and files that export one thing used
  once.
- Flags, options, and configuration with no setter.
- Hand-written versions of what the standard library ships.
- Helpers that duplicate one already living elsewhere in the tree.

Rank by size of cut, lines and dependencies together, then by how
certain the evidence is.

Before a sweep, look at the work already waiting for review. A cut an
open pull request already makes is not a finding; it is a duplicate of
work in flight, and reporting it as new is worse than saying nothing.

## What never appears

- The floor: validation at a trust boundary, data-loss handling,
  security controls, accessibility basics, anything explicitly asked
  for.
- The one runnable check that non-trivial logic keeps.
- Style preferences. "I would have named it differently" is not a cut.
- Bugs, vulnerabilities, and slow code. They are real, and they are
  another skill's findings: say in one closing line that you saw them,
  and where they should go.
