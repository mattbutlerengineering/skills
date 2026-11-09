---
stage: review
run: feature:pr-body-hook-coverage
date: 2026-11-09
assumptions:
  - "Reviewer is independent of the Implement and Verify workers. Scope is the diff a4b32bf..origin/main (1fd836d) for pr_body_preflight.py, tests/test_pr_body_preflight.py and docs/kb/pr-body-contract.md, plus the run directory; the four merged milestone PRs (#1660, #1663, #1666, #1669) each had their own reviews and the follow-up issues (#1655, #1661, #1664, #1667, #1670) are treated as settled and not re-litigated."
  - "Severities are proposals. The Owner arbitrates, so every deferral below is a proposal with a reason, not a decision."
  - "The corpus is private and was not touched. Corpus numbers cited are the ones verification.md records; nothing in this file is corpus text."
  - "Probing was tokenizer-only: fixtures through preflight() and a 40000-variant mutation fuzz of the hook's own input. No command under test was executed and nothing ran against a real PR. The mutation harness ran in a throwaway copy of the tree outside the repository."
---

# Review: Judge the same-call heredoc body

## Scope

`git diff a4b32bf..origin/main` for `pr_body_preflight.py` (633 to 1098
lines), `tests/test_pr_body_preflight.py` (+1357 lines, 166 tests, 99 in
`TestSameCallHeredoc`), `docs/kb/pr-body-contract.md`, and the run directory
(`idea.md`, `prd.md`, `architecture.md`, `breakdown.md`, `verification.md`).
Commits 2c8b88a, ccface0, f5e3f7b, 3931922 (M1 to M4), then 3f2b7a9
(kb re-stamp) and 1fd836d (verification.md, docs only). Code at 3f2b7a9, the
commit Verify judged, equals code at 1fd836d.

Soft gate: `verification.md` is present (PASS on all eight criteria), so the
order is the normal one. I read its qualifications and carry them: the 25%
result clears by 24 commands and depends on the disk of the day (19.15% with
no cwd); the between-commands rule is unverified by the oracle by
construction, and only 8 of 250 judged commands had anything between writer
and reader (5 `cd`, 3 `grep`).

What I read, in full: all 1098 lines of `pr_body_preflight.py` once, in order,
as the implementer who inherits it would; the kb page; the whole run
directory; the open follow-up issues. What I did beyond reading:

- About 50 preflight() fixtures over plausible agent shapes (tight and spaced
  operators, reader on the writer's own line, `git push` and `set -e` before
  the writer, variable paths, reassignment and `read`/`unset` between,
  symlink and `./` respellings, `ln`/`mv`/`sed -i`/`git checkout` between,
  cleanup after the reader, two readers, `-R`, `--web`, a title with `$( )`).
  None produced a refusal the shell-written file would not also get.
- A fuzz of 40000 random token insertions into five base commands. No
  internal exception reached a note (`not checked — XxxError:` never
  appeared) and the slowest call took 17 ms against the hook's 10 s timeout.
- 65 hand-written mutants of the binding rules (every regex alternative,
  constant set and guard I could name), each run against the full test file in
  a throwaway copy. All 65 were killed. Two further mutants I wrote were
  no-ops by construction (my regex edit left the alternation intact) and are
  discarded, not counted.

## Findings

Ranked. Nothing is critical.

### Major: ~160 lines of between- and before-the-writer machinery have no user on the measured corpus, in a live blocking hook

- Cut-list line: `speculative` (structure with no second user, an option
  nobody sets). Entry: `pr_body_preflight.py:600-641, 755-808` `INERT_VERBS`
  git/gh half, `_inert_git` (16 lines), `_inert_gh` (10), `_long_option` (6),
  `GIT_VERBS`, `GIT_CONFIG_SCOPES`, `GH_VERBS`, `GH_API_WRITES`, the
  assignment/`export` branch of `_inert` with `STEERING_NAME`, and the
  descriptor-prefix marker (`FD_PREFIX`, `FD_WORD`, `_unmark`,
  `_Unrun._fd_prefix` 14 lines, the digit-word absorption in
  `_simple_commands`, the `lstrip(DIGITS)` branch of `_write_redirect`).
  Together roughly 100 lines of functions and 60 of constants, inside a
  311-nonblank-line binding region (lines 517-869) that is itself most of the
  465 lines the run added.
