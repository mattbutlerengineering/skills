# Plan 005: Make `read_frontmatter` handle block-scalar descriptions and CRLF files

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 79b08fc..HEAD -- protocol.py tests/test_frontmatter.py`
> If `read_frontmatter` in `protocol.py` changed since this plan was
> written, compare the "Current state" excerpt against the live code; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug (latent)
- **Planned at**: commit `79b08fc`, 2026-07-03 (refreshed from the 8399f85 original by a /improve re-audit; `read_frontmatter` excerpt re-verified unchanged at HEAD, line refs updated)

## Why this matters

`protocol.py`'s `read_frontmatter` is the one frontmatter parser (ADR-0021)
— lint, the trigger-eval runner, and orientation all read through it. It
splits lines and takes `key: value` pairs, so two well-formed-YAML inputs
parse wrong today: a block scalar (`description: |` followed by indented
lines) yields `description` = `""` — lint then reports a false "has no
description" and `trigger_eval.load_descriptions` refuses to run — and a
CRLF-saved file matches no frontmatter at all (`\A---\n` misses `---\r\n`),
reported misleadingly as "has no frontmatter block". All 11 current skills
use single-line LF descriptions, so this is latent — but the trigger eval's
own `build_project_dir` *writes* block-scalar command files, proving the
format is in the repo's vocabulary; the first contributor to author one in
a SKILL.md gets a wrong diagnostic. Fixing the parser also brings
`build_project_dir`'s multi-line indent join (currently dead code) to life.

## Current state

- `protocol.py:38-56` at commit `79b08fc`:

```python
_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_CHECKBOX = re.compile(r"^\s*[-*+] \[([ xX])\]", re.MULTILINE)


def read_frontmatter(path):
    """Parse a `key: value` frontmatter block into a dict.

    Single error contract: returns None when the file has no frontmatter
    block; a present-but-fieldless block is an empty dict. Callers decide
    what a missing block means for them.
    """
    match = _FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        return None
    return dict(
        (line.split(":", 1)[0].strip(), line.split(":", 1)[1].strip())
        for line in match.group(1).splitlines()
        if ":" in line
    )
```

- Consumers (do not change them; their contracts must keep holding):
  - `lint.check_skills` (`lint.py:46-68`) — `None` → "has no frontmatter
    block"; falsy `description` → "has no description".
  - `trigger_eval.load_descriptions` (`trigger_eval.py:39-50`) — raises
    `ValueError` on `None` or missing description.
  - `trigger_eval.build_project_dir` (`trigger_eval.py:53-69`) — writes
    command files as `description: |` + indented lines via
    `"\n  ".join(description.split("\n"))`; with today's parser a
    multi-line description can never reach it (dead path this plan
    revives).
  - `protocol._ux_skipped` — reads `ux:` from `prd.md` frontmatter.
- Existing frontmatter test coverage is indirect only (fixture trees in
  `tests/test_lint_checkers.py` and `tests/test_orientation.py`); there is
  no direct `read_frontmatter` test module. You will create
  `tests/test_frontmatter.py`.
- Repo conventions: stdlib only (**no YAML library — do not add one**;
  extend the hand parser minimally), plain `unittest`, module docstring
  naming the seam, tests through the public interface
  (`from protocol import read_frontmatter`).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| One test module | `python3 -m unittest tests.test_frontmatter -v` | all pass |
| Tests   | `python3 -m unittest discover tests` | `OK`, exit 0 |
| Lint    | `python3 lint.py` | `lint: 0 problem(s) across 13 skills`, exit 0 |

## Scope

**In scope**:
- `protocol.py` — `_FRONTMATTER` regex and `read_frontmatter` only.
- `tests/test_frontmatter.py` (create).

**Out of scope** (do NOT touch):
- `lint.py`, `trigger_eval.py`, `orientation.py`, `eval_schema.py` — the
  point is that thin callers need no change.
- `next_stage`, `_ux_skipped`, `_implement_complete`, `_CHECKBOX` — same
  module, different responsibilities.
- Full YAML support (flow maps, quoting, `>` folded scalars, comments) —
  explicitly not wanted. Only `|` literal block scalars and CRLF
  normalization.

## Git workflow

- Branch: `fix/frontmatter-block-scalars` off `main`.
- Conventional Commits, e.g. `fix: parse block-scalar values and CRLF in read_frontmatter`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Write the failing tests (RED)

Create `tests/test_frontmatter.py`:

```python
"""Frontmatter seam: protocol.read_frontmatter is the one parser
(ADR-0021) behind lint, orientation, and the trigger-eval runner.

Pins the documented contract (None for no block, {} for an empty block,
key: value pairs) plus the two well-formed inputs the line-splitting
parser used to get wrong: `|` literal block scalars and CRLF line endings.
"""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from protocol import read_frontmatter  # noqa: E402


def write(text):
    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8", newline="")
    handle.write(text)
    handle.close()
    return Path(handle.name)


class TestExistingContract(unittest.TestCase):
    def test_simple_key_values(self):
        path = write("---\nname: idea\ndescription: d\n---\n\nbody\n")
        self.assertEqual(read_frontmatter(path),
                         {"name": "idea", "description": "d"})

    def test_no_block_returns_none(self):
        self.assertIsNone(read_frontmatter(write("body only\n")))

    def test_fieldless_block_returns_empty_dict(self):
        self.assertEqual(read_frontmatter(write("---\n\n---\n\nbody\n")), {})


