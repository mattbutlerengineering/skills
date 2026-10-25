---
stage: verify
run: maintenance:one-frontmatter-end
date: 2026-10-25
assumptions:
  - "Criteria source: there is no prd.md (maintenance run, re-entry: architect). The list is defect.md's four success criteria (S1-S4) plus every breakdown.md Accept clause they do not already cover (B1-B4)."
  - "Old means origin/main at ec8159f, the branch's merge base (re-fetched during this stage, unchanged). Each probe below loaded its readers from a git archive of that commit, or of HEAD, into a throwaway directory outside the repo, each side in its own `python3 -I` process. Probe scripts were written fresh for this stage; none of Implement's C2 scripts was reused."
  - "The sweep reads every tracked *.md file twice: as undecoded bytes with no newline translation, and through universal newlines as `cli.read_file` reads it. A verdict counts as changed if either reading differs."
  - "The brief's suite list named `tests.test_protocol`, which does not exist. The protocol suites that do exist and touch frontmatter were run in its place: `tests.test_protocol_frontmatter`, `tests.test_protocol_accessors` and `tests.test_protocol_conformance`."
  - "S3's 'every existing test passes unchanged' is judged with two recorded exceptions: the dual-membership pin's designed pair (architecture.md assumptions, breakdown B2) and the Owner-authorized edit to tests/test_eval_trends.py (breakdown.md, Design gaps found, 2026-10-25). Both are disclosed in S3, not hidden in the verdict."
  - "trigger_eval.py, charter_replay.py and `claude plugin eval` were not run: they are paid, on-demand model runs that no criterion names."
---

# Verification: one owner of where frontmatter ends

Verified at `6402fd3`: twelve commits on top of `origin/main` at
`ec8159f`.

## Summary

**8 criteria: 8 PASS, 0 FAIL.** Every criterion was run. One function,
`protocol.frontmatter_end`, now decides where frontmatter ends, and
`parse_frontmatter`, `_skip_frontmatter`, `launch_demo._body` and
`knowledge_plane._declared_status` each give its answer on all nine
rule-table shapes. On origin/main 7 of those 9 rows disagree. Detector M's
and `_rollup_applies`' reproductions now give one answer for a `---` and a
`--- ` opener. The old-against-new sweep over 1014 tracked markdown files
found 0 changed verdicts, as defect.md predicted. Two existing tests were
edited, both under recorded authority (S3). Things this stage did not
check are under Not verified.

## Criteria & evidence

### S1: one answer from all four callers on every shape; M and the roll-up agree across openers

- Check: an independent rule-table walk. A probe built each of
  architecture.md's nine shapes itself (block `status: ok`, body
  `# Body`, not read from `tests/frontmatter_shapes.py`). It called the
  owner with both `splitlines()` and `splitlines(keepends=True)`, then each
  caller, and compared every answer with the rule table: `parse_frontmatter`
  is None exactly when the end is None (`{}` for the empty block),
  `_skip_frontmatter` is `end + 1` or 0, `_body` returns the text after the
  closer or the text unchanged, and `_declared_status` reads `(2, 'ok')`
  exactly when the block holds it. Then defect.md's detector M repro (a
  `docs/fixes/old/defect.md` dated 2026-01-01 with no required sections, in
  a temp tree) and a verification.md dated 2026-01-01 for
  `_rollup_applies`, each under both openers. The same probe ran against
  origin/main to show it can see a difference.
