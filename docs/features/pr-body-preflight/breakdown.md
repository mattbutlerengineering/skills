---
stage: decompose
run: feature:pr-body-preflight
date: 2026-10-16
assumptions:
  - "No live review of the cut: milestone boundaries and sizing are the skill's own defaults, taken from its guidance (each milestone independently demonstrable, one item per sitting, vertical slices where the architecture allows). Milestone 1 is the gates.py extraction, because B's body rule becomes callable on a string with CI behaviour unchanged and that can be shown on its own. Milestone 2 is the hook, cut into three test-first slices: literal bodies, then heredoc / body-file / unreadable shapes, then the registration."
  - "Test-first ordering follows the repo's TDD rule: each implementation item is blocked by a tests item whose Accept is that its new cases run and fail against the tree before the implementation lands."
  - "No work-order ids and no (tracker: #N) markers: the brief seeds no issues and allows no tracker interaction before Ship, and dispatch mirrors one way (ADR-0032). The PRD carries no id, so detectors A and O have nothing to cite. Rows are plain items."
  - "The architecture's fixture list is split across the two hook test items by the body-recovery step each case exercises. The split is the decomposer's; every listed case appears exactly once."
  - "The catch-all fail-open contract (any exception after stdin is read gives exit 0 with a note) is pinned by a fixture that makes gates.pr_body_problems raise. The architecture states the contract but names no fixture for it; the fixture is derived from the contract, not added scope."
  - "Two design gaps were found (see Design gaps found). They are recorded, not designed around. The breakdown is committed anyway so the stage's state is not held by one checkout alone (ADR-0100). Implement should not start until Architect has resolved both gaps and this breakdown is revised to match."
  - "Revision 2026-10-16: both design gaps are resolved by Architect's re-entry (commit 766633c, ADR-0106). The item list, milestones and blocking edges are unchanged; the revision rewrites the Accept lines the amendment touched. No ADR item is added, because ADR-0106 is already written and committed by Architect. Only the pin update in tests/test_dual_membership.py is scheduled, on the Hook core item."
  - "Revision 2026-10-16: the two main-adapter tests the amendment names (main([], stdin=io.StringIO(...)) with stderr captured, and main([\"x\"]) giving exit 0 with the usage text) go in the Literal-body replay tests item, because the Hook core item is the one that adds main. A stdin read failure is pinned there too, by a stdin object whose read raises, since the amendment states the contract (exit 0 with a note) but names no fixture."
  - "Revision 2026-10-16: the delegation test's sentinel case asserts exit 2 and that the sentinel's lines are on stderr; it does not pin the docs/kb/pr-body-contract.md pointer line, which the failing-body cases already pin."
  - "Revision 2026-10-16: the earlier decompose commit's subject said eight items; there are nine. This revision's subject states nine."
---

# Breakdown: PR-body preflight hook

Progress lives in the checkboxes below. Implement checks items off as their
acceptance criteria are met. Every implementation item is blocked by the
tests item that pins it.

## Milestone 1: detector B's body rule has one owner that takes a string

When this milestone is done, `gates.pr_body_problems(body)` returns B's
strings for any body. `check_pr_traceability` delegates to it, and CI's B
output is unchanged.

- [x] **pr_body_problems tests** — direct cases for `gates.pr_body_problems` in `tests/test_gates.py`, beside `TestPrTraceability` — size:S
  - Accept: new cases assert the exact output for: a body with a four-digit `WO-` token and a `Closes #N` line (`[]`); a `No work order: <reason>` line and a `Closes #N` line (`[]`); the work-order line missing (`["B: PR body cites no work-order id"]`); the closing line missing (`["B: PR body has no Closes #N link"]`); both missing, and `""`, (both strings, in that order). Run against the tree before the extraction, they fail because `gates` has no `pr_body_problems`.
  - Blocked by: —
- [x] **Extract gates.pr_body_problems** — move the body logic out of `check_pr_traceability` unedited; `check_pr_traceability` keeps the event read, the silent skip, the `B: <error>` path and `or ""`, and calls the new function — size:S
  - Accept: the pr_body_problems tests pass. The existing `TestPrTraceability` cases and `gates_selftest`'s B cases pass unchanged (`python3 gates.py --selftest` prints `gates: 0 problem(s)`). `WO_TOKEN` and `CLOSES_TOKEN` are still defined only in `knowledge_plane.py` and `NO_WO_DECLARATION` only in `gates.py`, and the two problem strings appear once each in `gates.py`. Stray `.orig`/`.rej` files are deleted first, then `python3 factory_init.py update-manifest` runs and the manifest is committed with the change (`docs/kb/manifest-regen.md`). Detector E passes and `tests/test_factory_init.py` passes.
  - Blocked by: pr_body_problems tests

