"""factory_init.missing_make_targets reads only real `make <target>`
calls — a `make` command word inside a workflow's `run:` commands — and
never prose. The monorepo dry run for #702 found the false positive: a
consumer workflow's prompt text "so make the best backlog candidates
ready" reported a phantom `make the` target on every update.
"""
import re
import tempfile
import unittest
from pathlib import Path

import factory_init

REPO_ROOT = Path(__file__).resolve().parent.parent
PROSE = "so make the best backlog candidates ready"


def calls(text):
    return factory_init.make_calls(text)


class TestMakeCalls(unittest.TestCase):
    def test_inline_and_chained_run_commands_are_calls(self):
        self.assertEqual(calls(
            "jobs:\n  x:\n    steps:\n"
            "      - run: make check\n"
            "      - name: lint\n"
            "        run: foo && make lint\n"
            "      - run: a || make x-1; make y | tee out\n"),
            {"check", "lint", "x-1", "y"})

    def test_block_scalar_run_commands_are_calls(self):
        self.assertEqual(calls(
            "    steps:\n"
            "      - name: gate\n"
            "        run: |\n"
            "          set -e\n"
            "          make pr-event PR=\"$PR\"\n"
            "\n"
            "          make check > findings.txt 2>&1\n"
            "        env:\n"
            "          NOTE: make phantom\n"),
            {"pr-event", "check"})

    def test_prose_in_a_description_or_comment_is_not_a_call(self):
        self.assertEqual(calls(
            "name: triage\n"
            f"description: {PROSE}\n"
            "jobs:\n  x:\n    steps:\n"
            f"      # {PROSE}\n"
            f"      - name: {PROSE}\n"
            "        with:\n"
            "          prompt: |\n"
            f"            You are the triager, {PROSE}.\n"
            f"        run: echo hi  # {PROSE}\n"), set())

    def test_make_inside_a_run_line_but_not_as_a_command_is_not_a_call(
            self):
        self.assertEqual(calls(
            "      - run: echo \"remake the cake\"; git commit -m make\n"),
            set())

    def test_the_real_workflows_keep_every_call(self):
        # the old reader (every `make <word>` outside comment lines) on
        # this repo's own workflows, which say nothing in prose about make
        # outside comments: the new reader must find exactly those calls
        old = re.compile(r"\bmake\s+([a-z][a-z0-9-]*)")
        for path in sorted((REPO_ROOT / ".github/workflows").glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            body = "\n".join(line for line in text.splitlines()
                             if not line.lstrip().startswith("#"))
            with self.subTest(workflow=path.name):
                self.assertEqual(calls(text), set(old.findall(body)))


class TestMissingMakeTargets(unittest.TestCase):
    def target(self, tmp, workflow):
        root = Path(tmp)
        (root / ".github/workflows").mkdir(parents=True)
        (root / ".github/workflows/w.yml").write_text(workflow)
        (root / "Makefile").write_text("check:\n\ttrue\n")
        return root

    def test_the_monorepo_prose_reports_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.target(tmp, (
                "jobs:\n  x:\n    steps:\n      - uses: a/b@v1\n"
                "        with:\n          prompt: |\n"
                f"            No open issue is ready, {PROSE}.\n"
                "      - run: make check\n"))
            self.assertEqual(factory_init.missing_make_targets(root), [])

    def test_a_real_missing_call_is_still_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.target(tmp, (
                "jobs:\n  x:\n    steps:\n"
                "      - run: foo && make lint\n"))
            self.assertEqual(factory_init.missing_make_targets(root), [
                "factory-init: workflows call `make lint` but the Makefile"
                " has no lint target (add it, or re-stamp the Makefile)"])


if __name__ == "__main__":
    unittest.main()