- Evidence (HEAD):
  ```
  ok  LF, exact fences            owner=(2, 2) parse={'status': 'ok'} skip=3 body_stripped=True status=(2, 'ok')
  ok  CRLF                        owner=(2, 2) parse={'status': 'ok'} skip=3 body_stripped=True status=(2, 'ok')
  ok  opener trailing ws          owner=(2, 2) parse={'status': 'ok'} skip=3 body_stripped=True status=(2, 'ok')
  ok  closer trailing ws          owner=(2, 2) parse={'status': 'ok'} skip=3 body_stripped=True status=(2, 'ok')
  ok  unterminated opener         owner=(None, None) parse=None skip=0 body_stripped=False status=(0, None)
  ok  no frontmatter              owner=(None, None) parse=None skip=0 body_stripped=False status=(0, None)
  ok  empty block                 owner=(1, 1) parse={} skip=2 body_stripped=True status=(0, None)
  ok  closer at EOF, no newline   owner=(2, 2) parse={'status': 'ok'} skip=3 body_stripped=True status=(2, 'ok')
  ok  opener leading ws           owner=(None, None) parse=None skip=0 body_stripped=False status=(0, None)
  rows disagreeing with the rule table: 0
  opener '---': M problems=0 first=[]  _rollup_applies=False  _skip=4
  opener '--- ': M problems=0 first=[]  _rollup_applies=False  _skip=4
  ```
  The same probe against origin/main:
  ```
  ok  LF, exact fences            owner=n/a parse={'status': 'ok'} skip=3 body_stripped=True status=(2, 'ok')
  BAD CRLF                        owner=n/a parse={'status': 'ok'} skip=3 body_stripped=False status=(2, 'ok')
  BAD opener trailing ws          owner=n/a parse=None skip=3 body_stripped=False status=(2, 'ok')
  BAD closer trailing ws          owner=n/a parse=None skip=3 body_stripped=False status=(2, 'ok')
  BAD unterminated opener         owner=n/a parse=None skip=0 body_stripped=False status=(2, 'ok')
  ok  no frontmatter              owner=n/a parse=None skip=0 body_stripped=False status=(0, None)
  BAD empty block                 owner=n/a parse=None skip=2 body_stripped=False status=(0, None)
  BAD closer at EOF, no newline   owner=n/a parse=None skip=3 body_stripped=False status=(2, 'ok')
  BAD opener leading ws           owner=n/a parse=None skip=0 body_stripped=False status=(2, 'ok')
  rows disagreeing with the rule table: 7
  opener '---': M problems=0 first=[]  _rollup_applies=False  _skip=4
  opener '--- ': M problems=5 first=["M: docs/fixes/old/defect.md missing required section 'Defect (or Condition)'"]  _rollup_applies=True  _skip=4
  ```
  The architecture's extra shapes, HEAD only (each matches the end the
  architecture names):
  ```
  empty block, later ---   end=1 keepends=1 expected=1 parse={} skip=2 body_stripped=True status=(0, None)
  indented closer          end=None keepends=None expected=None parse=None skip=0 body_stripped=False status=(0, None)
  tab after opener         end=2 keepends=2 expected=2 parse={'status': 'ok'} skip=3 body_stripped=True status=(2, 'ok')
  lone CR                  end=2 keepends=2 expected=2 parse={'status': 'ok'} skip=3 body_stripped=True status=(2, 'ok')
  empty text               end=None keepends=None expected=None parse=None skip=0 body_stripped=False status=(0, None)
  single ---               end=None keepends=None expected=None parse=None skip=0 body_stripped=False status=(0, None)
  ```
- Result: PASS

### S2: one definition of the frontmatter fence

- Check: `git grep` over tracked non-test `.py`, root and payload, for the
  deleted names, the deleted `strip()` walk and launch_demo's old string
  search, then every caller of the owner, then the quoted `---` literals
  and dash regexes that remain.
