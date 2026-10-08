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


PLAN_BOARD = {"title": "T", "tagline": "G", "intro": "A.",
              "steps": [{"say": "B.", "do": ["python3 board.py"]}],
              "outro": "C."}


class TestPlan(unittest.TestCase):
    def test_the_timeline_of_a_one_step_storyboard(self):
        plan = launch_demo.plan(PLAN_BOARD, [2.0, 3.0, 1.0])
        self.assertEqual(plan["title"], "T")
        self.assertEqual(plan["tagline"], "G")
        self.assertEqual(plan["scenes"], [
            {"kind": "title", "say": "A.", "do": [], "hold": 3.0,
             "offset": 0.0},
            {"kind": "step", "say": "B.", "do": ["python3 board.py"],
             "hold": 3.5, "offset": 3.0},
            {"kind": "outro", "say": "C.", "do": [], "hold": 1.5,
             "offset": 7.3}])
        self.assertEqual(plan["planned"], 8.8)

    def test_a_long_intro_holds_the_title_card_past_its_floor(self):
        plan = launch_demo.plan(PLAN_BOARD, [4.0, 3.0, 1.0])
        self.assertEqual(plan["scenes"][0]["hold"], 4.5)

    def test_a_string_or_empty_do_adds_no_typing_time(self):
        for do in ("await page.click('#count');", []):
            with self.subTest(do=do):
                board = {**PLAN_BOARD, "steps": [{"say": "B.", "do": do}]}
                plan = launch_demo.plan(board, [2.0, 3.0, 1.0])
                self.assertEqual(plan["scenes"][2]["offset"], 6.5)
                self.assertEqual(plan["scenes"][1]["do"], do)

    def test_a_step_without_do_plans_an_empty_one(self):
        board = {**PLAN_BOARD, "steps": [{"say": "B."}]}
        plan = launch_demo.plan(board, [2.0, 3.0, 1.0])
        self.assertEqual(plan["scenes"][1]["do"], [])

    def test_a_seconds_count_that_does_not_fit_is_a_caller_slip(self):
        with self.assertRaises(ValueError):
            launch_demo.plan(PLAN_BOARD, [2.0, 3.0])


def duration_argv(path):
    return ["-v", "error", "-show_entries", "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", str(path)]


def writes(path_index=-1, text="x"):
    """A fake answer that writes the file named by one of its args."""
    def answer(args, input):
        Path(args[path_index]).write_text(text, encoding="utf-8")
        return ""
    return answer


class WorkdirMixin:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name) / "work"
        self.work.mkdir()


class TestNarrate(WorkdirMixin, unittest.TestCase):
    LINES = ["A.", "B."]
    VOICE = "say -o {out}"

    def test_each_line_is_spoken_to_its_own_wav_and_measured(self):
        runners = FakeRunners({"say": [writes(), writes()],
                               "ffprobe": ["2.0\n", "3.0\n"]})
        clips, problems = launch_demo.narrate(self.LINES, self.VOICE,
                                              self.work, runners)
        one, two = self.work / "line-1.wav", self.work / "line-2.wav"
        self.assertEqual(problems, [])
        self.assertEqual(clips, [(one, 2.0), (two, 3.0)])
        self.assertEqual(runners.calls, [
            ("say", launch_demo.VOICE_TIMEOUT, ["-o", str(one)], "A.\n"),
            ("ffprobe", launch_demo.PROBE_TIMEOUT, duration_argv(one), None),
            ("say", launch_demo.VOICE_TIMEOUT, ["-o", str(two)], "B.\n"),
            ("ffprobe", launch_demo.PROBE_TIMEOUT, duration_argv(two), None),
        ])

    def test_a_failing_voice_stops_at_its_line(self):
        err = subprocess.CalledProcessError(1, ["say"],
                                            stderr="Voice not found\n")
        runners = FakeRunners({"say": [err, writes()]})
        self.assertEqual(
            launch_demo.narrate(self.LINES, self.VOICE, self.work, runners),
            (None, ["launch-demo: voice failed on line 1: Voice not found"]))
        self.assertEqual(runners.binaries(), ["say"])

    def test_a_hung_voice_is_the_same_shape(self):
        err = subprocess.TimeoutExpired(["say"], 60)
        runners = FakeRunners({"say": [err]})
        import cli
        self.assertEqual(
            launch_demo.narrate(self.LINES, self.VOICE, self.work, runners),
            (None, [f"launch-demo: voice failed on line 1: {cli.detail(err)}"]))

    def test_a_voice_that_writes_nothing(self):
        runners = FakeRunners({"say": [""]})
        self.assertEqual(
            launch_demo.narrate(self.LINES, self.VOICE, self.work, runners),
            (None, ["launch-demo: voice wrote no file for line 1"]))

    def test_an_unmeasurable_wav_is_a_voice_failure(self):
        err = subprocess.CalledProcessError(
            1, ["ffprobe"], stderr="header\nInvalid data found\n")
        runners = FakeRunners({"say": [writes(), writes()],
                               "ffprobe": ["2.0\n", err]})
        self.assertEqual(
            launch_demo.narrate(self.LINES, self.VOICE, self.work, runners),
            (None, ["launch-demo: voice failed on line 2: Invalid data"
                    " found"]))

    def test_the_voice_template_names_the_binary(self):
        runners = FakeRunners({"espeak-ng": [writes()], "ffprobe": ["1.0\n"]})
        clips, problems = launch_demo.narrate(["A."], "espeak-ng -w {out}",
                                              self.work, runners)
        self.assertEqual(problems, [])
        self.assertEqual(runners.calls[0][:3],
                         ("espeak-ng", launch_demo.VOICE_TIMEOUT,
                          ["-w", str(self.work / "line-1.wav")]))


