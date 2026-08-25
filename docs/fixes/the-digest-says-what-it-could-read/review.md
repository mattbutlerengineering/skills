---
stage: review
run: maintenance:the-digest-says-what-it-could-read
date: 2026-08-25
assumptions:
  - "Reviewed as a scoped maintenance fix: the diff since the run began, not the module. The protocol scales review depth for maintenance runs and names Verify's regression as the floor, so the three passes concentrate on the changed contract rather than re-auditing gate_digest's ledger half, which this run did not touch."
---

# Review: the digest states its own coverage

**Examined.** `git diff origin/main` for `gate_digest.py` (+40/-9),
`tests/test_gate_digest.py` (+95/-6), and the two generated files
(`factory/templates/tools/factory/gate_digest.py`,
`factory/manifest.json`), plus `.github/workflows/gate-digest.yml` read
for context and not changed.

## Correctness

**Checked and clean: `aged` cannot be wrong in the direction that
matters.** `_queues` sets `aged` from `events_by_issue.get(number) is not
None`. Every item `_queues` emits is an open issue in `mirror`, and
`run_daily` builds `mirrored` from exactly `listing ∩ mirror` and passes
it to `_timelines` — so a timeline was *attempted* for every item that
can carry the mark. `aged=False` therefore means "attempted and failed",
never "never asked", which is what the rendered sentence claims.

**Checked and clean: the readable-but-eventless line did not move.**
Marking on `waited is None` alone would have put a failure's mark on an
ordinary history. `test_an_unaged_item_says_why_when_its_history_was_
unreadable` asserts both lines, so a regression to the simpler condition
fails.

**Checked and clean: `_capture_latency` is unaffected.** It reads
`events_by_issue` directly and never sees an `Item`; the ledger's dedup
identity is untouched, and the full suite's ledger tests pass.

### Finding 1 — minor, FIXED

`test_a_truncated_listing_is_stated_in_the_footer` asserted
`assertNotIn("- (empty)", partial.split("\n\n")[-1])` — that the last
paragraph is not a gate section. That is trivially true of every digest
ever composed, so the assertion pinned nothing while looking like it
pinned placement. Replaced with the assertion it was reaching for: the
note is the second-to-last paragraph and the standing provenance line is
the last, so a caveat can never drift below the footer and start reading
as a footnote about the tool rather than about the queue above it.

### Finding 2 — minor, FIXED

`test_an_aged_item_never_wears_the_mark` passes `waited=1800` with
`aged=False`, a combination `_queues` cannot currently produce (no
timeline → no arrival → no age). Left undocumented it reads as a guard
against a reachable bug, which would mislead the next person deciding
whether the `elif` branch is load-bearing. Given a docstring stating
plainly that it pins a render *precedence* against a hypothetical future
age source, not a live failure mode.

### Considered and rejected as a finding

**A totally failed listing leaves #178 stale.** `run_daily` returns
before `_post_digest` when `read.value is None`, so the digest issue
keeps yesterday's body. I nearly wrote this up as a major gap — this run
is about coverage honesty, and total failure is the most complete failure
of coverage there is. It does not survive re-reading, for two independent
reasons: the body carries `as_of` in its heading, so a stale digest
displays a stale date to exactly the reader who would be misled; and
`make gate-digest` exits nonzero, which reddens the scheduled run.
Recorded here rather than dropped, because the *shape* of the question
(should a failed read overwrite a good artifact with a failure notice?)
is a real design question — it is just not a defect, and answering it
would be a behaviour change needing its own evidence.

## Design

**Matches `architecture.md`.** Every contract in §Contracts is
implemented as specified: the named record, the required parameter, the
three rendering states, the footer sentence. No undocumented deviation.

**Matches the codebase's own idiom.** `Item` is the `cli.GhResult`
pattern one layer up, and the comment says so and says why. The required
parameter is unusual for this repo — most optional facts get defaults —
and that departure is argued in the docstring, in `architecture.md`, and
pinned by a test, which is the standard this repo holds a departure to.

**One fact, one owner.** Truncation renders once (footer) and unreadable
histories render once (per line). Neither is repeated in the other's
place, and `one_owner.py` is unchanged at 9 findings, with only line-
number drift on two pre-existing ones.

**Deliberate non-change.** `cli.gh_read` was not touched. The seam
already states `truncated` correctly and its docstring already assigns
the decision to the caller; this run is a caller that was not deciding.

## Security

Nothing new. The one added constant is a literal. Issue titles were
already interpolated into the body before this change and still are; the
body reaches `gh` as an argv element, never a shell string, so no
injection surface was added or widened. No secret, credential, or token
appears in the diff. The `--body` argument is unchanged in shape.

## Deferred, with reasons

- **The four adjacent readers** (`dashboard.py:158`, `dashboard.py:197`,
  `assembler.py:257`, `label_sync.py:111`) still ignore `truncated`.
  Deferred because each writes a different artifact for a different
  reader and each needs its own evidence that the omission costs
  something; folding four unevidenced fixes onto one measured one is how
  a scoped run turns into a refactor. Seeded at Operate.
- **The failed-listing design question** above. Seeded at Operate.
- **Detector A's fence-blindness**, recorded as an observation in
  `verification.md`. Not this run's scope; a detector's parse is
  load-bearing for every run in the repo.

## Verdict

No critical findings. Two minors, both fixed in this run. Ship.
