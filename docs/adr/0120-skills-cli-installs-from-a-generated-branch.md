# The skills CLI installs every skill from a generated `npx` branch

- Status: provisional
- Date: 2026-10-28

Issue #1130 asks that this repo install through `npx skills add`, the
third-party skills CLI (vercel-labs/skills). It follows ADR-0027 and
ADR-0076, which made omp and Grok supported harnesses, and ADR-0008
(self-contained skills). The Owner chose the generated branch over the
two alternatives below, and asked that all 35 skills install this way.

The CLI already finds every skill on `main`. It reads
`.claude-plugin/marketplace.json`, whose plugin source `./` puts
`skills/` on its search path, and every `SKILL.md` carries the `name`
and `description` it requires as one bare YAML scalar (PRD-0007).

How it installs is the constraint. Read from its source (`src/add.ts`,
`src/installer.ts`, `src/plugin-manifest.ts`, `src/source-parser.ts`,
2026-10-27): it clones the repo to a temporary directory, copies each
chosen skill's folder into `.agents/skills/<name>/`, links agent
directories to that copy, then deletes the clone. Nothing outside a
skill folder arrives, and a file named `metadata.json` is never copied.
Twenty-four of the thirty-five skills read the plugin root: every stage
and the router read `../../docs/pipeline-protocol.md`, others run a root
tool such as `board.py`, `kb.py` or `factory_init.py`, and `doctor`
reads `plugin.json` two levels above its folder. The tools those skills
run import 36 root modules and read the `factory/` payload. Installed
from `main`, those skills load and then fail on their first read.

## Decision

- **A generated `npx` branch is the skills CLI's source.** Users run
  `npx skills add mattbutlerengineering/skills#npx`; the CLI reads a
  `#ref` fragment on the `owner/repo` shorthand as the branch to clone.
- **`npx_bundle.py build <out>` writes the branch tree.** It adds one
  skill, `idea-to-prod-runtime`, holding every root `*.py` tool,
  `CONTEXT.md`, `dashboard.html`, `LICENSE`, `NOTICE`, `licenses/`,
  `output-styles/`, `factory/`, `.claude-plugin/plugin.json`,
  `docs/pipeline-protocol.md` and `docs/standards.json`, each at its
  root-relative path, because the tools find their payload beside
  themselves. Installed skills sit side by side, so `../idea-to-prod-runtime/`
  resolves from any of them. The build rewrites each skill's plugin-root
  paths (`../../` not followed by a sibling skill's slug, and "two levels
  above this skill's base directory") to name that folder, and appends a
  short note to every `SKILL.md`. The note says where root tools run from
  and which plugin features this install lacks.
- **The build checks its own output.** Every rewritten path must resolve
  inside the runtime, no path may still climb past the installed skill
  folders, and no file may be named `metadata.json`. `tests/test_npx_bundle.py`
  builds the real repo on every CI run, stamps a repo with the bundled
  `factory_init.py`, and runs the bundled `conductor.py`. A skill that
  names a root file the bundle lacks fails CI on its own PR, not on
  release.
- **`.github/workflows/npx-branch.yml` publishes it.** On a push to
  `main` that touches `plugin.json`, which is a release under ADR-0095,
  and on demand, it builds the tree and force-pushes it as a single
  commit. The branch keeps no history, and nobody edits it by hand.
- **`npx_bundle.py` is root-only.** No payload tool imports it, and
  it imports `cli.py`, so it joins ADR-0091's `cli.py` importer row
  (pinned in `tests/test_dual_membership.py`) and gets the
  `npx-bundle` verb in `factory.py`.
- **`main` holds one copy of every file.** The tree is generated, so no
  manifest pins it and no tool edit on `main` churns a second copy.

## Rejected

- **Commit the runtime skill on `main`.** The plain
  `npx skills add mattbutlerengineering/skills` would work with no
  branch, at the cost of about 2 MB of duplicated source in `main` and a
  manifest regeneration on every tool edit.
- **Clone on first use.** Each root-reading skill would fall back to
  cloning this repo into a cache folder. It is the least code, but it
  puts a network step and the fallback prose into 24 skills.
- **Install only the standalone subset from `main`.** This PR's first
  draft did that: a README command naming the 11 skills that read
  nothing outside their folder, guarded by lint. The Owner wanted every
  skill.

## Consequences

- The branch lags `main` until the next release, or until someone runs
  the workflow by hand. The workflow runs from `main` only, so the first
  publish needs a manual dispatch after this merges.
- Detection is lexical. A plugin-root read phrased some other way is not
  rewritten, and is caught only when someone runs the skill installed
  this way.
- The `/idea-to-prod:<skill>` names and the house-voice output style
  are plugin-only and stay absent from this install.
- No live `npx skills add` run backs this record yet. The analysis is
  from the CLI's source and the bundle's own tests.
