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
import html
import json
import os
import shlex
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

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
URL_SCHEMES = ("http", "https")
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
            and urlsplit(raw["against"]).scheme not in URL_SCHEMES):
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


STORYBOARD_FIELDS = ("title", "tagline", "intro", "steps", "outro")


def _normalised(text):
    return " ".join(text.split())


def _in_copy(line, copy):
    return isinstance(line, str) and _normalised(line) in copy


def _check_steps(steps, copy, recorder):
    """The per-step problems: each step's say present and cut from the
    copy, its do in the recorder's shape — a list of commands for the
    terminal, one string of statements for the browser, or absent."""
    problems = []
    for number, step in enumerate(steps, 1):
        label = f"{LABEL}: storyboard step {number}"
        if not isinstance(step, dict) or "say" not in step:
            problems.append(f"{label} has no say")
        elif not _in_copy(step["say"], copy):
            problems.append(f"{label} narration is not a sentence of"
                            " launch.md")
        if not isinstance(step, dict) or "do" not in step:
            continue
        if recorder == "terminal" and not isinstance(step["do"], list):
            problems.append(f"{label} do must be a list of commands")
        if recorder == "browser" and not isinstance(step["do"], str):
            problems.append(f"{label} do must be a string")
    return problems


def check_storyboard(storyboard, copy_text, recorder):
    """The storyboard held to its grammar and to the copy: problems, []
    when conformant. Every intro, say and outro must be a verbatim
    sentence of launch.md's body, compared whitespace-normalised on
    both sides, so "every narration line is cut from the copy" is a
    check rather than a hope. Pure: reads no file, runs nothing."""
    label = f"{LABEL}: storyboard"
    if not isinstance(storyboard, dict):
        return [f"{label} is not a JSON object"]
    copy = _normalised(copy_text)
    problems = []
    for field in STORYBOARD_FIELDS:
        if field not in storyboard:
            problems.append(f"{label} has no {field}")
        elif field in ("intro", "outro"):
            if not _in_copy(storyboard[field], copy):
                problems.append(f"{label} {field} is not a sentence of"
                                " launch.md")
        elif field == "steps":
            steps = storyboard["steps"]
            if not isinstance(steps, list) or not steps:
                problems.append(f"{label} steps must be a non-empty list")
            else:
                problems.extend(_check_steps(steps, copy, recorder))
    return problems


def plan(storyboard, seconds):
    """The timeline, the one owner of its arithmetic: scenes in order
    (title card, each step, outro), each with its kind, narration line,
    actions, hold and offset — hold is the narration's seconds plus
    SETTLE (the title card at least TITLE_SECONDS); offset is the sum of
    every earlier scene's hold and typing time, where that scene's
    narration starts — and `planned`, the whole recording's expected
    length. `seconds` is one narration duration per scene. A count that
    does not fit is a caller slip, so a ValueError, never a problem
    string. Pure: the same plan feeds the driver and the mux, so the
    two cannot disagree."""
    steps = storyboard["steps"]
    if len(seconds) != len(steps) + 2:
        raise ValueError(f"plan needs {len(steps) + 2} narration durations"
                         f" for {len(steps)} steps, got {len(seconds)}")
    cuts = ([("title", storyboard["intro"], [])]
            + [("step", step["say"], step.get("do", [])) for step in steps]
            + [("outro", storyboard["outro"], [])])
    scenes, offset = [], 0.0
    for (kind, say, do), narrated in zip(cuts, seconds):
        hold = narrated + SETTLE
        if kind == "title":
            hold = max(float(TITLE_SECONDS), hold)
        scenes.append({"kind": kind, "say": say, "do": do,
                       "hold": round(hold, 3), "offset": round(offset, 3)})
        # Typing a command costs TYPING_SPEED per character; a string do
        # (the browser form, run rather than typed) costs nothing.
        typed = sum(len(c) for c in do) if isinstance(do, list) else 0
        offset += hold + typed * TYPING_SPEED
    return {"title": storyboard["title"], "tagline": storyboard["tagline"],
            "scenes": scenes, "planned": round(offset, 3)}


def _duration(path, runner):
    """(seconds, None) from ffprobe's format=duration of one media file,
    or (None, the last line of ffprobe's stderr) — the one owner of the
    measurement argv, shared by narration and the recorders."""
    argv = ["-v", "error", "-show_entries", "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", str(path)]
    try:
        out = runner("ffprobe", PROBE_TIMEOUT)(argv).stdout
        return float(out.strip()), None
    except cli.CLI_FAILURES as err:
        return None, cli.detail(err)
    except ValueError:
        return None, f"ffprobe answered {out.strip()!r}"


