# Every plugin-eval case carries its skill directory as a tag

- Status: accepted (Owner, 2026-10-14)
- Date: 2026-10-14

The Owner chose this on 2026-10-14, in session ("Retag + ADR for tag
rule"). It resolves issue #862. It supersedes in part ADR-0081: the
Consequences clause that no detector or lint check reads
`plugin-evals/`, and that section's count of five cases. The rest of
ADR-0081 stands.

## Context

ADR-0081 §1 tags each case with its skill's slug "so `--tag <skill>`
runs one suite", and CLAUDE.md documents `--tag <skill>` the same way.
Nothing checked it. When the `knowledge-base` suite landed, its six
cases were tagged only with their arm, `[kb-on]` or `[kb-off]`, so the
documented `claude plugin eval . --tag knowledge-base` selected none of
them. The other five cases still followed the rule.

ADR-0081's Consequences also said the tree holds five cases. It holds
eleven: two each for `lean` and `next`, one for `implement`, and six
for `knowledge-base`.

## Decision

1. **Every case's tags include its skill directory name.** A case at
   `plugin-evals/<skill>/<case>/prompt.md` lists `<skill>` in its
   frontmatter `tags`, so `--tag <skill>` always selects the whole
   suite.
2. **Arm tags are allowed as extras.** A paired suite may add tags that
   select one arm, such as `kb-on` and `kb-off`, after the skill tag:
   `tags: [knowledge-base, kb-on]`.
3. **A unit test reads `plugin-evals/` to hold the rule.**
   `tests/test_plugin_eval_tags.py` reads each case's frontmatter
   `tags` and fails on any case whose tags omit its directory name. It
   reads only the case prompts, never `plugin-evals/records/` or
   `plugin-evals/results/`, and makes no model call. It is a test, not
   a `gates.py` detector, and the markdown under `plugin-evals/` still
   sits outside the trees detectors C, D and I scan.

## Rejected alternatives

- **Document arm tags without a check.** That records the divergence
  instead of removing it, and the next suite can drift the same way
  with nothing to say so.
- **A `gates.py` detector or a `lint.py` checker.** Either would reach
  into a tree whose case format the CLI owns, for one rule over eleven
  files. A unit test over the live tree is enough, as `TestLockstep`
  already is for the Makefile.

## Consequences

- The six `knowledge-base` cases are retagged `[knowledge-base, kb-on]`
  and `[knowledge-base, kb-off]`. Only their tags change. The committed
  record `plugin-evals/records/2026-10-10-3.json` keeps the tags it was
  run with, since records are append-only.
- `plugin-evals/` holds eleven cases. At 3 runs per arm a full suite is
  66 agent runs plus judge calls.
- A new suite that forgets its skill tag fails the unit test suite in
  CI, before `--tag <skill>` can silently skip it.
