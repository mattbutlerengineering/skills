---
name: doctor
description: Use when the question is whether the pipeline itself is installed correctly in this repo — "is any of this actually wired up", "did the factory stamp take", "make check fails on a fresh stamp and it looks like the tool is broken", "are the skills even installed", "check the CODEOWNERS/labels/workflows the stamp left behind". Diagnoses the install read-only and degrades honestly; it checks the plugin side in any repo, runs the already-installed detectors when the factory is stamped, and touches the network only when explicitly asked. It reports each problem with the fix to apply. It never advances or touches a run (that is next) and never stamps, writes, regenerates, or commits anything (that is factory-init) — it may print the exact command to run and stops there.
---

# Doctor

Answer one question about the repo you are standing in: **is any of this
actually wired up correctly?** Not "is this repo's code good" — `make check`
answers that, and only after a stamp. Doctor checks that the pipeline and the
gate itself are correctly installed, which no repo-side gate can see.

Strictly read-only. Doctor runs the tools that are already there and
interprets what they say; it never writes a file, never stamps, never
regenerates a manifest, never commits, never opens an issue. Naming the
command to run is the end of its job.

## Process

Work the tiers in order and stop at the first one whose precondition is
absent — then say so. A repo that installed the plugin and nothing else
still gets a real verdict; silence would read as a pass.

### Tier 0 — plugin side (any repo, no factory required)

1. **Every skill resolves.** Ask the harness for the installed skills and
   confirm the pipeline set is there: `next`, the stages (`idea`, `prd`,
   `ux-design`, `architect`, `decompose`, `implement`, `verify`, `review`,
   `ship`, `operate`), the maintenance entry `capture`, and the utility
   skills. A missing skill or an unreachable `next` is invisible to every
   repo-side gate, because no repo-side gate can see the harness.

2. **The protocol is readable.** Read the pipeline protocol from the
   installed plugin. It is the runtime interface here — this repo has no
   `protocol.py` to fall back on.

3. **Any run artifacts parse.** Walk the candidate run directories (`docs/`
   plus every `docs/features/*/` and `docs/fixes/*/`). For each artifact
   present, check what the protocol requires: a frontmatter block that
   parses, a `stage:` matching the artifact, a `run:` in a legal form
   (`product`, `feature:<slug>`, `maintenance:<slug>`), a `date:`, plus the
   conditionals — `ux:` on a `prd.md`, `re-entry:` on a `defect.md`, and a
   `ux-reason:` whenever `ux: not-applicable`. Report which run you would
   orient to and what its next stage would be, so the user can check the
   answer against what they expect. If `docs/backlog.md` exists, check every
   line against the seed grammar.

   A repo with no artifacts at all is not a problem — it is a greenfield
   repo, and Idea is the honest answer.

### Tier 1 — stamped repo (`tools/factory/` present)

Skip this whole tier if `tools/factory/` is absent, and say so: the repo is
plugin-only, which is a legitimate install.

4. **Run the installed detectors** and read their problem strings — never
   re-derive a finding they already report:

       python3 tools/factory/gates.py
       python3 tools/factory/gates.py --selftest

   Detector E is the one to explain rather than repeat. It covers both
   halves of the scaffold: the mirror under `factory/templates/` against
   `factory/manifest.json`, and — in a stamped repo — the executable payload
   actually in use (`tools/factory/`, `.github/workflows/`) against that
   same manifest. Its two findings mean different things, so pass the
   difference on: a *diverged* file is a hand edit, and the remedy is never
   to keep it — restore from the mirror or re-stamp; a *missing* one is a
   partial stamp. Detector F covers `.github/factory.json`'s shape; report
   what F says about budgets, routing bands, and caps rather than parsing
   the file yourself.

   What E deliberately does not compare is as worth reporting as what it
   does: the budgets, the code-owner handle, and the doc seeds are the
   repo's to edit, so a difference there is never drift. Say so when asked
   rather than leaving the user to wonder why a changed CODEOWNERS is
   silent. Detector J is the one place a repo-owned file *is* checked, and
   for a narrow reason worth passing on: `.github/labels.json` is theirs to
   curate, but the tools and the Makefile's lifecycle targets name labels
   in it, so a deletion would otherwise fail only when CI flips the label.
   Adding labels stays free — the WIRING check looks in one direction only.
   J also reports a taxonomy it cannot read at all — corrupt JSON, not an
   array, every entry malformed, a duplicated name — and those lines arrive
   with an `L:` prefix because they are the loader's own words, forwarded
   rather than restated. Pass that on too: an `L:` line under
   `gates: N problem(s)` is J speaking, not the networked label-sync sweep
   running inside the offline gate.

