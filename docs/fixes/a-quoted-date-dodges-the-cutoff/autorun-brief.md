# Autorun brief: a-quoted-date-dodges-the-cutoff

Not an artifact. Written 2026-10-17 by the orchestrator. The Owner invoked
`/idea-to-prod:autorun` with no description. No run was mid-pipeline, so
the Owner answered four questions one at a time in session, each taking
the recommended option:

1. What to drive: "O/M date dodge fix (Recommended)", the backlog seed at
   `docs/backlog.md` line 123 (from: session:2026-10-17), filed by the
   fail-closed-roll-up run's review fix loop.
2. Fix shape: "One shared helper (Recommended)".
3. Release: "Prepare and stop (Recommended)".
4. Operate: "Skip (Recommended)".

Everything else below is the orchestrator's reading of the seed and the
code, and is marked as such. A stage that needs an answer this brief does
not hold applies the autorun rule: take a skill-supplied default and log
it, or else stop and surface.

## Run scale

Maintenance (fix) run at `docs/fixes/a-quoted-date-dodges-the-cutoff/`,
entering at Capture. It is a defect: a gate rule can be switched off by
the spelling of a date.

## Capture inputs

- **What is broken.** Detectors O (`gates.py`, `COVERAGE_ADOPTED`, line
  ~1436) and M (`CAPTURE_ADOPTED`, line ~1706) grandfather an artifact
  with `isinstance(date, str) and date < CUTOFF`. That is a raw string
  compare. A quoted post-cutoff date (`date: "2026-10-20"`; `"` sorts
  before `2`), an empty `date:`, or a non-ISO date (`20/10/2026`) sorts
  before the cutoff and switches the rule off. A missing `date:`
  (non-string) is already judged.
- **Reproduction.** Capture must reproduce this for real, not cite the
  seed. For each of O and M, take one fixture its tests already use that
  O/M refuses when undated or post-cutoff. Re-date it with the dodge
  shapes, run the detector through its public function, and quote the
  silent `[]`. The seed and the fail-closed-roll-up review (H's
  identical hole) are the only prior evidence. **No artifact on main has
  these shapes** (orchestrator, measured by the fail-closed-roll-up
  re-review over every tracked verification.md; Capture should re-check
  prd.md and defect.md, the artifacts O and M read). This is prevention,
  and Capture should say so plainly.
- **Root cause (hypothesis).** Three detectors each compare a cutoff on
  their own. H's copy was fixed in #998 (`_rollup_applies`,
  `ROLLUP_ISO_DATE`) and O/M's were not: one fact, three owners, and the
  copies have drifted.
- **Blast radius.** `gates.py` and its payload copy
  (`factory/templates/tools/factory/gates.py`, manifest-pinned), so
  stamped repos get it on the next payload update. Behaviour changes
  only for dates that are quoted, empty, non-ISO, or a datetime. A
  trailing YAML comment (`date: 2026-10-01 # x`) becomes judged, as it
  already is in H. No artifact on main changes outcome; prove it with
  `python3 gates.py` on the real tree.
- **Re-entry depth.** Orchestrator's reading: `re-entry: implement`. The
  design is decided (Owner decision 2), and H's helper and its tests are
  the proven pattern. If Capture finds a real design question (for
  example, O or M reading `date` from a different parse than H's
  `parse_frontmatter(text)`, so the helper's input differs), that is a
  reason to choose `re-entry: architect`, logged.

## Fix shape (Owner decision 2)

One private helper in `gates.py` takes the frontmatter `date` value and a
cutoff and answers "grandfathered?". It holds H's normalization: strip
surrounding quotes and whitespace, read a datetime by its date part, and
grandfather only a `YYYY-MM-DD` value that sorts before the cutoff.
Everything else is judged. H, O and M all call it, and
`ROLLUP_ISO_DATE` (or its successor) has one owner. It stays inside
`gates.py`: no new module (CLAUDE.md's seam rule), and no change to the
cutoff values or to what each detector checks.

## Scope

In: the helper; H, O and M calling it; failing-first tests per dodge
shape for O and M through their public functions (exact problem strings),
with H's existing tests kept green; the payload mirror and
`factory_init.py update-manifest`; marking the backlog seed claimed;
updating any comment or ADR text that describes O/M's compare (ADR-0072
for O's cutoff; ADR-0107's amendment for H, if it names the helper). An
ADR is written only if Capture or Architect finds a decision not already
recorded; a provisional amendment line is preferred.

Out: changing any cutoff value; any other detector; rewriting shipped
artifacts; the fail-closed-roll-up run's deferred minors.

## Success criteria

- For O and M, each dodge shape (double-quoted, single-quoted,
  empty, non-ISO post-cutoff dates) is judged: the detector returns its
  existing problem string where it did not before. A pre-cutoff ISO
  date, quoted or a datetime, is still grandfathered.
- H's behaviour is unchanged: all its existing tests pass untouched.
- One owner: the ISO-date pattern and the normalization appear once in
  `gates.py`. Check this with a grep count, since `one_owner.py` cannot
  see function bodies.
- `python3 gates.py` reports 0 problems on main's real tree with no
  shipped artifact edited.
- `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
  `python3 gates.py && python3 gates.py --selftest` all pass, and
  detector E is clean after `update-manifest`.

## Constraints

Stdlib only. Problem-string contracts. Never touch
`.claude-plugin/plugin.json` (ADR-0095). Delete stray `.orig`/`.rej`
before `update-manifest`. Gates scan every markdown file, so write no
literal four-digit work-order or PRD-style id that does not exist.

## Tracker

No issues seed the run, and there is no tracker interaction before Ship.
At Ship, file one plain `type:defect` issue, close it from the PR with
`Closes #N`, and include a `No work order:` line. Run `gh pr create` as
the first command of its own Bash call, with the body file written in an
earlier call, so the preflight hook judges it.

## User-facing surface

None.

## Release authorization

Prepare and stop (Owner decision 3). Ship pushes, files the issue, opens
the PR, records `outcome: prepared` with `pending-merge:`, and stops. No
merge, tag or version bump.

## Operate

skip. The Owner decided this run gets no retro (decision 4). It prevents
a shape no artifact has, so no signal is expected. The run stays active.

stop-after: ship
