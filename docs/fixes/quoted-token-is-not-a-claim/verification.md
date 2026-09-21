---
stage: verify
run: maintenance:quoted-token-is-not-a-claim
date: 2026-08-24
assumptions:
  - "Criteria source: there is no prd.md — this is a maintenance run that entered at capture with re-entry: architect — so the criteria list is defect.md's Expected line and its explicit non-claim (D1, D2) plus every clause of breakdown.md's two acceptance criteria (A1.1-A1.2, A2.1-A2.6), with the battery scored once as B."
  - "The red state for A2.2 was re-derived rather than quoted from memory: a detached `git worktree` at 5210702 (the A1 commit) with THIS commit's tests/test_validator.py copied in, so the four cases run against the pre-change validator.py. The worktree was removed afterwards and the working tree was never mutated."
  - "trigger_eval.py and charter_replay.py were NOT run: both are real model runs that cost money and need the `claude` CLI, and CLAUDE.md puts them on demand only, never CI. Neither is named by any criterion here. Recorded under Not verified."
---

# Verification: a fence is evidence, not a claim

Verified at `b15d789`, two local commits `5210702..HEAD` off `main`,
working tree as the run left it.

## Summary

**11 criteria. 10 PASS, 1 PASS-WITH-A-CORRECTION, 0 FAIL.**

The gate no longer reads quoted material, the passing direction is
unchanged, and the boundary the design drew — inline code is typography,
not quotation — holds in both directions.

**The correction is D1's, and it is against `defect.md`'s own
reproduction, not against the fix.** The brief recorded the gate finding
two tokens in PR #330's body. Replaying it faithfully finds **one**. The
brief drove the body as it stands *today*, which includes a section added
by the very fix-up that redacted the ids; that section did not exist when
CI failed. The corrected replay agrees with the authoritative record —
the failing run's own log names one work order — and the conclusion is
unchanged: every token was quoted, and the gate now skips.

## D1 — a body whose only tokens are quoted cites no work order

`defect.md`'s Expected line. Scored against the real failure, not a
reconstruction of one: the run that failed is on record.

```
$ gh run view 32691298530 --log-failed | grep -i "V:" | head -5
needs-review-label	Flip the work order to wo:needs-review	2026-08-24T04:47:23.0267469Z env:
needs-review-label	Flip the work order to wo:needs-review	2026-08-24T04:47:23.3434419Z V: none of the work orders this PR cites (WO-0018) is mirrored to an issue it closes (#329) — a PR implements the work order whose breakdown row it closes
```

One work order, `WO-0018`. Replaying that body — the live body with the
fix-up's added section removed and its `WO-00xx` redaction undone — through
both spellings of the gate:

```
$ python3 probe1.py pr330.txt
tokens the OLD gate found (whole body): ['WO-0018']
  -> skip applies? False
tokens the NEW gate finds (quoted material stripped): []
  -> skip applies? True
where each token sat:
    35| > the state WO-0018/#123 is actually in — read as agreement. The knowledge
```

**PASS, with the correction above recorded rather than smoothed.** The
sole token sat in a blockquote; the old gate read it as a claim and the
new one does not. `defect.md`'s count of two was an artefact of replaying
the post-fix-up body and is corrected here; no line of `defect.md` is
rewritten.

## D2 — PR #306's prose case is NOT fixed, and not silently widened

`defect.md`'s "What is NOT claimed". An archaeology note in ordinary prose
is not quoted material, so the gate's answer must be byte-identical.

```
$ python3 - <<'PY'   # PR #306's shape: "introduced by 663265c (WO-0042)"
old gate saw: ['WO-0042']
new gate sees: ['WO-0042']
identical?  True
skip applies?  old: False  new: False
```

**PASS.** The out-of-scope case behaves exactly as before. The seed stays
half-closed and the closing artifacts say so.

## A1.1 — the pin passes against today's code, before any change

Written and landed at `5210702`, one commit before the change:

```
$ python3 -m unittest tests.test_validator.TestRunLifecycle.test_a_fenced_citation_that_resolves_still_flips_the_label -v
test_a_fenced_citation_that_resolves_still_flips_the_label (tests.test_validator.TestRunLifecycle.test_a_fenced_citation_that_resolves_still_flips_the_label)
The passing direction, pinned before the skip gate narrows. ... ok

----------------------------------------------------------------------
Ran 1 test in 0.003s
```

