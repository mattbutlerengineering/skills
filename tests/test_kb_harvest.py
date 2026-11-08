"""kb_harvest.py (issue #681): the knowledge-base skill's transcript
miner — check-failed -> fix -> check-passed arcs and recurring tool
errors from Claude Code session transcripts, proposed for review.

Every transcript here is synthetic: a fixture tree that mimics the
harness's JSONL shape (assistant tool_use, user tool_result) under a
temporary projects directory. No real session content is read or
copied by the suite.
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import git_repo  # noqa: E402
import kb  # noqa: E402
import kb_harvest  # noqa: E402

REPO = "/work/acme.app"
DAY = 86400


class Session:
    """Builds one synthetic transcript, a JSONL record per line."""

    def __init__(self, sid="s1", cwd=REPO):
        self.sid, self.cwd, self.lines, self.n = sid, cwd, [], 0

    def _record(self, kind, content):
        self.lines.append(json.dumps({
            "type": kind, "sessionId": self.sid, "cwd": self.cwd,
            "timestamp": f"2026-10-01T00:00:{len(self.lines):02d}Z",
            "message": {"role": kind, "content": content}}))

    def tool(self, name, inputs, result, error=False):
        self.n += 1
        use_id = f"toolu_{self.n}"
        self._record("assistant", [{"type": "tool_use", "id": use_id,
                                    "name": name, "input": inputs}])
        item = {"type": "tool_result", "tool_use_id": use_id,
                "content": result}
        if error:
            item["is_error"] = True
        self._record("user", [item])
        return self

    def bash(self, command, result="ok", error=False):
        return self.tool("Bash", {"command": command}, result, error)

    def edit(self, path):
        return self.tool("Edit", {"file_path": path, "old_string": "a",
                                  "new_string": "b"}, "updated")

    def text(self):
        return "\n".join(self.lines) + "\n"


class Tree(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.projects = Path(self._tmp.name) / "projects"
        self.slug = "-work-acme-app"
        self.dir = self.projects / self.slug
        self.dir.mkdir(parents=True)
        self.now = time.time()

    def save(self, session, name=None, age_days=0, where=None):
        path = (where or self.dir) / (name or f"{session.sid}.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(session.text(), encoding="utf-8")
        stamp = self.now - age_days * DAY
        os.utime(path, (stamp, stamp))
        return path

    def harvest(self, **kwargs):
        return kb_harvest.harvest(REPO, self.projects, now=self.now,
                                  **kwargs)


class TestLocate(Tree):
    def test_slug_replaces_every_non_alphanumeric(self):
        self.assertEqual(kb_harvest.slug("/work/acme.app/x_y"),
                         "-work-acme-app-x-y")

    def test_legacy_slug_keeps_dots(self):
        self.assertEqual(kb_harvest.legacy_slug("/work/acme.app"),
                         "-work-acme.app")

    def test_finds_the_project_and_its_worktree_dirs(self):
        worktree = self.projects / f"{self.slug}--claude-worktrees-w1"
        worktree.mkdir()
        (self.projects / f"{self.slug}-other").mkdir()
        self.assertEqual(kb_harvest.project_dirs(REPO, self.projects),
                         [self.dir, worktree])

    def test_falls_back_to_the_legacy_slug(self):
        self.dir.rmdir()
        legacy = self.projects / "-work-acme.app"
        legacy.mkdir()
        self.assertEqual(kb_harvest.project_dirs(REPO, self.projects),
                         [legacy])

    def test_a_long_path_matches_its_truncated_prefix(self):
        long_repo = "/" + "a" * 230
        hashed = self.projects / (kb_harvest.slug(long_repo)[:200] + "-1x2y")
        hashed.mkdir()
        self.assertEqual(kb_harvest.project_dirs(long_repo, self.projects),
                         [hashed])

    def test_no_project_dir_is_one_problem(self):
        self.dir.rmdir()
        result, problems = self.harvest()
        self.assertIsNone(result)
        self.assertEqual(problems, [
            f"harvest: no Claude Code transcripts for {REPO} under"
            f" {self.projects} (looked for {self.slug})"])


def real_git(cwd, *args):
    subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Tester",
         "-c", "commit.gpgsign=false", *args], cwd=cwd, check=True,
        capture_output=True, text=True)


class TestLinkedWorktree(Tree):
    """Issue #710: run from a linked worktree, harvest looked up the
    worktree's own slug and found no transcripts. It anchors at the main
    checkout, the parent of git's common dir."""

    def setUp(self):
        super().setUp()
        base = Path(self._tmp.name).resolve()
        self.main, self.linked = base / "main", base / "linked"
        git_repo.init(self.main, "-b", "main")
        real_git(self.main, "commit", "-q", "--allow-empty", "-m", "seed")
        real_git(self.main, "worktree", "add", "-q", str(self.linked))
        self.main_dir = self.projects / kb_harvest.slug(self.main)

    def test_finds_the_main_checkouts_transcripts(self):
        self.save(Session(cwd=str(self.main)), where=self.main_dir)
        result, problems = kb_harvest.harvest(self.linked, self.projects,
                                              now=self.now)
        self.assertEqual(problems, [])
        self.assertEqual(result["scanned"]["dirs"], [str(self.main_dir)])

    def test_the_problem_names_the_main_checkouts_slug(self):
        result, problems = kb_harvest.harvest(self.linked, self.projects,
                                              now=self.now)
        self.assertIsNone(result)
        self.assertEqual(problems, [
            f"harvest: no Claude Code transcripts for {self.linked} under"
            f" {self.projects} (looked for"
            f" {kb_harvest.slug(self.main)})"])


