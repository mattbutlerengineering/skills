---
run: maintenance:a-tenth-role-nothing-fails-on
date: 2026-08-27
---

# Autorun brief

**Scale.** Maintenance run, `re-entry: implement` — a located gap with a
demonstrated reproduction, not a design question.

**What and why.** `factory_roles.py` (ADR-0047) is the seam that owns the
nine-role vocabulary. Its docstring says why it exists: before it, the
role set had four homes that never imported each other, and "adding a
tenth role touched all of them, and nothing failed when they disagreed."
The seam made the nine agree. Nothing makes a tenth fail: every check in
the factory iterates `ROLES` and asks whether the files honour it, and
none asks whether the files hold anything `ROLES` does not name.

**Scope, in.** The inverse direction, asserted in
`tests/test_factory_charters.py` for the three places a role is spelled
on disk: the agent-stub directory, the charter directory, and the
`factory/CHARTERS.md` index table.

**Scope, out.** `factory_roles.py` itself — the seam is correct; it is
its domain that was never closed. No new production helper: the on-disk
enumeration would have exactly one caller, and the repo's bar for a
shared definition is multiple real callers plus observed divergence.
`lint.py` and `gates.py` (both contended by open PRs, and this is a
repo-shape invariant that belongs beside its existing partner tests).

**Success criteria.** A stub, charter directory, or index row naming a
role outside `ROLES` fails the suite; the clean repo stays green; no
production module and no payload byte changes.

**Constraints.** Stdlib only. `tests/test_factory_charters.py` is not
mirrored, so no manifest regeneration is expected.

**Release authorization.** None given. Ship prepares and stops.

**Tracker.** No issue interaction — read-only `gh` only.
