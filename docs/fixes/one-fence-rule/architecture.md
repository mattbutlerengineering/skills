---
stage: architect
run: maintenance:one-fence-rule
date: 2026-10-10
---

# Architecture: one fence rule

## Approach

`gates.py` already contains a correct fence walker: CommonMark closing
(same character, length ≥ the opener) plus the backtick-info rule. Move
it into `knowledge_plane.py` as public functions. Gates' H, M, N and O
then read it from there with no change in behaviour, and the two
divergent walkers (detector D's `ARCH_FENCE` and `validator._unquoted`'s
`FENCES` prefix match) are replaced by calls to it. The rule decides when
a token like `WO_TOKEN` or `CLOSES_TOKEN` is quoted rather than claimed,
and knowledge_plane already owns those tokens. Both callers already
import knowledge_plane, so no new import edge and no new mirror entry is
needed.

## Components

### knowledge_plane fence grammar (moved, now public)

- Responsibility: deciding which lines of a markdown document sit inside
  a fenced code block. Nothing else in the repo decides that.
- Collaborators: none; it is pure, over strings.

### Detector D (`gates._architecture_drift`)

- Responsibility: unchanged (claims in `architecture.md` agree with the
  tree). It now tracks fences with `fence_open`/`fence_closes`, and
  recognises its ```` ```tree-claims ```` block by `ARCH_CLAIMS_FENCE`
  on a line that `fence_open` accepts.
- Collaborators: knowledge_plane fence grammar.

### validator skip gate (`validator._unquoted`)

- Responsibility: unchanged (strip quoted material before the
  uncited-skip gate asks whether the author claims a work order). Fences
  are tracked with `fence_open`/`fence_closes`. Blockquote stripping
  stays local.
- Collaborators: knowledge_plane fence grammar.

### Gates H, M, N, O (`_walk_sections`, `_unfenced`)

- Responsibility: unchanged. They import the moved functions, and
  `gates._unfenced` becomes `knowledge_plane.unfenced`.

## Data model

None. A fence is the tuple `(marker char, marker length)` that
`_fence_open` already returns.

## Interfaces & contracts

### `knowledge_plane.fence_open(line)`

- Input: one line of text, without its newline.
- Output: `(char, length)` when the line opens a fence (`FENCE_OPEN`:
  any leading whitespace, then 3 or more `` ` `` or `~`, then an info
  string), otherwise `None`. A backtick opener whose info string contains
  a backtick is not an opener (CommonMark).
- Failure modes: none; it is total over strings.

### `knowledge_plane.fence_closes(line, char, length)`

- Input: a line, plus the open fence's char and length.
- Output: `True` iff the line is only whitespace and a run of `char` at
  least `length` long (`FENCE_CLOSE`).
- Failure modes: none.

### `knowledge_plane.unfenced(lines)`

- Input: a sequence of lines.
- Output: yields `(lineno, line)`, 1-based, for every line outside a
  fence. Fence lines themselves are never yielded. An unterminated fence
  swallows the rest of the input.
- Failure modes: none.

`FENCE_OPEN` and `FENCE_CLOSE` move with them and stay module constants.
Gates keeps no alias.

## Stack & dependencies

- Standard library `re` only, already imported by knowledge_plane.

## Decisions & alternatives

- **knowledge_plane** over keeping the walker in `gates` and making it
  public: validator would import a leaf tool for shared vocabulary, which
  ADR-0056's consequences retired as a pattern ("no module imports a leaf
  tool for shared vocabulary any more"). Chosen by the owner, 2026-10-10.
- **knowledge_plane** over a new `fences.py`: a new module would need its
  own `factory_init.MIRRORS` entry and manifest line for about 25 lines,
  when an existing mirrored module already owns the tokens this rule
  classifies.
- **The strict (CommonMark) rule** over D's or the validator's: it is the
  only one of the three that handles both reproductions in `defect.md`,
  and `_unquoted`'s own comment already states it as the intent.
- **`fence_closes` keeps its `(line, char, length)` signature** rather
  than taking the tuple: it is a move, not a redesign, and the existing
  call sites stay as they are.
- **Accepted behaviour change, validator:** a ```` ``` ```` line whose
  info string contains a backtick stops opening a fence in `_unquoted`,
  matching CommonMark and H/M/N/O.

## ADRs

None. No decision met the ADR bar (docs/pipeline-protocol.md, *When to
write an ADR*). Moving three pure functions into an existing seam is
cheap to reverse and unsurprising once read. The placement trade-off is
recorded above.
