---
stage: architect
run: feature:seed-backlog
date: 2026-07-05
ux: skipped — file convention and skill instructions; no user-facing surface
---

# Architecture: seed backlog

## Approach

Implement ADR-0029 as a convention, not a system: one new protocol section
defines `docs/backlog.md` and its entry grammar (single source of truth),
three skills gain a sentence or two of prose wiring (operate appends, next
reads at two safe moments, idea claims), and the grammar gets one parser in
`protocol.py` with a thin lint checker so conformance is mechanically
checkable. Nothing executes at runtime in target repos; the design's whole
job is to stay advisory — the file is readable by skills but never consulted
for orientation.

## Components

### Protocol section "Seed backlog (optional)" (docs/pipeline-protocol.md)

- Responsibility: the single source for location, entry grammar, producers,
  consumers, claim convention, and the advisory rule ("orientation never
  reads backlog state"), phrased parallel to the tracker-mirror section.
- Collaborators: read by every skill that touches the backlog; mirrored by
  `protocol.py`'s parser.

### Skill prose wiring (skills/operate, skills/next, skills/idea)

- Responsibility: operate step 6 appends retro seeds to `docs/backlog.md`
  (creating it if absent); next lists unclaimed seeds in exactly two
  moments — "what's next" with no active run, and its completed-run step —
  and never during active-run orientation; idea, when starting from a seed,
  marks it `(claimed: <run-ref>)` in place and records the origin in
  `idea.md`. One optional sentence in capture noting deferred defects may be
  parked as seeds.
- Collaborators: the protocol section (each skill's step 1 read).

### Backlog grammar in protocol.py + lint checker

- Responsibility: `parse_backlog(text)` / `check_backlog(text)` in
  `protocol.py` (artifact conventions are its charter, ADR-0021); a thin
  `check_backlog` lint checker registered in `lint.py`'s `CHECKERS`
  validating `docs/backlog.md` when present (absent file = no problems —
  strictly opt-in, like the tracker bridge).
- Collaborators: `lint.py`, `tests/test_lint_checkers.py`.

## Data model

`docs/backlog.md` — plain markdown bullet list, deliberately **no
frontmatter** (it is not a stage artifact; frontmatter would make it look
like orientation state). Optional single header line linking the protocol
section. Entry grammar (one line per seed):

```markdown
- <seed text> (from: <run-ref>)
- <seed text> (from: <run-ref>) (claimed: <run-ref>)
```

`<run-ref>` ::= `product` | `feature:<slug>` | `maintenance:<slug>` |
`session:<YYYY-MM-DD>`. The `session:` form covers mid-session seeds with no
run closing — the common case. Claimed entries stay in place; the claim
marker is appended, never rewritten over the origin.

## Interfaces & contracts

### protocol.parse_backlog(text)

- Input: the file's text (str).
- Output: list of entries `{text, origin, claimed}` (claimed may be None).
- Failure modes: never raises on malformed input; malformed lines are
  skipped by parse (check_backlog reports them).

### protocol.check_backlog(text)

- Input: the file's text (str).
- Output: list of label-prefixed problem strings
  (`backlog: <line N>: <what's wrong>`), empty when conformant. Non-entry
  lines (header, blanks) are ignored — only `- ` bullets are held to the
  grammar.
- Failure modes: none — malformed input yields problem strings, never
  exceptions (matches the repo's checker contract).

### lint.check_backlog(root)

- Input: repo root path.
- Output: problem strings from `protocol.check_backlog` for
  `docs/backlog.md` when the file exists; `[]` when absent.
- Failure modes: unreadable file → one problem string, no crash.

### Skill prose contracts

- operate: appends only well-formed entries; never rewrites existing lines.
- next: reads the backlog in its two moments only; output is a proposal
  ("unclaimed seeds: …, start one?") — never an orientation input.
- idea: claim = append ` (claimed: <run-ref>)` to the chosen line; the new
  `idea.md` records the seed as its origin.

## Stack & dependencies

- Python 3 stdlib only (`re` for the entry pattern) — repo hard convention.
- Markdown bullet list — boring, diff-friendly, hand-editable.

## Decisions & alternatives

- **Grammar in protocol.py** over lint-only private checker — artifact
  conventions are protocol.py's charter; lint plus tests are already two
  real callers.
- **`session:<date>` origin form** over requiring a run ref — mid-session
  seeds are the common case (idea.md evidence); fake run refs would be
  dishonest, free text would gut the lint.
- **No frontmatter on backlog.md** over stage-artifact-style YAML — the file
  must not look like state; absence of frontmatter is a design signal.
- **Two read moments for next** over no-active-run only — next's
  completed-run step already points at retro seeds; pointing it at the
  backlog (where those seeds now land) closes the loop without touching
  active-run orientation.
- **Claimed entries stay in place** over archive section — simplest honest
  history; revisit only if the file bloats (PRD open question, carried).

## ADRs

None new — this design implements ADR-0029 (provisional). Recommend flipping
ADR-0029 to `accepted` at Ship, since shipping is the confirmation its
status line awaits.
