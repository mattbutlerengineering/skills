---
stage: review
run: feature:launch-demo
date: 2026-10-10
assumptions:
  - "No live severity arbitration: autorun drove this stage, so the severities are this stage's ranking on the scale earlier reviews used (critical means wrong behaviour that ships silently, a lie in an artifact, or a broken contract with no workaround; major means a concrete failure a real user hits; minor means an edge or a decay with a cheap workaround). The orchestrator's rule applied: fix critical and major findings on the branch with TDD, defer minors with a reason. The fixes were small enough to make here instead of routing back to Implement, and each got its own breakdown row (WO-0126, WO-0127) and a $0 owner-session ledger row like WO-0125's."
  - "The untested cli.detail fallback in _node_reason (Verify's gap) was ranked major because the orchestrator named it a major test gap. It was fixed with a test only, so it has no breakdown row: no product code changed. The mutant Verify described (`else \"MUTANT\"`) was applied to the worktree, the suite was run, the file was restored from a scratchpad copy, and `git diff` was checked empty before the commit."
  - "docs/standards.json was read. It has four advisory statements, and stdlib-only, adr0004, adr0032 and eval-honesty all hold for this diff: the new imports are errno and unittest.mock, both standard library, and only in tests; no typed id moved; the two new WO rows existed before anything else referred to them; no eval evidence was written. No finding cites a statement, and no enforced statement exists."
  - "The merge check ran against origin/main fetched at review time. origin/main is still the run's merge base (736f54b), so the merge is a fast-forward and no roster, README or LEDGER change on main can collide. No scratch merge worktree was needed."
  - "The real-shell test added for finding 1 runs bash from the unit suite, skipped when bash is absent. That is a deliberate exception to 'CI runs no real recorder': bash is not a recorder, and only a real shell can show that the quoting holds. The encoding was also checked by hand on zsh and sh."
---

# Review: Launch demo

## Scope