class TestSelect(Tree):
    def test_default_is_the_newest_top_level_session(self):
        self.save(Session("old"), age_days=2)
        newest = self.save(Session("new"))
        self.save(Session("agent"), name="agent-x.jsonl")
        self.assertEqual(kb_harvest.select(
            [self.dir], days=None, session=None, now=self.now), [newest])

    def test_days_takes_every_transcript_in_the_window(self):
        inside = self.save(Session("a"), age_days=1)
        nested = self.save(Session("b"), name="subagents/agent-b.jsonl",
                           where=self.dir / "a")
        self.save(Session("c"), age_days=9)
        self.assertEqual(kb_harvest.select(
            [self.dir], days=7, session=None, now=self.now),
            sorted([inside, nested]))

    def test_session_by_id(self):
        wanted = self.save(Session("abc"), age_days=3)
        self.save(Session("new"))
        self.assertEqual(kb_harvest.select(
            [self.dir], days=None, session="abc", now=self.now), [wanted])

    def test_unknown_session_is_a_problem(self):
        self.save(Session("new"))
        result, problems = self.harvest(session="nope")
        self.assertEqual(problems, [
            f"harvest: no session transcript 'nope' in {self.dir}"])


class TestMine(Tree):
    def test_failed_edit_passed_is_an_arc(self):
        self.save(Session()
                  .bash("cd /work/acme.app && python3 -m unittest discover"
                        " tests", "Exit code 1\nFAILED (failures=1)",
                        error=True)
                  .edit(f"{REPO}/src/a.py")
                  .edit(f"{REPO}/tests/test_a.py")
                  .bash("python3 -m unittest discover tests -q", "OK"))
        result, problems = self.harvest()
        self.assertEqual(problems, [])
        self.assertEqual(result["arcs"], [{
            "check": "python3 -m unittest",
            "failure": "FAILED (failures=1)",
            "fixed_by": ["src/a.py", "tests/test_a.py"],
            "attempts": 1,
            "session": "s1",
            "failed_at": "2026-10-01T00:00:01Z",
            "passed_at": "2026-10-01T00:00:07Z",
        }])

    def test_a_retry_with_no_edit_between_is_not_an_arc(self):
        self.save(Session()
                  .bash("make check", "Exit code 2\nboom", error=True)
                  .bash("make check", "ok"))
        result, _ = self.harvest()
        self.assertEqual(result["arcs"], [])

    def test_repeated_failures_count_as_attempts(self):
        self.save(Session()
                  .bash("make check", "Exit code 2\nlint: 3 problem(s)",
                        error=True)
                  .edit(f"{REPO}/a.py")
                  .bash("make check", "Exit code 2\nlint: 1 problem(s)",
                        error=True)
                  .edit(f"{REPO}/b.py")
                  .bash("make check", "ok"))
        arc, = self.harvest()[0]["arcs"]
        self.assertEqual((arc["check"], arc["attempts"], arc["fixed_by"],
                          arc["failure"]),
                         ("make check", 2, ["a.py", "b.py"],
                          "lint: 3 problem(s)"))

    def test_list_content_and_env_prefix_are_read(self):
        self.save(Session()
                  .bash("CI=1 npm test", [{"type": "text",
                                           "text": "Error: x broke"}],
                        error=True)
                  .edit("/elsewhere/z.ts")
                  .bash("npm test", [{"type": "text", "text": "pass"}]))
        arc, = self.harvest()[0]["arcs"]
        self.assertEqual((arc["check"], arc["failure"], arc["fixed_by"]),
                         ("npm test", "Error: x broke", ["/elsewhere/z.ts"]))

    def test_recurring_errors_cluster_across_sessions(self):
        for sid in ("s1", "s2"):
            self.save(Session(sid)
                      .bash("pnpm build", "Exit code 1\nmodule @x/core at"
                            f" line {len(sid) * 7} not built", error=True)
                      .bash("ls", "a b"), age_days=1)
        self.save(Session("s3").bash("pnpm lint", "Exit code 1\nonce",
                                     error=True), age_days=1)
        result, _ = self.harvest(days=7)
        self.assertEqual(result["recurring_errors"], [{
            "tool": "Bash", "error": "module @x/core at line N not built",
            "count": 2, "sessions": 2, "example": "pnpm build"}])

    def test_user_rejections_are_not_errors(self):
        for sid in ("s1", "s2"):
            self.save(Session(sid).bash(
                "rm -rf x", "The user doesn't want to proceed with this"
                " tool use.", error=True))
        result, _ = self.harvest(days=7)
        self.assertEqual(result["recurring_errors"], [])

    def test_malformed_lines_are_counted_not_fatal(self):
        path = self.save(Session().bash("ls", "a"))
        path.write_text(path.read_text(encoding="utf-8") + "{not json\n",
                        encoding="utf-8")
        result, problems = self.harvest()
        self.assertEqual(problems, [])
        self.assertEqual(result["scanned"]["skipped_lines"], 1)
        self.assertEqual(result["scanned"]["transcripts"], 1)


