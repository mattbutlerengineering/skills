# Autorun brief — maintenance:plugin-description-drift

Collected 2026-08-23. Not an artifact: carries no frontmatter and never
counts toward orientation or run discovery.

## Origin

Backlog seed, `docs/backlog.md:31` (from: session:2026-08-19), claimed in
place as `(claimed: maintenance:plugin-description-drift)`. Selected by the
operator from three candidates when autorun found its only active run
(`feature:first-live-dispatch`) hard-blocked on operator-minted secrets.

## Scale and slug

Maintenance run, slug `plugin-description-drift`, artifacts under
`docs/fixes/plugin-description-drift/`.

## What and why

`.claude-plugin/plugin.json`'s `description` enumerates the plugin's
utility skills and names nine of twelve. `lint.check_manifest` reads that
file only to assert required fields are non-empty, so nothing holds the
description to the taxonomy — while `check_readme_skills` and
`check_ledger` hold README.md and LEDGER.md to it. The description is the
string a user reads first when deciding whether to install.

## Scope

In: the description's utility-skill list, and a lint checker that holds it
to `protocol.UTILITY_SKILLS`. Out: the stage-skill prose in the same
string (it names stages in title case, not slugs, and changing that is a
wording decision nobody asked for); the `pi.skills` omp manifest
(`check_pi_package` already guards it); README and LEDGER (already held).

## Constraints

Repo conventions apply unchanged: stdlib only, problem-string contracts
(label-prefixed strings returned to a caller that prints and exits
nonzero), tests asserting exact strings through public interfaces, and the
full battery green before Ship.

## Tracker

No tracker seeding. An issue is opened at Ship for the PR to close, per
this repo's detector-B traceability grammar.

## Release authorization

None given. Ship therefore prepares and stops: no merge, no tag, no
publish. This run may open a PR and push its branch, because that is how
the repo records work, but merge authority is the operator's under
ADR-0036 clause 2 — the author cannot be the independent reviewer.