def narrate(lines, voice, workdir, runner=cli.runner):
    """(clips, []) — one (wav path, seconds) per line, in order — or
    (None, [one problem]) at the first line the voice cannot render.
    The voice is the config's template with {out} substituted by
    workdir/line-N.wav and split with shlex (no shell), the line on
    stdin; the WAV is measured by ffprobe. Retry is safe: each run
    overwrites its own file."""
    clips = []
    for number, line in enumerate(lines, 1):
        wav = Path(workdir) / f"line-{number}.wav"
        argv = shlex.split(voice.replace("{out}", str(wav)))
        try:
            runner(argv[0], VOICE_TIMEOUT)(argv[1:], input=line + "\n")
        except cli.CLI_FAILURES as err:
            return None, [f"{LABEL}: voice failed on line {number}:"
                          f" {cli.detail(err)}"]
        if not wav.is_file():
            return None, [f"{LABEL}: voice wrote no file for line {number}"]
        seconds, problem = _duration(wav, runner)
        if problem:
            return None, [f"{LABEL}: voice failed on line {number}:"
                          f" {problem}"]
        clips.append((wav, seconds))
    return clips, []


FONT_SIZE = 18
# What each scene kind prints before its hold: a bold title over its
# tagline, a dim caption line, the bold closing line. The recorder
# draws every word; ffmpeg draws nothing.
SCREEN_FORMATS = {"title": r"\033[1m%s\033[0m\n\n%s\n",
                  "step": r"\033[2m%s\033[0m\n\n",
                  "outro": r"\033[1m%s\033[0m\n"}


def _tape_string(text):
    """A vhs string literal. vhs strings carry no escape processing, so
    the delimiter is one the text does not contain; a text holding all
    three loses its backticks."""
    for quote in ("`", '"', "'"):
        if quote not in text:
            return f"{quote}{text}{quote}"
    return "`" + text.replace("`", "'") + "`"


def _screen(plan, scene):
    """The shell line that clears the terminal and prints a scene's
    on-screen text, typed off camera."""
    words = ([plan["title"], plan["tagline"]] if scene["kind"] == "title"
             else [scene["say"]])
    return (f"clear; printf '{SCREEN_FORMATS[scene['kind']]}' "
            + " ".join(shlex.quote(word) for word in words))


def _tape(plan, raw, against):
    """The vhs tape realised from the plan: a header carrying no timing,
    then per scene the hidden screen print, the step's commands typed
    and entered, and the scene's hold."""
    lines = [f"Output {raw.resolve()}", f"Set Shell {against}",
             f"Set Width {WIDTH}", f"Set Height {HEIGHT}",
             f"Set FontSize {FONT_SIZE}",
             f"Set TypingSpeed {round(TYPING_SPEED * 1000)}ms"]
    for scene in plan["scenes"]:
        lines += ["Hide", f"Type {_tape_string(_screen(plan, scene))}",
                  "Enter", "Show"]
        for command in scene["do"]:
            lines += [f"Type {_tape_string(command)}", "Enter"]
        lines.append(f"Sleep {scene['hold']:.1f}s")
    return "\n".join(lines) + "\n"


def record_terminal(plan, workdir, against, runner=cli.runner):
    """The terminal adapter: ((raw video path, offsets), []) or (None,
    [one problem]). Writes workdir/demo.tape from the plan, runs vhs on
    it under RECORD_TIMEOUT, then measures the raw recording — offsets
    are the plan's computed ones, so a recording further than
    DRIFT_TOLERANCE from the planned length is refused: an out-of-sync
    video is worse than none. Knows no publish path."""
    workdir = Path(workdir)
    raw, tape = workdir / "raw.mp4", workdir / "demo.tape"
    tape.write_text(_tape(plan, raw, against), encoding="utf-8")
    failed = f"{LABEL}: terminal recorder failed"
    try:
        runner("vhs", RECORD_TIMEOUT)([str(tape)])
    except cli.CLI_FAILURES as err:
        return None, [f"{failed}: {cli.detail(err)}"]
    if not raw.is_file():
        return None, [f"{failed}: wrote no {raw.name}"]
    recorded, problem = _duration(raw, runner)
    if problem:
        return None, [f"{failed}: {problem}"]
    if abs(recorded - plan["planned"]) > DRIFT_TOLERANCE:
        return None, [f"{LABEL}: recording ran {recorded:.1f} s where the"
                      f" plan expected {plan['planned']:.1f} s — narration"
                      " would drift"]
    return (raw, [scene["offset"] for scene in plan["scenes"]]), []


