# parse_run reads every run artifact and the ADR index through the guarded read

- Status: accepted (Owner, 2026-10-14)
- Date: 2026-10-14

The Owner chose this on 2026-10-14, in session ("Guard + amend
ADR-0068"). It resolves issue #881. It amends ADR-0068: the shape of
`parse_run`'s per-run walk, where only `verification.md` had an error
channel. The rest of ADR-0068 stands.

## Context

ADR-0068 records `parse_run`'s walk. For each run it captures the lines
of `breakdown.md`, `prd.md` (and its frontmatter) and `architecture.md`,
plus `verification.md`'s text or its decode error, mirroring detector
H. It also reads `docs/adr/README.md`. Only `verification.md` and, since
issue #855, the ADR files were read guarded.

Issue #877 guarded the `scannable` read through `cli.read_file`
(ADR-0075), so detector D names an undecodable doc as
`D: cannot read <rel>: <err>`. The run artifacts and the ADR index are
in that selection too, but the run-level read happens first. A non-UTF-8
`prd.md`, `breakdown.md`, `architecture.md` or ADR index still raised
`UnicodeDecodeError` out of a full `gates.py` run, as a traceback
instead of a problem string.

## Decision

1. **Every other `parse_run` read goes through `cli.read_file`.** That
   covers each run's `breakdown.md`, `prd.md` and `architecture.md`, and
   `docs/adr/README.md`. `prd.md` is read once, and its frontmatter is
   parsed from that text (`protocol.parse_frontmatter`, which
   `read_frontmatter` now calls). `verification.md` keeps its ADR-0068
   shape, `verification_error`, which detector H reports in its own
   words.
2. **An unreadable file is None plus one named problem.** Its field is
   None, as if the run carried no such file, and `parse_run` adds the
   unlabelled `cannot read <rel>: <err>` string to a new
   `artifact_problems` list.
3. **Detector D reports them.** D already reports `adr_problems` and
   `scannable_problems`, and these files are also scanned docs, so the
   same string can arrive twice. D de-duplicates across all three lists
   and reports each once. An ADR index that exists but cannot be read is
   not also reported as missing.

## Rejected alternatives

- **Report each artifact from the detector that reads it (A, G, N,
  O).** Four detectors would each grow the same read-error case, and a
  file read by two of them would be reported twice under different
  labels. D already owns `cannot read` for the ADRs and scanned docs.
- **Leave the reads uncaught.** One undecodable file anywhere in a run
  stops every detector from reporting, which is what #877 removed for
  the scanned docs.

## Consequences

- Detectors A, G, N and O see an unreadable artifact as absent. The
  only report is D's `cannot read` line.
- `parse_run`'s returned dict gains `artifact_problems`. Hand-built
  parsed dicts in tests carry it too.
