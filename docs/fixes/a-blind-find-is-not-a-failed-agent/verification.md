---
stage: verify
run: maintenance:a-blind-find-is-not-a-failed-agent
date: 2026-08-25
assumptions:
  - "The centrepiece is the step-output comparison, not the return value. The defect was measured on what assembler.yml branches on — the exit code and $GITHUB_OUTPUT — so that is where it is pinned. The unit tests on Find cover the four contract rows more cheaply but would not catch a find-pr leg that computed `looked` and forgot to write it."
---

# Verification: the factory says whether it looked

Commands run in the run worktree. Output quoted, not summarised.

## C1 — a blind find is now distinguishable from an empty one

`defect.md` measured two rows as identical in both channels the workflow
reads. Same probe, same fakes, after the fix:

```
--- agent DELIVERED, gh readable
    exit=0  outputs='pr=6\nlooked=true'
--- agent DELIVERED, gh rate-limited
    exit=1  outputs='pr=\nlooked=false'
--- agent delivered NOTHING, gh readable
    exit=1  outputs='pr=\nlooked=true'
```

Rows two and three now differ on `looked`, which is exactly what
ADR-0063's failure-step condition reads. **PASS.** Pinned by
`test_a_blind_find_says_it_did_not_look` and
`test_a_readable_find_says_it_looked` (the latter over both the matched
and the genuinely-absent case, so `looked=true` is not accidentally
coupled to finding something).

## C2 — exit codes are unchanged

All three rows exit exactly as they did before: `0`, `1`, `1`. A find
that cannot look is still a failure and still reddens the run — the
change is the attribution, never the loudness. **PASS.**

## C3 — a truncated listing no longer blames the agent

```
    def test_a_truncated_listing_does_not_blame_the_agent(self):
        ...
        self.assertNotIn("delivered no traceable PR",
                         " ".join(found.problems))
        self.assertTrue(any("full" in problem for problem in
                            found.problems), found.problems)
```

Watched fail before the change with the agent-blaming sentence present;
passes after, with `looked=False` and a problem naming the full window.
**PASS.**

## C4 — the workflow condition is pinned, in the form that matters

```
        self.assertIn("steps.find.outputs.looked != 'false'", condition)
        self.assertNotIn("steps.find.outputs.looked == 'true'", condition)
```

The negative assertion is the load-bearing one. `!=` lets an unset output
— a run that died before the find step executed — still flip the order;
`== 'true'` would silently stop recording those failures at all. **PASS.**

## C5 — payload and manifest in lockstep

```
$ python3 -B factory_init.py update-manifest
factory-init: 0 problem(s)
$ git status --short
 M factory/manifest.json
 M factory/templates/.github/workflows/assembler.yml
 M factory/templates/tools/factory/assembler.py
```

Three generated files, matching the two mirrored sources. **PASS.**

## C6 — the repo's own battery

```
$ python3 -m unittest discover tests
Ran 1348 tests in 16.221s

OK

$ python3 lint.py
lint: 0 problem(s) across 24 skills

$ python3 gates.py
gates: 0 problem(s)

$ python3 gates.py --selftest
selftest: ok
```

**PASS.** Four tests added; three existing tests updated for the new
return shape.

## C7 — no new second owner

`python3 one_owner.py` on this branch, diffed against the detached
`origin/main` checkout (`622e7c0`):

```
2c2
< ... assembler.py:54 READY_LABEL ...
> ... assembler.py:55 READY_LABEL ...
```

9 problems before, 9 after. The single difference is a line number on a
pre-existing finding that moved because `Find` was defined above it. No
finding added, none removed. **PASS.**

## Not verified

- **The workflow has not run.** `assembler.yml` executes only on a real
  dispatch, and `CLAUDE_CODE_OAUTH_TOKEN` is unminted, so nothing here
  observed the condition taking effect. The YAML is pinned by reading;
  that catches deletion and rewording and nothing else.
- **GitHub's step-output semantics on a failed step.** The whole design
  rests on GitHub recording `looked=false` from a step that exits
  nonzero. `write_outputs` provably runs before `report()` in `main`, and
  this is documented GitHub behaviour — but it is documentation, not an
  observation, and if it were wrong the condition would read `''` and the
  flip would happen anyway. That failure mode is the current behaviour,
  so the change cannot be worse than the status quo, but it could be a
  no-op. **This is the single largest untested assumption in the run.**
- **The orphaned PR.** After a blind find, the agent's PR is still
  unvalidated. Out of scope by design (`architecture.md §Out of scope`);
  nothing here improves it.
- **A real rate limit.** The failure is simulated through `FakeGh`'s
  `failing=` vocabulary, which raises what `cli.CLI_FAILURES` catches.
  That is the same class `gh_runner` documents, not a live rate limit.
