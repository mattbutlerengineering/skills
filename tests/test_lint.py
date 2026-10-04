"""Lint-checker seam: every checker takes the repo root as a parameter,
so seeded temp trees are a second adapter beside the real repo.

Trees are built programmatically (not committed like the orientation
fixtures) because the clean tree must track protocol.py's taxonomy —
committed copies would duplicate those constants and rot. Each defect
test seeds the clean tree, breaks one aspect, and asserts the checker's
exact problem strings through its public interface.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import lint  # noqa: E402
import protocol  # noqa: E402
from protocol import (ALL_SKILLS, MAINTENANCE_STAGES,  # noqa: E402
                      STAGE_ARTIFACTS, STAGES, TEMPLATED_STAGES)

SPINE = [stage for stage, _ in STAGE_ARTIFACTS]
SPINE_ARTIFACT = dict(STAGE_ARTIFACTS)


def _in_flight_line():
    """The recital a run-starting skill owes the protocol's in-flight
    guard. Taken from lint's own constant so the clean tree tracks a
    reworded heading instead of pinning a stale copy of it."""
    return (f"Before claiming a seed, run the protocol's "
            f"{lint.IN_FLIGHT_HEADING!r} check.")


def recital_body(slug):
    """The smallest body whose recitals state the protocol facts
    check_skill_recitals pins — one canonical phrasing per convention,
    derived from the protocol tables so the clean tree tracks them."""
    if slug == "capture":
        return ("## Process\n\n"
                f"1. {_in_flight_line()}\n"
                "2. Record `re-entry: implement` or `re-entry: architect`.\n"
                "3. Write the artifact as `defect.md`.\n"
                "4. Hand off per the recorded re-entry.\n")
    if slug not in SPINE:
        return "body\n"
    i = SPINE.index(slug)
    lines = []
    if i > 0:
        gate = f"Predecessor artifact: `{SPINE_ARTIFACT[SPINE[i - 1]]}`."
        if SPINE[i - 1] == "ux-design":
            gate = (f"Predecessor artifacts: `{SPINE_ARTIFACT[SPINE[i - 2]]}`,"
                    f" plus `{SPINE_ARTIFACT[SPINE[i - 1]]}`.")
        lines.append(f"1. **Soft gate.** {gate}")
    lines.append(f"2. Write the artifact as `{SPINE_ARTIFACT[slug]}`.")
    if i + 1 < len(SPINE):
        hand = f"Next stage is {SPINE[i + 1].replace('-', ' ')}."
        if SPINE[i + 1] == "ux-design":
            hand += f" When skipped, next is {SPINE[i + 2]}."
        lines.append(f"3. **Hand off.** {hand}")
    if slug in lint.RUN_STARTING:
        lines.append(f"4. {_in_flight_line()}")
    return "## Process\n\n" + "\n".join(lines) + "\n"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402


def protocol_table(rows):
    """The protocol doc's orientation table for a walk table — the shape
    check_protocol_tables parses back out."""
    return ("| Stage | Artifact | Complete when |\n"
            "|-------|----------|---------------|\n"
            + "".join(f"| {stage} | `{artifact}` | file exists |\n"
                      for stage, artifact in rows))


def make_clean_tree(root):
    """Seed the smallest tree on which every checker reports zero problems."""
    plugin_dir = root / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    # check_plugin_skills holds the description to naming every utility
    # skill, so the smallest clean tree carries them all.
    (plugin_dir / "plugin.json").write_text(json.dumps(
        {"name": "t", "version": "0",
         "description": "t — utility skills ("
                        + ", ".join(protocol.UTILITY_SKILLS) + ")"}),
        encoding="utf-8")

    (root / "package.json").write_text(json.dumps(
        {"name": "t", "version": "0", "private": True,
         "keywords": ["pi-package"], "pi": {"skills": ["./skills"]}}),
        encoding="utf-8")

    for slug in ALL_SKILLS:
        skill_dir = root / "skills" / slug
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {slug}\ndescription: d\n---\n\n{recital_body(slug)}",
            encoding="utf-8")
    for slug in TEMPLATED_STAGES:
        (root / "skills" / slug / "TEMPLATE.md").write_text(
            "t\n", encoding="utf-8")
    # The router needs its hand-off list, not just the slugs: check_router
    # pins that list's membership and pipeline order, so a bare mention
    # dump is no longer a clean router.
    # check_router_conditionals holds the same file to naming its two
    # frontmatter conditionals and the Implement checkbox rule.
    (root / "skills" / "next" / "SKILL.md").write_text(
        "---\nname: next\ndescription: d\n---\n\n"
        "Honor the `ux:` field in `prd.md` frontmatter, the `re-entry:`"
        " field in `defect.md` frontmatter, and the Implement checkbox"
        " rule.\n\n"
        + "\n".join(f"   - {stage} → the `{stage}` skill"
                    for stage in lint.routed_order()) + "\n",
        encoding="utf-8")

    # check_readme_skills holds the README to naming every skill, so the
    # smallest clean tree carries one. The `## Stages` heading is there for
    # check_readme_no_orphans, which reads only that section (see
    # lint.readme_stage_mentions) — without it, the smallest tree would
    # fail the one checker whose whole job is reading that heading.
    (root / "README.md").write_text(
        "# t\n\n## Stages\n\n"
        + "".join(f"- `{slug}`\n" for slug in ALL_SKILLS),
        encoding="utf-8")

    (root / "docs").mkdir()
    # Both orientation tables, not a stub: check_protocol_tables pins the
    # doc's stage order and artifacts to protocol.py's walk tables, so the
    # smallest tree every checker passes on genuinely has to carry them.
    (root / "docs" / "pipeline-protocol.md").write_text(
        f"spec\n\n### {lint.IN_FLIGHT_HEADING}\n\n"
        "## Artifacts are the state\n\n"
        + protocol_table(protocol.STAGE_ARTIFACTS)
        + "\n### Maintenance-run orientation\n\n"
        + protocol_table(protocol.MAINTENANCE_STAGE_ARTIFACTS),
        encoding="utf-8")

    cases = [{"id": f"{slug}-{n}", "kind": "direct",
              "expected": slug, "query": "q"}
             for slug in ALL_SKILLS for n in range(3)]
    cases += [{"id": f"none-{n}", "kind": "distractor",
               "expected": None, "query": "q"} for n in range(3)]
    (root / "evals").mkdir()
    (root / "evals" / "routing.json").write_text(
        json.dumps({"version": 1, "cases": cases}), encoding="utf-8")

    fixture = root / "evals" / "fixtures" / "seeded-run"
    fixture.mkdir(parents=True)
    (root / "evals" / "output").mkdir()
    (root / "evals" / "output" / "idea.json").write_text(json.dumps({
        "skill_name": "idea",
        "evals": [{"id": 1, "prompt": "p", "run_scale": "feature:x",
                   "expected_output": "o", "expectations": ["x"],
                   "run_fixture": "evals/fixtures/seeded-run"}],
    }), encoding="utf-8")

    results = root / "evals" / "results"
    results.mkdir()
    (results / "trigger-2026-01-01.json").write_text("{}", encoding="utf-8")
    rows = [f"| {slug} | "
            "[2026-01-01](evals/results/trigger-2026-01-01.json) |\n"
            for slug in ALL_SKILLS]
    (root / "LEDGER.md").write_text("".join(rows), encoding="utf-8")


class CheckerTreeTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="lint-tree-"))
        self.addCleanup(shutil.rmtree, self.root)
        make_clean_tree(self.root)

    def test_bytes_that_are_not_utf8_are_a_problem_not_a_crash(self):
        """RFC 8259 §8.1 makes JSON a UTF-8 interchange format, so bytes
        that will not decode are not valid JSON — the existing message is
        right, only the guard was too narrow. UnicodeDecodeError subclasses
        ValueError, not JSONDecodeError, so it escaped as a traceback and
        CI reported a crash instead of `lint: N problem(s)`."""
        path = self.root / ".claude-plugin" / "plugin.json"
        path.write_bytes('{"name": "caf\u00e9"}'.encode("latin-1"))
        problems = lint.check_manifest(self.root)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            "plugin.json is not valid JSON:"), problems)


class TestCleanTree(CheckerTreeTest):
    def test_every_checker_reports_zero_problems(self):
        for checker in lint.CHECKERS:
            with self.subTest(checker=checker.__name__):
                self.assertEqual(checker(self.root), [])


class TestManifest(CheckerTreeTest):
    def test_missing_field(self):
        path = self.root / ".claude-plugin" / "plugin.json"
        path.write_text(json.dumps({"name": "t", "version": "0"}),
                        encoding="utf-8")
        self.assertEqual(lint.check_manifest(self.root),
                         ["plugin.json missing field: description"])


    def test_a_manifest_that_is_not_an_object_names_its_shape(self):
        # A JSON top level is legally any of these; none of them has .get
        path = self.root / ".claude-plugin" / "plugin.json"
        for shape in ("null", "42", '"text"', '["a"]', "true"):
            with self.subTest(shape=shape):
                path.write_text(shape, encoding="utf-8")
                self.assertEqual(lint.check_manifest(self.root),
                                 ["plugin.json is not a JSON object"])

    def test_a_non_object_manifest_does_not_stop_the_gate(self):
        # check_manifest is CHECKERS[0]: a raise here hides every other
        # finding in the repo behind a traceback
        (self.root / ".claude-plugin" / "plugin.json").write_text(
            "null", encoding="utf-8")
        problems = []
        for checker in lint.CHECKERS:
            with self.subTest(checker=checker.__name__):
                problems += checker(self.root)
        self.assertEqual(problems, ["plugin.json is not a JSON object"])

    def test_a_manifest_that_is_not_json_is_one_exact_problem(self):
        (self.root / ".claude-plugin" / "plugin.json").write_text(
            "{not json", encoding="utf-8")
        self.assertEqual(lint.check_manifest(self.root), [
            "plugin.json is not valid JSON: Expecting property name"
            " enclosed in double quotes: line 1 column 2 (char 1)"])

    def test_an_empty_manifest_is_one_exact_problem(self):
        (self.root / ".claude-plugin" / "plugin.json").write_text(
            "", encoding="utf-8")
        self.assertEqual(lint.check_manifest(self.root), [
            "plugin.json is not valid JSON: Expecting value: line 1 column 1"
            " (char 0)"])

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-000 file")
    def test_a_manifest_the_process_may_not_read_is_a_problem(self):
        # check_manifest is CHECKERS[0]: a PermissionError here hid every
        # other finding in the repo behind a traceback
        path = self.root / ".claude-plugin" / "plugin.json"
        path.chmod(0)
        try:
            self.assertEqual(lint.check_manifest(self.root), [
                "cannot read plugin.json: [Errno 13] Permission denied:"
                f" '{path}'"])
        finally:
            path.chmod(0o644)


class TestPiPackage(CheckerTreeTest):
    """The Pi (oh-my-pi) discovery manifest, guarded like the Claude one so
    the dual-target packaging can't silently drift (ADR-0027)."""

    def test_missing_package_json(self):
        (self.root / "package.json").unlink()
        self.assertEqual(lint.check_pi_package(self.root),
                         ["missing package.json"])

    def test_invalid_json(self):
        (self.root / "package.json").write_text("{not json", encoding="utf-8")
        problems = lint.check_pi_package(self.root)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            "package.json is not valid JSON:"))

    def test_an_empty_package_json_is_one_exact_problem(self):
        (self.root / "package.json").write_text("", encoding="utf-8")
        self.assertEqual(lint.check_pi_package(self.root), [
            "package.json is not valid JSON: Expecting value: line 1 column 1"
            " (char 0)"])


    def test_a_package_that_is_not_an_object_names_its_shape(self):
        path = self.root / "package.json"
        for shape in ("null", "42", '"text"', '["a"]', "true"):
            with self.subTest(shape=shape):
                path.write_text(shape, encoding="utf-8")
                self.assertEqual(lint.check_pi_package(self.root),
                                 ["package.json is not a JSON object"])

    def test_bytes_that_are_not_utf8_are_a_problem_not_a_crash(self):
        """Guarded like check_manifest — ADR-0027 keeps the two packaging
        manifests in step, and that has to include how they fail."""
        (self.root / "package.json").write_bytes(
            '{"private": true, "name": "caf\u00e9"}'.encode("latin-1"))
        problems = lint.check_pi_package(self.root)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            "package.json is not valid JSON:"), problems)

    def test_not_private(self):
        (self.root / "package.json").write_text(json.dumps(
            {"keywords": ["pi-package"], "pi": {"skills": ["./skills"]}}),
            encoding="utf-8")
        self.assertEqual(lint.check_pi_package(self.root),
                         ["package.json must set private: true"])

    def test_missing_pi_package_keyword(self):
        (self.root / "package.json").write_text(json.dumps(
            {"private": True, "pi": {"skills": ["./skills"]}}),
            encoding="utf-8")
        self.assertEqual(lint.check_pi_package(self.root),
                         ["package.json keywords must include 'pi-package'"])

    def test_pi_skills_does_not_point_at_skills_dir(self):
        (self.root / "package.json").write_text(json.dumps(
            {"private": True, "keywords": ["pi-package"], "pi": {}}),
            encoding="utf-8")
        self.assertEqual(lint.check_pi_package(self.root),
                         ["package.json pi.skills must include './skills'"])


