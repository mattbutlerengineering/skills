# Utility skills alongside stage skills and the router

- Status: provisional
- Date: 2026-07-02

ADR-0010 gave the plugin two skill kinds: directly-invocable stage skills
and a thin router. A third kind now exists: **utility skills** — skills
that act on the work surrounding the pipeline (the first is
`address-pr-review`, which works reviewer feedback on an authored PR)
rather than advancing a run's artifacts. This extends ADR-0010's taxonomy
(itself provisional); it does not contradict it — stages and the router
are untouched.

What a utility skill is and is not:

- It lives in `skills/<slug>/` with the same frontmatter contract as every
  other skill, and it is a full member of `ALL_SKILLS` (owned by
  `protocol.py` as `UTILITY_SKILLS`, per ADR-0021) — so the structural
  lint checks its frontmatter, the LEDGER tracks its maturity, and the
  trigger eval installs its description alongside the rest and holds it to
  the same coverage policy. Discrimination pressure is the point: utility
  skills sit near stage skills in phrasing space (address-pr-review vs
  review) and must earn their descriptions.
- It has **no stage artifact, no `TEMPLATE.md`, no row in the artifact
  table, and no soft gate** — it does not advance `next_stage`, and the
  router never routes to it. Users invoke it directly when its situation
  arises.
- Its content stays harness-neutral (no hard dependency on third-party
  tooling), like every other skill.

The bar for adding another utility skill is the same as for any skill:
a recurring situation the pipeline's stages don't serve, a description
that discriminates against its neighbors, and a draft LEDGER row it must
graduate honestly.

Skill counts quoted in earlier ADRs (e.g. ADR-0019's "all eleven
descriptions") reflect the roster at their date and are not rewritten;
`protocol.py`'s `ALL_SKILLS` is the living roster.
