---
stage: architect
run: maintenance:seen-before-partner
date: 2026-10-24
assumptions:
  - "prd.md is absent by protocol: this is a maintenance run with re-entry: architect, whose predecessor is defect.md (pipeline-protocol.md, Maintenance-run orientation). No ux: echo for the same reason; the only surface is CLI lines, unchanged."
  - "No live interview. Every question defect.md and autorun-brief.md left to Architect is settled from the code and from read-only experiments in a scratch clone, taking the recommended default each time. Not an Owner answer."
  - "DEVIATION FROM THE BRIEF, for the Owner to confirm: autorun-brief.md scope item 1 asks to fold a run into seen only once used (paired as a hit, or voted). Reproduced in a scratch clone, both literal readings are unsound: folding on use loses the lesson through the vote path (a hit run that downvotes before its partner exists is folded and skipped), and folding only a paired hit while leaving an unpaired hit unseen lets that run vote on lessons derived after it was first measured, so a second update over unchanged input changes the file (211 of 1,500 random update sequences). The design keeps seen = measured and instead changes who pairing skips (a seen hit run is skipped only when a seen clean partner also exists). It meets the brief's goal and its acceptance lines (update 1 over H, update 2 over H + C equals one update over both; a repeat is unchanged; clean-first still derives) and needs no on-disk change. If the Owner wants the literal fold rule, this stage's evidence is the case against it."
  - "Unverified lead settled by running it: _ballot and votes do not lose a vote the way pairing loses a lesson. A voter measured before any lesson of its kind exists, or in the update that derives the lesson, never votes on it; that is the exposure rule (a run cannot vote on a lesson it could not have read), identical under the old and the new design, and is left as it is."
  - "Migration: none, shape unchanged. An ADR-0116-era file loads as it is. It heals the defect's case (a seen hit run whose partner arrives after the upgrade). A hit run and a partner both already seen by the earlier rule stay unpaired: the trace is identical to a dropped lesson (two seen runs in no lesson's sources), so no cheap honest detection exists. Cheapest honest handling, taken: leave it, record it in the ADR Consequences, and give ADR-0116's recovery (delete the file and run update). `git ls-tree -r --name-only origin/main | grep decompose-lessons.jsonl` prints nothing at ec8159f and no such file exists in this working tree, so no real file is affected."
  - "Size: no effect. The header is written by the unchanged fold; MAX_LESSONS_BYTES stays 1 MiB. Measured 2026-10-24 over this clone's real history through decompose_signals: 42 runs, 103 entries, 4,383 bytes."
  - "ADR number: 0117 re-checked 2026-10-24 after a fetch: `git ls-tree --name-only origin/main docs/adr/` ends at 0116 (origin/main ec8159f); the one open PR, #1073, is docs-only."
  - "The ADR-0116 status line and the ADR index row carry the annotation `(the pairing skip rule; provisional)`, the same form ADR-0113 carries for ADR-0116. The brief says ADR-0117 supersedes the seen-equals-measured rule; because the design keeps that rule, the superseded part is ADR-0116's pairing-skip sentence."
---

# Architecture: a hit run seen before its clean partner still pairs

## Approach

`seen` stays exactly what ADR-0116 made it: one `<signal>:<run ref>` entry
per measured (signal, run), folded at the fold where the signal is measured.
Pairing changes who it skips. Today `fold` hands `pairs` the whole `seen`
set as `skip`, so a hit run measured before its clean partner exists is
skipped for ever. After the change `fold` hands `pairs` only the hit runs
that already had their chance: a hit run seen for a signal **and** with at
least one clean partner of its kind and label, measured for that signal,
that is also seen. A seen hit run with no seen partner is offered to
pairing again and pairs with the first clean run in record order, exactly as
an unseen one does.

Why the partner test is right. When the update that first measures a hit
run H runs, either a partner C exists (H pairs there, both become seen) or
none does (H becomes seen, no pair). A partner that arrives later is unseen
at the start of its first update, so H is not yet spent and pairs then. Once
H and any partner are both seen, H is spent: a lesson dropped at 0 cannot
come back from them, and a clean run that arrives later (even earlier in
record order) does not re-open the pair. The clean role needs nothing:
`pairs` already looks the partner up in the full record list, so a seen
clean run still partners (defect.md, case 2); this design keeps that
asymmetry and relies on it.

Three shapes were compared by running them, in a scratch clone at ec8159f,
over random update sequences (3 stages, 3 to 7 runs, both kinds, both
labels, counts 0 to 3, runs maturing at random stages, git faked, every run
treated):

