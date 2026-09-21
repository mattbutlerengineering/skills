---
stage: review
run: maintenance:heredoc-delimiter-is-guessable
date: 2026-08-27
assumptions: []
---

# Review: the heredoc delimiter is guessable

## Scope

`cli.py` (+1 import, +1 helper, 1 changed line), `tests/test_cli.py`
(+68, purely additive), and the regenerated mirror
(`factory/templates/tools/factory/cli.py`, `factory/manifest.json`).
Three passes: correctness, design, security.

One item needs a human, and it is a documentation decision rather than a
code defect — finding 1.

## Findings

### Major: ADR-0040 states the delimiter format this run changes

- Scenario: not a runtime failure — a decision record that no longer
  describes the code. `docs/adr/0040-write-outputs-joins-the-cli-seam.md`
  says, in its Decision section: *"The delimiter is neutral
  (`__<KEY>_EOF__`)."* After this run the delimiter is
  `__EOF_<32 hex chars>__`. A reader trusting the ADR would look for a
  key-derived delimiter and not find one.
- I checked whether this run reopens that decision. **It does not.**
  ADR-0040's decision is *ownership* — `cli` owns `write_outputs`,
  `assembler` and `cost_report` become thin callers — and the property
  the delimiter clause is protecting is **tool-neutrality**, replacing
  the assembler-branded `__ASM_*_EOF__` the ADR was written to retire.
  `__EOF_<hex>__` names no tool, and the ADR's own
  no-tool-branding pin (`test_the_delimiter_carries_no_tool_branding`)
  passes unmodified. The ADR further records, under Consequences, that
  *"workflows are unaffected (they read step outputs by key, never by
  delimiter)"* — which is precisely why the format is free to change.
- So the parenthetical describes the then-current form, not a constraint.
  But it is stated in a Decision section, and leaving it means the record
  is wrong.
- Decision: **deferred to the user, deliberately not acted on.** Two
  reasons. First, the repo's rule is to supersede or amend, never
  rewrite, so correcting ADR-0040 in place is forbidden and the fix would
  be a *new* ADR — which is the user's call to make, not an unattended
  run's. Second, and more concretely: **ADR numbering would collide.**
  Open PRs #351, #349 and #333 each add a new ADR — numbered 0062, 0063
  and 0064 respectively, none merged, none present in this tree (gate C
  flags a reference to one, which is how this was confirmed). A new ADR
  written here would have to claim 0065 while guessing nothing else is
  in flight. Proposed text, if
  wanted:

  > **ADR-00NN — the step-output delimiter is unguessable.** Amends
  > ADR-0040. Its Decision reads "The delimiter is neutral
  > (`__<KEY>_EOF__`)". Neutrality stands and is unchanged; the
  > key-derived *form* is retired. A delimiter derivable from the key
  > lets a multiline value close its own heredoc, after which the runner
  > reads the remainder as further assignments. The delimiter is now
  > drawn per call from `secrets.token_hex` and regenerated while it
  > appears in the body. ADR-0040's consequence that "workflows read step
  > outputs by key, never by delimiter" is what makes this free.

### Minor: the blast-radius table is not pinned by anything

- Scenario: `defect.md` classifies all six callers, and the fix's
  severity rests on only one of them writing a multiline value. Nothing
  enforces that. If `gate_digest` or `rejection_mining` later put an
  excerpted review body into its outputs dict — `rejection_mining`
  already handles such text, it just routes it to the issue body instead
  — that caller silently enters the heredoc branch, and the severity
  analysis in `defect.md` goes stale with no signal.
- Decision: deferred. After this run the heredoc branch is safe for any
  input, so a new multiline caller is no longer a defect — it would only
  invalidate a paragraph of prose. Recorded so the next reader knows the
  table is a snapshot, not an invariant.

### Minor: `_heredoc_delimiter` loops without a bound

- Scenario: none reachable. `text` is finite, the delimiter space is
  2^128, and the loop exits on the first draw with overwhelming
  probability. A bounded retry would need a failure branch that can never
  be taken, and inventing behaviour for it is the speculative
  defensiveness the repo's discipline rules out.
- Decision: kept as written, with the invariant stated in the docstring
  rather than encoded as a counter. The forced-collision test exercises
  the loop twice, so the path is covered rather than assumed.

## Passes with no findings

- **Security.** This is the security fix; the residual surface was
  checked. The delimiter is drawn from `secrets`, not `random` — seeded
  PRNG output would be the original defect restated. Nothing is logged or
  interpolated that was not already; `_heredoc_delimiter` returns
  `[0-9a-f]` plus underscores, so it cannot itself inject a newline or an
  `=`.
- **Design.** The change matches the seam's shape: the helper is private
  and local to `cli.py`, `write_outputs` keeps its two-line body, and the
  diff is one changed line. An earlier draft folded the call into the
  f-string with a walrus; it was reverted before commit because the repo
  has no walrus precedent (grep found none outside my own edit) and the
  original two-line shape reads better.
- **Compatibility.** Nothing in the tree reads the delimiter back:
  grepping `_EOF__` across `*.py`, `*.yml`, `*.yaml` and `*.md` returns
  only the new test's poisoned literal and ADR-0040's prose. No workflow
  parses `$GITHUB_OUTPUT` itself — the runner does.

## Verdict

Ready to ship as a prepared, unmerged branch. No critical findings; both
minors are deliberate.

The ADR record is the human's call: the code is correct and CI-green
either way, but until an amending ADR exists, ADR-0040's Decision
section names a delimiter format the code no longer produces. ADR-0036
clause 2 independently blocks self-merge — a non-authoring reviewer must
re-execute verification and record it on the PR.
