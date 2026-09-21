---
stage: capture
run: maintenance:the-digest-says-what-it-could-read
date: 2026-08-25
re-entry: architect
intake: #346
assumptions:
  - "Captured as a DEFECT brief rather than a condition brief. The digest states something false — an empty gate section on a truncated read asserts nothing is waiting — rather than merely reading poorly. Re-entry is architect because what the digest should say, and where that sentence should live, is genuinely open."
  - "Scoped to gate_digest.py alone, though four other windowed reads (dashboard.py:158 and :197, assembler.py:257, label_sync.py:111) never consult read.truncated either. Each writes a different artifact for a different reader, so each needs its own evidence that the omission costs something. Widening this run to all five would carry four unevidenced fixes on one measured one."
  - "The in-flight check ran (protocol, Work already in flight): open PR #343 fixes this defect CLASS in rejection_mining.py and is unmerged. Judged adjacent, not duplicate — different module, different artifact (#294 vs #178), and a different fix shape, because rejection_mining already had a Sources: line to extend and the digest has no provenance line at all. Recorded rather than treated as a blocker."
---

# Defect: the daily gate digest does not say what it could read

## Defect

**Observed.** `run_daily` (`gate_digest.py:187`) learns twice that its view
of the world may be partial, and drops the fact both times:

- Line 197 passes `window=LIST_WINDOW` to `cli.gh_read` and never reads
  the `truncated` field it gets back.
- `_timelines` (line 95) treats a failed per-issue timeline fetch as a
  problem and continues — deliberately, and its docstring says so: *"a
  failed fetch is a problem, never a lost queue item (the digest still
  lists the issue, just without an age)"*.

Both facts reach the workflow log via `report()`. Neither reaches
`compose_digest`, and so neither reaches issue #178 — the pinned artifact
a human reads to know what is waiting at a gate.

**Expected.** The digest is the whole product of this tool. When the run
could not see the whole queue, or could not age an item in it, the body
should say so where the reader is looking. The workflow log is not that
place: nobody opens an Actions log to find out whether yesterday's queue
was complete.

**Not a request to make truncation fatal.** `cli.gh_read`'s docstring
settles that: *"the seam states the fact and the CALLER decides what it
means — most report and continue, work_queue and sweeps.live_issues refuse
the value outright."* Report-and-continue is right for a daily digest; a
digest that refuses to post because it saw 1000 issues is worse than a
partial one. The defect is that the caller decided *nothing*.

## Reproduction / Evidence

Measured against the repo's own injected gh fakes
(`tests/fake_gh.FakeGh`, driven through `gate_digest.run_daily`), reading
the body actually handed to `gh issue create`.

**1. A truncated listing produces a byte-identical digest.**

Two runs, one healthy and one whose issue listing comes back at a full
1000-entry window. The digest bodies are character-for-character equal:

```
--- HEALTHY
## Blueprint gate (wo:prd-approved)
- #123 WO-0018 rejection mining — waiting 2d 0h

--- LISTING TRUNCATED
## Blueprint gate (wo:prd-approved)
- #123 WO-0018 rejection mining — waiting 2d 0h
```

The truncated run emitted `gd: gh issue list returned a full 1000-entry
window — older entries are invisible` to the log, and nothing to the
reader. Every `- (empty)` section in that digest means either "nothing is
waiting" or "I could not see that far", and the body cannot tell them
apart.

**2. An unreadable timeline renders as a readable one.**

With the timeline endpoint answering non-JSON, against the same issue at
the same gate:

```
timeline read fine, no gate event : '- #123 WO-0018 rejection mining'
timeline could not be read        : '- #123 WO-0018 rejection mining'
IDENTICAL LINE: True
```

The suffix `— waiting 2d 0h` is simply absent. A reader sees a line that
also renders for an item whose history was read perfectly well and held no
gate arrival — i.e. "just arrived, no age yet". The tool's entire purpose
is stating how long something has waited, and the one line that most needs
a caveat is the one that silently omits it.

## Why it survived

`tests/test_gate_digest.py` covers both conditions already:

- `test_a_full_issue_window_is_reported_and_the_digest_still_posts`
  (line 277) asserts the exact truncation problem string and that
  `issue create` was called once.
- `test_an_unparseable_timeline_still_posts_the_digest` (line 291) does
  the same for the timeline failure.

Both assert the *log* and the *fact of posting*. Neither asserts one word
about what the posted body contains. The half of the behaviour that has a
human on the other end of it is the half with no test.

## Impact

#178 is a permanent pinned state issue that automation rewrites daily and
a human reads to decide what to unblock. A work order past the window, or
one whose age could not be read, is a work order that waits without anyone
knowing it is waiting — which is the specific failure the gate digest was
built (WO-0017, ADR-0041) to prevent.

Severity is bounded by likelihood, and honestly: this repo has ~150
issues, so the 1000-entry window is not close to full today. The timeline
half is the live one — a single flaky `gh api` call is ordinary, and it
degrades a line silently every time it happens.

## Scope

`gate_digest.py`, `tests/test_gate_digest.py`, and — because
`gate_digest.py` is in `factory_init.MIRRORS` — the payload copy at
`factory/templates/tools/factory/gate_digest.py` plus
`factory/manifest.json`.

Out of scope, named so the next reader does not think they were missed:
the four other windowed reads that never consult `truncated`
(`dashboard.py:158`, `dashboard.py:197`, `assembler.py:257`,
`label_sync.py:111`). Each writes a different artifact for a different
reader; each needs its own evidence.
