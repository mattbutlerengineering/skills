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

import eval_schema
import protocol
from protocol import (ALL_SKILLS, MAINTENANCE_STAGES, STAGES,
                      TEMPLATED_STAGES, read_frontmatter)


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


def check_pi_package(root):
    """The oh-my-pi (omp) discovery manifest. Its own packaging layer beside
    the Claude plugin manifest (ADR-0027): omp finds the skills through a
    `package.json` `pi.skills` entry. Guarded like check_manifest so the
    dual-target packaging can't silently drift."""
    path = root / "package.json"
    if not path.is_file():
        return ["missing package.json"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [f"package.json is not valid JSON: {err}"]
    problems = []
    if data.get("private") is not True:
        problems.append("package.json must set private: true")
    keywords = data.get("keywords")
    if not isinstance(keywords, list) or "pi-package" not in keywords:
        problems.append("package.json keywords must include 'pi-package'")
    pi = data.get("pi")
    skills = pi.get("skills") if isinstance(pi, dict) else None
    if not isinstance(skills, list) or "./skills" not in skills:
        problems.append("package.json pi.skills must include './skills'")
    return problems


def extra_skills(root):
    """Skill directories on disk that the protocol taxonomy doesn't know —
    a dir under skills/ installs as a skill, so the frontmatter and ledger
    checks must see it even before protocol.py registers it (issue #28).
    Dotdirs are ignored (harnesses don't install them)."""
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(p.name for p in skills_dir.iterdir()
                  if p.is_dir() and not p.name.startswith(".")
                  and p.name not in ALL_SKILLS)


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
            + ([f"skills/{slug}/SKILL.md description exceeds Pi's "
                "1024-char limit"]
               if fm.get("description")
               and len(fm["description"]) > 1024 else [])
        )
    # An unregistered dir is itself a problem: taxonomy membership is what
    # subjects a skill to the routing-coverage policy (ADR-0023). Its
    # frontmatter is still checked so both defects surface in one run.
    return [p for slug in ALL_SKILLS for p in problems_for(slug)] + [
        p for slug in extra_skills(root)
        for p in ([f"skills/{slug} is not in the skill taxonomy "
                   "(protocol.py ALL_SKILLS)"] + problems_for(slug))
    ]


def check_templates(root):
    return [f"missing skills/{slug}/TEMPLATE.md"
            for slug in TEMPLATED_STAGES
            if not (root / "skills" / slug / "TEMPLATE.md").is_file()]


# The router's hand-off list: "  - <slug> -> the `<slug>` skill".
HANDOFF_LINE = re.compile(r"^\s*-\s+([a-z][a-z-]*)\s+→\s+the\s+"
                          r"`([a-z][a-z-]*)`\s+skill")


def routed_order():
    """The order the router must hand off in, DERIVED from protocol's two
    walk tables rather than restated: the product/feature walk, preceded by
    any stage only a maintenance run enters (ADR-0025). The maintenance
    tail is a suffix of the product walk, so this is a total order, not a
    merge that has to pick sides."""
    product = [stage for stage, _ in protocol.STAGE_ARTIFACTS]
    entry = [stage for stage, _ in protocol.MAINTENANCE_STAGE_ARTIFACTS
             if stage not in product]
    return entry + product


