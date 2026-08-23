---
stage: review
run: maintenance:one-fact-one-owner
date: 2026-08-23
assumptions:
  - "No live user input — this run is driven from autorun-brief.md, so every severity call and every fix/defer decision below is mine, taken against CLAUDE.md, CONTEXT.md, the cited ADRs and the run's own artifacts rather than the operator's judgment. A severity the operator disagrees with is a line to correct, not a design change"
  - "Review depth is scaled to the blast radius defect.md records — internal tooling, nothing in CI, no user-facing surface. The new tool and its marker mechanism got a full-depth pass, driven against throwaway fixture trees in a scratch directory; the run's own documents got a lighter one; the eight true findings the tool prints were adjudicated only far enough to test the tool's precision, never to decide them (defect.md puts folding them out of scope)"
  - "Verify's battery is the floor and was NOT re-run (the maintenance scaling rule). What I re-derived instead was chosen from Verify's own Not verified list: two of the eight findings it read only as tool output, and the boundary behaviour it covered through injected fakes"
  - "Nothing was committed, pushed or fixed. The pre-existing uncommitted files (docs/backlog.md and the two other runs' retro.md) were left untouched, as were this run's other artifacts"
---

# Review: a pre-pass that asks whether a fact is stated twice

## Scope

`git diff a527688^..HEAD` — 14 commits (`a527688` through `62a3e56`),
12 files, +2,028 / −1. Not the whole repo. Plus the run's uncommitted
artifacts (`defect.md`, `architecture.md`, `breakdown.md`,
`verification.md`).

What that covers, by subject:

- **The tool** — `one_owner.py` (443 lines), its five public interfaces
  (`groups`, `fact_sites`, `source_files`, `markers`, `check`) and its
  `main`.
- **The suite** — `tests/test_one_owner.py` (975 lines), 61 cases across
  12 classes, all against literal fact sites or fixture trees.
- **The mechanism** — the `# one-owner:` marker grammar and the three
  live annotations on the `runner('git')` group (`budget_guard.py:113`,
  `dashboard.py:63`, `one_owner.py:54`).
- **The record** — `docs/adr/0061-a-carve-out-lives-at-the-definition-site.md`
  (provisional) and its `docs/adr/README.md` index row.
- **The payload** — the regenerated
  `factory/templates/tools/factory/budget_guard.py` twin and the one
  changed line in `factory/manifest.json`.
- **The triggers** — the `CLAUDE.md` entry, `factory.py`'s verb row, and
  the added step 9 in `docs/factory/improvement-routine.md` §2.

**What I re-derived rather than read.** Verify's battery is the floor, so
I did not re-run it. I drove `one_owner.check` against four throwaway
fixture trees in a scratch directory to test boundaries the suite does
not reach (a git-quoted path, a decorated definition, a counterpart that
is defined but is not a fact site, two junk short-string groups). I
adjudicated two of the eight findings Verify read only as tool output
(`budget_guard.record` / `cost_ledger.row_key`, and the
`READY_LABEL` triple) by reading the sources. I measured
`one_owner.py`'s docstring-to-code ratio against all 28 root modules to
settle the size question. I re-confirmed the three tripwires the run set
itself: `plane_drift.py` is absent from the diff, `gates.py` is absent
from the diff entirely (letter `K` still reads `"K": (None, None,
"unused")` at `gates.py:1111`), and no module imports `one_owner`.

