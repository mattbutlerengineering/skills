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
                      TEMPLATED_STAGES)


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
    """Frontmatter contract per skill: protocol.skill_frontmatter_problems
    owns the rules and the strings (ADR-0052); this checker keeps the
    taxonomy walk."""
    def problems_for(slug):
        return protocol.skill_frontmatter_problems(root, slug)
    # An unregistered dir is itself a problem: taxonomy membership is what
    # subjects a skill to the routing-coverage policy (ADR-0023). Its
    # frontmatter is still checked so both defects surface in one run.
    return [p for slug in ALL_SKILLS for p in problems_for(slug)] + [
        p for slug in extra_skills(root)
        for p in ([f"skills/{slug} is not in the skill taxonomy "
                   "(protocol.py ALL_SKILLS)"] + problems_for(slug))
    ]


# The recital vocabulary check_skill_recitals is strict about (ADR-0052):
# a numbered process step, a backticked artifact filename inside one, and
# a "next stage is <stage>" claim (stage names read hyphens as spaces,
# and phrases may wrap across lines).
STEP_LINE = re.compile(r"^\d+\.\s")
GATE_ARTIFACT = re.compile(r"`([a-z0-9._-]+\.md)`")


def _numbered_steps(text):
    """The `N. ` process steps of a skill body; a step runs to the next
    numbered step or heading."""
    steps, current = [], None
    for line in text.splitlines():
        if STEP_LINE.match(line):
            if current is not None:
                steps.append("\n".join(current))
            current = [line]
        elif line.startswith("#"):
            if current is not None:
                steps.append("\n".join(current))
            current = None
        elif current is not None:
            current.append(line)
    if current is not None:
        steps.append("\n".join(current))
    return steps


def _next_stage_claims(text):
    """Every stage a 'next stage is <stage>' phrase in the body names."""
    normalized = re.sub(r"[-\s]+", " ", text.lower())
    return [slug for slug in STAGES + MAINTENANCE_STAGES
            if re.search(rf"next stage is {slug.replace('-', ' ')}\b",
                         normalized)]


def _gate_problems(label, text, expected, upstream, spine_artifacts):
    """The soft-gate step names every expected predecessor artifact and
    no stage artifact from further down the pipeline."""
    steps = [s for s in _numbered_steps(text) if "soft gate" in s.lower()]
    if not steps:
        return [f"{label} has no soft-gate step"]
    named = {a for step in steps for a in GATE_ARTIFACT.findall(step)}
    return ([f"{label} soft gate never names predecessor artifact {a!r}"
             for a in sorted(expected - named)]
            + [f"{label} soft gate names downstream artifact {a!r}"
               for a in sorted(named & (spine_artifacts - upstream))])


def _hand_off_problems(label, slug, text, successor, skip_target):
    """Every 'next stage is <stage>' claim names the table successor; the
    stage before the conditional UX stage also names the skip target."""
    claims = _next_stage_claims(text)
    if successor is None:
        return [f"{label} states next stage {claim!r}, "
                f"but {slug!r} completes the run" for claim in claims]
    problems = ([f"{label} never states next stage {successor!r}"]
                if successor not in claims else [])
    problems += [f"{label} states next stage {claim!r}, "
                 f"expected {successor!r}"
                 for claim in claims if claim != successor]
    if skip_target and not re.search(
            rf"\b{skip_target}\b", re.sub(r"[-\s]+", " ", text.lower())):
        problems.append(f"{label} never names the ux-skip target "
                        f"{skip_target!r}")
    return problems


def _capture_problems(label, text):
    """Capture's hand-off is the re-entry conditional: both recorded
    frontmatter options must be recited, and any 'next stage is' claim
    must be one of the re-entry stages."""
    lowered = text.lower()
    problems = [f"{label} never records re-entry option {option!r}"
                for option in ("re-entry: implement", "re-entry: architect")
                if option not in lowered]
    return problems + [
        f"{label} states next stage {claim!r}, expected re-entry to "
        "'implement' or 'architect'"
        for claim in _next_stage_claims(text)
        if claim not in ("implement", "architect")]


def check_skill_recitals(root):
    """Stage-skill prose recites the protocol — soft-gate predecessor,
    own artifact, hand-off successor. Vended skills can't import
    protocol.py (ADR-0008), so the copies are forced; this checker pins
    them to STAGE_ARTIFACTS / MAINTENANCE_STAGE_ARTIFACTS so drift is
    loud (ADR-0052). Robust to phrasing, strict on the facts: artifact
    filenames and stage names."""
    spine = [stage for stage, _ in protocol.STAGE_ARTIFACTS]
    artifact = dict(protocol.STAGE_ARTIFACTS
                    + protocol.MAINTENANCE_STAGE_ARTIFACTS)
    spine_artifacts = {a for _, a in protocol.STAGE_ARTIFACTS}
    problems = []
    for i, slug in enumerate(spine):
        path = protocol.skill_path(root, slug)
        if not path.is_file():
            continue  # absence already reported by check_skills
        text = path.read_text(encoding="utf-8")
        label = f"skills/{slug}/SKILL.md"
        if i > 0:
            # the conditional UX stage gates on its own artifact OR the
            # one before it (ADR-0017), so its successor's gate must
            # recite both
            expected = {artifact[spine[i - 1]]}
            if spine[i - 1] == "ux-design":
                expected.add(artifact[spine[i - 2]])
            upstream = {artifact[s] for s in spine[:i]}
            problems += _gate_problems(label, text, expected, upstream,
                                       spine_artifacts)
        if f"`{artifact[slug]}`" not in text:
            problems.append(f"{label} never names its artifact "
                            f"{artifact[slug]!r}")
        successor = spine[i + 1] if i + 1 < len(spine) else None
        skip_target = spine[i + 2] if successor == "ux-design" else None
        problems += _hand_off_problems(label, slug, text, successor,
                                       skip_target)
    for slug in MAINTENANCE_STAGES:  # entry stages: no soft gate to pin
        path = protocol.skill_path(root, slug)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        label = f"skills/{slug}/SKILL.md"
        if f"`{artifact[slug]}`" not in text:
            problems.append(f"{label} never names its artifact "
                            f"{artifact[slug]!r}")
        problems += _capture_problems(label, text)
    return problems


def check_templates(root):
    return [f"missing skills/{slug}/TEMPLATE.md"
            for slug in TEMPLATED_STAGES
            if not (root / "skills" / slug / "TEMPLATE.md").is_file()]


def check_router(root):
    router = protocol.skill_path(root, "next")
    if not router.is_file():
        return []  # absence already reported by check_skills
    text = router.read_text(encoding="utf-8")
    # the full routed taxonomy: the spine plus maintenance entry points
    # (ADR-0025) — utility skills are excluded because the router never
    # routes to them (ADR-0023)
    return [f"router never mentions stage skill {slug!r}"
            for slug in STAGES + MAINTENANCE_STAGES if slug not in text]


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


CHECKERS = (check_manifest, check_pi_package, check_skills,
            check_skill_recitals, check_templates, check_router,
            check_protocol, check_backlog, check_evals,
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
