# Brief grammar

What the tool holds fixed, so the skill can spend its judgement on the
words. Four parts: the config, the voice swap, the storyboard per
recorder, and the two rules that shape a storyboard — where the happy
path comes from, and three parts to three scenes.

## The config: `docs/launch-demo.json`

One JSON object, the consuming repo's, written once by a person and read
on every invocation. The tool reads nothing else about the repo. Every
absent or malformed field is one exact problem line; only `voice` has a
default.

| Field | Grammar | Meaning |
|---|---|---|
| `when` | `"ship"` or `"on-demand"` | `ship`: Ship runs the skill at every release; `on-demand`: only a direct invocation does |
| `recorder` | `"terminal"` or `"browser"` | which adapter records — vhs for a CLI, Playwright for a page |
| `against` | non-empty string; for `browser`, an `http` or `https` URL | the shell vhs types the steps into (`bash`, `zsh`, …), or the URL the browser opens first |
| `voice` | optional; non-empty string containing `{out}` | the voice command — see the swap below |
| `publish` | plain relative path, no `..`, inside the repo | the directory under which `<slug>/` is written |

A minimal terminal config:

```json
{"when": "ship", "recorder": "terminal", "against": "bash",
 "publish": "docs/launches"}
```

A browser config points `against` at a served page and keeps the same
other fields; the page must answer an HTTP `HEAD` when the tool runs, or
the verdict is copy-only with the reason.

## The voice swap

`voice` is any command that reads one line of text on stdin and writes
a WAV at the path substituted for `{out}`. The tool runs it once per
narration line, split without a shell, under a 60-second budget per
line, and measures the WAV with ffprobe to place it on the timeline.

The two free defaults, chosen by platform when the field is absent:

- macOS: `say --data-format=LEI16@22050 -o {out}`
- elsewhere: `espeak-ng -w {out}` (one distribution package, no model
  to download)

Any voice that fits the contract replaces them — a local Piper model
(`piper --model en_US-lessac-medium.onnx --output_file {out}`), or a
wrapper script around a hosted voice. A hosted voice's key is its own
business, read by that script from its own environment; this config
never carries it, and the tool never names an endpoint. Nothing here
spends money unless the repo chooses a voice that does.

## The storyboard: `<publish>/<slug>/storyboard.json`

```json
{"title": "Launch demo",
 "tagline": "A launch brief nobody made by hand",
 "intro": "<one sentence of What it is>",
 "steps": [{"say": "<one sentence of What it does>",
            "do": ["python3 board.py"]}],
 "outro": "<one sentence of How it helps>"}
```

- `title` and `tagline` are free text for the title card.
- `intro`, every step's `say`, and `outro` must each be a verbatim
  sentence of `launch.md`'s body. The comparison ignores how either
  side is wrapped, and nothing else: a sentence differing by one word
  is refused with the line's number. Cut; never paraphrase.
- `steps` is a non-empty list. A step without `do` is allowed — it
  narrates over the screen it has.
- `do` is per recorder:
  - **terminal** — a list of shell commands, typed one per line into
    the configured shell, each followed by Enter. The list may be
    empty.
  - **browser** — one string of JavaScript statements that run inside
    `async (page) => { … }` with Playwright's `page`, for example
    `"await page.click('#count'); await page.fill('#name', 'Ada');"`.
    The string may be empty. A step that navigates keeps its caption:
    the bar is re-added on every document load.
- The storyboard carries no timing. Each scene is held for its
  narration's length plus a short settle; the title card for at least
  three seconds. The tool computes the terminal timeline and refuses a
  recording that drifts from it; the browser timeline is measured from
  the driver's own marks.

## Where the happy path comes from

The video shows one walk through the feature, never guessed. The first
source that exists wins, in this order:

1. a `storyboard.json` already at the publish path — reused unchanged,
   never edited;
2. an executable path — an E2E test `verification.md` names, or the
   commands verification ran for the feature;
3. `ux.md`'s primary flow;
4. `verification.md`'s evidence;
5. the pull request body's before-and-after evidence section.

With none, there is no storyboard and no video: `launch.md`'s `video:`
line records `none — no happy-path source (looked at: …)` and the
verdict is copy-only. The copy stands on its own.

## Three parts to three scenes

The copy's three labelled parts map to the video's three kinds of
scene, which is what gives the storyboard its shape and the check its
rule:

| `launch.md` section | scene | what is on screen |
|---|---|---|
| *What it is* | the title card | the title and tagline, over the `intro` narration |
| *What it does* | the steps | each step's `do` running, its `say` as the caption |
| *How it helps* | the outro | the `outro` line, spoken and shown |

The skill chooses sentences, not structure. One sentence per scene is
the norm; a step whose action takes longer than its sentence is held
anyway, because narration is the clock and the recording follows it,
never the other way round.