5. **`tests/` exists.** The stamped `check` target runs
   `python3 -m unittest discover -q tests` and errors outright without a
   `tests/` directory — a fresh stamp into a test-less repo fails its first
   gate for a reason that reads like a broken tool. Fix: create `tests/`
   with at least one test module.

6. **The Makefile carries its full target set.** `check`, `review`,
   `pr-event`, the four lifecycle targets (`wo-merged`, `wo-in-progress`,
   `wo-needs-review`, `wo-failed`), `wo-record`, `assembler`, `find-pr`,
   `cost-report`, `gate-digest`, `toolsmith-mine`, `web-quality`. A missing
   lifecycle target is a hole in the work-order state machine that nothing
   else reports: without `wo-failed`, for instance, a dispatched run that
   dies leaves its order on `wo:in-progress` forever; without `wo-record`,
   every finished run is free as far as the monthly circuit breaker can
   tell (issue #222). A missing `pr-event` is narrower and just as quiet:
   a validator dispatched against a PR number writes no event, so every
   PR-shaped leg reads nothing and skips.

7. **The six workflows are present and call the factory through `make`.**
   `validator.yml`, `assembler.yml`, `design.yml`, `cost-report.yml`,
   `gate-digest.yml`, `toolsmith-mine.yml`. The drift to look for is
   narrow and specific: a `run:`
   step invoking `python3 tools/factory/...` directly instead of a make
   target. The target set is the contract CI and a local `make check` share,
   so a workflow that steps around it can pass CI while `make check` fails,
   or the reverse. Steps that legitimately do other work — `gh issue
   create`, checkout, Python setup — are not drift; do not report them.

8. **CODEOWNERS is substituted.** The template ships every path owned by the
   placeholder `@<owner>`. If the stamped repo's `.github/CODEOWNERS` still
   contains `@<owner>`, GitHub silently ignores those entries — the
   collaborator they name does not exist — and the code-owner gate, the
   human approval record, goes inert. Fix: replace every `@<owner>` with a
   real GitHub handle or team that is a collaborator on this repo.

### Tier 2 — networked (opt-in, never unasked)

9. Only when the user explicitly asks for it, check the label taxonomy that
    backs the lifecycle machine, the gate digest, and the sweeps' triage:

        python3 tools/factory/label_sync.py

    Read-only without `--apply`; report the drift and print the `--apply`
    command rather than running it. A doctor that needs the network to say
    anything is useless on a plane, so this tier stays off by default and
    its absence is stated in the report, never implied.

### Report

10. One label-prefixed line per problem, each naming the fix, then a tiered
    summary — the same shape the repo's own checkers use:

        DOCTOR [tier 1]: no tests/ directory — `make check` runs
          `unittest discover -q tests` and errors without one; create
          tests/ with at least one test module
        doctor: 1 problem(s) — tier 0 ok, tier 1 1 problem(s),
          tier 2 not run (networked, ask to include it)

    A tier that could not run is reported as not run, never as clean.

## Rules

- Read-only, without exception. Print the command; never run the one that
  writes.
- Never reimplement a check that a shipped tool performs. Doctor's value is
  diagnosis and the fix instruction, not detection — a finding it derives
  itself is a finding no gate will keep enforcing.
- Degrade honestly. Name every tier that did not run and why. An absent
  precondition is a fact to report, not a check to skip silently.
- Doctor never advances a run, never edits an artifact, and never fires from
  the router — it is a utility skill, invoked directly.
- Distinguish an unfinished install from a legitimate one: plugin-only is a
  valid state, an empty repo is a valid state, and calling either broken
  trains the user to ignore the report.