FRAME_RATE = 30
SUMMARY_ENTRIES = "stream=codec_type,codec_name:format=duration"


def _filter_graph(count, offsets):
    """One ffmpeg filter graph: the raw video scaled into and padded to
    the frame, each narration clip delayed to its scene's offset (in
    whole milliseconds, both channels), all of them mixed into one
    track at full level."""
    video = (f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio="
             f"decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2[v]")
    delays = []
    for index, offset in enumerate(offsets[:count], 1):
        ms = round(offset * 1000)
        delays.append(f"[{index}:a]adelay={ms}|{ms}[a{index}]")
    mix = ("".join(f"[a{index}]" for index in range(1, count + 1))
           + f"amix=inputs={count}:normalize=0[a]")
    return ";".join([video, *delays, mix])


def assemble(raw, clips, offsets, out, runner=cli.runner):
    """(summary, []) or (None, [one problem]). The one ffmpeg call: the
    raw recording and every narration WAV in, one H.264 video stream
    and one AAC mix out, written beside the raw recording and probed
    there; only a result ffprobe can read is os.replace-d into `out`
    (its parent created), so the publish path never holds a partial
    mp4. The summary is ffprobe's stream and duration lines, each
    prefixed, for Verify to paste. ffmpeg draws nothing: every word on
    screen is the recorder's."""
    raw, out = Path(raw), Path(out)
    scratch_out = raw.parent / out.name
    argv = ["-y", "-i", str(raw)]
    for wav, _ in clips:
        argv += ["-i", str(wav)]
    argv += ["-filter_complex", _filter_graph(len(clips), offsets),
             "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FRAME_RATE),
             "-c:a", "aac", "-movflags", "+faststart", str(scratch_out)]
    failed = f"{LABEL}: ffmpeg failed"
    try:
        runner("ffmpeg", FFMPEG_TIMEOUT)(argv)
        out_text = runner("ffprobe", PROBE_TIMEOUT)(
            ["-v", "error", "-show_entries", SUMMARY_ENTRIES,
             str(scratch_out)]).stdout
    except cli.CLI_FAILURES as err:
        return None, [f"{failed}: {cli.detail(err)}"]
    out.parent.mkdir(parents=True, exist_ok=True)
    os.replace(scratch_out, out)
    return [f"{LABEL}: {line}" for line in out_text.splitlines()
            if line.strip()], []