**What I did not examine.** Six of the eight true findings (out of scope
to decide, and Verify's enumeration reconciles). `trigger_eval.py` and
`charter_replay.py` (paid model runs). `update-manifest` idempotence
(it writes to the tree; detector E and `tests/test_factory_init.py` are
green). The commit-by-commit test-ordering evidence, which Verify scored
under D7 from the commit bodies.

## Findings

**No critical findings. Nothing blocks Ship on correctness.** Two majors
and six minors follow.

### Major: the carve-out has exactly one escape hatch, and it costs an ADR

- Scenario: `_stated_value` (`one_owner.py:121-125`) excludes a bare
  numeric, boolean or `None` literal and nothing else, so any shared
  string is a fact. Driven in a scratch tree: two modules each binding
  `ENCODING = 'utf-8'`, and two each binding `SEP = ', '`, produce two
  findings. The only way to silence one is a `# one-owner:` marker, and
  `_MARKER` (`one_owner.py:69-71`) makes `(ADR-####)` mandatory while
  `_rent` (`one_owner.py:396-398`) requires it to resolve to a file in
  `docs/adr/`. A reviewer facing a junk group therefore has three
  moves, and CLAUDE.md forbids two of them: fold the constant into a
  seam (fails the seam bar — no observed divergence, and anticipated
  reuse does not qualify); write an ADR for a string constant (fails
  defect.md's own restatement of the bar — "offer an ADR only when a
  decision is hard to reverse, surprising without context, and the
  result of a real trade-off"); or cite an unrelated ADR, which is the
  move that makes the citation decorative.
- The day-one annotation already shows the pressure. The three live
  markers read `(ADR-0061) — ADR-0037 sanctions the alias`, with
  ADR-0037 quoted in the comment line above as *"so their problem
  strings read unchanged"*. ADR-0037's actual sentence
  (`docs/adr/0037-factory-seam-modules.md:35-37`) names two aliases —
  `GH_FAILURES`, `GIT_FAILURES` — and its rationale is true of them:
  they appear in problem strings. `git_runner` appears in no problem
  string, so the quoted rationale does not apply to the annotated
  binding. The generous reading is available (ADR-0037 lists
  `runner(binary)` among the seam's three names), but the marker cites
  the clause by a rationale that is false of what it excuses — and
  nothing mechanical can catch that, because `_rent` checks only that
  the file exists. The mechanism guarantees a carve-out names *an* ADR,
  never that the ADR sanctions *this* duplicate.
- Decision: **deferred.** No junk group exists at HEAD, the tool is not
  a gate, and widening the grammar (an optional citation, or a second
  marker form for "not a fact, a knob") reopens ADR-0061's recorded
  decision — that is Architect's, not a pre-ship patch. Reason to log
  when it is seeded: the first tightening pressure will arrive as a
  false positive nobody can silence proportionately, which is
  defect.md's hazard 1 arriving through the carve-out rather than
  around it.

### Major: the routine step asks for a delta the routine cannot compute

- Scenario: `docs/factory/improvement-routine.md` §2 step 9 says
  findings "are report material, and a group that is NEW since the last
  routine run is a `docs/backlog.md` seed proposal under Proposals".
  The routine's memory is fixed by §7: *"the journal is the routine's
  only memory"*, and the journal comment's skeleton has six slots —
  Pick, Health, Queue, Reflect, Proposals, Spend — plus a
  `<!-- routine-state last-scan=... -->` marker carrying a timestamp
  and nothing else. There is no slot for a findings list, and by design
  there is no baseline file (architecture.md rejects one: "a baseline
  is a roster with a worse name"). So on day N+1 the routine sees ten
  findings where day N saw nine and has no recorded prior list to
  subtract; §2 is read-only, so it cannot re-run the pass at the
  previous commit either. It then either proposes nothing (the daily
  trigger silently delivers nothing, and the tool degrades to the
  on-demand command — which architecture.md's own assumption allows,
  but not silently) or re-proposes all ten every day, which is the
  backlog noise that gets a pre-pass ignored.
- Every other §2 step lands in a named slot (step 6 CI to Health, step
  8 beads to Queue, step 7 LEDGER to Proposals). Step 9 is the only one
  whose output has no home.
- Decision: **fix before Ship**, routed to Implement. It is a
  documentation edit of a few lines — give the findings a slot in §7's
  skeleton (or name Health/Proposals explicitly) and say that the
  report lists the group identities, which is what makes the next run's
  delta computable. This makes C4's own acceptance criterion true;
  today it is written but not implementable.
- **Fixed 2026-08-23 in `881787b`.** The smaller of the two shapes
  above was taken: §7's six-slot skeleton is untouched, and step 9
  itself now defines a new group as one `docs/backlog.md` does not
  already name, with the proposal quoting the tool's line so the
  group's `<module>.<name>` members travel into the seed. The delta is
  computable from a tracked file the routine reads in the same step, no
  baseline or suppressions file was added, and the step is still
  read-only §2 intel that never colours main red. C4's acceptance
  criterion is now true as written.

### Minor: a git-quoted path is skipped, and any duplicate inside it is invisible

- Scenario: `source_files` (`one_owner.py:214`) runs
  `git ls-files -- '*.py'` and splits on newlines. Git C-quotes any
  path with non-ASCII bytes or control characters by default. Driven in
  a scratch repo containing `café.py` and `plain.py`, both binding the
  same string: git returns `"caf\303\251.py"`, `Path(root) / rel`
  cannot open it, and `check` returns exactly one problem —
  `one-owner: "caf\303\251.py" cannot be read: [Errno 2] ...` — while
  the duplicate the two files share is **not** reported. A path
  containing a newline would corrupt the split outright.
- The failure is loud rather than silent (the unreadable file is a
  problem string), which is why this is minor and not major, and the
  tool's stated invariant "an EMPTY universe is never silently clean"
  still holds. But the universe is partially blinded, and the module's
  own docstring claims the list is "every module this repo owns, and
  nothing else".
- Decision: **deferred.** No tracked path in this repo has a non-ASCII
  or control character (98 tracked `.py` files, all ASCII). Fix when
  seeded: `ls-files -z` split on NUL, or `-c core.quotePath=false`.

### Minor: a marker above a decorated definition is rejected as "above no definition"

- Scenario: `markers` joins to `fact_sites` by the definition's own
  `lineno`, and `ast.FunctionDef.lineno` is the `def` line, not the
  first decorator. Driven directly:
  `markers("probe.py", "# one-owner: other.fn (ADR-0061) — reason\n@staticmethod\ndef fn(payload): ...")`
  returns `([], ['one-owner: probe.py:1 is a one-owner marker above no
  definition'])`. An author who writes a correct carve-out above a
  decorated function gets two problems instead of zero, and the
  diagnostic tells them there is no definition when there plainly is
  one. The only workaround is to bury the comment between the decorator
  and the `def`.
- The implementation matches architecture.md's literal wording ("the
  definition's own line"), so this is a gap in the design's join key,
  not a coding slip. It silences nothing, so it can never buy a false
  quiet.
- Decision: **deferred.** The repo has one decorator in 28 root modules
  (`cli.py:169`) and it is not a fact site. Fix when seeded: attach
  from `min(d.lineno for d in node.decorator_list)` when the list is
  non-empty.

### Minor: `_adr_ids` reads the filesystem, which is the rule the tool refuses everywhere else

- Scenario: `_adr_ids` (`one_owner.py:321-326`) globs
  `docs/adr/[0-9][0-9][0-9][0-9]-*.md` off disk, while `source_files`
  builds its universe from git precisely because "no committed file can
  be relied on" to hide untracked ones. An author drafts
  `docs/adr/0062-....md` locally, adds a marker citing it, runs the
  pass and gets silence — then commits the marker and forgets to
  `git add` the record. The dangling citation is now in the repo, and
  the tool reports it for every other checkout but not for the author's.
  The module docstring's "the same tree yields byte-identical output"
  is true only of a working tree, not of a commit.
- Decision: **deferred.** Low blast radius (the pass is not a gate, and
  the next person to run it sees the dangling citation), and the fix is
  the same one-line change as the quoting finding — derive the ADR list
  from the same `ls-files` call.

### Minor: "which is not defined in this repo" fires for a counterpart that is defined

- Scenario: `_rent` builds `defined` from fact sites only, so a
  counterpart that exists but states no fact is reported as missing.
  Driven in a scratch tree: `b.py` defines `def foo(payload)` reading
  one key (below the two-key floor, so not a fact site); a marker in
  `a.py` naming `b.foo` yields
  `one-owner: a.py:1 names b.foo, which is not defined in this repo`.
  The realistic path here is a fold: the counterpart is simplified
  until it drops below the floor, and the maintainer is sent looking
  for a deletion that never happened.
- Decision: **deferred.** The message is wrong about the cause, not
  about the conclusion — the marker does need attention either way.
  Seed the wording fix ("names `b.foo`, which states no fact this pass
  can see").

### Minor: ADR-0061 records the first annotation as a pair; the tree carries three

- Decayed contract: `docs/adr/0061-a-carve-out-lives-at-the-definition-site.md:79-83`
  says *"The first annotation this decision writes is
  `budget_guard.git_runner` / `dashboard.git_runner`, the `runner('git')`
  **pair**"*. The tree carries three markers, because `one_owner.py:55`
  binds `runner('git')` too and joins the group. `breakdown.md` design
  gap 3 identified the triple before Implement started, and A5/B4 were
  written over "every member the tool reports" for exactly that reason
  — but the ADR text, copied from architecture.md's pre-tool proposal,
  was not updated with it.
- Scenario: a maintainer auditing the carve-out in six months reads the
  record, counts two sanctioned owners and finds three markers, and
  cannot tell whether `one_owner.git_runner`'s marker is part of the
  decision or a later unrecorded addition. This is the decay ADR-0061
  exists to prevent, in the record itself, on day one.
- Decision: **fix before Ship**, routed to Implement. It is a
  one-sentence edit to a provisional record this run is already
  authorized to write (architecture.md's *ADRs* resolution), and
  `docs/adr/**` is not mirrored, so no manifest regeneration follows.
- **Fixed 2026-08-23 in `58db94a`.** The Consequences bullet now names
  the `runner('git')` group's three members and the cycle they close,
  corrected in place rather than superseded: the status stays
  `provisional`, and the decision, the reasoning and the operator's
  mirrored-file paragraph are untouched, with the `docs/adr/README.md`
  index row still byte-identical to the status line.

### Minor: the suite hand-writes a pin the shared CLI contract already owns

- Decayed contract: `tests/cli_contract.py:22` defines `ReportContract`
  — the mixin whose whole job is "a clean run exits 0 and ENDS with the
  tool's exact summary line ... the count always computed, never a
  hand-typed literal" — and its docstring records that seven suites'
  copies were folded into it. Thirteen test files use it, and
  `tests/test_handoff.py` is the only other suite that mixes in
  `CliContract` without it. `tests/test_one_owner.py:533` mixes in `CliContract` only and
  hand-writes the equivalent assertion at `:552-557`.
- Scenario: `cli.report`'s summary grammar has already grown once
  (`prefix`/`suffix`). The next change to it updates `ReportContract`
  in one place and every suite that uses it; `test_one_owner.py`'s copy
  has to be found and edited separately. The cost is one extra edit and
  a loud failure, not a silent pass — hence minor.
- Worth naming because of what it says about the run's own boundary:
  this duplicate is invisible to `one_owner.py` twice over. `tests/**`
  is excluded from the universe (architecture.md's fourth assumption),
  and even included it would not fire, because the duplication is
  behavioural prose rather than a shared value or a shared key set —
  the known-miss class C2 pins.
- Decision: **deferred.** Test-only, loud on failure, and the fix is a
  two-line mixin swap that is cheaper to do alongside the next change
  to `cli.report`.

## Passes with no findings

**Security — clean.** `cli.runner` (`cli.py:296-303`) invokes
`subprocess.run([binary, *args], check=True, capture_output=True,
text=True)` — argument list, no shell, no interpolation, so the
`ls-files` call has no injection surface and `one_owner.py` adds none.
The only external input the tool reads is repo source it parses with
`ast.parse`, which evaluates nothing. No secret, credential, token,
path outside the repo, or environment read appears anywhere in the
diff. Errors surface through `cli.detail`, which is the repo's existing
convention for a failed CLI call and leaks only git's own stderr line.
The tool writes nothing, anywhere — no state file, no baseline, no
cache — which is also what makes retry trivially safe. The one boundary
worth naming is `tokenize` failures being swallowed at
`one_owner.py:261-262`, and that is correct rather than silent:
`fact_sites` reports the same unparseable module, and the comment says
so.

**Design — clean against every hard convention.** Stdlib only (`ast`,
`io`, `re`, `sys`, `tokenize`, `collections`, `pathlib`); standalone,
with a `__main__` guard and a front-door verb. No `gates` import, and
no module imports `one_owner` — the tool-to-tool coupling ADR-0058
removed is not reintroduced in either direction. No new shared module:
`check` has one production caller and no observed divergence with
anything, so the seam bar is not even approached. `one_owner.py` joins
no `factory_init.MIRRORS` entry, which is ADR-0060's mirrored-iff-
imported rule applied correctly; the one mirrored file it does touch
(`budget_guard.py`) got its twin regenerated and its manifest line
updated in the same commit, and ADR-0061 states the rule for the next
annotation rather than leaving it a one-off. The problem-string
contract is honoured exactly — `check` returns a sorted list of
`one-owner: `-prefixed strings and raises on nothing, `main` prints
through `cli.report` and returns its code, `__main__` does the
`sys.exit`. ADR-0032 is respected: no `WO-####` token is minted and no
tracker issue exists. Detector letter `K` is still unclaimed,
`CHECKERS` is untouched, and `gates.py` does not appear in the diff at
all, so the mid-flight `first-live-dispatch` work order's target is
undisturbed.

**The run's own tripwires hold.** `plane_drift.py` is absent from the
diff and from `git status`; the acceptance fixture still reports at
`cli.py:376` / `plane_drift.py:31`. The self-reference defence is real
rather than asserted: `_standalone_comments` tokenizes instead of line-
scanning, so the grammar at `one_owner.py:21` (inside the module
docstring) and at `:66` (a string constant) are a STRING token and not
a COMMENT, and `tests/test_one_owner.py:648-655` pins that at the
interface. The vouching cycle degrades correctly under ordinary edits —
I walked deletion, rename and binding-removal of each of the three
members, and every case produces findings in the surviving files rather
than silence, which is the property ADR-0061 claims.

**The size overrun is incidental, not structural.** Measured across all
28 root modules, `one_owner.py` is 36% docstring — inside the band the
codebase already holds (`cli.py` 40%, `budget_guard.py` 44%,
`plane_drift.py` 39%, `cost_ledger.py` 36%), and its 198 code lines sit
at the median and inside architecture.md's ~250 estimate. Six root
modules are longer than 443 lines. Splitting it would create a second
module with exactly one caller, which is the seam bar failing in the
other direction. Deviation 7's own analysis is correct and I confirmed
it independently. `tests/test_one_owner.py` at 975 lines is the fifth
largest of 51 test files; four are larger.

**Correctness — the two findings I adjudicated are true findings, and
sharp ones.** `budget_guard.record` (`budget_guard.py:198`) writes
`existing.get("wo") == wo and existing.get("run_id") == run_id` three
lines after calling `cost_ledger.entry` — an inline retyping of
`cost_ledger.row_key`'s ADR-0041 dedup identity, in a module that
imports the seam. That is a textbook instance of the class, found
unaided, and it is the strongest evidence in this run that the
`same-keys` rule earns its place. The `READY_LABEL` triple
(`assembler.py:54`, `validator.py:79`, `work_queue.py:39`) is a genuine
third owner of a dispatch label with no recorded decision behind it. I
found no false positive among the findings I read.

## Verdict

**Ready to ship once the two fixes land.** No critical findings; nothing
in the diff is wrong in a way that would misreport the tree, and the
success criterion the run exists for — the acceptance fixture found
unaided, with the tool's own source naming none of it — holds under
independent re-derivation.

Two items route back to Implement before Ship, both documentation and
both small: the routine step's uncomputable delta
(`docs/factory/improvement-routine.md` §2 step 9 and §7's skeleton) and
ADR-0061's "pair" that is a triple. Neither touches `one_owner.py`, so
Verify's evidence survives both; a re-run of `lint.py` after the edits
is the whole re-verification cost.

Five minors are deferred with reasons logged above, and the major about
the carve-out's ADR-only escape hatch is deferred to Architect as a
`docs/backlog.md` seed — it is the first thing that will bite, and it
should be decided rather than discovered.
