"""launch_demo_drivers: the text each launch-demo recorder writes and
runs — the vhs tape for the terminal, the Playwright module and its
title and outro cards for the browser — as pure functions of the plan
launch_demo.plan builds. No I/O and no external CLI: launch_demo.py's
recorder adapters write these to the scratch directory and run them.
Stdlib only.
"""
import html
import json

# The frame every driver records at, and the terminal's typing cadence
# (launch_demo.plan prices each typed character at it).
WIDTH = 1280
HEIGHT = 720
FONT_SIZE = 18
TYPING_SPEED = 0.05


def typeable(command):
    """One line holding at most two of vhs's three string delimiters, so
    a free one can wrap it: vhs strings carry no escapes."""
    return (isinstance(command, str) and "\n" not in command
            and any(quote not in command for quote in "`\"'"))


# What each scene kind prints before its hold: a bold title over its
# tagline, a dim caption line, the bold closing line. The recorder
# draws every word; ffmpeg draws nothing.
SCREEN_FORMATS = {"title": r"\033[1m%b\033[0m\n\n%b\n",
                  "step": r"\033[2m%b\033[0m\n\n",
                  "outro": r"\033[1m%b\033[0m\n"}


def _tape_string(text):
    """A vhs string literal in a delimiter the text lacks (typeable's
    guarantee for a command, _printf_word's for a screen line)."""
    quote = next(quote for quote in "`\"'" if quote not in text)
    return f"{quote}{text}{quote}"


def _printf_word(text):
    """text as one single-quoted printf %b word, each quote, backslash
    and line break octal-escaped: printed verbatim, never parsed."""
    return "'" + "".join(f"\\0{ord(c):03o}" if c in "`'\"\\\r\n" else c
                         for c in text) + "'"


def _screen(plan, scene):
    """The shell line that clears the terminal and prints a scene's
    on-screen text, typed off camera."""
    words = ([plan["title"], plan["tagline"]] if scene["kind"] == "title"
             else [scene["say"]])
    return (f"clear; printf '{SCREEN_FORMATS[scene['kind']]}' "
            + " ".join(map(_printf_word, words)))


def tape(plan, raw, against):
    """The vhs tape realised from the plan: a header carrying no timing,
    then per scene the hidden screen print, the step's commands typed
    and entered, and the scene's hold. vhs parses an absolute Output
    path only when quoted (a mkdtemp path never holds a double quote)."""
    lines = [f'Output "{raw.resolve()}"', f"Set Shell {against}",
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

# The browser driver, filled by driver: the scene code is generated
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


def driver(plan):
    steps_seen = 0
    blocks = []
    for scene in plan["scenes"]:
        first_step = scene["kind"] == "step" and steps_seen == 0
        steps_seen += scene["kind"] == "step"
        blocks.append(_scene_code(scene, first_step))
    return DRIVER_HEAD.format(width=WIDTH, height=HEIGHT,
                              scenes="\n\n".join(blocks))


def card(title, text):
    return CARD_HTML.format(width=WIDTH, height=HEIGHT,
                            title=html.escape(title), text=html.escape(text))
