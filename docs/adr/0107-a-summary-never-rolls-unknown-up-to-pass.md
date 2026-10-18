# A verification Summary never rolls a disclosed NOT RUN up into a pass

- Status: superseded in part by ADR-0108 (the naming clause; provisional)
- Date: 2026-10-17

Recorded by the `fail-closed-roll-up` feature run
(`docs/features/fail-closed-roll-up/`), unattended, so it is provisional.

## Context

Detector H makes every section of a `verification.md` that carries a
labelled verdict show its own fenced evidence or lead with a NOT-RUN
disclosure. That is the per-section half of an honest roll-up. The
other half is the `## Summary`: the line the Owner, Ship's pre-flight,
Review and the unattended routines actually read. No rule states, and
no gate checks, that a Summary may not read as a pass over a criterion
that disclosed NOT RUN, skipped or deferred.

On 2026-10-17 no tracked `verification.md` breaks that rule (the run's
`idea.md` counts all 77). Authors count their gaps by habit, and the
authors are now increasingly scheduled routines with no Owner reading
the whole file. So this is prevention, and the risk in prevention is a
rule over free prose that false-positives on honest Summaries or
teaches authors to reword past it.

## Decision

Unknown, unsupported, truncated and skipped never aggregate to pass.
`CONTEXT.md` owns the words (the four claim kinds and the rule);
`docs/pipeline-protocol.md` states the rule once and points there. The
verify template's Summary guidance and the review template's Verdict
guidance carry it. Detector H enforces the verification half:

- **Trigger.** Any section other than a `## Summary` holds a labelled
  verdict that `gates._is_disclosure` accepts. H's prose `not_run`
  flag does not trigger it: it fires on prose that discloses no
  criterion.
- **Satisfied by naming the kind.** At least one section titled
  exactly `Summary` (case-insensitive) carries, outside any fence, a
  word from the unknown vocabulary: H's disclosure heads read anywhere
  in the line (n/a, skipped, deferred, untested, unverified, pending,
  todo, tbd, not run / ran / verified / executed / checked / tested /
  attempted), plus `not yet`, `unknown`, `unmet` and `unproven`. Any
  kind satisfies any other: every disclosure head is the same claim
  kind, unknown. There is no separate test for "asserts an unqualified
  pass": a Summary that names the unknown kind is qualified by
  definition, and one that names nothing reads as a pass.
- **No Summary, no rule.** An artifact with no `## Summary` section has
  no roll-up line to judge.
- **Grandfathered by date.** The rule applies when the artifact's own
  frontmatter `date:` is on or after `ROLLUP_ADOPTED = "2026-10-17"`,
  this ADR's date. A missing date is not grandfathered (fail closed),
  the same convention as `COVERAGE_ADOPTED` (ADR-0072) and
  `CAPTURE_ADOPTED` (ADR-0073).
- **One problem per artifact**, at the Summary heading's line:
  `H: {rel}:{lineno} summary "{title}" neither counts nor names the {n}
  criterion section(s) disclosed as not run (first: "{criterion}", line
  {l}); unknown never rolls up to pass`.

## Rejected alternatives

- **Key the trigger on H's prose `not_run` flag.** It lights ten files
  on main whose "not run" text discloses no criterion.
- **Require a count (a number next to a disclosure word).** Two of the
  three honest Summaries on main count; the third names its kind in a
  sentence. A count rule would push authors toward a number, not toward
  honesty.
- **Require the same head word as the criterion** ("1 DEFERRED" does not
  satisfy a `SKIPPED` criterion). It splits one claim kind into
  synonyms and fails honest Summaries that name the kind in their own
  words.
- **Also scan the Summary for pass words** ("all criteria pass") to
  judge an unqualified pass. A second free-prose grammar, with its own
  false positives, that adds nothing once naming the kind is required.
- **Disclosure vocabulary only, without `not yet` / `unknown` /
  `unmet` / `unproven`.** It fails the honest
  `docs/fixes/toolsmith-mine-pr-permissions/verification.md`, whose
  Summary reads "2 NOT YET VERIFIABLE".
- **A cutoff that Ship sets at merge.** A constant that moves after
  review is a constant review never saw; the ADR's own date is the
  precedent ADR-0072 set.
- **Grandfather a missing date.** Omitting the date would dodge the
  rule.

## Consequences

- No shipped artifact is rewritten, and main's tree stays at 0 problems
  (prototyped over all 77 files, with and without the cutoff).
- A Summary can satisfy the rule by negation ("nothing was skipped").
  The rule is a floor that catches the silent case; the template
  carries the intent. A dodge seen in a real artifact is a reason for a
  new ADR, not a rewrite of this one.
- A verdict that asserts PASS with a not-run hedge appended is a claim,
  not a disclosure, and stays out of reach: changing that would change
  H's per-section rule.
- `review.md` gets the rule through its template only; nothing gates it.
- `gates.py` ships into stamped repos (`factory_init.MIRRORS`), so the
  rule reaches them on their next update. Their existing artifacts are
  dated before the cutoff and stay silent; a dateless one is judged.

## Amendment (2026-10-17)

The run's review found two gaps; the Owner decided live on 2026-10-17 to
fix both before Ship.

- **Grandfathered only by an ISO date.** The raw-string compare let a
  quoted (`date: "2026-10-20"`), empty (`date:`) or non-ISO
  (`date: 20/10/2026`) value sort before the cutoff and switch the rule
  off, so "omitting the date cannot dodge the rule" was false for an
  empty `date:`. The value is now stripped of surrounding quotes and
  whitespace and a datetime is read by its date part; only a
  `YYYY-MM-DD` value before `ROLLUP_ADOPTED` is grandfathered, and
  anything else is judged (fail closed). Detectors O and M keep their
  compare; the same shape there is a `docs/backlog.md` seed.
- **The vocabulary widened on evidence.** Summary-only words that can
  only mean not examined: `not applicable`, `not_run` / `notrun`,
  `unverifiable`, `unexercised`, `not be(en) run`, and a contracted
  `n't (been) run`. A hyphen or slash may now follow a word
  ("skipped-by-design", "deferred/blocked"). `outstanding`, `blocked`
  and `skips` were considered and rejected as common in incidental
  prose (the run's `breakdown.md` Notes give each reason). The heads
  shared with H's verdict regex are unchanged.

Amended 2026-10-17 (maintenance run a-quoted-date-dodges-the-cutoff): the
seed above is done. Detectors O and M no longer keep their compare; H, O
and M all grandfather through one private `gates._grandfathered(date,
cutoff)`, and `ROLLUP_ISO_DATE` is renamed `FRONTMATTER_ISO_DATE`, with
that helper as its only user.