class TestSkills(CheckerTreeTest):
    def test_name_mismatch(self):
        (self.root / "skills" / "idea" / "SKILL.md").write_text(
            "---\nname: notidea\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_skills(self.root),
            ["skills/idea/SKILL.md frontmatter name is 'notidea', "
             "expected 'idea'"])

    def test_no_frontmatter_and_no_description_are_distinct(self):
        (self.root / "skills" / "idea" / "SKILL.md").write_text(
            "body only\n", encoding="utf-8")
        (self.root / "skills" / "prd" / "SKILL.md").write_text(
            "---\nname: prd\n---\n\nbody\n", encoding="utf-8")
        self.assertEqual(
            lint.check_skills(self.root),
            ["skills/idea/SKILL.md has no frontmatter block",
             "skills/prd/SKILL.md frontmatter has no description"])

    def test_discovered_dir_outside_taxonomy_gets_both_signals(self):
        rogue = self.root / "skills" / "rogue"
        rogue.mkdir()
        (rogue / "SKILL.md").write_text(
            "---\nname: notrogue\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_skills(self.root),
            ["skills/rogue is not in the skill taxonomy "
             "(protocol.py ALL_SKILLS)",
             "skills/rogue/SKILL.md frontmatter name is 'notrogue', "
             "expected 'rogue'"])

    def test_discovered_dir_without_skill_md_is_reported(self):
        (self.root / "skills" / "empty-dir").mkdir()
        self.assertEqual(
            lint.check_skills(self.root),
            ["skills/empty-dir is not in the skill taxonomy "
             "(protocol.py ALL_SKILLS)",
             "missing skills/empty-dir/SKILL.md"])

    def test_valid_discovered_dir_still_flags_missing_registration(self):
        extra = self.root / "skills" / "extra"
        extra.mkdir()
        (extra / "SKILL.md").write_text(
            "---\nname: extra\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_skills(self.root),
            ["skills/extra is not in the skill taxonomy "
             "(protocol.py ALL_SKILLS)"])

    def test_dotdirs_under_skills_are_ignored(self):
        (self.root / "skills" / ".cache").mkdir()
        self.assertEqual(lint.check_skills(self.root), [])
        self.assertEqual(lint.check_ledger(self.root), [])

    def test_description_over_pi_limit_is_flagged(self):
        # Pi (oh-my-pi) caps a skill description at 1024 chars; a longer one
        # loads on Claude but silently drops the skill on omp (ADR-0027).
        (self.root / "skills" / "idea" / "SKILL.md").write_text(
            f"---\nname: idea\ndescription: {'x' * 1025}\n---\n\nbody\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_skills(self.root),
            ["skills/idea/SKILL.md description exceeds Pi's 1024-char limit"])


