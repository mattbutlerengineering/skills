---
stage: review
run: maintenance:one-frontmatter-end
date: 2026-10-25
assumptions:
  - "Severity arbitration: autorun-driven, so the Owner was not asked about each finding. The skill's default applies: criticals are fixed before Ship, majors are fixed or deferred, minors may be deferred freely. There are no criticals or majors. All three findings are minor and deferred with reasons, so no code changed in this stage."
  - "Standards filtered to domain factory (the diff touches root tools, factory/** and tests): adr0032-one-way-mirror and stdlib-only, both advisory in docs/standards.json. Neither is touched. The new imports are protocol (stdlib only) and, in a test, ast, re and subprocess."
  - "Scope is `git diff origin/main...HEAD` at fb77fc4, merge base ec8159f. The run's own artifacts were read for their claims but not reviewed as code."
  - "Cross-PR check: open PRs were listed with `gh pr list --state open` and their files. #1079 and #1074 share paths with this branch, and #1077 and #1073 do not. The pair simulation stacked this branch on #1079's head, which already contains origin/main, and then #1074. Conflicts were resolved the way each file's owner resolves them (manifest: `update-manifest`; ADR index: keep both rows), in a detached worktree in the session scratchpad that was removed afterwards."
  - "Date is the UTC date, matching verification.md."
---

# Review: one owner of where frontmatter ends

## Scope

`git diff origin/main...HEAD` (fb77fc4 against merge base ec8159f):
`protocol.py`, `gates.py`, `knowledge_plane.py` and `launch_demo.py`, the
three payload twins under `factory/templates/tools/factory/`,
`factory/manifest.json`, the new `tests/frontmatter_shapes.py`, the additions
to `tests/test_protocol_frontmatter.py`, `tests/test_gates.py`,
`tests/test_knowledge_plane.py` and `tests/test_launch_demo.py`, the pin pair
in `tests/test_dual_membership.py`, the Owner-authorized edit to
`tests/test_eval_trends.py`, ADR-0118 with its index row, and the claimed
backlog seed. I re-read every caller of `parse_frontmatter` and
`read_frontmatter` in tracked non-test Python, not only the changed hunks.
`python3 one_owner.py` was run too. Its one hit near the diff
(`gates.py:319 ARCH_PLAIN_PATH`) predates the run and is outside its scope.

## Findings

### Minor: an empty block changes two consumers' messages, and the design traced neither

- Scenario: a kb page or a `SKILL.md` whose frontmatter is `---` then `---`.
  Before, `parse_frontmatter` returned None. Two callers test `is None`:
  `kb._field_problems` (kb.py:111) and `protocol.skill_frontmatter_problems`
  (protocol.py:191). Each then reported "has no frontmatter block". Now the
  block is `{}`. kb reports "is missing frontmatter field" once for each
  required field, and `kb.check` (kb.py:250) runs the page's link checks.
  The skill check reports "frontmatter name is None, expected '<slug>'" and
  "frontmatter has no description". architecture.md's rule table says only
  "protocol (None to `{}`)", and ADR-0118's Consequences do not name either
  consumer. Every other caller uses `or {}`, so for them None and `{}` are
  the same.
- Standard: none
- Decision: deferred, with no code change. Both consumers still fail
  closed, because the file is still reported. The new messages are the
  accurate ones under `read_frontmatter`'s own contract ("a
  present-but-fieldless block is an empty dict"). No tracked file has an
  empty block: a fresh old-against-new sweep of 1015 tracked `*.md` files
  found 0 changed verdicts. This entry is the record.

### Minor: the count pin has false positives and blind spots that breakdown.md does not log

- Scenario: run in a scratch probe, `fence_definitions` counts each of these
  as a frontmatter fence definition: a unified-diff header test
  (`line.startswith("--- ")`), a horizontal-rule regex
  (`re.compile(r"^-{3,}\s*$")`), and a YAML document split
  (`text.split("\n---\n")`, `partition("\n---\n")`). Code like that, added
  later for a reason that has nothing to do with frontmatter, fails
  `test_the_exact_count_map`. The failure shows only a dict diff. It misses
  three shapes that breakdown.md's blind-spot list leaves out:
  `from re import compile` then `compile(r"^---\s*$")`, a `pattern=` keyword
  argument, and bytes literals (`b"---"`). The list does name `import re as
  r`, run-time construction and dash-run regexes.
- Standard: none
- Decision: deferred. The pin is a tripwire, not a proof. A false positive
  fails loudly, and the fix is one commented map entry, the same treatment
  `lint.py`'s table separator already gets. The missed shapes are unlikely
  spellings in this codebase, which uses `re.compile` with a positional
  pattern throughout. This entry records them next to the logged ones. On
  size: the detector is about 60 lines and the tests about 50. That is
  proportionate. A grep for the deleted names cannot see a re-added
  `startswith("---\n")` copy, and C1's second mutation shows the pin
  catching one. So it is not a cut.

### Minor: a BOM-prefixed opener is still not frontmatter, for every reader

