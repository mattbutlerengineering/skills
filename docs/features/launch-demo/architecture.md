---
stage: architect
run: feature:launch-demo
date: 2026-10-08
ux: skipped — no interactive surface; the video's storyboard (title card, steps, outro) is the architect's and implementer's concern, not a flow or screen
assumptions:
  - "The skill's trade-off read-out (step 6) was not held live; the four decisions that could have gone another way (the config home, the mp4 in git, who renders the on-screen text, the copy-only exit status) are recorded under Decisions & alternatives with the option that lost, and this stage's own recommendation was taken for each. Taken without user input."
  - "Config home and shape: one file per repo at docs/launch-demo.json — five fields (when, recorder, against, voice, publish), read by the tool through cli.read_file, absence a fact — rather than a block inside factory.json. Taken without user input."
  - "Happy-path precedence: an existing storyboard at the publish path, then an executable path (an E2E test or the commands the feature's own verification ran), then ux.md's primary flow, then verification.md's evidence, then the pull request's evidence section; with none, the skill stops at the copy (verdict COPY-ONLY, reason recorded in launch.md) and never invents a path. Taken without user input."
  - "The split: the agent writes the copy and the storyboard (prose plus per-step actions); the shipped tool launch_demo.py owns the config grammar, the probe, narration, the generated driver, the recording, the timeline and the mux. The tool rides with the plugin like board.py and is not mirrored into stamped repos, so factory_init.MIRRORS gains no entry; the manifest is still regenerated because protocol.py (mirrored) changes and the plugin version it pins moves. Taken without user input."
  - "Publish path: <publish>/<slug>/ holding launch.md, storyboard.json, the generated driver and launch.mp4; the mp4 is committed, with Git LFS named as the consuming repo's lever if it grows, rather than an ignored directory. Taken without user input."
  - "Storyboard: three narrated parts mapping the copy's three labelled parts (What it is → title card, What it does → steps, How it helps → outro); every narration line is a verbatim sentence of launch.md and the tool refuses one that is not. The recorder renders the title card and captions itself — the owner's ffmpeg carries no text filter — and ffmpeg only transcodes and muxes. Taken without user input."
  - "Copy-only exits 0 with the verdict word COPY-ONLY on stdout, the repo's verdict convention (budget_guard, cost_report); nonzero is reserved for problems. Ship pastes the tool's reason and verdict lines into the release log and never blocks on them. Taken without user input."
  - "Linux voice default is espeak-ng (one package, no model download); Piper is the documented swap. For the terminal recorder, `against` is the shell vhs runs the steps in. Taken without user input."
  - "cli.runner gains an optional timeout and a per-call stdin input, and CLI_FAILURES gains subprocess.TimeoutExpired, rather than the tool keeping a private runner. Taken without user input."
  - "The skill joins the README figure's existing card 'Around a pull request' rather than a seventh card. Taken without user input."
  - "One ADR is proposed (a second reason a skill earns a shipped tool, and the per-repo config home) and not written: docs/adr/ is a human merge gate in this repo. Taken without user input."
---

# Architecture: Launch demo

## Approach

A utility skill, `launch-demo`, backed by one stdlib tool at the plugin
root, `launch_demo.py`, split the way ADR-0062 split `pipeline-board` and
`board.py`: the agent owns what is taste and judgement — the copy, and a
storyboard that cuts that copy into a title card, narrated steps and an
outro — and the tool owns everything that must be deterministic and
testable: the config grammar, the tool probe, narration through the voice
command, the generated driver script, the recording, the timeline that
lays each narration clip at its step, the ffmpeg mux, and the verdict.
The consuming repo declares five facts in `docs/launch-demo.json`; the
tool reads nothing else about the repo. Ship gains one conditional step
that invokes the skill and pastes its verdict into the release log.

The shape that lost is prose-only: a SKILL.md that tells the agent to run
vhs, the voice and ffmpeg itself. It fails the PRD at two criteria it
cannot reach — exact problem strings per config field asserted through a
public interface, and recorders exercised with injected fake runners — and
it would make every launch's ffmpeg filter graph a fresh derivation, the
"second live deriver" ADR-0062 named. The other shape that lost is a live
browser agent; the brief already decided against it, and nothing here
reopens it: the driver is generated from the storyboard, and a bad
storyboard fails loudly.

