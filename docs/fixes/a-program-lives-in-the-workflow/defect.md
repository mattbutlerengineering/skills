---
stage: capture
run: maintenance:a-program-lives-in-the-workflow
date: 2026-08-30
re-entry: implement
assumptions:
  - The synthesized action stays "opened" — the dispatch path stands in
    for a freshly opened PR, and every consumer branches on the PR body,
    author and labels rather than on the action word.
  - GITHUB_REPOSITORY stays the source of the repo slug, exactly as in
    the step being replaced, rather than gh's own {owner}/{repo} path
    placeholders — the substitution is a behaviour change nobody asked
    for.
  - The Collect findings step's set +e / exit 0 shell stays in the
    workflow. It captures make check's own exit code into $GITHUB_ENV
    and cannot be a make target. It is plumbing, not a repo tool.
---

# The workflow names a program of its own

## What is wrong

`.github/workflows/validator.yml` says, in its own header, that it
"names no commands of its own" and that "every step goes through a
`make` target". Three of its four jobs run a program:

```
run: |
  gh api "repos/${GITHUB_REPOSITORY}/pulls/${PR}" \
    | python3 -c 'import json, sys; print(json.dumps({"action": "opened", "pull_request": json.load(sys.stdin)}))' \
    > "${RUNNER_TEMP}/pr-event.json"
  echo "GITHUB_EVENT_PATH=${RUNNER_TEMP}/pr-event.json" >> "$GITHUB_ENV"
```

That program constructs the synthetic `pull_request` event the
PR-shaped legs consume through `cli.read_event` — the shape detector B
reads a PR body from, and the shape the two lifecycle label flips
resolve a work order from. It exists in three hand-maintained copies,
in a file mirrored VERBATIM into every stamped product repo, and the
repo denies its existence in three places.

## Reproduction

The claim, stated three times in the files this grep covers — the count
grew to five authored statements once the root Makefile's own header and
`factory_init.py`'s `missing_make_targets` were read, and to seven lines
once the two generated mirrors are counted (`verification.md` §1):

```
$ grep -rn "names no commands of its own\|name no commands of their own" \
    .github/workflows/validator.yml validator.py factory/templates/Makefile
.github/workflows/validator.yml:5:# why it names no commands of its own. Every step goes through a `make`
validator.py:6:The workflows name no commands of their own — they run `make` targets, and
factory/templates/Makefile:4:# stamped .github/workflows/validator.yml names no commands of its own, it
```

The program, present three times in the file that denies it:

```
$ grep -n "python3 -c" .github/workflows/validator.yml
58:            | python3 -c 'import json, sys; print(json.dumps({"action": "opened", "pull_request": json.load(sys.stdin)}))' \
116:            | python3 -c 'import json, sys; print(json.dumps({"action": "opened", "pull_request": json.load(sys.stdin)}))' \
165:            | python3 -c 'import json, sys; print(json.dumps({"action": "opened", "pull_request": json.load(sys.stdin)}))' \
```

And the test that is supposed to cover it cannot see the copies at all.
`tests/test_assembler.py`'s `test_dispatch_path_synthesizes_the_event_payload`
greps the whole file:

```python
text = self.VALIDATOR.read_text(encoding="utf-8")
self.assertIn("GITHUB_EVENT_PATH=", text)
self.assertIn('"action": "opened"', text)
```

`assertIn` over the whole file passes when ONE copy is right. Break two
of the three and the suite stays green — which is precisely the failure
this defect is about.

## The failure scenario

The event shape gains a field. Say a detector starts needing
`repository.full_name`, or the `action` word begins to matter to a
lifecycle leg. An editor updates the copy in the `check` job, watches
`make check` go green, and ships. The `review` and `needs-review-label`
jobs still build the old shape.

The result is two jobs disagreeing about the same PR on a
`workflow_dispatch` re-run — `check` passing while `review` reports a
different verdict, or a label flip silently skipping because the body
it read was assembled differently. Nothing fails loudly, and the
header told the editor there were no commands in the file to look for.

## Scope

The event shape has no owner in Python and no behavioural test. The fix
is the repo's own existing convention, not a new one: a tool invocation
goes through a `make` target, because the Makefile is the seam that
knows whether the tools sit at the root or under `tools/factory/`.

Out of scope: the `Collect findings` step's `set +e` / `exit 0`. It
captures `make check`'s exit code into `$GITHUB_ENV`, so it cannot
itself be a make target. The corrected claim names it rather than
pretending it is not there.

## Re-entry

`implement`. The defect is understood and the design is the convention
the repo already holds; nothing here needs an architecture stage.
