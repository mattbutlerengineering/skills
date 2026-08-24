# Both lifecycle legs treat an uncited PR the same way

- Status: amended by ADR-0062
- Date: 2026-08-22

The work-order lifecycle has two label-writing legs, and until now they
disagreed about what a PR citing no work order means.

`needs-review-label` runs on PR open with `--uncited skip`: a body naming
no work order at all is a silent no-op, because human housekeeping PRs
are normal traffic. `merged-label` runs on merge with the strict default:
the same body is `V: PR body cites no work-order id`, and the job fails.

Nothing recorded that asymmetry as a decision. It lived in
`run_lifecycle`'s docstring and in one test
(`test_the_merged_leg_stays_strict_by_default`), whose stated reason was
that the merged leg *mutates* an issue and only a resolved citation says
which one. That reason is sound for a **malformed** citation — a body
that names a work order which resolves to none — but the skip was never
about that case. The skip applies only when the body names no work order
at all, and then nothing resolves and nothing is mutated.

The two legs are not merely inconsistent; for a PR that implements no
work order they are contradictory, and there is no body that satisfies
both:

| PR body | `needs-review-label` | `merged-label` |
|---|---|---|
| names a work-order id | fails — cites a WO it does not close | fails |
| names no work-order id | passes | fails — cites no WO id |

PR #306 demonstrated both halves inside one merge. Opened with a body
crediting the commit that introduced the regression, it failed the open
leg. The id was removed to satisfy that leg, which guaranteed the merge
leg would fail — and it did. Four consecutive non-work-order PRs (#302,
#303, #304, #306) have merged with a red post-merge run.

## Decision

**`wo-merged` takes `--uncited skip`, exactly as `wo-needs-review`
does.** A PR naming no work order is a no-op on both legs.

**The malformed-citation case is unchanged and stays loud on both
legs.** A body that names a work order which resolves to none — no
`Closes #N`, ambiguous, unmirrored — is a malformed work-order PR. That
is what `run_lifecycle`'s strictness was really protecting, and
`--uncited skip` already preserves it: the relaxation is gated on
`not WO_TOKEN.findall(body)`.

**The missed flip is reported, not gated.** If a genuine work-order PR
merges having lost its citation entirely, its issue never reaches
`wo:merged`. That is cross-plane drift, and ADR-0045 already decided how
this repo handles cross-plane drift: `sweeps.py reconcile` reports it —
a checked row whose issue carries no `wo:merged` is drift it names by
breakdown path and issue number. Reddening every housekeeping merge to
catch a case the reconcile sweep already catches is the wrong trade.

## Consequences

- Housekeeping PRs merge green. The post-merge run stops being a signal
  everyone learns to ignore, which is what a permanently-red job becomes.
- A work-order PR that loses its citation now merges quietly and surfaces
  in the next reconcile sweep instead of at merge time. That is slower,
  and it is the accepted cost of the trade above.
- `test_the_merged_leg_stays_strict_by_default` is replaced by tests
  asserting the new symmetry, and the merged leg keeps its own
  malformed-citation coverage so the relaxation cannot widen unnoticed.
- This does **not** fix the adjacent problem: the validator still cannot
  tell a work order a PR *implements* from one it names as provenance,
  so an honest archaeology note still cannot carry a WO id. An
  `Implements: WO-####` trailer read in preference to a bare-token scan
  would separate the two; it is seeded, not decided here.
- Status is provisional: the trade above is a judgment about which
  failure is worse to miss, and it should be confirmed by the owner
  rather than inherited silently.
