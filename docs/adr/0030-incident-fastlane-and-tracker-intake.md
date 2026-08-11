# Incident fast lane and tracker intake

- Status: accepted (Decision 2, 2026-08-10; Decision 1 remains provisional)
- Date: 2026-07-05

The maintenance run (ADR-0025) closed the on-ramp gap for defects, but two
halves of the bug loop are still missing. First, capture is a deliberate
sit-down interview — the wrong shape for a live production incident, where
nobody can answer five questions while the site is down. Second, the
issue-tracker bridge (ADR-0026) is one-way out: the pipeline can emit
issues, but a bug filed in the tracker can never trigger a run. This ADR
proposes both halves as two decisions. They compose: an incident often
arrives as a tracker issue, and a hotfix run may be seeded from an intake
issue. This is a design spike deliverable (issue #95); both decisions are
provisional pending human acceptance, and nothing in skills or the
protocol changes until then.

## Decision 1: a hotfix variant of the maintenance run

### Context

Capture's contract is "the knowledge is in the user's head … this skill
interviews — it does not draft," one question at a time, covering
reproduction, hypothesis, blast radius, and ruled-out dead ends before any
work starts. During a live incident that order is exactly backwards: the
valuable minutes belong to mitigation, and the interview's answers are
better *after* the fire is out anyway (the mitigation itself is evidence).
But abandoning the pipeline during an incident loses the artifact trail
precisely when the stakes are highest, and ADR-0025's invariant — "Verify
is never skippable in a maintenance run; the regression test is the
point" — is most at risk exactly when people are tempted to skip it.

### Decision (recommended, provisional)

A **hotfix variant** of the maintenance run — not a fourth run scale.
Same directory (`docs/fixes/<slug>/`), same seed artifact (`defect.md`),
same orientation table; the variant only reorders capture: **mitigate
first, capture the brief after**.

**The Verify invariant survives; only its timing moves.** In a normal
maintenance run Verify sits between Implement and Review. In a hotfix
run the mitigation may ship before `verification.md` exists — that is the
point of the fast lane. Exactly when the regression test becomes due:
**the moment the mitigation is deployed.** Concretely: the mitigation
record (below) is written with `regression-test: pending` at deploy time;
the regression test is the first work item of the post-mitigation phase;
and the run can never complete — orientation keeps routing to Verify, and
`retro.md` may not be written — until `verification.md` exists. Ship of
the mitigation may precede Verify; closure of the run may not.

**Capture-mode sketch.** In hotfix mode, capture's process reorders as:

1. **Stub the run (seconds, not minutes).** Agree the slug, write a stub
   `defect.md` with protocol frontmatter plus `variant: hotfix` and
   `re-entry: implement`, and only two content fields: the observed
   failure (one line) and blast radius (one line — it scopes the
   mitigation). No hypothesis, no ruled-out, no full interview.
2. **Mitigate.** Hand off to Implement immediately; it works from the
   stub. Implement's soft gate does not fire — the stub *is* the
   predecessor artifact.
3. **Record the mitigation.** When the mitigation lands, a **mitigation
   record** goes into `defect.md` frontmatter:

   ```yaml
   variant: hotfix
   re-entry: implement
   mitigation:
     applied: 2026-07-05T14:32Z
     change: <commit / PR reference>
     regression-test: pending   # replaced by the test reference at Verify
   ```

   `regression-test: pending` is the visible debt: a greppable,
   orientation-visible marker that Verify is still owed.
4. **Re-enter capture (the post-fire interview).** After the fire is out,
   capture runs its normal interview — observed vs expected, reproduction
   evidence, root-cause hypothesis (labelled a hypothesis), full blast
   radius, ruled-out dead ends — and backfills the stub into a full brief.
   The interview may revise `re-entry` to `architect` if the *durable*
   fix (as opposed to the mitigation) is design-touching.
5. **Verify.** The regression test is written and `verification.md`
   produced; `regression-test: pending` is replaced with the test
   reference. Review and Ship then scale to the recorded blast radius as
   usual (ADR-0025).

### Alternatives considered

- **A fourth run scale ("incident run").** Rejected: it would duplicate
  the maintenance shape ADR-0025 just generalized. A variant flag on the
  existing scale models the difference — reordered capture, deferred
  Verify timing — with no new orientation table.
- **No run during the incident; backfill via soft gating afterwards.**
  Rejected: soft gating handles a *missing* predecessor, but here there
  would be no run directory at all while the highest-stakes work happens —
  no slug, no artifact trail, and Implement's soft gate prompting for a
  backfill interview mid-fire is the exact failure this variant exists to
  avoid.
- **Make Verify optional for hotfixes.** Rejected outright: it breaks the
  core invariant. A mitigation without a regression test is how the same
  incident recurs; deferral is acceptable, waiver is not.
- **Agent drafts the brief from logs in parallel while the user
  mitigates.** Rejected: capture interviews, it does not draft
  (ADR-0011); a brief drafted from logs presents guesses as findings —
  precisely the "hypothesis dressed as root cause" failure capture's
  rules warn against.

### Open questions (each with a recommended answer)

1. *Is a hotfix always `re-entry: implement`?* — Recommended: the stub
   always starts as `implement` (a mitigation is by definition a scoped
   change); the post-fire interview may revise to `architect` for the
   durable fix.
2. *Does the mitigation deploy go through Ship?* — Recommended: no. The
   emergency deploy is captured in the mitigation record; `release.md` is
   still written when the run closes and references it. Ship-the-stage
   covers the durable fix at blast-radius scale.
3. *Should lint or orientation escalate a stale `regression-test:
   pending` (e.g. older than N days)?* — Recommended: no timer in the
   protocol; the run simply cannot complete, and the retro loop is the
   place recurring "pending debt" surfaces. Revisit if dogfooding shows
   pending markers going stale silently.
4. *Does the hotfix variant apply to condition briefs?* — Recommended:
   no. A refactor or upgrade is never a live fire; the variant is for
   defect briefs only.

### Consequences

- The protocol's maintenance-run section gains the `variant: hotfix`
  frontmatter field, the mitigation-record shape, and the reworded Verify
  rule ("never skippable; in a hotfix run it falls due the moment the
  mitigation is deployed, and the run cannot complete without it").
- Capture gains a second mode, which is real complexity in a skill whose
  value is its discipline; the mode must be entered only on an explicit
  live-incident signal, never as a default shortcut around the interview.
- A stub brief is a weaker seed for downstream scale decisions until the
  post-fire interview backfills it — acceptable, because Review and Ship
  happen after backfill anyway.

## Decision 2: tracker intake — issue-to-defect seeding

### Context

ADR-0026 made the tracker bridge an opt-in one-way mirror: import happens
only at run seeding into a *breakdown* (existing issues become work items),
export at Decompose, close at Implement item boundaries. A bug filed in
the tracker therefore cannot *start* anything: the pipeline can be
mirrored into a tracker but never driven from one, and a defect reported
while no session was open waits invisible. The tempting fixes — a
background watcher, or letting orientation list open bugs — are exactly
what ADR-0026 rejected: a second source of truth and broken
resume-after-close whenever the tracker is unreachable.

### Decision (recommended, provisional)

An **intake convention** that turns a designated tracker issue into a
defect-brief seed for a maintenance run. This **refines ADR-0026 — it
does not supersede it**: import-at-run-seeding already exists in the
bridge; intake extends the same allowance from breakdown seeding to
defect-brief seeding. Every ADR-0026 invariant stands: opt-in, one-way,
sync only at stage boundaries, no background sync, no webhooks, and
**orientation never reads tracker state** — seeding is not orientation.
The tracker read happens inside capture, at seeding time, at the user's
explicit request, and never again for the life of the run.

**What marks an issue as intake:** a designated **intake marker** — by
convention a tracker label named `pipeline-intake` (the protocol names
the convention generically; the concrete label and tracker CLI stay in
packaging-facing text, preserving ADR-0026's harness neutrality). Two
entry paths, both user-initiated inside capture: the user names an issue
directly ("capture #123"), or asks capture to list intake-marked issues
and picks one. Nothing polls; an unclaimed intake issue just waits.

**What the seeding step copies vs references:**

- **Copied** (into `defect.md`, becoming the state per ADR-0004): the
  issue title as the working title, the filed date, and the issue body's
  observed-behavior and reproduction content — verbatim quotes are fine —
  as *interview raw material*. Copied text pre-answers what it can;
  capture still interviews for the rest (hypothesis, blast radius,
  ruled-out). Intake seeds the interview; it does not replace it.
- **Referenced, never re-read:** the issue itself, recorded in `defect.md`
  frontmatter as `intake: #123` (the tracker's own notation, same
  reference grammar as work-item mirroring). Comments and attachments not
  copied into the brief are reachable through the reference for humans,
  but no skill reads them after seeding. From that moment the tracker
  copy is a mirror again: updates flow one way, out.
- **Close leg:** the intake issue closes when the run's fix ships —
  `release.md` exists — with a closing comment referencing the run
  directory. "Closed" on the tracker should mean "fixed in a release,"
  not "a run started."

### Alternatives considered

- **Background watcher / webhook auto-seeding runs from labeled issues.**
  Rejected: ADR-0026's no-background-sync stance stands under every
  option, and a run seeded with nobody present has no interviewee —
  capture interviews, so unattended seeding produces exactly the drafted-
  not-interviewed brief the pipeline refuses elsewhere.
- **Orientation lists open intake issues** (so `/next` could say "3
  intake bugs waiting"). Rejected: this is literally "orientation reads
  tracker state" — a second source of truth, broken resume-after-close
  when the tracker is unreachable, ADR-0004 weakened. If accepted, this
  path would require superseding ADR-0026; the recommendation is not to.
- **Two-way sync — keep the issue body updated as the brief evolves.**
  Rejected: the mirror becomes bidirectional, invites conflicts, and
  turns every stage boundary into a sync point. One-way out, plus the
  single close event, is the whole contract.
- **Copy the entire issue thread into `defect.md`.** Rejected: the brief
  is an interview product, not a dump. Downstream stages scale to what
  the brief records; a raw thread buries the blast radius under noise.
  Copy selectively, reference the rest.

### Open questions (each with a recommended answer)

1. *What is the intake marker, concretely?* — Recommended: a label; the
   protocol says "a designated intake marker," and packaging for the
   GitHub-based harnesses names `pipeline-intake`. A title prefix was
   considered and rejected as tracker-search-hostile.
2. *When does the intake issue close?* — Recommended: at Ship
   (`release.md` exists). Closing at Verify was considered (the
   regression test proves the fix) but the tracker audience cares about
   the fix being *live*. If the run is abandoned, the issue is un-marked,
   never silently closed.
3. *Can one run intake multiple issues (duplicates of one defect)?* —
   Recommended: yes — one primary `intake:` reference plus an
   `intake-duplicates:` list in frontmatter; all close together at Ship.
4. *Do intake-marked feature requests seed runs too?* — Recommended: no.
   A missing capability is a feature, not a defect (capture's standing
   rule); capture routes such an issue to the `idea` skill and leaves it
   open. Whether Idea gains a symmetric intake is a separate future ADR.
5. *Does intake compose with the hotfix variant?* — Recommended: yes,
   trivially: the stub brief carries `intake: #123` from the start and
   the body content is backfilled at the post-fire interview along with
   everything else.

### Consequences

- The protocol's tracker-mirror section gains the intake conventions: the
  intake marker, the `intake:` frontmatter field, the copy-vs-reference
  rule, and the close-at-Ship leg. Capture gains an optional intake step.
- The bridge stays opt-in and one-way; the tracker becomes an *entry
  point* without becoming a state store. On a bare install without a
  tracker, nothing changes.
- ADR-0026's status line is untouched — this ADR refines it. If the
  human decision instead prefers orientation-visible intake, that choice
  must be recorded as an explicit supersession of ADR-0026, not an edit.

Refines [ADR-0025](0025-maintenance-run-scale.md) (adds the hotfix
variant to the maintenance scale) and
[ADR-0026](0026-tracker-mirror-one-way.md) (extends import-at-seeding to
defect briefs). Supersedes nothing.
