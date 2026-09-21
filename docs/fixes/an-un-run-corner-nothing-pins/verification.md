---
stage: verify
run: maintenance:an-un-run-corner-nothing-pins
date: 2026-08-27
assumptions: []
---

# Verification: an un-run corner nothing pins

Eight criteria, each with the command run and its actual output.

## 1. A stranded third recorder passes the old pin — PASS

A recorder importing `describe_skills`, a name `trigger_eval` does not
export — the exact seam-drift the file exists to catch:

```
$ python3 -c "import trigger_eval; print('describe_skills present:', hasattr(trigger_eval, 'describe_skills'))"
describe_skills present: False
$ python3 -m unittest tests.test_fixture_recorders
Ran 1 test in 0.019s

OK
$ python3 -m unittest discover tests
Ran 1344 tests in 16.082s

OK
```

## 2. The derived pin catches it — PASS

Same tree, the rewritten enumeration:

```
$ python3 -m unittest tests.test_fixture_recorders
    from trigger_eval import HARNESSES, describe_skills  # noqa: E402
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ImportError: cannot import name 'describe_skills' from 'trigger_eval'

----------------------------------------------------------------------
Ran 5 tests in 0.021s

FAILED (errors=8)
```

## 3. A dead CLI records as a no-fire — PASS

The claude recorder driven with a CLI that exits 127 and prints nothing,
against a copy in a temp tree so no real fixture was touched:

```
$ python3 emptyrec.py
no-fire: fired=None, 0 lines recorded
record() returned: None and exited normally

wrote no-fire.jsonl: 1 bytes, 1 lines
wrote provenance.json:
{
  "run_id": "pinned01",
  "transcripts": {
    "no-fire": {
      "query": "Rename the userId variable",
      "fired": null,
      "recorded": "2026-08-27",
      "cli_version": "2.1.250 (Claude Code)",
      "model": null,
      "isolated_settings": true
    }
  }
}
```

## 4. The guard refuses, and writes nothing — PASS

The same drive against the fixed recorder:

```
$ python3 emptyrec.py
record: the CLI produced no output — a recording that never ran is not a no-fire (stderr goes to /dev/null here; re-run the command by hand to see why)
SystemExit: 1
files left in the fixture dir: ['__pycache__', 'record.py']
```

No `no-fire.jsonl`, no `provenance.json`. The refusal happens before
either write, not after.

## 5. A stream with output is still recordable — PASS

The guard refuses the empty case only, so ordinary recordings are
unaffected. Both recorders, through the suite:

```
$ python3 -m unittest tests.test_fixture_recorders
Ran 5 tests in 0.023s

OK
```

That run includes `test_a_stream_with_output_is_recordable` and
`test_the_recorders_refuse_identically`, so the two copies of the guard
are asserted to be the same refusal, not merely both present.

## 6. The injected third recorder was removed before commit — PASS

```
$ rm -rf tests/fixtures/codex-transcripts
$ git status --short
 M tests/fixtures/omp-transcripts/record.py
 M tests/fixtures/transcripts/record.py
 M tests/test_fixture_recorders.py
```

Three modified files, nothing added under `tests/fixtures/`.

## 7. The clean battery is green — PASS

```
$ python3 -m unittest discover tests
Ran 1348 tests in 15.520s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
```

1348 = the 1344 on `origin/main` plus four: the pin file went from one
test to five.

## 8. No payload byte moved — PASS

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ git status --short
 M tests/fixtures/omp-transcripts/record.py
 M tests/fixtures/transcripts/record.py
 M tests/test_fixture_recorders.py
```

Nothing under `tests/` is mirrored, and no production module changed.

## Not verified

- **No recorder was run against a real CLI.** Every check above drives
  a copy of the recorder with an injected fake process; the live path
  needs an authenticated `claude` or `omp` and spends money, which this
  run does not do. What is verified is the refusal, the exit, and that
  no file is written — not that a real recording still succeeds
  end to end. The guard sits before the CLI-facing code and changes
  nothing about it.
- **A partial crash is still indistinguishable from an early
  decision.** A CLI that dies after three lines produces a non-empty
  stream that replays to `None`, exactly like a genuine no-fire. Closing
  that needs the runner's own answer to the same question, which lives
  in `trigger_eval.py` — contended by an open branch, and deliberately
  out of scope here. Stated in the brief and repeated here rather than
  left to be discovered.
- **The wholesale duplication between the two recorders is untouched.**
  They are near-identical files; this run added a fourth shared
  concern to them and pinned it, rather than folding them together.
  That is a deepening, not a fix.
- **`one_owner` is unchanged at nine findings and says nothing here** —
  its `EXCLUDED` tuple skips `tests/` entirely, so it is structurally
  blind to every file in this diff, including the deliberate two-copy
  guard.