- **(a) Fold on use** (paired as a hit, or voted; the brief's wording):
  loses the lesson through the vote path. A hit run that downvotes an
  existing lesson before its partner exists is folded by the vote and then
  skipped by pairing; reproduced (the later lesson is never derived).
- **(b) Fold every measured run except an unpaired hit run**: fixes the
  pairing loss, but the vote guard no longer covers an unpaired hit run, so
  any treated unpaired hit run downvotes every lesson derived after it, even
  one it could not have read. A second `update` over unchanged input then
  changes the file in 211 of 1,500 sequences, against 0 for the current
  code.
- **(c) Keep the fold, change the skip** (chosen): 0 sequences change the
  file on a second update, with and without votes; with votes off, the set
  of lesson ids after three incremental updates equals one update over the
  last records in all 3,000 sequences, where the current code differs in 105
  of 3,000; no lesson the current code derives is lost (3,000 sequences, 101
  gain one).

One module and its tests change; the one decision that outlives the commit
is what pairing skips, so it gets ADR-0117, superseding ADR-0116's pairing
sentence in part.

## Components

### Partner lookup (`_partners`, new, in `decompose_lessons.py`)

- Responsibility: the clean runs (count 0) of a kind and label on a signal,
  in record order. The one place the partner predicate lives; `pairs` takes
  its first element, as it takes the first today.
- Collaborators: Pair derivation, Spent hit runs.

### Spent hit runs (`_spent`, new)

- Responsibility: given the records and the `seen` set, the seen keys of the
  hit runs (count above 0, measurable) that are seen for a signal and have a
  partner (from `_partners`) that is also seen for it. This set is what
  `pairs` skips.
- Collaborators: Partner lookup, Fold.

### Pair derivation (`pairs`)

- Responsibility: unchanged except it reads its partner from `_partners`.
  Signature, `skip` meaning (keys it is given are skipped), the first-clean
  exemplar, and the no-partner-no-pair rule are unchanged, so its existing
  tests stand.
- Collaborators: Partner lookup.

### Fold (`fold`)

- Responsibility: `pairs(records, skip=_spent(records, set(seen)))` replaces
  `pairs(records, skip=set(seen))`. The returned `seen` is the input plus
  every measured key, unchanged (`_measured`). Votes, adds, edits and the
  drop at 0 are unchanged.
- Collaborators: Spent hit runs, Pair derivation, Voting.

### Voting (`votes`, `_ballot`) and File (`load`, `serialize`, `dump`)

- Responsibility: unchanged. Settled by running, not by assertion: the vote
  guard cannot lose a vote the way pairing lost a lesson (Decisions).

## Data model

Unchanged. Line 1 is `{"seen": [<signal>:<run ref>, ...]}`, sorted, one
entry per measured (signal, run); lesson lines are as ADR-0113 fixed them.
The meaning of an entry is unchanged too: that signal was measured for the
run when the fold ran, whatever its count.

What changes is what an entry does to a hit run: it no longer skips the run
for ever, only once the run has a seen partner. The table is what the skip
now is, per signal and role (the signal is the same for all three signals;
`replan` shown):

| seen state at the start of the update | role | skipped by pairing? |
|---|---|---|
| hit run unseen | hit | no (as before) |
| hit run seen, no seen clean run of its kind and label | hit | **no** (was yes; this is the fix) |
| hit run seen, a seen clean run of its kind and label exists | hit | yes (as before) |
| clean run, seen or not | clean | never consulted: a partner is looked up in the full record list |

Invariant owners: run records and labels belong to `decompose_signals`; the
entry grammar and `_hit_label` belong to `decompose_lessons`; the partner
predicate has one owner, `_partners`.

Idempotence, argued and run. After an `update` every measured hit run is
seen and every measured clean run is seen. The next `update` over the same
records finds each hit run spent if it has a partner (the partner is seen),
so it derives no pair; a hit run with no partner has none to pair with
either; the vote guard (`seen` and the lesson's `voted` list) is unchanged,
so no second vote. Run: 0 of 3,000 random sequences change the file on a
repeated update, with votes on and off.

## Interfaces & contracts

### `fold(lessons, seen, records, ballots)`

- Input and output: unchanged.
- Failure modes: unchanged (a lesson-operation problem abandons the whole
  fold and leaves the file untouched).
- New behaviour: a hit run seen without a seen partner pairs when a partner
  exists in `records`. Its lesson is ADDed (new id) or EDITed (known id whose
  sources grow); a lesson id dropped in the same fold is not re-added.

### `pairs(records, skip=())`, `_partners(...)`, `_spent(records, seen)`

- `pairs`: unchanged contract. `_partners(records, field, num, run_kind,
  label)` returns a list of records. `_spent(records, seen)` returns a set
  of seen keys. Both pure; no I/O, no git, no new import. Pinned: no new
  constant, no new output line, no new problem string, no change to
  `NO_PAIR`, `LABEL`, `MAX_LESSONS_BYTES` or any CLI text.

### File and `update`

- Unchanged. An ADR-0116-era file loads as it is. A lessons file is still
  not written when there is no lesson and no file (the first update over a
  hit run alone writes nothing, so the loss needs a ledger to exist; the
  defect's script keeps one with two maintenance runs).

### The Decompose skill

`skills/decompose/SKILL.md` reads lessons, not the header, and its
`seen`-header wording stays true. No skill edit, no `plugin.json` edit, no
release PR owed by this run (ADR-0095).

## Stack & dependencies

- Standard library only; no new import. The dual-membership pin stays 55.
  `decompose_lessons` stays root-only, read-only on git history, no network.

## Accepted behaviour changes (old rule against new rule)

Both rules were run over the inputs where they differ (the fuzz above, and
by hand for the named cases):

1. Hit run H seen, partner C arriving in a later update: old, no pair, the
   lesson never derived; new, the pair is derived in the update C arrives.
   This is the fix. 101 of 3,000 random sequences gained a lesson; none lost
   one.
2. H and C both seen: old and new skip H. A lesson dropped at 0 stays
   dropped. A clean run arriving later, even first in record order, does not
   re-open the pair (a seen partner exists).
3. Clean run seen before any hit exists: old and new derive the lesson when
   the hit arrives. Unchanged.
4. Votes: no change. The vote guard still reads `seen` (measured) and the
   lesson's `voted` list; sequences with votes on change a file only where
   the extra derived lessons are voted on in later updates, as for any
   lesson.
5. Header: byte-identical to what the old rule writes for the same records.
6. Sources of a lesson: when an earlier-in-record-order clean run arrives
   after the hit, the incremental lesson's sources are the hit and the clean
   run it first paired with, where one update over everything would pick the
   earlier clean run. That is the first-clean-in-record-order exemplar rule,
   unchanged; the lesson id set is the same. Sources differ from the
   single-update result in 111 of 3,000 sequences (226 under the current code).
7. A lesson dropped at 0 and then supported by a genuinely new hit run is
   ADDed again, in old and new alike (2 of 3,000 sequences in both).
8. An ADR-0116-era file: heals a seen hit run whose partner arrives later;
   does not heal a pair already both seen (Data model, assumptions).

Unchanged by design: vote order; early exposure (operational); the
first-clean exemplar; the exposure rule for votes.

## Decisions & alternatives

- **Change the pairing skip, keep `seen` = measured** over folding on use —
  folding on use loses the lesson through the vote path and, in the
  unpaired-hit variant, breaks the vote guard and idempotence (both
  reproduced). ADR-0117.
- **Decide the skip in `fold`, leave `pairs` alone** over teaching `pairs`
  about partners — `pairs` keeps its contract and its tests; one new helper
  decides what is skipped.
- **One partner predicate (`_partners`)** over a second copy in `_spent` —
  the partner rule would otherwise be stated twice and could drift.
- **No migration, no detection** over a header upgrade or a stranded-pair
  check — an entry does not say why it is there; a stranded pair and a
  dropped lesson leave the same trace.
- **Votes: unchanged** over a fix — no vote is lost that the voter could
  have read (below).
- **Not decided here:** vote order and early exposure (documented
  decisions, brief-binding).

The vote lead, settled by running it: V1, a clean treated voter measured
while no lesson of its kind exists, then the lesson derived in the next
update; V2, the voter measured in the same update that derives the lesson;
V3, the voter measured after the lesson exists. Old code and new code
agree on all three: V3 upvotes; V1 and V2 do not vote, because the run
could not have read a lesson derived after it. This is the exposure rule,
not a lost vote.

## ADRs

- ADR-0117 (provisional): a hit run seen before its clean partner still
  pairs when the partner arrives; the skip is decided from `seen` plus a
  seen partner, and `seen` itself is unchanged. Supersedes ADR-0116's
  pairing-skip sentence in part (ADR-0116's status line and the index row
  updated). Passes the three legs: hard to reverse (the persisted meaning
  of the header decides which lessons a ledger ever contains, and ADR-0113
  says a header change needs a superseding ADR), surprising without
  context (a reader expects seen-means-skipped, and expects the issue's
  fold-on-use fix, which fails), and a real trade-off (three rejected
  alternatives, two reproduced failures).

## Traceability

| Brief item | Where |
|---|---|
| Fold rule for hit and clean roles | Approach; Data model table; assumptions (deviation) |
| Symmetric case, asymmetry kept | Approach; Accepted behaviour changes 3 |
| Vote lead settled by running | Decisions & alternatives; assumptions |
| Second update idempotent, no double vote | Data model, Idempotence |
| On-disk shape, old file, stale entry | Data model; assumptions (migration) |
| Header size effect | assumptions (size) |
| New ADR, supersession, status and README | ADRs; ADR-0117 |
| Root-only, pin 55, no skill or plugin.json edit | Stack & dependencies; Interfaces |