One finding reshaped the video half. The owner's ffmpeg (Homebrew 8.1,
checked 2026-10-08) is built without libfreetype or libass, so neither
`drawtext` nor `subtitles` exists there, and depending on them would make
the owner's own machine copy-only. So the **recorder renders every word
on screen**: vhs clears the terminal and prints the title card and each
step's caption line off camera (`Hide … Show`, which the same check showed
costs no recorded time), and the Playwright wrapper opens a title page
and injects a caption bar. ffmpeg transcodes, pads and muxes; it draws
nothing.

```tree-claims
# What this design reads or edits, as it stands in this worktree on 2026-10-08.
exists: protocol.py
exists: cli.py
exists: factory_config.py
exists: factory_init.py
exists: board.py
exists: lint.py
exists: gates.py
exists: skills/ship/SKILL.md
exists: skills/ship/TEMPLATE.md
exists: skills/next/SKILL.md
exists: skills/pipeline-board/SKILL.md
exists: README.md
exists: docs/assets/skill-map.svg
exists: LEDGER.md
exists: .claude-plugin/plugin.json
exists: evals/routing.json
exists: factory/manifest.json
exists: tests/test_cli.py
exists: tests/test_fake_gh.py
exists: docs/features/launch-demo/prd.md
```

## Components

### `skills/launch-demo/SKILL.md` (+ `references/brief-grammar.md`)

- Responsibility: the judgement half. Given a feature reference — a run
  directory (`docs/features/<slug>/`, named or discovered) or `--pr <n>`
  for a feature with no run — it (1) runs `config`, stopping on problems;
  (2) runs `probe` and notes READY or COPY-ONLY; (3) reads the sources:
  `prd.md`, `verification.md`, `release.md` when the run exists, else the
  pull request body (through the forge CLI, as `audit` and `automate`
  already do) and the changelog entry naming it; (4) writes `launch.md`
  — three labelled parts, *What it is*, *What it does*, *How it helps*,
  in plain words, naming no path, function or identifier; (5) finds the
  happy path by the precedence in the data model below, and with none
  stops, recording why in `launch.md`'s `video:` line and printing
  COPY-ONLY; (6) writes `storyboard.json`, every `intro`/`say`/`outro`
  a verbatim sentence of `launch.md`; (7) runs `render <slug>` and
  reports its reason and verdict lines and the paths written. The
  reference file carries the config grammar (including the voice swap:
  point `voice` at any command that reads one line on stdin and writes a
  WAV to `{out}`; its key is its own, outside this config), the storyboard
  grammar per recorder, and the three-parts-to-three-scenes rule. Utility
  skill (ADR-0023): owns no artifact, has no template, the router never
  names it. Harness-neutral: it names the tool by path relative to its own
  directory (`../../launch_demo.py`, as `pipeline-board` does) and names no
  harness tool. ADR-0008 holds because step (4) needs nothing installed.
- Collaborators: `launch_demo.py` (every fact); `protocol.UTILITY_SKILLS`
  (registration); the Ship hook (its only automatic invoker).

### `launch_demo.py` (root tool; not mirrored)

- Responsibility: the deterministic half, as pure functions over `root`
  and injected runners, plus a thin `main`. `load(root)` reads
  `docs/launch-demo.json` through `cli.read_file` and applies the field
  grammar; `probe(config, which, run)` names what is missing;
  `check_storyboard(storyboard, copy_text, recorder)` holds the storyboard
  to its grammar and to the copy; `narrate(...)` renders each line to a
  WAV and measures it; `plan(storyboard, seconds)` is the one owner of the
  timeline arithmetic (pure — no subprocess import reachable from it);
  `record_terminal` / `record_browser` are the two recorder adapters
  behind one `record(plan, workdir, run)` contract; `assemble(...)` is the
  one ffmpeg call plus the ffprobe summary; `render(...)` composes them
  and decides the verdict. Policy (grammar, plan, verdict) imports nothing
  from the adapters; the adapters translate argv and files and call
  inward. Lives beside `board.py` and is invoked the same way; it ships
  with the plugin checkout on both harnesses and is not in
  `factory_init.MIRRORS` because no stamped-repo workflow runs it
  (CI-event triggers are out of scope). Stdlib only.