class TestSkillRecitals(CheckerTreeTest):
    """Stage-skill prose recites the protocol (soft-gate predecessor,
    own artifact, hand-off successor). Vended skills can't import
    protocol.py, so the copies are forced — check_skill_recitals pins
    them to the protocol tables instead (ADR-0052)."""

    def seed(self, slug, body):
        (self.root / "skills" / slug / "SKILL.md").write_text(
            f"---\nname: {slug}\ndescription: d\n---\n\n{body}",
            encoding="utf-8")

    def test_wrong_gate_artifact_is_flagged_both_ways(self):
        self.seed("prd",
                  "1. **Soft gate.** Predecessor artifact: `ux.md`.\n"
                  "2. Write the artifact as `prd.md`.\n"
                  "3. **Hand off.** Next stage is ux design. When skipped, "
                  "next is architect.\n")
        self.assertEqual(
            lint.check_skill_recitals(self.root),
            ["skills/prd/SKILL.md soft gate never names predecessor "
             "artifact 'idea.md'",
             "skills/prd/SKILL.md soft gate names downstream artifact "
             "'ux.md'"])

    def test_missing_soft_gate_step(self):
        self.seed("review",
                  "1. Write the artifact as `review.md`.\n"
                  "2. **Hand off.** Next stage is ship.\n")
        self.assertEqual(
            lint.check_skill_recitals(self.root),
            ["skills/review/SKILL.md has no soft-gate step"])

    def test_wrong_successor_is_flagged_both_ways(self):
        self.seed("decompose",
                  "1. **Soft gate.** Predecessor artifact: "
                  "`architecture.md`.\n"
                  "2. Write the artifact as `breakdown.md`.\n"
                  "3. **Hand off.** Next stage is verify.\n")
        self.assertEqual(
            lint.check_skill_recitals(self.root),
            ["skills/decompose/SKILL.md never states next stage "
             "'implement'",
             "skills/decompose/SKILL.md states next stage 'verify', "
             "expected 'implement'"])

    def test_terminal_stage_claims_no_next_stage(self):
        self.seed("operate",
                  "1. **Soft gate.** Predecessor artifact: `release.md`.\n"
                  "2. Write the artifact as `retro.md`.\n"
                  "3. **Hand off.** Next stage is idea.\n")
        self.assertEqual(
            lint.check_skill_recitals(self.root),
            ["skills/operate/SKILL.md states next stage 'idea', "
             "but 'operate' completes the run"])

    def test_missing_own_artifact(self):
        self.seed("verify",
                  "1. **Soft gate.** Predecessor artifact: `breakdown.md`.\n"
                  "2. **Hand off.** Next stage is review.\n")
        self.assertEqual(
            lint.check_skill_recitals(self.root),
            ["skills/verify/SKILL.md never names its artifact "
             "'verification.md'"])

    def test_capture_must_record_both_re_entry_options(self):
        self.seed("capture",
                  f"1. {_in_flight_line()}\n"
                  "2. Record `re-entry: implement`.\n"
                  "3. Write the artifact as `defect.md`.\n")
        self.assertEqual(
            lint.check_skill_recitals(self.root),
            ["skills/capture/SKILL.md never records re-entry option "
             "'re-entry: architect'"])

    def test_a_run_starting_skill_must_name_the_in_flight_check(self):
        """The moment a run starts is the only moment this rule can be
        honoured, so the two skills that start one owe it a recital. The
        pin proves the words are present and nothing more — whether the
        agent looked is not knowable here, and a checker that implied
        otherwise would manufacture the false clean result the protocol
        section exists to forbid."""
        self.seed("capture",
                  "1. Record `re-entry: implement` or `re-entry: "
                  "architect`.\n"
                  "2. Write the artifact as `defect.md`.\n"
                  "3. Hand off per the recorded re-entry.\n")
        self.assertEqual(
            lint.check_skill_recitals(self.root),
            [f"skills/capture/SKILL.md never names the protocol's "
             f"{lint.IN_FLIGHT_HEADING!r} check, which is where a run "
             "that is already open in review gets caught"])

    def test_the_spine_entry_carries_the_same_obligation(self):
        """`idea` claims backlog seeds too, and it is a spine stage rather
        than the maintenance entry — two different loops in the checker.
        Asserted separately because one loop passing says nothing about
        the other."""
        self.seed("idea",
                  "1. Write the artifact as `idea.md`.\n"
                  "2. **Hand off.** Next stage is prd.\n")
        self.assertEqual(
            lint.check_skill_recitals(self.root),
            [f"skills/idea/SKILL.md never names the protocol's "
             f"{lint.IN_FLIGHT_HEADING!r} check, which is where a run "
             "that is already open in review gets caught"])

    def test_a_recital_that_wraps_still_counts(self):
        """Found by the pin failing on a correct recital. These documents
        are hard-wrapped near 72 columns, so a four-word phrase lands
        across a line break often — and a raw substring test would call
        that a missing rule, which is pinning the formatting and calling
        it the fact. The wrap here is the real one from capture."""
        self.seed("capture",
                  "1. Look over the work awaiting review — the protocol's"
                  " *Work\n   already in flight* section.\n"
                  "2. Record `re-entry: implement` or `re-entry: "
                  "architect`.\n"
                  "3. Write the artifact as `defect.md`.\n"
                  "4. Hand off per the recorded re-entry.\n")
        self.assertEqual(lint.check_skill_recitals(self.root), [])

    def test_a_mid_spine_stage_owes_no_recital(self):
        """The discriminating half. A stage that cannot start a run has
        nothing to check — it already has artifacts to orient from — so a
        pin that fired on every skill would be pinning the wrong fact and
        would pass this suite just as happily."""
        self.seed("prd",
                  "1. **Soft gate.** Predecessor artifact: `idea.md`.\n"
                  "2. Write the artifact as `prd.md`.\n"
                  "3. **Hand off.** Next stage is ux design. When skipped, "
                  "next is architect.\n")
        self.assertEqual(lint.check_skill_recitals(self.root), [])

    def test_ux_skip_target_must_be_named(self):
        self.seed("prd",
                  "1. **Soft gate.** Predecessor artifact: `idea.md`.\n"
                  "2. Write the artifact as `prd.md`.\n"
                  "3. **Hand off.** Next stage is ux design.\n")
        self.assertEqual(
            lint.check_skill_recitals(self.root),
            ["skills/prd/SKILL.md never names the ux-skip target "
             "'architect'"])

    def test_line_wrapped_hand_off_phrase_still_counts(self):
        # the real implement skill wraps "next\n   stage is Verify"
        self.seed("implement",
                  "1. **Soft gate.** Predecessor artifact: `breakdown.md`.\n"
                  "2. Check items off in `breakdown.md`.\n"
                  "3. **Hand off.** The stage is complete; next\n"
                  "   stage is verify.\n")
        self.assertEqual(lint.check_skill_recitals(self.root), [])

    def test_missing_skill_md_reports_nothing(self):
        # absence is check_skills' finding, not a recital problem
        (self.root / "skills" / "idea" / "SKILL.md").unlink()
        self.assertEqual(lint.check_skill_recitals(self.root), [])


