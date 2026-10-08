"""launch_demo.py — the launch-demo skill's shipped tool (PRD-0009):
the config grammar, the tool probe, and the CLI legs, asserted through
the public functions over a tempfile root and injected fakes.

The fake runner factory below takes cli.runner's port — `(binary,
timeout=None)` returning `run(args, input=None)` — so every external
CLI (say, ffprobe, vhs, ffmpeg, node) is scripted here and CI runs no
real recorder. Neither `__call__` is `(self, args)`, so
tests/test_fake_gh.py's one-gh-fake rule does not read them as gh fakes.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402

import launch_demo  # noqa: E402

LABEL = "launch-demo: docs/launch-demo.json"
VALID = {"when": "ship", "recorder": "terminal", "against": "bash",
         "publish": "docs/launches"}
ALL_TOOLS = {"ffmpeg": "/usr/bin/ffmpeg", "ffprobe": "/usr/bin/ffprobe",
             "vhs": "/usr/bin/vhs", "node": "/usr/bin/node",
             "say": "/usr/bin/say", "espeak-ng": "/usr/bin/espeak-ng"}


class FakeRun:
    """One binary's scripted run(args, input=None): each call pops the
    next answer — a str (stdout), an exception (raised), or a callable
    `(args, input) -> stdout` that may write files or raise."""

    def __init__(self, factory, binary, timeout):
        self.factory, self.binary, self.timeout = factory, binary, timeout

    def __call__(self, args, input=None):
        self.factory.calls.append((self.binary, self.timeout, list(args),
                                   input))
        answers = self.factory.script.get(self.binary, [])
        answer = answers.pop(0) if answers else ""
        if isinstance(answer, BaseException):
            raise answer
        if callable(answer):
            answer = answer(list(args), input)
        return subprocess.CompletedProcess([self.binary, *args], 0,
                                           stdout=answer, stderr="")


class FakeRunners:
    """cli.runner's port: `(binary, timeout=None)` -> FakeRun, recording
    every call as (binary, timeout, args, input) in `calls`."""

    def __init__(self, script=None):
        self.script = {k: list(v) for k, v in (script or {}).items()}
        self.calls = []

    def __call__(self, binary, timeout=None):
        return FakeRun(self, binary, timeout)

    def binaries(self):
        return [call[0] for call in self.calls]


class FakeWhich:
    """shutil.which's port over a name -> path-or-None table, recording
    what it was asked."""

    def __init__(self, table):
        self.table, self.asked = dict(table), []

    def __call__(self, name):
        self.asked.append(name)
        return self.table.get(name)


def write_config(root, payload):
    (root / "docs").mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload)
    (root / "docs" / "launch-demo.json").write_text(text, encoding="utf-8")


class TestLoad(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def load(self, payload, platform="darwin"):
        write_config(self.root, payload)
        return launch_demo.load(self.root, platform=platform)

    def test_no_file_is_the_missing_problem(self):
        self.assertEqual(launch_demo.load(self.root, platform="darwin"),
                         (None, ["launch-demo: missing docs/launch-demo.json"]))

    def test_bytes_that_are_not_json(self):
        config, problems = self.load("{not json")
        self.assertIsNone(config)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith(
            f"{LABEL} is not valid JSON:"), problems)

    def test_a_top_level_array(self):
        self.assertEqual(self.load([]),
                         (None, [f"{LABEL} is not a JSON object"]))

    def test_an_empty_object_names_every_required_field_in_order(self):
        self.assertEqual(self.load({}), (None, [
            f"{LABEL} has no when",
            f"{LABEL} has no recorder",
            f"{LABEL} has no against",
            f"{LABEL} has no publish"]))

    def test_when_grammar(self):
        self.assertEqual(self.load({**VALID, "when": "always"}),
                         (None, [f'{LABEL} when must be "ship" or "on-demand"']))

    def test_recorder_grammar(self):
        self.assertEqual(
            self.load({**VALID, "recorder": "gif"}),
            (None, [f'{LABEL} recorder must be "terminal" or "browser"']))

    def test_against_must_be_a_non_empty_string(self):
        for bad in ("", 7):
            with self.subTest(against=bad):
                self.assertEqual(
                    self.load({**VALID, "against": bad}),
                    (None, [f"{LABEL} against must be a non-empty string"]))

    def test_the_browser_recorder_needs_a_url(self):
        self.assertEqual(
            self.load({**VALID, "recorder": "browser", "against": "bash"}),
            (None, [f"{LABEL} against must be an http(s) URL for the"
                    " browser recorder"]))

    def test_voice_must_name_out_when_present(self):
        for bad in ("say -o out.wav", ""):
            with self.subTest(voice=bad):
                self.assertEqual(
                    self.load({**VALID, "voice": bad}),
                    (None, [f"{LABEL} voice must be a non-empty string"
                            " naming {out}"]))

    def test_publish_must_be_a_plain_relative_path(self):
        for bad in ("/tmp/x", "../x", ""):
            with self.subTest(publish=bad):
                self.assertEqual(
                    self.load({**VALID, "publish": bad}),
                    (None, [f"{LABEL} publish must be a plain relative path"
                            " inside the repo"]))

    def test_a_valid_file_gets_the_macos_voice_default(self):
        config, problems = self.load(VALID, platform="darwin")
        self.assertEqual(problems, [])
        self.assertEqual(config, {**VALID,
                                  "voice": "say --data-format=LEI16@22050"
                                           " -o {out}"})

    def test_a_valid_file_gets_the_espeak_default_elsewhere(self):
        config, problems = self.load(VALID, platform="linux")
        self.assertEqual(problems, [])
        self.assertEqual(config["voice"], "espeak-ng -w {out}")

    def test_a_set_voice_is_kept(self):
        config, problems = self.load({**VALID, "voice": "piper -o {out}"})
        self.assertEqual(problems, [])
        self.assertEqual(config["voice"], "piper -o {out}")


TERMINAL = {**VALID, "voice": "say -o {out}"}
BROWSER = {**VALID, "recorder": "browser", "against": "http://127.0.0.1:8765",
           "voice": "say -o {out}"}
NODE_PROBE = ["-e", "require.resolve('playwright')"]


class TestProbe(unittest.TestCase):
    def test_everything_present_is_nothing_missing(self):
        runners = FakeRunners()
        self.assertEqual(launch_demo.probe(TERMINAL, FakeWhich(ALL_TOOLS),
                                           runners), ([], []))

    def test_ffmpeg_and_ffprobe_absent_are_two_entries(self):
        which = FakeWhich({**ALL_TOOLS, "ffmpeg": None, "ffprobe": None})
        missing, problems = launch_demo.probe(TERMINAL, which, FakeRunners())
        self.assertEqual(problems, [])
        self.assertEqual([entry[0] for entry in missing], ["ffmpeg", "ffprobe"])
        for entry in missing:
            self.assertEqual(len(entry), 3)
            self.assertTrue(all(isinstance(part, str) and part
                                for part in entry), entry)

    def test_a_terminal_config_probes_vhs_and_never_node(self):
        which = FakeWhich({**ALL_TOOLS, "vhs": None})
        runners = FakeRunners()
        missing, _ = launch_demo.probe(TERMINAL, which, runners)
        self.assertEqual([entry[0] for entry in missing], ["vhs"])
        self.assertIn("vhs", which.asked)
        self.assertNotIn("node", which.asked)
        self.assertEqual(runners.calls, [])

    def test_a_browser_config_resolves_playwright_through_node(self):
        runners = FakeRunners({"node": [""]})
        missing, _ = launch_demo.probe(BROWSER, FakeWhich(ALL_TOOLS), runners)
        self.assertEqual(missing, [])
        self.assertEqual(runners.calls,
                         [("node", launch_demo.PROBE_TIMEOUT, NODE_PROBE,
                           None)])

    def test_an_unresolvable_playwright_is_missing(self):
        err = subprocess.CalledProcessError(1, ["node"],
                                            stderr="Cannot find module\n")
        runners = FakeRunners({"node": [err]})
        missing, problems = launch_demo.probe(BROWSER, FakeWhich(ALL_TOOLS),
                                              runners)
        self.assertEqual(problems, [])
        self.assertEqual([entry[0] for entry in missing], ["playwright"])

    def test_node_absent_is_missing_and_never_run(self):
        runners = FakeRunners()
        which = FakeWhich({**ALL_TOOLS, "node": None})
        missing, _ = launch_demo.probe(BROWSER, which, runners)
        self.assertEqual([entry[0] for entry in missing], ["node"])
        self.assertEqual(runners.calls, [])

    def test_the_voice_commands_first_token_is_probed(self):
        which = FakeWhich({**ALL_TOOLS, "say": None})
        missing, _ = launch_demo.probe(TERMINAL, which, FakeRunners())
        self.assertEqual([entry[0] for entry in missing], ["say"])
        which = FakeWhich({**ALL_TOOLS, "piper": None})
        config = {**TERMINAL, "voice": "piper --model x -o {out}"}
        missing, _ = launch_demo.probe(config, which, FakeRunners())
        self.assertEqual([entry[0] for entry in missing], ["piper"])


class CliMixin:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.which = FakeWhich(ALL_TOOLS)
        self.runners = FakeRunners()

    def run_cli(self, argv):
        return cli_contract.capture(launch_demo.main, argv, root=self.root,
                                    which=self.which, runner=self.runners,
                                    platform="darwin")


class TestConfigLeg(CliMixin, cli_contract.CliContract,
                    cli_contract.ReportContract, unittest.TestCase):
    usage_fragment = "python3 launch_demo.py config | probe | render"
    summary_line = "launch-demo: 0 problem(s)"

    def clean_cli(self):
        write_config(self.root, VALID)
        return self.run_cli(["config"])

    def test_a_valid_config_prints_the_summary_alone(self):
        code, out = self.clean_cli()
        self.assertEqual((code, out), (0, "launch-demo: 0 problem(s)\n"))

    def test_an_invalid_config_prints_each_problem_and_the_count(self):
        write_config(self.root, {"when": "always", "recorder": "gif"})
        code, out = self.run_cli(["config"])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            f'{LABEL} when must be "ship" or "on-demand"',
            f'{LABEL} recorder must be "terminal" or "browser"',
            f"{LABEL} has no against",
            f"{LABEL} has no publish",
            "launch-demo: 4 problem(s)"])


class TestProbeLeg(CliMixin, unittest.TestCase):
    def test_ready_when_nothing_is_missing(self):
        write_config(self.root, VALID)
        code, out = self.run_cli(["probe"])
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), ["READY",
                                            "launch-demo: 0 problem(s)"])

    def test_copy_only_names_each_missing_tool(self):
        write_config(self.root, VALID)
        self.which = FakeWhich({**ALL_TOOLS, "ffmpeg": None})
        missing, _ = launch_demo.probe(
            {**VALID, "voice": "say -o {out}"}, self.which, self.runners)
        (_, purpose, hint), = missing
        code, out = self.run_cli(["probe"])
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), [
            f"launch-demo: missing ffmpeg — {purpose}; install: {hint}",
            "COPY-ONLY",
            "launch-demo: 0 problem(s)"])

    def test_a_missing_config_is_a_problem_exit(self):
        code, out = self.run_cli(["probe"])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            "launch-demo: missing docs/launch-demo.json",
            "launch-demo: 1 problem(s)"])


COPY = """## What it is

