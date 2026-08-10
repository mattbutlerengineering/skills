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
import protocol  # noqa: E402
from protocol import (ALL_SKILLS, MAINTENANCE_STAGES, STAGES,  # noqa: E402
                      TEMPLATED_STAGES)


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
            f"---\nname: {slug}\ndescription: d\n---\n\nbody\n",
            encoding="utf-8")
    for slug in TEMPLATED_STAGES:
        (root / "skills" / slug / "TEMPLATE.md").write_text(
            "t\n", encoding="utf-8")
    # The router needs its hand-off list, not just the slugs: check_router
    # pins that list's membership and pipeline order, so a bare mention
    # dump is no longer a clean router.
    (root / "skills" / "next" / "SKILL.md").write_text(
        "---\nname: next\ndescription: d\n---\n\n"
        + "\n".join(f"   - {stage} → the `{stage}` skill"
                    for stage in lint.routed_order()) + "\n",
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


if __name__ == "__main__":
    unittest.main()
