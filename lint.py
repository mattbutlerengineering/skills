#!/usr/bin/env python3
"""Structural lint for the idea-to-prod plugin.

Checks the things that break an install or the router: manifest validity,
skill frontmatter, artifact templates, router references, protocol doc,
and ledger coverage. Exit 0 = clean, 1 = problems (printed one per line).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGES = ["idea", "prd", "ux-design", "architect", "decompose",
          "implement", "verify", "review", "ship", "operate"]
# implement's artifact is code itself; every other stage ships a template
TEMPLATED_STAGES = [s for s in STAGES if s != "implement"]
ALL_SKILLS = ["next"] + STAGES
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def read_frontmatter(path):
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        return None
    return dict(
        (line.split(":", 1)[0].strip(), line.split(":", 1)[1].strip())
        for line in match.group(1).splitlines()
        if ":" in line
    )


def check_manifest():
    path = ROOT / ".claude-plugin" / "plugin.json"
    if not path.is_file():
        return ["missing .claude-plugin/plugin.json"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [f"plugin.json is not valid JSON: {err}"]
    return [f"plugin.json missing field: {field}"
            for field in ("name", "description", "version")
            if not data.get(field)]


def check_skills():
    def problems_for(slug):
        skill = ROOT / "skills" / slug / "SKILL.md"
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


def check_templates():
    return [f"missing skills/{slug}/TEMPLATE.md"
            for slug in TEMPLATED_STAGES
            if not (ROOT / "skills" / slug / "TEMPLATE.md").is_file()]


def check_router():
    router = ROOT / "skills" / "next" / "SKILL.md"
    if not router.is_file():
        return []  # absence already reported by check_skills
    text = router.read_text(encoding="utf-8")
    return [f"router never mentions stage skill {slug!r}"
            for slug in STAGES if slug not in text]


def check_protocol():
    path = ROOT / "docs" / "pipeline-protocol.md"
    return [] if path.is_file() else ["missing docs/pipeline-protocol.md"]


def check_ledger():
    path = ROOT / "LEDGER.md"
    if not path.is_file():
        return ["missing LEDGER.md"]
    text = path.read_text(encoding="utf-8")
    return [f"LEDGER.md has no row for skill {slug!r}"
            for slug in ALL_SKILLS if slug not in text]


def main():
    problems = [p for checker in (check_manifest, check_skills,
                                  check_templates, check_router,
                                  check_protocol, check_ledger)
                for p in checker()]
    for problem in problems:
        print(f"LINT: {problem}")
    print(f"lint: {len(problems)} problem(s) across {len(ALL_SKILLS)} skills")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
