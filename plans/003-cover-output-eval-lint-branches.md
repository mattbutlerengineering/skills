# Plan 003: Cover `check_output_evals`' untested defect branches

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 8399f85..HEAD -- lint.py tests/test_lint_checkers.py`
> If `check_output_evals` in `lint.py` changed since this plan was written
> (issue #25 rewrites it through `eval_schema.py`), compare the "Current
> state" excerpt against the live code; on a mismatch, treat it as a STOP
> condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (interacts with issue #25 — see Maintenance notes)
- **Category**: tests
- **Planned at**: commit `8399f85`, 2026-07-02

## Why this matters

`check_output_evals` is a CI gate: it runs on every push/PR via
`python3 lint.py`. It distinguishes six defect kinds, but only two are
tested (skill_name mismatch and missing run_fixture). The other four —
invalid JSON, stem-not-a-skill-slug, duplicate eval ids, empty
expectations — can silently regress to false-pass, and a lint gate that
passes broken eval sets defeats its purpose.

## Current state

- `lint.py:77-107` at commit `8399f85` — the checker:

```python
def check_output_evals(root):
    def problems_for(path):
        slug = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            return [f"evals/output/{path.name} is not valid JSON: {err}"]
        evals = data.get("evals", [])
        ids = [e.get("id") for e in evals]
        return (
            ([f"evals/output/{path.name} stem is not a skill slug"]
             if slug not in ALL_SKILLS else [])
            + ([f"evals/output/{path.name} skill_name is "
                f"{data.get('skill_name')!r}, expected {slug!r}"]
               if data.get("skill_name") != slug else [])
            + [f"evals/output/{path.name} has duplicate eval id {i!r}"
               for i in sorted({i for i in ids if ids.count(i) > 1})]
            + [f"evals/output/{path.name} eval {e.get('id')!r} has no "
               "expectations"
               for e in evals if not e.get("expectations")]
            + [f"evals/output/{path.name} eval {e.get('id')!r} run_fixture "
               f"{e.get('run_fixture')!r} does not exist"
               for e in evals
               if e.get("run_fixture")
               and not (root / e["run_fixture"]).is_dir()]
        )
    output_dir = root / "evals" / "output"
    if not output_dir.is_dir():
        return []
    return [p for path in sorted(output_dir.glob("*.json"))
            for p in problems_for(path)]
```

- `tests/test_lint_checkers.py` — the existing test module. Its pattern:
  `make_clean_tree(root)` seeds a minimal zero-problem tree (including
  `evals/output/idea.json` with one valid eval and the fixture dir
  `evals/fixtures/seeded-run`); each defect test subclasses
  `CheckerTreeTest` (tempdir + clean tree in `setUp`), breaks ONE aspect,
  and asserts the checker's **exact problem strings**. The existing
  output-eval test to model after (`tests/test_lint_checkers.py:158-170`):

```python
class TestOutputEvals(CheckerTreeTest):
    def test_skill_name_mismatch_and_missing_fixture(self):
        output_dir = self.root / "evals" / "output"
        (output_dir / "idea.json").write_text(json.dumps({
            "skill_name": "prd",
            "evals": [{"id": 1, "expectations": ["x"],
                       "run_fixture": "evals/fixtures/absent"}],
        }), encoding="utf-8")
        self.assertEqual(
            lint.check_output_evals(self.root),
            ["evals/output/idea.json skill_name is 'prd', expected 'idea'",
             "evals/output/idea.json eval 1 run_fixture "
             "'evals/fixtures/absent' does not exist"])