The board is one picture of every run. It needs no commands
to read.

## What it does

It places each run on its stage. It counts the boxes that are
checked. It marks the runs that cannot be oriented.

## How it helps

You see where everything is at a glance. Nothing is guessed.
"""
STORYBOARD = {
    "title": "Pipeline board",
    "tagline": "Every run, one picture",
    "intro": "The board is one picture of every run.",
    "steps": [{"say": "It places each run on its stage.",
               "do": ["python3 board.py"]},
              {"say": "It counts the boxes that are checked.",
               "do": []}],
    "outro": "You see where everything is at a glance.",
}
SB = "launch-demo: storyboard"


def storyboard(**changes):
    board = {k: v for k, v in STORYBOARD.items()}
    board["steps"] = [dict(step) for step in STORYBOARD["steps"]]
    board.update(changes)
    return board


class TestCheckStoryboard(unittest.TestCase):
    def check(self, board, recorder="terminal"):
        return launch_demo.check_storyboard(board, COPY, recorder)

    def test_a_conformant_terminal_storyboard(self):
        self.assertEqual(self.check(STORYBOARD), [])

    def test_a_conformant_browser_storyboard_takes_string_dos(self):
        board = storyboard()
        board["steps"][0]["do"] = "await page.click('#count');"
        board["steps"][1]["do"] = ""
        self.assertEqual(self.check(board, "browser"), [])

    def test_each_missing_field_is_named(self):
        for field in ("title", "tagline", "intro", "steps", "outro"):
            with self.subTest(field=field):
                board = storyboard()
                del board[field]
                self.assertEqual(self.check(board),
                                 [f"{SB} has no {field}"])

    def test_several_missing_fields_come_in_field_order(self):
        board = storyboard()
        del board["outro"], board["title"], board["steps"]
        self.assertEqual(self.check(board), [f"{SB} has no title",
                                             f"{SB} has no steps",
                                             f"{SB} has no outro"])

    def test_steps_must_be_a_non_empty_list(self):
        for bad in ([], "x"):
            with self.subTest(steps=bad):
                self.assertEqual(self.check(storyboard(steps=bad)),
                                 [f"{SB} steps must be a non-empty list"])

    def test_a_step_without_say(self):
        board = storyboard()
        del board["steps"][0]["say"]
        self.assertEqual(self.check(board), [f"{SB} step 1 has no say"])

    def test_a_terminal_do_must_be_a_list(self):
        board = storyboard()
        board["steps"][0]["do"] = "python3 board.py"
        self.assertEqual(self.check(board),
                         [f"{SB} step 1 do must be a list of commands"])

    def test_a_browser_do_must_be_a_string(self):
        board = storyboard()
        del board["steps"][1]["do"]
        self.assertEqual(self.check(board, "browser"),
                         [f"{SB} step 1 do must be a string"])

    def test_a_step_without_do_is_conformant_for_both(self):
        board = storyboard()
        for step in board["steps"]:
            del step["do"]
        self.assertEqual(self.check(board, "terminal"), [])
        self.assertEqual(self.check(board, "browser"), [])

    def test_an_intro_not_in_the_copy(self):
        board = storyboard(intro="The board is one picture of every repo.")
        self.assertEqual(self.check(board),
                         [f"{SB} intro is not a sentence of launch.md"])

    def test_a_narration_line_not_in_the_copy(self):
        board = storyboard()
        board["steps"][1]["say"] = "It counts the boxes that are ticked."
        self.assertEqual(
            self.check(board),
            [f"{SB} step 2 narration is not a sentence of launch.md"])

    def test_an_outro_not_in_the_copy(self):
        board = storyboard(outro="Something is guessed.")
        self.assertEqual(self.check(board),
                         [f"{SB} outro is not a sentence of launch.md"])

    def test_the_comparison_is_whitespace_normalised(self):
        # "It needs no commands\nto read." wraps in the copy.
        board = storyboard(intro="It needs no commands to read.")
        self.assertEqual(self.check(board), [])
        board = storyboard(intro="It  needs no\ncommands to read.")
        self.assertEqual(self.check(board), [])

    def test_a_non_object_storyboard(self):
        for bad in ([], "x", None):
            with self.subTest(storyboard=bad):
                self.assertEqual(self.check(bad),
                                 [f"{SB} is not a JSON object"])


if __name__ == "__main__":
    unittest.main()
