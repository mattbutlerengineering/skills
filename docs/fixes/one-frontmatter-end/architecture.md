---
stage: architect
run: maintenance:one-frontmatter-end
date: 2026-10-24
assumptions:
  - "The rule (brief decision 1, default taken): a fence line matches gates' current `^---\\s*$`, so trailing whitespace is allowed and leading whitespace is not. CRLF counts, because every line break `str.splitlines` splits on ends a line. An empty block is frontmatter with no fields. A closer at end of file closes the block. An unterminated or indented opener means no frontmatter. Chosen because gates' answer is then unchanged on every input, detectors H and M fail safe (an exact-fence rule would scan a trailing-space block's `status:` as a verdict), and defect.md's sweep found 0 of 1010 tracked markdown files in any shape where the readers disagree."
  - "The owner (brief decision 2, default taken): `protocol.frontmatter_end(lines)`, returning the closing fence's index or None. The four current owners become thin callers, and their signatures stay as they are."
  - "ADR number 0118, not 0117: 0116 is the last ADR on this branch, but open PR #1074 (branch fix/seen-before-partner) already adds an ADR numbered 0117. Ship confirms the number against main before release, per the protocol's numbering rule."
  - "The dual-membership pin in tests/test_dual_membership.py gains the pair (launch_demo, protocol). The pin exists to record such a change, and ADR-0110, ADR-0112 to ADR-0115 each added their pairs the same way. Adding a recorded pair is not editing a test to make it pass: the test is designed so that its expected set changes with an ADR."
  - "The shared shape table lives in a test helper module (tests/frontmatter_shapes.py, beside tests/cli_contract.py and tests/fixture_tree.py), so the owner test and the three caller tests read one table, not four copies."
  - "Interview: the autorun brief supplies both decisions with defaults. No question without a default came up, so no trade-off was put to the Owner live. The ADR lands provisional for the Owner to accept."
---

# Architecture: one owner of where frontmatter ends

## Approach

Move gates' frontmatter fence rule, as it stands, into `protocol.py`, the
seam ADR-0021 named for frontmatter reading. Add one function there that
answers "where does this file's frontmatter end". All four current owners
call it: `protocol.parse_frontmatter`, `gates._skip_frontmatter`,
`launch_demo._body` and `knowledge_plane._declared_status`. Taking gates'
rule rather than protocol's means no change on any input for the reader the
detectors lean on most, and H and M fail safe. protocol, launch_demo and
knowledge_plane change only on shapes that no tracked file contains. The
function takes lines and returns an index, because two callers already hold
lines and need a body index, and the two text callers can split their text
once. `protocol` imports neither `gates`, `knowledge_plane` nor
`launch_demo`, so the edges still point from callers to the seam.

## Components

### protocol frontmatter fence (new owner)

- Responsibility: deciding whether a file has frontmatter and which line
  closes it. Nothing else in the repo decides that.
- Collaborators: none. It is a pure function over a list of strings. It
  holds the one fence regex, `^---\s*$`, moved from `gates.FRONTMATTER_FENCE`.
  `protocol._FRONTMATTER` is deleted.

### `protocol.parse_frontmatter` / `read_frontmatter` (thin caller)

- Responsibility: unchanged (the `key: value` field grammar, `|` block
  scalars, None for no block, `{}` for a block with no fields). It splits
  the text with `splitlines()`, asks the owner for the end, and parses
  `lines[1:end]`. The CRLF `replace` step is no longer needed, because
  `splitlines` already splits on `\r\n`.
- Collaborators: protocol frontmatter fence.

### `gates._skip_frontmatter` (thin caller, detectors H and M)

- Responsibility: unchanged (the first body line index, else 0). It returns
  `end + 1` when the owner finds an end, else 0. `gates.FRONTMATTER_FENCE` is
  deleted. Nothing outside gates referred to it.
- Collaborators: protocol frontmatter fence. `_rollup_applies` and detector
  M's date read keep calling `parse_frontmatter`. Since both now sit on the
  owner, the section walk and the date read give one answer about one file.

### `launch_demo._body` (thin caller)

