---
stage: decompose
run: maintenance:one-fact-one-owner
date: 2026-08-23
assumptions:
  - "The cut was not reviewed live — this run is driven from autorun-brief.md, so the milestone boundaries, the item sizes and the ordering below are read out of architecture.md's Components and Interfaces & contracts sections rather than from the operator's judgment. A mis-sized row is a note to log at implement time, not a design change."
  - "Items are lettered and carry a size class (ADR-0034 vocabulary), matching docs/fixes/deepening-tool-seams/breakdown.md, this run's stated artifact-depth precedent. No row mints a WO-#### id and no row carries a (tracker: #N) reference: WO- tokens are dispatch-plane identifiers that detectors A and C read, minting one with no issue behind it would run the dispatch plane ahead of the knowledge plane (ADR-0032), and defect.md rules out tracker interaction entirely. These checkboxes are the whole state (ADR-0026)."
  - "The test-ordering rule is served INSIDE each item, not as standalone pin items. one_owner.py does not exist, so no test at its intended interface can land green against today's code — the file would not import. So every item writes its cases first, watches them fail, and records that failure in the commit message, which is the same way the precedent's A1 and C1 served the rule. The alternative — a whole test file landing red as an item of its own — leaves the tree red at an item boundary, which the precedent explicitly refuses."
  - "factory.py's verb row is absorbed into A5 rather than routed back to Architect. architecture.md never mentions the front door, but tests/test_factory_cli.py DERIVES factory.VERBS from a scan of root modules carrying an `if __name__ == \"__main__\":` guard and its own docstring says a new guard breaks the test until the tool gets its verb. Nothing is chosen — the verb IS the module name and the convention column is derived from main's signature — so this is a lookup, not a decision. Recorded under Design gaps found with its authority named."
  - "CLAUDE.md placement: architecture.md's assumption puts the command 'beside the existing on-demand tools', and that section's preamble today reads 'On demand only (real model runs, costs money, never CI; both need the `claude` CLI)'. Every one of those claims is false of one_owner.py. C3's criterion therefore constrains the outcome (a reader can find and run the command; the preamble is not left false) and leaves the exact wording to Implement, because the inputs name the file and not the sentence."
  - "The eight true findings the tool prints on day one are NOT an Implement work item. architecture.md calls routing them to docs/backlog.md 'the run's closing act, not a design element', and the protocol names Operate as the backlog's producer at run close. No item here folds, fixes, or seeds them."
  - "The known-miss pin (C2) lands in tests/test_one_owner.py. The operator's resolution names the SHAPE (tests/test_knowledge_plane.py:99-107) but not the file; the pin is about this tool's limit, so it lives in this tool's suite."
  - "The optional daily-routine trigger is kept as C4 rather than dropped. architecture.md's own assumption says the design works on the documented command alone and the trigger degrades without taking the tool with it, so it is written last, marked optional, and blocks nothing."
---

# Breakdown: a pre-pass that asks whether a fact is stated twice

Progress lives in the checkboxes below. Source is `architecture.md` in this
directory, which designed one root tool against a feasibility probe run at
HEAD `7650052` and at `fbfa3c3`. Rows carry an item letter, a size class and
blocking edges; they carry no work-order id and no tracker reference.

**The one thing that must not happen.** `plane_drift.issue_lifecycle` is this
run's acceptance fixture and stays exactly as it is. No item below touches
`plane_drift.py`. An item that "cleaned up" that duplicate would destroy the
only live proof the tool has, and `defect.md` puts it out of scope for
precisely that reason. If a diff in this run modifies `plane_drift.py`, the
item has been misread — revert it.

**The ordering rule, which decides the cut.** Tests at the intended interface
land before the implementation. The tool is a new module, so no test can land
green against today's code; the rule is therefore honoured *inside* every
item — the cases are written, watched to fail, and the failure is recorded in
that item's commit message before the code that turns them green. Read the
history for that pattern, not for separate pin commits.

