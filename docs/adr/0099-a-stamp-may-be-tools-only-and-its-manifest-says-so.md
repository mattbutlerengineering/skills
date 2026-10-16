# A stamp may be tools-only, and its manifest says so

- Status: provisional
- Date: 2026-10-15

Supersedes nothing. ADR-0032's pristine payload and ADR-0048's
installed-vs-payload location grammar both stand; this ADR adds a second
shape of stamp beside the full one. Recorded for issue #941, found in a
consumer repo.

## Context

A consumer with its own CI, labels and docs took only the Conductor:
`tools/factory/*.py` and `.github/factory.json`, copied by hand from the
plugin's payload. That install had no upgrade path. `factory_init.py
update` refreshes an already-stamped target and needs the
`factory/manifest.json` that only `stamp` writes, and `stamp` brings
everything the consumer left out: the Makefile, the workflows, the doc
seeds and the pristine mirror. So the consumer's CLAUDE.md documented a
hand procedure instead — copy the tools, diff each against the
manifest's sha256 entries, record the version by hand — and it stayed in
sync only because the Owner knew to do it. `conductor.py` had no way to
say which payload it was: a batch ran on 0.15.0 tools the day 0.18.0
shipped, with no tell.

## Decision

1. **`stamp --tools-only` and `update --tools-only` exist.** The
   tools-only payload is `tools/factory/` plus `.github/factory.json`
   (`factory_init.TOOLS_ONLY_DESTINATIONS`): the tools and the config
   they read, nothing else. No Makefile, no workflows, no seeds, and no
   `factory/templates/` mirror.
2. **The written manifest names only those keys and carries a marker.**
   A tools-only target's `factory/manifest.json` holds the source
   manifest's `plugin` and `version`, `"install": "tools-only"`
   (`gates.INSTALL_KEY`, `gates.TOOLS_ONLY`) and the subset's `files`. A
   full stamp's manifest is the plugin's own, byte for byte, and never
   carries the marker, so an existing full stamp is untouched by this
   decision.
3. **Detector E honours the marker.** With it, E's mirror half stands
   down — there is no mirror to compare, by design — and its stamped
   half, which checks every listed tool in use against the manifest, is
   the whole gate. Without it, a missing mirror is still a partial stamp.
   Doctor's Makefile, workflow and code-owner steps do not apply to a
   marked target.
4. **Plain `update` honours the marker.** It refreshes what the manifest
   lists — every tool, including one the payload gained since the stamp
   — rewrites the manifest, lands nothing else, and prints no make-target
   report. `--tools-only` on `update` is the adoption path for a tools
   tree copied by hand with no manifest; it refuses a full stamp rather
   than downgrading one. `update` now also refuses a manifest it cannot
   read, with the read's own words, rather than overwriting it with the
   whole payload: a stamp it cannot classify is not a full stamp.
5. **`conductor.py --version` reads the manifest's `version`**, which
   every stamp has recorded from `.claude-plugin/plugin.json` at regen
   time since the manifest existed, and `plan` and `open` end with the
   same line. No new field: the version was already there, unread. A
   tools tree with no manifest reports `unversioned` and names the
   adoption command.

## Rejected alternatives

- **Mirroring the tools subset under `factory/templates/` in a
  tools-only target**, so that E needs no marker. It doubles the files
  the consumer said it did not want, and the mirror's one use there —
  restoring a hand-edited tool — is `update` from the plugin checkout in
  any case.
- **Deriving the subset from the keys a target's manifest happens to
  list** instead of from a marker. A tool the payload gained since the
  stamp would never land, and the Conductor's siblings import each
  other, so a missing sibling is a broken stamp.
- **Warning in `plan` when the payload is behind the installed plugin.**
  The running plugin's version is discoverable from a consumer only
  through Claude Code's private `installed_plugins.json`, which is
  undocumented, schema-versioned, and holds several entries per plugin
  keyed by project path (four versions of this plugin at once on the
  Owner's machine, one per worktree). A warning that resolves the wrong
  entry, or none, is worse than printing the payload version and letting
  the Owner compare.

## Consequences

- A tools-only consumer upgrades with `python3 factory_init.py update
  <target>` from the plugin checkout, like every other stamped repo, and
  its hand procedure retires.
- `tests/test_factory_init.py` pins the subset, the marker, the
  adoption and refusal paths, and — against the real payload — that a
  tools-only target passes its own gates and reports its version.
- The `ask` and `answer` argv parsers moved from `conductor.py` to
  `conductor_consent.py` so that `conductor.py` stays under its
  800-line ceiling once `--version` joined its dispatch; the rows they
  append are still conductor's.
