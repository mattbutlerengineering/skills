# Autorun brief: a-rename-the-merge-train-may-not-see

Not an artifact. Written 2026-11-04 by the orchestrator. After the
a-brief-the-fast-path-waves-through run completed, the Owner invoked
`/idea-to-prod:autorun` again and answered two questions in session:

1. Run: "144: implement-queue renames", the `docs/backlog.md` line 144
   seed (from: feature:faster-sdlc).
2. Terms: "Same as last run". That means one `type:defect` intake
   issue (filed as #1149), release prepare and stop,
   `operate: minimum-signal: merged`, and no launch brief.

Everything else below is the orchestrator's reading of the seed and
the code, and is marked as such. A stage that needs an answer this
brief does not hold applies the autorun rule: take a skill-supplied
default and log it, or else stop and surface.

## Run scale

Maintenance (fix) run at `docs/fixes/a-rename-the-merge-train-may-not-see/`,
entering at Capture. It is a suspected defect, not yet proven.

## Capture inputs

- **What may be broken.** The implement-queue skill's Phase 3 merge
  rule refuses a PR that "changes a file `gate_paths` matches"
  (`skills/implement-queue/SKILL.md` line 198). The skill, its
  references, `.claude/implement-queue.md` and
  `docs/factory/merge-train-routine.md` never say how the changed-file
  list is obtained (orchestrator's reading, from a grep of those
  files). The likely sources are `gh pr diff --name-only`,
  `gh pr view --json files`, or a local `git diff --name-only`. If the
  source reports only a rename's destination, a PR that moves a
  gate-path file (`.github/workflows/*.yml`, `docs/adr/*.md`,
  `.claude-plugin/plugin.json`) into an ungated path escapes the
  check. That is the same blind spot `fast_path.py` had until #1144.
- **Reproduction.** Capture must settle this with real evidence, never
  a citation:
  - **(a)** Find what the train actually runs. Read the merge-train
    journal #930 comments and any recorded run transcript for the
    command it uses to list a PR's files.
  - **(b)** Test what each candidate source reports for a rename. Use
    `gh pr view <N> --json files` and `gh pr diff <N> --name-only` on
    a real merged PR that renamed a file (search merged PRs for one),
    or read GitHub's documented REST `pulls/{n}/files` shape, which
    carries `status: renamed` and `previous_filename`. Quote the
    output.
  - **(c)** Check whether the local `git diff --name-only` without
    `--no-renames` is used anywhere in the train's path.
- **Outcomes Capture may reach.** One of these:
  - **Proven gap:** a real source the train uses omits rename
    sources. Write the defect; the probable re-entry is `implement`.
  - **Undefined source:** the skill leaves the source unspecified, so
    the agent may pick any. The orchestrator reads this as a defect
    in the skill's contract, even if today's journal shows a safe
    source. The probable re-entry is `implement`: name the source in
    the skill and require rename sources to count.
  - **Not a defect:** the train's source is specified elsewhere and
    reports old paths. Write `defect.md` as a "ruled out" record with
    the evidence, set `re-entry: implement` with a single work item
    that pins the behaviour in a test or doc line, and say so plainly.
- **Evidence it bites today.** Check merged PRs since the train's
  first run (2026-10-16 00:38 UTC) for any rename whose source matched
  a gate path and that merged through the train (journal #930). Quote
  what is found, or say that none did.
- **Blast radius.** `skills/implement-queue/SKILL.md` (a payload
  skill; check whether it is mirrored or in the manifest),
  `.claude/implement-queue.md`, `docs/factory/merge-train-routine.md`,
  and possibly a small stdlib helper. An existing tool such as
  `fast_path.py` may already be the right owner of "the changed paths
  of a PR, rename sources included". The repo's seam rule forbids a
  second copy (AGENTS.md, "Seam modules").
- **Re-entry depth.** Orchestrator's reading: `re-entry: implement`,
  unless Capture finds that naming the source needs a design choice
  across tools. In that case Capture chooses `architect` and logs why.

## Scope

In:
- settling the question with quoted evidence;
- if it is a gap, the smallest fix that makes the train's `gate_paths`
  check see rename sources, with failing-first tests through a public
  interface (exact strings) and doc lines in the skill and profile
  naming the source;
- an ADR only if the protocol's "When to write an ADR" test holds,
  written as `provisional`;
- marking backlog line 144 claimed:
  `(claimed: maintenance:a-rename-the-merge-train-may-not-see)`.

Out: the other backlog seeds (145 onward, including line 146's
journal audit of past merges; Capture's bite check above is narrower);
glob dialect and case-sensitivity (line 154); any change to
`fast_path.py`'s classification rule.

## Success criteria

- `defect.md` states which source the train uses, what it reports for
  a rename, and the evidence for both.
- If there is a gap: a PR that renames a gate-path file into an
  ungated path is refused by the train's check in a test that fails on
  the pre-fix behaviour, and the skill names the source.
- `python3 run_tests.py`, `python3 lint.py`, `python3 kb.py drift`,
  `python3 gates.py && python3 gates.py --selftest` all pass, and
  detector E is clean after `update-manifest` if a mirrored file
  changed.

## Constraints

Stdlib only. Problem-string contracts. Never touch
`.claude-plugin/plugin.json` (ADR-0095). Delete stray `.orig`/`.rej`
before `update-manifest`. Gates scan every markdown file, so write no
literal four-digit work-order or PRD-style id that does not exist.
Wall-clock tests fail under heavy machine load. A failed full-suite
run is never reported as a pass; re-run it when load drops, and
record `uptime`.

## Tracker

Issue #1149 (`type:defect`) seeds the run as intake (ADR-0030):
Capture records `intake: #1149` in `defect.md`. The PR closes it
with `Closes #1149` and carries a `No work order:` line. Run
`gh pr create` as the first command of its own shell call, with the
body file written in an earlier call.

## User-facing surface

None. Ship does not produce a launch brief (Owner decision 2,
"no launch brief"), whatever `launch_demo.py config` prints.

## Release authorization

Prepare and stop. Ship pushes, opens the PR, records
`outcome: prepared` with `pending-merge:`, and stops. No merge, tag or
version bump.

## Operate

operate:
  minimum-signal: Ship written back as released (the PR merged).

`users-observed:` is counted from the signal Operate finds; this brief
never supplies it.
