---
stage: capture
run: maintenance:a-filter-rebuilds-the-redacted-id
date: 2026-08-27
re-entry: implement
assumptions: ["no user-supplied brief exists for this run; the brief was
  authored from this session's own investigation under a standing autorun
  instruction, and its provenance is recorded at the head of
  autorun-brief.md"]
---

# Defect: a filter rebuilds the redacted id

## Defect

`knowledge_plane.sanitize` owns one of the dispatch plane's hard rules
(ADR-0032): a sweep intake may never name a work order.

```python
# knowledge_plane.py:47
def sanitize(value, limit=FIELD_LIMIT):
    """... WO ids are redacted (neither a sweep intake nor a mined queue
    entry may name a work order — ADR-0032), and the result is
    length-capped."""
```

`sweeps.sentry_intakes` builds the intake's dedupe key by editing that
result:

```python
# sweeps.py:157
short_id = UNSAFE_KEY.sub("", sanitize(entry.get("shortId"),
                                       KEY_LIMIT))
```

`UNSAFE_KEY` is `[^A-Za-z0-9_.:-]` and it **deletes** what it matches.
Deletion closes gaps, and the gap it closes may be the one that stopped
`WO_TOKEN` matching a moment earlier. The redaction is applied to a
string that is then edited into a different string, so its guarantee
does not reach the value that is used.

## Why it matters

The `shortId` is untrusted external input — it is whatever a Sentry
payload says — and the reconstructed id reaches three places in a filed
GitHub issue: the dedupe key, the title, and the rendered body.

## Reproduction

Four shortIds through the same two steps. The one that is already a work
order is redacted correctly; three that are not are turned into one:

```
$ python3 -c "
import knowledge_plane as kp, sweeps
for raw in ['WO-0042', 'WO-[0042]', 'WO-00 42', 'WO-00​42']:
    s = kp.sanitize(raw, sweeps.KEY_LIMIT)
    sq = sweeps.UNSAFE_KEY.sub('', s)
    print(f'{raw!r:18} {s!r:18} {sq!r:14} {bool(kp.WO_TOKEN.search(sq))}')
"
'WO-0042'          'WO-[redacted]'    'WO-redacted'  False
'WO-[0042]'        'WO-[0042]'        'WO-0042'      True
'WO-00 42'         'WO-00 42'         'WO-0042'      True
'WO-00​42'    'WO-00 42'         'WO-0042'      True
```

The last one is the interesting one: `sanitize` did its job — it turned
the zero-width space into a plain space, exactly as it should — and the
filter then removed the space. A code-fence character between the `W`
and the `O` works the same way, for the same reason.

End to end, the filed plan names the work order everywhere:

```
$ python3 -c "
import sweeps
[i], _ = sweeps.sentry_intakes([{'shortId': 'WO-[0042]',
                                 'title': 'crash in dispatch'}])
print('key  :', i.key)
print('title:', i.title)
print('body :', [l for l in i.body.splitlines() if 'intake-key' in l])
"
key  : sentry:WO-0042
title: [sentry] WO-0042: crash in dispatch
body : ['intake-key: sentry:WO-0042']
```

## Why the tests did not catch it

`tests/test_sweeps.py` already has a class whose docstring states this
exact invariant:

```python
class TestUntrustedInputBoundary(unittest.TestCase):
    """A hostile Sentry payload: nothing it says may steer an agent,
    break out of the quoted block, or name a work order."""
```

Its hostile payload puts the `WO-0005` bait in `title`, and `title` is
the field with no post-`sanitize` editing. The one field that IS edited
afterwards — `shortId` — carries a path-traversal probe instead. The
suite asserts the invariant and never exercises the path that breaks it.

## Breakdown

- [x] The redaction is the last transformation applied to the key.
      Acceptance: a test asserts that a `shortId` of `WO-[0042]`,
      `WO-00 42`, and a zero-width-separated `WO-0042` each produce an
      intake whose key, title and body name no work order.
- [x] The existing hostile payload exercises the field that is edited.
      Acceptance: `TestUntrustedInputBoundary`'s `shortId` carries a
      reconstruction attempt, and its existing assertions still hold
      (path traversal still neutralised, key still usable).
- [x] Full battery green.

## Notes

2026-08-27 — the fix is not the composition order the breakdown item's
wording implies. Both orderings leak. Sanitizing first and filtering
after is today's bug: deletion closes the gap that stopped the redaction
firing. Filtering first and sanitizing after only moves the leak the
other way — deletion also FUSES words, so `foo WO-0042` squeezed first
is `fooWO-0042`, which `WO_TOKEN` no longer matches at all because its
`\b` is gone, and the id then survives unredacted.

What is actually wrong is the deletion, not the order. `UNSAFE_KEY.sub`
now substitutes `_` instead of the empty string, which neither closes
gaps nor fuses words. `_` is the only safe filler: it is inside the
key-safe class, and it is not in the work-order grammar, so the
substitution cannot build a token either — a `-` filler could, turning
`WO 0042` into `WO-0042`.

The order is therefore left exactly as it was, and the redaction is once
again the last word because nothing after it can create a token: every
character the filter emits is either an original character in its
original position or an `_`.

2026-08-27 — a shortId containing a character outside the key-safe class
now produces a different dedupe key (`EVIL-1_.._.._etc_passwd` where it
was `EVIL-1....etcpasswd`). The existing expectation in
`test_the_dedupe_key_cannot_carry_path_traversal` was updated rather
than worked around; the consequence is priced in `review.md`.
