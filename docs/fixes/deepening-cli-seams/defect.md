---
stage: capture
run: maintenance:deepening-cli-seams
date: 2026-08-13
re-entry: architect
---

# Condition: four modules whose interfaces cost about what their implementations do

## Condition

A deepening review of this repo at commit 57635f6 (2026-08-11) walked four
candidates and confirmed each against real call sites rather than a feeling
of friction. The degradation is not breakage; it is interface cost —
callers learning facts a module should own:

1. **The report seam is unfinished.** ADR-0051 folded ten tools onto
   `cli.report`; two mirrored tools retype the epilogue in four places, one
   of them behind a name collision with the seam itself.
2. **The front door routes nothing.** `factory.py` keeps a 14-verb table by
   hand while the Makefile, the workflows and the docs all still invoke
   tools by filename.
3. **gh's silence has five readers.** Five call sites each reassemble the
   same three failure modes, and two sites carrying the same hazard decided
   it differently.
4. **`protocol.py` serves two families.** The factory payload uses 1 of its
   15 names; every stamped repo carries ~250 lines of pipeline taxonomy no
   tool there can call.

**Target state that ends this run:** the report seam has one owner of the
summary line and the exit code; `factory.py` has one decided shape, recorded
as a decision rather than left in the middle; the truncation policy no
longer disagrees between callers; and candidates 3 and 4 have either a
recorded design answer or a recorded, reasoned deferral. Items 1 and 3 are
already landed (see `breakdown.md`); 2 and 4 are what remain.

## Reproduction / Evidence

Enumerated, not inferred — every count below came from walking the sites.