- Evidence the tag owes (the count of users, listed): `verification.md`
  criterion 4 records that 242 of the 250 commands judged through the binding
  have nothing between writer and reader, and the other 8 are 5 `cd` and 3
  read-only `grep`. Its funnel rows for "before-the-writer rules" and the
  `$'` guard each lose 0. Its Not verified section states that no judged
  command in the corpus exercises the `git`, `gh`, `printf`, assignment or
  `export` branches of the inert list. So on the corpus these branches have
  zero users beyond fixtures, and the fd-prefix marker's only effect (keeping
  `2>&1` and `2>/dev/null` between writer and reader "judged") is also
  unexercised.
- Failure scenario (the decayed contract, not a bug): each of these branches
  is a place where a false block on a live hook can hide. The run's own
  record is the measure: the four milestone reviews and the follow-up
  issues (#1655 with 8 gaps, #1661, #1664, #1667, #1670) kept finding
  precision gaps in exactly this region (`2>&1`, steering names, `exec`
  wrappers, trap forms, `{NAME}` matching). `verification.md`'s funnel has
  the rule set binding 307 of 550 same-call readers; the part that decides
  any of them is `cd`, `grep` and the "nothing between" case.
- What replaces it (cut direction only, never loosening): let only a bare
  `cd`/`pushd`/`popd` and the read-only verbs already in `INERT_VERBS` sit
  between writer and reader; every other command, including `git`, `gh`,
  assignments and any descriptor-prefixed redirect, is a "not checked" note.
  The cut adds notes and never a refusal, so it stays on the safe side of the
  hook's fail-open contract. The before-the-writer rules (`_shadows`,
  `_opens_descriptor`) are NOT in this cut: they protect against false blocks
  and removing them would loosen the hook.
- Cost of cutting: a plausible shape (`git status` or `export X=1` between
  writer and reader) would turn from judged into a note. It is not in the
  Owner's corpus, which is the point of the proposal, but one Owner's history
  is one sample.
- Standard: none (`stdlib-only` is untouched).
- Decision: proposed defer. Reason: the cut touches the live hook and the
  25% margin is 24 commands, so it needs a fresh Verify replay (the harness
  hashes are in `verification.md`) and should be measured, not guessed. Open a
  lean sweep issue after Ship that re-runs the funnel with each branch
  disabled and cuts the ones that lose 0. Owner arbitrates.

### Minor: architecture.md describes a binding the code is not; the deltas live only in breakdown Notes

