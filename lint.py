#!/usr/bin/env python3
"""Structural lint for the idea-to-prod plugin.

Checks the things that break an install or the router: manifest validity,
skill frontmatter, artifact templates, router references, protocol doc,
and ledger coverage. Exit 0 = clean, 1 = problems (printed one per line).

Every checker takes the repo root as a parameter; the CLI entry passes
the real repo, the test suite passes fixture trees.
"""
import ast
import inspect
import json
import re
import sys
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

import eval_schema
import protocol
from cli import read_file, report
from protocol import (ALL_SKILLS, MAINTENANCE_STAGES, STAGES,
                      TEMPLATED_STAGES, UTILITY_SKILLS)


def check_manifest(root):
    data, problem = read_file(root / ".claude-plugin" / "plugin.json",
                              "plugin.json", dict)
    if problem:
        return [problem]
    if data is None:
        return ["missing .claude-plugin/plugin.json"]
    return [f"plugin.json missing field: {field}"
            for field in ("name", "description", "version")
            if not data.get(field)]


def check_plugin_skills(root):
    """Every utility skill in the taxonomy is named in plugin.json's
    description. That string is what a reader sees first when deciding
    whether to install, and check_manifest asserts only that the field is
    non-empty — so a skill can be added, registered, tested and released
    without the install surface ever hearing about it. That is the same
    gap check_readme_skills closes for README.md, on the surface that had
    no checker: three diagram skills went unnamed here while the README
    and the ledger were held to the full list.

    Utility skills only. The description names stages as title-case prose
    ("Idea", "UX Design") rather than by slug, so holding the whole
    taxonomy to a substring test would demand a restyling nobody asked
    for. The parenthetical utility list is the part that claims to be
    exhaustive, so it is the part held to the taxonomy.

    Whole slugs, never substrings — the same rule check_readme_skills
    holds README.md to, and the same function: `architecture-diagram`
    occurs inside `interactive-architecture-diagram`, so a plain `in`
    test would call the list complete after the shorter name was dropped
    from it — a blind spot for one of the very skills this checker
    exists to catch. names_slug is the one owner of that rule; this
    checker no longer retypes it.

    A missing, unreadable, unparseable or non-object manifest returns
    nothing — read_file's problem is discarded on purpose: check_manifest
    already reports it, and this checker reporting it too would give one
    broken file two problem strings.
    """
    data, _ = read_file(root / ".claude-plugin" / "plugin.json",
                        "plugin.json", dict)
    if data is None:
        return []
    text = data.get("description") or ""
    return [f"plugin.json's description never names utility skill {slug!r}"
            for slug in UTILITY_SKILLS if not names_slug(text, slug)]


def check_pi_package(root):
    """The oh-my-pi (omp) discovery manifest. Its own packaging layer beside
    the Claude plugin manifest (ADR-0027): omp finds the skills through a
    `package.json` `pi.skills` entry. Guarded like check_manifest so the
    dual-target packaging can't silently drift."""
    data, problem = read_file(root / "package.json", "package.json", dict)
    if problem:
        return [problem]
    if data is None:
        return ["missing package.json"]
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


def names_slug(text, slug):
    """True when TEXT names SLUG, as a whole slug and not as part of one.

    Slug characters are lowercase letters, digits and hyphens, so the
    boundary is "not one of those on either side" — `architecture-diagram`
    inside `interactive-architecture-diagram` is not a mention of the
    shorter name. Three of the registered slugs are contained in a longer
    one, and a plain `in` test reports none of them missing.
    """
    return re.search(rf"(?<![a-z0-9-]){re.escape(slug)}(?![a-z0-9-])",
                     text) is not None


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


