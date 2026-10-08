#!/usr/bin/env python3
"""launch_demo: the deterministic half of the launch-demo skill
(feature:launch-demo, PRD-0009) — the config grammar, the tool probe,
narration through the consuming repo's voice command, the generated
recorder driver, the recording, the timeline, the ffmpeg mux and the
verdict, as pure functions over `root` and injected runners plus a
thin main. The agent owns the copy and the storyboard; this tool owns
everything that must be exact and testable (ADR-0062's split, the
second reason a skill earns a shipped tool).

Same shape as board.py: lives at the plugin root, invoked by path from
the skill's directory, not mirrored into stamped repos. Every external
CLI (ffmpeg, ffprobe, vhs, node, the voice) goes through cli.runner, so
tests inject fake runners and CI runs no real recorder. Stdlib only.
"""
import shlex
import shutil
import sys
from pathlib import Path

import cli

LABEL = "launch-demo"
CONFIG = "docs/launch-demo.json"
USAGE = "usage: python3 launch_demo.py config | probe | render <slug>"

# The timeline's constants: the title card's floor, the pause after each
# narration line, the recorder's typing cadence, the tolerated gap
# between a computed and a recorded duration, and the frame.
TITLE_SECONDS = 3
SETTLE = 0.5
TYPING_SPEED = 0.05
DRIFT_TOLERANCE = 1.5
WIDTH = 1280
HEIGHT = 720

# Per-child timeouts, seconds: the probes and measurements, one
# narration line, one recording, one mux, and the reachability HEAD.
PROBE_TIMEOUT = 30
VOICE_TIMEOUT = 60
RECORD_TIMEOUT = 600
FFMPEG_TIMEOUT = 600
HEAD_TIMEOUT = 5

WHENS = ("ship", "on-demand")
RECORDERS = ("terminal", "browser")
VOICE_DEFAULTS = {"darwin": "say --data-format=LEI16@22050 -o {out}"}
VOICE_FALLBACK = "espeak-ng -w {out}"

# What a missing tool is for and how to get it, by name: the free parts
# of the `missing` line the probe leg prints.
TOOLS = {
    "ffmpeg": ("transcodes, pads and muxes the recording",
               "brew install ffmpeg (macOS) or apt install ffmpeg"),
    "ffprobe": ("measures narration and recording durations",
                "ships with ffmpeg"),
    "vhs": ("records the terminal",
            "brew install vhs (needs ttyd) or go install"
            " github.com/charmbracelet/vhs@latest"),
    "node": ("runs the Playwright browser driver",
             "brew install node (macOS) or apt install nodejs"),
    "playwright": ("records the browser",
                   "npm install playwright && npx playwright install"
                   " chromium, from the repo root"),
}
VOICE_PURPOSE = "renders each narration line to a WAV"
VOICE_HINT = ("install it, or point voice in docs/launch-demo.json at"
              " any command reading one line on stdin and writing {out}")


def _is_text(value):
    return isinstance(value, str) and bool(value)


def _plain_relative(path):
    """A relative path with no `..` step, no leading slash and no
    drive — one that stays inside the repo wherever it is joined."""
    if not _is_text(path):
        return False
    pure = Path(path)
    return (not pure.is_absolute() and not path.startswith("/")
            and ".." not in pure.parts and pure.parts != ())


def _check_when(raw):
    if raw["when"] not in WHENS:
        return 'when must be "ship" or "on-demand"'


def _check_recorder(raw):
    if raw["recorder"] not in RECORDERS:
        return 'recorder must be "terminal" or "browser"'


def _check_against(raw):
    if not _is_text(raw["against"]):
        return "against must be a non-empty string"
    if (raw.get("recorder") == "browser"
            and not raw["against"].startswith(("http://", "https://"))):
        return "against must be an http(s) URL for the browser recorder"


def _check_voice(raw):
    if not (_is_text(raw["voice"]) and "{out}" in raw["voice"]):
        return "voice must be a non-empty string naming {out}"


def _check_publish(raw):
    if not _plain_relative(raw["publish"]):
        return "publish must be a plain relative path inside the repo"


# One grammar check per field, in field order; each answers the
# unprefixed problem or None.
_FIELD_CHECKS = {"when": _check_when, "recorder": _check_recorder,
                 "against": _check_against, "voice": _check_voice,
                 "publish": _check_publish}


def load(root, platform=sys.platform):
    """(config, []) with the parsed docs/launch-demo.json, its voice
    defaulted by platform when absent, or (None, problems) — one exact
    string per field, in field order, every one prefixed `launch-demo: `.
    Absence is the missing problem here; the Ship hook tests for the
    file before invoking the skill and treats absence as nothing to do."""
    shown = f"{LABEL}: {CONFIG}"
    raw, problem = cli.read_file(Path(root) / CONFIG, CONFIG, dict)
    if problem:
        return None, [f"{LABEL}: {problem}"]
    if raw is None:
        return None, [f"{LABEL}: missing {CONFIG}"]
    problems = []
    for field, check in _FIELD_CHECKS.items():
        if field not in raw:
            if field != "voice":  # the one field with a default
                problems.append(f"{shown} has no {field}")
            continue
        problem = check(raw)
        if problem:
            problems.append(f"{shown} {problem}")
    if problems:
        return None, problems
    config = dict(raw)
    config.setdefault("voice", VOICE_DEFAULTS.get(platform, VOICE_FALLBACK))
    return config, []


def _entry(name):
    purpose, hint = TOOLS[name]
    return (name, purpose, hint)


def probe(config, which=shutil.which, runner=cli.runner):
    """(missing, problems) — missing is [(name, purpose, how to
    install)] over ffmpeg and ffprobe, the configured recorder's tools
    (vhs; node and the playwright package, resolved through node from
    the working directory), and the voice command's first token. A
    probe cannot fail, only report, so problems is always []: a
    Playwright browser that was never installed is not probeable and
    surfaces at record time as that adapter's failure."""
    missing = [_entry(name) for name in ("ffmpeg", "ffprobe")
               if not which(name)]
    if config["recorder"] == "terminal":
        if not which("vhs"):
            missing.append(_entry("vhs"))
    elif not which("node"):
        missing.append(_entry("node"))
    else:
        try:
            runner("node", PROBE_TIMEOUT)(["-e",
                                           "require.resolve('playwright')"])
        except cli.CLI_FAILURES:
            missing.append(_entry("playwright"))
    voice = shlex.split(config["voice"])[0]
    if not which(voice):
        missing.append((voice, VOICE_PURPOSE, VOICE_HINT))
    return missing, []


def _print_missing(missing):
    for name, purpose, hint in missing:
        print(f"{LABEL}: missing {name} — {purpose}; install: {hint}")


def main(argv, root=None, which=shutil.which, runner=cli.runner,
         platform=sys.platform):
    """`python3 launch_demo.py config | probe | render <slug>` from the
    repo root: problems then `launch-demo: N problem(s)` (exit 1), or
    the leg's lines, its verdict word alone, and the zero summary
    (exit 0); unrecognised argv is usage (exit 2)."""
    root = Path(root or ".")
    if argv == ["config"]:
        _, problems = load(root, platform)
        return cli.report(LABEL, problems)
    if argv == ["probe"]:
        config, problems = load(root, platform)
        if problems:
            return cli.report(LABEL, problems)
        missing, problems = probe(config, which, runner)
        _print_missing(missing)
        print("COPY-ONLY" if missing else "READY")
        return cli.report(LABEL, problems)
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