CARD_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>
html, body {{ margin: 0; width: {width}px; height: {height}px;
  background: #14130f; color: #f3efe6; overflow: hidden; }}
body {{ display: flex; flex-direction: column; justify-content: center;
  align-items: center; text-align: center; padding: 0 96px;
  box-sizing: border-box; font-family: system-ui, sans-serif; }}
h1 {{ font-size: 56px; font-weight: 700; margin: 0 0 24px; }}
p {{ font-size: 28px; opacity: 0.8; margin: 0; }}
</style></head>
<body><h1>{title}</h1><p>{text}</p></body></html>
"""

# The browser driver, filled by _driver: the scene code is generated
# per scene and spliced in at {scenes}; the two values the run needs
# travel as argv, never the environment.
DRIVER_HEAD = """import {{ chromium }} from "playwright";
import {{ renameSync, writeFileSync }} from "node:fs";
import {{ join }} from "node:path";
import {{ pathToFileURL }} from "node:url";

const against = process.argv[2];
const work = process.argv[3];
let currentCaption = "";
const CAPTION_SCRIPT = `
  window.__launchDemoShowCaption = (text) => {{
    let bar = document.getElementById("launch-demo-caption");
    if (!text) {{ if (bar) bar.remove(); return; }}
    if (!bar) {{
      bar = document.createElement("div");
      bar.id = "launch-demo-caption";
      bar.style.cssText = "position:fixed;left:0;right:0;bottom:0;"
        + "z-index:2147483647;padding:16px 32px;"
        + "background:rgba(20,19,15,0.9);color:#f3efe6;"
        + "font:24px/1.4 system-ui,sans-serif;";
      (document.body || document.documentElement).appendChild(bar);
    }}
    bar.textContent = text;
  }};
  document.addEventListener("DOMContentLoaded", async () => {{
    window.__launchDemoShowCaption(await window.__launchDemoCaptionText());
  }});
`;

const browser = await chromium.launch({{ headless: true }});
const context = await browser.newContext({{
  viewport: {{ width: {width}, height: {height} }},
  recordVideo: {{ dir: work, size: {{ width: {width}, height: {height} }} }},
}});
// The caption bar is re-added on every document load, so a step that
// navigates keeps its caption; the text comes from this process.
await context.exposeFunction("__launchDemoCaptionText", () => currentCaption);
await context.addInitScript(CAPTION_SCRIPT);
const page = await context.newPage();
const marks = [Date.now()];
const sleep = (seconds) => new Promise((r) => setTimeout(r, seconds * 1000));
const caption = async (text) => {{
  currentCaption = text;
  await page.evaluate((t) => window.__launchDemoShowCaption(t), text);
}};
const card = (name) => pathToFileURL(join(work, name)).href;

{scenes}
const video = page.video();
await context.close();
renameSync(await video.path(), join(work, "raw.webm"));
writeFileSync(join(work, "marks.json"), JSON.stringify(marks));
await browser.close();
"""


def _scene_code(scene, first_step):
    """One scene's statements: mark its start, then the title card,
    the step (caption, its do inside an async (page) => wrapper), or
    the outro card, each held for its planned seconds."""
    lines = ["marks.push(Date.now());"]
    if scene["kind"] == "title":
        lines.append('await page.goto(card("title.html"));')
    elif scene["kind"] == "outro":
        lines += ['await caption("");', 'await page.goto(card("outro.html"));']
    else:
        if first_step:
            lines.append("await page.goto(against);")
        do = scene["do"] if isinstance(scene["do"], str) else ""
        lines += [f"await caption({json.dumps(scene['say'])});",
                  f"await (async (page) => {{ {do} }})(page);"]
    lines.append(f"await sleep({scene['hold']});")
    return "\n".join(lines)


def _driver(plan):
    steps_seen = 0
    blocks = []
    for scene in plan["scenes"]:
        first_step = scene["kind"] == "step" and steps_seen == 0
        steps_seen += scene["kind"] == "step"
        blocks.append(_scene_code(scene, first_step))
    return DRIVER_HEAD.format(width=WIDTH, height=HEIGHT,
                              scenes="\n\n".join(blocks))


def _card(title, text):
    return CARD_HTML.format(width=WIDTH, height=HEIGHT,
                            title=html.escape(title), text=html.escape(text))


def record_browser(plan, workdir, against, runner=cli.runner):
    """The browser adapter: ((raw video path, offsets), []) or (None,
    [one problem]). Writes the title and outro cards and demo.mjs from
    the plan, runs it under node with RECORD_TIMEOUT (the URL and the
    scratch directory as arguments), and reads the marks the driver
    recorded — page creation, then each scene start — so offsets are
    measured, not the plan's. Knows no publish path."""
    workdir = Path(workdir)
    outro = plan["scenes"][-1]
    (workdir / "title.html").write_text(
        _card(plan["title"], plan["tagline"]), encoding="utf-8")
    (workdir / "outro.html").write_text(_card(outro["say"], ""),
                                        encoding="utf-8")
    driver = workdir / "demo.mjs"
    driver.write_text(_driver(plan), encoding="utf-8")
    failed = f"{LABEL}: browser recorder failed"
    try:
        runner("node", RECORD_TIMEOUT)([str(driver), against, str(workdir)])
    except cli.CLI_FAILURES as err:
        return None, [f"{failed}: {cli.detail(err)}"]
    raw = workdir / "raw.webm"
    if not raw.is_file():
        return None, [f"{failed}: wrote no {raw.name}"]
    marks, problem = cli.read_file(workdir / "marks.json", "marks.json", list)
    if problem or marks is None:
        return None, [f"{failed}: {problem or 'wrote no marks.json'}"]
    scenes = len(plan["scenes"])
    if len(marks) != scenes + 1:
        return None, [f"{failed}: marks.json has {len(marks)} marks for"
                      f" {scenes} scenes"]
    offsets = [round((mark - marks[0]) / 1000, 3) for mark in marks[1:]]
    return (raw, offsets), []


def _head(url, timeout):
    """An HTTP HEAD of url: its status, with an HTTP error status still
    a status (the server answered); anything else raises."""
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status
    except urllib.error.HTTPError as err:
        return err.code


def reachable(against, head=None):
    """(True, None) when a HEAD of against is answered with any HTTP
    status, else (False, reason). The default head goes through
    urllib.request under HEAD_TIMEOUT; tests inject one."""
    try:
        (head or _head)(against, HEAD_TIMEOUT)
    except TimeoutError:
        return False, f"timed out after {HEAD_TIMEOUT} s"
    except urllib.error.URLError as err:
        if isinstance(err.reason, TimeoutError):
            return False, f"timed out after {HEAD_TIMEOUT} s"
        return False, str(err.reason)
    except OSError as err:
        return False, str(err)
    return True, None


# recorder -> (adapter, the driver it writes to the scratch directory,
# copied beside the mp4 so a reader sees what ran).
ADAPTERS = {"terminal": (record_terminal, "demo.tape"),
            "browser": (record_browser, "demo.mjs")}


def _body(text):
    """launch.md's body: the text after its frontmatter block."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5:]
    return text


def _narration_lines(board):
    return ([board["intro"]] + [step["say"] for step in board["steps"]]
            + [board["outro"]])


def _read_sources(root, shown_dir, slug_dir):
    """(copy body, storyboard, problems) from the slug directory."""
    problems = []
    copy, problem = cli.read_file(slug_dir / "launch.md",
                                  f"{shown_dir}/launch.md", str)
    if problem:
        problems.append(f"{LABEL}: {problem}")
    elif copy is None:
        problems.append(f"{LABEL}: missing {shown_dir}/launch.md")
    board, problem = cli.read_file(slug_dir / "storyboard.json",
                                   f"{shown_dir}/storyboard.json", dict)
    if problem:
        problems.append(f"{LABEL}: {problem}")
    elif board is None:
        problems.append(f"{LABEL}: missing {shown_dir}/storyboard.json")
    return copy, board, problems


def render(root, config, slug, which=shutil.which, runner=cli.runner,
           head=None, scratch=None):
    """(verdict, lines, problems) for <publish>/<slug>/: the composed
    run and the verdict. Checks run in cost order — the copy and the
    storyboard read and held to the grammar (problems before any tool
    runs), the probe (COPY-ONLY before any tool runs), then narration,
    the configured recorder and the mux. In COPY-ONLY nothing is
    written to the publish path; on PRODUCED the slug directory gains
    the driver and launch.mp4. Intermediates stay in the scratch
    directory (a launch-demo- tempdir unless given), named in the
    first line so a failed run can be inspected. Reads nothing about
    the repo but the config and the slug directory."""
    root = Path(root)
    shown_dir = f"{config['publish']}/{slug}"
    slug_dir = root / config["publish"] / slug
    copy, board, problems = _read_sources(root, shown_dir, slug_dir)
    if problems:
        return None, [], problems
    problems = check_storyboard(board, _body(copy), config["recorder"])
    if problems:
        return None, [], problems
    missing, _ = probe(config, which, runner)
    if missing:
        return "COPY-ONLY", [_missing_line(entry) for entry in missing], []
    if config["recorder"] == "browser":
        ok, reason = reachable(config["against"], head)
        if not ok:
            return "COPY-ONLY", [f"{LABEL}: against {config['against']} is"
                                 f" unreachable: {reason}"], []
    workdir = Path(scratch or tempfile.mkdtemp(prefix="launch-demo-"))
    lines = [f"{LABEL}: scratch {workdir}"]
    clips, problems = narrate(_narration_lines(board), config["voice"],
                              workdir, runner)
    if problems:
        return None, lines, problems
    timeline = plan(board, [seconds for _, seconds in clips])
    record, driver = ADAPTERS[config["recorder"]]
    result, problems = record(timeline, workdir, config["against"], runner)
    if problems:
        return None, lines, problems
    raw, offsets = result
    summary, problems = assemble(raw, clips, offsets, slug_dir / "launch.mp4",
                                 runner)
    if problems:
        return None, lines, problems
    shutil.copyfile(workdir / driver, slug_dir / driver)
    lines += [f"{LABEL}: wrote {shown_dir}/{driver}",
              f"{LABEL}: wrote {shown_dir}/launch.mp4"]
    return "PRODUCED", lines + summary, []


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


def _missing_line(entry):
    name, purpose, hint = entry
    return f"{LABEL}: missing {name} — {purpose}; install: {hint}"


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
        for entry in missing:
            print(_missing_line(entry))
        print("COPY-ONLY" if missing else "READY")
        return cli.report(LABEL, problems)
    if len(argv) == 2 and argv[0] == "render":
        config, problems = load(root, platform)
        if problems:
            return cli.report(LABEL, problems)
        verdict, lines, problems = render(root, config, argv[1], which,
                                          runner)
        for line in lines:
            print(line)
        if verdict:
            print(verdict)
        return cli.report(LABEL, problems)
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