class TestSkillAssets(CheckerTreeTest):
    """A skill's own markdown is read by an agent at runtime, so a rename
    or a never-committed file fails in the agent's hands and no other gate
    sees it. Every .md in the skill is walked, not just SKILL.md, because
    reference files link to each other (ADR-0008 self-containment)."""

    def write_skill(self, slug, body):
        skill = self.root / "skills" / slug / "SKILL.md"
        skill.write_text(f"---\nname: {slug}\ndescription: d\n---\n\n{body}",
                         encoding="utf-8")
        return skill.parent

    def write_ref(self, skill_dir, name, body):
        (skill_dir / "references").mkdir(exist_ok=True)
        (skill_dir / "references" / name).write_text(body, encoding="utf-8")

    def test_named_asset_that_does_not_exist(self):
        self.write_skill("idea", "Read [`references/playbook.md`]"
                                 "(references/playbook.md) first.\n")
        self.assertEqual(
            lint.check_skill_assets(self.root),
            ["skills/idea/SKILL.md names 'references/playbook.md', "
             "which does not exist"])

    def test_named_asset_that_ships_is_clean(self):
        skill_dir = self.write_skill(
            "idea", "Read `references/playbook.md` first.\n")
        self.write_ref(skill_dir, "playbook.md", "p\n")
        self.assertEqual(lint.check_skill_assets(self.root), [])

    def test_case_differing_file_does_not_satisfy_the_name(self):
        # Path.exists() folds case on macOS, so this would pass locally and
        # break on the case-sensitive filesystem the plugin installs onto.
        skill_dir = self.write_skill(
            "idea", "Read `references/playbook.md` first.\n")
        self.write_ref(skill_dir, "Playbook.md", "p\n")
        self.assertEqual(
            lint.check_skill_assets(self.root),
            ["skills/idea/SKILL.md names 'references/playbook.md', "
             "which does not exist"])

    def test_absent_directory_is_a_problem_not_a_traceback(self):
        self.write_skill("idea", "Copy `assets/boilerplate.html`.\n")
        self.assertEqual(
            lint.check_skill_assets(self.root),
            ["skills/idea/SKILL.md names 'assets/boilerplate.html', "
             "which does not exist"])

    def test_each_missing_asset_reported_once_however_often_named(self):
        self.write_skill("idea",
                         "See `references/one.md`, then `references/one.md` "
                         "again,\nand `assets/two.svg`.\n")
        self.assertEqual(
            lint.check_skill_assets(self.root),
            ["skills/idea/SKILL.md names 'assets/two.svg', "
             "which does not exist",
             "skills/idea/SKILL.md names 'references/one.md', "
             "which does not exist"])

    def test_dir_outside_the_taxonomy_is_checked_too(self):
        rogue = self.root / "skills" / "rogue"
        rogue.mkdir()
        (rogue / "SKILL.md").write_text(
            "---\nname: rogue\ndescription: d\n---\n\n"
            "Read `references/gone.md`.\n", encoding="utf-8")
        self.assertEqual(
            lint.check_skill_assets(self.root),
            ["skills/rogue/SKILL.md names 'references/gone.md', "
             "which does not exist"])

    def test_missing_skill_md_belongs_to_check_skills(self):
        (self.root / "skills" / "idea" / "SKILL.md").unlink()
        self.assertEqual(lint.check_skill_assets(self.root), [])

    def test_broken_link_between_two_reference_files(self):
        # The gap the SKILL.md-only walk missed: reference files link to
        # each other, and renaming one breaks every sibling silently.
        skill_dir = self.write_skill(
            "idea", "Read [the playbook](references/playbook.md).\n")
        self.write_ref(skill_dir, "playbook.md",
                       "Vocabulary is in [language](language.md).\n")
        self.assertEqual(
            lint.check_skill_assets(self.root),
            ["skills/idea/references/playbook.md names 'language.md', "
             "which does not exist"])

    def test_resolving_sibling_link_is_clean(self):
        skill_dir = self.write_skill(
            "idea", "Read [the playbook](references/playbook.md).\n")
        self.write_ref(skill_dir, "playbook.md",
                       "Vocabulary is in [language](language.md).\n")
        self.write_ref(skill_dir, "language.md", "terms\n")
        self.assertEqual(lint.check_skill_assets(self.root), [])

    def test_link_out_of_the_skill_directory_from_skill_md(self):
        self.write_skill("idea", "See [prd's template](../prd/TEMPLATE.md).\n")
        self.assertEqual(
            lint.check_skill_assets(self.root),
            ["skills/idea/SKILL.md names '../prd/TEMPLATE.md', which is "
             "outside the skill directory (ADR-0008: skills are "
             "self-contained)"])

    def test_link_out_of_the_skill_directory_from_a_reference_file(self):
        # One ../ from references/ lands back inside the skill; escaping
        # takes two, and the checker must count depth rather than dots.
        skill_dir = self.write_skill(
            "idea", "Read [the playbook](references/playbook.md).\n")
        self.write_ref(skill_dir, "playbook.md",
                       "See [prd](../../prd/TEMPLATE.md).\n")
        self.assertEqual(
            lint.check_skill_assets(self.root),
            ["skills/idea/references/playbook.md names '../../prd/"
             "TEMPLATE.md', which is outside the skill directory "
             "(ADR-0008: skills are self-contained)"])

    def test_anchors_and_urls_are_not_files(self):
        skill_dir = self.write_skill(
            "idea", "Read [the playbook](references/playbook.md).\n")
        self.write_ref(skill_dir, "playbook.md",
                       "Jump to [terms](#terms) or read\n"
                       "[the source](https://example.com/a.md).\n")
        self.assertEqual(lint.check_skill_assets(self.root), [])

    def test_bare_path_is_not_matched_inside_a_longer_path(self):
        # Without the lookbehind, '../prd/references/x.md' would ALSO yield
        # a bare 'references/x.md' resolved against the skill root — one
        # broken link reported as two, the second at a path nobody wrote.
        self.write_skill("idea", "See [prd](../prd/references/x.md).\n")
        self.assertEqual(
            lint.check_skill_assets(self.root),
            ["skills/idea/SKILL.md names '../prd/references/x.md', which is "
             "outside the skill directory (ADR-0008: skills are "
             "self-contained)"])


class TestReadmeSkills(CheckerTreeTest):
    """A skill can be added, registered, tested and released without the
    README hearing about it — which is how interactive-architecture-diagram
    shipped undocumented."""

    def test_unnamed_skill_is_reported(self):
        path = self.root / "README.md"
        path.write_text(path.read_text(encoding="utf-8")
                        .replace("`ship`", "`the release stage`"),
                        encoding="utf-8")
        self.assertEqual(lint.check_readme_skills(self.root),
                         ["README.md never names skill 'ship'"])

    def test_discovered_dir_outside_the_taxonomy_is_held_to_it_too(self):
        rogue = self.root / "skills" / "rogue"
        rogue.mkdir()
        (rogue / "SKILL.md").write_text(
            "---\nname: rogue\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
        self.assertEqual(lint.check_readme_skills(self.root),
                         ["README.md never names skill 'rogue'"])

    def test_a_slug_nested_in_a_longer_one_is_still_required(self):
        """`architect` sits inside `architecture-diagram` and inside
        `interactive-architecture-diagram`. A substring test calls the
        README complete once either longer name is there, so the shorter
        skill is the one the checker cannot report — and the docstring
        above records that a diagram skill shipping undocumented is
        exactly what this checker exists to stop."""
        path = self.root / "README.md"
        path.write_text(path.read_text(encoding="utf-8")
                        .replace("- `architect`\n", ""), encoding="utf-8")
        self.assertEqual(lint.check_readme_skills(self.root),
                         ["README.md never names skill 'architect'"])

    def test_every_registered_skill_can_be_reported_missing(self):
        """Closure: no slug is unreportable. One dropped name at a time,
        the whole taxonomy, so a blind spot cannot hide behind the three
        slugs the other tests happen to pick."""
        original = (self.root / "README.md").read_text(encoding="utf-8")
        path = self.root / "README.md"
        for slug in ALL_SKILLS:
            with self.subTest(slug=slug):
                path.write_text(original.replace(f"- `{slug}`\n", ""),
                                encoding="utf-8")
                self.assertEqual(lint.check_readme_skills(self.root),
                                 [f"README.md never names skill {slug!r}"])

    def test_missing_readme_is_one_problem_not_one_per_skill(self):
        (self.root / "README.md").unlink()
        self.assertEqual(lint.check_readme_skills(self.root),
                         ["missing README.md"])


class TestReadmeNoOrphans(CheckerTreeTest):
    """The reverse direction of check_readme_skills (issue #502 — the
    README half of #455 that check_ledger_no_orphans left open, see
    docs/fixes/nothing-notices-a-dropped-readme-mention/defect.md): a
    skill named in README.md's `## Stages` section that the current
    taxonomy no longer registers. Scoped to that section on purpose —
    lint.readme_stage_mentions owns why."""

    def test_every_current_mention_stays_clean(self):
        # The clean fixture's README names every registered skill and
        # nothing else. No false positives.
        self.assertEqual(lint.check_readme_no_orphans(self.root), [])

    def test_an_orphaned_table_mention_is_reported(self):
        path = self.root / "README.md"
        path.write_text(
            path.read_text(encoding="utf-8") + "- `retired-skill`\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_readme_no_orphans(self.root),
            ["README.md's '## Stages' section names 'retired-skill', "
             "which the taxonomy no longer registers"])

    def test_a_prose_only_utility_mention_is_reported(self):
        """The scenario #502 was actually raised about: a utility skill
        has no table row (ADR-0023), so its only mention is a prose
        sentence in this same section. If that sentence outlives the
        skill, this is the only checker that notices."""
        path = self.root / "README.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + "`retired-utility` used to do something useful.\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_readme_no_orphans(self.root),
            ["README.md's '## Stages' section names 'retired-utility', "
             "which the taxonomy no longer registers"])

    def test_a_mention_nested_in_a_longer_registered_slug_is_not_an_orphan(
            self):
        """`architect` is a substring of `architecture-diagram`, both
        registered. readme_stage_mentions reads exact backtick tokens
        (SLUG_TOKEN), not substrings, so neither is mistaken for an
        orphan of the other."""
        self.assertEqual(lint.check_readme_no_orphans(self.root), [])
        self.assertIn(
            "architect",
            lint.readme_stage_mentions(
                (self.root / "README.md").read_text(encoding="utf-8")))

    def test_a_backtick_token_outside_the_section_is_not_scanned(self):
        """Why this checker cannot scan the whole document: the real
        README names the `claude` CLI tool, not a skill, outside the
        Stages section — a whole-document version of this check would
        misfire on it the moment it was written (see defect.md). Mirrored
        here with a planted, out-of-section, slug-shaped, non-skill
        token."""
        path = self.root / "README.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\n## Development\n\nneeds the `claude` CLI\n",
            encoding="utf-8")
        self.assertEqual(lint.check_readme_no_orphans(self.root), [])

    def test_missing_stages_heading_is_reported(self):
        """check_readme_skills's forward direction never depended on this
        heading, so nothing else would notice it disappearing."""
        path = self.root / "README.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("## Stages\n\n", ""),
            encoding="utf-8")
        self.assertEqual(
            lint.check_readme_no_orphans(self.root),
            ["README.md has no '## Stages' section — it is where "
             "check_readme_no_orphans reads which skills are currently "
             "claimed"])

    def test_missing_readme_yields_no_problem_here(self):
        # check_readme_skills already reports "missing README.md"; a
        # second checker reporting the same absence would double it.
        (self.root / "README.md").unlink()
        self.assertEqual(lint.check_readme_no_orphans(self.root), [])


