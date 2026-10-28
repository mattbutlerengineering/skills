# The skills CLI installs the standalone skills only, and lint derives the list

- Status: provisional
- Date: 2026-10-27

Issue #1130 asks that this repo install through `npx skills add`, the
third-party skills CLI (vercel-labs/skills). It follows ADR-0027 and
ADR-0076, which made omp and Grok supported harnesses, and ADR-0008
(self-contained skills).

The CLI already finds every skill here with no change. It reads
`.claude-plugin/marketplace.json`, whose plugin source `./` puts
`skills/` on its search path, and every `SKILL.md` carries the `name`
and `description` it requires. `protocol.skill_frontmatter_problems`
already holds each description to a bare YAML scalar, the shape the CLI's
strict YAML parser needs (PRD-0007).

How it installs is the constraint. Read from its source (`src/add.ts`,
`src/installer.ts`, `src/plugin-manifest.ts`, 2026-10-27): it clones the
repo to a temporary directory, copies each chosen skill's folder into
`.agents/skills/<name>/`, links agent directories to that copy, then
deletes the clone. Nothing outside the skill folder arrives. Twenty-four
of the thirty-five skills read a file at the plugin root: every stage and
the router read `../../docs/pipeline-protocol.md`, and others run a root
tool such as `board.py`, `kb.py` or `factory_init.py`, or read
`plugin.json` two levels above their folder. Installed that way, those
skills load and then fail on their first read.

## Decision

- **No new manifest.** The CLI reads `.claude-plugin/` as Grok does. A
  `skills` array in `marketplace.json` was considered and left out: the
  CLI adds `skills/` to its search path whether the array is there or
  not, so the array would be a second owner of the roster.
- **The README offers one command that names only the standalone
  skills**, those whose folder survives the lone copy. A skill is
  standalone when no markdown in its folder climbs past `skills/`
  (`../../`), says "two levels above", or runs `python3 <tool>.py` for a
  tool the plugin root holds, and when every sibling skill whose files it
  names (`../<sibling>/references/...`) is standalone too. `automate` is
  out on the second rule: it reads `audit`'s references, and `audit`
  reads the plugin root.
- **`lint.check_readme_skills_cli` derives that set from the skill
  folders** and fails when the README's fenced command installs a skill
  outside it, leaves one out, or names a slug that is not a skill. The
  list is a hand-kept copy of a fact the folders hold, so it is checked
  in both directions.
- **The stages, the router and the root-reading utilities stay
  plugin-only.** Making them standalone would mean a copy of the pipeline
  protocol, and of the root tools, inside each skill folder: many owners
  of one spec, against the seam rule in CLAUDE.md.

## Consequences

- A skill that starts reading the plugin root fails lint until it leaves
  the README command, and a new standalone skill fails lint until it
  joins.
- The detection is lexical. A plugin-root read phrased some other way is
  not seen, and is caught only when someone installs the skill this way.
- No live `npx skills add` run backs this record. The analysis is from
  the CLI's source. Running `npx skills add mattbutlerengineering/skills
  --list` confirms discovery.
