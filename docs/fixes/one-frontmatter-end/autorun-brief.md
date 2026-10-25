# Autorun brief: maintenance:one-frontmatter-end

Not an artifact. The brief autorun collects once, standing in for the
interviews the stages would otherwise run. Collected 2026-10-25, one
question at a time, from the Owner.

## Origin

Backlog seed `docs/backlog.md:101` (from: maintenance:one-fence-rule),
to be claimed in place as `(claimed: maintenance:one-frontmatter-end)`.

## Run scale and entry

Maintenance, slug `one-frontmatter-end`, artifacts at
`docs/fixes/one-frontmatter-end/`. Entry is capture with
`re-entry: architect` (Owner decision): the fix decides a rule and an
owner, not a tuning value.

## Defect

Three functions each decide where a file's frontmatter ends, and they
disagree (observed on main at collection; capture re-reproduces each
for real):

- `protocol.parse_frontmatter` (`_FRONTMATTER`,
  `\A---\n(.*?)\n---\n`, after CRLF normalization) returns None for a
  file whose opening fence is `--- ` (trailing whitespace).
- `gates._skip_frontmatter` (`FRONTMATTER_FENCE`, `^---\s*$`) treats
  that same file as having frontmatter, so detectors H and M skip a
  block protocol says is not frontmatter.
- `launch_demo._body` matches only a literal `---\n...\n---\n`: no
  CRLF, no trailing whitespace.

## Decisions for Architect

Architect drafts both with a recommended default, takes the default,
and logs it under `assumptions:`; any ADR lands `provisional` for the
Owner to accept.

1. **The rule.** Is a fence line with trailing whitespace a frontmatter
   fence? Does CRLF count? What does an unterminated opener mean?
2. **The owner.** Recommended: `protocol.py` (the ADR-0021 seam, which
   `gates.py` already imports) owns "where frontmatter ends"; `gates`
   and `launch_demo` become thin callers. CLAUDE.md's seam rule
   (multiple real callers AND observed divergence) is met.

## Constraints

- Stdlib only. Test first; never edit an existing test to make it pass.
- `gates.py` and `protocol.py` are mirrored into the payload
  (`factory_init.MIRRORS`): delete stray `.orig`/`.rej`, then
  `python3 factory_init.py update-manifest`, and commit the manifest.
- Battery: `python3 run_tests.py`, `python3 lint.py`,
  `python3 kb.py drift`, `python3 gates.py && python3 gates.py --selftest`.
- Open PR #1079 also edits `gates.py` (the zero-count window, a
  different region); Ship chain-checks the pair with merge-tree.
- Verify sweeps every tracked `*.md` file, old vs new frontmatter
  verdict, and reports every change.
- Never fabricate evidence.

## Tracker

File one plain issue labelled `type:defect`; the PR body carries a
`No work order:` line and `Closes #N`.

## User-facing surface

None.

## Release authorization

**None.** Prepare and stop: Ship pushes, files the issue, opens the PR,
records `outcome: prepared` with `pending-merge:`, and stops. No merge,
tag or version bump (ADR-0095).

## Operate

skip. Prevention with no user signal expected; the run stays active.

stop-after: ship