**The battery is green at every item**, in full: `python3 -m unittest
discover tests`, `python3 lint.py` (matching `lint: 0 problem(s)`) and
`python3 gates.py && python3 gates.py --selftest` (matching `gates: 0
problem(s)` and `selftest: ok`). Note that `python3 one_owner.py` exiting
nonzero is **not** part of the battery and never becomes part of it: the tool
is deliberately outside `make check` (architecture.md, *Approach*), and a
finding must never colour main red.

**Manifest churn.** One item and only one touches a `factory_init.MIRRORS`
entry: **B4**, whose annotation lands in `budget_guard.py`. That contradicts
`architecture.md`'s own claim that this run "touches no checksum", so it is
recorded as **design gap 1** and routed back to Architect rather than
absorbed. Every other item leaves `factory/` untouched and needs no
`update-manifest` run.

## Milestone A: the pass exists and finds the live fixture unaided

Demonstrable at the close: `python3 one_owner.py` runs from the repo root and
prints the identities `architecture.md` measured, including the acceptance
fixture — `cli.label_names` and `plane_drift.issue_lifecycle` reading the
same payload keys — with no rule in the tool naming either one.

- [x] **A1** the module and its pure core — size:S, blocked by: —
  - Accept: `one_owner.py` exists at the repo root with a one-line summary
    docstring (`factory.index()` reads each module's docstring first line, so
    a missing one degrades the front-door index), the `FactSite`, `Marker`
    and `Group` `namedtuple`s exactly as `architecture.md`'s *Data model*
    declares them, and `groups(sites)` returning the groups whose members
    span two or more distinct modules, sorted by identity. `TestGroups` in
    `tests/test_one_owner.py` covers: two members in distinct modules group;
    two members in the SAME module do not; three members in three modules
    group as one; identical identities sort deterministically; the function
    is total and raises on nothing, driven from literal `FactSite` lists with
    no filesystem, no subprocess and no clock. Every case is written and
    watched to fail (the module does not import) before the code exists, and
    the commit message says so. The module imports only stdlib plus
    `cli`/`knowledge_plane` names it actually uses, and imports `gates` never
    — a tool importing a detector module is the coupling ADR-0058 removed.
    No `__main__` guard yet (that is A5's, together with its verb row).
    `factory/` untouched; no manifest regeneration.
- [x] **A2** `same-value` — a module states a value a second module states — size:M, blocked by: A1
  - Accept: `fact_sites(path, source)` returns `([FactSite, ...], problems)`
    in source order for the `same-value` kind: a module-level `NAME = <expr>`
    assignment whose identity is `ast.unparse(value)`, excluded when the
    value is a bare numeric, boolean or `None` literal. Cases, written red
    first: the miss-1 shape (two modules each binding
    `re.compile(r"^\s*[-*+]\s+\[x\]", re.IGNORECASE)` under different names)
    yields one group; the same value written with different formatting and
    line-wrapping yields the same identity, because `ast.unparse` normalises
    it; a bare `100` shared by two modules yields nothing, and so does a
    shared `True` and a shared `None`; **the canonical deliberate pair stays
    silent** — two modules holding `protocol._CHECKBOX` and
    `knowledge_plane.ROW` exactly as written at HEAD produce NO group,
    because their patterns and flags differ and the identity is exact, with
    no marker involved; a module whose source does not parse yields no sites
    and the problem `one-owner: <path> cannot be parsed: <err>`, with every
    other module still contributing. `factory/` untouched.
- [x] **A3** `same-keys` — two functions read the same named external shape — size:M, blocked by: A2
  - Accept: `fact_sites` also returns the `same-keys` kind: a function
    definition anywhere in the module, whose identity is the sorted set of
    string literals used as `.get("...")` arguments or `[...]` subscripts,
    when there are at least two. Cases, written red first: the miss-3 shape —
    one function shaped like `cli.label_names` and one shaped like
    `plane_drift.issue_lifecycle`, whose shared key set is exactly
    `{labels, name}` — yields one group, which is why the floor is **two**
    keys and not three; a function reading one key yields no site, so the
    floor is asserted at its boundary rather than assumed; two functions
    reading the same two keys through different syntax (`.get` on one side,
    subscript on the other) share an identity; two functions whose key sets
    merely overlap do not; a nested function is reached, since the rule is
    "anywhere in the module". Demonstrable here rather than at A5: the two
    identities together cover both mechanical forms `defect.md`'s *Target
    state* names. `factory/` untouched.
- [x] **A4** the universe comes from git, never from a filesystem walk — size:M, blocked by: A1
  - Accept: `source_files(root, run=git_runner)` returns
    `([(repo-relative posix path, source text), ...], problems)` sorted by
    path, with the list derived from `git -C <root> ls-files -- '*.py'` and
    from nothing else, and with `factory/**` and `tests/**` excluded. The
    runner is injected, so the suite never shells out. Cases, written red
    first: a fake runner returning a path under `.claude/worktrees/` proves
    the walk cannot see it, which is the concrete hazard `defect.md`'s Notes
    recorded (at HEAD, `rglob` finds 248 Python files where git tracks 96,
    and 152 of the difference are stale worktree copies hidden only by the
    local, uncommitted `.git/info/exclude:11`); a tracked path under
    `factory/` is excluded, and so is one under `tests/`; a `CLI_FAILURES`
    raise becomes `one-owner: git ls-files failed: <cli.detail(err)>` with an
    empty file list; a file that cannot be decoded becomes `one-owner: <path>
    cannot be read: <err>` and is skipped while the rest of the run
    continues. **An empty universe is never silently clean** — the empty-list
    case is asserted to carry a problem, so a broken environment cannot read
    as "no duplicates". `factory/` untouched.
- [x] **A5** `check`, `main`, and the acceptance fixture found unaided — size:M, blocked by: A3, A4
  - Accept: `check(root, run=git_runner)` returns a sorted list of
    `one-owner: `-prefixed problem strings, and an uncovered group renders as
    `… state the same value — one fact, one owner` or `… read the same
    payload keys (<keys>) — one fact, one owner`, every member listed, sorted
    by path then line, byte-identical across two runs on the same tree.
    `main(argv)` returns `cli.report("one-owner", check(repo_root()))` and an
    `if __name__ == "__main__":` guard calls it; `factory.VERBS` gains
    `"one-owner": ("one_owner", "argv")` in the same change, because
    `tests/test_factory_cli.py` derives that table from a scan for the guard
    and goes red the moment one appears without its verb (design gap 2).
    `factory.py` is not a MIRRORS entry, so this adds no manifest churn.
    **The acceptance criterion of the whole run lands here:** run against the
    live tree, the output contains the group holding `cli.py … label_names`
    and `plane_drift.py … issue_lifecycle`, and `grep -n -e label_names -e
    issue_lifecycle -e plane_drift -e cli\\.py one_owner.py` finds nothing —
    the tool was not told about it. `plane_drift.py` is not modified.
    Expect the `runner('git')` group to hold **three** members from this item
    onward, not the pair `architecture.md`'s table shows: `one_owner.py`'s
    own `git_runner` binding joins it (design gap 3), and the item asserts
    what the tool prints rather than a count copied from the design.
    `factory/` untouched.

## Milestone B: the carve-out pays rent in both directions

Demonstrable at the close of B3: the mechanism exists, is exercised against
fixture trees, and the decision behind it is recorded. Demonstrable at the
close of B4 — **once design gap 1 is answered** — the `runner('git')` group
is silent because every member vouches for another, and deleting any one
marker makes the whole group speak up again.

- [x] **B1** the marker grammar, read at the definition site — size:M, blocked by: A3
  - Accept: `markers(path, source)` returns `([Marker, ...], problems)` for
    comment lines matching `# one-owner: <module>.<name> (ADR-####) —
    <reason>` inside the contiguous comment block immediately above a fact
    site's own line, blank lines ending the block, joined to `fact_sites` by
    the definition's `lineno`. Cases, written red first: a well-formed marker
    directly above a definition is read; one separated from it by a blank
    line is not attached; a marker mid-block among ordinary comments is read
    (`budget_guard.py:108-110` is a real three-line block, so this is the
    shape the first annotation actually needs); an unreadable `# one-owner:`
    line yields `one-owner: <path>:<line> is not a readable one-owner marker
    (expected …)`; an empty reason yields `one-owner: <path>:<line> marks
    <name> deliberate with no reason — a bare marker waives nothing`; a
    marker above no definition yields `one-owner: <path>:<line> is a
    one-owner marker above no definition`. In each failure case the marker
    silences nothing — the suite asserts the group still reports. **The
    self-reference hazard is closed in this item:** the grammar is documented
    in `one_owner.py`'s module docstring and appears in no comment in that
    file, verified by running the tool against the live tree and finding
    `one_owner.py` reporting no stale marker of its own. `factory/`
    untouched.
- [ ] **B2** silence is a property of the group, never of one marker — size:M, blocked by: A5, B1
  - Accept: `check` joins markers to groups and adds the five remaining
    shapes from `architecture.md`'s contract, each pinned by exact string
    against a fixture tree: a member with no marker in an otherwise-marked
    group → `… joins a recorded deliberate group without a marker — a new
    owner cannot admit itself`; a member no other member names → `… carries a
    marker but no other owner names it — an existing owner must vouch for a
    new one`; a marker matching no group → `… is marked deliberate against
    <counterpart>, but nothing duplicates it — remove the marker`; an
    unresolvable counterpart → `… names <counterpart>, which is not defined
    in this repo`; a citation with no file in `docs/adr/` → `… cites
    <ADR-####>, which is not in docs/adr/`. Two properties are asserted
    directly, because they are the reasons the mechanism exists: a fully
    covered group is **silent**, and adding a third, unmarked member to that
    same fixture group makes it speak again — the ADR-0039 failure, made
    impossible. Status liveness is deliberately NOT checked, and a fixture
    citing a superseded ADR is asserted to produce no problem, so the
    deferral is visible in the suite rather than only in prose. `check`
    raises on nothing. `factory/` untouched.
- [ ] **B3** the 0061 decision record is written — size:S, blocked by: —
  - Accept: `docs/adr/0061-a-carve-out-lives-at-the-definition-site.md`
    exists with the text the operator agreed to in `architecture.md`'s *ADRs*
    section, status `provisional`, dated 2026-08-23. Its `- Status:` line
    satisfies `gates.ADR_STATUS` (detector D), and a new row joins
    `docs/adr/README.md`'s index in the same three-column shape as the 0060
    row above it: a first cell linking the file by its own filename, a title
    cell reading "A carve-out lives at the definition site and must pay
    rent", and a status cell matching the file's `- Status:` line **byte for
    byte**, which is what detector D compares. (The row is described rather
    than quoted here because a live markdown link to a file that does not
    exist yet is a stale link to detector I.) This is the one file this run adds
    under `docs/adr/`, and it makes seven open provisionals, knowingly.
    `python3 gates.py && python3 gates.py --selftest` green. `factory/`
    untouched; `docs/` is not mirrored, so no manifest regeneration.
- [ ] **B4** the first annotation, and the mechanism has a real user — size:S, blocked by: B2, B3 — **gap 1 answered 2026-08-23: the annotation stays in the `runner('git')` group, `budget_guard.py` included, and the manifest is regenerated with it**
  - Accept: every member of the live `runner('git')` group carries a
    `# one-owner:` marker citing the 0061 record with a non-empty reason naming
    the ADR-0037 sanction ("Callers alias to their own names … so their
    problem strings read unchanged"), and every member is named by some other
    member's marker, so `python3 one_owner.py` no longer reports that group.
    Membership is read from the tool's own output rather than from
    `architecture.md`'s table, which predates the tool: expect
    `budget_guard.py`, `dashboard.py` and `one_owner.py` (design gap 3).
    Deleting any single marker and re-running makes the group speak — checked
    by hand and recorded in the commit message, because it is the whole claim
    of the 0061 record and no fixture can prove it about the live tree. **If the
    annotation still lands in `budget_guard.py` after gap 1 is answered:**
    `python3 factory_init.py update-manifest` runs in that same commit, the
    regenerated payload twin and manifest are committed with it, detector E
    is green and `tests/test_factory_init.py`'s payload-vs-root pin is green.
    `plane_drift.py` is not touched, and the fixture at line nine still
    reports.

## Milestone C: the run's evidence, and the command a person can find

Demonstrable at the close: the suite would have caught two of the three
historical instances and says out loud, in the suite itself, that it does not
catch the third and why; and a reader of `CLAUDE.md` can run the tool.

- [ ] **C1** the two historical instances the tool catches — size:M, blocked by: A5
  - Accept: `tests/test_one_owner.py` pins the exact problem strings through
    `check` against **fixture trees**, never the live tree, so the suite does
    not decay as the tree is cleaned. Miss 1: a fixture reproducing
    `gates.MERGED_ROW` and `knowledge_plane.DONE_ROW` — byte-identical
    `re.compile` bindings in two modules — yields the `same value` string
    naming both. Miss 3: a fixture reproducing `cli.label_names` and
    `sweeps.issue_lifecycle` at `fbfa3c3` — the two differing walks over
    `{labels, name}` — yields the `same payload keys (labels, name)` string
    naming both. Each fixture cites, in a comment, the commit and PR from
    `defect.md`'s evidence table it reproduces (`208ffdb`/#130 and
    `4333370`/#221; `f38fbdd`/#204 and `622e2bf`/#247), so a later reader can
    tell a fixture from an invention. The suite injects a fake git runner and
    shells out nowhere. `factory/` untouched.
- [ ] **C2** the third instance, pinned as a known miss — size:S, blocked by: C1
  - Accept: a case in `tests/test_one_owner.py`, in the shape of
    `tests/test_knowledge_plane.py:99-107`, asserts that a fixture
    reproducing `sweeps.reconcile_drift` and `dashboard._drift` at `fbfa3c3`
    (7 statements over 69 lines against 3 over 21, sharing no identical text
    and a narrower rule on one side) yields **no** finding, with the reason
    in a comment above it: no cheap syntactic rule reaches a
    re-implementation, two candidate rules were built and lost on measured
    evidence (`architecture.md`, *Decisions & alternatives*), and closing it
    needs semantic comparison — the over-cleverness `defect.md`'s hazard 2
    names as a way this run dies. The comment states that this is the
    **amended** success criterion: `defect.md` asked for a test catching all
    three, the operator accepted the substitution on 2026-08-23, and the
    amendment is recorded in `architecture.md`'s *Measured against the tree*.
    The assertion's message says plainly that a finding here is a
    **welcome** change and means the rules got stronger, not that the test
    broke. Verify scores against the amended form and must say it was amended
    and why. `factory/` untouched.
- [ ] **C3** `CLAUDE.md` documents the command, and the battery closes the run — size:S, blocked by: A5
  - Accept: `CLAUDE.md` names `python3 one_owner.py`, says in one line what
    it answers, and says that it is not part of `make check` and never
    colours main red. It sits beside the existing non-CI tools, and the
    section's preamble is not left false by it — today that preamble reads
    "On demand only (real model runs, costs money, never CI; **both** need
    the `claude` CLI)", and `one_owner.py` is free, needs no `claude` CLI,
    and is a third entry, so either it gets its own framing or the preamble
    is corrected; the wording is Implement's, the constraint is that a reader
    who has never seen the tool can find it and run it. `CLAUDE.md` is not a
    `factory_init.MIRRORS` entry, so no manifest regeneration. **The full
    battery closes the required work:** `python3 -m unittest discover tests`,
    `python3 lint.py` matching `lint: 0 problem(s)`, and `python3 gates.py &&
    python3 gates.py --selftest` matching `gates: 0 problem(s)` and
    `selftest: ok`, all green on a clean checkout, with `git status` showing
    no unregenerated payload and no stray file.
- [ ] **C4** OPTIONAL — the daily routine runs the pass — size:S, blocked by: C3
  - Accept: **This item is declinable and blocks nothing.**
    `architecture.md`'s own assumption says the design works on the
    documented command alone and the trigger degrades without taking the tool
    with it. If taken: `docs/factory/improvement-routine.md` §2 Orient gains
    one read-only step running `python3 one_owner.py`, whose findings become
    report material and, when a *new* group appears, a `docs/backlog.md` seed
    proposal under Proposals. It goes in §2 and **not** §3 Health sweep,
    stated in the step itself: §3 classifies main green or red, and a
    one-owner finding must never colour main red — the same bar that
    disqualified the detector home. The routine is tuned by PR and never by
    itself (`CLAUDE.md`), which is what makes this edit sanctioned. `python3
    lint.py` green after the edit; `docs/` is not mirrored, so no manifest
    regeneration.

## Design gaps found

**One gap routes back to Architect. Two omissions were absorbed, and both are
named here with the authority that decided them.**

### Gap 1 — routed back: the day-one annotation lands in a mirrored file

`architecture.md` (*Components → `one_owner.py`*) states the tool "joins no
`factory_init.MIRRORS` entry, and touches no checksum", and that
"`update-manifest` is not required by this run *unless* the routine-doc
trigger is declined and a Makefile target is chosen instead". Both sentences
are about the tool, and both are true of the tool.

But the design's named day-one customer is `budget_guard.git_runner` /
`dashboard.git_runner`, and **`budget_guard.py` IS a `factory_init.MIRRORS`
entry** (`factory_init.py:142`), with a byte-identical payload twin at
`factory/templates/tools/factory/budget_guard.py` (verified with `diff -q` at
HEAD `7650052`). A `# one-owner:` comment above `budget_guard.py:111`
therefore changes a mirrored root file: the payload twin must be regenerated,
`python3 factory_init.py update-manifest` must run in the same commit, and
detector E plus `tests/test_factory_init.py`'s payload-vs-root pin both fire
otherwise. `dashboard.py` is not mirrored, so the other half of the pair is
free.

The consequence is not only churn. The marker ships into every stamped
product repo's `tools/factory/budget_guard.py`, where it cites an ADR
number that repo does not have and names `dashboard.git_runner`, which is not
mirrored and does not exist there. That is the same objection the design used
to reject the detector home — "impose this repo's seam convention on product
source that never agreed to it" — in miniature. It does not turn a stamped
repo red: `gates._scannable_files` is `docs/**/*.md` plus `CONTEXT.md`, so
detectors A, C and D never read a `.py` comment, verified at HEAD. But the
design asserted no checksum is touched, and one is.

**Why this is not Decompose's to absorb.** There is a real choice with real
alternatives — keep the annotation where the design put it and accept both
the regeneration and a marker in shipped payload; move the day-one customer
to a pair that is entirely root-only; or state that markers in mirrored files
are fine, and say why the detector-home objection does not apply to them.
`B4` is written above so the work is visible, and it is blocked on this
answer. Nothing else in the run is blocked: B1, B2 and B3 land the mechanism,
its rules and its ADR regardless, and milestone C does not depend on B4.

> **Answered 2026-08-23 — option 1, with the reason recorded as a rule.**
> The annotation stays where the design put it: every member of the live
> `runner('git')` group is marked, `budget_guard.py` included, and
> `python3 factory_init.py update-manifest` runs in that same commit with
> the regenerated payload twin and manifest. `B4`'s Accept criterion
> already carries this branch verbatim and needs no rewrite; only the
> blocking clause changed. The 0061 record additionally states *why* a
> marker in a mirrored file is acceptable — an inert comment no
> stamped-repo tooling reads, so the detector-home objection does not
> transfer — which makes `B3` carry one more paragraph than the
> architecture's proposed text. `architecture.md` records the full
> resolution and the two root-only alternatives that were measured and
> rejected.

### Gap 2 — absorbed: the front door has no verb for the new tool

`architecture.md` never mentions `factory.py`. `tests/test_factory_cli.py`
derives `factory.VERBS` from a mechanical scan of root modules carrying an
`if __name__ == "__main__":` guard, and its own docstring says so: "a new `if
__name__ == \"__main__\":` guard breaks this test until the tool gets its
verb". `one_owner.py` has `main(argv)` and a documented `python3
one_owner.py` command, so the guard exists and the verb is forced. Nothing is
chosen: "the verb IS the module's name" (`one-owner`), and the convention
column is derived from the signature (`argv`). A5 carries it. `factory.py` is
not a MIRRORS entry, so it adds no manifest churn, and `factory.index()`
reads each module's docstring first line, which is why A1 requires one.

### Gap 3 — absorbed: the `runner('git')` group is a triple, not the pair the design names

`source_files(root, run=git_runner)` binds `runner("git")` at module level in
`one_owner.py`, and `same-value` identity is `ast.unparse(value)`, so the
tool's own binding joins `budget_guard.git_runner` and
`dashboard.git_runner`. `architecture.md`'s ten-finding table was measured
before the tool existed and calls that group a pair. The group-wide coverage
rule already handles a triple — every member marked, every member named by
some other member's marker — so there is nothing to decide; A5 and B4 are
written over "every member the tool reports" rather than over a count copied
from the design.

## Notes

- **Milestone order.** A first, because nothing can be demonstrated until the
  pass runs and the fixture is found — that is the run's headline criterion
  and it is met at A5, before any carve-out exists. B second, because the
  carve-out only means anything once there is a finding to excuse. C last,
  because the historical fixtures pin exact strings through `check`, and the
  documented command should describe a tool that already behaves.
- **Thirteen items, six of which are the tool's five interfaces.** `groups`
  (A1), `fact_sites` (A2, A3 — split so each half is driven by the
  historical shape it exists to catch), `source_files` (A4), `markers` (B1),
  `check`/`main` (A5, B2). Every component in `architecture.md`'s
  *Components* section appears in some item: the tool (A1–A5, B1, B2), the
  marker convention (B1, B3, B4), the fixture suite (C1, C2) and the trigger
  (C3, C4).
- **Every `defect.md` success criterion has a home.** Check exists with a
  documented command and label-prefixed strings → A5, C3. Finds the fixture
  unaided → A5. Silent on recorded deliberate duplicates → A2 (the exact
  identity, for `_CHECKBOX`/`ROW`) and B4 (the marker, for the ADR-0037
  pair). A test that would have caught each of the three historical
  instances → C1 and C2, **as amended**: two caught, the third pinned as a
  known miss. Full battery green → C3, and every item before it. Manifest
  regeneration if a mirrored tool is touched → design gap 1 and B4, the only
  place the question arises. Test-ordering visible in history → the ordering
  rule above, served inside every item.
- **The exact bytes of a problem string are Implement's to settle, once.**
  `architecture.md` renders each string line-wrapped inside markdown prose;
  the emitted string is a single line. The first item that emits each shape
  fixes its bytes and its suite pins them, and no later item re-words one.
  An exact-string test that needs editing after the item that wrote it is
  the signal to revert, not to edit the test.
- **What this breakdown deliberately does NOT contain.** No item folds any of
  the eight true findings the tool prints on day one — `architecture.md`
  enumerates them so the classification is on the record, and routing them to
  `docs/backlog.md` is Operate's closing act, not Implement's. No item
  touches `DETECTORS`, detector `J`, `CHECKERS`, or any workflow; letter `K`
  stays unclaimed and the mid-flight `first-live-dispatch` work order
  that owns the J-roster disagreement is undisturbed. No item
  adds a `make one-owner` target — the root Makefile mirrors into the product
  Makefile and the tool is not in `factory_init._PRODUCT_TOOLS`. No item
  creates a baseline or suppressions file; a baseline is a roster with a
  worse name.
- **How this run dies, restated as a check on these rows.** The tool grows a
  third rule to reach `sweeps.reconcile_drift` and becomes the semantic
  comparison `defect.md`'s hazard 2 names — C2's pin exists so that limit is
  recorded rather than chased. Or the carve-out is skipped and the tool fires
  on a decision the repo already made — B4 is the item that proves it does
  not, which is why gap 1 needs an answer rather than a workaround. Or
  someone "tidies up" `plane_drift.issue_lifecycle` while they are in there,
  and the run loses the only live proof it has.
