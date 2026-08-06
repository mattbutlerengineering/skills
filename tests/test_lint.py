"""Lint-checker seam: every checker takes the repo root as a parameter,
so seeded temp trees are a second adapter beside the real repo.

Trees are built programmatically (not committed like the orientation
fixtures) because the clean tree must track protocol.py's taxonomy —
committed copies would duplicate those constants and rot. Each defect
test seeds the clean tree, breaks one aspect, and asserts the checker's
exact problem strings through its public interface.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import lint  # noqa: E402
from protocol import (ALL_SKILLS, MAINTENANCE_STAGES,  # noqa: E402
                      STAGE_ARTIFACTS, STAGES, TEMPLATED_STAGES)

SPINE = [stage for stage, _ in STAGE_ARTIFACTS]
SPINE_ARTIFACT = dict(STAGE_ARTIFACTS)


def recital_body(slug):
    """The smallest body whose recitals state the protocol facts
    check_skill_recitals pins — one canonical phrasing per convention,
    derived from the protocol tables so the clean tree tracks them."""
    if slug == "capture":
        return ("## Process\n\n"
                "1. Record `re-entry: implement` or `re-entry: architect`.\n"
                "2. Write the artifact as `defect.md`.\n"
                "3. Hand off per the recorded re-entry.\n")
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
    return "## Process\n\n" + "\n".join(lines) + "\n"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402


def make_clean_tree(root):
    """Seed the smallest tree on which every checker reports zero problems."""
    plugin_dir = root / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(json.dumps(
        {"name": "t", "description": "t", "version": "0"}), encoding="utf-8")

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
    (root / "skills" / "next" / "SKILL.md").write_text(
        "---\nname: next\ndescription: d\n---\n\n"
        + " ".join(STAGES + MAINTENANCE_STAGES) + "\n",
        encoding="utf-8")

    (root / "docs").mkdir()
    (root / "docs" / "pipeline-protocol.md").write_text("spec\n",
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
                  "1. Record `re-entry: implement`.\n"
                  "2. Write the artifact as `defect.md`.\n")
        self.assertEqual(
            lint.check_skill_recitals(self.root),
            ["skills/capture/SKILL.md never records re-entry option "
             "'re-entry: architect'"])

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
    def test_omitted_stage(self):
        mentions = " ".join(s for s in STAGES + MAINTENANCE_STAGES
                            if s != "ship")
        (self.root / "skills" / "next" / "SKILL.md").write_text(
            "---\nname: next\ndescription: d\n---\n\n" + mentions + "\n",
            encoding="utf-8")
        self.assertEqual(lint.check_router(self.root),
                         ["router never mentions stage skill 'ship'"])

    def test_omitted_maintenance_stage(self):
        # capture sits outside the spine but the router routes to it
        # (ADR-0025) — a router that forgets it is as broken as one that
        # forgets ship.
        (self.root / "skills" / "next" / "SKILL.md").write_text(
            "---\nname: next\ndescription: d\n---\n\n"
            + " ".join(STAGES) + "\n", encoding="utf-8")
        self.assertEqual(lint.check_router(self.root),
                         ["router never mentions stage skill 'capture'"])


class TestProtocol(CheckerTreeTest):
    def test_missing_spec(self):
        (self.root / "docs" / "pipeline-protocol.md").unlink()
        self.assertEqual(lint.check_protocol(self.root),
                         ["missing docs/pipeline-protocol.md"])


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
        path.chmod(0)
        self.addCleanup(path.chmod, 0o644)
        problems = lint.check_backlog(self.root)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            "backlog: docs/backlog.md is unreadable:"))


class TestLedger(CheckerTreeTest):
    def test_missing_row(self):
        (self.root / "LEDGER.md").write_text(
            "".join(f"| {slug} |\n" for slug in ALL_SKILLS
                    if slug != "operate"), encoding="utf-8")
        self.assertEqual(lint.check_ledger(self.root),
                         ["LEDGER.md has no row for skill 'operate'"])

    def test_discovered_skill_needs_a_row_too(self):
        extra = self.root / "skills" / "extra"
        extra.mkdir()
        (extra / "SKILL.md").write_text(
            "---\nname: extra\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
        self.assertEqual(lint.check_ledger(self.root),
                         ["LEDGER.md has no row for skill 'extra'"])


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