class TestRecordTerminal(WorkdirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.plan = launch_demo.plan(PLAN_BOARD, [2.0, 3.0, 1.0])
        self.raw = self.work / "raw.mp4"
        self.tape = self.work / "demo.tape"

    def record(self, runners):
        return launch_demo.record_terminal(self.plan, self.work, "bash",
                                           runners)

    def test_the_tape_the_vhs_run_and_the_computed_offsets(self):
        runners = FakeRunners({"vhs": [lambda args, input:
                                       self.raw.write_text("v") and ""],
                               "ffprobe": ["9.1\n"]})
        result, problems = self.record(runners)
        self.assertEqual(problems, [])
        self.assertEqual(result, (self.raw, [0.0, 3.0, 7.3]))
        self.assertEqual(runners.calls, [
            ("vhs", launch_demo.RECORD_TIMEOUT, [str(self.tape)], None),
            ("ffprobe", launch_demo.PROBE_TIMEOUT, duration_argv(self.raw),
             None)])
        lines = self.tape.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[:6], [
            f"Output {self.raw.resolve()}", "Set Shell bash",
            "Set Width 1280", "Set Height 720", "Set FontSize 18",
            "Set TypingSpeed 50ms"])
        body = lines[6:]
        blocks = []
        for line in body:
            if line == "Hide":
                blocks.append([])
            blocks[-1].append(line)
        self.assertEqual(len(blocks), 3)
        for block, text, commands, sleep in (
                (blocks[0], ("T", "G"), [], "Sleep 3.0s"),
                (blocks[1], ("B.",), ["python3 board.py"], "Sleep 3.5s"),
                (blocks[2], ("C.",), [], "Sleep 1.5s")):
            self.assertEqual(block[0], "Hide")
            self.assertTrue(block[1].startswith("Type "), block[1])
            self.assertIn("clear; printf", block[1])
            for part in text:
                self.assertIn(part, block[1])
            self.assertEqual(block[2:4], ["Enter", "Show"])
            typed = block[4:-1]
            self.assertEqual(len(typed), 2 * len(commands))
            for index, command in enumerate(commands):
                self.assertTrue(typed[2 * index].startswith("Type "))
                self.assertIn(command, typed[2 * index])
                self.assertEqual(typed[2 * index + 1], "Enter")
            self.assertEqual(block[-1], sleep)

    def test_drift_past_the_tolerance_is_a_problem_and_no_result(self):
        runners = FakeRunners({"vhs": [lambda args, input:
                                       self.raw.write_text("v") and ""],
                               "ffprobe": ["11.0\n"]})
        self.assertEqual(self.record(runners), (None, [
            "launch-demo: recording ran 11.0 s where the plan expected"
            " 8.8 s — narration would drift"]))

    def test_a_failing_vhs(self):
        err = subprocess.CalledProcessError(
            1, ["vhs"], stderr="File: demo.tape\nttyd: command not found\n")
        self.assertEqual(self.record(FakeRunners({"vhs": [err]})), (None, [
            "launch-demo: terminal recorder failed: ttyd: command not"
            " found"]))

    def test_a_hung_vhs(self):
        import cli
        err = subprocess.TimeoutExpired(["vhs"], 600)
        self.assertEqual(self.record(FakeRunners({"vhs": [err]})), (None, [
            f"launch-demo: terminal recorder failed: {cli.detail(err)}"]))