**Seam (candidate 1).** Four retyped epilogues: `work_queue.py` on its
config-failure leg and its tail, `budget_guard.py` on its `record` and
`record-run` legs. `work_queue.py:191` defined its own `def report(batch,
deferred, spent, wip)`, so the file imported five `cli` names and not that
one. Both files are `factory_init.MIRRORS` entries, and `work_queue.main`
had **zero** test callers. Ordering matters and was checked with
`git merge-base --is-ancestor`: both files landed 2026-08-10 (#221, #245),
hours *before* the fold shipped (#247) — a missed sweep, not a fork after a
decision.

**Front door (candidate 2).** `factory.py`, 91 lines, landed 2026-08-10
(#246). Callers walked: Makefile 0 (13 targets invoke tools by filename),
workflows 0, docs 0, tests 1 file. `tests/test_factory_cli.py:27–36`
derives the verb set mechanically from the root's `__main__` guards; the
module restates it by hand. `tests/test_factory_cli.py:53` handles a third
calling convention (`"argv0"`) that no table row uses.

**gh's silence (candidate 3).** Five sites: `label_sync.py:99–113`,
`gate_digest.py:294–304`, `sweeps.py:328–348`, `sweeps.py:449–487`,
`work_queue.py:162–179`. The comment "gh truncates a windowed listing
silently; the window size is declared once…" appears verbatim at
`label_sync.py:92` and `gate_digest.py:167`.

**A real defect inside candidate 3, since fixed.** `sweeps.live_issues`
refuses to report on a truncated listing because absence reads as a
finding; `work_queue` carried the identical hazard and warned instead.
Reproduction: a full 100-entry ready listing plus a breakdown row whose
mirrored issue sits past the window makes the tool print
`no open issue #999 carries wo:ready-for-agent — the owner applies that
label…` — inventing drift, and sending the owner to apply a label the issue
may already carry — in the same output as its own truncation warning. That
reproduction is now the regression test
(`tests/test_work_queue.py`, `TestMain`,
`test_an_untrusted_listing_defers_no_row_for_a_reason_it_cannot_know`).

**Two families (candidate 4).** Payload consumers in full:
`tools/factory/gates.py:73` and `tools/factory/assembler.py:43`, each
importing exactly `read_frontmatter`. Plugin-side: `lint.py` (6 names),
`trigger_eval.py` (3 names). `is_maintenance_run` has zero callers
anywhere.

## Root-cause hypothesis

**Hypothesis, not a finding:** the repo's shipping cadence outruns its own
sweeps. ADR-0051's fold swept the adopters that existed at sweep time, and
two more landed the same day; nothing re-checks adopters afterward. The
detector suite covers citation, drift, staleness and payload checksums, but
nothing detects "a tool retypes a seam's grammar" — the seam is a
convention held by review, and review is what missed it.

A second hypothesis for candidate 2: `factory.py` is three days old and its
non-adoption may simply be pending rather than decided. The review flagged
this explicitly and it is why B1 is a decision item, not a refactor.

## Blast radius

- **Shipped, not just internal.** `work_queue.py` and `budget_guard.py` are
  mirrored into the factory payload, so every stamped product repo carries
  both — including, until this run, a `work_queue.main` with no test over
  its CLI at all. Since 2026-08-10.
- **The invented-drift defect was latent, not observed.** It needs a
  tracker with at least 100 open ready-labelled issues to bite; this repo
  has far fewer, and no incident was reported. It would have misled an
  operator on a larger tracker, silently.
- **Candidate 2 affects nobody yet** — zero non-test callers, three days
  old, no dependents on either answer.
- **Candidate 4 is carrying cost, not breakage:** ~250 unreachable lines
  per stamped repo, and it is the stated blocker on ADR-0046's deferred
  identity map.

**Scale: small.** Review and Ship scale down accordingly. Verify does not —
the regression test above is the reason.

## Ruled out

Dead ends the review walked and closed, with the reason each is closed —
none of these should be re-investigated without new evidence.

- **The harness registry's home** (`charter_replay` importing `HARNESSES`
  from `trigger_eval`). ADR-0053 decided this deliberately: the registry's
  entries close over eval-plane detectors, and `cli` is mirrored into the
  payload so it must not import eval tooling. Reopening needs a third
  consumer or an observed drift.
- **Three `design-system.md` copies across the diagram skills.** Measured
  rather than assumed: only 9–28 identical lines between copies, describing
  genuinely different visual languages. ADR-0008 forbids cross-skill file
  sharing and `lint.check_skill_assets` enforces it. Not twins.
- **Four diagram skills with adjacent descriptions.** Each description
  disambiguates the other three, which is the right shape — and no
  measurement exists either way: the newest results snapshot predates two
  of the four skills, so the routing eval has never run with all four
  installed. That is an eval-freshness fact, not a deepening candidate.
- **`cli.py` as five vocabularies under one name.** Six of thirteen
  importers rename its exports at the door, which is a fair signal the
  names do not fit their callers — but each function is individually deep,
  five accepted ADRs put them there on purpose, and no caller reported
  friction. A naming observation, not a demonstrated cost.
- **The `--selftest` / unittest duplication in `gates.py`.** Two test
  surfaces over the same detectors, but the selftest travels with the
  payload into repos that get no `tests/` directory. It earns its keep.
- **The workflow-brain `main()` triple** (assembler, cost_report,
  gate_digest). Three byte-identical mains with no observed divergence does
  not clear this repo's shared-module bar, and ADR-0051 already carved the
  usage epilogue out by name.

## Notes

- **This brief is a backfill, written 2026-08-13 at the router's
  direction.** The run was entered at decompose on 2026-08-12 under a
  logged soft gate; `breakdown.md`'s `assumptions:` records the same gap
  from the other side. With this file present the router reads the run's
  progress from the breakdown's checkboxes instead of orienting back to
  capture.
- **Capture interviews; this one did not.** Every question the stage asks
  was already answered on the record — the review walked and enumerated the
  evidence, and the breakdown settled the scope. The one thing not sourced
  from evidence is the *target state* above: it is my reading of what would
  end this run, and it is the sentence to correct if it is wrong.
- **Variant.** This is a condition brief (degradation) that turned out to
  contain one behavioral defect, recorded above with its reproduction. The
  filename stays `defect.md` per the protocol.
- **Re-entry is architect** because two of the four candidates are
  decisions, not refactors: what `factory.py` is for, and whether a
  mirrored twin may pin a root-to-root pair. Work items therefore live in
  `architecture.md` and `breakdown.md`, not here.