- Scenario: a UTF-8 file that starts with a byte-order mark, then `---`.
  `read_frontmatter` decodes with `utf-8`, not `utf-8-sig`, so `lines[0]` is
  `'﻿---'`, `_FENCE` does not match, and every reader reports no
  frontmatter. The probe shows the same answer from all four readers, before
  and after the change.
- Standard: none
- Decision: deferred, and out of scope. This is consistent behaviour that
  predates the run, not a divergence. 0 tracked `*.md` files start with a
  BOM. Whether a BOM should be stripped is a reading-boundary question for
  `cli.read_file` and `read_frontmatter`, not for the fence rule. It is
  named here as the related cleanup that remains, and not seeded, because
  nothing has hit it.

## Passes with no findings

- **Correctness:**
  - `frontmatter_end` matches ADR-0118's rule on each edge input I probed.
    Empty text and a lone `---` (with or without a newline) give None. A
    `\r`-only file, a `\x85` closer and a form feed after the opener give one
    end, for bare and kept line ends alike. A `|` block scalar parses to the
    same dict as on origin/main.
  - Nothing is quadratic. The owner makes one linear pass. A 10^6-line
    unterminated opener takes `parse_frontmatter` 111 ms (40.7 ms on main)
    and `_body` 113 ms (2.8 ms). A file with no frontmatter now pays for one
    whole-file `splitlines` (6 ms per 10^6 lines, against 2.1 ms). That is
    linear and immaterial at this repo's sizes.
  - `_body` keeps the body exactly. `"".join(text.splitlines(keepends=True))`
    is `text` for any string, so the slice after the closer is the exact
    suffix, for LF and CRLF alike.
  - `gates._skip_frontmatter` is the old loop with the same regex, so it is
    unchanged on every input, as ADR-0118 says.
  - `_declared_status` narrows only to the block. My own sweep (origin/main
    against HEAD, each in its own `python3 -I` process, over every tracked
    `*.md`) found 0 changed verdicts for all four readers. No tracked ADR
    reports differently.
  - The import graph has no cycle. `protocol.py` imports only `re` and
    `pathlib`.
- **Design:** the code matches architecture.md's contracts: one regex,
  signatures unchanged, the index interface, and the deleted names gone. The
  two decisions that outlive the commit, the rule and the new import edge,
  have ADR-0118 (provisional). The 55-to-56 pin change follows the
  precedent of ADR-0110 and ADR-0112 to ADR-0115. ADR-0091's historical
  table was not updated for those ADRs either, so leaving it alone is
  consistent.
- **Security:** pure functions over strings. No new input boundary.
  `launch_demo` still reads through `cli.read_file`. The pin's `git ls-files`
  subprocess has fixed arguments, the same as `tests/test_one_owner.py`.
- **Complexity:** the cut-list has nothing to cut. `frontmatter_end` is 6
  lines with 4 callers. `tests/frontmatter_shapes.py` has 4 consumers. The
  diff adds no `lean:` marker. Shape concerns: none to hand to `deepen`.
- **ADR compliance** (live set from `adr_status.py`): no violation found.
  ADR-0021 (the protocol seam owns the rule) holds. So does ADR-0050: `cmp`
  exits 0 for all three twins, and the manifest is regenerated. ADR-0075
  holds (the guarded read is unchanged). ADR-0091 (partial) holds through
  the dual-membership pair recorded in the pin. ADR-0095 holds:
  `plugin.json` is untouched. So does ADR-0052: the skill contract still
  reports an empty block, as the first finding describes. ADR-0118 is
  provisional and the diff matches its Decision.
- **Cross-PR** (docs/kb/cross-pr-merge-hazards.md):
  - `git merge-tree --write-tree --name-only HEAD origin/fix/a-long-line-stalls-the-gate`
    conflicts in `factory/manifest.json` only. `gates.py`, its twin,
    `tests/test_gates.py` and `docs/backlog.md` auto-merge.
  - `git merge-tree --write-tree --name-only HEAD origin/fix/seen-before-partner`
    conflicts in `docs/adr/README.md` only. Both branches append rows after
    0116, and #1074 also changes 0116's status cell.
  - Chain simulation: in a detached worktree at #1079's head, merge this
    branch. Take #1079's manifest and run `python3 factory_init.py update-manifest`
    (`factory-init: 0 problem(s)`, gates twin `cmp` 0). Then merge #1074 and
    keep both index rows (#1074's 0116 and 0117 rows, then 0118). On that
    tree, `tests: 3827 tests across 118 modules ... 0 problem(s)`,
    `lint: 0 problem(s) across 34 skills`, `drift: 0 problem(s)`,
    `gates: 0 problem(s)` and `selftest: ok`.
  - Both conflicts are mechanical, and the merged tree is green. Whichever
    PR lands second resolves them that way. With #1074's ADR numbered 0117,
    0118 is the right number in either order.
- **Domain passes:** none selected (no changed path matches payments,
  migrations or dependencies).

## Verdict

Ready to ship. There are no critical or major findings, and no finding cites
an enforced standard. Three minors are deferred with reasons above. All five
passes ran, plus the cross-PR pair check. Not run here, and so not covered by
this verdict: detector B and the live CI on a PR event (both run when Ship
opens the PR), and the payload exercised in a stamped repo. Verify already
lists both.
