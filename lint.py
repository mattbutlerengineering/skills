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
from cli import report
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


# The protocol subsection the run-STARTING skills must recite. Derived,
# never a second list: a run starts at the head of the spine or at the
# maintenance entry, and those are protocol.py's to name.
RUN_STARTING = (STAGES[0], *MAINTENANCE_STAGES)
IN_FLIGHT_HEADING = "Work already in flight"


def _in_flight_problems(label, text):
    """A skill that starts a run recites the protocol's in-flight guard.

    Pins the section name and nothing else. Whether an agent actually
    looked at the open review work is not a thing a linter can know, and a
    checker that implied otherwise would be manufacturing exactly the
    false clean result that section exists to forbid.

    Whitespace is normalized before the comparison, unlike the artifact
    and stage recitals beside it. Those pin single tokens; this pins four
    words, and every one of these documents is hard-wrapped near 72
    columns — so a raw substring test fails a correct recital that happens
    to wrap, which is pinning the formatting and calling it the fact."""
    if IN_FLIGHT_HEADING.lower() in " ".join(text.lower().split()):
        return []
    return [f"{label} never names the protocol's "
            f"{IN_FLIGHT_HEADING!r} check, which is where a run that is "
            "already open in review gets caught"]


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
        if slug in RUN_STARTING:
            problems += _in_flight_problems(label, text)
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
        if slug in RUN_STARTING:
            problems += _in_flight_problems(label, text)
        problems += _capture_problems(label, text)
    return problems


# Bundled-file paths a SKILL.md names without linking them: "read
# `references/playbook.md`". Reference files use markdown links instead.
# The lookbehind keeps it from matching inside a longer path: without
# it, "../audit/references/playbook.md" also yields a bare
# "references/playbook.md" resolved against the wrong directory.
SKILL_ASSET = re.compile(
    r"(?<![A-Za-z0-9._/-])(?:references|assets)/[A-Za-z0-9._-]+")
# A markdown link to a local file. In-page anchors are not files.
LOCAL_LINK = re.compile(r"\]\(([^)#][^)]*)\)")


def named_files(path, skill_dir):
    """(reference-as-written, directory it resolves against) for every
    local file `path` names. Links resolve against the LINKING file's
    own directory, because that is how a reader resolves them — a
    reference file's `language.md` is its sibling, not the skill root's."""
    text = path.read_text(encoding="utf-8")
    named = [(ref, path.parent) for ref in LOCAL_LINK.findall(text)
             if "://" not in ref]
    if path.name == "SKILL.md":
        named += [(ref, skill_dir) for ref in SKILL_ASSET.findall(text)]
    return sorted(set(named))


