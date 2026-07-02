#!/usr/bin/env python3
"""Structural lint for the idea-to-prod plugin.

Checks the things that break an install or the router: manifest validity,
skill frontmatter, artifact templates, router references, protocol doc,
and ledger coverage. Exit 0 = clean, 1 = problems (printed one per line).

Every checker takes the repo root as a parameter; the CLI entry passes
the real repo, the test suite passes fixture trees.
"""
import json
import re
import sys
from pathlib import Path

from protocol import ALL_SKILLS, STAGES, TEMPLATED_STAGES, read_frontmatter


def check_manifest(root):
    path = root / ".claude-plugin" / "plugin.json"
    if not path.is_file():
        return ["missing .claude-plugin/plugin.json"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [f"plugin.json is not valid JSON: {err}"]
    return [f"plugin.json missing field: {field}"
            for field in ("name", "description", "version")
            if not data.get(field)]


def check_skills(root):
    def problems_for(slug):
        skill = root / "skills" / slug / "SKILL.md"
        if not skill.is_file():
            return [f"missing skills/{slug}/SKILL.md"]
        fm = read_frontmatter(skill)
        if fm is None:
            return [f"skills/{slug}/SKILL.md has no frontmatter block"]
        return (
            ([f"skills/{slug}/SKILL.md frontmatter name is "
              f"{fm.get('name')!r}, expected {slug!r}"]
             if fm.get("name") != slug else [])
            + ([f"skills/{slug}/SKILL.md frontmatter has no description"]
               if not fm.get("description") else [])
        )
    return [p for slug in ALL_SKILLS for p in problems_for(slug)]


def check_templates(root):
    return [f"missing skills/{slug}/TEMPLATE.md"
            for slug in TEMPLATED_STAGES
            if not (root / "skills" / slug / "TEMPLATE.md").is_file()]


def check_router(root):
    router = root / "skills" / "next" / "SKILL.md"
    if not router.is_file():
        return []  # absence already reported by check_skills
    text = router.read_text(encoding="utf-8")
    return [f"router never mentions stage skill {slug!r}"
            for slug in STAGES if slug not in text]


def check_protocol(root):
    path = root / "docs" / "pipeline-protocol.md"
    return [] if path.is_file() else ["missing docs/pipeline-protocol.md"]


def check_evals(root):
    path = root / "evals" / "routing.json"
    if not path.is_file():
        return ["missing evals/routing.json"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [f"evals/routing.json is not valid JSON: {err}"]
    if "version" not in data:
        return ["evals/routing.json missing 'version' field"]
    cases = data.get("cases", [])
    kinds = ("direct", "situational", "near-miss", "distractor", "router")

    ids = [c.get("id") for c in cases]
    problems = (
        [f"evals/routing.json has duplicate case id {i!r}"
         for i in sorted({i for i in ids if ids.count(i) > 1})]
        + [f"evals/routing.json case {c.get('id')!r} has invalid "
           f"expected {c.get('expected')!r}"
           for c in cases
           if c.get("expected") is not None
           and c.get("expected") not in ALL_SKILLS]
        + [f"evals/routing.json case {c.get('id')!r} has invalid "
           f"kind {c.get('kind')!r}"
           for c in cases if c.get("kind") not in kinds]
        + [f"evals/routing.json case {c.get('id')!r} has no query"
           for c in cases if not c.get("query")]
    )

    coverage = [c.get("expected") for c in cases]
    problems += [f"evals/routing.json covers skill {slug!r} in only "
                 f"{coverage.count(slug)} case(s), need >= 3"
                 for slug in ALL_SKILLS if coverage.count(slug) < 3]
    if coverage.count(None) < 3:
        problems += [f"evals/routing.json has only {coverage.count(None)} "
                     "distractor case(s) (expected: null), need >= 3"]
    return problems


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


def check_ledger(root):
    path = root / "LEDGER.md"
    if not path.is_file():
        return ["missing LEDGER.md"]
    text = path.read_text(encoding="utf-8")
    return [f"LEDGER.md has no row for skill {slug!r}"
            for slug in ALL_SKILLS if slug not in text]


EVAL_LINK = re.compile(r"\]\((evals/results/[^)]+)\)")


def check_ledger_links(root):
    """Every eval-evidence link in LEDGER.md resolves to a results file."""
    path = root / "LEDGER.md"
    if not path.is_file():
        return []  # absence already reported by check_ledger
    text = path.read_text(encoding="utf-8")
    return [f"LEDGER.md links to missing eval results file {target!r}"
            for target in EVAL_LINK.findall(text)
            if not (root / target).is_file()]


CHECKERS = (check_manifest, check_skills, check_templates, check_router,
            check_protocol, check_evals, check_output_evals, check_ledger,
            check_ledger_links)


def main():
    root = Path(__file__).resolve().parent
    problems = [p for checker in CHECKERS for p in checker(root)]
    for problem in problems:
        print(f"LINT: {problem}")
    print(f"lint: {len(problems)} problem(s) across {len(ALL_SKILLS)} skills")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
