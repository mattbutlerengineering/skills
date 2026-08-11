# Recorded detection transcripts

Real `claude -p` stream-json transcripts, pinned as test fixtures so the
trigger-eval detection seam has a second adapter beside the live pipe
(issue #24). `tests/test_trigger_eval_detection.py` replays each transcript
through `detect_fired` and asserts the outcome recorded here — a CLI
output-shape change breaks CI instead of silently corrupting eval
results. (These are not eval fixtures in the CONTEXT.md sense — no seed
docs tree, no output eval — which is why they live under `tests/`.)

- `skill-fires.jsonl` — a direct routing query; the Skill tool fires.
- `no-fire.jsonl` — a distractor query; no skill fires.
- `provenance.json` — per transcript: the query, the fired slug, the
  recording date, the CLI version, and the invocation facts (model,
  settings isolation). Plus the fixed `run_id` embedded in the
  transcripts' skill names, which the replay test rebuilds its
  name-to-slug map from.
- `record.py` — the recorder that produced them.

## Re-recording (when the CLI output shape changes)

From the repo root, with an authenticated claude CLI:

```bash
python3 tests/fixtures/transcripts/record.py skill-fires \
  "Write a PRD for the CSV export feature"
python3 tests/fixtures/transcripts/record.py no-fire \
  "Rename the userId variable to accountId across the codebase"
```

`record.py` mirrors the trigger-eval runner's invocation (flags, env
strip, isolated project layout, early-stop on detection); if the
runner's invocation changes, update record.py to match — nothing pins
the two automatically. Each re-recording replaces the transcript and
its provenance entry together; commit both in the same change. Never
edit a transcript by hand — a recording is evidence of what the CLI
actually emitted, and touching one up defeats the pinning (the same
honesty stance LEDGER.md takes for eval results, though results are
append-only while these are replaced by re-recording).

If a re-recorded transcript replays to a different outcome than
expected (e.g. the direct query stops firing), that is routing drift,
not a fixture problem — investigate the descriptions before touching
the fixtures.