class TestBlockScalars(unittest.TestCase):
    def test_literal_block_scalar_joins_indented_lines(self):
        path = write("---\n"
                     "name: idea\n"
                     "description: |\n"
                     "  first line\n"
                     "  second line\n"
                     "---\n\nbody\n")
        self.assertEqual(read_frontmatter(path)["description"],
                         "first line\nsecond line")

    def test_key_after_block_scalar_still_parses(self):
        path = write("---\n"
                     "description: |\n"
                     "  multi\n"
                     "name: idea\n"
                     "---\n\nbody\n")
        self.assertEqual(read_frontmatter(path),
                         {"description": "multi", "name": "idea"})


class TestLineEndings(unittest.TestCase):
    def test_crlf_file_parses_like_lf(self):
        path = write("---\r\nname: idea\r\ndescription: d\r\n---\r\n\r\nbody\r\n")
        self.assertEqual(read_frontmatter(path),
                         {"name": "idea", "description": "d"})


if __name__ == "__main__":
    unittest.main()
```

**Verify**: `python3 -m unittest tests.test_frontmatter -v` → the three
`TestExistingContract` tests PASS; the block-scalar and CRLF tests FAIL
(block scalar: description is `""`; CRLF: result is `None`).

### Step 2: Extend the parser (GREEN)

In `protocol.py`, replace `read_frontmatter` (keep `_FRONTMATTER`
unchanged) with:

```python
def read_frontmatter(path):
    """Parse a `key: value` frontmatter block into a dict.

    Single error contract: returns None when the file has no frontmatter
    block; a present-but-fieldless block is an empty dict. Callers decide
    what a missing block means for them. Values may be `|` literal block
    scalars (following indented lines joined with newlines); CRLF files
    are normalized before matching.
    """
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = _FRONTMATTER.match(text)
    if not match:
        return None
    fields = {}
    key = None
    block_lines = None
    for line in match.group(1).splitlines():
        if block_lines is not None and (line.startswith("  ") or not line.strip()):
            block_lines.append(line[2:])
            continue
        if key is not None and block_lines is not None:
            fields[key] = "\n".join(block_lines).rstrip("\n")
        key = None
        block_lines = None
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if value == "|":
            block_lines = []
        else:
            fields[key] = value
    if key is not None and block_lines is not None:
        fields[key] = "\n".join(block_lines).rstrip("\n")
    return fields
```

Behavior notes (these ARE the spec for this step):
- Only `|` starts a block scalar; any other value keeps today's exact
  behavior (including `value.strip()`).
- Continuation lines are those indented ≥2 spaces (2 spaces stripped) or
  blank; the first non-indented line ends the block and is processed
  normally.
- Trailing newlines of a block value are stripped (`rstrip("\n")`), so a
  single-line block scalar equals its plain-value spelling.

**Verify**: `python3 -m unittest tests.test_frontmatter -v` → all 6 pass.

### Step 3: Full gates

The existing indirect coverage is the real regression net here — every
lint-checker and orientation fixture parses through this function.

**Verify**: `python3 -m unittest discover tests` → all pass;
`python3 lint.py` → `lint: 0 problem(s) across 13 skills`.

### Step 4: Commit

```bash
git add protocol.py tests/test_frontmatter.py
git commit -m "fix: parse block-scalar values and CRLF in read_frontmatter"
```

## Test plan

- New `tests/test_frontmatter.py` (6 tests): existing contract pinned
  first (simple pairs, no-block → None, empty block → {}), then the two
  fixed behaviors (block scalar joined, key-after-block, CRLF).
- Existing suites (`test_lint_checkers`, `test_orientation`,
  `test_eval_schema`, trigger tests) must stay green untouched — they are
  the proof the thin callers didn't notice the change.

## Done criteria

- [ ] `python3 -m unittest tests.test_frontmatter -v` → 6 tests pass
- [ ] `python3 -m unittest discover tests` exits 0 with no other file modified to make it so
- [ ] `python3 lint.py` exits 0
- [ ] `git status --short` shows only `protocol.py` and `tests/test_frontmatter.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `read_frontmatter` no longer matches the "Current state" excerpt.
- Any existing test fails after Step 2 — the parser change leaked into a
  caller's contract; report the failing test and diff rather than patching
  the caller.
- You find yourself wanting a YAML library or supporting `>` folded
  scalars/quoting — that's scope creep; the repo is stdlib-only and this
  plan covers `|` and CRLF only.

## Maintenance notes

- This revives `build_project_dir`'s multi-line indent join in
  `trigger_eval.py` — the first multi-line SKILL.md description will now
  flow through it. A follow-up trigger-eval run (`--only <slug>`) is worth
  doing when that first multi-line description lands.
- If a future contributor needs folded scalars (`>`) or quoted values, that
  is the moment to discuss a real parser in an ADR — don't grow this
  function past block scalars.
- Reviewer should scrutinize: the end-of-block flush (both mid-loop and
  after the loop) and that a blank line inside a block is preserved as an
  empty string line.