SUMMARY_ARGV = ["-v", "error", "-show_entries",
                "stream=codec_type,codec_name:format=duration"]
PROBE_LINES = "codec_name=h264\ncodec_type=video\ncodec_name=aac\n" \
              "codec_type=audio\n"
ENCODE_TAIL = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
               "-c:a", "aac", "-movflags", "+faststart"]


class TestAssemble(WorkdirMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.raw = self.work / "raw.mp4"
        self.clips = [(self.work / "line-1.wav", 2.0),
                      (self.work / "line-2.wav", 3.0)]
        self.out = Path(self.tmp.name) / "publish" / "demo" / "launch.mp4"
        self.scratch_out = self.work / "launch.mp4"

    def assemble(self, runners):
        return launch_demo.assemble(self.raw, self.clips, [0.0, 3.0],
                                    self.out, runners)

    def test_one_ffmpeg_call_then_the_move_then_the_summary(self):
        runners = FakeRunners({"ffmpeg": [writes()],
                               "ffprobe": [PROBE_LINES]})
        summary, problems = self.assemble(runners)
        self.assertEqual(problems, [])
        self.assertEqual(summary, ["launch-demo: codec_name=h264",
                                   "launch-demo: codec_type=video",
                                   "launch-demo: codec_name=aac",
                                   "launch-demo: codec_type=audio"])
        self.assertTrue(self.out.is_file())
        self.assertFalse(self.scratch_out.exists())
        self.assertEqual(runners.binaries(), ["ffmpeg", "ffprobe"])
        binary, timeout, args, _ = runners.calls[0]
        self.assertEqual(timeout, launch_demo.FFMPEG_TIMEOUT)
        self.assertEqual(args[:7], ["-y", "-i", str(self.raw),
                                    "-i", str(self.clips[0][0]),
                                    "-i", str(self.clips[1][0])])
        self.assertEqual(args[7], "-filter_complex")
        graph = args[8]
        self.assertIn("adelay=0|0", graph)
        self.assertIn("adelay=3000|3000", graph)
        self.assertEqual(graph.count("amix=inputs=2"), 1)
        self.assertIn("scale=1280:720", graph)
        self.assertIn("pad=1280:720", graph)
        self.assertEqual(args[-11:], ENCODE_TAIL + [str(self.scratch_out)])
        self.assertNotIn(str(self.out), args)
        self.assertEqual(runners.calls[1],
                         ("ffprobe", launch_demo.PROBE_TIMEOUT,
                          SUMMARY_ARGV + [str(self.scratch_out)], None))

    def test_a_failing_ffmpeg_leaves_nothing_at_out(self):
        err = subprocess.CalledProcessError(
            1, ["ffmpeg"], stderr="ffmpeg version 8.1\nUnrecognized option"
                                  " 'nope'\n")
        self.assertEqual(self.assemble(FakeRunners({"ffmpeg": [err]})),
                         (None, ["launch-demo: ffmpeg failed: Unrecognized"
                                 " option 'nope'"]))
        self.assertFalse(self.out.exists())

    def test_a_hung_ffmpeg(self):
        import cli
        err = subprocess.TimeoutExpired(["ffmpeg"], 600)
        self.assertEqual(self.assemble(FakeRunners({"ffmpeg": [err]})),
                         (None, [f"launch-demo: ffmpeg failed:"
                                 f" {cli.detail(err)}"]))

    def test_an_unreadable_result_is_the_same_problem_and_no_file(self):
        err = subprocess.CalledProcessError(
            1, ["ffprobe"], stderr="moov atom not found\n")
        runners = FakeRunners({"ffmpeg": [writes()], "ffprobe": [err]})
        self.assertEqual(self.assemble(runners),
                         (None, ["launch-demo: ffmpeg failed: moov atom not"
                                 " found"]))
        self.assertFalse(self.out.exists())


LAUNCH_MD = """---
launch: demo
date: 2026-10-08
sources: [docs/features/demo/prd.md]
video: launch.mp4
---

# Launch: demo

""" + COPY


def vhs_writes_raw(args, input):
    (Path(args[0]).parent / "raw.mp4").write_text("v", encoding="utf-8")
    return ""


def produced_script():
    """Fakes for one PRODUCED terminal run of STORYBOARD: four narration
    lines, the recording, the mux, the summary."""
    return {"say": [writes()] * 4,
            "ffprobe": ["2.0\n", "3.0\n", "1.0\n", "1.0\n", "10.5\n",
                        PROBE_LINES],
            "vhs": [vhs_writes_raw],
            "ffmpeg": [writes()]}


class RenderMixin:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = {**VALID, "publish": "out", "voice": "say -o {out}"}
        write_config(self.root, self.config)
        self.slug_dir = self.root / "out" / "demo"
        self.slug_dir.mkdir(parents=True)
        (self.slug_dir / "launch.md").write_text(LAUNCH_MD, encoding="utf-8")
        (self.slug_dir / "storyboard.json").write_text(
            json.dumps(STORYBOARD), encoding="utf-8")
        self.scratch = self.root / "scratch"
        self.scratch.mkdir()
        self.which = FakeWhich(ALL_TOOLS)
        self.runners = FakeRunners(produced_script())

    def render(self):
        return launch_demo.render(self.root, self.config, "demo", self.which,
                                  self.runners, scratch=self.scratch)

    def published(self):
        return sorted(path.name for path in self.slug_dir.iterdir())


class TestRender(RenderMixin, unittest.TestCase):
    def test_no_copy_is_the_missing_problem(self):
        (self.slug_dir / "launch.md").unlink()
        self.assertEqual(self.render(),
                         (None, [], ["launch-demo: missing out/demo/launch.md"]))

    def test_no_storyboard_is_the_missing_problem(self):
        (self.slug_dir / "storyboard.json").unlink()
        self.assertEqual(self.render(), (None, [], [
            "launch-demo: missing out/demo/storyboard.json"]))

    def test_a_bad_storyboard_is_problems_before_any_tool_runs(self):
        board = storyboard(outro="Something is guessed.")
        (self.slug_dir / "storyboard.json").write_text(json.dumps(board),
                                                       encoding="utf-8")
        self.assertEqual(self.render(), (None, [], [
            f"{SB} outro is not a sentence of launch.md"]))
        self.assertEqual(self.runners.calls, [])

    def test_a_missing_tool_is_copy_only_before_any_tool_runs(self):
        self.which = FakeWhich({**ALL_TOOLS, "vhs": None})
        verdict, lines, problems = self.render()
        self.assertEqual((verdict, problems), ("COPY-ONLY", []))
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("launch-demo: missing vhs — "),
                        lines)
        self.assertEqual(self.runners.calls, [])
        self.assertEqual(self.published(), ["launch.md", "storyboard.json"])

    def test_a_produced_run_in_order(self):
        verdict, lines, problems = self.render()
        self.assertEqual((verdict, problems), ("PRODUCED", []))
        self.assertEqual(lines[:3], [
            f"launch-demo: scratch {self.scratch}",
            "launch-demo: wrote out/demo/demo.tape",
            "launch-demo: wrote out/demo/launch.mp4"])
        self.assertEqual(lines[3:], ["launch-demo: codec_name=h264",
                                     "launch-demo: codec_type=video",
                                     "launch-demo: codec_name=aac",
                                     "launch-demo: codec_type=audio"])
        self.assertEqual(self.runners.binaries(), [
            "say", "ffprobe", "say", "ffprobe", "say", "ffprobe", "say",
            "ffprobe", "vhs", "ffprobe", "ffmpeg", "ffprobe"])
        self.assertEqual(self.published(), ["demo.tape", "launch.md",
                                            "launch.mp4", "storyboard.json"])
        self.assertEqual((self.slug_dir / "demo.tape").read_text(),
                         (self.scratch / "demo.tape").read_text())
        for name in ("line-1.wav", "raw.mp4", "demo.tape"):
            self.assertTrue((self.scratch / name).is_file(), name)

    def test_the_narration_is_every_line_in_scene_order(self):
        self.render()
        spoken = [call[3] for call in self.runners.calls if call[0] == "say"]
        self.assertEqual(spoken, [STORYBOARD["intro"] + "\n",
                                  STORYBOARD["steps"][0]["say"] + "\n",
                                  STORYBOARD["steps"][1]["say"] + "\n",
                                  STORYBOARD["outro"] + "\n"])

    def test_a_default_scratch_is_a_named_launch_demo_tempdir(self):
        import shutil
        verdict, lines, _ = launch_demo.render(self.root, self.config, "demo",
                                               self.which, self.runners)
        scratch = Path(lines[0].removeprefix("launch-demo: scratch "))
        self.addCleanup(shutil.rmtree, scratch, True)
        self.assertEqual(verdict, "PRODUCED")
        self.assertTrue(scratch.name.startswith("launch-demo-"))
        self.assertTrue((scratch / "raw.mp4").is_file())

    def test_a_voice_failure_writes_nothing(self):
        err = subprocess.CalledProcessError(1, ["say"],
                                            stderr="Voice not found\n")
        self.runners = FakeRunners({**produced_script(), "say": [err]})
        verdict, lines, problems = self.render()
        self.assertEqual((verdict, problems), (None, [
            "launch-demo: voice failed on line 1: Voice not found"]))
        self.assertEqual(lines, [f"launch-demo: scratch {self.scratch}"])
        self.assertEqual(self.published(), ["launch.md", "storyboard.json"])

    def test_a_drift_failure_writes_nothing(self):
        script = produced_script()
        script["ffprobe"][4] = "20.0\n"
        self.runners = FakeRunners(script)
        verdict, _, problems = self.render()
        self.assertEqual((verdict, problems), (None, [
            "launch-demo: recording ran 20.0 s where the plan expected"
            " 10.3 s — narration would drift"]))
        self.assertEqual(self.published(), ["launch.md", "storyboard.json"])

    def test_an_ffmpeg_failure_writes_nothing(self):
        err = subprocess.CalledProcessError(
            1, ["ffmpeg"], stderr="Unrecognized option 'nope'\n")
        self.runners = FakeRunners({**produced_script(), "ffmpeg": [err]})
        verdict, _, problems = self.render()
        self.assertEqual((verdict, problems), (None, [
            "launch-demo: ffmpeg failed: Unrecognized option 'nope'"]))
        self.assertEqual(self.published(), ["launch.md", "storyboard.json"])


class TestRenderLeg(RenderMixin, cli_contract.CliContract,
                    unittest.TestCase):
    usage_fragment = "python3 launch_demo.py config | probe | render"
    bad_argv = ("render",)

    def run_cli(self, argv):
        return cli_contract.capture(launch_demo.main, argv, root=self.root,
                                    which=self.which, runner=self.runners,
                                    platform="darwin")

    def test_a_produced_run_prints_lines_verdict_and_summary(self):
        code, out = self.run_cli(["render", "demo"])
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("launch-demo: scratch "))
        self.assertEqual(lines[1:3], ["launch-demo: wrote out/demo/demo.tape",
                                      "launch-demo: wrote out/demo/launch.mp4"])
        self.assertEqual(lines[-2:], ["PRODUCED", "launch-demo: 0 problem(s)"])
        import shutil
        shutil.rmtree(lines[0].removeprefix("launch-demo: scratch "), True)

    def test_problems_print_with_the_count_and_no_verdict(self):
        (self.slug_dir / "storyboard.json").unlink()
        code, out = self.run_cli(["render", "demo"])
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            "launch-demo: missing out/demo/storyboard.json",
            "launch-demo: 1 problem(s)"])


if __name__ == "__main__":
    unittest.main()
