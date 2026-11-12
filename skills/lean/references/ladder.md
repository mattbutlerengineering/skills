# The ladder

Seven questions, asked in order, stopping at the first that holds. This
file is what each rung looks like when it does — and when the ladder is
the wrong tool.

The ladder is Ponytail's
([DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail),
copyright 2026 DietrichGebert, MIT licence): the idea that an
experienced engineer's reluctance to write code can be written down as
an ordered list. The seven rungs, the floor of things never cut, the
marked-shortcut convention, and the six kinds of cut are adapted from it
and restated in this pipeline's terms. The evidence rules in
[`cut-list.md`](cut-list.md) are this pipeline's own.

## Before the first rung

Understanding is not a rung, because it is not optional. Read the task,
read the code it touches, trace one real request through it, and list
the callers of whatever you are about to change. A rung chosen before
that is a guess with a small diff.

## 1. Does this need to exist?

It probably does not when:

- no request, acceptance criterion, or failing test asks for it;
- it handles a case that cannot occur given the callers that exist;
- it is configurable and nothing configures it;
- it is "for when we need X" and X has no date.

Leave it out and say so in one line, with what would make it real.

> Asked for: a CSV export of the report. Not asked for: a column picker,
> a background job, delivery by email. Build the export. Name the other
> three in one sentence and stop.

## 2. Is it already in this repo?

Search for the verb and the noun before writing either: *slugify*,
*retry*, *parse date*, *format money*. Look where the repo says its
shared code lives. Reuse covers patterns as well as functions — how the
neighbouring handlers validate input and report errors is already
decided, and a second way of doing the same thing is a cost even when it
is shorter.

Reuse is not coupling for its own sake. When an existing helper nearly
fits, and bending it would complicate it for the callers it already has,
a few direct lines (rung 6) are the leaner answer.

## 3. Does the standard library do it?

The usual hand-rolled suspects:

| Written by hand | Already shipped |
|---|---|
| A memo dictionary around one function | `functools.lru_cache` |
| A recursive deep copy | `copy.deepcopy`, `structuredClone` |
| A grouping loop | `itertools.groupby`, `collections.defaultdict`, `Object.groupBy` |
| Argument parsing with string splits | `argparse`, `util.parseArgs` |
| Random tokens and identifiers | `secrets`, `uuid`, `crypto.randomUUID` |
| Splitting URLs and query strings | `urllib.parse`, `URL`, `URLSearchParams` |
| Date arithmetic on integers | `datetime`, `Intl.DateTimeFormat` |
| Temporary file names | `tempfile`, `mkdtemp` |

Two library options the same size? Take the one that is correct on the
edge cases. The point is less code to own, not the shortest call.

## 4. Does the platform do it?

- **The browser.** `<input type="date">`, `<dialog>`, `<details>`, form
  validation attributes, `position: sticky`, scroll snapping, lazy image
  loading, `IntersectionObserver`. Markup and CSS before script.
- **The database.** A unique constraint instead of check-then-insert. A
  foreign key instead of clean-up code. An upsert instead of
  read-modify-write. A transaction instead of a hand-made lock.
- **The operating system and runtime.** A scheduler entry instead of a
  polling loop. A file lock. Environment variables for configuration.
- **The framework already in use.** Its router, its form handling, its
  cache, its validation. Fighting the framework is the long way round.

A platform answer owes one fact: that the platform versions this project
supports actually ship the feature.

## 5. Does an installed dependency do it?

Read the dependency manifest before proposing a new entry in it. A new
dependency is paid for in install weight, an update stream, a security
surface, a licence, and somebody's attention. That is worth paying for
hard, well-tested logic nobody should rewrite: cryptography, time zones,
a parser for a real format. It is never worth paying for something a few
lines do.

## 6. Is it a few direct lines?

Write them where they are used. No new file, class, layer, or exported
name until a second caller exists. Inline now; extract when the second
caller shows up and shows what the shared shape really is.

## 7. Only then: the minimum that meets the criterion

What is left is real work. Build the smallest design that passes the
acceptance criterion: fewest files, fewest new names, no extension
points. Where you take a shortcut with a known ceiling, mark it with a
`lean:` comment that names the ceiling and the trigger for the upgrade.

## When the ladder is the wrong tool

- **The floor.** Validation at a trust boundary, protection against data
  loss, security controls, accessibility basics, and anything explicitly
  requested are not candidates. A shorter version without them is not a
  simplification; it is a defect.
- **The world outside the process.** Anything that touches hardware, a
  clock, a network, or another team's system keeps its tolerances
  adjustable: a timeout, a retry budget, a calibration constant. Those
  are not speculative configuration. Reality will need them tuned.
- **Shortest is not simplest.** A one-liner every reader has to decode
  costs more than five plain lines. The measure is what a tired reader
  has to hold in their head, not the character count.
- **The user said so.** When the fuller version is asked for after
  hearing the leaner one, build it. Once is advice; twice is an
  argument.