- Evidence:
  ```
  $ git grep -nE '\b_FRONTMATTER\b|FRONTMATTER_FENCE' -- '*.py' ':!tests/*'
  (exit 1)
  $ git grep -nF 'strip() == "---"' -- '*.py' ':!tests/*'
  (exit 1)
  $ git grep -nE 'startswith\("---|find\("\\n---' -- '*.py' ':!tests/*'
  (exit 1)
  $ git grep -n 'FRONTMATTER' -- '*.py' ':!tests/*' ':!factory/templates/*'
  gates.py:274:FRONTMATTER_ISO_DATE = re.compile(
  gates.py:1249:    iso = FRONTMATTER_ISO_DATE.match(value)
  gates.py:1396:# grandfathered — fail closed through _grandfathered (FRONTMATTER_ISO_DATE),
  knowledge_plane.py:537:_FRONTMATTER_STATUS = re.compile(r"^status:\s*(.*?)\s*$")
  knowledge_plane.py:592:            match = _FRONTMATTER_STATUS.match(line)
  $ git grep -nE 'frontmatter_end\(' -- '*.py' ':!tests/*'
  factory/templates/tools/factory/gates.py:1119:    end = frontmatter_end(lines)
  factory/templates/tools/factory/knowledge_plane.py:589:    end = frontmatter_end(lines)
  factory/templates/tools/factory/protocol.py:89:def frontmatter_end(lines):
  factory/templates/tools/factory/protocol.py:120:    end = frontmatter_end(lines)
  gates.py:1119:    end = frontmatter_end(lines)
  knowledge_plane.py:589:    end = frontmatter_end(lines)
  launch_demo.py:556:    end = frontmatter_end(lines)
  protocol.py:89:def frontmatter_end(lines):
  protocol.py:120:    end = frontmatter_end(lines)
  ```
  Every remaining `---` in root non-test `.py` code (comment-only lines
  dropped by the trailing `grep -v`):
  ```
  $ git grep -nF -e '---' -- '*.py' ':!tests/*' ':!factory/templates/*' | grep -vE '^[a-z_]+\.py:[0-9]+:\s*#' | cut -c1-110
  charter_replay.py:83:--- YOUR CHARTER ---
  charter_replay.py:86:--- YOUR WORK ORDER ---
  charter_replay.py:89:--- END ---
  gates.py:1085:    ===/--- underline beneath it. Callers rule out fenced content first. A list
  gates.py:1086:    item or block quote is not a title: `- item` over `---` is a list followed
  gates.py:1112:    after a closing `---` fence, when the artifact opens with a YAML
  gates.py:1153:        if underlined:  # the ===/--- under a Setext title, already consumed
  gates_selftest.py:47:        "---\nstage: prd\nid: PRD-0001\n---\n# PRD\n", encoding="utf-8")
  gates_selftest.py:70:        "| ADR | Decision | Status |\n|-----|----------|--------|\n"
  gates_selftest.py:153:        "---\nstage: capture\nrun: maintenance:demo\n"
  [... 13 more gates_selftest.py fixture-text lines, same shape ...]
  lint.py:866:        if stage.lower() in ("stage", "---"):
  protocol.py:81:_FENCE = re.compile(r"^---\s*$")
  trigger_eval.py:71:            f"---\n"
  trigger_eval.py:74:            f"---\n\n"
  trigger_eval.py:97:            f"---\n"
  trigger_eval.py:101:            f"---\n\n"
  ```
  `protocol._FENCE` is the one owner. The rest are non-owners.
  `charter_replay.py`'s prompt delimiters and `lint.py:866`'s table
  separator are listed in defect.md. The `gates.py` lines are docstrings
  and a Setext comment. `trigger_eval.py` writes frontmatter, which
  defect.md also lists. `gates_selftest.py` is fixture text, which defect.md
  does not list: it writes fixture artifacts and parses none.
  `gates.SETEXT_UNDERLINE` (`-+`) holds no literal `---` and is the Setext
  non-owner defect.md lists. The two `FRONTMATTER*` names left are a date
  grammar and a field regex, not fences.
- Result: PASS

### S3: existing tests pass unchanged, and the battery is green

- Check: list every removed line under `tests/` in
  `git diff origin/main...HEAD`, then run the battery and the targeted
  suites.
- Evidence (removed test lines):
  ```
  -# 55 pairs over nine mirrored modules (ADR-0097 added fast_path to the
  -# added eval_trends to the cli.py row). The
  -        "board", "dashboard", "decompose_signals", "kb", "kb_drift", "lint",
  -        "trigger_eval",
  -    def test_the_pin_holds_the_eval_trends_edge_and_55_pairs(self):
  -        self.assertEqual(len(pinned), 55)
  -from protocol import (SKILL_DESCRIPTION_LIMIT, read_frontmatter,  # noqa: E402
  -                      skill_frontmatter_problems, skill_path)
  ```
  These are three changes. In `tests/test_dual_membership.py` the
  `("launch_demo", "protocol")` pair was added, the designed change
  ADR-0118 records (55 to 56 pairs). In `tests/test_eval_trends.py` the
  count assertion was dropped and the method renamed: the Owner's in-session
  decision "Drop the count, keep assertIn", recorded in breakdown.md and
  committed alone as 976ef33. In `tests/test_protocol_frontmatter.py` the
  import list was widened. No other existing test line was removed or
  changed.
  ```
  $ python3 run_tests.py; echo "run_tests exit=$?"
  run_tests exit=0
  tests: 3816 tests across 118 modules in 26.5s on 8 workers, 0 problem(s)
  $ python3 lint.py
  lint: 0 problem(s) across 34 skills
  $ python3 kb.py drift
  drift: 0 problem(s)
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  $ python3 -m unittest tests.test_protocol_frontmatter tests.test_protocol_accessors \
      tests.test_protocol_conformance tests.test_gates tests.test_launch_demo \
      tests.test_knowledge_plane tests.test_dual_membership tests.test_eval_trends
  Ran 574 tests in 7.933s
  OK
  ```
