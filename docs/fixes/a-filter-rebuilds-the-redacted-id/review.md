---
stage: review
run: maintenance:a-filter-rebuilds-the-redacted-id
date: 2026-08-27
assumptions: []
---

# Review: a filter rebuilds the redacted id

Scope: `sweeps.py` (+11/-2) and `tests/test_sweeps.py` (+52/-4).
`sweeps.py` is not in `factory_init.MIRRORS`, so there is no payload
copy and no manifest to regenerate.

Written by the same agent that wrote the change, so ADR-0036 clause 2 is
unsatisfied.

## Correctness

**Checked, not a finding — the substitution cannot itself build a work
order id.** A token is `\bWO-\d{4}\b`. The filter emits only original
characters in their original positions and `_` fillers. `_` is not `W`,
`O`, `-` or a digit, so all eight characters of any token in the output
must be original and, because nothing is deleted, contiguous in the
input too. The word boundaries carry across for the same reason: a
filler is a word character, so a `\b` in the output can only sit where
one sat in the input. A token in the output therefore implies the same
token in `sanitize`'s output, which `sanitize` would have redacted.

**Checked, not a finding — `-` would have been the wrong filler.** It is
key-safe, so it passes the obvious test, and it is in the token grammar,
so `WO 0042` becomes `WO-0042`. The comment at `KEY_FILL` says this
because the next person to touch it will reach for `-` first.

**Major, accepted with its cost — the dedupe key format changes for
malformed shortIds.** `EVIL-1/../../etc/passwd` keyed as
`EVIL-1....etcpasswd` and now keys as `EVIL-1_.._.._etc_passwd`. Keys
are matched against live issues by `known_keys`, so an intake already
filed under an old key would be filed once more, under the new one, and
then dedupe normally. The exposure is bounded to shortIds containing a
character outside `[A-Za-z0-9_.:-]`; a Sentry shortId is a project slug
and an alphanumeric suffix, and the test pins that a well-formed one
keeps its key exactly. Accepted: the alternative — preserving the old
key format — is the defect.

**Checked, not a finding — the other two `sanitize` call sites in this
function are already correct.** `title` and `fields` pass the sanitized
text through unedited, so the redaction is already their last word.
`rejection_mining`'s caller does the same. This function's `shortId` was
the only place in the repo where sanitized text was edited afterwards.

**Open, not fixed here — `WO_TOKEN`'s word boundaries mean a work order
id can be present to a reader and absent to the grammar.** `passwdWO-0042`
matches nothing, and every tool that reads work order ids agrees it names
none. That is a property of the plane-wide grammar in
`knowledge_plane.py`, not of this change, and this change does not make
it worse — with the filler in place, adjacent words are never fused in
the first place. Recorded rather than fixed: it belongs to whoever owns
`WO_TOKEN`, and changing that regex moves the dispatch plane.

## Design

`KEY_FILL` is a named constant beside `UNSAFE_KEY` rather than a literal
at the call site, because the choice of filler is load-bearing and the
comment has to live somewhere a reader will find before changing it.
No new dependency, no new function, no interface change.

## Security

This is the security fix. It closes a path by which untrusted external
text controlled part of a filed GitHub issue's title, key and body in a
way ADR-0032 forbids. The neighbouring protections in the same function
— fence defanging, control stripping, length caps, the data-not-
instructions preamble — are unchanged and still asserted by the hostile
payload class, which now also exercises the field that was broken.

## Verdict

No critical findings. One major accepted with its cost stated, one
pre-existing grammar limitation recorded and left to its owner. The
blocking condition on shipping is ADR-0036 clause 2.