def check_router(root):
    """The router skill is prose an agent reads at RUNTIME, so drift in it
    is drift in the shipped behaviour — and nothing was pinning it. The
    mention check below passes on the word "idea" appearing anywhere, so a
    hand-off list that omitted a stage, named a retired one, or listed them
    out of pipeline order stayed green.

    What is checkable is the list itself: its membership and its order are
    derivable from protocol's walk tables. The CONDITIONALS the router also
    carries — the UX field, the re-entry field, the Implement checkbox rule
    — are English and stay unpinned; see the note in tests/test_lint_checkers
    so that limit is recorded rather than assumed covered.
    """
    router = root / "skills" / "next" / "SKILL.md"
    if not router.is_file():
        return []  # absence already reported by check_skills
    text = router.read_text(encoding="utf-8")
    # the full routed taxonomy: the spine plus maintenance entry points
    # (ADR-0025) — utility skills are excluded because the router never
    # routes to them (ADR-0023)
    problems = [f"router never mentions stage skill {slug!r}"
                for slug in STAGES + MAINTENANCE_STAGES if slug not in text]
    listed = []
    for line in text.splitlines():
        match = HANDOFF_LINE.match(line)
        if not match:
            continue
        stage, skill = match.groups()
        if stage != skill:
            problems.append(f"router hands {stage!r} off to the {skill!r}"
                            " skill; a stage routes to the skill of the"
                            " same name")
        listed.append(stage)
    if not listed:
        problems.append("router has no hand-off list — step 5's"
                        " '<stage> → the `<stage>` skill' lines are what"
                        " route a run, and nothing else names the order")
        return problems
    expected = routed_order()
    unknown = [stage for stage in listed if stage not in expected]
    problems.extend(f"router hands off to {stage!r}, which protocol's walk"
                    " tables do not route to" for stage in unknown)
    missing = [stage for stage in expected if stage not in listed]
    problems.extend(f"router's hand-off list omits stage skill {stage!r}"
                    for stage in missing)
    if not unknown and not missing and listed != expected:
        problems.append("router's hand-off list is out of pipeline order:"
                        f" expected {' → '.join(expected)}, got"
                        f" {' → '.join(listed)}")
    return problems


def check_protocol(root):
    path = root / "docs" / "pipeline-protocol.md"
    return [] if path.is_file() else ["missing docs/pipeline-protocol.md"]


def check_evals(root):
    _, problems = eval_schema.load(root / "evals" / "routing.json",
                                   ALL_SKILLS, label="evals/routing.json")
    return problems


def check_output_evals(root):
    """Record shape is owned by eval_schema (issue #25); this checker keeps
    the filesystem half — file walk, JSON parse, stem naming, fixture stat."""
    def problems_for(path):
        slug = path.stem
        label = f"evals/output/{path.name}"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            return [f"{label} is not valid JSON: {err}"]
        return (
            ([f"{label} stem is not a skill slug"]
             if slug not in ALL_SKILLS else [])
            + eval_schema.validate_output(data, slug, label)
            + [f"{label} eval {eid!r} run_fixture {ref!r} does not exist"
               for eid, ref in eval_schema.fixture_refs(data)
               if not (root / ref).is_dir()]
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
            for slug in ALL_SKILLS + extra_skills(root) if slug not in text]


def check_backlog(root):
    """The seed backlog is strictly opt-in (ADR-0029): an absent
    docs/backlog.md is no problem. protocol.check_backlog owns the entry
    grammar; this checker keeps the filesystem half — existence and
    readability."""
    path = root / "docs" / "backlog.md"
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as err:
        return [f"backlog: docs/backlog.md is unreadable: {err}"]
    return protocol.check_backlog(text)


EVAL_LINK = re.compile(r"\]\((evals/results/[^)]+)\)")


def check_ledger_links(root):
    """Every eval-evidence link in LEDGER.md follows the results naming
    grammar (eval_schema owns it, issue #26) and resolves to a results
    file. Both facts are independent, so an off-grammar link to a missing
    target surfaces both problems in one run."""
    path = root / "LEDGER.md"
    if not path.is_file():
        return []  # absence already reported by check_ledger
    targets = EVAL_LINK.findall(path.read_text(encoding="utf-8"))
    return (
        [f"LEDGER.md links to eval results path {target!r} "
         "that does not match the results naming grammar"
         for target in targets
         if not eval_schema.valid_results_link(target)]
        + [f"LEDGER.md links to missing eval results file {target!r}"
           for target in targets if not (root / target).is_file()]
    )


CHECKERS = (check_manifest, check_pi_package, check_skills, check_templates,
            check_router, check_protocol, check_backlog, check_evals,
            check_output_evals, check_ledger, check_ledger_links)


def main():
    root = Path(__file__).resolve().parent
    problems = [p for checker in CHECKERS for p in checker(root)]
    for problem in problems:
        print(f"LINT: {problem}")
    checked = len(ALL_SKILLS) + len(extra_skills(root))
    print(f"lint: {len(problems)} problem(s) across {checked} skills")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