- Responsibility: unchanged (launch.md's text after its frontmatter). It
  splits with `splitlines(keepends=True)`, asks the owner, and returns
  `"".join(lines[end + 1:])`, which keeps the body's bytes exactly, or the
  text unchanged when there is no end.
- Collaborators: protocol frontmatter fence. This is a new import:
  `launch_demo` is root-only and `protocol` is mirrored, so ADR-0091's
  dual-membership set gains one pair.

### `knowledge_plane._declared_status` (thin caller)

- Responsibility: unchanged (the `- Status:` line, else a frontmatter
  `status:` field, else `(0, None)`). The fallback scans only `lines[1:end]`
  when the owner finds an end. The inline `strip() == "---"` walk is deleted.
- Collaborators: protocol frontmatter fence (`knowledge_plane` already
  imports `parse_frontmatter` from protocol).

### Payload twins

- Responsibility: `factory/templates/tools/factory/{protocol,gates,knowledge_plane}.py`
  stay byte copies of the root files (`factory_init.MIRRORS`). The manifest
  is regenerated with `python3 factory_init.py update-manifest`, after any
  stray `.orig` or `.rej` files are deleted. `launch_demo.py` is not
  mirrored, and it stays that way.

## Data model

None. A file's frontmatter is described by one integer: the index of the
closing fence line in its list of lines, or None. The block is
`lines[1:end]` and the body is `lines[end + 1:]`.

### The rule, shape by shape

Each shape's block holds `status: ok`, and its body is `# Body`, as in
defect.md's verdict table. "Now" is what the four callers do today. "Rule"
is the one answer all four give afterwards.

| Shape | Now (protocol / gates / launch_demo / knowledge_plane) | Rule: `frontmatter_end` | Who changes |
|---|---|---|---|
| LF, exact fences | fm / fm / fm / fm | 2 (frontmatter) | nobody |
| CRLF | fm / fm / none / fm | 2 (frontmatter) | launch_demo (only for undecoded text; `cli.read_file` already decodes) |
| opener with trailing whitespace | none / fm / none / fm | 2 (frontmatter) | protocol, launch_demo |
| closer with trailing whitespace | none / fm / none / fm | 2 (frontmatter) | protocol, launch_demo |
| unterminated opener | none / none / none / fm | None (no frontmatter) | knowledge_plane |
| no frontmatter | none / none / none / none | None | nobody |
| empty block (`---` then `---`) | none / fm / none / none | 1 (frontmatter, no fields) | protocol (None to `{}`), launch_demo |
| closer at end of file, no newline | none / fm / none / fm | 2 (frontmatter) | protocol, launch_demo |
| opener with leading whitespace | none / none / none / fm | None (no frontmatter) | knowledge_plane |

The comparison also turned up shapes the table did not list. Each was found
by running the old and new rules over inputs where they differ:

- **Empty block with a later `---` line.** Today protocol's regex reads
  `---`, `---`, body, `---` as one block that runs from the first fence to
  the later `---` line, so body lines that look like `key: value` become
  fields. Under the rule, the block ends at line 1 and the body is never
  parsed.
- **A closer indented by whitespace.** knowledge_plane closes the block on
  it today. Under the rule it is not a fence, so the block runs on to a later
  closer, or has no frontmatter at all.
- **Other line breaks.** A lone `\r`, `\v`, `\f`, `\x1c` to `\x1e`, `\x85`,
  ` ` and ` ` end a line for gates today, because gates splits with
  `splitlines`. Under the rule they end a line for protocol and launch_demo
  too.

## Interfaces & contracts

### `protocol.frontmatter_end(lines)`

- Input: a list of a file's lines, from `splitlines()` or from
  `splitlines(keepends=True)`. The same file gives the same index either way,
  because `\s*` absorbs the line ending.
- Output: the index of the closing fence line, an int of at least 1, when
  `lines[0]` and some later line both match `^---\s*$`. Otherwise None: the
  list is empty, the first line is not a fence (an indented opener included),
  or no later line closes it. The first matching later line wins.
- Failure modes: none. It is total over lists of strings, and it neither
  raises nor reads anything. A None answer is the "no frontmatter" contract,
  and each caller already maps it: protocol returns None, gates returns 0,
  launch_demo returns the text unchanged, and knowledge_plane skips the
  fallback.

### Callers (signatures unchanged)

- `protocol.parse_frontmatter(text)` and `read_frontmatter(path)`: same
  inputs and outputs. They return None exactly when `frontmatter_end` does.
- `gates._skip_frontmatter(lines)`: same output on every input as before.
- `launch_demo._body(text)`: same output for exact-fence LF text. On the
  shapes in the table, it now strips the block.
- `knowledge_plane._declared_status(lines)`: same output whenever a
  `- Status:` line exists, or the block is terminated with column-0 fences.

## Stack & dependencies

- Python 3 standard library only (`re`), as `stdlib-only` requires. No new
  module and no new dependency.
- One new import edge, `launch_demo` to `protocol`. It is root-only to
  mirrored, so it adds no payload file.

## Test strategy

Implement writes these first, before any code moves. The rule is pinned
once, and each caller is pinned against the owner, never against its own
copy.

- **The shape table** (`tests/frontmatter_shapes.py`, a test helper module):
  `SHAPES`, a tuple of `(name, text, expected end)` rows. It covers every row
  of the rule table above, plus the extra shapes from the comparison: an
  empty block with a later `---` line, an indented closer, a tab after the
  opener, a lone `\r` file, empty text, and a file that is a single `---`.
- **The owner test** (`tests/test_protocol_frontmatter.py`): for each row,
  `frontmatter_end(text.splitlines())` and
  `frontmatter_end(text.splitlines(keepends=True))` both equal the expected
  end. Table-driven, one `subTest` per row.
- **Caller agreement**, one test per caller, in that caller's own suite,
  each iterating `SHAPES`:
  - `test_protocol_frontmatter.py`: `parse_frontmatter(text)` is None
    exactly when the end is None. Otherwise it equals the fields parsed from
    the block.
  - `test_gates.py`: `_skip_frontmatter(lines)` equals `end + 1`, or 0.
    Detector M's reproduction from defect.md (a capture brief dated before
    `CAPTURE_ADOPTED` with no required sections) gives `[]` for both the
    `---` and the `--- ` opener, and `_rollup_applies` gives `False` for both.
  - `test_launch_demo.py`: `_body(text)` equals the text after the closing
    fence line, or the text unchanged.
  - `test_knowledge_plane.py`: with no `- Status:` line,
    `_declared_status(lines)` reads the block's `status:` exactly when the
    end is not None.
