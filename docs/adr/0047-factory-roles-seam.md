# Factory roles seam: factory_roles.py owns the role vocabulary

- Status: accepted
- Date: 2026-08-05

The factory's role taxonomy had no seam; its de-facto authority was a
test file. Four statements of the role set existed, none importing any
other, and they disagreed:

- **tests/test_factory_charters.py** — a nine-entry `ROLES` tuple plus
  `REQUIRED_FIELDS` for agent-stub frontmatter: a vocabulary living in
  tests/.
- **charter_replay.py** — a three-entry `ROLES` literal whose comment
  ("WO-0014's full set extends this") was a TODO encoded as a constant.
  Fixture validation silently rejected six real charters, and deleting
  the literal would have turned a typo'd fixture role into a green
  replay.
- **assembler.py** — `CHARTER_BY_TYPE` mapping four labels onto two
  roles plus a default.
- **factory/CHARTERS.md** — the nine roles again, in prose.

Adding a tenth role touched ~7 places with nothing failing when they
disagreed. That meets the shared-module bar (CLAUDE.md: multiple real
callers AND observed divergence — the copies stood at 9 vs 3 vs 2).

The naming compounded the problem: the charters lived at
`factory/skills/<role>/SKILL.md`, overloading "skill" a third way in a
repo named skills (plugin stage skills in `skills/`, role charters, and
a harness skill in `.agents/`) — and the swe charter's own body says
"Not a plugin skill."

## Decision

- **`factory_roles.py`** at the repo root is the one home of the role
  vocabulary: `ROLES` (the nine PRD-0001 §Actors roles),
  `REQUIRED_FIELDS` (agent-stub frontmatter beyond `name:`), and the
  two per-role path builders `charter_path(root, role)` /
  `agent_path(root, role)`. charter_replay validates fixtures against
  the full set (its shipped-fixture coverage is a declared, pinned
  `SUPPORTED_REPLAY_ROLES` subset that gates nothing);
  tests/test_factory_charters.py asserts the real files through the
  seam; factory/CHARTERS.md stays the human index.
- **`factory/skills/` is renamed `factory/charters/`**, and each
  role's `SKILL.md` becomes `CHARTER.md` — the name CHARTERS.md
  already used. `find -name SKILL.md` now returns only real skills.
- **factory_roles.py is NOT mirrored** into stamped repos.
  assembler.py (mirrored) keeps its label->role dispatch map as plain
  data: stamped repos carry no charter tree, so an import would ship
  paths to files that do not exist there. tests/test_factory_roles.py
  pins `CHARTER_BY_TYPE`'s values (and the default) to the seam's
  vocabulary instead.

## Consequences

- A tenth role is a one-module edit (plus its two files and the index
  row) — and every consumer disagrees loudly, not silently, until the
  files exist: the seam tests walk `ROLES` against the real tree.
- Charter files rename; every pointer (agent stubs, CHARTERS.md,
  assembler's prompt, docs) moved with them. Zero packaging impact:
  `.claude-plugin/` and `package.json` reference only `./skills`, and
  `factory/charters/` is not in the template payload.
- charter_replay now accepts fixtures for all nine roles; six were
  previously rejected as invalid. Coverage stays honest: the golden
  set still covers only WO-0013's three, stated by
  `SUPPORTED_REPLAY_ROLES` and pinned by tests until fixtures land.
- assembler.py's seam link is test-pinned rather than imported — the
  price of keeping the mirrored payload free of a module whose paths
  are meaningless in a stamped repo.