- Collaborators: `cli.runner`, `cli.CLI_FAILURES`, `cli.detail`,
  `cli.read_file`, `cli.report`; `shutil.which`; `urllib.request` (the
  reachability check); `tempfile`; `tests/test_launch_demo.py` (fake
  runners take the `(args, input=None)` port, so `tests/test_fake_gh.py`'s
  one-gh-fake rule does not read them as gh fakes).

### `cli.runner` — timeout and stdin (seam edit)

- Responsibility: stay the one sanctioned way to shell out (ADR-0037)
  while gaining what this tool's children need and no earlier caller did:
  `runner(binary, timeout=None)` returns `run(args, input=None)`, and
  `CLI_FAILURES` gains `subprocess.TimeoutExpired` so a hung vhs or
  ffmpeg becomes a problem string through `cli.detail` (whose
  `str(err)` branch already reads "timed out after N seconds") instead of
  a traceback. Both defaults preserve every existing call byte for byte;
  `gh_runner` passes neither. `cli.py` is mirrored, so the manifest is
  regenerated in the same change.
- Collaborators: `tests/test_cli.py` (pins the timeout raise and the
  stdin pass-through); `factory_init.update_manifest`.

### The Ship hook (`skills/ship/SKILL.md`, one step)

- Responsibility: fire the skill at the right moment and record the
  outcome, changing nothing else. A new step opens the Release stage,
  before the release mechanism runs, so the brief rides in the change the
  owner merges and is watched before merge: *if `docs/launch-demo.json`
  exists and its `when` is `ship`, load the `launch-demo` skill through
  the harness's skill-loading mechanism (a skill tool where one exists,
  otherwise a read of the skill file), run it for this run, commit what it
  wrote on the branch, and add one Release-log entry quoting the tool's
  reason line(s) and verdict verbatim; with no config file, or any other
  `when`, do nothing and write nothing.* The hook never blocks a release:
  a verdict of COPY-ONLY and a problem exit are both one log line.
  `skills/ship/TEMPLATE.md` is untouched — the entry is one numbered
  Release-log line, the PRD's "beyond the line that records the hook
  fired or degraded" — and `skills/next/SKILL.md` is untouched.
- Collaborators: the skill; `release.md` (the line); lint's
  `check_skill_recitals` (the step names no artifact and no stage, so the
  recital pins are unaffected).

### Roster and packaging entries

