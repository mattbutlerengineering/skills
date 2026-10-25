---
stage: capture
run: maintenance:one-frontmatter-end
date: 2026-10-24
re-entry: architect
origin:
  - "docs/backlog.md seed (from: maintenance:one-fence-rule): protocol.read_frontmatter returns None for a file opening with a trailing-space fence while gates._skip_frontmatter treats the same file as having frontmatter, and launch_demo._body skips CRLF; claimed in place as maintenance:one-frontmatter-end"
assumptions:
  - "Section set: like docs/fixes/one-fence-rule/defect.md (this seed's origin run and the repo's precedent for a re-entry: architect brief), this brief adds a design question, a scope and success criteria after the template's own sections. None of the template's sections is dropped or reordered."
  - "Brief variant: a defect brief, not a condition brief. The autorun brief files it as a defect (`type:defect`) and the repro shows one detector reaching two answers about one file."
  - "Work already in flight: checked 2026-10-24 with `gh pr list --state open` and each PR's diff. Four open PRs: #1079 edits gates.py's zero-count window and a distant backlog line, #1077, #1074 and #1073 touch no frontmatter code. Nothing matches."
---

# Defect: four owners of where frontmatter ends

## Defect (or Condition)

Four functions in tracked Python each decide where a markdown file's
YAML frontmatter ends. They use four different rules and disagree on
the same text. The seed named three. A mechanical sweep found the
fourth (see Reproduction).

| Owner | Location | Rule it applies |
|---|---|---|
| protocol | `protocol._FRONTMATTER` / `parse_frontmatter` (protocol.py:78, :98-105) | after CRLF normalization, the regex `\A---\n(.*?)\n---\n` (DOTALL): an exact `---` opener, an exact `---` closer, a newline after the closer, and at least one line between them |
| gates | `gates.FRONTMATTER_FENCE` / `_skip_frontmatter` (gates.py:186, :1110-1124) | over `text.splitlines()`, line 0 and the first later line matching `^---\s*$`. Trailing whitespace is allowed, an empty block is allowed, and an unterminated opener means no frontmatter |
| launch_demo | `launch_demo._body` (launch_demo.py:551-557) | the literal `---\n` prefix, then the first `\n---\n` from index 4. No CRLF, no trailing whitespace, no empty block, no closer at end of file |
| knowledge_plane | `knowledge_plane._declared_status` (knowledge_plane.py:581-595) | `lines[0].strip() == "---"` and the first later line whose `strip()` is `---`. Leading and trailing whitespace are allowed, and an unterminated opener runs to end of file as frontmatter |

**Expected:** one rule for "is there frontmatter, and where does the
body start", owned in one place, so every reader gives the same answer
about the same file.

**Observed:** the readers disagree on six of the nine shapes tested.
Inside detectors H and M, gates' fence rule and protocol's parse
disagree about one file. So a dated, grandfathered artifact is judged
as undated.

## Reproduction / Evidence

All runs were against this branch at 9a45a3b (main plus the autorun
brief), read-only on source, from throwaway scripts outside the repo.

**Verdict table.** A throwaway script fed each text below to
`protocol.parse_frontmatter(text)`, `gates._skip_frontmatter(text.splitlines())`,
`launch_demo._body(text)` (the "frontmatter" column means the result
differs from the input) and
`knowledge_plane._declared_status(text.splitlines())`. Each text's
block holds `status: ok`, and its body is `# Body`.

| Shape | protocol | gates | launch_demo | knowledge_plane |
|---|---|---|---|---|
| LF, exact fences | `{'status': 'ok'}` | body at line 3 | frontmatter | `(2, 'ok')` |
| CRLF | `{'status': 'ok'}` | body at line 3 | **no frontmatter** | `(2, 'ok')` |
| opener with trailing space | **None** | body at line 3 | **no frontmatter** | `(2, 'ok')` |
| closer with trailing space | **None** | body at line 3 | **no frontmatter** | `(2, 'ok')` |
| unterminated opener | None | none (0) | no frontmatter | **`(2, 'ok')`** |
| no frontmatter | None | none (0) | no frontmatter | `(0, None)` |
| empty block (two fence lines) | **None** | body at line 2 | **no frontmatter** | `(0, None)` |
| closer at end of file, no newline | **None** | body at line 3 | **no frontmatter** | `(2, 'ok')` |
| opener with leading space | None | none (0) | no frontmatter | **`(2, 'ok')`** |