## Milestone 2: a non-conforming `gh pr create` body is refused before the PR exists

When this milestone is done, a session in this repo that runs
`gh pr create` with a readable failing body gets exit 2 and B's strings,
and nothing else is ever blocked.

- [x] **Literal-body replay tests** — `tests/test_pr_body_preflight.py`, replaying complete hook payloads (JSON with `tool_name: "Bash"`, `tool_input.command` and `cwd`) through the pure seam as `pr_body_preflight.preflight(json.dumps(payload))`, which returns `(exit_code, stderr_lines)` — size:M
  - Accept: the module holds these cases, each asserting the returned exit code and the exact stderr lines: a passing literal `--body` (exit 0, silent); the work-order line missing, the closing line missing, and both missing (exit 2, stderr equal to `gates.pr_body_problems(body)` for the same body, then one line naming `docs/kb/pr-body-contract.md`); the `-b`, `--body=V`, `-bV` and `-b=V` spellings (judged like `--body`); a compound `cd x && gh pr create --body …` (judged); two commands separated by a newline, one of them a failing `gh pr create` (exit 2); an unclosed quote (exit 0, note); a non-gh command, `echo "gh pr create"` and `git commit -m "gh pr create"` (exit 0, the last two with the `saw "gh pr create" but found no such command` note); a non-JSON payload, a non-object payload and a payload with no string command (exit 0, silent); a payload where `gates.pr_body_problems` is patched to raise (exit 0, note). One delegation test patches `gates.pr_body_problems` to return a sentinel list for a body that would pass, and asserts exit 2 with the sentinel's lines on stderr, so the hook judges through B's one owner and not a copy (it replaces the earlier identity test, which the lazy `gates` import makes impossible). Three adapter tests drive `main`: `main([], stdin=io.StringIO(payload))` with stderr captured gives the same code and lines as `preflight` for a failing body; `main(["x"])` returns 0 with the usage text on stderr; a `stdin` whose `read` raises gives 0 and a `pr-body-preflight: not checked — <reason>` note. The module defines no function taking only `args` that answers a gh command (`tests/test_fake_gh.py` walks `tests/`). Before the script exists the module fails on import.
  - Blocked by: Extract gates.pr_body_problems
- [x] **Hook core: pre-filter, tokenize, split, literal body** — root-level `pr_body_preflight.py` as a `factory` verb: a pure `preflight(payload_text) -> (exit_code, stderr_lines)` seam, a thin `main(argv, stdin=None)` adapter and `__main__` as `sys.exit(main(sys.argv[1:]))`, implementing body-recovery steps 1, 3, 4, 5 and the literal branch of 6 from the architecture — size:M
  - Accept: the literal-body replay tests pass. `factory.VERBS` gains the row `"pr-body-preflight": ("pr_body_preflight", "argv")`, and the module docstring's first line is its `pr-body-preflight: …` index line; `tests/test_factory_cli.py` passes unchanged. `main` with a non-empty `argv` writes the docstring usage to stderr and returns 0; otherwise it reads `stdin`, or `sys.stdin` looked up at call time when `stdin` is None, passes the text to `preflight`, writes its lines to stderr and returns its code, and a failure reading stdin returns 0 with a note. The catch-all runs inside `preflight`. `tests/test_dual_membership.py`'s pin gains the pairs `(pr_body_preflight, gates)` and `(pr_body_preflight, cli)` and its comment's count reads 43 pairs, per ADR-0106, and the test passes. `.claude/settings.json`'s command still runs the script by filename, not through `factory.py`. A command lacking any of the substrings `gh`, `pr`, `create` returns 0 before `gates` is imported (`gates` is imported inside the candidate path, not at module top). The tokenizer is `shlex.shlex(posix=True, punctuation_chars=";&|()<>\n")` with `whitespace_split=True`, `whitespace=" \t"` and `commenters=""`. A `gh pr create` is recognised only after leading `NAME=value` assignments, with `gh` or a path ending in `/gh`, and `bash -c`, `env`, `xargs` and `command` prefixes are not looked through. Every exception after stdin is read gives exit 0 with a `pr-body-preflight: not checked — <reason>` note. The script imports only the standard library, `gates` and `cli`, and it is not in `factory_init.MIRRORS`.
  - Blocked by: Literal-body replay tests
