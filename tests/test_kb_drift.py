"""kb_drift.py (issue #682): instruction-file drift — the claims
CLAUDE.md, AGENTS.md and .claude/rules/** make about the repo, checked
against what is on disk. Pinned against tempfile fixture trees; every
problem string is asserted exactly.
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kb  # noqa: E402
import kb_drift  # noqa: E402


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Tree(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        write(self.root / "src" / "app.py", "x = 1\n")
        write(self.root / "scripts" / "build.sh", "echo\n")

    def file(self, rel, text):
        write(self.root / rel, text)

    def skill(self, name, base=".claude/skills"):
        write(self.root / base / name / "SKILL.md",
              f"---\nname: {name}\n---\n")

    def agent(self, filename, name):
        write(self.root / ".claude" / "agents" / filename,
              f"---\nname: {name}\n---\n")

    def drift(self):
        return kb_drift.drift(self.root)


class TestFiles(Tree):
    def test_no_instruction_file_is_one_problem(self):
        self.assertEqual(self.drift(), [
            "drift: no instruction file (CLAUDE.md, AGENTS.md,"
            " .claude/CLAUDE.md, .claude/rules/**/*.md) to audit"])

    def test_clean_file_has_no_problems(self):
        self.file("CLAUDE.md", "# Notes\n\nEdit `src/app.py`, then run"
                  " `bash scripts/build.sh`.\n")
        self.assertEqual(self.drift(), [])

    def test_rules_files_are_audited(self):
        self.file(".claude/rules/style/a.md", "See `src/gone.py`.\n")
        self.assertEqual(self.drift(), [
            "drift: .claude/rules/style/a.md:1 names path 'src/gone.py',"
            " which does not exist"])


class TestPaths(Tree):
    def test_dangling_paths_in_spans_links_and_commands(self):
        self.file("CLAUDE.md", "\n".join([
            "# Notes",
            "Read `docs/missing.md` and [the guide](docs/guide.md#top).",
            "```",
            "python3 tools/gone.py --flag",
            "node scripts/build.sh",
            "```",
            "Run `bash scripts/old.sh now`.",
        ]) + "\n")
        self.assertEqual(self.drift(), [
            "drift: CLAUDE.md:2 names path 'docs/missing.md', which does"
            " not exist",
            "drift: CLAUDE.md:2 names path 'docs/guide.md', which does not"
            " exist",
            "drift: CLAUDE.md:4 names path 'tools/gone.py', which does not"
            " exist",
            "drift: CLAUDE.md:7 names path 'scripts/old.sh', which does"
            " not exist",
        ])

    def test_titled_and_angle_bracket_dangling_links(self):
        self.file("CLAUDE.md", '[a](docs/a.md "Title") [b](<docs/b.md>)'
                  ' [ok](<src/app.py> "App")\n')
        self.assertEqual(self.drift(), [
            "drift: CLAUDE.md:1 names path 'docs/a.md', which does not"
            " exist",
            "drift: CLAUDE.md:1 names path 'docs/b.md', which does not"
            " exist",
        ])

    def test_placeholders_urls_globs_home_and_absolute_are_skipped(self):
        self.file("CLAUDE.md", "\n".join([
            "`docs/features/<slug>/run.md` `https://x.io/a.md`",
            "`src/*.py` `~/.claude/skills/` `/etc/hosts.conf`",
            "`$HOME/a/b.md` `{a,b}/c.md` [web](https://x.io/b.md)",
            "`src/app.py:12` `a/b` `and/or`",
        ]) + "\n")
        self.assertEqual(self.drift(), [])

    def test_a_bare_extension_is_not_a_path(self):
        self.file("CLAUDE.md", "Edit `.md` and `.js/.ts` files.\n")
        self.assertEqual(self.drift(), [])

    def test_gitignored_output_paths_are_not_dangling(self):
        self.file(".gitignore", "# out\n/out/results/\ndist/\n*.txt\n"
                  "!keep.txt\n")
        self.file("CLAUDE.md", "`out/results/` `pkg/dist/x.js` `a.txt`"
                  " `out/other/` `keep.txt`\n")
        self.assertEqual(self.drift(), [
            "drift: CLAUDE.md:1 names path 'out/other/', which does not"
            " exist",
            "drift: CLAUDE.md:1 names path 'keep.txt', which does not"
            " exist",
        ])

    def test_a_bare_filename_resolves_anywhere_in_the_repo(self):
        self.file("CLAUDE.md", "`app.py` lives deep; `nowhere.py` does"
                  " not.\n")
        self.assertEqual(self.drift(), [
            "drift: CLAUDE.md:1 names path 'nowhere.py', which does not"
            " exist"])

    def test_a_link_resolves_against_its_file_too(self):
        self.file(".claude/rules/a.md", "[b](b.md)\n")
        self.file(".claude/rules/b.md", "ok\n")
        self.assertEqual(self.drift(), [])

    def test_ignore_marker_excuses_a_named_path(self):
        self.file("CLAUDE.md", "<!-- drift-ignore: docs/prd/ -->\nNever a"
                  " parallel `docs/prd/` tree.\n")
        self.assertEqual(self.drift(), [])


class TestTables(Tree):
    def test_skill_table_both_directions(self):
        self.skill("deploy")
        self.skill("tdd")
        self.skill("lint-fix")
        self.file("CLAUDE.md", "\n".join([
            "| Skill | Use |", "|---|---|",
            "| `/deploy` | ship |", "| `ghost` | gone |",
            "| `/lint-fix` | tidy |",
        ]) + "\n")
        self.assertEqual(self.drift(), [
            "drift: CLAUDE.md:4 lists skill 'ghost', which is not on disk",
            "drift: skill 'tdd' is on disk (.claude/skills/tdd/) but no"
            " skill table in an instruction file lists it",
        ])

    def test_agent_table_uses_the_frontmatter_name(self):
        self.agent("reviewer.md", "code-reviewer")
        self.agent("planner.md", "planner")
        self.file("AGENTS.md", "\n".join([
            "| Agent | Role |", "|---|---|",
            "| `reviewer` | reviews |", "| planner | plans |",
        ]) + "\n")
        self.assertEqual(self.drift(), [
            "drift: AGENTS.md:3 lists agent 'reviewer', which is not on"
            " disk",
            "drift: agent 'code-reviewer' is on disk"
            " (.claude/agents/reviewer.md) but no agent table in an"
            " instruction file lists it",
        ])

    def test_no_table_means_no_undocumented_entry_finding(self):
        self.skill("deploy")
        self.file("CLAUDE.md", "# Notes\n")
        self.assertEqual(self.drift(), [])


class TestSlashCommands(Tree):
    def test_unresolved_and_resolved_commands(self):
        self.skill("deploy")
        self.file(".claude/commands/ship.md", "x\n")
        self.file("CLAUDE.md", "Use `/deploy`, `/ship now`, `/help`,"
                  " `/tdd` and `/src/app.py`.\n")
        self.assertEqual(self.drift(), [
            "drift: CLAUDE.md:1 references /tdd, which resolves to no"
            " skill or command in this repo"])

    def test_plugin_qualified_commands(self):
        write(self.root / ".claude-plugin" / "plugin.json",
              json.dumps({"name": "kit"}))
        self.skill("next", base="skills")
        self.skill("lint", base="plugins/tools/skills")
        write(self.root / ".claude" / "settings.json", json.dumps(
            {"enabledPlugins": {"remote@market": True,
                                "off@market": False}}))
        self.file("CLAUDE.md", "\n".join([
            "`/kit:next` `/kit:gone` `/tools:lint` `/remote:any`",
            "`/off:x` `/nope:y`",
        ]) + "\n")
        self.assertEqual(self.drift(), [
            "drift: CLAUDE.md:1 references /kit:gone, but plugin 'kit'"
            " has no skill or command 'gone'",
            "drift: CLAUDE.md:2 references /off:x, but plugin 'off' is"
            " neither in this repo nor enabled in .claude/settings.json",
            "drift: CLAUDE.md:2 references /nope:y, but plugin 'nope' is"
            " neither in this repo nor enabled in .claude/settings.json",
        ])

    def test_unreadable_settings_is_a_problem(self):
        write(self.root / ".claude" / "settings.json", "{oops")
        self.file("CLAUDE.md", "# Notes\n")
        problems = self.drift()
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            "drift: .claude/settings.json is not valid JSON: "))


class TestSurfaces(Tree):
    def test_populated_undocumented_directory(self):
        self.agent("a.md", "a")
        self.agent("b.md", "b")
        write(self.root / ".claude" / "hooks" / "one.sh", "x\n")
        self.file("CLAUDE.md", "# Notes\n")
        self.assertEqual(self.drift(), [
            "drift: .claude/agents/ holds 2 entries but no instruction"
            " file mentions it or any of them"])

    def test_a_directory_named_or_an_entry_named_counts_as_documented(self):
        self.agent("a.md", "a")
        self.agent("b.md", "b")
        write(self.root / "plugins" / "x" / "p.json", "{}")
        write(self.root / "plugins" / "y" / "p.json", "{}")
        self.file("CLAUDE.md", "Agents live in .claude/agents.\n")
        self.file("AGENTS.md", "The `y` plugin is ours.\n")
        self.assertEqual(self.drift(), [])


class TestMain(Tree):
    def test_drift_reports_through_the_problem_contract(self):
        self.file("CLAUDE.md", "`gone/x.md`\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = kb.main(["drift", str(self.root)])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue().splitlines(), [
            "drift: CLAUDE.md:1 names path 'gone/x.md', which does not"
            " exist",
            "drift: 1 problem(s)"])


if __name__ == "__main__":
    unittest.main()
