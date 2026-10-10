# Knowledge base — first paired ablation (2026-10-10)

The paired test ADR-0078 names: the same tasks run with the knowledge base
present and absent, on this repo, reporting pass rate, steps and cost.
Record: `plugin-evals/records/2026-10-10-3.json` (copied unedited from the
run's `aggregate-result.json`). Cases: `plugin-evals/knowledge-base/`.

## Method

- Each workspace is this repo at `756e9a8` (`git archive`). Arm **on**
  keeps `docs/kb/` and the generated block in `CLAUDE.md`/`AGENTS.md`;
  arm **off** removes both. Nothing else differs (`seed.sh`).
- Three questions, one per seeded page, each answerable from the repo
  without the knowledge base (the facts are also in code and ADRs):
  manifest regeneration with a stray `.orig`, a PR body with no work
  order, a sample id inside a code fence.
- Read-only tools (Read, Glob, Grep), `claude-sonnet-5`, judge
  `claude-haiku-4-5` (three votes), 3 runs per case, `--max-cost-usd 8`.
  Total cost $4.06; not partial.

## Results

| Task | Pass off → on | Mean turns off → on | Cost off → on |
|---|---|---|---|
| gates-scan | 3/3 → 3/3 | 18.0 → 13.3 | $1.42 → $0.83 |
| manifest-regen | 3/3 → 3/3 | 20.3 → 8.3 | $0.77 → $0.37 |
| pr-body | 0/3 → 0/3 | 2.3 → 2.7 | $0.42 → $0.26 |

## Reading

- **Correctness: no change.** Where the agent searched, it found the fact
  either way; where it didn't search, the knowledge base did not help.
- **Efficiency: large on the two tasks where the agent investigated** —
  roughly half the turns and 41–52% less cost. This matches the evidence
  survey's prediction (`knowledge-base-evidence.md`): the win is
  efficiency, not correctness.
- **pr-body fails in both arms.** With the index line in the always-loaded
  file, the agent still drafted a generic body in 1–4 turns without
  opening the page. An index line that names a fact is not enough when
  the task doesn't look like it needs looking up; the guardrail form
  ("do not X") belongs in the always-loaded file itself, as ADR-0078
  already says for "do not" rules.

## Limits

n = 3 per arm, three tasks, one repo, one model. Read as a direction, not
a rate. Under ADR-0081 clause 5 this record is supporting evidence and
does not graduate the LEDGER row; `draft` → `used-once` still takes a
real run of the skill.