**PASS.** It also passed at `5210702` itself — the four-failure run under
A2.2 below is 94 tests with exactly four failures, and this is not one of
them.

## A1.2 — A1 changed no production file

```
$ git show --stat 5210702 -- factory/ --format=
(no output: the commit touches nothing under factory/)
$ git show --stat --format= 5210702
 ...057-lifecycle-legs-agree-about-an-uncited-pr.md |   2 +-
 docs/adr/0062-a-quoted-token-is-not-a-claim.md     |  70 ++++++++++++
 docs/adr/README.md                                 |   3 +-
 .../quoted-token-is-not-a-claim/architecture.md    | 120 +++++++++++++++++++++
 .../fixes/quoted-token-is-not-a-claim/breakdown.md |  45 ++++++++
 tests/test_validator.py                            |  24 +++++
 6 files changed, 262 insertions(+), 2 deletions(-)
```

**PASS.** Docs, ADRs and one test file; no root module, no payload twin,
no manifest.

## A2.1 — `_unquoted` exists and the gate reads it

The whole production change, every non-comment line of it:

```
$ git diff 5210702..HEAD --stat -- validator.py
 validator.py | 48 +++++++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 47 insertions(+), 1 deletion(-)
$ git diff 5210702..HEAD -- validator.py | grep -E "^[-+][^-+]" | grep -vE "^\+#|^\+ "
+FENCES = ("```", "~~~")
+def _unquoted(body):
-        if uncited == "skip" and not WO_TOKEN.findall(body):
```

```
$ sed -n '/if uncited == "skip"/,+2p' validator.py
        if uncited == "skip" and not WO_TOKEN.findall(_unquoted(body)):
            return []
        return problems
```

**PASS.** One expression replaced, one helper and one constant added, one
line deleted — and that deleted line is the old gate.

## A2.2 — the four skip cases were watched to fail, for the right reason

Re-derived at `5210702` with this commit's tests copied in:

```
$ git worktree add -q --detach $S/pre-a2 5210702 && cp tests/test_validator.py $S/pre-a2/tests/
$ cd $S/pre-a2 && python3 -m unittest tests.test_validator
FAIL: test_a_tilde_fence_quotes_as_a_backtick_fence_does (tests.test_validator.TestRunLifecycle.test_a_tilde_fence_quotes_as_a_backtick_fence_does)
AssertionError: Lists differ: ['V: PR body has no Closes #N link, so the[68 chars]ons'] != []
FAIL: test_a_token_only_inside_a_blockquote_is_not_a_claim_either (tests.test_validator.TestRunLifecycle.test_a_token_only_inside_a_blockquote_is_not_a_claim_either)
AssertionError: Lists differ: ['V: PR body has no Closes #N link, so the[68 chars]ons'] != []
FAIL: test_a_token_only_inside_a_fence_is_not_a_claim (tests.test_validator.TestRunLifecycle.test_a_token_only_inside_a_fence_is_not_a_claim)
AssertionError: Lists differ: ['V: PR body has no Closes #N link, so the[68 chars]ons'] != []
FAIL: test_an_unterminated_fence_swallows_the_rest_of_the_body (tests.test_validator.TestRunLifecycle.test_an_unterminated_fence_swallows_the_rest_of_the_body)
AssertionError: Lists differ: ['V: PR body has no Closes #N link, so the[68 chars]ons'] != []
Ran 94 tests in 0.062s
FAILED (failures=4)
```

**PASS.** Exactly four failures, each returning the malformed-citation
problem instead of skipping — the right reason, not an import error or a
fixture fault. And after the change:

```
$ python3 -m unittest tests.test_validator.TestRunLifecycle.test_a_token_only_inside_a_fence_is_not_a_claim ... (four cases, run one at a time)
test_a_token_only_inside_a_fence_is_not_a_claim            OK
test_a_token_only_inside_a_blockquote_is_not_a_claim_either OK
test_a_tilde_fence_quotes_as_a_backtick_fence_does         OK
test_an_unterminated_fence_swallows_the_rest_of_the_body   OK
```

## A2.3 — inline code is typography, not quotation

The boundary that must not move. It passed at `5210702` (it is not among
the four failures above) and passes now:

```
$ python3 -m unittest tests.test_validator.TestRunLifecycle.test_inline_code_is_typography_not_quotation
test_inline_code_is_typography_not_quotation               OK
```

**PASS.** A body citing `WO-0004` in backticked prose with no `Closes`
line is still the malformed-citation problem, on both sides of the change.

## A2.4 — the named pre-existing tests pass unchanged

Unchanged is asserted structurally, not by eye — A2 deleted no line of the
suite at all:

```
$ git diff 5210702..HEAD --stat -- tests/test_validator.py
 tests/test_validator.py | 77 +++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 77 insertions(+)