Only "LF, exact fences" and "no frontmatter" get the same answer from
all four. For an unterminated opener, knowledge_plane is the only one
that reads a frontmatter `status:`, and it would read a `status:` line
from anywhere in the file.

**The divergence inside one detector.** Detector M splits sections
with `_skip_frontmatter` (gates.py:1676) but reads the grandfathering
`date:` through `read_frontmatter` (gates.py:1745). A throwaway script
wrote one `docs/fixes/old/defect.md` into a temp tree twice: frontmatter
dated `2026-01-01` (before `CAPTURE_ADOPTED`, 2026-09-21) and a body
with none of the required sections. `gates.check_capture_completeness(root)`
returned:

- with a `---` opener: `[]` (grandfathered, as designed);
- with a `--- ` opener (one trailing space): five problems, starting
  with `M: docs/fixes/old/defect.md missing required section 'Defect (or Condition)'`.

The section walk skipped the block as frontmatter, but the date read
found no frontmatter. The file then fails closed as undated. Detector
H's roll-up has the same split: `_skip_frontmatter` (gates.py:1215)
against `_rollup_applies`' `parse_frontmatter` (gates.py:1261). On a
verification.md dated `2026-01-01`, `gates._rollup_applies(text)`
returned `False` with a `---` opener and `True` with `--- `, while
`_skip_frontmatter` returned body line 4 for both.

**launch_demo's CRLF gap does not reach the disk path today.**
`launch_demo.render` reads launch.md through `cli.read_file`
(`Path.read_text`, universal newlines). A throwaway script wrote a CRLF
launch.md, read it that way and got `'---\nstage: x\n---\nBody\n'`, and
`_body` returned `'Body\n'`. The CRLF row above fails only when a
caller hands `_body` undecoded text. The trailing-space and
end-of-file rows do reach `render` (launch_demo.py:599).

**Enumerating the class.** An AST sweep listed every string constant
containing `---` in tracked non-test `.py` files. A grep followed for
`frontmatter`, `FRONTMATTER`, `-{3` and escaped dashes. Places that
decide where frontmatter ends:

1. `protocol.py:78` `_FRONTMATTER`, used by `parse_frontmatter` /
   `read_frontmatter`, the seam every other reader imports (gates,
   knowledge_plane, kb, kb_drift, trace, trigger_eval, assembler,
   conductor_run).
2. `gates.py:186` `FRONTMATTER_FENCE`, used by `_skip_frontmatter`
   (gates.py:1110) for detectors H (`verification_sections`, :1215) and
   M (`capture_sections`, :1676).
3. `launch_demo.py:551` `_body`, its own string search.
4. `knowledge_plane.py:588-590` `_declared_status`, an inline `strip()`
   walk for an ADR's frontmatter `status:` fallback.

Payload twins: `factory/templates/tools/factory/{protocol,gates,knowledge_plane}.py`
carry owners 1, 2 and 4 byte for byte (`factory_init.MIRRORS`).
launch_demo.py is not mirrored.

Matches that are not frontmatter-end owners: `gates.SETEXT_UNDERLINE`
(gates.py:129-135, a Setext underline whose comment notes it is
ambiguous with the frontmatter fence), `lint.py:866` (a table
separator), `charter_replay.py:83-89` (prompt delimiters),
`trigger_eval.py:71-101` (writes frontmatter and does not parse it), and
`pr_body_preflight._body` (a pull-request body, an unrelated function).

**Incidence today: zero.** A throwaway script read every tracked `*.md`
file (1010 files, 733 of them opening with a fence line) as raw bytes.
It found:

| Shape | Tracked files |
|---|---|
| opener with trailing whitespace | 0 |
| closer with trailing whitespace | 0 |
| CRLF line endings anywhere (`\r\n` in the bytes) | 0 |
| unterminated opener | 0 |
| empty block | 0 |
| opener with leading whitespace | 0 |
| protocol, gates and launch_demo disagree on the decoded text | 0 |

This is a latent defect, not a live outage. `.gitattributes` sets no
`eol` or `text` rule, so a checkout under `core.autocrlf=true` could
produce CRLF files. protocol and gates both absorb that, as the table
shows.

## Root-cause hypothesis