class TestPluginSkills(CheckerTreeTest):
    """The plugin description enumerates the utility skills, and it is the
    string a user reads first when deciding whether to install. Nothing
    held it to the taxonomy: check_manifest asserts only that the field is
    non-empty, so three skills went unnamed on the install surface while
    README.md and LEDGER.md were held to the full list. Same bar and same
    shape as check_readme_skills, for the same reason."""

    def rewrite_description(self, description):
        path = self.root / ".claude-plugin" / "plugin.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["description"] = description
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_unnamed_utility_skill_is_reported(self):
        named = [slug for slug in protocol.UTILITY_SKILLS if slug != "deepen"]
        self.rewrite_description("utility skills (" + ", ".join(named) + ")")
        self.assertEqual(
            lint.check_plugin_skills(self.root),
            ["plugin.json's description never names utility skill 'deepen'"])

    def test_every_missing_skill_gets_its_own_problem(self):
        self.rewrite_description("no skills here")
        self.assertEqual(
            lint.check_plugin_skills(self.root),
            [f"plugin.json's description never names utility skill {slug!r}"
             for slug in protocol.UTILITY_SKILLS])

    def test_a_complete_description_is_clean(self):
        self.assertEqual(lint.check_plugin_skills(self.root), [])

    def test_only_utility_skills_are_required(self):
        """Stage skills are named in the description as title-case prose
        ("Idea", "UX Design"), never by slug, so holding the string to the
        whole taxonomy would demand a restyling nobody asked for. The
        parenthetical list is the part that claims to be exhaustive."""
        self.rewrite_description(
            "utility skills (" + ", ".join(protocol.UTILITY_SKILLS) + ")")
        self.assertEqual(lint.check_plugin_skills(self.root), [])

    def test_a_longer_slug_does_not_satisfy_the_shorter_one(self):
        """`architecture-diagram` is a substring of
        `interactive-architecture-diagram`. A plain `in` test calls the
        list complete after the shorter name is dropped — silently
        blessing exactly the drift this checker exists to catch."""
        kept = [slug for slug in protocol.UTILITY_SKILLS
                if slug != "architecture-diagram"]
        self.rewrite_description("utility skills (" + ", ".join(kept) + ")")
        self.assertEqual(
            lint.check_plugin_skills(self.root),
            ["plugin.json's description never names utility skill"
             " 'architecture-diagram'"])

    def test_a_missing_manifest_is_left_to_check_manifest(self):
        """One broken file, one problem string. check_manifest already
        reports a missing or unparseable manifest, so reporting it here
        too would double it — and lint aggregates every checker, so the
        run still fails."""
        (self.root / ".claude-plugin" / "plugin.json").unlink()
        self.assertEqual(lint.check_plugin_skills(self.root), [])
        self.assertEqual(lint.check_manifest(self.root),
                         ["missing .claude-plugin/plugin.json"])

    def test_an_unparseable_manifest_is_left_to_check_manifest(self):
        (self.root / ".claude-plugin" / "plugin.json").write_text(
            "{not json", encoding="utf-8")
        self.assertEqual(lint.check_plugin_skills(self.root), [])
        self.assertEqual(len(lint.check_manifest(self.root)), 1)

    def test_a_non_object_manifest_is_left_to_check_manifest(self):
        path = self.root / ".claude-plugin" / "plugin.json"
        for shape in ('["a"]', '"text"'):
            with self.subTest(shape=shape):
                path.write_text(shape, encoding="utf-8")
                self.assertEqual(lint.check_plugin_skills(self.root), [])

    @unittest.skipIf(os.geteuid() == 0, "root reads a mode-000 file")
    def test_an_unreadable_manifest_is_left_to_check_manifest(self):
        path = self.root / ".claude-plugin" / "plugin.json"
        path.chmod(0)
        try:
            self.assertEqual(lint.check_plugin_skills(self.root), [])
        finally:
            path.chmod(0o644)

    def test_a_manifest_that_is_not_utf8_is_left_to_check_manifest(self):
        (self.root / ".claude-plugin" / "plugin.json").write_bytes(
            b"\xff\xfe")
        self.assertEqual(lint.check_plugin_skills(self.root), [])
        self.assertEqual(len(lint.check_manifest(self.root)), 1)


