---
stage: verify
run: maintenance:heredoc-delimiter-is-guessable
date: 2026-08-27
assumptions: []
---

# Verification: the heredoc delimiter is guessable

## Summary

Five criteria, five PASS. The injection is demonstrated through
`write_outputs`' public interface against the pre-fix module and shown
closed at HEAD: a poisoned value that forged `dispatch=true` — the flag
deciding whether the factory dispatches an agent — no longer forges
anything, and the value survives byte for byte.

## Criteria & evidence

### 1. The delimiter is not guessable from the key

- Check: run the two new tests against the **pre-fix** module
  (`git show origin/main:cli.py` laid over the post-fix tests in a
  scratch checkout), then against HEAD.
- Evidence — RED, pre-fix:
  ```
  FAIL: test_a_value_cannot_forge_an_output
      self.assertEqual(parsed["dispatch"], "false")
  AssertionError: 'true' != 'false'

  FAIL: test_the_delimiter_differs_between_calls
      self.assertEqual(len(seen), 2, "delimiter repeated across calls")
  AssertionError: 1 != 2 : delimiter repeated across calls
  ```
  The first is the defect itself: the caller wrote `dispatch=false` and
  the runner reads `true`.
- Evidence — the raw file the pre-fix module produced, and how Actions
  parses it (heredoc ends at the first line equal to the delimiter):
  ```
  dispatch=false
  prompt<<__PROMPT_EOF__
  do the work
  __PROMPT_EOF__
  dispatch=true
  model=expensive-model
  __PROMPT_EOF__
  -->  'dispatch' = 'true'
       'prompt'   = 'do the work'
       'model'    = 'expensive-model'
  ```
  A `model` output appears that no caller wrote.
- Evidence — GREEN at HEAD:
  ```
  ............................................................
  Ran 60 tests in 3.731s

  OK
  ```
- Result: PASS

### 2. The delimiter is never present in the body

- Check: randomness makes collision negligible, not impossible, so the
  loop must be exercised rather than trusted.
  `test_a_delimiter_that_collides_is_regenerated` patches
  `cli.secrets.token_hex` to hand out `c0ffee` twice — a value the body
  contains as `__EOF_c0ffee__` — then `d1ffe0`.
- Evidence: the third draw is the one used, and the body is unaltered:
  ```
  self.assertIn("prompt<<__EOF_d1ffe0__", text)
  self.assertEqual(self.parse_as_actions(text)["prompt"], body)
  ->  OK (part of the 60 above)
  ```
  `mock.patch` reaches this because the collision path runs in-process;
  no subprocess is involved.
- Result: PASS

### 3. The three existing TestWriteOutputs tests pass unmodified

- Check: `git diff origin/main...HEAD -- tests/test_cli.py`, filtered for
  removed lines.
- Evidence — the change is purely additive, so no existing test was
  edited to accommodate the fix:
  ```
   tests/test_cli.py | 68 +++++++++++++++++++++++++++++++++++++++++++++++++++++++
   1 file changed, 68 insertions(+)
  ```
  Grepping the same diff for `^-` lines (excluding the `---` header)
  returns nothing. `test_the_delimiter_carries_no_tool_branding` still
  holds for its original reason: lowercase hex cannot spell `ASM`.
- Result: PASS

### 4. The mirror is regenerated

- Check: `cli.py` is in `factory_init.MIRRORS`, so the payload copy and
  `factory/manifest.json` must move with it or detector E fails.
- Evidence:
  ```
  $ python3 factory_init.py update-manifest
  factory-init: 0 problem(s)

  $ python3 gates.py
  gates: 0 problem(s)
  ```
  `git status` after the regen listed `factory/manifest.json` and
  `factory/templates/tools/factory/cli.py` alongside `cli.py`, and both
  are in the commit.
- Result: PASS

### 5. Battery green

- Check: the repo's four commands, each measured unpiped so the exit code
  is the command's own.
- Evidence:
  ```
  Ran 1347 tests in 15.534s

  OK
  tests exit=0
  lint: 0 problem(s) across 24 skills
  lint exit=0
  gates: 0 problem(s)
  gates exit=0
  selftest: ok
  ```
  1347 against a 1344 baseline on the merge-base with `origin/main`:
  +3, exactly the three tests added here.
- Evidence — `one_owner.py`, the free pre-pass (not a gate):
  ```
  one-owner: 9 problem(s)
  ```
  Unchanged from baseline, so no new duplicated fact.
- Result: PASS

## Failures

None.

## Not verified

- **Linux/CI.** All evidence above is macOS and local; CI evidence is
  recorded in `release.md` after the push.
- **A real workflow run.** The parse in criterion 1 is *my* emulation of
  how the runner reads `$GITHUB_OUTPUT`, written to the documented rule
  that a heredoc body ends at the first line equal to the delimiter. It
  is not the runner. No Actions job was run to confirm the forged
  `dispatch` would actually have been honoured downstream — that would
  need a live workflow, which this run has no authorization to trigger.
  The fix does not depend on the emulation being exact: it removes the
  attacker's ability to know the delimiter at all.
- **The payload copy's behaviour.** `factory/templates/tools/factory/cli.py`
  is verified as a byte-identical mirror by detector E and
  `tests/test_factory_init.py`, not by executing its tests separately —
  the suite exercises the root module.
- **The other five callers.** They were read and classified in
  `defect.md`'s blast-radius table (all single-line, none reaching the
  heredoc branch), but no test pins that classification; it would go
  stale silently if a caller started writing a multiline value.
