# protocol.py owns where frontmatter ends, and a fence line may carry trailing whitespace

- Status: provisional
- Date: 2026-10-24

Recorded by the `one-frontmatter-end` maintenance run
(`docs/fixes/one-frontmatter-end/`), unattended, so it is provisional. It
follows ADR-0021 (`protocol.py` is the seam for frontmatter reading) and
ADR-0110, ADR-0112, ADR-0113, ADR-0114 and ADR-0115 for the dual-membership
pin.

## Context

Four functions decide where a markdown file's frontmatter ends, each with its
own rule: `protocol.parse_frontmatter` (an exact-fence regex after CRLF
normalization), `gates._skip_frontmatter` (`^---\s*$` per line),
`launch_demo._body` (a literal `---\n` string search) and
`knowledge_plane._declared_status` (a `strip() == "---"` walk). They disagree
on six of nine shapes in the run's verdict table. Detectors H and M use two of
them on one file: a dated artifact whose opener is `--- ` has its block
skipped as frontmatter by the section walk, but its `date:` read as missing,
so a grandfathered file is judged as undated. No tracked file hits a divergent
shape today. ADR-0021's seam rule (multiple real callers and observed
divergence) is met.

Two things outlive the commit. The first is the rule, which ships in every
stamped repo's CI through the mirrored `protocol.py`, `gates.py` and
`knowledge_plane.py`. The second is the import edge `launch_demo` gains.

## Decision

- **The rule.** A fence line is a line that matches `^---\s*$`: three dashes
  at column 0, then nothing but whitespace. This is gates' current rule,
  moved as it stands. A file has frontmatter when its first line is a fence
  line and a later line is too. The block is the lines between them, and the
  body starts on the line after the closer. Every line break that
  `str.splitlines` splits on ends a line, so CRLF counts. An empty block
  (two fence lines in a row) is frontmatter with no fields. A closer at end of
  file with no newline closes the block. An opener with no closer, or an
  opener indented by whitespace, means the file has no frontmatter.
- **The owner.** `protocol.frontmatter_end(lines)` returns the index in
  `lines` of the closing fence line, or None when the file has no
  frontmatter. `lines` may come from `splitlines()` or from
  `splitlines(keepends=True)`, and both give the same index.
  `parse_frontmatter`, `gates._skip_frontmatter`, `launch_demo._body` and
  `knowledge_plane._declared_status` all call it, and their signatures and
  return shapes stay as they are. `protocol._FRONTMATTER` and
  `gates.FRONTMATTER_FENCE` are deleted, and no other module defines a
  frontmatter fence.
- **The import edge.** `launch_demo` (root-only) imports `protocol`
  (mirrored), so the dual-membership set gains the pair `launch_demo` to
  `protocol` and grows from 55 pairs to 56. `tests/test_dual_membership.py`'s
  pin carries the new pair. `protocol` imports none of its callers, so the
  edge adds no cycle.

## Rejected alternatives

- **protocol's exact-fence rule.** Detectors H and M would then scan a
  trailing-space block as body and read its `status:` as a verdict. That is
  the false positive and backstop bypass `gates.py`'s frontmatter comment
  records, so H would fail open. It would also change gates, the most-used
  reader in the detectors, rather than protocol, whose divergent shapes no
  tracked file reaches.
- **knowledge_plane's `strip()` rule.** It accepts an indented opener and
  reads a status from an unterminated block, from anywhere in the file. No
  other reader treats either as frontmatter.
- **The owner in `gates.py` or `knowledge_plane.py`.** `protocol.py` is the
  seam ADR-0021 named for frontmatter reading, and `gates` and
  `knowledge_plane` already import it. Owning the rule anywhere else would
  make protocol import a caller.
- **An owner that returns the body text.** `gates` and `knowledge_plane`
  hold lines and need an index. A text-returning owner would make them join
  and re-split, and the index answer serves the text callers too.

## Consequences

- `parse_frontmatter` now parses three shapes it used to return None for: a
  fence with trailing whitespace, an empty block (now `{}`), and a closer at
  end of file. It also stops treating an empty block that a later `---` line
  follows as a block running to that later line. `launch_demo._body` strips
  frontmatter from CRLF text, trailing-space fences, empty blocks and closers
  at end of file. `knowledge_plane._declared_status` stops reading a status
  from an unterminated or indented opener, so detector D reports that ADR as
  declaring no Status line, which fails closed. `gates._skip_frontmatter`'s
  answer does not change on any input.
- Line breaks other than `\n` and `\r\n` (a lone `\r`, `\v`, `\f`, `\x1c` to
  `\x1e`, `\x85`, ` `, ` `) now end a line for every reader, as they
  already did for gates.
- The rule is now one regex in a mirrored module. Changing it changes every
  stamped repo's detectors at once and needs a new ADR. A change to the
  callers' handling of the block's fields is out of scope here: the
  `key: value` grammar is unchanged.
