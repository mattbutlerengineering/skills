---
stage: review
run: maintenance:json-that-is-not-utf8
date: 2026-08-30
assumptions: []
---

# Review: a JSON file whose bytes are not UTF-8

Self-authored; ADR-0036 clause 2 still wants a non-authoring reviewer.

## Findings

### 1. Reusing "is not valid JSON" is the load-bearing decision — kept

The tempting fix is a new message: `is not valid UTF-8`. It is worse.
RFC 8259 §8.1 defines JSON interchange as UTF-8, so undecodable bytes
genuinely *are* invalid JSON — one verdict deserves one string, and a
second one would force every caller matching on problem text to learn
both. The `err` interpolation still carries the byte and the offset, so
nothing diagnostic is lost.

### 2. Five copies of the same except tuple — a real one-owner question, raised not answered

The change leaves `(json.JSONDecodeError, UnicodeDecodeError)` written
five times. `one_owner.py` does not flag it (it reports nine unrelated
findings, unchanged by this run), and CLAUDE.md's bar for a new shared
module — multiple real callers *and* observed divergence — is arguably
met: eleven sites across the repo currently spell this guard three
different ways.

But "read a JSON file, get `(value, problems)`" would be a **new seam**,
and every seam in this repo has an ADR behind it (0021, 0022, 0037,
0039, 0040, 0056, 0060). An agent should not mint one unilaterally, and
an ADR PR is a human gate-2 merge under ADR-0036 clause 3. So: the
question is written down in the tracking issue for the owner, and this
run stays a behaviour fix. Widening five guards is reversible; a seam
is not.

### 3. `OSError` deliberately not added — held

Four of the five sites still let `OSError` through. That is a genuinely
adjacent hole and it is *not* fixed here: it is a different failure
class with its own in-flight PRs (#401 "a file the pack cannot read is
a note, not a crash", #353 "simulate unreadable/unwritable files
without chmod"). Folding it in would put this run in conflict with both
and blur what the verification actually proves. Noted in
`verification.md` under what-is-not-verified so it cannot be mistaken
for done.

### 4. Scope stops at the shipped payload — held, with the boundary stated

Six repo-internal sites share the bug and are listed in `defect.md` and
the issue. The line is drawn where the reachability argument is: these
five read files a downstream owner hand-edits in a stamped repo. The
other six read repo-controlled files that only this repo's own CI
writes. A fix run touching eight files against a 44-deep PR queue buys
conflicts for no added safety.

### 5. The detector-E tests are a real gap closed, not padding

`check_scaffold_sync`'s malformed-manifest branch had no test. One of
the two new cases passed immediately — it pins existing behaviour that
nothing was holding. Worth having independently of this defect.

### 6. The shadowed-class hiccup is disclosed, not buried

`verification.md` §5 records that the first cut silently deleted three
tests while the suite reported `OK`, and that only test-count
arithmetic caught it. That is the honest record, and it is also the
strongest argument for the separate check filed alongside this run: if
it can happen mid-review here, it can happen in a PR nobody counts.