- **One definition, counted** (`test_protocol_frontmatter.py`): an AST walk
  over every tracked non-test `.py` file, root and payload alike, collects
  each string constant that defines a frontmatter fence matcher (a `---`
  regex passed to `re.compile`, or a `"---"` literal compared with `==`). It
  then asserts the exact per-module count map: protocol.py and its payload
  twin hold one each, plus the known non-owners defect.md lists
  (`SETEXT_UNDERLINE`, `lint.py`'s table separator, `charter_replay.py`'s
  prompt delimiters), each at its current count. It asserts equality on
  counts, not `assertIn`, so a second copy fails it. A mutation check should
  show the pin catching a re-added `FRONTMATTER_FENCE` in gates.py.
- **The pin for the new edge**: `tests/test_dual_membership.py`'s
  `ROOT_ONLY_IMPORTS_MIRRORED` gains `("launch_demo", "protocol")`, from 55
  pairs to 56, citing ADR-0118.
- **Every existing test passes unchanged otherwise.** That includes
  `test_fieldless_block_returns_empty_dict` (`---`, blank line, `---` stays
  `{}`) and the CRLF parse test.

## Traceability to defect.md's success criteria

- One answer from all four callers on every verdict-table shape: the owner,
  the caller-agreement tests, and detector M's and `_rollup_applies`'
  reproductions.
- One definition of the fence: deleting `_FRONTMATTER`, `FRONTMATTER_FENCE`
  and the `strip()` walk, plus the counted pin.
- Every existing test unchanged, and the battery green: the test strategy,
  the dual-membership pin above, and the payload twins with the regenerated
  manifest.
- Verify's old-against-new sweep over every tracked `*.md` file: Verify owns
  it. The rule table predicts no change, because defect.md found 0 tracked
  files in any changed shape.

## Decisions & alternatives

- **Trailing whitespace makes a fence (gates' rule)** over an exact `---`
  fence (protocol's rule). Under the exact rule, H and M would scan a
  trailing-space block's `status:` as a verdict, which is the backstop
  bypass gates' comment records, so H would fail open. It would also move
  the verdicts of gates, the busiest reader, rather than protocol's, which no
  tracked file reaches. ADR-0118.
- **An unterminated or indented opener means no frontmatter** over
  knowledge_plane's reading of either as frontmatter. No other reader agrees.
  The fallback then fails closed: detector D reports that ADR as declaring
  no Status line. ADR-0118.
- **An empty block is frontmatter with no fields** over None. This matches
  gates, and it matches `read_frontmatter`'s documented contract ("a
  present-but-fieldless block is an empty dict"). ADR-0118.
- **The owner in protocol.py** over gates.py or knowledge_plane.py.
  protocol is ADR-0021's frontmatter seam, and both of the others already
  import it. Any other home would make protocol import a caller. ADR-0118.
- **The interface returns the closing line's index** over the body text or
  the body index. Two callers hold lines and need an index. The text callers
  can split once, and the closing index also gives them the block
  (`lines[1:end]`) without a second search.
- **launch_demo imports protocol** over keeping its own string search, or
  importing through knowledge_plane. Its own search is the divergence being
  removed, and it does not otherwise need knowledge_plane. The one new pair
  is recorded in the pin. ADR-0118.
- **One shape table in a test helper** over a table copied into each suite.
  Four copies would be the four-owner problem again, inside the tests.

## ADRs

- [ADR-0118](../../adr/0118-protocol-owns-where-frontmatter-ends.md):
  protocol.py owns where frontmatter ends, and a fence line may carry
  trailing whitespace (provisional).
