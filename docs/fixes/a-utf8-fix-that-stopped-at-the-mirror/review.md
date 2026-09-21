---
stage: review
run: maintenance:a-utf8-fix-that-stopped-at-the-mirror
date: 2026-08-31
assumptions: []
---

# Review: the UTF-8 read fix stopped at the mirror boundary

Self-authored; ADR-0036 clause 2 still wants a non-authoring reviewer.

## Findings

### 1. The finding is an incomplete fix, and that is the durable lesson — kept

The parent run (PR #410) was correct in every site it touched. Its
omission was one of *scoping*: it swept the template payload, and the
payload is a packaging boundary that the defect class does not respect.
`lint.py` is no less exposed than `gates.py`; it simply does not ship.

That is worth stating plainly in `defect.md` — which it is — because the
next class-wide fix in this repo will face the same fork. The rule that
falls out: when a fix is *class*-shaped, enumerate the class mechanically
(here, an AST sweep over every git-tracked file) rather than walking a
directory that happens to contain the first few instances.

### 2. Message reuse — inherited, not re-litigated

Every site keeps the message it already had. RFC 8259 §8.1 defines JSON
interchange as UTF-8, so undecodable bytes genuinely are invalid JSON,
and one verdict deserves one string. This decision belongs to the parent
run; this run simply does not diverge from it.

`dashboard.repo_set` is the exception worth noticing, and it is not a
divergence: it already had two arms with two different messages —
`cannot read` for `OSError` and `is not valid JSON` for
`JSONDecodeError`. An undecodable file is unreadable, so it joins the
first. That is the most precise shape of the three in the repo, because
it tells the operator whether to fix the bytes or fix the syntax.

### 3. The one-owner question the parent run raised is now stronger — still raised, not answered

PR #410's review declined to build a "read a JSON file, get
`(value, problems)`" seam, on the grounds that a new seam needs an ADR
and the bar in CLAUDE.md is multiple real callers **and** observed
divergence. After both runs merge the tally is 16 sites in three
spellings:

| spelling | sites | why |
|---|---|---|
| `(json.JSONDecodeError, UnicodeDecodeError)` | 12 | read and parse share one arm, one message |
| `(OSError, json.JSONDecodeError, UnicodeDecodeError)` | 3 | path comes from outside; `cannot read` |
| `(OSError, UnicodeDecodeError)` | 1 | separate parse arm with its own message |

Each spelling is principled rather than accidental, which is the honest
reading and cuts *against* collapsing them. But 16 sites is materially
more evidence than 11, and two runs have now had to touch the same
guard. That is exactly the "observed divergence between copies" clause.

This run does not build the seam: creating one unilaterally would be a
new shared module without an ADR, and ADR-0036 clause 3 makes any
`docs/adr/**` change a human gate-2 merge. Recorded here so the third
run to touch this guard inherits a count and not a hunch.

### 4. One gratuitous divergence found and removed — fixed in this run

The first draft spelled `charter_replay.py`'s handler
`(OSError, UnicodeDecodeError, json.JSONDecodeError)` — the same three
exceptions as `cli.py`, in a different order, for no reason. Reordered
to match `cli.py:238` exactly. Same set, same order, same message shape;
the two sites now read as one idiom, which is the whole of what a seam
would have bought here.

### 5. Tests pin behavior through public interfaces — kept

`eval_schema.load_case_set` is tested through `eval_schema.load`, the
interface both real callers use, per this repo's convention. The other
five are tested through the checker or entry point a caller invokes.
None reaches into a private helper.

### 6. Scope — no mirror, no manifest

None of the four modules is in `factory_init.MIRRORS`, so detector E is
not in play and `update-manifest` was correctly not run. Verified by
reading `MIRRORS` rather than by inspecting the payload directory.

## Residual risk

If PR #410 is closed unmerged, its ten sites remain broken. The two runs
are disjoint in files, so neither blocks the other, but neither
completes the class alone.