- Result: PASS

### S4: old-against-new sweep over every tracked markdown file

- Check: an independent sweep. `git ls-files '*.md'` gave the list. Both
  origin/main's and HEAD's `*.py` were extracted with `git archive`, and
  each side ran in its own `python3 -I` process. For every file, under both
  readings (undecoded and universal newlines), it recorded
  `parse_frontmatter(text)`, `_skip_frontmatter(lines)`, `_body(text)` and
  `_declared_status(lines)`, then compared the two sides field by field. The
  first two lines confirm each side loaded its own tree.
- Evidence:
  ```
  old modules: ['old']
  new modules: ['new']
  files: 1014, with frontmatter (new _skip_frontmatter > 0): 736
  parse: 0 changed []
  skip: 0 changed []
  body: 0 changed []
  status: 0 changed []
  total changed verdicts: 0
  ```
  S1's origin/main run shows the same two module sets giving different
  answers on 7 synthetic shapes, so a zero here is not a blind instrument.
  It reflects defect.md's incidence count: no tracked file is in a
  divergent shape.
- Result: PASS

### B1: the regression tests are red on the old code and green on the new (A1-A2, B1-B3)

- Check: this branch's `tests/frontmatter_shapes.py` and its four edited
  test modules were copied into a `git archive` of origin/main, and the new
  test classes were run there. B1's `_skip_frontmatter` pin is a
  characterization pin (breakdown assumptions), so it is expected green on
  both. The same classes on HEAD are inside S3's runs.
- Evidence (origin/main code, new tests):
  ```
  FAIL: test_every_shape (tests.test_launch_demo.TestBody.test_every_shape) (shape='crlf')
  FAIL: test_every_shape (tests.test_launch_demo.TestBody.test_every_shape) (shape='opener with trailing whitespace')
  FAIL: test_every_shape (tests.test_launch_demo.TestBody.test_every_shape) (shape='closer with trailing whitespace')
  FAIL: test_every_shape (tests.test_launch_demo.TestBody.test_every_shape) (shape='empty block')
  FAIL: test_every_shape (tests.test_launch_demo.TestBody.test_every_shape) (shape='closer at end of file, no newline')
  FAIL: test_every_shape (tests.test_launch_demo.TestBody.test_every_shape) (shape='empty block with a later fence line')
  FAIL: test_every_shape (tests.test_launch_demo.TestBody.test_every_shape) (shape='tab after the opener')
  FAIL: test_every_shape (tests.test_launch_demo.TestBody.test_every_shape) (shape='lone carriage returns')
  FAIL: test_every_shape (tests.test_knowledge_plane.TestDeclaredStatusFallback.test_every_shape) (shape='unterminated opener')
  FAIL: test_every_shape (tests.test_knowledge_plane.TestDeclaredStatusFallback.test_every_shape) (shape='opener with leading whitespace')
  FAIL: test_every_shape (tests.test_knowledge_plane.TestDeclaredStatusFallback.test_every_shape) (shape='indented closer')
  FAIL: test_a_grandfathered_capture_brief_is_silent_under_either_opener (tests.test_gates.TestOneFrontmatterAnswer...) (opener='--- ')
  FAIL: test_a_grandfathered_verification_skips_the_rollup_under_either_opener (tests.test_gates.TestOneFrontmatterAnswer...) (opener='--- ')
  Ran 5 tests in 0.005s
  FAILED (failures=13)
  $ python3 -m unittest tests.test_protocol_frontmatter
  ImportError: cannot import name 'frontmatter_end' from 'protocol'
  FAILED (errors=1)
  ```
  The per-shape counts match Implement's notes: launch_demo 8, knowledge_plane
  3, gates 2 (the `--- ` opener only), and protocol's suite fails to import.