class TestProtocolTables(CheckerTreeTest):
    """The protocol doc and protocol.py are both authorities on the walk
    and neither derives from the other: offline tools read the module,
    and an agent in a consuming repo reads the doc. Drift routes two
    ways in one pipeline."""

    PRODUCT = "## Artifacts are the state"
    MAINTENANCE = "### Maintenance-run orientation"

    def doc(self):
        return self.root / "docs" / "pipeline-protocol.md"

    def rewrite(self, old, new):
        path = self.doc()
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)          # the fixture really said it
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def test_clean_tree_is_clean(self):
        self.assertEqual(lint.check_protocol_tables(self.root), [])

    def test_reordered_stage_in_the_doc(self):
        self.rewrite("| review | `review.md` | file exists |\n"
                     "| ship | `release.md` | file exists |\n",
                     "| ship | `release.md` | file exists |\n"
                     "| review | `review.md` | file exists |\n")
        problems = lint.check_protocol_tables(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("out of step with protocol.py", problems[0])
        self.assertIn("verify → ship → review → operate", problems[0])

    def test_renamed_artifact_in_the_doc(self):
        self.rewrite("| verify | `verification.md` |", "| verify | `verify.md` |")
        self.assertEqual(
            lint.check_protocol_tables(self.root),
            ["protocol doc gives stage 'verify' artifact 'verify.md'; "
             "protocol.py reads 'verification.md'"])

    def test_stage_missing_from_the_doc(self):
        self.rewrite("| ship | `release.md` | file exists |\n", "")
        problems = lint.check_protocol_tables(self.root)
        self.assertEqual(len(problems), 1)
        self.assertIn("out of step with protocol.py", problems[0])

    def test_each_table_is_judged_independently(self):
        self.rewrite("| verify | `verification.md` |", "| verify | `verify.md` |")
        self.rewrite("| verify | `verification.md` |", "| verify | `nope.md` |")
        self.assertEqual(len(lint.check_protocol_tables(self.root)), 2)

    def test_missing_table_names_the_heading(self):
        path = self.doc()
        path.write_text("spec only\n", encoding="utf-8")
        problems = lint.check_protocol_tables(self.root)
        self.assertEqual(len(problems), 2)
        self.assertIn(self.PRODUCT, problems[0])
        self.assertIn(self.MAINTENANCE, problems[1])

    def test_prose_stage_names_normalize_to_slugs(self):
        # The real doc writes "UX Design"; protocol.py says "ux-design".
        # Both forms have to parse, or one is dropped silently and the
        # failure reads as a reordering.
        self.rewrite("| ux-design | `ux.md` |", "| UX Design | `ux.md` |")
        self.assertEqual(lint.check_protocol_tables(self.root), [])

    def test_absent_doc_belongs_to_check_protocol(self):
        self.doc().unlink()
        self.assertEqual(lint.check_protocol_tables(self.root), [])
        self.assertEqual(lint.check_protocol(self.root),
                         ["missing docs/pipeline-protocol.md"])

    def test_non_file_artifact_cell_is_not_compared(self):
        # Implement's cell in the real doc reads "code" — the stage's
        # product, not the file orientation reads. The stage still has to
        # be in the right place; only the artifact comparison is skipped.
        self.rewrite("| implement | `breakdown.md` |", "| implement | code |")
        self.assertEqual(lint.check_protocol_tables(self.root), [])


class TestTemplates(CheckerTreeTest):
    def test_missing_template(self):
        (self.root / "skills" / "verify" / "TEMPLATE.md").unlink()
        self.assertEqual(lint.check_templates(self.root),
                         ["missing skills/verify/TEMPLATE.md"])

    def test_discovered_non_stage_skill_needs_no_template(self):
        extra = self.root / "skills" / "extra"
        extra.mkdir()
        (extra / "SKILL.md").write_text(
            "---\nname: extra\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
        self.assertEqual(lint.check_templates(self.root), [])
        self.assertEqual(lint.check_router(self.root), [])


class TestRouter(CheckerTreeTest):
    """The router skill is prose an agent reads at RUNTIME, so drift there
    is drift in shipped behaviour. The mention check alone passed on the
    word "idea" appearing anywhere; these pin the hand-off list, whose
    membership and order are derivable from protocol's walk tables.

    What stays UNPINNED, deliberately and worth stating: the router's
    conditionals — the `ux:` field, the `re-entry:` field, the Implement
    checkbox rule. Those are English, and no mechanical check here reads
    them. A green lint means the list is right, not that the routing prose
    is.
    """

    def write(self, body):
        (self.root / "skills" / "next" / "SKILL.md").write_text(
            "---\nname: next\ndescription: d\n---\n\n" + body + "\n",
            encoding="utf-8")

    def handoffs(self, stages):
        return "\n".join(f"   - {s} → the `{s}` skill" for s in stages)

    def test_a_complete_in_order_list_is_clean(self):
        self.write(self.handoffs(lint.routed_order()))
        self.assertEqual(lint.check_router(self.root), [])

    def test_omitted_stage(self):
        stages = [s for s in lint.routed_order() if s != "ship"]
        self.write(" ".join(stages) + "\n\n" + self.handoffs(stages))
        self.assertEqual(lint.check_router(self.root), [
            "router never mentions stage skill 'ship'",
            "router's hand-off list omits stage skill 'ship'"])

    def test_omitted_maintenance_stage(self):
        # capture sits outside the spine but the router routes to it
        # (ADR-0025) — a router that forgets it is as broken as one that
        # forgets ship.
        stages = [s for s in lint.routed_order() if s != "capture"]
        self.write(" ".join(stages) + "\n\n" + self.handoffs(stages))
        self.assertEqual(lint.check_router(self.root), [
            "router never mentions stage skill 'capture'",
            "router's hand-off list omits stage skill 'capture'"])

    def test_a_router_with_no_handoff_list_at_all(self):
        """The case the mention check could never see: every slug present
        as prose, nothing routing anywhere."""
        self.write(" ".join(lint.routed_order()))
        self.assertEqual(lint.check_router(self.root), [
            "router has no hand-off list — step 5's '<stage> → the"
            " `<stage>` skill' lines are what route a run, and nothing"
            " else names the order"])

    def test_a_list_out_of_pipeline_order(self):
        order = lint.routed_order()
        swapped = order[:]
        i, j = swapped.index("verify"), swapped.index("review")
        swapped[i], swapped[j] = swapped[j], swapped[i]
        self.write(self.handoffs(swapped))
        problems = lint.check_router(self.root)
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith(
            "router's hand-off list is out of pipeline order:"), problems)
        self.assertIn("verify → review", problems[0])

    def test_a_list_naming_a_stage_the_tables_do_not_route_to(self):
        self.write(self.handoffs(lint.routed_order() + ["retire"]))
        self.assertEqual(lint.check_router(self.root), [
            "router hands off to 'retire', which protocol's walk tables do"
            " not route to"])

    def test_a_stage_pointed_at_the_wrong_skill(self):
        order = lint.routed_order()
        body = self.handoffs(order).replace(
            "- verify → the `verify` skill", "- verify → the `review` skill")
        self.write(body)
        problems = lint.check_router(self.root)
        self.assertIn("router hands 'verify' off to the 'review' skill; a"
                      " stage routes to the skill of the same name",
                      problems)

    def test_the_shipped_router_satisfies_all_of_it(self):
        """Against the real file, not a fixture — the point is the shipped
        prose, and a checker only ever run on fixtures pins nothing."""
        self.assertEqual(lint.check_router(ROOT), [])

    def test_the_order_is_derived_not_restated(self):
        """routed_order() must come from protocol's tables, so adding a
        stage there is a single edit. Pinning the literal list here would
        recreate the duplication this closes."""
        self.assertEqual(
            lint.routed_order(),
            [s for s, _ in protocol.MAINTENANCE_STAGE_ARTIFACTS
             if s not in [p for p, _ in protocol.STAGE_ARTIFACTS]]
            + [s for s, _ in protocol.STAGE_ARTIFACTS])


class TestRouterConditionals(CheckerTreeTest):
    """Issue #444: the router's conditionals (ux:, re-entry:, the
    Implement checkbox rule) are English restating protocol.py, and
    nothing checked the restatement still says what the code does.
    """

    def write(self, body):
        (self.root / "skills" / "next" / "SKILL.md").write_text(
            "---\nname: next\ndescription: d\n---\n\n" + body + "\n",
            encoding="utf-8")

    def clean_body(self):
        return ("Honor the `ux:` field in `prd.md` frontmatter, the"
                " `re-entry:` field in `defect.md` frontmatter, and the"
                " Implement checkbox rule.\n\n"
                + "\n".join(f"   - {s} → the `{s}` skill"
                            for s in lint.routed_order()))

    def test_a_conforming_router_is_clean(self):
        self.write(self.clean_body())
        self.assertEqual(lint.check_router_conditionals(self.root), [])

    def test_the_shipped_router_satisfies_all_of_it(self):
        """Against the real file, not a fixture."""
        self.assertEqual(lint.check_router_conditionals(ROOT), [])

    def test_a_dropped_conditional_is_flagged(self):
        body = self.clean_body().replace(
            "Honor the `ux:` field in `prd.md` frontmatter, the"
            " `re-entry:` field in `defect.md` frontmatter, and the"
            " Implement checkbox rule.",
            "Honor the `re-entry:` field in `defect.md` frontmatter.")
        self.write(body)
        self.assertEqual(lint.check_router_conditionals(self.root), [
            "router names no 'ux' conditional (`ux:` field in `<file>`)",
            "router names no Implement checkbox rule"])

    def test_a_conditional_missing_its_file_entirely_is_flagged(self):
        body = self.clean_body().replace("`prd.md` frontmatter", "the run")
        self.write(body)
        self.assertEqual(lint.check_router_conditionals(self.root), [
            "router names no 'ux' conditional (`ux:` field in `<file>`)"])

    def test_cross_wired_fields_are_flagged(self):
        """Review round 1 (issue #444): the first version of this checker
        verified `ux:`/`re-entry:` and `prd.md`/`defect.md` each appeared
        SOMEWHERE in the document, so swapping which file each conditional
        claims to live in passed clean — the exact drift the checker's own
        message claims to catch. CONDITIONAL_PHRASE requires the file to
        sit in the same "`field:` field in `file`" clause as its field, so
        a swap must now be caught."""
        body = self.clean_body().replace(
            "`ux:` field in `prd.md`", "`ux:` field in `TEMP`"
        ).replace(
            "`re-entry:` field in `defect.md`", "`re-entry:` field in `prd.md`"
        ).replace("`TEMP`", "`defect.md`")
        self.write(body)
        self.assertEqual(lint.check_router_conditionals(self.root), [
            "router's 'ux' conditional names 'defect.md';"
            " protocol._ux_skipped reads it from 'prd.md'",
            "router's 're-entry' conditional names 'prd.md';"
            " protocol._re_entry_architect reads it from 'defect.md'"])

    def test_a_code_side_field_rename_is_flagged_not_missed(self):
        """The point of deriving from the code's own source rather than a
        second hand-typed 'ux'/'re-entry' pair: if protocol.py stopped
        reading the field the router still claims it reads, this must
        say so rather than staying quiet because the prose still matches
        what a human typed here yesterday."""
        self.write(self.clean_body())

        def renamed(run_dir):
            prd = run_dir / "prd.md"
            if not prd.is_file():
                return False
            return (protocol.read_frontmatter(prd) or {}).get(
                "ux-mode") == "not-applicable"

        renamed.__name__ = "_ux_skipped"
        original = lint.ROUTER_CONDITIONALS
        lint.ROUTER_CONDITIONALS = (("ux", "prd.md", renamed),) \
            + original[1:]
        try:
            self.assertEqual(lint.check_router_conditionals(self.root), [
                "protocol._ux_skipped no longer reads 'ux' — the router"
                " prose is stale"])
        finally:
            lint.ROUTER_CONDITIONALS = original

    def test_a_docstring_decoy_does_not_defeat_the_rename_check(self):
        """Review round 1 (issue #444): inspect.getsource returns the
        docstring verbatim, unstripped. A migration-note docstring that
        still quotes the OLD field name defeated a plain substring search
        even though the function's real `.get(...)` call had moved on —
        exactly the silent-drift shape this checker exists to catch.
        _code_literals must see only what the function's body actually
        executes, so this decoy must not launder a real rename."""
        self.write(self.clean_body())

        def renamed(run_dir):
            """(renamed from "ux" to "ux_mode" — see migration notes)"""
            prd = run_dir / "prd.md"  # was: reads "ux"
            if not prd.is_file():
                return False
            return (protocol.read_frontmatter(prd) or {}).get(
                "ux_mode") == "not-applicable"

        renamed.__name__ = "_ux_skipped"
        original = lint.ROUTER_CONDITIONALS
        lint.ROUTER_CONDITIONALS = (("ux", "prd.md", renamed),) \
            + original[1:]
        try:
            self.assertEqual(lint.check_router_conditionals(self.root), [
                "protocol._ux_skipped no longer reads 'ux' — the router"
                " prose is stale"])
        finally:
            lint.ROUTER_CONDITIONALS = original


class TestProtocol(CheckerTreeTest):
    def test_missing_spec(self):
        (self.root / "docs" / "pipeline-protocol.md").unlink()
        self.assertEqual(lint.check_protocol(self.root),
                         ["missing docs/pipeline-protocol.md"])

    def test_a_deleted_in_flight_section_strands_two_recitals(self):
        """The other half of the recital pin. That pin holds capture and
        idea to IN_FLIGHT_HEADING and holds IN_FLIGHT_HEADING to nothing,
        so deleting the section leaves all three agreeing while both
        skills point at a heading that is gone — green, and wrong."""
        path = self.root / "docs" / "pipeline-protocol.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                f"### {lint.IN_FLIGHT_HEADING}\n\n", ""),
            encoding="utf-8")
        self.assertEqual(
            lint.check_protocol(self.root),
            [f"docs/pipeline-protocol.md no longer states "
             f"{lint.IN_FLIGHT_HEADING!r}, which capture and idea both "
             "recite"])