def _states(text, phrase):
    """Does `text` state `phrase`, ignoring how it happens to be wrapped?

    Every document this module reads is hard-wrapped near 72 columns, so a
    multi-word phrase lands across a line break routinely — and a raw
    substring test then fails a correct statement, which is pinning the
    formatting and calling it the fact. Its two callers ask the same
    question of a skill and of the protocol doc, and asking it twice in
    two spellings is the drift this repo keeps writing ADRs about."""
    return phrase.lower() in " ".join(text.lower().split())


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
    to wrap. `_states` owns that comparison for both callers."""
    if _states(text, IN_FLIGHT_HEADING):
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
    — are English; check_router_conditionals pins those (issue #444).
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


# The router's two frontmatter conditionals (issue #444): the field it
# names, the file that field lives in, and the protocol.py function that
# actually reads it. A rename on either side — the prose or the code —
# must go red; deriving these from protocol.py's own source (below) means
# neither side is hand-typed against the other, without turning the
# router's prose into generated output (that fork was raised and declined
# — a five-line human-facing paragraph is not a good codegen target).
ROUTER_CONDITIONALS = (("ux", "prd.md", protocol._ux_skipped),
                      ("re-entry", "defect.md", protocol._re_entry_architect))

# "the `<field>:` field in `<file>`" — the phrase this repo's own prose
# already uses everywhere it names one of these conditionals. Requiring
# this shape, rather than "field and file both appear somewhere in the
# document", is what catches a field bound to the WRONG file (issue #444
# review round 1: swapping which file each conditional claims to live in
# passed a membership-only check clean).
CONDITIONAL_PHRASE = re.compile(
    r"`(?P<field>[a-z][a-z-]*):`\s*field\s+in\s*`(?P<file>[\w.-]+)`")


def _code_literals(func):
    """Every string-literal VALUE in FUNC's body, excluding its docstring.

    inspect.getsource returns the docstring and any comments verbatim —
    review round 1 planted a stale field name in a migration-note
    docstring while the real `.get(...)` call read the renamed key, and a
    plain substring search over that text found the decoy and stayed
    quiet. ast.walk never sees comments at all (they are not nodes), and
    dropping the leading Expr(Constant(str)) statement drops the
    docstring the same way — so what is left is only string literals the
    function actually executes, exact-matched rather than substring-
    matched (a literal equal to "ux" only, not one that merely contains
    it).
    """
    source = textwrap.dedent(inspect.getsource(func))
    body = ast.parse(source).body[0].body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    return {node.value for stmt in body for node in ast.walk(stmt)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)}


def check_router_conditionals(root):
    """check_router pins the hand-off list; this pins the sentence beside
    it (step 3) that names the router's three conditionals — the `ux:`
    field, the `re-entry:` field, and the Implement checkbox rule. Those
    are English, restating protocol._stage_complete /
    _maintenance_stage_complete, and nothing checked that the restatement
    still says what the code does.

    Cross-checked against the field name each function's own body ACTUALLY
    reads (`_code_literals`, an ast-derived exact-match set — see its
    docstring for why not a raw text search), not a second hand-typed copy
    of "ux" and "re-entry" — so a field rename in protocol.py, with the
    router prose left alone, is caught here rather than only showing up as
    a run silently routing wrong.

    Deliberately NOT covered: docs/pipeline-protocol.md's "Complete when"
    column carries the same restatement and is equally unpinned
    (check_protocol_tables's docstring says so) — a sibling gap, not
    fixed here; issue #444 scoped this to the router.
    """
    router = protocol.skill_path(root, "next")
    if not router.is_file():
        return []  # absence already reported by check_skills
    text = router.read_text(encoding="utf-8")
    named = {m["field"]: m["file"] for m in
            (m.groupdict() for m in CONDITIONAL_PHRASE.finditer(text))}
    problems = []
    for field, filename, func in ROUTER_CONDITIONALS:
        if field not in named:
            problems.append(f"router names no {field!r} conditional"
                            f" (`{field}:` field in `<file>`)")
        elif named[field] != filename:
            problems.append(f"router's {field!r} conditional names"
                            f" {named[field]!r}; protocol.{func.__name__}"
                            f" reads it from {filename!r}")
        literals = _code_literals(func)
        if field not in literals:
            problems.append(f"protocol.{func.__name__} no longer reads"
                            f" {field!r} — the router prose is stale")
        if filename not in literals:
            problems.append(f"protocol.{func.__name__} no longer reads"
                            f" {filename} — the router prose is stale")
    if "Implement checkbox" not in text:
        problems.append("router names no Implement checkbox rule")
    return problems


def check_readme_skills(root):
    """Every skill in the taxonomy is named in README.md. The README is
    where a reader learns what the plugin ships, and it is prose — so a
    skill can be added, registered, tested, and released without the
    README ever hearing about it. That is not hypothetical: it is how
    interactive-architecture-diagram shipped undocumented.

    Same bar as check_ledger, different shape, because the two files are
    different shapes: the ledger is a table with a row per skill and this
    is prose, so naming the skill anywhere is the whole requirement. What
    both share is that the name has to be the whole slug — see
    names_slug."""
    path = root / "README.md"
    if not path.is_file():
        return ["missing README.md"]
    text = path.read_text(encoding="utf-8")
    return [f"README.md never names skill {slug!r}"
            for slug in ALL_SKILLS + extra_skills(root)
            if not names_slug(text, slug)]


# The README's `## Stages` heading through the next `## ` heading (or end
# of file): the table of stage skills, plus the prose immediately below it
# that introduces each utility skill one by one, by slug (ADR-0023 —
# utility skills have no table row of their own, so that paragraph is
# their only mention). Together they are the one part of README.md whose
# entire job is enumerating what the plugin currently ships — the same
# role LEDGER.md's table plays for check_ledger_no_orphans, just split
# across a table and the paragraph the same lead-in sentence introduces.
STAGES_HEADING = "## Stages"
STAGES_SECTION = re.compile(
    rf"^{re.escape(STAGES_HEADING)}\n(.*?)(?=^## |\Z)", re.M | re.S)

# The README's first figure — the other README structural fact lint owns
# (docs/features/readme-skill-map/architecture.md): a committed SVG whose
# visible text is a hand-placed copy of the roster, so check_readme_figure
# holds it to the same taxonomy check_readme_skills holds the prose to.
README_FIGURE = "docs/assets/skill-map.svg"

# A slug-shaped backtick token — same character class names_slug and
# extra_skills use. A filename (`idea.md`) or a doc path
# (`docs/pipeline-protocol.md`) has a dot or a slash in it and never
# matches, so those are filtered out for free.
SLUG_TOKEN = re.compile(r"`([a-z0-9][a-z0-9-]*)`")


def readme_stage_mentions(text):
    """Every slug-shaped backtick token inside README.md's `## Stages`
    section, or None when that section can't be found.

    Scoped on purpose, not a whole-document scan: elsewhere in the same
    README, `` `claude` `` names the CLI tool under the on-demand-commands
    section, not a skill — a slug-shaped backtick token is not reliably a
    skill claim anywhere in the document (confirmed against the current,
    correct file; see
    docs/fixes/nothing-notices-a-dropped-readme-mention/defect.md).
    Inside the Stages section there is no such exception today: the
    table's first cell is always a skill slug, and the paragraph right
    below it exists to introduce utility skills one by one, by slug,
    because they have no row of their own — every token found there is a
    skill mention by that section's own, single purpose.
    """
    match = STAGES_SECTION.search(text)
    if not match:
        return None
    return set(SLUG_TOKEN.findall(match.group(1)))


def check_readme_no_orphans(root):
    """The reverse of check_readme_skills (issue #502 — the README half
    of #455 that check_ledger_no_orphans left open): a skill named in
    README.md's `## Stages` section that the current taxonomy no longer
    registers.

    check_ledger_no_orphans reverses check_ledger by reading the exact
    same structural element both ways (a table row). check_readme_skills
    has no equivalent to reverse: its forward direction accepts a mention
    anywhere in the whole document, prose included, and there is no "set
    of things README.md claims are skills" to read back out of free text
    in general — only within `## Stages` does every slug-shaped backtick
    token happen to be one, because naming the plugin's skills is that
    section's entire job (see readme_stage_mentions).

    Only that section is scanned. A skill named elsewhere in the document
    is not this checker's concern, the same way check_ledger_no_orphans
    does not scan LEDGER.md's reading notes below its table: that prose
    can discuss a retired skill historically without a live claim being
    made about it. Unlike check_ledger_no_orphans, which never leaves its
    row boundary, this checker does read prose — a known, bounded cost: a
    future edit that adds an unrelated slug-shaped backtick term inside
    `## Stages` (one that does not name a skill) would read as a false
    orphan here. That risk is accepted in exchange for catching a retired
    *utility* skill's stale prose mention, which is the case issue #502
    was actually raised about and a table-only reading would silently
    miss — utility skills have no table row to lose.

    A missing or renamed `## Stages` heading is its own problem, not a
    silent []: check_readme_skills's forward direction never depended on
    that heading, so nothing else would notice it disappearing.
    """
    path = root / "README.md"
    if not path.is_file():
        return []  # absence already reported by check_readme_skills
    mentions = readme_stage_mentions(path.read_text(encoding="utf-8"))
    if mentions is None:
        return [f"README.md has no {STAGES_HEADING!r} section — it is "
                "where check_readme_no_orphans reads which skills are "
                "currently claimed"]
    known = set(ALL_SKILLS) | set(extra_skills(root))
    return [f"README.md's {STAGES_HEADING!r} section names {slug!r}, "
            "which the taxonomy no longer registers"
            for slug in sorted(mentions - known)]


def check_readme_figure(root):
    """Every skill in the taxonomy is named in README.md's first figure,
    and README.md still embeds that figure. The figure is a committed
    SVG (README_FIGURE) hand-placed by a person, so it is a second copy
    of the roster that nothing else would notice drifting — the way
    plugin.json's utility list once did (check_plugin_skills). Same
    roster as check_readme_skills, same two functions: ALL_SKILLS plus
    extra_skills, whole slugs through names_slug, no list of its own.

    Read off the figure's visible text, never its raw bytes: the joined
    content of every `<text>` element (tspans included — a label that
    wraps is still one label), elements separated so no two fuse into a
    token. An `id` attribute, a comment or a `<style>` rule that carries
    a slug is not a name a reader can see, and a box whose label says
    "Ship" while its id says `ship` is exactly the rotted figure this
    exists to catch.

    One string and an early return for a figure that is missing,
    unreadable or not well-formed XML, so a broken file never fans out
    into one line per skill. A missing or unreadable README.md is left
    to check_readme_skills, as check_readme_no_orphans leaves it; the
    embed line can only be judged on a README that reads.
    """
    text, problem = read_file(root / README_FIGURE, README_FIGURE, str)
    if problem:
        return [problem]
    if text is None:
        return [f"missing {README_FIGURE}"]
    try:
        tree = ET.fromstring(text)
    except ET.ParseError as err:
        return [f"{README_FIGURE} is not valid SVG: {err}"]
    visible = " ".join("".join(element.itertext())
                       for element in tree.iter()
                       if element.tag.rpartition("}")[2] == "text")
    problems = [f"{README_FIGURE} never names skill {slug!r}"
                for slug in ALL_SKILLS + extra_skills(root)
                if not names_slug(visible, slug)]
    readme, _ = read_file(root / "README.md", "README.md", str)
    if readme is not None and README_FIGURE not in readme:
        problems.append(f"README.md never embeds {README_FIGURE!r}")
    return problems


def check_protocol(root):
    """The doc exists, and still says the thing two skills send readers to.

    The second half closes a loop the recital pin leaves open: that pin
    holds `capture` and `idea` to IN_FLIGHT_HEADING, and IN_FLIGHT_HEADING
    to nothing. Delete the section and all three still agree — with both
    skills pointing at a heading that is gone. Checked here rather than in
    the recital pin because it is a fact about the doc, and the doc's
    checker is this one."""
    path = root / "docs" / "pipeline-protocol.md"
    if not path.is_file():
        return ["missing docs/pipeline-protocol.md"]
    if _states(path.read_text(encoding="utf-8"), IN_FLIGHT_HEADING):
        return []
    return [f"docs/pipeline-protocol.md no longer states "
            f"{IN_FLIGHT_HEADING!r}, which capture and idea both recite"]


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
        # Hand-written rather than cli.read_file (ADR-0075): the shape
        # check is validate_output's, reported beside the stem line, and
        # a directory the glob matched is "cannot read", not absent.
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except OSError as err:
            return [f"cannot read {label}: {err}"]
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
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


# The first cell of a LEDGER.md table row, which is the skill slug. The
# header (`| Skill |`) and the separator (`|---|`) are not rows: a slug is
# lowercase and a row's first cell holds nothing else. The leading
# character class matches names_slug's — extra_skills accepts any
# directory name, so a slug that opens with a digit has to read as a row
# here exactly as it reads as a mention there.
LEDGER_ROW = re.compile(r"^\|\s*([a-z0-9][a-z0-9-]*)\s*\|", re.M)


def ledger_rows(text):
    """Every skill slug LEDGER.md has a table row for.

    A set of exact slugs, not a search over the file. Both halves of that
    matter, and each closes a way the old `slug not in text` was blind.

    Exact, because three of the registered slugs are contained in a longer
    one — `architect` in `architecture-diagram` and in
    `interactive-architecture-diagram`, `review` in `address-pr-review`,
    `architecture-diagram` in the interactive form. A substring test can
    never find their rows missing, and one of those is the shorter sibling
    of the very skill whose undocumented release is why the README's
    checker exists.

    Rows, because the problem string says row and the file is a table
    followed by paragraphs of reading notes that name skills by slug. A
    row deleted while the reading still mentions the skill passed the
    check that claimed to look for the row.
    """
    return set(LEDGER_ROW.findall(text))


def check_ledger(root):
    """Every skill in the taxonomy has a maturity row in LEDGER.md.

    ledger_rows owns what counts as a row; this checker owns which slugs
    must have one. check_ledger_links reads the same file for a different
    fact (the eval-evidence links) and keeps reading the whole text —
    those links live in the row cells and in the reading below alike.
    """
    path = root / "LEDGER.md"
    if not path.is_file():
        return ["missing LEDGER.md"]
    rows = ledger_rows(path.read_text(encoding="utf-8"))
    return [f"LEDGER.md has no row for skill {slug!r}"
            for slug in ALL_SKILLS + extra_skills(root) if slug not in rows]


def check_ledger_no_orphans(root):
    """The reverse of check_ledger (issue #455): a row naming a skill the
    taxonomy no longer registers.

    Issue #455 framed the reverse direction as needing a source of truth
    for "was a skill" — a historical registry the taxonomy does not keep.
    It does not: `ALL_SKILLS + extra_skills(root)` is already the trusted
    "is a skill, right now" set check_ledger holds LEDGER.md to in the
    forward direction, and a row naming something outside it is exactly as
    wrong whether that name was renamed, dropped, or never a skill at all
    — the checker does not need to know which. Same set, same row
    extraction (ledger_rows), read the other way.

    Row-scoped like check_ledger, for the same reason: the reading notes
    below the table name skills by slug too, and a retired skill can stay
    in that prose (an explicit "dropped" note, say) without a live row
    claiming a maturity that no longer exists.
    """
    path = root / "LEDGER.md"
    if not path.is_file():
        return []  # absence already reported by check_ledger
    known = set(ALL_SKILLS) | set(extra_skills(root))
    rows = ledger_rows(path.read_text(encoding="utf-8"))
    return [f"LEDGER.md has a row for skill {slug!r}, which the taxonomy "
            "no longer registers" for slug in sorted(rows - known)]


def check_backlog(root):
    """The seed backlog is strictly opt-in (ADR-0029): an absent
    docs/backlog.md is no problem. protocol.check_backlog owns the entry
    grammar; this checker keeps the filesystem half — existence and
    readability."""
    path = root / "docs" / "backlog.md"
    if not path.is_file():
        return []
    # Hand-written rather than cli.read_file (ADR-0075): this checker's
    # phrase is "is unreadable", where read_file says "cannot read".
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
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


CHECKERS = (check_manifest, check_plugin_skills,
            check_pi_package, check_skills,
            check_skill_recitals, check_skill_assets, check_templates,
            check_router, check_router_conditionals,
            check_readme_skills, check_readme_no_orphans,
            check_readme_figure, check_protocol,
            check_protocol_tables, check_backlog, check_evals,
            check_output_evals, check_ledger, check_ledger_no_orphans,
            check_ledger_links)


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
