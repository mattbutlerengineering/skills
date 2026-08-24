# The front door routes humans, not files

- Status: accepted
- Date: 2026-08-13

## Context

`factory.py` landed 2026-08-10 (#246) as the one front door over the
fourteen CLI-bearing root modules (issue #237): an index of what exists and
a dispatcher over the `main()`s that already do.

Three days later a deepening review walked its callers and found none. The
Makefile's 13 targets, the five workflows and the docs all still invoke
tools by filename; only a test imports it. The review read that as an
unfinished adoption — a verb table maintained by hand that nothing walks
through — and asked for a decision either way, since the middle is the
shallow state.

Two facts refine the question:

- **The table is mostly pinned already.** `tests/test_factory_cli.py`
  derives the verb set from a mechanical scan of the root's
  `__main__` guards and asserts each verb is its module's name
  hyphenated. Only the calling-convention column is hand-declared — and
  `tests/test_factory_cli.py` carries a branch for a third convention
  (`"argv0"`) that no row uses.
- **Routing real traffic through it is not cheap.** `factory.py` is not a
  `factory_init.MIRRORS` entry, so a recipe reading
  `python3 factory.py gates` would either force the front door into the
  template payload as a fifteenth mirrored tool, or make
  `factory_init.product_form` translate verbs into payload paths —
  growing the very adapter ADR-0046 exists to delete. The product
  Makefile also *drops* the plugin-only lint line, a rule that would have
  to learn the verb spelling too.

## Decision

- **The front door's callers are humans.** Zero file callers is the
  decided state, not pending adoption. The Makefile, the workflows and
  the docs keep invoking tools by filename, which keeps `product_form` a
  path respelling and nothing more.
- **The dispatcher stays alongside the index.** Discovery without a way to
  run what you just found is half a front door, and the delegation is 25
  lines.
- **The convention column joins the pinned two.**
  `tests/test_factory_cli.py` derives it from each module's `main`
  signature rather than trusting the declaration. The table stays static
  in the module so dispatch imports one module, not fourteen; the
  derivation lives in the test, which may import freely.
- **`bare` means no argv slot, not "callable with no arguments."** The
  discriminator is the slot's *existence*, because a `main(argv=None)`
  binds `main()` happily and then resolves argv from the process — under
  the front door that is the verb itself. Any main with a positional
  parameter is routed `argv`; only a main with none is `bare`.
- **The dead `"argv0"` branch goes** — a convention no row uses is a
  third spelling waiting to be adopted by accident.

## Consequences

- "`factory.py` routes nothing" stops being a finding. A future review
  reads this ADR instead of re-deriving the same walk, the service
  ADR-0046 and ADR-0053 already perform for their dead ends.
- A stamped product repo has no front door: `factory.py` is not in the
  payload, and its Makefile remains the one command surface there. That
  asymmetry is deliberate and is the reason Route A was refused.
- Nothing in the verb table can drift silently: a new tool, a renamed
  verb, or a changed `main` signature fails the build.
- **The pin's first catch was a live defect**, found by this run's own
  review rather than by the pin: `charter-replay` was declared `bare`, so
  `python3 factory.py charter-replay` handed argparse the process's argv
  and died with `unrecognized arguments: charter-replay`, while
  `--only`/`--transcripts`/`--record` were refused outright as "takes no
  arguments." The verb was unusable from the day the door opened. Its row
  is now `argv`, and the corrected derivation above is what fails the
  build on the next one.
- If machine traffic should ever route through the front door, the cost is
  the payload question above — reopen this decision then rather than
  adopting it a recipe at a time.