class TestEvals(CheckerTreeTest):
    def test_invalid_expected_and_thin_coverage(self):
        data = json.loads(
            (self.root / "evals" / "routing.json").read_text(encoding="utf-8"))
        case = next(c for c in data["cases"] if c["id"] == "idea-0")
        case["expected"] = "bogus"
        (self.root / "evals" / "routing.json").write_text(
            json.dumps(data), encoding="utf-8")
        problems = lint.check_evals(self.root)
        self.assertIn("evals/routing.json case 'idea-0' has invalid "
                      "expected 'bogus'", problems)
        self.assertIn("evals/routing.json covers skill 'idea' in only "
                      "2 case(s), need >= 3", problems)


class TestOutputEvals(CheckerTreeTest):
    def test_skill_name_mismatch_and_missing_fixture(self):
        output_dir = self.root / "evals" / "output"
        (output_dir / "idea.json").write_text(json.dumps({
            "skill_name": "prd",
            "evals": [{"id": 1, "prompt": "p", "run_scale": "feature:x",
                       "expected_output": "o", "expectations": ["x"],
                       "run_fixture": "evals/fixtures/absent"}],
        }), encoding="utf-8")
        self.assertEqual(
            lint.check_output_evals(self.root),
            ["evals/output/idea.json skill_name is 'prd', expected 'idea'",
             "evals/output/idea.json eval 1 run_fixture "
             "'evals/fixtures/absent' does not exist"])

    def test_record_missing_documented_fields_is_flagged(self):
        # the previously silent gap (issue #25): docs promise six fields,
        # lint used to accept records without prompt/run_scale/expected_output
        (self.root / "evals" / "output" / "idea.json").write_text(json.dumps({
            "skill_name": "idea",
            "evals": [{"id": 1, "expectations": ["x"],
                       "run_fixture": "evals/fixtures/seeded-run"}],
        }), encoding="utf-8")
        self.assertEqual(
            lint.check_output_evals(self.root),
            ["evals/output/idea.json eval 1 missing field: prompt",
             "evals/output/idea.json eval 1 missing field: run_scale",
             "evals/output/idea.json eval 1 missing field: expected_output"])

    def test_null_evals_is_diagnosed_not_crashed(self):
        # a present-but-null collection must yield validate_output's
        # diagnostic, and the run_fixture stat loop must not raise
        (self.root / "evals" / "output" / "idea.json").write_text(json.dumps({
            "skill_name": "idea",
            "evals": None,
        }), encoding="utf-8")
        problems = lint.check_output_evals(self.root)
        self.assertIn("evals/output/idea.json evals is not a list", problems)

    def test_bytes_that_are_not_utf8_are_a_problem_not_a_crash(self):
        """This checker walks a directory, so one undecodable file must
        not take the whole walk down with it — the same reason the null
        case above is diagnosed rather than crashed."""
        (self.root / "evals" / "output" / "idea.json").write_bytes(
            '{"skill_name": "caf\u00e9"}'.encode("latin-1"))
        problems = lint.check_output_evals(self.root)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            "evals/output/idea.json is not valid JSON:"), problems)

    def test_a_record_file_that_is_not_json_is_one_exact_problem(self):
        (self.root / "evals" / "output" / "idea.json").write_text(
            "{nope", encoding="utf-8")
        self.assertEqual(lint.check_output_evals(self.root), [
            "evals/output/idea.json is not valid JSON: Expecting property"
            " name enclosed in double quotes: line 1 column 2 (char 1)"])

    def test_a_null_record_file_is_not_a_json_object(self):
        """The shape wording is eval_schema.validate_output's and covers
        null — which is why this reader keeps its own parse rather than
        asking cli.read_file for a shape."""
        (self.root / "evals" / "output" / "idea.json").write_text(
            "null", encoding="utf-8")
        self.assertEqual(lint.check_output_evals(self.root),
                         ["evals/output/idea.json is not a JSON object"])


class TestBacklog(CheckerTreeTest):
    """The seed backlog is strictly opt-in (ADR-0029): the clean tree has
    no docs/backlog.md and TestCleanTree already proves absence is zero
    problems. protocol.check_backlog owns the grammar; this checker keeps
    the filesystem half."""

    def test_present_backlog_is_validated_against_the_grammar(self):
        (self.root / "docs" / "backlog.md").write_text(
            "- good seed (from: feature:x)\n- dangling seed\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_backlog(self.root),
            ["backlog: line 2: entry does not match "
             "'- <seed text> (from: <run-ref>)'"])

    def test_conformant_backlog_yields_no_problems(self):
        (self.root / "docs" / "backlog.md").write_text(
            "advisory header\n\n"
            "- a seed (from: session:2026-07-05)\n"
            "- claimed seed (from: product) (claimed: feature:y)\n",
            encoding="utf-8")
        self.assertEqual(lint.check_backlog(self.root), [])

    def test_unreadable_backlog_yields_one_problem_string(self):
        path = self.root / "docs" / "backlog.md"
        path.write_text("- a seed (from: product)\n", encoding="utf-8")
        with mock.patch.object(Path, "read_text",
                                side_effect=OSError("Permission denied")):
            problems = lint.check_backlog(self.root)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            "backlog: docs/backlog.md is unreadable:"))

    def test_an_empty_backlog_yields_no_problems(self):
        (self.root / "docs" / "backlog.md").write_text("", encoding="utf-8")
        self.assertEqual(lint.check_backlog(self.root), [])


