---
stage: capture
run: maintenance:one-fact-one-owner
date: 2026-08-23
re-entry: architect
origin:
  - "docs/backlog.md:19 — retyped-seam-grammar detector (from: maintenance:deepening-cli-seams)"
  - "docs/backlog.md:45 — one-fact-many-owners, with the measured 4-of-7 miss rate (from: maintenance:deepening-tool-seams)"
assumptions:
  - "Origin shape: the protocol names no form for a run seeded by two backlog seeds, so both are recorded as a YAML list of `docs/backlog.md:<line> — <gist> (from: <run-ref>)` entries. Both were claimed in place with the sanctioned suffix append."
  - "Ruled out: the brief records no investigated dead ends, so this brief takes the template's `none yet` default. The brief's `How this dies` failure modes are recorded under Notes as hazards NOT yet ruled out — they are predictions, not eliminations."
  - "Root-cause hypothesis: the brief states the condition (`Nothing mechanical checks it`) but never labels a root cause. This brief promotes that sentence to a hypothesis and labels it as one, per the capture skill's rule that a guess must not be dressed as a finding."
---

# Condition: nothing mechanical asks "is this fact stated twice?"

## Condition

This repo's stated bar is **one fact, one owner**. `CLAUDE.md` states it as
the shared-module rule ("A new shared module needs multiple real callers AND
observed divergence between their copies"). ADR-0037, ADR-0039, ADR-0040,
ADR-0056 and ADR-0060 are each one instance of a human enforcing it by hand,
after the fact.

**Nothing mechanical checks it.** The detector suite covers citations (A),
checksums (E), staleness (I) and label taxonomy (J/LABEL-WIRING); `lint.py`
covers skill and artifact grammar. Nothing asks whether a fact has acquired a
second owner. The only finder the class has is a human reading the tree
during a manual deepening review — and that finder now has a measured miss
rate of **4 of 7**.

**Target state.** Something mechanical answers "is this fact stated twice?"
and runs often enough to catch a duplicate in days rather than at the next
manual review. The ambition is deliberately bounded: seed 45 says *"the
mechanical form is cheap enough to be a pre-pass rather than a detector at
first."* The two mechanical forms the seeds name:

1. **Identical module-level bodies** — the same regex or constant defined in
   two modules (the `DONE_ROW` / `MERGED_ROW` shape).
2. **A module that imports a seam helper and also retypes it** — the
   `plane_drift` / `label_names` shape, and the `cli.report` epilogue shape
   from seed 19.

The run ends when a mechanical check exists, runs from a documented command,
finds the one live instance unaided, and stays silent on the recorded
deliberate duplicates.

## Reproduction / Evidence

Every fact below was **re-verified against the working tree at HEAD
`7650052`** on 2026-08-23 (`refactor(factory): one cross-plane drift rule,
one absence policy (#316)`). Corrections to the seeding brief are marked.

### The measured miss rate

The seeding deepening review was taken at `fbfa3c3` (2026-08-17). It
confirmed six candidates and its run fixed four. Three further instances of
the same class were **already in the tree at that same commit** and the
review did not surface them. `docs/fixes/deepening-tool-seams/retro.md:279-289`
records the count in its own words: *"the seeding review confirmed six
candidates, this run fixed four, and at least three more instances of the
same class were sitting in the same tree … the measured hit rate of the one
that seeded this run is 4 of 7."*

### The three missed instances

| Instance | Duplicate created | Closed |
|---|---|---|
| `knowledge_plane.DONE_ROW` byte-identical to `gates.MERGED_ROW` | `MERGED_ROW` `208ffdb` 2026-07-11 (#130); `DONE_ROW` `4333370` 2026-08-10 (#221) | ADR-0058, `7988962` 2026-08-22 (#312) |
| `sweeps.reconcile_drift` vs `dashboard._drift` | `_drift` `02de371` 2026-08-13 (#268) | ADR-0060, `7650052` 2026-08-22 (#316) |
| `sweeps.issue_lifecycle` retyping `cli.label_names` | `issue_lifecycle` `f38fbdd` 2026-08-10 (#204); `label_names` `622e2bf` 2026-08-10 (#247) — same day | **Still open.** ADR-0060 moved the copy into `plane_drift.issue_lifecycle` unchanged |

Every hash, date and PR number in that table verifies at HEAD:

```
$ git log -1 --format='%h %ad %s' --date=short <sha>
208ffdb 2026-07-11 feat(factory): WO-0008 detectors D (blueprint-drift), G (cost-ledger), I (staleness) (#130)
4333370 2026-08-10 feat(skills): work-queue — run several ready work orders in parallel (#221)
02de371 2026-08-13 feat(dashboard): WO-0021 — drift findings (#268)
f38fbdd 2026-08-10 feat(factory): wo:failed writer + cross-plane reconcile sweep (ADR-0045) (#204)
622e2bf 2026-08-10 refactor: land the 2026-08-05 architecture deepening — seams, renames, quick wins (wo-lbi) (#247)
7988962 2026-08-22 refactor(factory): one owner for the checked-row grammar (#312)
7650052 2026-08-22 refactor(factory): one cross-plane drift rule, one absence policy (#316)
fbfa3c3 2026-08-17 feat(factory): WO-0044 — assembler accepts subscription OAuth credential
```

The two closures also verify as closures, not claims: `git log -S` shows
`MERGED_ROW` and `DONE_ROW` each touched twice — created, then removed at
`7988962`; `dashboard._drift` created at `02de371` and removed at `7650052`.
At HEAD, `gates.MERGED_ROW` exists nowhere in the tracked tree, and
`tests/test_knowledge_plane.py:101-107` pins its absence.

### The live instance — this run's acceptance fixture

`plane_drift.issue_lifecycle` retypes the labels-array walk that
`cli.label_names` owns. Confirmed at HEAD, exactly as the brief describes:

- `plane_drift.py:28` — its **only** import is
  `from knowledge_plane import row_done, row_tracker_issue`. It does not
  import `cli`.
- `plane_drift.py:31` — `def issue_lifecycle(issue)`, whose body at
  `plane_drift.py:36-40` runs its own labels walk:

  ```python
  labels = issue.get("labels")
  names = [entry.get("name") for entry in labels
           if isinstance(entry, dict)] if isinstance(labels, list) else []
  return sorted(name for name in names
                if isinstance(name, str) and name.startswith("wo:"))
  ```

- `cli.py:376` — `def label_names(payload)`, whose docstring claims the fact
  outright: *"One deliberate strictness for every caller — the strictest all
  of them tolerate: an entry that is not an object, or whose name is not a
  non-empty string, contributes NO name."* The two walks genuinely differ:
  `label_names` drops a nameless label at extraction; `issue_lifecycle`
  admits `None` into `names` and filters it a line later. Same rule, two
  strictnesses, one of them undocumented.
- **Both of `plane_drift.py`'s callers import the seam and use it feet
  away**: `sweeps.py:63` imports `label_names` from `cli` and uses it at
  `sweeps.py:291`; `dashboard.py:46` imports it and uses it at
  `dashboard.py:181` and `dashboard.py:251`.

Every one of those line numbers is correct at HEAD; none had moved since the
brief was written.

The sharpest fact in this brief: **the refactor whose whole purpose was
collapsing a duplicated rule carried a different duplicated rule across with
it, and said so in its own ADR** (ADR-0060, provisional, 2026-08-22).

### The deliberate duplicates the check must not fire on

- `protocol.py:71` — `_CHECKBOX = re.compile(r"^\s*[-*+]\s+\[([ xX])\]", re.MULTILINE)`
- `knowledge_plane.py:76` — `ROW = re.compile(r"^\s*[-*+]\s+\[[ xX]\]\s")`

Near-identical bodies, deliberately two owners. ADR-0058 (provisional,
2026-08-22) states it: *"The three regexes genuinely differ: `ROW` matches
either box and requires trailing whitespace, `protocol._CHECKBOX` captures
the box contents and is deliberately factory-agnostic."* The tree carries
the same statement in place at `knowledge_plane.py:69` and `:74`.

Two further recorded carve-out rosters: ADR-0037 lists what deliberately did
**not** move to the seams; ADR-0056 lists what deliberately did not move to
`human_gates`.

### Corrections to the seeding brief

Three claims in `autorun-brief.md` are wrong or stale at HEAD. Downstream
stages should use the corrected versions here, not the brief's.

1. **"detector letters `A`–`L` are all in use, so `M` is the next free one"
   (brief, Scope §3) is false.** `gates.py:1100-1113`'s `DETECTORS` roster
   records `"J": (None, None, "unused")` and `"K": (None, None, "unused")`,
   and the comment above it at `gates.py:1097-1099` says so: *"J and K are
   unclaimed — the shared ai-tooling letter namespace assigns nothing to
   them, so a new detector takes the next free letter and adds its row
   here."* **`M` is not the next free letter.**
2. **The roster and the docstring disagree about `J`, and that disagreement
   is itself an instance of this run's class.** `gates.py:26` documents
   `J LABEL-WIRING` as a shipped detector; `check_label_wiring` exists at
   `gates.py:808`, is wired into `CHECKERS` at `gates.py:1116`, and the
   selftest names its problems `"J"` at `gates.py:1243`, `:1260` and `:1264`
   — while the roster and the closing docstring line at `gates.py:44-47`
   both say `J` is unclaimed. **This is already owned**: it is the payload of
   `WO-0039` ("gates.py J-roster agreement",
   `docs/features/first-live-dispatch/breakdown.md:31`), in the active
   `first-live-dispatch` feature run, which is mid-flight and blocked on
   operator-held secrets. It stays out of scope. The practical consequence
   for this run: **`K` is the only uncontested free letter**, and if the
   Architect chooses the detector route it must take `K` and not assume `J`
   is free or that `M` is next.
3. **ADR-0037's status is `amended by ADR-0039`, not `accepted`** (brief,
   Constraints). Its carve-out list is still the input to the carve-out
   question; only the brief's status label was stale.

Everything else in the brief verified unchanged, including the ADR statuses:
ADR-0039 `amended by ADR-0040 (roster further amended by ADR-0058)`,
ADR-0051 `accepted`, ADR-0056 / ADR-0058 / ADR-0060 `provisional`, and
"six of the last seven ADRs are provisional" (0054, 0056, 0057, 0058, 0059,
0060 provisional; only 0055 accepted).

## Root-cause hypothesis

**Hypothesis, not a finding.** The class is not caused by carelessness at the
moment of duplication — every instance was created by a competent change that
had a local reason. It is caused by there being **no re-check after the
fold**: a seam is created, its adopters are converted once by hand, and
nothing ever asks again whether a later module retyped the rule. Seed 19
states the same mechanism from the other side: *"post-fold adopters are never
re-checked."* Both surviving 2026-08-22 instances were created by changes
that landed *after* their seam already existed — `DONE_ROW` thirty days after
`MERGED_ROW`, `issue_lifecycle` the same day as `label_names` — so the gap is
in the re-check, not in the original fold.

A corollary hypothesis, and the reason the design question below is the crux:
**a carve-out roster decays by exactly the same mechanism.** ADR-0039's
roster was written correct on 2026-07-22 and was stale by 2026-08-22, which
is what ADR-0058 exists to record.

## The design question — Architect's to answer, not capture's

**Do not let any stage skip past this.** A checker for this class has a
false-positive problem the other detectors do not, because this repo has
*recorded, deliberate* duplicates. The canonical one is
`protocol._CHECKBOX` versus `knowledge_plane.ROW` — recorded as deliberate
by ADR-0039 and again by ADR-0058, and restated in the source at
`knowledge_plane.py:69`. ADR-0037 and ADR-0056 each carry a further list of
what deliberately did not move.

So the tool needs a way to say "this pair is deliberate, and here is the
ADR" — an annotation at the definition site, an allow-list file, a carve-out
roster in the tool, or something else. **Where that list lives, and what
stops IT from going stale, is the design question.** ADR-0039's own roster
went stale in exactly this way, so an unchecked carve-out list would
reproduce the very failure this run exists to fix. A tool that cries wolf on
decisions the repo already made gets ignored, which is worse than not having
the tool.

Capture does not pre-decide this, and neither did the brief. **Architect owns
the answer, and `architecture.md` must contain it explicitly.**

## Blast radius

- **Who suffers:** the operator and the dispatched factory agents. Coping
  today means a duplicate lives in the tree until someone runs a manual
  deepening review and happens to see it — measured, 4 times in 7.
- **What is affected:** internal tooling only, and CI if the check ships as a
  `gates.py` detector. No user-facing surface, no data, no external
  contract, no runtime behaviour of any shipped skill.
- **Since when:** the class has been live at least since 2026-07-11
  (`MERGED_ROW`). It is not slowing down: two instances needed emergency
  ADRs on 2026-08-22, four days after a run that was specifically hunting
  this class shipped, and a third is still open in a module created that same
  day.
- **Why now:** the factory is about to dispatch agents at these tools, and an
  agent reading a tree with two disagreeing owners of one rule picks one at
  random.
- **The risk this run itself carries:** a noisy check that gets ignored, or —
  worse — one that turns CI red on a deliberate carve-out.
- **Scale consequence:** small. Review and Ship scale to this blast radius;
  Verify does not scale away.

## Ruled out

- **None yet.** The brief records no investigated dead ends, and this stage
  investigated none — it re-verified evidence rather than trying fixes.
  Downstream stages should treat the hazards under Notes as *unruled-out
  predictions*, not as eliminations.

## Scope

**In scope:**

1. The mechanical check itself, in whichever of the two forms above the
   Architect stage justifies. One form is an acceptable first cut if the
   second is argued and deferred in `architecture.md`.
2. The carve-out mechanism for deliberate duplicates, per the design question.
3. Its home and its trigger: a `gates.py` detector, a standalone script, a
   Makefile target, or a review-time pre-pass. **Facts, not decisions:** a
   `gates.py` detector runs in CI on every push, must be exact-string tested,
   and needs near-zero false positives; a pre-pass carries a much lower bar
   because a human reads its output. If the detector route is chosen, the
   letter is `K` (see Correction 2 — not `M`, and not `J`).
4. **The acceptance fixture:** the tool must find `plane_drift.issue_lifecycle`
   retyping `cli.label_names` **without being told about it specifically**. A
   tool that cannot find the known-live instance is not done.

**Out of scope, and why — do not widen into these:**

- **Fixing `plane_drift.issue_lifecycle`.** It is this run's *fixture*, not
  its cleanup target. It is seeded separately (`docs/backlog.md:46`), and
  fixing it here would leave the tool with nothing live to prove itself
  against.
- **`row_done`'s missing `ROW.match` guard** (`docs/backlog.md:41`) — a
  behaviour change that moves what detector G counts as a merged work order.
  Its own decision, not a ride-along.
- **Provisional-ADR staleness** (`docs/backlog.md:47`) and **`label_sync.py`
  having no runner** (`docs/backlog.md:48`). Real, seeded, different runs.
- **Restructuring the `DETECTORS` roster, or the `J`-roster disagreement in
  Correction 2.** That is `WO-0039`'s payload in the active
  `first-live-dispatch` run, which is mid-flight and blocked on
  operator-held secrets — do not disturb its target. *Adding* a row to the
  roster is fine; changing how the roster works is not.
- Any change to `skills/**` prose, `evals/**`, or the pipeline protocol.
- Re-litigating any ADR named under the design question. They are the input
  to the carve-out list, not candidates for reopening.

## Success criteria

- The check exists, runs from a documented command, and its output is
  label-prefixed problem strings per the repo's contract.
- **It finds `plane_drift.issue_lifecycle` retyping `cli.label_names`**
  without being told about it specifically.
- **It stays silent on every recorded deliberate duplicate**, at minimum
  `protocol._CHECKBOX` versus `knowledge_plane.ROW`. Zero false positives on
  the tree at HEAD, or every exception is in the carve-out list with its ADR
  named.
- A test exists that would have caught each of the three historical instances
  in the evidence table — run against fixtures reproducing their shapes, not
  against the live tree, so the test does not decay as the tree is cleaned.
- The full battery is green: `python3 -m unittest discover tests`,
  `python3 lint.py` (matching `lint: 0 problem(s)`), `python3 gates.py &&
  python3 gates.py --selftest` (matching `gates: 0 problem(s)` and
  `selftest: ok`).
- If the check ships as a `gates.py` detector or a mirrored root tool,
  `python3 factory_init.py update-manifest` is run and committed in the same
  change, and detector E is green.
- The test-ordering rule is visible in the history: tests at the intended
  interface land before the implementation.

## Constraints and things already decided

- **Stdlib only.** Standalone Python 3 standard library, no third-party
  imports. Consequence: no AST-diffing library and no YAML parser; `ast`
  itself is stdlib and is available.
- **Problem-string contracts:** checkers return lists of label-prefixed
  problem strings; callers print and exit nonzero. Tests assert exact strings
  through public interfaces.
- **New shared module bar** (`CLAUDE.md`): multiple real callers AND observed
  divergence. Anticipated reuse does not qualify.
- **Mirrored-into-payload rule** (ADR-0060): a module is mirrored iff a
  payload tool imports it — not because it is shared. A new root tool that no
  payload tool imports stays root-only and joins no manifest.
- **Template mirroring is checksum-pinned.** Any edit under
  `factory/templates/**` or to a root file in `factory_init.MIRRORS` requires
  `python3 factory_init.py update-manifest`, committed with the change, or
  detector E fires.
- **Recorded decisions that touch this work, all live, none being reopened:**
  ADR-0037 (`amended by ADR-0039` — the seam modules and what deliberately
  did not move), ADR-0039 (`amended by ADR-0040 (roster further amended by
  ADR-0058)` — the checkbox-regex roster, and the record of how a roster goes
  stale), ADR-0051 (`accepted` — the report epilogue fold, whose adopters are
  seed 19's subject), ADR-0056 (`provisional` — `human_gates`), ADR-0058
  (`provisional` — two owners, not three), ADR-0060 (`provisional` — the
  drift rule and the mirrored-iff-imported rule). Six of the last seven ADRs
  are provisional; treat a provisional ADR as citable but unsettled, exactly
  as ADR-0060 had to.
- **Offer an ADR only** when a decision is hard to reverse, surprising
  without context, and the result of a real trade-off. The carve-out
  mechanism probably qualifies; the tool's existence probably does not.
- Match the surrounding style. Many small files; 200-400 lines typical.
- **No tracker interaction.** No issues created, imported or closed; work
  items carry no `(tracker: #N)` references. No `intake:` — this run was
  seeded from the backlog, not from a tracker issue.
- **User-facing surface: none.** Internal tooling only; maintenance runs skip
  PRD, so no `ux:` decision arises.
- **Release authorization: prepare and stop.** No release is authorized. The
  operator was asked and expressed no preference, and absent an explicit yes
  the default is prepare-and-stop. Ship writes `release.md` recording
  readiness and the exact steps, and executes **no externally visible
  action**: no branch push, no PR, no merge, no tag, no workflow dispatch.
  "Production" for this repo is `main`; there is no deploy step and the
  project has never tagged a release, so the recorded steps are a branch, a
  PR against main, a green battery, and a squash merge — recorded for the
  operator to execute, not executed.
- **Artifact-depth precedent:** `docs/fixes/deepening-tool-seams/`
  (2026-08-18), which is also the run that produced the sharper of this run's
  two seeds.

## Notes

- **Re-entry is `architect`** because this run adds a tool that does not
  exist and the design question above is real and unanswered. There is
  deliberately no inline checkbox breakdown here; the
  `architecture.md` + `breakdown.md` chain owns the work items.

- **Hazards, not ruled out — the brief's "how this dies", carried forward as
  design input:**
  1. The carve-out list is skipped and the tool fires on
     `protocol._CHECKBOX` on day one, so it gets disabled.
  2. The check is built so cleverly (AST equivalence, cross-module call
     analysis) that it costs more to maintain than the manual review it
     replaces.
  3. It ships as a detector with a bar it cannot meet and turns CI red on a
     false positive.

- **A concrete scanning hazard found while verifying, worth the Architect's
  attention.** `grep -rn "MERGED_ROW" --include="*.py" .` from the repo root
  at HEAD returns six hits in `.claude/worktrees/agent-*/gates.py` — three
  stale agent worktrees each holding a full, months-old copy of the repo,
  including `MERGED_ROW` definitions that the tracked tree deleted at
  `7988962`. Those paths are excluded via `.git/info/exclude:11`
  (`**/.claude/worktrees/`), which is a *local, uncommitted* exclude — so
  `git ls-files` does not see them but a naive `Path(root).rglob("*.py")`
  does. A file-walking check must derive its file list from git, or skip
  `.claude/`, `__pycache__/` and `factory/templates/` explicitly. Note the
  related, already-seeded precedent at `docs/backlog.md:37`, where
  `update-manifest`'s walk pinned gitignored `__pycache__` bytecode for
  exactly this reason.

- **`factory/templates/tools/factory/` is a deliberate byte-for-byte mirror
  of root tools** and will read as a wall of duplicates to any naive
  scanner — `cli.py`, `validator.py` and `gate_digest.py` all appear twice in
  a repo-root grep. It is checksum-pinned by design (detector E). Whatever
  the check is, the mirrored payload tree cannot be treated as a second owner
  of anything.

- **Both origin seeds are claimed** in `docs/backlog.md` (lines 19 and 45)
  with `(claimed: maintenance:one-fact-one-owner)` appended in place; the
  `(from: …)` origin markers were not rewritten, and no other line in that
  file was touched. `python3 lint.py` is green after the claim.