- Scenario (decayed contract): `architecture.md` still states, as the design
  Implement was held to,
  - a `Ledger` mapping F's spelling to `Live(text, writer_index)` or
    `Dead(reason)`, "built by one forward walk … consulted once". There is no
    ledger. `_bound_body(spelling, context)` re-scans `records` in five
    separate loops (writer search, before-writer, between redirects, closers,
    between verbs). The breakdown Notes never mention the ledger or the
    `_bound_body(commands, heredocs, position, spelling)` signature the
    Interfaces section gives (`grep -i ledger` over the breakdown is empty),
    so this deviation is unrecorded.
  - keywords between writer and reader get rule 3's invalidation reason; code
    gives the chain note (recorded: #1664, 3b).
  - the closer rule is "other than `/dev/null`"; code uses rule 1's
    descriptor exemption (recorded, M3 review note).
  - the inert list says an assignment dies only when NAME is a variable F's
    spelling names; code also dies on any steering name (`STEERING_NAME`)
    (recorded, M3 note).
  - nothing mentions `_shadows`, `exec`/`{NAME}` before the writer, the `$'`
    guard, the fd marker, trap forms or `LEADERS` (recorded in Notes as
    "Architect routes", but not in the document that is the contract).
- Not a deviation that passes the ADR test: see "ADR compliance" below.
- Proposal: one Architect re-entry folding the Notes' deltas into
  `architecture.md` and deleting the `Ledger` paragraph (or recording why it
  was not built). Fix-or-defer: can ride with #1664/#1667/#1670, which already
  route Architect. Open issues #1664, #1667, #1670 mean this is already
  half-queued; the unrecorded part is the ledger.
- Standard: none.
- Decision: proposed defer to the Architect re-entry that closes those
  issues; it blocks nothing in Ship.

### Minor: parallel heredoc representations and a duplicated literal rule

- Cut-list line: `reuse` (a second copy of something already in this repo).
  Evidence, listed:
  - `_heredoc_at` (line 88) returns `(text, literal)` and `_mask_heredocs`
    keeps them as bare tuples in `context["heredocs"]`; `_Unrun` records the
    same fact as `Heredoc(text, literal, terminated)` in
    `context["statements"]`. `_resolve` (line 876) unpacks the tuple form;
    `_bound_body` and `_running_redirect` read the namedtuple. One concept,
    two shapes.
  - The literal rule `quoted or not any(ch in body for ch in "$`\\")` is
    written at line 111 and again at line 347; the reason string `an unquoted
    heredoc body holds $, a backtick or a backslash` at lines 836 and 879;
    the reason `a body file is read only from the first command` at 503 and
    816; the name pattern `[A-Za-z_][A-Za-z0-9_]*` five times (48, 67, 536 x2,
    639).
  - The context dict carries the same position twice: `commands`/`position`
    (word-bearing records, used by `_check_target`) and
    `records`/`record` (every record, via `with_words`, used by the binding).
- Failure scenario: a future change to what counts as a literal heredoc (the
  rule B and the shell must agree on) is a two-site edit with no test linking
  them; a drift gives a heredoc judged on one path and noted on the other.
  One-owner would catch a duplicated constant, not duplicated logic.
- What replaces it: `_heredoc_at` returns `Heredoc(text, literal, True)`; one
  `_literal(text, quoted)` helper; one place that names each shared reason;
  index the context once.
- Standard: none.
- Decision: proposed defer to the `deepen` handoff below (it is a shape
  cleanup, no behaviour change).

### Minor: the first-command path reads disk when a leading redirect-only command truncates the same file

- Scenario: `> /tmp/b.md` on its own line, then `gh pr create --title t -F
  /tmp/b.md`, with a passing file already on disk. `first` is computed over
  word-bearing records (so a leading `> log` does not demote the reader, by
  the Architect's finding 10), the reader is `first`, and the hook reads the
  stale passing file: result `(0, [])`, silent. The shell truncates the file
  first, gh reads an empty body, and CI's B refuses. Reproduced through
  preflight() with a throwaway fixture file (since removed).
- Direction: the hook under-blocks (a miss, never a false block); the other
  leading-redirect shapes (`: > F`, an assignment) are already notes, because
  they have words. The form is implausible for an agent (truncate a file to
  read it).
- Proposal: demote `first` when a leading word-less record carries a write
  redirect that is not `/dev/null`; `> log` then needs a spelling comparison
  with F to avoid regressing finding 10, which conflicts with the "never
  compare spellings for invalidation" principle, so this is a real
  trade-off, not an oversight.
- Standard: none.
- Decision: proposed defer (log as accepted limit in the kb page). It needs
  an Architect call and has no user.

### Minor: the not-first note blames "first command" when a same-call writer exists

- Scenario: `cat > b.md <<'EOF' … EOF`, then `gh pr create -F ./b.md`, or a
  symlinked directory spelled two ways, or a `--body "$(cat b.md)"` after a
  writer. The binding looks for a writer of the exact spelling, finds none,
  and raises the pre-feature text `a body file is read only from the first
  command`. Reproduced. That text was true before this run; it is now
  misleading, because a same-call writer is a readable shape and the agent
  can no longer tell why its (correctly bound-looking) command was skipped.
  The architecture keeps it on purpose ("today's reason", and
  `test_a_body_file_after_another_command_fails_open` pins it).
- Proposal: when any `cat > <other spelling> <<D` writer exists earlier, say
  `no heredoc writer with this exact spelling precedes it`; leave the old
  text for the no-writer case. Update the one pinned test.
- Standard: none.
- Decision: proposed defer; wording only, no behaviour change.

### Minor: the kb page does not say which writers bind

- Scenario: the page names only `cat > F <<'EOF'`. A reader who gets a note
  (`not certain to run`, `may be rewritten or removed by`, or the pre-feature
  reason) cannot map it to a rule. The verification funnel shows the common
  losses (a `printf`/`tee`/`sed` writer 59, a writer behind `&&` with a
  newline before the reader 100, an unquoted body with `$` 29), and none of
  them is in the page. The page's own contract is "what the hook reads", and
  the shapes it silently does not read are what an agent needs to know to
  restructure.
- Proposal: one sentence: only an exact `cat > F <<D` writer binds; `printf`,
  `tee`, `sed -i`, an unquoted body with `$`, a backtick or a backslash, a
  writer after `&&` followed by a newline, and any command that may write F
  between are notes. `kb.py drift` must be re-stamped after.
- Standard: none.
- Decision: proposed fix with the next edit to the page; no urgency.

### Minor: tests pin private structure at seven sites

- Scenario: `tests/test_pr_body_preflight.py` calls `_Unrun`, `_mask_heredocs`,
  `_tokens` and `_simple_commands` directly (lines 312, 358, 370-372, 567,
  571, 1339) and patches `pr_body_preflight._bound_body` (1637), as the
  breakdown's Accept lines asked. `deepen` reshaping the module's internals
  (see the handoff) has to carry these. Behaviour is covered at the
  preflight() seam: 65 of 65 valid mutants were killed by the full suite
  (above), but I did not measure which of them depend on the private-API
  tests, so I cannot say whether removing them loses coverage.
- Separately, #1670(2) already records that the steering tests compute `what`
  and never use it; I confirm it and do not re-raise it. `assert_a_note`
  (line 783) accepts any note, so a case meant to pin rule X also passes when
  an earlier rule fires first. The 65-mutant run says that weakness is not
  currently letting a rule go uncovered.
- Standard: none.
- Decision: proposed defer with the deepen handoff; convert the private-API
  fixtures to preflight() fixtures when the module is reshaped.

## Passes with no findings

- **Correctness, residual false-block shapes.** Beyond the above, I found no
  plausible agent command the hook refuses where the shell-written file would
  pass B, and no plausible form that makes the hook judge a different body
  than gh reads. The two near-misses are recorded: the leading-truncation
  under-block (Minor above) and the shapes the Notes already accept
  (`set -o noclobber`/`set -C` before the writer, `eval`, `source`, `declare
  -x`, `export PATH=x FOO`, a failing writer; see `_shadows`'s docstring and
  the Notes). Not re-litigated.
- **Correctness, one stdin shape the run did not scope (observation, not a
  finding).** `gh pr create --body-file - <<'EOF'` and `… | gh pr create
  -F -` are `--body-file - reads the body from stdin` notes, as the
  architecture's accepted limit says. The PRD never names them. They are an
  obvious agent form; whether they are common is a count in the frozen
  snapshot (`--body-file -` or `-F -` readers), which the harness can give.
  Settles whether a "judge a heredoc on the reader's own stdin" follow-up is
  worth its margin.
- **Design, vs architecture.md and the codebase.** The binding stays in the
  one file, imports nothing, hands `gates.pr_body_problems` a string, and
  adds no import edge (`TestOneOwner` and `one_owner.py` clean for this file).
  `_Unreadable` is the one failure channel, as designed. The deviations are
  listed in the Architect-routes finding above.
- **Security.** The hook executes nothing: no `subprocess`, `os.system`,
  `eval` or `exec` in the module; the only filesystem reads are
  `cli.read_file` (the guarded read, ADR-0075), `.git`/`commondir`/`config`,
  and `is_dir()` on a `cd` argument. Errors surface as
  `Type: message` notes, no paths beyond what the command already named.
  Pathological input is bounded: deep nesting hits `RecursionError`, which
  `preflight()` catches as an `Exception` and turns into exit 0; the fuzz
  never exceeded 17 ms per call. Exit 2 is advisory, not a security control.
- **Complexity, other cut-list lines.** `dead`: no unused name in the module
  (an AST single-reference sweep found none). `stdlib`: no hand-written
  stdlib equivalent. `platform`, `shorter`: nothing worth a cut. No
  `lean:` marker is added by the diff, so no marker owes a ceiling or
  trigger. The `speculative` and `reuse` cuts are the two findings above.
- **ADR compliance.** Live ADRs from `adr_status.py`: 128 ADRs (81 active,
  32 provisional, 15 partial, none retired). The ones the diff can reach: ADR-0106 (partial;
  the `cli.py` row superseded in part by ADR-0110) pins the
  `pr_body_preflight` -> `gates.py`/`cli.py` edges: unchanged, the diff adds
  no import edge, `tests/test_dual_membership.py` untouched. ADR-0075
  (provisional): the file read still goes through `cli.read_file`, there is
  no private `open()`. ADR-0061 (provisional, one-owner carve-outs): no
  duplicated constant is introduced; the duplicated logic is a `reuse`
  finding, not an ADR violation. The other ADRs address subjects the diff
  never reaches (pipeline, factory, eval, tracker). No ADR violated. No
  edit to any ADR's Decision section: `git diff --name-only` shows no
  `docs/adr/` path.
- **ADR owed? No.** Closest candidates against the three legs (hard to
  reverse, surprising without context, a real trade-off):
  1. Fail-closed allowlist (spelling identity, inert list, chain rule) for a
     blocking hook. A real trade-off and recorded as such in
     `architecture.md`; but it is private to one function with no stored
     data and no public interface, reversible by an edit, and the Verify
     replay was built to find out whether it had to be reversed.
  2. A hand-rolled partial shell lexer (`_Unrun`, 211 lines) rather than a
     sandboxed shell. The rejected alternative and its reason are in
     `architecture.md`; `stdlib-only` forced the shape. Reversible by
     rewriting the module's internals; the hook's contract (stdin payload,
     exit 0/2) does not move.
  3. Lowering the PRD target from 40% to 25% (Owner decision on 2026-11-09,
     recorded in `architecture.md` and the PRD). A product decision, not an
     architectural one, and reversible.
  Each fails the first leg. Records in the run's own artifacts are the right
  place, and they exist.
- **Standards.** `docs/standards.json` has four statements (`adr0004`,
  `adr0032`, `eval-honesty`, `stdlib-only`), all `advisory`; none is
  `enforced`. `stdlib-only` (factory domain) is met: imports are `re`,
  `shlex`, `json`, `os`, `sys`, `collections`, `pathlib`. `eval-honesty`
  (eval domain) is not touched by the diff. No finding cites a slug.
- **Test quality.** Strong. Assertions are exact `(exit, lines)` pairs against
  `gates.pr_body_problems(body) + [POINTER]`; only 12 assertions in 2004 lines
  are not exact (`assertIn`/`assertTrue`), and the #1667 vacuous
  `assertIn(code, (0, 2))` was replaced. The mutation run is the
  evidence for "no vacuous assertion in the binding rules": 65 of 65
  mutants killed. The two weaker spots (private-API pins, any-note helper)
  are the Minor above.
- **Module size and shape.** `pr_body_preflight.py` is 1098 lines with 42
  top-level definitions, one 211-line class (`_Unrun`) and a 57-line
  `_bound_body`. The shape concern is handed to `deepen` below, not
  refactored here.
- **kb page and docstring accuracy.** Module docstring and the kb paragraph
  match the final code for what binds and what is a note. Gaps: the page does
  not say which writers bind (Minor above); `verified: 3931922` is current
  (`kb.py drift` 0 problems before and after this PR).
- **Domain passes: none selected.** Changed paths are `pr_body_preflight.py`,
  `tests/test_pr_body_preflight.py`, `docs/kb/pr-body-contract.md` and
  `docs/features/pr-body-hook-coverage/*`: no payment, migration,
  dependency-manifest or UI-extension path matches
  `skills/review/references/domain-reviewers.md`. The word `checkout` appears
  in artifact text (`gh pr checkout`) but never in a changed path.

## Verdict

Ready to ship. No critical finding: I found no plausible agent command the
hook blocks wrongly and no plausible form that makes it judge a different
body than gh reads; the one residual (a leading truncation of the same file)
under-blocks and is implausible. One Major (the lean cut) and five Minors are
proposed deferrals the Owner arbitrates.

Unknowns, counted and not read as a pass: (1) the between-commands rule beyond
the 8 corpus cases (verification's own unknown, carried; my fixtures and the
mutant run exercise it but a real shell never ran those commands, by design);
(2) how many corpus readers use a stdin `--body-file -` form (not measured;
the corpus is private and I did not open it); (3) whether the 25% margin of 24
commands holds on another machine or day (verification's disk dependence,
carried); (4) which private-API tests the 65-mutant kill depends on (not
measured). The gates (`lint.py`, `gates.py`, `kb.py drift`) were run on this
branch and are clean; a green gate here proves the artifact is well-formed,
not that the code is correct.

`deepen` handoff (one line): `pr_body_preflight.py` mixes a hand-written shell
lexer (`_Unrun`, `_tokens`, `_simple_commands`), the binding policy
(`_bound_body` and the inert list) and the target policy (`_check_target`) in
one 1098-line module with two heredoc representations and a doubled position
index; look for the seam that lets the lexer and the policy change separately
without adding a root-module import edge (ADR-0106, `stdlib-only`).