- Result: PASS

### B2: the shape table and the owner contract (A1)

- Check: list `tests/frontmatter_shapes.SHAPES`, then run
  `tests.test_protocol_frontmatter`.
- Evidence:
  ```
  15
    lf exact fences -> 2
    crlf -> 2
    opener with trailing whitespace -> 2
    closer with trailing whitespace -> 2
    unterminated opener -> None
    no frontmatter -> None
    empty block -> 1
    closer at end of file, no newline -> 2
    opener with leading whitespace -> None
    empty block with a later fence line -> 1
    indented closer -> None
    tab after the opener -> 2
    lone carriage returns -> 2
    empty text -> None
    a single fence line -> None
  Ran 25 tests in 0.321s
  OK
  ```
  These are the nine rule-table rows with the table's ends, plus the six
  extra shapes the Accept names.
- Result: PASS

### B3: the counted pin holds one fence definition and catches a second (C1)

- Check: run `TestOneFenceDefinition`. Then re-run C1's mutation
  independently: append `FRONTMATTER_FENCE = re.compile(r"^---\s*$")` to
  `gates.py`, run the class, restore the file with `git checkout -- gates.py`,
  run it again, and confirm the tree is clean.
- Evidence:
  ```
  test_the_detector_sees_each_copy_shape (...TestOneFenceDefinition...) ... ok
  test_the_exact_count_map (...TestOneFenceDefinition...) ... ok
  test_the_known_non_owners_count_zero (...TestOneFenceDefinition...) ... ok
  --- mutated:
  FRONTMATTER_FENCE = re.compile(r"^---\s*$")
  -  'gates.py': ['^---\\s*$'],
  Ran 3 tests in 0.313s
  FAILED (failures=1)
  --- restored:
  Ran 3 tests in 0.318s
  OK
  $ git status --porcelain
  (empty)
  ```
- Result: PASS

### B4: payload twins, manifest and the dual-membership pair (A1-B3, C2)

- Check: `cmp` each mirrored root file against its
  `factory/templates/tools/factory/` twin. Confirm launch_demo.py has no
  twin and no `.orig`/`.rej` file is untracked. Run a fresh
  `python3 factory_init.py update-manifest` and check
  `git status --porcelain`. Read the pin set's size and the new pair.
- Evidence:
  ```
  cmp protocol.py exit=0
  cmp gates.py exit=0
  cmp knowledge_plane.py exit=0
  ls: factory/templates/tools/factory/launch_demo.py: No such file or directory
  $ git ls-files -o --exclude-standard | grep -E '\.(orig|rej)$'
  orig/rej grep exit=1
  $ python3 factory_init.py update-manifest
  factory-init: 0 problem(s)
  $ git status --porcelain
  porcelain-end
  pairs: 56 True
  ```
  (`porcelain-end` is the echo placed after `git status`: nothing printed
  before it. `True` means `("launch_demo", "protocol")` is in
  `ROOT_ONLY_IMPORTS_MIRRORED`.)
- Result: PASS

## Failures

None.

## Not verified

- Detector B and the live CI run on a PR event have not run. They run when
  Ship opens the PR. `gates.py` skips B locally without an event payload.
- The pairwise merge with open PR #1079, which also edits `gates.py`, was
  not checked. Ship chain-checks that pair with merge-tree
  (docs/kb/cross-pr-merge-hazards.md).
- The payload was not exercised in a stamped product repo. Byte equality
  with root (B4) and detector E are the only evidence for the mirrored
  copies.
- ADR-0118's number was checked against main only. origin/main's last ADR
  is 0116, but open PR #1074 claims 0117. Ship confirms the number before
  release, per architecture.md.
- `trigger_eval.py`, `charter_replay.py` and `claude plugin eval` were not
  run. They are paid, on-demand model runs that no criterion names.