$ git diff 5210702..HEAD -- tests/test_validator.py | grep -c "^-[^-]"
0
```

```
$ (each named case, run one at a time)
test_the_merged_leg_keeps_a_malformed_citation_loud        OK
test_the_relaxation_must_be_asked_for                      OK
test_uncited_skip_still_flips_a_cited_work_order           OK
test_a_mentioned_work_order_does_not_get_the_merged_label  OK
test_a_fenced_citation_that_resolves_still_flips_the_label OK
```

**PASS.** Zero deletions, and every named case green, A1's pin included.

## A2.5 — `cited_work_order` was not edited

```
$ git diff 5210702..HEAD -- validator.py | grep -n "cited_work_order"
26:+    Only the gate reads this. Resolution (`cited_work_order`) still reads
```

**PASS.** The single occurrence in the diff is a line of the new
docstring. Resolution still sees the whole body, which is the property
that keeps every label flip that happens today happening.

## A2.6 — the payload twin and the manifest travelled with it

```
$ git show --stat --format= b15d789
 .../quoted-token-is-not-a-claim/architecture.md    |  8 ++-
 .../fixes/quoted-token-is-not-a-claim/breakdown.md | 18 ++++-
 factory/manifest.json                              |  2 +-
 factory/templates/tools/factory/validator.py       | 48 +++++++++++++-
 tests/test_validator.py                            | 77 ++++++++++++++++++++++
 validator.py                                       | 48 +++++++++++++-
 6 files changed, 196 insertions(+), 5 deletions(-)
```

```
$ python3 -m unittest tests.test_factory_init.TestRealTreeMirrors -v
test_every_mirrored_root_file_matches_its_payload_copy (tests.test_factory_init.TestRealTreeMirrors.test_every_mirrored_root_file_matches_its_payload_copy) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.002s
```

**PASS.** Root and payload changed together in one commit; detector E is
green in the battery below, and the payload↔root direction is pinned here.

## B — the battery

```
$ python3 -m unittest discover tests
Ran 1350 tests in 17.191s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

**PASS.** 1345 → 1350: the five new cases, and nothing lost.

## Not verified

- **Detector B in anger.** It cannot be pre-flighted locally — `gates.py`
  skips it without a PR event payload — so the claim that this run's own
  PR body passes `needs-review-label` is untested until the PR exists.
  That job takes checkout's default ref on a `pull_request` event
  (`.github/workflows/validator.yml:152-154`, deliberately: the breakdown
  row the flip reads landed on the default branch first), which is the
  merge ref and therefore carries this branch's `validator.py`. So the
  open leg on this run's own PR is the fix's first live exercise, and it
  exercises the new gate rather than the old one. Ship records that.
- **`trigger_eval.py` and `charter_replay.py`.** Real model runs, on
  demand only, no criterion names them.
- **The `Implements: WO-####` convention.** Out of scope by `defect.md`;
  D2 verifies only that this run did not quietly change that case.
- **CommonMark conformance.** `_unquoted` is a line walk, not a markdown
  parser: indented code blocks (four spaces), fences opened with more than
  three characters and closed with fewer, and lazy blockquote
  continuations are not modelled. Each mis-read is a token *kept*, i.e. a
  problem reported rather than a wrong flip, so the failure direction is
  the safe one — but it is not verified, because it is not implemented.