- [x] **Heredoc, body-file and unreadable-shape replay tests** — further cases in `tests/test_pr_body_preflight.py`, with body files in a temp directory used as the payload `cwd`, each replayed as `pr_body_preflight.preflight(json.dumps(payload))` — size:M
  - Accept: the module adds these cases, each asserting the returned exit code and exact stderr lines: `--body-file` and `-F` with a real file, one passing and one failing (judged); `--body-file` with a missing file (exit 0, note); a relative body-file path with no `cwd` in the payload (exit 0, note); `--body "$(cat file)"` and `--body "$(< file)"` (judged as that file); a quoted-delimiter heredoc body (`$(cat <<'EOF' … EOF)`) holding inner `"` and `'` (judged on the verbatim text, so a body ending `#12"` still satisfies B's word boundary); an unquoted-delimiter heredoc holding `$X` (exit 0, note); an unquoted-delimiter heredoc with no `$` or backtick (judged); a `--body` value holding `$VAR` or a backtick (exit 0, note); `cd x && gh pr create --body-file f` (exit 0, note, because the file is read only from the first simple command); `--fill`, `--fill-first`, `--web`, `--editor`, `--template`, `--recover` and `--body-file -` (exit 0, note each); no body source and two body sources (exit 0, note); a cluster such as `-db` (exit 0, note). Run before the next item, the judged cases among them fail.
  - Blocked by: Hook core: pre-filter, tokenize, split, literal body
- [x] **Hook body recovery: heredoc mask, body files, unreadable shapes** — body-recovery steps 2, 5's unreadable flags, 6 and 7 from the architecture — size:M
  - Accept: the heredoc, body-file and unreadable-shape replay tests pass, and the literal-body replay tests still pass. Heredoc substitutions are masked on the raw command string before tokenizing. A body file is read through `cli.read_file(path, shown, str)`, and an absent, unreadable or non-UTF-8 file gives a note carrying the problem text as its reason. No path through the hook exits 2 except a judged body whose `pr_body_problems` list is non-empty.
  - Blocked by: Heredoc, body-file and unreadable-shape replay tests
- [x] **Registration tests** — a subprocess test in `tests/test_pr_body_preflight.py` that runs the exact `command` string read from `.claude/settings.json` — size:S
  - Accept: the test reads `.claude/settings.json`, finds the single `PreToolUse` entry with matcher `Bash`, `type: "command"` and `timeout: 10`, and runs its command through `/bin/sh` with `CLAUDE_PROJECT_DIR` set to the repo root: a failing-body payload exits 2 with B's strings on stderr, and a non-gh payload exits 0. The same command with `CLAUDE_PROJECT_DIR` set to a directory with no script exits 0. Run while `.claude/settings.json` is still `{}`, the test fails.
  - Blocked by: Hook body recovery: heredoc mask, body files, unreadable shapes
- [x] **Register the hook in .claude/settings.json** — the checked-in file goes from `{}` to the architecture's `PreToolUse` entry, `[ ! -f … ] ||` guard included; `settings.local.json` is untouched — size:S
  - Accept: the registration tests pass. `git diff --name-only` for this item lists `.claude/settings.json` and no `settings.local.json`. A `gh pr create --body "x"` run in a live session in this repo is refused with B's two strings (manual check, recorded in Notes).
  - Blocked by: Registration tests
- [x] **Whole-repo verify** — the four CI checks and the one-owner pre-pass over the finished change — size:S
  - Accept: `python3 run_tests.py` exits 0; `python3 lint.py` prints `lint: 0 problem(s)`; `python3 gates.py` and `python3 gates.py --selftest` print `gates: 0 problem(s)`; `python3 kb.py drift` prints `drift: 0 problem(s)`. `python3 one_owner.py` reports no `one-owner:` problem naming `pr_body_preflight.py` and either B regex or either B string. No file under `skills/` and not `.claude-plugin/plugin.json` changed (ADR-0095).
  - Blocked by: Register the hook in .claude/settings.json

## Design gaps found

Both gaps come from pinned repo tests the architecture does not account
for. The Accept lines above require `python3 run_tests.py` to pass, and
the architecture as written cannot meet that. Route back to Architect
before Implement.

1. **The hook's `main` signature and its `__main__` guard conflict with
   the `factory` verb table's pins (ADR-0054).** The architecture gives
   the script a pure `main(stdin_text) -> (exit_code, stderr_lines)`
   plus a thin `__main__`. `tests/test_factory_cli.py` derives the set
   of root modules carrying `if __name__ == "__main__":` and requires
   that each has exactly one `factory.VERBS` row named after it
   (`pr-body-preflight`). It also requires that the module's `main` has
   either no parameters (`bare`) or a first positional parameter named
   `argv`. A `main(stdin_text)` fails the second pin, and no `VERBS`
   row fails the first. Architect needs to decide the hook's
   entry-point contract: whether it becomes a `factory` verb, what its
   `main` takes, and what the pure test seam is called. That decision
   decides the Hook core item's interface and both replay-test items'
   call shape.
2. **The hook adds two crossing pairs to the pinned dual-membership
   set, and the pin requires an ADR, but the architecture records
   "ADRs: None".** `pr_body_preflight.py` is root-only and imports the
   mirrored `gates` and `cli`. `tests/test_dual_membership.py` pins
   ADR-0091's root-only to mirrored import set (41 pairs after
   ADR-0097). Adding `(pr_body_preflight, gates)` and
   `(pr_body_preflight, cli)` fails it, with the message "record it in
   an ADR superseding ADR-0091's table, then update this pin". ADR-0097
   is the precedent: one new pair, one provisional ADR. Architect needs
   to record that decision, or choose a shape that leaves the set
   unchanged. Then this breakdown gains an ADR item and a pin-update
   Accept line on the Hook core item.