class Talk(Session):
    """A transcript with human and agent text turns besides tool calls,
    the shape an interactive session has."""

    def _add(self, kind, content, **extra):
        self.lines.append(json.dumps({
            "type": kind, "sessionId": self.sid, "cwd": self.cwd,
            "timestamp": f"2026-10-01T00:00:{len(self.lines):02d}Z",
            "message": {"role": kind, "content": content}, **extra}))
        return self

    def human(self, text, **extra):
        return self._add("user", text, **extra)

    def say(self, text, **extra):
        return self._add("assistant", [{"type": "text", "text": text}],
                         **extra)

    def at(self, index):
        return f"2026-10-01T00:00:{index:02d}Z"


class TestHumanTurns(Tree):
    """Human corrections and answered questions, mined only from
    top-level interactive transcripts, under their own key."""

    def turns(self, talk, name=None, **kwargs):
        self.save(talk, name=name)
        result, problems = self.harvest(**kwargs)
        self.assertEqual(problems, [])
        return result["human_turns"]

    def test_a_correction_after_an_agent_action(self):
        talk = (Talk().human("fix the build")
                .bash("make check", "ok")
                .human("No, don't run make check here; use run_tests.py."))
        self.assertEqual(self.turns(talk), [{
            "kind": "correction", "signal": "correction-wording",
            "human": "No, don't run make check here; use run_tests.py.",
            "agent": "Bash: make check",
            "session": "s1", "at": talk.at(3)}])

    def test_an_edit_is_named_by_its_path(self):
        talk = (Talk().human("tidy it").edit(f"{REPO}/src/a.py")
                .human("Revert that, it was right."))
        turn, = self.turns(talk)
        self.assertEqual((turn["kind"], turn["agent"]),
                         ("correction", "Edit: src/a.py"))

    def test_excerpts_are_capped(self):
        talk = (Talk().human("go").say("x" * 300)
                .human("Actually " + "y" * 300))
        turn, = self.turns(talk)
        self.assertLessEqual(len(turn["human"]), kb_harvest.EXCERPT)
        self.assertLessEqual(len(turn["agent"]), kb_harvest.EXCERPT)

    def test_an_answer_to_a_text_question(self):
        talk = (Talk().human("rename the flag")
                .say("I found two callers.\n\nShould I keep the old flag?")
                .human([{"type": "text",
                         "text": "Keep it, the CI scripts still pass it."}]))
        self.assertEqual(self.turns(talk), [{
            "kind": "answer", "signal": "after-agent-question",
            "human": "Keep it, the CI scripts still pass it.",
            "agent": "Should I keep the old flag?",
            "session": "s1", "at": talk.at(2)}])

    def test_an_answer_through_the_question_tool(self):
        talk = (Talk().human("ship it")
                .tool("AskUserQuestion",
                      {"questions": [{"question": "Which branch?"}]},
                      "User has answered your questions: release"))
        self.assertEqual(self.turns(talk), [{
            "kind": "answer", "signal": "question-tool",
            "human": "User has answered your questions: release",
            "agent": "AskUserQuestion: Which branch?",
            "session": "s1", "at": talk.at(2)}])

    def test_a_question_tool_error_is_no_answer(self):
        talk = (Talk().human("ship it")
                .tool("AskUserQuestion",
                      {"questions": [{"question": "Which branch?"}]},
                      "Exit code 1\ntool failed", error=True))
        self.assertEqual(self.turns(talk), [])

    def test_approvals_are_not_answers(self):
        for reply in ("go ahead", "OK.", "Yes!", "sounds good"):
            with self.subTest(reply=reply):
                talk = (Talk().human("push it").say("Shall I push now?")
                        .human(reply))
                self.assertEqual(self.turns(talk), [])

    def test_a_plain_instruction_is_not_listed(self):
        talk = (Talk().human("add the test").say("Added the test.")
                .human("Now update the README too."))
        self.assertEqual(self.turns(talk), [])

    def test_meta_and_tagged_turns_are_skipped(self):
        talk = (Talk().human("start").say("Done.")
                .human("No, that is injected.", isMeta=True)
                .human("<command-name>/clear</command-name> no"))
        self.assertEqual(self.turns(talk), [])

    def test_two_human_turns_in_a_row_yield_at_most_one(self):
        talk = (Talk().human("start").say("Use the new parser?")
                .human("No, keep the old one.")
                .human("Wait, actually stop."))
        self.assertEqual(len(self.turns(talk)), 1)

    def test_an_autonomous_transcript_yields_none(self):
        talk = (Talk().human("Work the queue. Never ask.")
                .bash("make check", "Exit code 1\nboom", error=True)
                .edit(f"{REPO}/a.py").bash("make check", "ok"))
        self.assertEqual(self.turns(talk), [])

    def test_a_subagent_file_yields_none(self):
        talk = (Talk().human("start").bash("ls", "a")
                .human("No, do not list."))
        self.assertEqual(self.turns(talk, name="agent-x.jsonl", days=7), [])

    def test_sidechain_records_yield_none(self):
        talk = (Talk().human("start", isSidechain=True)
                .say("Should I stop?", isSidechain=True)
                .human("Stop, wrong file.", isSidechain=True))
        self.assertEqual(self.turns(talk), [])

    def test_existing_kinds_are_unchanged_and_the_key_is_empty(self):
        self.save(Session()
                  .bash("make check", "Exit code 2\nboom", error=True)
                  .edit(f"{REPO}/a.py")
                  .bash("make check", "ok"))
        result, problems = self.harvest()
        self.assertEqual(problems, [])
        self.assertEqual(sorted(result), ["arcs", "human_turns",
                                          "recurring_errors", "scanned"])
        self.assertEqual(result["human_turns"], [])
        self.assertEqual(result["scanned"], {
            "transcripts": 1, "skipped_lines": 0,
            "dirs": [str(self.dir)]})
        self.assertEqual(result["recurring_errors"], [])
        self.assertEqual([a["check"] for a in result["arcs"]],
                         ["make check"])

    def test_main_prints_the_key(self):
        self.save(Talk().human("go").say("Keep it?").human("Drop it."))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = kb.main(["harvest", REPO, "--projects-dir",
                            str(self.projects)])
        self.assertEqual(code, 0)
        self.assertEqual([t["kind"] for t in json.loads(
            out.getvalue())["human_turns"]], ["answer"])


