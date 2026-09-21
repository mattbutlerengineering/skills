---
stage: capture
run: maintenance:an-un-run-corner-nothing-pins
date: 2026-08-27
re-entry: implement
assumptions: []
---

# Defect: the un-run corner, and the pin that only covers two of it

## Defect

Two defects, one file family.

**One — the pin's enumeration is hand-typed.**
`tests/test_fixture_recorders.py` says exactly why it exists:

```
The two record.py scripts under tests/fixtures/ run rarely (only when a
pinned transcript is re-recorded) and CI never executes them, so a seam
move can strand them silently — round 5's cli_version extraction did
exactly that.
```

And then names them by hand:

```
RECORDERS = (
    REPO / "tests" / "fixtures" / "transcripts" / "record.py",
    REPO / "tests" / "fixtures" / "omp-transcripts" / "record.py",
)
```

A third recorder is stranded the moment it is added — by the shape of
the enumeration in the file whose whole job is to prevent stranding.

**Two — a recording that never ran is written out as a no-fire.**
Both recorders hand the CLI's stdout to the detector and write whatever
came back:

```
        fired = ADAPTER.detect(ADAPTER.decode(teed_lines()), name_to_slug)
    finally:
        ...
    (HERE / f"{name}.jsonl").write_text("\n".join(lines) + "\n", ...)
```

The detector answers `None` when nothing fired. It answers `None` just
the same when nothing *arrived*. And the recorders run the CLI with
`stderr=subprocess.DEVNULL`, so a CLI that dies on the first breath is
silent: no output, no error on screen, and a transcript on disk.

## Why it matters

A pinned transcript is eval evidence. CLAUDE.md's eval-honesty section
is the repo's least negotiable rule — "Never fabricate run or eval
evidence" — and this manufactures some by accident: an empty stream
becomes a committed `fired: null` no-fire, stamped with a real
`cli_version` read from the actually-installed CLI, which makes the
artifact look authentic to every later reader.

The two defects compound. Defect one means a new harness's recorder is
never checked; defect two means the recorder it forgot can write a
fabricated fixture without complaint. The corner CI does not execute is
also the corner nothing else watches.

## Reproduction

**One.** A third recorder that imports a name `trigger_eval` does not
have — the precise failure the file was written for:

```
$ cat tests/fixtures/codex-transcripts/record.py
...
from trigger_eval import HARNESSES, describe_skills
...
$ python3 -c "import trigger_eval; print(hasattr(trigger_eval, 'describe_skills'))"
False
$ python3 -m unittest tests.test_fixture_recorders
Ran 1 test in 0.019s

OK
$ python3 -m unittest discover tests
Ran 1344 tests in 16.082s

OK
```

Green, both times.

**Two.** The claude recorder driven with a CLI that exits 127 and prints
nothing (a copy in a temp tree, so no real fixture was touched):

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

A one-byte transcript and a provenance entry asserting an outcome that
was never observed. The script exits 0 and prints `0 lines recorded` —
the only clue, and it reads like a statistic rather than a failure.

## Why the tests did not catch it

Defect one is invisible to its own test by construction: the tuple is
both the enumeration and the thing that would have to change.

Defect two is not covered anywhere, and the near miss is instructive.
The replay suites *do* guard the committed fixtures —
`tests/test_trigger_eval_detection.py` and its omp twin both carry
`self.assertTrue(events, f"{name}.jsonl replayed to zero events")` — so
an empty transcript that reached the repo would fail CI. That is the
right check in the right place and it is the reason this defect is a
near miss rather than a live fabrication. It does not close the hole:
it fires after the bad fixture is committed, and it says nothing about
a *partial* recording, which is non-empty and replays to `None` like a
genuine no-fire.

## Fix

**One.** Derive the enumeration from the filesystem —
`FIXTURES.glob("*/record.py")` — with a non-vacuity guard, because a
glob that matched nothing would make every test in the file pass
vacuously. That is the failure mode of deriving an enumeration, and it
deserves its own assertion rather than trust.

**Two.** A `recording_problems(lines)` checker in each recorder,
returning `record:`-prefixed problem strings per the repo's convention,
refusing the one stream that is never evidence:

```
    if not lines:
        return ["record: the CLI produced no output — a recording that"
                " never ran is not a no-fire (stderr goes to /dev/null"
                " here; re-run the command by hand to see why)"]
```

`record()` prints and raises `SystemExit(1)` before writing anything, so
neither the transcript nor the provenance entry is created.

Deliberately only the empty case. A short stream may be a genuine early
decision — the recorder stops as soon as the detector decides — and a
length threshold would refuse real recordings to catch a crash a human
re-recording is going to notice anyway.

The two recorders share no import, so the guard is two copies. That is
stated rather than hidden, and
`test_the_recorders_refuse_identically` holds them together: the one
place the copies can be compared is the suite that already loads both.

## Breakdown

- [x] Reproduce one: a stranded third recorder, whole battery green.
- [x] Reproduce two: a dead CLI writing a transcript and a provenance
      entry, exit 0.
- [x] Derive `recorders()` from the filesystem, with a non-vacuity pin.
- [x] Add `recording_problems` to both recorders and refuse before the
      write.
- [x] Pin the two copies as identical.
- [x] Remove the injected third recorder; clean battery green.

## Notes

- 2026-08-27: the injected third recorder was deleted before commit —
  `git status --short` shows three modified files and no additions
  under `tests/fixtures/`.
- 2026-08-27: two dead ends checked first and dismissed rather than
  written up. The two replay suites are twins and *both* carry the
  zero-event guard, so there was no divergence there; and the claude
  recorder's provenance omitting `harness` mirrors the eval result
  record, which has no `harness` field either — the omp recorder adds
  one, it does not restore one.