Resolved 2026-10-16: both gaps closed by Architect's re-entry, commit
766633c (`architecture.md`, "Amended 2026-10-16"). Gap 1: the hook is a
`factory` verb with `main(argv, stdin=None)` over a pure
`preflight(payload_text)` seam. Gap 2: ADR-0106 (provisional) records
the two new pairs; no ADR item is needed since it is already written,
and the pin update is on the Hook core item. The Accept lines above are
revised to match.

## Notes

- 2026-10-16: revised after Architect's re-entry (commit 766633c,
  ADR-0106). Rewrote the Accept lines of the Literal-body replay tests,
  Hook core and heredoc replay tests items for the `preflight` seam, the
  `argv` main, the `VERBS` row, the dual-membership pin and the
  delegation test. Items, milestones and blocking edges unchanged; nine
  items. Implement logs deviations here, dated.
- 2026-10-16 (Implement): all nine items done test-first; each tests
  item was run red before its implementation. Red evidence:
  pr_body_problems tests `AttributeError: module 'gates' has no
  attribute 'pr_body_problems'` (6 errors); literal-body tests
  `ModuleNotFoundError: No module named 'pr_body_preflight'`; heredoc /
  body-file tests `FAILED (failures=32)`, the judged cases among them
  (the quoted heredoc body got `cannot parse the command: No closing
  quotation`, `--body-file pass.md` got `no --body or --body-file`);
  registration tests `0 != 1 : one PreToolUse Bash entry` against `{}`.
- 2026-10-16 (Implement), deviation in sequencing: the Hook core item
  pinned only `(pr_body_preflight, gates)` in
  `tests/test_dual_membership.py`, because the core does not yet import
  `cli`; the `(pr_body_preflight, cli)` pair and the comment's count of
  43 landed with the body-recovery item, which adds the import. Both
  pairs are ADR-0106's; the end state matches the Hook core Accept line.
- 2026-10-16 (Implement), refinements inside the architecture's
  fail-open rule (no ADR: each is a cheap, local parsing detail, and
  none adds an exit-2 path): `-f` (gh's `--fill` shorthand) joins the
  flags that leave the body to gh; the value-taking flags (`-t`, `-B`,
  `-H`, `-a`, `-l`, `-m`, `-p`, `-r`, `-R` and their long forms) skip
  their next word, so a title such as `-b` is never read as a body
  flag, and a value flag's joined value (`-Bfix/b`) is not treated as a
  cluster; a redirection token drops itself and its target word; a
  `--body` value holding a heredoc placeholder alongside other text is
  unreadable. Note reasons are pinned verbatim by the replay tests.
- 2026-10-16 (Implement), the Register item's manual live check: the
  hook loaded in the implementing session as soon as
  `.claude/settings.json` was written. The command run was
  `false && gh pr create --body "x"`, not a bare
  `gh pr create --body "x"`. The `false &&` makes sure gh can never
  run, so a hook that failed to load could not open a real PR. The hook
  judges the `gh pr create` segment the same way whatever comes before
  it, and refused the call with `PreToolUse:Bash hook error: ... B: PR
  body cites no work-order id` / `B: PR body has no Closes #N link` /
  `pr-body-preflight: the body contract is docs/kb/pr-body-contract.md`.
  A bare `gh pr create --body "x"` in a live session was not run. That
  exact observation is left to Verify or the Owner.
- 2026-10-16 (Implement), whole-repo verify: `python3 run_tests.py`
  gave `tests: 3264 tests across 106 modules in 15.9s on 8 workers, 0
  problem(s)`. `python3 lint.py`, `python3 kb.py drift`,
  `python3 gates.py` and `python3 gates.py --selftest` were all clean
  (the selftest prints `selftest: ok`). `python3 one_owner.py` reported
  9 problems, the same 9 as on `main`, and none names
  `pr_body_preflight.py`, either B regex or either B string.
  `git diff --stat main...HEAD -- skills/ .claude-plugin/plugin.json`
  is empty.