def memory_file(name, description="A lesson.", kind="project",
                nested=False, extra=""):
    """A fixture memory entry: frontmatter with name, description and a
    type, top-level or nested under metadata, then a body."""
    type_line = f"metadata:\n  type: {kind}" if nested else f"type: {kind}"
    return (f"---\nname: {name}\ndescription: {description}\n{type_line}\n"
            f"{extra}---\n\nBody written for the test.\n")


PAGES = ("cross-pr-merge-hazards", "manifest-regen", "pr-body-contract")


class TestMemory(Tree):
    """Auto-memory entries as candidates, read only on request, paired
    with pages by file name, user scope never shown."""

    def setUp(self):
        super().setUp()
        self.repo = Path(self._tmp.name) / "repo"
        self.memory = self.dir / "memory"
        self.memory.mkdir()
        for slug in PAGES:
            (self.repo / "docs" / "kb").mkdir(parents=True, exist_ok=True)
            (self.repo / "docs" / "kb" / f"{slug}.md").write_text(
                f"---\nsummary: {slug}\n---\n", encoding="utf-8")
        self.pages = {slug: f"docs/kb/{slug}.md" for slug in PAGES}

    def remember(self, stem, text):
        path = self.memory / f"{stem}.md"
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text, encoding="utf-8")
        return path

    def seed(self):
        self.remember("cross-pr-hazard-pairwise-merge-test", memory_file(
            "Cross-PR hazard", "Two green PRs can go red together."))
        self.remember("manifest-regen-stray-patch-files", memory_file(
            "Manifest regen", "Delete stray patch files first.",
            kind="feedback", nested=True))
        self.remember("pr-body-no-work-order-waiver", memory_file(
            "PR body waiver", "A PR body needs its waiver line.",
            kind="reference"))
        self.remember("gh-pr-edit-broken-use-rest", memory_file(
            "gh pr edit is broken", "Use the REST API to edit a PR body."))

    def harvest_memory(self, **kwargs):
        with mock.patch.object(kb_harvest, "main_checkout",
                               lambda root: Path(REPO)):
            return kb_harvest.harvest(self.repo, self.projects,
                                      now=self.now, memory=True, **kwargs)

    def test_memory_type_reads_one_scope(self):
        cases = {
            memory_file("a"): "project",
            memory_file("a", kind="feedback", nested=True): "feedback",
            memory_file("a", kind="reference"): "reference",
            memory_file("a", kind="user"): "user",
            "no frontmatter at all\n": None,
            "---\nname: a\ndescription: b\n---\n": None,
            memory_file("a", extra="metadata:\n  type: user\n"): None,
            memory_file("a", kind="secret"): None,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(kb_harvest.memory_type(text), expected)

    def test_pair_by_shared_file_name_tokens(self):
        self.assertEqual(
            kb_harvest.pair("cross-pr-hazard-pairwise-merge-test", PAGES),
            ("cross-pr-merge-hazards", ["cross", "pr", "merge", "hazard"]))
        self.assertEqual(
            kb_harvest.pair("manifest-regen-stray-patch-files", PAGES),
            ("manifest-regen", ["manifest", "regen"]))
        self.assertEqual(
            kb_harvest.pair("pr-body-no-work-order-waiver", PAGES),
            ("pr-body-contract", ["pr", "body"]))
        self.assertEqual(
            kb_harvest.pair("gh-pr-edit-broken-use-rest", PAGES), (None, []))

    def test_a_tie_goes_to_the_first_slug_in_sorted_order(self):
        self.assertEqual(
            kb_harvest.pair("alpha-beta", ["alpha-beta-y", "alpha-beta-x"]),
            ("alpha-beta-x", ["alpha", "beta"]))

    def test_candidates_pair_three_and_leave_one_unpaired(self):
        self.seed()
        memory = kb_harvest.memory_candidates(self.memory, self.pages)
        self.assertEqual(memory["dir"], str(self.memory))
        self.assertEqual((memory["listed"], memory["user_scoped"],
                          memory["skipped"]), (4, 0, 0))
        self.assertEqual(
            [(c["file"], c["page"], c["shared"], c["type"])
             for c in memory["candidates"]],
            [("cross-pr-hazard-pairwise-merge-test.md",
              "docs/kb/cross-pr-merge-hazards.md",
              ["cross", "pr", "merge", "hazard"], "project"),
             ("gh-pr-edit-broken-use-rest.md", None, [], "project"),
             ("manifest-regen-stray-patch-files.md",
              "docs/kb/manifest-regen.md", ["manifest", "regen"],
              "feedback"),
             ("pr-body-no-work-order-waiver.md",
              "docs/kb/pr-body-contract.md", ["pr", "body"], "reference")])
        first = memory["candidates"][0]
        self.assertEqual((first["name"], first["description"]),
                         ("Cross-PR hazard",
                          "Two green PRs can go red together."))

    def test_user_scope_and_the_index_never_reach_the_output(self):
        self.seed()
        self.remember("owner-private-habit", memory_file(
            "Private", "SENTINEL-7Q personal detail", kind="user"))
        self.remember("MEMORY", "- INDEX-SENTINEL pointer line\n")
        result, problems = self.harvest_memory(kb_dir="docs/kb")
        self.assertEqual(problems, [])
        printed = json.dumps(result)
        for secret in ("owner-private-habit", "SENTINEL-7Q", "Private",
                       "MEMORY.md", "INDEX-SENTINEL"):
            self.assertNotIn(secret, printed)
        self.assertEqual(result["memory"]["user_scoped"], 1)
        self.assertEqual(result["memory"]["listed"], 4)

    def test_every_skip_reason_is_counted(self):
        self.seed()
        self.remember("no-block", "Just prose, no frontmatter.\n")
        self.remember("no-type", "---\nname: x\ndescription: y\n---\n")
        self.remember("two-types", memory_file(
            "x", extra="metadata:\n  type: feedback\n"))
        self.remember("unknown-type", memory_file("x", kind="secret"))
        self.remember("undecodable", b"---\ntype: project\n\xff\xfe\n---\n")
        self.remember("someone", memory_file("x", kind="user"))
        examined = len([p for p in self.memory.glob("*.md")
                        if p.name != "MEMORY.md"])
        memory = kb_harvest.memory_candidates(self.memory, self.pages)
        self.assertEqual((memory["listed"], memory["user_scoped"],
                          memory["skipped"]), (4, 1, 5))
        self.assertEqual(memory["listed"] + memory["user_scoped"]
                         + memory["skipped"], examined)

    def test_descriptions_are_capped(self):
        self.remember("long-lesson", memory_file("Long", "z" * 400))
        candidate, = kb_harvest.memory_candidates(
            self.memory, self.pages)["candidates"]
        self.assertLessEqual(len(candidate["description"]),
                             kb_harvest.EXCERPT)

    def test_harvest_pairs_with_the_kb_dir_it_is_given(self):
        self.seed()
        result, problems = self.harvest_memory(kb_dir="docs/kb")
        self.assertEqual(problems, [])
        self.assertEqual(
            sorted(c["page"] or "" for c in result["memory"]["candidates"]),
            ["", "docs/kb/cross-pr-merge-hazards.md",
             "docs/kb/manifest-regen.md", "docs/kb/pr-body-contract.md"])

    def test_no_kb_dir_leaves_every_candidate_unpaired(self):
        self.seed()
        result, problems = self.harvest_memory()
        self.assertEqual(problems, [])
        self.assertEqual({c["page"] for c in result["memory"]["candidates"]},
                         {None})

    def test_no_memory_directory_is_one_problem(self):
        self.memory.rmdir()
        result, problems = self.harvest_memory(kb_dir="docs/kb")
        self.assertIsNone(result)
        self.assertEqual(problems, [
            f"harvest: no memory directory at {self.memory}"])

    def test_without_the_flag_there_is_no_memory_key(self):
        self.seed()
        self.save(Session().bash("ls", "a"))
        result, _ = self.harvest()
        self.assertNotIn("memory", result)

    def test_harvest_writes_nothing(self):
        self.seed()
        self.remember("someone", memory_file("x", kind="user"))
        self.save(Talk().human("go").say("Keep it?").human("Drop it."))
        tree = Path(self._tmp.name)

        def snapshot():
            return {path: path.read_bytes() for path in tree.rglob("*")
                    if path.is_file()}

        before = snapshot()
        result, problems = self.harvest_memory(kb_dir="docs/kb")
        self.assertEqual(problems, [])
        self.assertEqual(snapshot(), before)

    def run_main(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch.object(
                kb_harvest, "main_checkout", lambda root: Path(REPO)):
            code = kb.main(argv)
        return code, out.getvalue()

    def test_kb_main_passes_the_page_directory(self):
        self.seed()
        code, out = self.run_main(["harvest", str(self.repo), "--memory",
                                   "--projects-dir", str(self.projects)])
        self.assertEqual(code, 0)
        self.assertEqual(
            sum(c["page"] is not None
                for c in json.loads(out)["memory"]["candidates"]), 3)

    def test_main_with_no_memory_directory_prints_no_json(self):
        self.memory.rmdir()
        code, out = self.run_main(["harvest", str(self.repo), "--memory",
                                   "--projects-dir", str(self.projects)])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            f"harvest: no memory directory at {self.memory}",
            "harvest: 1 problem(s)"])

    def test_usage_names_the_flag(self):
        for argv in (["harvest", "--help"], ["harvest", "--bogus"]):
            with self.subTest(argv=argv):
                code, out = self.run_main(argv)
                self.assertEqual(code, 2)
                self.assertIn("[--memory]", out)


class TestMain(Tree):
    def run_main(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = kb.main(argv)
        return code, out.getvalue()

    def test_harvest_prints_json(self):
        self.save(Session().bash("ls", "a"))
        code, out = self.run_main(["harvest", REPO, "--projects-dir",
                                   str(self.projects)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["arcs"], [])

    def test_bad_days_is_a_problem(self):
        code, out = self.run_main(["harvest", REPO, "--days", "zero",
                                   "--projects-dir", str(self.projects)])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            "harvest: --days must be a positive whole number, got 'zero'",
            "harvest: 1 problem(s)"])


if __name__ == "__main__":
    unittest.main()