class TestLedger(CheckerTreeTest):
    def test_missing_row(self):
        (self.root / "LEDGER.md").write_text(
            "".join(f"| {slug} |\n" for slug in ALL_SKILLS
                    if slug != "operate"), encoding="utf-8")
        self.assertEqual(lint.check_ledger(self.root),
                         ["LEDGER.md has no row for skill 'operate'"])

    def test_a_slug_nested_in_a_longer_one_still_needs_its_own_row(self):
        """`architect` is a substring of two other registered slugs, so a
        substring test can never find its row missing. `review` (inside
        `address-pr-review`) and `architecture-diagram` (inside
        `interactive-architecture-diagram`) are held up the same way."""
        (self.root / "LEDGER.md").write_text(
            "".join(f"| {slug} |\n" for slug in ALL_SKILLS
                    if slug != "architect"), encoding="utf-8")
        self.assertEqual(lint.check_ledger(self.root),
                         ["LEDGER.md has no row for skill 'architect'"])

    def test_prose_under_the_table_is_not_a_row(self):
        """The problem string says row, and the real LEDGER.md carries
        several paragraphs of reading notes below the table that name
        skills by slug. A row deleted while the reading still mentions the
        skill must not pass the check that claims to look for the row."""
        (self.root / "LEDGER.md").write_text(
            "".join(f"| {slug} |\n" for slug in ALL_SKILLS
                    if slug != "operate")
            + "\nReading: operate mostly under-triggers.\n",
            encoding="utf-8")
        self.assertEqual(lint.check_ledger(self.root),
                         ["LEDGER.md has no row for skill 'operate'"])

    def test_every_registered_skill_can_be_reported_missing(self):
        """Closure over the taxonomy: drop each slug's row in turn and
        the checker names that slug, so no blind spot can hide behind
        whichever three slugs the tests above happen to pick. Says
        nothing about the other direction — a stale row for a skill that
        no longer exists has no checker at all, here or anywhere."""
        for slug in ALL_SKILLS:
            with self.subTest(slug=slug):
                (self.root / "LEDGER.md").write_text(
                    "".join(f"| {other} |\n" for other in ALL_SKILLS
                            if other != slug), encoding="utf-8")
                self.assertEqual(lint.check_ledger(self.root),
                                 [f"LEDGER.md has no row for skill {slug!r}"])

    def test_a_row_and_a_mention_agree_about_what_a_slug_is(self):
        """extra_skills accepts any directory name, so the two halves of
        the fix have to accept the same names. A slug opening with a
        digit is a row for check_ledger exactly as it is a mention for
        check_readme_skills — otherwise a present row reads as missing."""
        rogue = self.root / "skills" / "3d-diagram"
        rogue.mkdir()
        (rogue / "SKILL.md").write_text(
            "---\nname: 3d-diagram\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
        for path, line in ((self.root / "LEDGER.md", "| 3d-diagram |\n"),
                           (self.root / "README.md", "- `3d-diagram`\n")):
            path.write_text(path.read_text(encoding="utf-8") + line,
                            encoding="utf-8")
        self.assertEqual(lint.check_ledger(self.root), [])
        self.assertEqual(lint.check_readme_skills(self.root), [])

    def test_discovered_skill_needs_a_row_too(self):
        extra = self.root / "skills" / "extra"
        extra.mkdir()
        (extra / "SKILL.md").write_text(
            "---\nname: extra\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
        self.assertEqual(lint.check_ledger(self.root),
                         ["LEDGER.md has no row for skill 'extra'"])


class TestLedgerNoOrphans(CheckerTreeTest):
    """The reverse direction (issue #455): a LEDGER.md row naming a skill
    the current taxonomy no longer registers. ALL_SKILLS + extra_skills is
    already the trusted "what is a skill" source check_ledger holds
    LEDGER.md to in the forward direction; no historical registry is
    needed to hold it to the same set in reverse."""

    def test_orphaned_row_is_reported(self):
        ledger = self.root / "LEDGER.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8") + "| retired-skill |\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_ledger_no_orphans(self.root),
            ["LEDGER.md has a row for skill 'retired-skill', which the "
             "taxonomy no longer registers"])

    def test_every_current_skill_stays_clean(self):
        # A row for every registered skill, and nothing else: the exact
        # shape make_clean_tree writes. No false positives.
        self.assertEqual(lint.check_ledger_no_orphans(self.root), [])

    def test_a_row_nested_in_a_longer_registered_slug_is_not_an_orphan(self):
        """'review' is a substring of 'address-pr-review', both registered.
        The orphan check reads exact row slugs (ledger_rows), not
        substrings, so neither's row is mistaken for the other's."""
        self.assertEqual(lint.check_ledger_no_orphans(self.root), [])
        self.assertIn("review", lint.ledger_rows(
            (self.root / "LEDGER.md").read_text(encoding="utf-8")))

    def test_prose_mentioning_a_dropped_skill_is_not_a_row(self):
        """Mirrors check_ledger's own row-only scope: a mention in the
        reading notes below the table is not a row, so it is not
        reported. Same boundary, same file, same reason (#371)."""
        ledger = self.root / "LEDGER.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8")
            + "\nReading: retired-skill was dropped last quarter.\n",
            encoding="utf-8")
        self.assertEqual(lint.check_ledger_no_orphans(self.root), [])

    def test_missing_ledger_yields_no_problem_here(self):
        (self.root / "LEDGER.md").unlink()
        self.assertEqual(lint.check_ledger_no_orphans(self.root), [])


class TestLedgerLinks(CheckerTreeTest):
    def test_unresolved_eval_link(self):
        ledger = self.root / "LEDGER.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8")
            + "| extra | "
            "[2026-02-02](evals/results/trigger-2026-02-02.json) |\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_ledger_links(self.root),
            ["LEDGER.md links to missing eval results file "
             "'evals/results/trigger-2026-02-02.json'"])

    def test_link_to_directory_not_file_is_reported(self):
        (self.root / "evals" / "results" / "output").mkdir()
        ledger = self.root / "LEDGER.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8")
            + "| extra | [2026-03-03](evals/results/output) |\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_ledger_links(self.root),
            ["LEDGER.md links to eval results path 'evals/results/output' "
             "that does not match the results naming grammar",
             "LEDGER.md links to missing eval results file "
             "'evals/results/output'"])

    def test_off_grammar_link_is_reported_even_when_file_exists(self):
        # issue #26: the check must enforce the naming grammar, not just
        # that something exists under evals/results/
        (self.root / "evals" / "results" / "notes.md").write_text(
            "n\n", encoding="utf-8")
        ledger = self.root / "LEDGER.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8")
            + "| extra | [notes](evals/results/notes.md) |\n",
            encoding="utf-8")
        self.assertEqual(
            lint.check_ledger_links(self.root),
            ["LEDGER.md links to eval results path 'evals/results/notes.md' "
             "that does not match the results naming grammar"])

    def test_valid_output_grading_link_passes(self):
        grading_dir = (self.root / "evals" / "results" / "output"
                       / "idea-2026-01-01-2")
        grading_dir.mkdir(parents=True)
        (grading_dir / "grading.json").write_text("{}", encoding="utf-8")
        ledger = self.root / "LEDGER.md"
        ledger.write_text(
            ledger.read_text(encoding="utf-8")
            + "| idea | [2026-01-01]"
            "(evals/results/output/idea-2026-01-01-2/grading.json) |\n",
            encoding="utf-8")
        self.assertEqual(lint.check_ledger_links(self.root), [])


class TestMainSummary(cli_contract.ReportContract, unittest.TestCase):
    """lint.main against the real repo — the one summary with a coda
    (`across N skills`) after the count clause. CI greps this line."""

    @property
    def summary_line(self):
        checked = len(lint.ALL_SKILLS) + len(lint.extra_skills(ROOT))
        return f"lint: 0 problem(s) across {checked} skills"

    def clean_cli(self):
        return cli_contract.capture(lint.main)


if __name__ == "__main__":
    unittest.main()