- Responsibility: make the skill exist everywhere the lint roster looks,
  each by its existing rule, no new checker: `launch-demo` appended to
  `protocol.UTILITY_SKILLS`; one README utility-table row (Moment:
  *Around a pull request*, why-line distilled from the description); one
  `<text class="row mono">` line in `docs/assets/skill-map.svg`'s
  *Around a pull request* card with the card's rect grown by one row, as
  the two-row cards are drawn; a `| launch-demo | draft | — | — |` LEDGER
  row; the slug added to `plugin.json`'s parenthetical utility list and
  the version set to `0.4.0`; at least three `evals/routing.json` cases
  expecting `launch-demo` (one `direct`, one `situational`, one
  `near-miss` against `ship` — "ship it" must not fire this, "make the
  launch video" must not fire `ship`), existing cases untouched; and
  `python3 factory_init.py update-manifest` run last, so
  `factory/manifest.json`'s `version` follows the plugin and the
  `protocol.py` and `cli.py` checksums follow their edits (the `0.3.0`
  bump did the same). `package.json`'s version has never tracked these
  bumps and stays as it is.
- Collaborators: `lint.check_plugin_skills`, `check_readme_skills`,
  `check_readme_no_orphans`, `check_readme_figure`, `check_ledger`,
  `check_evals` (the ≥3-cases policy), `gates` detector E.

### This repo as first consumer, and the browser fixture

- Responsibility: prove both recorders. `docs/launch-demo.json` here is
  `{"when": "ship", "recorder": "terminal", "against": "bash",
  "publish": "docs/launches"}` — no `voice`, so the macOS default speaks.
  For the browser smoke test a committed fixture page
  `tests/fixtures/launch-demo/index.html` (static, two or three
  interactive elements a step can click) and its storyboard
  `tests/fixtures/launch-demo/storyboard.json` are served by
  `python3 -m http.server` from that directory; Verify runs `render`
  against a throwaway config pointing `against` at that server and
  records, in those words, that this proves the recorder on a fixture.
  The `docs/launches/` directory is not a run-directory candidate
  (`knowledge_plane.run_dirs` walks `docs/`, `docs/features/*`,
  `docs/fixes/*` only), and its `launch.md` files are scanned by
  detectors C, D and I like any doc — which the copy survives by
  construction: it names no typed id, and in copy-only mode it links to no
  missing mp4.
- Collaborators: Verify (the two recordings); `tests/test_launch_demo.py`
  (the fixture storyboard doubles as the browser-grammar test input).

### Traceability (PRD-0009 success criteria → components)

- Terminal recorder, end to end → the terminal adapter, `assemble`, this
  repo's config; Verify records the run.
- Browser recorder, smoke-tested → the browser adapter, the fixture page
  and storyboard.
- Copy from artifacts, or from the pull request → SKILL.md steps (3)–(4)
  and the invocation contract's `--pr` path.
- Copy-only degradation → `probe`, `render`'s order of checks, the CLI
  contract (nothing written to the publish path in COPY-ONLY).
- A free voice, no key, no spend by default → the config's `voice` field
  and the voice command contract.
- Per-repo config, validated → `load` and its problem strings.
- Two triggers, Ship otherwise untouched → the Ship hook and the
  invocation contract; `skills/next/` untouched.
- A utility skill, on every roster → the roster and packaging entries.
- Stdlib only; tools are the consuming repo's → the tool component, the
  `cli.runner` edit, the stack list; the manifest regeneration.
- Battery → nothing here adds or removes a `make check` target; the three
  commands run unchanged.

## Data model

Five local shapes, each with one writer, chosen from who reads them and
when. Every read is a local file at invocation time — must-be-true when
written, nothing settles later — and the one write that must never be
half-visible (the mp4 at the publish path) lands by writing to the scratch
directory and `os.replace`-ing into place.

1. **The config** — `docs/launch-demo.json`, one JSON object, the
   consuming repo's. Written by a person once; read by `load` on every
   invocation. Fields and grammar (every absent or malformed field is a
   problem, except `voice`):

   | Field | Grammar | Meaning |
   |---|---|---|
   | `when` | `"ship"` or `"on-demand"` | whether Ship fires the skill |
   | `recorder` | `"terminal"` or `"browser"` | which adapter records |
   | `against` | non-empty string; for `browser`, starts with `http://` or `https://` | the shell vhs runs the steps in (`bash`, `zsh`, …), or the URL the browser opens first |
   | `voice` | optional; non-empty string containing `{out}` | the voice command: reads one line on stdin, writes a WAV at `{out}`; absent → `say --data-format=LEI16@22050 -o {out}` on macOS, `espeak-ng -w {out}` elsewhere |
   | `publish` | plain relative path, no `..`, inside the repo | the directory under which `<slug>/` is written |

   Not a `factory_config.ARTIFACT_HOMES` entry: it has one home, no
   payload twin, and no default a template could carry.

2. **The storyboard** — `<publish>/<slug>/storyboard.json`, written by the
   agent (or reused when already present), read by `check_storyboard`,
   `narrate` and `plan`:

   ```json
   {"title": "Launch demo",
    "tagline": "A launch brief nobody made by hand",
    "intro": "<one sentence from What it is>",
    "steps": [{"say": "<one sentence from What it does>",
               "do": ["python3 board.py"]}],
    "outro": "<one sentence from How it helps>"}
   ```

   `title` and `tagline` are free text for the title card. `intro`, every
   `say` and `outro` must each be a whitespace-normalised substring of
   `launch.md`'s body — the invariant that makes "every narration line is
   cut from the copy" a check rather than a hope, owned by
   `check_storyboard`. `do` is per recorder: for `terminal`, a list of
   shell commands typed one per line (may be empty: a step that narrates
   over the screen it has); for `browser`, one string of JavaScript
   statements run inside `async (page) => { … }` (may be empty). The
   storyboard holds no timing: durations come from the narration.

   **Happy-path precedence** (the agent's rule for writing `steps`): a
   storyboard already at the publish path is reused unchanged; else an
   executable path — an E2E test `verification.md` names, or the commands
   that verification ran for the feature; else `ux.md`'s primary flow;
   else `verification.md`'s evidence; else the pull request body's
   before-and-after evidence section. None → no storyboard, verdict
   COPY-ONLY, `video: none — no happy-path source (looked at: …)` in
   `launch.md`. The walkthrough is never guessed (idea.md's second risk).

3. **The plan** — in memory, from `plan(storyboard, seconds)`: scenes in
   order (title card, steps, outro), each with `hold = narration seconds +
   SETTLE` (title card at least `TITLE_SECONDS`), and for the terminal the
   computed offset of each scene (`Σ` of earlier holds and typing times,
   `len(command) × TYPING_SPEED` per typed command; hidden printing costs
   nothing, measured above) plus the tape text; for the browser the holds
   only, offsets arriving measured from the wrapper. Constants
   (`TITLE_SECONDS = 3`, `SETTLE = 0.5`, `TYPING_SPEED = 0.05`,
   `DRIFT_TOLERANCE = 1.5`, `1280×720`) are module constants of the tool.
   The same plan feeds the driver and the mux, so the two cannot disagree.

4. **The launch directory** — `<publish>/<slug>/`, the published brief:
   `launch.md` (frontmatter `launch:`, `date:`, `sources:` — the files or
   the PR it was written from — and `video:` naming `launch.mp4` or `none
   — <reason>`; then the three labelled sections), `storyboard.json`, the
   generated driver (`demo.tape` or `demo.mjs`, written by the tool from
   the plan so a reader sees what ran, and for the browser so Node's
   package resolution walks up from inside the repo to `node_modules/
   playwright`), and `launch.mp4`. Intermediates — narration WAVs, the raw
   recording, `marks.json` — live in a `tempfile.mkdtemp` directory the
   tool names in its output and leaves for inspection. The mp4 is
   committed: a brief whose video exists only on the machine that made it
   has not removed the manual step, and the viewer this run can reach is
   the one at the in-repo path. A terminal recording at these settings is
   a few hundred kilobytes to a few megabytes; a repo that outgrows that
   adopts Git LFS through `.gitattributes`, which is invisible to a tool
   that writes a file.

5. **The release-log line** — one numbered entry in `release.md`, the
   tool's reason and verdict lines verbatim. Owner of the wording: the
   tool; Ship copies.

## Interfaces & contracts

### `launch_demo.load(root)` — the config contract

- Input: the repo root.
- Output: `(config, [])` with the parsed object, or `(None, problems)`.
  Absence is `(None, ["launch-demo: missing docs/launch-demo.json"])` on
  direct invocation; the Ship hook tests for the file first and treats
  absence as "do nothing". `cli.read_file`'s own strings pass through
  under the `launch-demo: ` label (`cannot read …`, `… is not valid
  JSON: …`, `… is not a JSON object`).
- Failure modes, one string per field, exact and pinned by tests through
  this function: `launch-demo: docs/launch-demo.json has no <field>` for
  each of `when`, `recorder`, `against`, `publish`; `… when must be
  "ship" or "on-demand"`; `… recorder must be "terminal" or "browser"`;
  `… against must be a non-empty string`; `… against must be an http(s)
  URL for the browser recorder`; `… voice must be a non-empty string
  naming {out}` (only when present); `… publish must be a plain relative
  path inside the repo`. Never a silent default except `voice`.

### `launch_demo.probe(config, which=shutil.which, run=…)`

- Input: a loaded config; `which` and a runner, injected.
- Output: `(missing, problems)` — `missing` is `[(name, purpose, how to
  install)]` over: `ffmpeg` and `ffprobe` (always); `vhs` (terminal);
  `node` and the `playwright` package (`node -e
  "require.resolve('playwright')"` from the repo root, timeout 30 s,
  browser); the voice command's first token. Prints one line per missing
  tool and the verdict `READY` or `COPY-ONLY`; exit 0 either way.
- Failure modes: none that are not "missing" — a probe cannot fail, only
  report. A Playwright browser that was never installed is not probeable
  and surfaces at record time as that adapter's failure.

### `launch_demo.check_storyboard(storyboard, copy_text, recorder)`

- Input: the parsed storyboard, `launch.md`'s body, the configured
  recorder.
- Output: problems, `[]` when conformant.
- Failure modes: `launch-demo: storyboard has no <field>` (`title`,
  `tagline`, `intro`, `steps`, `outro`); `… steps must be a non-empty
  list`; `… step N has no say`; `… step N do must be a list of commands`
  (terminal) / `… step N do must be a string` (browser); `… intro is not
  a sentence of launch.md`, `… step N narration is not a sentence of
  launch.md`, `… outro is not a sentence of launch.md`.

### The voice command (cross-process)

- Input: the template with `{out}` substituted by a `.wav` path in the
  scratch directory, split with `shlex` (no shell); the line on stdin.
- Output: a WAV at `{out}`, measured by `ffprobe` (timeout 30 s) to a
  duration in seconds.
- Failure modes: timeout 60 s per line; a `CLI_FAILURES` raise becomes
  `launch-demo: voice failed on line N: <cli.detail>`; a command that
  exits 0 and writes nothing is `launch-demo: voice wrote no file for
  line N`. Retry is safe (each run overwrites its own file); `render`
  does not retry — the invoker reruns.

### `record(plan, workdir, run)` — the recorder seam, two adapters

- Input: the plan, the scratch directory, the adapter's runner.
- Output: `(raw video path, offsets)` — offsets in seconds, one per
  scene, where that scene's narration starts.
- **Terminal adapter** (`vhs`): writes `demo.tape` from the plan —
  `Output`, `Set Shell <against>`, size, font, `Set TypingSpeed`; per
  scene `Hide`, `Type` a `clear; printf` that prints the bold title and
  tagline (title card), the dim caption line (a step), or the outro line,
  `Enter`, `Show`, then the step's commands typed and entered, then
  `Sleep <hold>` — and runs `vhs demo.tape` with the repo root as cwd,
  timeout 600 s. Offsets are the plan's computed ones; after recording
  the raw duration is probed and `|recorded − planned| >
  DRIFT_TOLERANCE` is `launch-demo: recording ran X s where the plan
  expected Y s — narration would drift` (no mp4: an out-of-sync video is
  worse than none, idea.md's unattended-quality risk). vhs needs ttyd; a
  missing one is vhs's own stderr through `cli.detail`.
- **Browser adapter** (Playwright): first a reachability check — an HTTP
  `HEAD` of `against`, timeout 5 s, any HTTP status counts as reachable,
  a connection failure or timeout is the verdict COPY-ONLY with
  `launch-demo: against <url> is unreachable: <reason>` (idea.md's first
  risk, said out loud). Then writes `demo.mjs` from the plan — imports
  `chromium` from `playwright`, launches headless, a context with
  `recordVideo` at 1280×720, opens the tool-written `title.html` for the
  title-card hold, `goto(against)`, then per step sets the caption bar
  (re-applied on every document load, so a navigating step keeps it),
  runs the step's `do`, waits its hold, and at the end opens `outro.html`;
  it records `Date.now()` at page creation and at every scene start into
  `marks.json`, closes the context, and moves the webm to `raw.webm` —
  and runs `node demo.mjs` with the repo root as cwd, env carrying
  `LAUNCH_DEMO_AGAINST` and `LAUNCH_DEMO_WORK`, timeout 600 s. Offsets are
  the measured marks. A missing browser binary, a selector a `do` cannot
  find, or a script error is Playwright's own last stderr line as
  `launch-demo: browser recorder failed: <cli.detail>`.
- Failure modes common to both: timeout → problem; retry safe (scratch is
  fresh per run, the publish path untouched until assembly succeeds).
  Production plus a test double exist for each adapter (fake runners that
  write the files the adapter expects), and the two real adapters make
  the seam real.

### `assemble(raw, clips, offsets, out, run)` — ffmpeg and ffprobe

- Input: the raw recording, the narration WAVs with their offsets, the
  destination.
- Output: `launch.mp4` — one H.264 video stream (`yuv420p`, 30 fps) and
  one AAC audio stream assembled with one `adelay` per clip into one
  `amix`, `+faststart`, duration that of the raw recording — written to
  scratch and `os.replace`d into the publish directory; then the
  `ffprobe -show_entries stream=codec_type,codec_name:format=duration`
  summary printed for Verify to paste.
- Failure modes: timeout 600 s (ffmpeg) / 30 s (ffprobe); `launch-demo:
  ffmpeg failed: <cli.detail>` and no file at the publish path — never a
  partial mp4; a result ffprobe cannot read is the same problem with
  ffprobe's line. Retry safe.

### `python3 launch_demo.py config | probe | render <slug>` — the CLI

- Input: run from the repo root (cwd is the root; the recorders and
  Node's module resolution depend on it, as `board.py` depends on its
  working directory). `render` reads `<publish>/<slug>/launch.md` and
  `storyboard.json`.
- Output: stdout lines prefixed `launch-demo: ` (what was written, the
  scratch path, the ffprobe summary, each missing tool), then the verdict
  word alone — `READY`/`COPY-ONLY` for `probe`, `PRODUCED`/`COPY-ONLY` for
  `render` — then `cli.report`'s `launch-demo: N problem(s)` as the last
  line; exit 0 with a verdict, 1 with problems, 2 for unrecognised argv
  (`tests/cli_contract.ReportContract` pins the epilogue).
- Failure modes: `render` runs `check_storyboard` and `probe` first, so a
  bad storyboard is problems before any tool runs and a missing tool is
  COPY-ONLY before any tool runs; in COPY-ONLY nothing is written to the
  publish path — `launch.md` is already the agent's, and the PRD's `ls`
  shows it alone.

### The skill's invocation contract

- Input: a feature reference — a run directory or slug under
  `docs/features/` (the one active run when none is named), or `--pr <n>`
  for a feature that shipped from a bare pull request (slug: a kebab-case
  cut of the PR title, recorded as `pr: #<n>` in `launch.md`).
- Output: the launch directory populated as far as the verdict allows,
  and a report ending in the tool's verdict line.
- Failure modes: no config → stop with the tool's missing-config line;
  config problems → stop, quote them; no happy-path source → COPY-ONLY
  with the reason in `launch.md`; `render` problems → quote them, leave
  `launch.md`. The skill never writes a placeholder video, never edits an
  existing storyboard, and never commits — the invoker (Ship, or a person)
  commits.

## Stack & dependencies

- Python 3 standard library for `launch_demo.py` and the `cli.py` edit —
  the repo's rule (`stdlib-only`); `urllib.request`, `shlex`, `shutil`,
  `tempfile`, `json`, `subprocess` through `cli.runner`.
- vhs (with ttyd) — the terminal recorder; the consuming repo's, invoked
  as a CLI; chosen because it renders text natively and its tape timing
  is deterministic enough to compute offsets from.
- Playwright on Node — the browser recorder, through its built-in
  `recordVideo`; the consuming repo's package; chosen over driving a
  browser from Python because the repo may not have Python Playwright and
  this repo ships no third-party Python.
- ffmpeg + ffprobe — transcode, pad, mux, measure; the consuming repo's.
  Required capabilities: `libx264`, `aac`, `adelay`, `amix` — present in
  the owner's slim build; no text filter required, by design.
- `say` (macOS) / `espeak-ng` (Linux) — the free local default voices; any
  command fitting the stdin→`{out}` contract replaces them. No network, no
  key, no hosted endpoint named anywhere in skill or tool.
- Each external dependency is the cheap kind by the canon's test: a
  binary behind one `runner` call and one problem string, none of whose
  types reach any signature.

## Decisions & alternatives

- **`docs/launch-demo.json`, its own file** over a `launch_demo` block in
  `factory.json` — the stamp is not a precondition of recording a demo
  (a plugin-only repo has no `factory.json`), this repo reads its own
  `factory.json` from the template payload that every stamped repo
  inherits, and the dispatch plane's routing truth (ADR-0004, ADR-0037)
  should not carry a video recorder's settings; `docs/` is the one
  directory every pipeline repo has and already holds machine-read
  non-artifacts (`docs/standards.json`, `docs/backlog.md`).
- **Tool at the plugin root, not mirrored** over an entry in
  `factory_init.MIRRORS` — the skill invokes it from the plugin checkout
  exactly as `pipeline-board` invokes `board.py` (ADR-0062); a stamped
  copy would serve only CI-event triggers, which are out of scope, and
  would ship a tool no stamped workflow runs to every product repo. The
  manifest is regenerated anyway (`protocol.py`, `cli.py`, the version).
- **The recorder renders the on-screen text** over ffmpeg `drawtext` /
  burned subtitles — the owner's ffmpeg has neither filter, and requiring
  a differently built ffmpeg would make the PRD's own first criterion
  fail on the machine it names; each recorder draws text natively and
  well.
- **Narration is the clock; offsets computed for vhs, measured for the
  browser** over one mechanism for both — vhs exposes no marks, Playwright
  exposes no deterministic timing; each adapter answers the seam's one
  question the way it can, and a drift check guards the computed one.
- **The storyboard carries actions and the tool writes the driver** over
  the agent writing a raw tape or script — one committed source of
  truth, pacing the tool can compute, and a grammar small enough to test;
  the cost is that a terminal step is "commands typed one per line",
  which is what a CLI happy path is.
- **The mp4 is committed** over an ignored directory — a video nobody but
  its maker can open is the manual step un-removed; LFS is the growth
  lever and costs this design nothing.
- **COPY-ONLY exits 0 as a verdict** over a nonzero exit — the copy was
  produced, which is the invocation's guaranteed output, and the repo's
  verdict tools already draw the line at "nonzero means misconfiguration"
  (`budget_guard`, `cost_report`); Ship reads the word, not the code.
- **espeak-ng as the Linux default** over Piper — one distribution
  package, no model to download and no model to choose on the repo's
  behalf; Piper sounds better and is one `voice` line away.
- **`cli.runner` gains `timeout` and `input`** over a tool-private
  runner — a second runner is a second owner of the one subprocess
  adapter (ADR-0037, ADR-0051's one-owner direction); the extension is
  additive and every existing caller is unchanged.
- **Hook before the release mechanism** over after it — the brief must be
  in the pull request the owner watches before merging; a failed release
  then leaves a brief for an unreleased feature, which the release log
  records like any other hiccup.
- **"Around a pull request" card** over a seventh card — the brief rides
  in the PR and sits by the review–ship stretch where that card already
  is; a new card is a larger figure edit for one row.
- **Three parts to three scenes** over free-form narration — the copy's
  labelled parts give the storyboard its shape and the check its rule;
  the agent chooses sentences, not structure.

## ADRs

One proposed, not written — `docs/adr/` is a human merge gate here, so the
implementer opens it as its own change for the owner to accept or reject:

**A skill that drives the consuming repo's toolchain runs a shipped tool,
configured from `docs/`.** ADR-0062 let a skill earn a tool for one reason
— it states a fact a seam already owns. This adds a second: a skill whose
work is invoking the consuming repo's external CLIs under `cli.py`'s
adapter conventions earns a tool, because a validated config with exact
problem strings and recorders exercised through injected fake runners
exist only as code; prose cannot be tested that way. Such a tool rides
with the plugin checkout and is invoked relative to the skill's directory
(the `board.py` shape), is not mirrored into stamped repos unless a
stamped workflow runs it, and reads its per-repo settings from one file at
`docs/<skill>.json`, read through `cli.read_file` with absence a fact —
never from `factory.json`, whose shape is the dispatch plane's. It meets
the bar: hard to reverse once consuming repos carry the config file,
surprising beside ADR-0062's "deliberately narrow" clause, and a real
trade-off against the prose-only shape every other skill has.
