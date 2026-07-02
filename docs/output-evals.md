# Output evals

Output evals check that a stage skill, given a seeded run directory and
pre-supplied interview answers, produces an artifact meeting objective
expectations. They cost real model runs, so they execute **on demand** —
there is no always-on gate. Trigger/routing evals are separate: see
`trigger_eval.py` and ADR-0019.

## Anatomy

- `evals/output/<slug>.json` — the eval set for one skill:
  `{"skill_name": "<slug>", "evals": [{id, prompt, run_fixture, run_scale,
  expected_output, expectations: [...]}]}`. Each expectation is an
  objectively verifiable statement about the produced artifact or response.
- `evals/fixtures/<name>/` — a seed docs tree copied into the scratch
  project. Upstream artifacts pre-answer what the skill would otherwise
  interview for; the eval `prompt` pre-supplies the remaining review-step
  answers.
- `evals/results/output/<slug>-<date>[-N]/grading.json` — committed record
  of a graded run; `-2`, `-3`… suffixes distinguish same-day runs.

## Workflow (one eval)

1. **Seed a scratch project.**

   ```bash
   SCRATCH=$(mktemp -d)
   cp -R evals/fixtures/<fixture>/. "$SCRATCH"/
   mkdir -p "$SCRATCH"/.claude/skills "$SCRATCH"/.claude/docs
   cp -R skills/<slug> "$SCRATCH"/.claude/skills/
   cp docs/pipeline-protocol.md "$SCRATCH"/.claude/docs/
   ```

   The protocol doc goes to `.claude/docs/` because skills reference it as
   `../../docs/pipeline-protocol.md` relative to their own directory.

2. **Execute.** From inside a Claude Code session, dispatch a subagent whose
   prompt is the eval's `prompt` with cwd `$SCRATCH`; or headless:

   ```bash
   (cd "$SCRATCH" && env -u CLAUDECODE claude -p "<eval prompt>" \
     --output-format stream-json --verbose > transcript.jsonl)
   ```

3. **Grade.** Dispatch a fresh subagent (or a second `claude -p`) with the
   grader prompt below. It must judge only against the expectations, citing
   evidence for every verdict.

4. **Record.** Save the grader's `grading.json` to
   `evals/results/output/<slug>-<date>/grading.json` and commit it. If an
   expectation turned out ambiguous or non-discriminating, fix the eval
   definition in the same commit and say so in the commit message.

## Grader prompt template

```
You are grading a skill-produced artifact against fixed expectations.
Work directory: <SCRATCH>. Files of interest: the run directory
docs/features/<slug>/ and transcript.jsonl (if present).

Expectations (grade each independently, no partial credit):
<numbered expectations from the eval>

For each expectation: verify it against the actual files/transcript — quote
or cite the evidence. Do not grade on style or effort; only on whether the
statement is true.

Return ONLY a JSON object shaped exactly like:
{
  "expectations": [
    {"text": "<the expectation>", "passed": true, "evidence": "<citation>"}
  ],
  "summary": {"passed": N, "failed": M, "total": N+M, "pass_rate": 0.0-1.0}
}
```

The field names `text`, `passed`, `evidence` are a contract — downstream
tooling (and skill-creator's viewers, if used) depend on them exactly.

## Lessons from the pilot (decompose, 2026-07-01)

- Pre-supplying interview answers in the prompt works: decompose's "review
  the cut" step accepts "use your recommended boundaries" and proceeds to
  write the artifact instead of stalling on a question.
- Grade from the files first, transcript second — the artifact is the
  deliverable; the transcript only settles process expectations (e.g. the
  soft-gate offer).
- The grader returns its JSON inside a ```json fence — strip the fence
  before saving grading.json, and validate with `python3 -c "import json;
  json.load(open('grading.json'))"` before committing.
- A second run of the same skill on the same day gets a `-2` suffix on its
  results directory (`decompose-2026-07-01-2/`), mirroring the trigger
  runner's collision convention — results stay append-only, never merged
  into an existing directory.
- Headless soft-gate runs can't interview, so the skill picks
  proceed-with-assumptions itself. "Offers both options" proved ambiguous
  under that condition, so the expectation was amended (per the policy
  above) to grade the naming of both paths — with backfill left open —
  rather than which one was taken.