def check_skill_assets(root):
    """Every local file a skill's own markdown names actually ships
    beside it, and none of them reaches outside the skill directory.
    Skills are self-contained (ADR-0008) and nothing enforced either
    half: a reference renamed, or never committed, fails only at runtime
    in the agent's hands — as a read that quietly returns nothing — and
    no gate sees it. Every .md in the skill is walked, not just
    SKILL.md, because reference files link to each other too. Missing
    SKILL.md files are check_skills' finding, not this one's."""
    def ships(directory, name):
        """Case-exact existence. Path.exists() answers with the local
        filesystem's case folding, so on macOS a SKILL.md naming
        'references/Playbook.md' passes beside a file called
        playbook.md — and then fails on the case-sensitive filesystem
        the plugin installs onto. Reading the directory is what makes
        this check unsatisfiable by the wrong file."""
        try:
            return name in {entry.name for entry in directory.iterdir()}
        except OSError:
            return False

    def problems_for(slug):
        skill_dir = root / "skills" / slug
        if not (skill_dir / "SKILL.md").is_file():
            return []
        problems = []
        for path in sorted(skill_dir.rglob("*.md")):
            source = path.relative_to(skill_dir).as_posix()
            for ref, base in named_files(path, skill_dir):
                target = (base / ref).resolve()
                if not target.is_relative_to(skill_dir.resolve()):
                    problems.append(
                        f"skills/{slug}/{source} names {ref!r}, which is "
                        "outside the skill directory (ADR-0008: skills "
                        "are self-contained)")
                elif not ships(target.parent, target.name):
                    problems.append(f"skills/{slug}/{source} names {ref!r}, "
                                    "which does not exist")
        return problems

    return [p for slug in ALL_SKILLS + extra_skills(root)
            for p in problems_for(slug)]


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
    — are English and stay unpinned; see the note in tests/test_lint
    so that limit is recorded rather than assumed covered.
    """
    router = protocol.skill_path(root, "next")
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


def check_readme_skills(root):
    """Every skill in the taxonomy is named in README.md. The README is
    where a reader learns what the plugin ships, and it is prose — so a
    skill can be added, registered, tested, and released without the
    README ever hearing about it. That is not hypothetical: it is how
    interactive-architecture-diagram shipped undocumented. Same bar and
    same shape as check_ledger, for the same reason."""
    path = root / "README.md"
    if not path.is_file():
        return ["missing README.md"]
    text = path.read_text(encoding="utf-8")
    return [f"README.md never names skill {slug!r}"
            for slug in ALL_SKILLS + extra_skills(root) if slug not in text]


def check_protocol(root):
    path = root / "docs" / "pipeline-protocol.md"
    return [] if path.is_file() else ["missing docs/pipeline-protocol.md"]


# A row of either orientation table in the protocol doc:
# "| UX Design | `ux.md` | file exists ... |".
# The hyphen matters: the doc writes stages in prose ("UX Design"),
# but a slug ("ux-design") is just as reasonable, and a row this
# fails to match is dropped silently — surfacing as an order
# mismatch rather than as the formatting difference it is.
TABLE_ROW = re.compile(r"^\|\s*([A-Za-z][A-Za-z -]*?)\s*\|\s*(.+?)\s*\|")
# The artifact cell when it names a file rather than what the stage
# produces. Implement's cell reads "code" and is deliberately not a file.
ARTIFACT_CELL = re.compile(r"^`([a-z]+\.md)`$")


def doc_table(text, heading):
    """The (stage-slug, artifact-or-None) rows of the markdown table that
    follows `heading` in the protocol doc, in document order. Stage names
    are title-case prose there and slugs in protocol.py, so "UX Design"
    normalizes to "ux-design"; the artifact is None when the cell names a
    product rather than a file. Returns [] when the heading or its table
    is absent, which check_protocol_tables reports as its own problem."""
    after = text.split(heading, 1)
    if len(after) < 2:
        return []
    rows = []
    for line in after[1].splitlines():
        if not line.startswith("|"):
            if rows:
                break       # the table ended
            continue        # prose between the heading and the table
        match = TABLE_ROW.match(line)
        if not match:
            continue
        stage, artifact = match.groups()
        if stage.lower() in ("stage", "---"):
            continue
        cell = ARTIFACT_CELL.match(artifact)
        rows.append((stage.lower().replace(" ", "-"),
                     cell.group(1) if cell else None))
    return rows


def check_protocol_tables(root):
    """The protocol doc's two orientation tables agree with protocol.py's
    walk tables. Both are authorities and neither derives from the other:
    in a stamped repo the offline tools read protocol.py, while in a
    consuming repo the doc is what an agent reads at runtime — doctor
    calls it the runtime interface precisely because there is no
    protocol.py to fall back on there. A stage added to one and not the
    other routes two different ways in the same pipeline, and nothing
    was red.

    Deliberately NOT covered, so a green run is not misread: the
    "Complete when" column, which carries the Implement checkbox rule and
    the ux:/re-entry: conditionals in English. Those still restate
    protocol._stage_complete with nothing pinning them."""
    path = root / "docs" / "pipeline-protocol.md"
    if not path.is_file():
        return []  # absence already reported by check_protocol
    text = path.read_text(encoding="utf-8")
    problems = []
    for heading, table in (("## Artifacts are the state",
                            protocol.STAGE_ARTIFACTS),
                           ("### Maintenance-run orientation",
                            protocol.MAINTENANCE_STAGE_ARTIFACTS)):
        rows = doc_table(text, heading)
        if not rows:
            problems.append(f"protocol doc has no orientation table under "
                            f"{heading!r} — it is what an agent reads to "
                            "orient a run, and nothing else states the order")
            continue
        documented = [stage for stage, _ in rows]
        expected = [stage for stage, _ in table]
        if documented != expected:
            problems.append(
                f"protocol doc's {heading!r} table is out of step with "
                f"protocol.py: expected {' → '.join(expected)}, "
                f"got {' → '.join(documented)}")
            continue
        problems.extend(
            f"protocol doc gives stage {stage!r} artifact {named!r}; "
            f"protocol.py reads {artifact!r}"
            for (stage, named), (_, artifact) in zip(rows, table)
            if named is not None and named != artifact)
    return problems


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
            check_skill_recitals, check_skill_assets, check_templates,
            check_router, check_readme_skills, check_protocol,
            check_protocol_tables, check_backlog, check_evals,
            check_output_evals, check_ledger, check_ledger_links)


def main():
    root = Path(__file__).resolve().parent
    problems = [p for checker in CHECKERS for p in checker(root)]
    checked = len(ALL_SKILLS) + len(extra_skills(root))
    # Checker strings carry no label (their suite pins them bare); the
    # LINT: prefix is print-time dress, applied before the shared epilogue.
    return report("lint", [f"LINT: {p}" for p in problems],
                  suffix=f" across {checked} skills")


if __name__ == "__main__":
    sys.exit(main())
