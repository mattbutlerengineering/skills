---
stage: review
run: maintenance:isdigit-is-not-an-int-guard
date: 2026-08-31
assumptions: []
---

# Review: `str.isdigit()` is not an `int()` guard

Self-authored; ADR-0036 clause 2 still wants a non-authoring reviewer.

## Findings

### 1. `isascii() and isdigit()` over `try/except int()` — deliberate, and the weaker-looking choice is the right one

The obvious alternative is `try: int(x) except ValueError:` plus a
`< 0` check. It is more robust *in general* and was rejected for two
specific reasons.

- **Spec fidelity.** RFC 9110 §8.6 defines `Content-Length` over
  `DIGIT = %x30-39` — ASCII only. `int()` accepts `'٣'` (Arabic-Indic)
  and returns 3, so a `try/except` guard would *accept* a header the
  grammar forbids. `isascii() and isdigit()` rejects it.
- **Surgery.** At `validator.py:459` and `assembler.py:280` the guard is
  a boolean inside an existing condition. `try/except` would restructure
  both functions; adding `isascii()` is one token and leaves the shape
  alone.

The cost is that the guard now depends on a non-obvious fact, so the
fact is written down at all three sites rather than assumed.

### 2. The Unicode hole is the actual finding — worth stating plainly

The `Content-Length` crash alone would have been a small bug. What makes
this run worth its size is that **the repair that suggests itself does
not repair it**: `.isdigit()` is this repo's existing idiom at both
other string-to-int boundaries, and both were already holed. Had the
sweep stopped at `dashboard.py`, the fix would have shipped with the two
CLI sites still raising and a new third site written the same broken way.

### 3. `do_POST` had no tests, and that is why the logic hid there

`respond_post` — the pure half — is well covered. The handler was
described as having "no logic", so nothing tested it, and the one line
of logic that *was* there went unguarded. The tests added here drive a
real request cycle over a `BytesIO` connection rather than asserting on
`content_length` alone, because the defect was that the exception
escaped the handler, not that the arithmetic was wrong.

Twelve tests: five pure, five over HTTP, one each for the CLI sites.

### 4. Three sites now spell one guard the same way — the one-owner question, raised not answered

`isascii() and isdigit()` is written three times, with the same comment
at each. That is the shape `one_owner.py` exists to notice, and it does
not flag it (nine findings, unchanged from `main`) because the fact is
duplicated as *code*, not as a value or a payload key.

A `non_negative_int(text)` helper would have one obvious home:
`cli.py`, the CLI/harness-IO seam. But `dashboard.py` is not a CLI tool,
`cli.py`'s existing "non-negative integer" check is over parsed JSON
ints rather than strings, and CLAUDE.md's bar for a new shared thing is
multiple real callers **and** observed divergence. There is no
divergence yet — all three copies are identical, deliberately. Recorded
here so a fourth site is a decision rather than a reflex.

### 5. The disclosed residual is a policy decision, not laziness — kept

An overstated `Content-Length` still hangs, and `verification.md` §4
shows it still hanging after the fix rather than quietly omitting the
row. Fixing it means a socket timeout applied to every request, which
trades a hang for a truncated slow upload. That is a change to what the
server promises, not a bad-input rejection, and it belongs to whoever
owns the console's behaviour.

### 6. Bounded blast radius

Every change is a guard that can only turn a former traceback into a
problem string or a `400`. No message, signature, return shape or
success path moves: the two controls in `TestPostContentLengthOverHttp`
exist to pin exactly that, and both passed before the change as well as
after.

## Residual risk

The `400` body reuses the module's `{"problems": [...]}` shape, so a
client parsing responses sees a familiar envelope. Nothing consumes it
today — the console's JS only posts to `/api/backlog-order` — so the
new status code cannot break an existing caller.