Hypothesis: four authors on four dates, with no shared owner.
protocol's regex arrived with the protocol module extraction (a6c671f,
#18, 2026-07-02). gates' fence arrived with detector H (fb33432, #128,
2026-07-12), and its docstring claims "frontmatter skipping has one
home" while `protocol` was already imported. launch_demo's `_body` came
with the launch-demo feature (cf060a9, #623, 2026-10-10).
knowledge_plane's walk arrived when the ADR record folded into it
(178e1bd, #757, 2026-10-12). No ADR, review or fix run found records a
choice to differ.

## Blast radius

- **Detectors H and M.** A file with a trailing-space fence, a
  closer at end of file, or an empty block is grandfathering-blind. Its
  `date:` is read as missing, so a pre-cutoff artifact is judged in full
  and `make check` goes red on an honest old file. The reverse (a new
  file escaping a check) needs protocol to find a date that gates does
  not skip. No shape in the table produces that.
- **protocol's other callers.** kb pages, skill frontmatter
  (`skill_frontmatter_problems`), PRD ids for detector C, and the
  orientation fields (`re-entry:`, `outcome:`, `users-observed:`) all
  read through `parse_frontmatter`. A trailing-space fence makes those
  fields vanish. That is protocol's own rule, applied consistently.
- **launch_demo.** A launch.md with a trailing-space fence or a closer
  at end of file has its frontmatter checked as copy by
  `check_storyboard`.
- **knowledge_plane.** An ADR with no `- Status:` line and an
  unterminated or leading-space opener has its status read from a line
  that the other three readers do not treat as frontmatter.
- **Mirrored.** gates, protocol and knowledge_plane ship in the factory
  payload, so every stamped product repo runs owners 1, 2 and 4 in CI.
- **Since:** 2026-07-12 (gates beside protocol). No known occurrence,
  and zero tracked files hit any divergent shape today.

## Ruled out

- **A deliberate difference.** gates' `_skip_frontmatter` docstring
  states the intent of one home. The one-fence-rule run left protocol's
  frontmatter fence out of scope as "a different construct", which
  defers the question and does not choose a different rule. No ADR
  covers a frontmatter fence grammar.
- **CRLF in launch_demo via the disk path.** Universal-newline
  decoding in `cli.read_file` absorbs it (reproduced above). It is not
  reachable through `render` today.
- **Setext underlines.** `SETEXT_UNDERLINE` matches `---` but decides
  heading titles, not frontmatter. `_walk_sections` starts after
  `_skip_frontmatter`'s index, so it is a consumer of the rule, not an
  owner.
- **Live incidence.** 0 of 1010 tracked markdown files hit a divergent
  shape, so no existing artifact's verdict is wrong today.

## The design question: Architect's to answer, not capture's

The autorun brief asks Architect to draft both with a recommended
default:

1. **The rule.** Is a fence line with trailing whitespace a fence?
   Does CRLF count? What do an unterminated opener, an empty block and a
   closer at end of file mean? What about a leading-space opener, which
   only knowledge_plane accepts?
2. **The owner.** The brief recommends `protocol.py` (the ADR-0021 seam
   that gates and knowledge_plane already import). It would own "where
   frontmatter ends", with gates, launch_demo and knowledge_plane as
   thin callers. The interface must serve both a text caller (protocol,
   launch_demo) and a lines caller that needs a body index (gates H and
   M, knowledge_plane).

## Scope

- **In:** one owner for the frontmatter-end rule. The four owners
  above read through it, and their payload twins and the manifest are
  regenerated.
- **Out:** the `key: value` field grammar inside the block (block
  scalars, the YAML indicator checks in `skill_frontmatter_problems`).
  Also out: frontmatter writers (`trigger_eval`), and the Setext and
  fence rules.

## Success criteria

- Every shape in the verdict table gets one answer from all four
  callers. Detector M's repro gives the same result for the `---` and
  `--- ` openers, and so does `_rollup_applies`.
- One definition of the frontmatter fence exists. A grep for
  `FRONTMATTER`, `---` literals and `strip() == "---"` in tracked
  non-test `.py` finds a single owner, plus the non-owners listed above.
- Every existing test passes unchanged. `python3 run_tests.py`,
  `python3 lint.py`, `python3 kb.py drift` and
  `python3 gates.py && python3 gates.py --selftest` are green.
- Verify sweeps every tracked `*.md` file, old against new verdict, and
  reports every change. Today's incidence predicts none.

## Notes

- 2026-10-24: the seed named three owners. The class sweep added
  knowledge_plane's `_declared_status` and two shapes the seed did not
  name (empty block, closer at end of file).