```

- Repo conventions: problem-string-list contracts asserted exactly; tests
  through the public checker interface (`lint.check_output_evals(root)`),
  never through private helpers.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| One test class | `python3 -m unittest tests.test_lint_checkers.TestOutputEvals -v` | all pass |
| Tests   | `python3 -m unittest discover tests` | `OK`, exit 0 |
| Lint    | `python3 lint.py` | `lint: 0 problem(s) across 11 skills`, exit 0 |

## Scope

**In scope**:
- `tests/test_lint_checkers.py` — add tests to the existing
  `TestOutputEvals` class only.

**Out of scope** (do NOT touch):
- `lint.py` — read-only. These are characterization tests of the current
  contract.
- `make_clean_tree` — do not change the seeded tree; write defect files
  inside each test like the existing test does.
- `eval_schema.py` — issue #25's territory.

## Git workflow

- Branch: `test/output-eval-lint-branches` off `main`.
- Conventional Commits, e.g. `test: cover check_output_evals defect branches`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Add the four missing branch tests

Append to `class TestOutputEvals` in `tests/test_lint_checkers.py`
(after `test_skill_name_mismatch_and_missing_fixture`):

```python
    def test_invalid_json_is_reported_alone(self):
        (self.root / "evals" / "output" / "idea.json").write_text(
            "{nope", encoding="utf-8")
        problems = lint.check_output_evals(self.root)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            "evals/output/idea.json is not valid JSON: "))

    def test_stem_that_is_not_a_skill_slug(self):
        (self.root / "evals" / "output" / "bogus.json").write_text(
            json.dumps({"skill_name": "bogus", "evals": []}),
            encoding="utf-8")
        problems = lint.check_output_evals(self.root)
        self.assertIn("evals/output/bogus.json stem is not a skill slug",
                      problems)

    def test_duplicate_eval_ids_reported_once_per_id(self):
        (self.root / "evals" / "output" / "idea.json").write_text(
            json.dumps({"skill_name": "idea", "evals": [
                {"id": 1, "expectations": ["x"]},
                {"id": 1, "expectations": ["y"]},
                {"id": 2, "expectations": ["z"]},
            ]}), encoding="utf-8")
        self.assertEqual(
            lint.check_output_evals(self.root),
            ["evals/output/idea.json has duplicate eval id 1"])

    def test_eval_with_no_expectations(self):
        (self.root / "evals" / "output" / "idea.json").write_text(
            json.dumps({"skill_name": "idea", "evals": [
                {"id": 1, "expectations": []},
                {"id": 2},
            ]}), encoding="utf-8")
        self.assertEqual(
            lint.check_output_evals(self.root),
            ["evals/output/idea.json eval 1 has no expectations",
             "evals/output/idea.json eval 2 has no expectations"])
```

Notes on expected strings (derived from the code excerpt — verify against
the live code if anything fails):
- The duplicate-id message uses `{i!r}` — for the integer id `1` that
  renders as `1`, not `'1'`.
- The no-expectations message uses `{e.get('id')!r}` — integer ids render
  bare; a missing `expectations` key and an empty list both trigger it.
- `bogus.json` with matching `skill_name: "bogus"` isolates the stem
  branch (skill_name mismatch would otherwise also fire — it compares
  against the stem, so keeping them equal yields exactly one problem).

**Verify**: `python3 -m unittest tests.test_lint_checkers.TestOutputEvals -v`
→ 5 tests, all pass. If an exact-string assertion fails, read the live
`check_output_evals` and fix the *test's expected string* to match the
code — never the other way around (characterization tests document current
behavior).

### Step 2: Full gates

**Verify**: `python3 -m unittest discover tests` → all pass;
`python3 lint.py` → `lint: 0 problem(s) across 11 skills`.

### Step 3: Commit

```bash
git add tests/test_lint_checkers.py
git commit -m "test: cover check_output_evals defect branches"
```

## Test plan

This plan IS the test plan: the four untested branches (invalid JSON
short-circuit, non-slug stem, duplicate ids deduped and sorted, empty/absent
expectations), asserted as exact problem strings through the public checker
interface. Pattern: the existing `TestOutputEvals` test in the same class.

## Done criteria

- [ ] `python3 -m unittest tests.test_lint_checkers.TestOutputEvals -v` → 5 tests pass
- [ ] `python3 -m unittest discover tests` exits 0
- [ ] `python3 lint.py` exits 0
- [ ] `git status --short` shows only `tests/test_lint_checkers.py` modified
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `check_output_evals` no longer matches the excerpt — issue #25 (output
  evals through `eval_schema.py`) has likely landed; these tests belong in
  that new shape instead, so report rather than writing tests against a
  moved contract.
- A test reveals the checker crashing (not just a wrong string) on any of
  these inputs — that's a production bug; report it, don't patch `lint.py`.

## Maintenance notes

- **Issue #25** plans to move output-eval shape validation into
  `eval_schema.py` with lint as a thin caller (mirroring ADR-0022). These
  tests pin today's problem strings; when #25 lands, they should move with
  the code (same strings, new owner module) — that migration is #25's job,
  and having these tests first makes that refactor safe.
- Reviewer should scrutinize: assertions are exact-match lists where the
  branch under test is the only one firing (test isolation per branch).