The whole branch against `main` (`git diff 736f54b...HEAD`): 38 files,
+5129/−38 including this stage's fixes. Read line by line:
`launch_demo.py` (all of it), `tests/test_launch_demo.py` (the fakes and
every recorder, assemble and render test), the `cli.py` seam edit
(`runner` timeout and stdin, `TimeoutExpired` in `CLI_FAILURES`,
`detail`'s bytes decode) and its mirror under `factory/templates/`,
`skills/launch-demo/SKILL.md`, `references/brief-grammar.md`, the Ship
hook in `skills/ship/SKILL.md`, the roster entries (`protocol.py`
`UTILITY_SKILLS` and its mirror, `factory.py` `VERBS`, the README row,
the LEDGER row, `plugin.json` 0.4.0, the four routing-eval cases),
`.gitignore`, the committed outputs under `docs/launches/pipeline-board/`
(`demo.tape`, `storyboard.json`, `launch.md`, the size of `launch.mp4`),
and the run artifacts, including `verification.md`'s gap note.

Checks run from the worktree:

```
$ python3 -m unittest discover tests      -> Ran 2039 tests ... OK
$ python3 lint.py                         -> lint: 0 problem(s) across 26 skills
$ python3 gates.py && python3 gates.py --selftest
                                          -> gates: 0 problem(s) / selftest: ok
$ python3 factory_init.py update-manifest -> factory-init: 0 problem(s) (manifest unchanged)
$ python3 one_owner.py                    -> 6 problem(s), none naming launch_demo.py
$ wc -l launch_demo.py                    -> 800
$ git merge-tree --write-tree origin/main HEAD -> 23364a3 (clean, exit 0)
```

## Findings

### Major: narration text could run as shell in the terminal recording (fixed)

- Scenario: launch.md is markdown, so a narration line can easily hold
  a backtick and an apostrophe, e.g. ``Run `make; touch ran-1` and it's
  done.`` `_screen` passed the line through `shlex.quote`, which turns
  the apostrophe into `'"'"'`. The screen line then held all three vhs
  delimiters, and `_tape_string` replaced every backtick with `'`. That
  re-quoted the shell word: the text between the backticks ended up
  outside quotes and the recording shell ran it. Seen red in bash:
  `printf` printed `Run make` and `touch ran-1` executed. A subtler
  copy would just print the wrong words or leave the shell waiting on
  an unclosed quote for the rest of the tape. The storyboard's `do`
  commands are code by design, but `say` is prose, and SKILL.md
  promises it is only shown. The committed pipeline-board storyboard
  already has the apostrophe; one backtick away from this.
- A terminal `do` command holding all three quote characters was also
  rewritten silently the same way, so a different command got typed. A
  command with a line break split the `Type` line, and its second half
  was read as a vhs command.
- Fix: WO-0126. Each screen word is now a single-quoted printf `%b`
  argument with every quote, backslash and line break octal-escaped, so
  narration is printed and never parsed. `check_storyboard` refuses a
  terminal command that no vhs string can carry, so `_tape_string`
  never rewrites one. The brief grammar now states that rule. The test
  runs the generated screen line in real bash from an empty directory:
  exact text out, no files created.
- Standard: none
- Decision: fixed — `4c53fa7`

### Major: assemble crashed when scratch and repo are on different filesystems (fixed)

- Scenario: on a Linux host whose `/tmp` is tmpfs (the default on
  Fedora and Arch), the scratch directory and the repo sit on different
  devices. `assemble`'s `os.replace(scratch_out, out)` raised `OSError:
  [Errno 18] Invalid cross-device link`. Nothing caught it, so the user
  got a traceback, not a verdict, at the last step of a multi-minute
  render, and the Ship hook logged a crash. Verify ran on macOS, where
  `/var/folders` and the repo share one APFS volume, so it never hit
  this.
- Fix: WO-0127. The probed result is `shutil.move`d to a hidden
  `.launch.mp4.partial` beside `out` and then `os.replace`d into `out`
  inside that one directory, so `out` is still never a partial file.
  The test patches `os.rename` and `os.replace` to raise EXDEV across
  directories. This refines architecture.md's "write to scratch, then
  `os.replace`" contract, which assumed a single filesystem; the
  breakdown row records the refinement.
- Standard: none
- Decision: fixed — `22bc61d`

### Major: `_node_reason`'s `cli.detail` fallback was untested (fixed)

- Scenario: Verify showed that replacing `else cli.detail(err)` with
  `else "MUTANT"` survived every test. The only "no error line" test
  used stderr `node: bad option: --nope`, which WO-0125's wider
  `NODE_ERROR_LINE` already matches as an error line. A regression in
  the reason for a hung run or a banner-only crash would have shipped
  unseen.
- Fix: one test with two subtests, a banner-and-frames-only stderr
  (reason `Node.js v22.22.3`) and a `TimeoutExpired` (reason
  `cli.detail(err)`). The mutant fails both.
- Standard: none
- Decision: fixed (test only) — `3d8c821`

### Minor: `DRIFT_BAND`'s lower bound allows overlapping narration

- Scenario: offsets are scaled by `recorded ÷ planned`, but the clips
  keep their own length. A scene's narration runs into the next scene's
  when `ratio × (narration + 0.5 s + typing) < narration`. At the band
  floor of 0.75 that happens for any untyped line over 1.5 s, and the
  verdict is still PRODUCED. The real runs measured 0.94–0.97, where no
  line overlapped (Verify's per-scene table).
- Decision: deferred — the observed ratios are well inside the safe
  range. Narrowing the band, or checking "no clip outlasts its scaled
  hold" directly, needs more real recordings to set the bound, and
  `launch_demo.py` is at its 800-line cap. Seed for Operate.

### Minor: the `render` slug is not held inside the publish path

- Scenario: `render ../../x` resolves `slug_dir` outside `<publish>`.
  If a `launch.md` and `storyboard.json` exist there, the mp4 is
  written there too. `publish` itself is checked to be a plain relative
  path; the slug is not.
- Decision: deferred — the slug comes from the skill's own agent and
  both source files must already exist at the target, so the exposure
  is small. The fix (the `_plain_relative` check plus a single-segment
  check) needs lines that the 800 cap does not have.

### Minor: config strings reach argv and the tape loosely

- Scenario: `voice` substitutes `{out}` before `shlex.split`, so a
  scratch path containing a space splits into two tokens. A voice with
  an unbalanced quote raises `ValueError` from `probe`, a traceback
  where a problem string belongs. For the terminal recorder, `against`
  is written into `Set Shell` unchecked, so a line break in it adds
  tape lines.
- Decision: deferred — every one of these is the repo owner's own
  config file, written once and validated by the `config` leg's
  grammar. Tightening that grammar (shlex-parseable voice, one-line
  against) is a small follow-up row.

### Minor: storyboard `title` and `tagline` are not type-checked

- Scenario: `"title": 7` passes `check_storyboard`, then raises
  `TypeError` in the screen encoder or `html.escape`. That is a
  traceback, not a storyboard problem.
- Decision: deferred — the agent writes these from the grammar, and a
  non-string title has never been seen in practice. It joins the
  grammar-tightening follow-up above.

### Minor: a timeout kills vhs and node but not their children

- Scenario: `subprocess.run(timeout=…)` kills only the direct child.
  vhs's ttyd and headless Chrome, or Playwright's browser, can outlive
  a `RECORD_TIMEOUT` kill as orphans.
- Decision: deferred — the timeout is a 10-minute backstop that no run
  has hit. Killing a process group needs `start_new_session` in the
  shared `cli.runner` seam, which belongs in its own change.

### Minor: published artifacts carry machine noise and weight

- Scenario: the committed `demo.tape` opens with the absolute scratch
  path (`/private/var/folders/…/raw.mp4`), so every re-render diffs on
  that line. `launch.mp4` (433 KB) is now the largest blob in history
  (the largest before it was the 358 KB readme-skill-map screenshots),
  and every re-render adds about 0.4 MB.
- Decision: deferred — committing the mp4 is architecture.md's
  recorded decision, with Git LFS named as the lever if it grows. The
  tape path is cosmetic. The scratch directory is likewise kept after a
  PRODUCED run by design (it is named for inspection).

### Minor: `_node_reason` repeats `cli.detail`'s bytes decode

- Scenario: the decode of a timed-out child's undecoded stderr now
  lives in two places. A fix to one will not reach the other.
- Decision: deferred — two lines, and the right owner is a
  `cli.stderr_text(err)` helper used by both. That is a seam change
  with only two callers, below the "observed divergence" bar CLAUDE.md
  sets for a new shared piece.

## Passes with no findings

- **Security, browser path:** narration reaches the driver only through
  `json.dumps`. Card titles and taglines go through `html.escape`. The
  URL and the scratch directory travel as argv, never interpolated or
  sent through the environment. `do` is Playwright code by contract.
  The driver's temporary home is removed in a `finally`, on both
  success and failure (both tested).
- **Subprocess handling:** every external CLI goes through
  `cli.runner` with a per-call timeout, and `TimeoutExpired` is in
  `CLI_FAILURES`, so a hang returns a problem string. The seam edit
  leaves every earlier caller unchanged (defaults `None`).
- **Problem-string contract, seam modules:** every leg returns
  label-prefixed problem strings that the tests assert exactly.
  `launch_demo.py` is a thin caller of `cli` (`runner`, `read_file`,
  `report`, `detail`) and owns no shared fact (`one_owner.py` is clean
  for it).
- **Skill bodies:** SKILL.md's description names its trigger phrasings
  and its near-neighbour (`ship`), and the four routing cases cover the
  ship/launch-demo boundary from both sides. Neither SKILL.md nor the
  Ship hook names a harness: the hook says "the harness's
  skill-loading mechanism", and the one CLI named is the forge's `gh`.
- **Roster:** `UTILITY_SKILLS`, the README table and figure, the LEDGER
  row (`draft`, no fabricated evidence), the plugin description and
  0.4.0 all agree, and lint confirms it.

## Verdict

Ready to ship. All three majors are fixed on the branch with red-first
tests: narration running as shell (`4c53fa7`), the cross-filesystem
publish (`22bc61d`) and the untested fallback (`3d8c821`). The battery
is green at 2039 tests, and `launch_demo.py` sits at exactly its
800-line cap. No critical finding was raised. Seven minors are
deferred with reasons above; the drift-band, slug and
config-grammar ones are worth seeding at Operate. The branch merges
cleanly with `origin/main`, which has not moved since the run began.
Next stage: Ship.
