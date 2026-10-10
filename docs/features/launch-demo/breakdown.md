---
stage: decompose
run: feature:launch-demo
date: 2026-10-08
assumptions:
  - "The cut was not reviewed live (skill step 5): five milestones and the S/M/L sizes are this stage's reading of architecture.md — the roster row L, the tool's function rows M, the config file, plan, fixture, hook and close-out S."
  - "Test-first runs inside each Python row, not as a separate red row: tests first, red recorded, then green, so lint, gates and the suite are green at every row boundary."
  - "The roster entries, the manifest regeneration and the 0.4.0 bump land in one row (0108): any one alone turns lint red (an unregistered skills/ directory, an orphan README or LEDGER row, an eval case expecting an unregistered slug)."
  - "Where the architecture names a function's inputs and outputs but not its parameters or a value, the rows fix one so a test can pin it (narrate, the adapters taking `against`, render, main, the constants, the printed line shapes); each reading is dated under Notes. Taken without user input."
  - "demo.mjs takes `against` and the scratch directory as positional arguments, not environment variables: cli.runner has no env parameter and the seam edit asked for is timeout and stdin only. Taken without user input."
  - "tests/fixtures/launch-demo/ also carries launch.md, the copy its storyboard quotes: check_storyboard holds every narration line to the copy and the architecture names no other copy for the fixture."
  - "Check-offs follow the owner-session ledger policy (readme-skill-map and pocock-1-3-takeaways breakdowns; ADR-0069): each appends one zero-cost row via python3 budget_guard.py record, run_id session-2026-10-08-wo-NNNN, model claude-fable-5-1, 0 tokens, 0.0 cost, outcome owner-session:unmetered — the rows are worked by this session, no dispatched agent."
  - "Rows 0112 and 0113 (resumed after Verify, 2026-10-10) follow the same owner-session ledger policy with run_id session-2026-10-10-wo-NNNN and model claude-opus-5-5 — the model that actually worked them, not the earlier rows' claude-fable-5-1. Taken without user input."
  - "Row 0125 (resumed after re-verification's Failure 5, 2026-10-10) is a new row, not a reopening of row 0113: 0113's acceptance was met as written and its test was the wrong one, so the correction is tracked as its own row like 0111. Its id skips 0114–0124, which branch docs/docs-audit's breakdown already holds (ids are repo-global across branches). Same owner-session ledger policy, run_id session-2026-10-10-wo-0125, model claude-opus-5-5. Taken without user input."
  - "Row 0125 leaves test_a_node_failure_with_no_error_line_keeps_the_last_line as it was: its stderr `node: bad option: --nope` now matches the widened rule (a flush-left name, then `: `) and so reaches the same reason through the error-line branch rather than cli.detail's fallback. The outcome is unchanged and the line is an error message; the fallback branch is still taken by a stderr with no such line (`boom`), though no test now asserts that branch's reason. Logged, not edited (surgical scope); a follow-up for Review. Taken without user input."
  - "The proposed ADR is no row: architecture.md's ADRs section has the implementer open it as its own change for the owner, so Operate seeds it."
---

# Breakdown: Launch demo

Progress lives in the checkboxes below — Implement checks items off as
their acceptance criteria are met. Rows follow the house grammar: a
repo-global work-order id (continuing from 0096), size class, blocking
edges, and the PRD citation. No tracker mirror for this run (the brief
rules out any tracker interaction; the checkboxes are the state,
ADR-0026). Reconciled against `architecture.md` on 2026-10-08: every
component it names lands in a row below, and every PRD-0009 success
criterion is covered by at least one Accept paragraph; the Coverage
section at the end says which. Each Python row writes its tests before
its code and records the red, and the skill's roster entries land in one
commit, so every commit on the branch stays lint-, gates- and
suite-green. Rows are referred to below by their number alone (row 0097)
so that no line outside a checkbox row carries a work-order token.

Every row's check-off appends one zero-cost ledger row (frontmatter
assumptions; the Notes entry of 2026-10-08 below), which is what keeps
detector G green as rows are checked.

## Milestone 1: The tool reads its config and names what is missing

- [x] **WO-0097** cli.runner gains timeout and stdin; TimeoutExpired joins the vocabulary — size:S, blocked by: — (PRD-0009 §Success criteria)
  - Accept: `tests/test_cli.py` gains, before `cli.py` is touched, tests asserting through the public seam alone: `TestRunner` — `cli.runner("bash", timeout=0.5)(["-c", "sleep 5"])` raises `subprocess.TimeoutExpired` and that exception is caught by `except cli.CLI_FAILURES`; `cli.runner("cat")([], input="hello\n")` returns a CompletedProcess whose `stdout` is `hello\n`; the two existing `TestRunner` tests are untouched and still pass. `TestDetail` — `cli.detail(subprocess.TimeoutExpired(["vhs"], 600, stderr=b"ttyd: not found\n"))` is the str `ttyd: not found`, never a bytes repr (observed in this worktree before the edit, Python 3.14.6: `cli.detail` answers `b'oops'` for a timed-out child that wrote stderr, because `subprocess.run` attaches the undecoded stderr to the exception). Observed red: `python3 -m unittest tests.test_cli` fails exactly the three new tests (`TypeError` on the unknown keywords, `AssertionError` on the bytes) and nothing else — write the output to a file and grep it for `FAILED` and `ERROR`. Then `cli.py`: `runner(binary, timeout=None)` returns `run(args, input=None)` that passes both through to `subprocess.run` as `timeout=timeout, input=input`; `CLI_FAILURES` becomes `(subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError)` with its comment widened by one clause; `detail` decodes a bytes `stderr` (`decode("utf-8", errors="replace")`) before stripping and taking the last line; `_gh = runner("gh")` and `gh_runner` are byte-identical (`git diff main -- cli.py` touches the three definitions and the module docstring's one new sentence, nothing else). `python3 factory_init.py update-manifest` is run in the same commit so `factory/templates/tools/factory/cli.py` and `factory/manifest.json` follow (`python3 gates.py` prints `gates: 0 problem(s)`; `python3 -m unittest tests.test_factory_init` prints `OK`). `python3 -m unittest discover tests` prints `OK`; `python3 lint.py` prints `lint: 0 problem(s)`.
- [x] **WO-0098** launch_demo.load and probe, and the config and probe CLI legs — size:M, blocked by: WO-0097 (PRD-0009 §Success criteria)
  - Accept: `tests/test_launch_demo.py` is written first, against a module that does not exist (observed red: every test errors with `ModuleNotFoundError`, every other suite passes). Its fixture is a `tempfile` root carrying `docs/launch-demo.json`; its fake runners are a factory class whose `__call__(self, binary, timeout=None)` returns a callable whose `__call__(self, args, input=None)` records `(binary, timeout, args, input)` and answers a scripted `subprocess.CompletedProcess` or raises a scripted `CLI_FAILURES` member — neither signature is `(self, args)`, so `tests/test_fake_gh.py`'s one-fake rule does not read them as gh fakes (`python3 -m unittest tests.test_fake_gh` prints `OK` after the file exists). Through `launch_demo.load(root, platform=sys.platform)` → `(config, problems)` it pins the exact strings, each prefixed `launch-demo: `: no file → `(None, ["launch-demo: missing docs/launch-demo.json"])`; bytes that are not JSON → one string starting `launch-demo: docs/launch-demo.json is not valid JSON:`; a top-level array → `launch-demo: docs/launch-demo.json is not a JSON object`; an object with no fields → exactly four strings in this order, `launch-demo: docs/launch-demo.json has no when`, `… has no recorder`, `… has no against`, `… has no publish` (the ellipsis stands for the same prefix throughout this row; `voice` absent is no problem); `"when": "always"` → `launch-demo: docs/launch-demo.json when must be "ship" or "on-demand"`; `"recorder": "gif"` → `… recorder must be "terminal" or "browser"`; `"against": ""` or a number → `… against must be a non-empty string`; `"recorder": "browser"` with `"against": "bash"` → `… against must be an http(s) URL for the browser recorder`; `"voice": "say -o out.wav"` (no `{out}`) or `"voice": ""` → `… voice must be a non-empty string naming {out}`; `"publish": "/tmp/x"`, `"publish": "../x"` and `"publish": ""` each → `… publish must be a plain relative path inside the repo`; a valid file with no `voice` → `config["voice"]` is `say --data-format=LEI16@22050 -o {out}` when `platform` is `darwin` and `espeak-ng -w {out}` otherwise, every other field verbatim, `problems == []`; a valid file with `voice` set keeps it. Through `launch_demo.probe(config, which, runner)` → `(missing, problems)`, `which` a fake name→path-or-None: a terminal config with everything present → `([], [])`; `ffmpeg` and `ffprobe` absent → two entries whose first elements are `ffmpeg` and `ffprobe`, each a three-tuple `(name, purpose, how to install)` of non-empty strings; a terminal config probes `vhs` and never `node`; a browser config with `node` present runs the factory with `("node", PROBE_TIMEOUT)` and args `["-e", "require.resolve('playwright')"]`, a `CalledProcessError` from that run adds `playwright` to missing, and `node` absent adds `node` and does not run it; the voice command's first token (`shlex.split(config["voice"])[0]`) is probed by `which` and its absence is an entry named by that token; `problems` is `[]` in every case. Through `launch_demo.main(argv, root=…, which=…, runner=…, platform=…)` with `tests/cli_contract.CliContract` (`usage_fragment` `python3 launch_demo.py config | probe | render`) and `ReportContract` (`summary_line` `launch-demo: 0 problem(s)`): `["config"]` on a valid file prints `launch-demo: 0 problem(s)` alone and returns 0; on an invalid one prints each problem then `launch-demo: N problem(s)` with the computed count and returns 1; `["probe"]` prints one line per missing tool in the shape `launch-demo: missing ffmpeg — ` then the purpose, then `; install: ` then the hint (the tuple's second and third elements, the only free parts of the line), then the verdict word alone, `READY` when nothing is missing and `COPY-ONLY` otherwise, then the summary line, and returns 0 either way; a missing config makes `probe` print the missing-config line and the summary and return 1; `["nonsense"]` prints usage and returns 2. Then `launch_demo.py` exists at the repo root beside `board.py`, imports only the standard library and `cli` (`python3 -c "import ast,sys; t=ast.parse(open('launch_demo.py').read()); print(sorted({(n.names[0].name if isinstance(n, ast.Import) else n.module).split('.')[0] for n in ast.walk(t) if isinstance(n,(ast.Import,ast.ImportFrom))}))"` prints a list whose only non-stdlib name is `cli`), reads the config through `cli.read_file(root / "docs" / "launch-demo.json", "docs/launch-demo.json", dict)` and prefixes its strings, carries the module constants `TITLE_SECONDS = 3`, `SETTLE = 0.5`, `TYPING_SPEED = 0.05`, `DRIFT_TOLERANCE = 1.5`, `WIDTH = 1280`, `HEIGHT = 720`, `PROBE_TIMEOUT = 30`, `VOICE_TIMEOUT = 60`, `RECORD_TIMEOUT = 600`, `FFMPEG_TIMEOUT = 600`, `HEAD_TIMEOUT = 5`, and ends `if __name__ == "__main__": sys.exit(main(sys.argv[1:]))`. Every test above is green with no test edited; `python3 -m unittest discover tests` prints `OK`, `python3 lint.py` prints `lint: 0 problem(s)`, `python3 gates.py` prints `gates: 0 problem(s)` (the tool is not mirrored: `factory_init.MIRRORS` is untouched, and `factory_config.py` is untouched — the config is no `ARTIFACT_HOMES` entry; `git diff main -- factory_init.py factory_config.py` is empty).
- [x] **WO-0099** This repo's docs/launch-demo.json — size:S, blocked by: WO-0098 (PRD-0009 §Success criteria)
  - Accept: `docs/launch-demo.json` exists with exactly `{"when": "ship", "recorder": "terminal", "against": "bash", "publish": "docs/launches"}` (four fields, no `voice`, so the macOS default speaks); from the repo root `python3 launch_demo.py config` prints `launch-demo: 0 problem(s)` and exits 0; `python3 launch_demo.py probe` prints zero or more `launch-demo: missing …` lines for whatever this machine lacks, then `READY` or `COPY-ONLY`, then `launch-demo: 0 problem(s)`, and exits 0 — the actual output is pasted under Notes, dated, naming which tools this machine had; `docs/launches/` is not created by this row. `python3 lint.py` prints `lint: 0 problem(s)` and `python3 gates.py` prints `gates: 0 problem(s)` (a JSON file under `docs/` is no run artifact and no scannable doc).

## Milestone 2: The storyboard is held to the copy and the clock is computed

- [x] **WO-0100** check_storyboard, the grammar and the verbatim-sentence rule — size:M, blocked by: WO-0098 (PRD-0009 §Success criteria)
  - Accept: tests first in `tests/test_launch_demo.py`, through `launch_demo.check_storyboard(storyboard, copy_text, recorder)` → problems, with a copy text of three short paragraphs and a conformant storyboard whose `intro`, one `say` and `outro` are sentences of it: the conformant storyboard yields `[]` for `terminal` (its `do` a list) and, with `do` a string, `[]` for `browser`; each of `title`, `tagline`, `intro`, `steps`, `outro` removed yields `launch-demo: storyboard has no title` (and so on, the field name substituted), in field order when several are missing; `"steps": []` and `"steps": "x"` each yield `launch-demo: storyboard steps must be a non-empty list`; a step without `say` yields `launch-demo: storyboard step 1 has no say` (steps numbered from 1); a terminal step whose `do` is a string yields `launch-demo: storyboard step 1 do must be a list of commands`, a browser step whose `do` is a list yields `launch-demo: storyboard step 1 do must be a string`, and a step with no `do` at all is conformant for both (an empty step narrates over the screen it has); an `intro` not in the copy yields `launch-demo: storyboard intro is not a sentence of launch.md`, a `say` not in the copy yields `launch-demo: storyboard step 2 narration is not a sentence of launch.md`, an `outro` not in the copy yields `launch-demo: storyboard outro is not a sentence of launch.md`; the comparison is whitespace-normalised on both sides (`" ".join(text.split())`), so a sentence wrapped across two lines in the copy matches its one-line form in the storyboard, and a sentence differing by one word does not; a storyboard that is not a dict yields `launch-demo: storyboard is not a JSON object` alone. Observed red: each new test fails with `AttributeError` before the function exists. Then the function exists, is pure (no import of `subprocess`, `shutil` or `cli` reachable from it — it touches no file and runs nothing), and every test is green with none edited; the full battery is green.
- [x] **WO-0101** plan, the one owner of the timeline arithmetic — size:S, blocked by: WO-0100 (PRD-0009 §Success criteria)
  - Accept: tests first, through `launch_demo.plan(storyboard, seconds)` with `seconds` the narration durations in scene order (intro, each step, outro): for the storyboard `{"title": "T", "tagline": "G", "intro": "A.", "steps": [{"say": "B.", "do": ["python3 board.py"]}], "outro": "C."}` and `seconds = [2.0, 3.0, 1.0]` the plan's `scenes` are three dicts in order with `kind` `title`, `step`, `outro`, `say` `A.`, `B.`, `C.`, `do` `[]`, `["python3 board.py"]`, `[]`, `hold` `3.0` (the title card held to at least `TITLE_SECONDS` — `max(TITLE_SECONDS, 2.0 + SETTLE)`), `3.5`, `1.5` (narration plus `SETTLE`), and `offset` `0.0`, `3.0`, `7.3` (each scene's offset is the sum of every earlier scene's hold and typing time, a typed command costing `len(command) * TYPING_SPEED` — sixteen characters, `0.8`), with `planned` `8.8` (the last offset plus the outro's hold and typing); `seconds = [4.0, 3.0, 1.0]` gives the title card `hold` `4.5`; a step with `do` a string (the browser form) or an empty list adds no typing time; `len(seconds) != len(steps) + 2` raises `ValueError` (a caller slip, never a problem string); `title` and `tagline` are carried on the plan verbatim for the title card. Observed red: `AttributeError` before the function exists. Then the function exists and is pure — `python3 -c "import ast; t=ast.parse(open('launch_demo.py').read()); f=[n for n in t.body if isinstance(n, ast.FunctionDef) and n.name=='plan'][0]; print([n.id for n in ast.walk(f) if isinstance(n, ast.Name) and n.id in ('subprocess','shutil','cli','os')])"` prints `[]` — the only owner of these sums: `TYPING_SPEED` and `SETTLE` are read by `plan` and, after row 0103, by the tape header's `Set TypingSpeed` derivation, and nowhere else (`grep -n 'TYPING_SPEED\|SETTLE' launch_demo.py` lists the two definitions and those uses only); the full battery is green.

## Milestone 3: A terminal recording, narrated and muxed, under fake runners

- [x] **WO-0102** narrate, the voice command contract — size:M, blocked by: WO-0098, WO-0101 (PRD-0009 §Success criteria)
  - Accept: tests first, through `launch_demo.narrate(lines, voice, workdir, runner)` → `(clips, problems)` with the fake factory of row 0098: for `lines = ["A.", "B."]` and `voice = "say -o {out}"`, the fake records two runs on binary `say` with `timeout` `VOICE_TIMEOUT`, args `["-o", str(workdir / "line-1.wav")]` then `["-o", str(workdir / "line-2.wav")]` (the template split with `shlex` after `{out}` is substituted — no shell), and `input` `"A.\n"` then `"B.\n"`; when the fake `say` writes the file and the fake `ffprobe` (binary `ffprobe`, `timeout` `PROBE_TIMEOUT`, args `["-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(wav)]`) answers `2.0\n` then `3.0\n`, `clips` is `[(workdir / "line-1.wav", 2.0), (workdir / "line-2.wav", 3.0)]` and `problems` is `[]`; a `say` run that raises `CalledProcessError` with stderr `Voice not found\n` yields `(None, ["launch-demo: voice failed on line 1: Voice not found"])` and no second run; a `TimeoutExpired` from `say` yields the same shape with `cli.detail`'s text; a `say` run that exits 0 and writes nothing yields `(None, ["launch-demo: voice wrote no file for line 1"])`; an `ffprobe` that raises on line 2 yields `(None, ["launch-demo: voice failed on line 2: " + the last line of ffprobe's stderr])` — a WAV the measurer cannot read is a voice that produced nothing usable; a `voice` of `espeak-ng -w {out}` runs binary `espeak-ng`. Observed red: `AttributeError` before the function exists. Then the function exists, builds every argv with `shlex.split`, names no hosted endpoint or key variable (`grep -n -i -E 'api[_-]?key|elevenlabs|openai|polly|https?://' launch_demo.py` prints nothing — the reachability check of row 0107 compares scheme prefixes without writing a URL), and every test is green with none edited; the full battery is green.
- [x] **WO-0103** record_terminal, the tape, the vhs run and the drift check — size:M, blocked by: WO-0101, WO-0102 (PRD-0009 §Success criteria)
  - Accept: tests first, through `launch_demo.record_terminal(plan, workdir, against, runner)` → `(result, problems)` where `result` is `(raw video path, offsets)`: with the plan of row 0101 and `against = "bash"`, the function writes `workdir / "demo.tape"` whose first six lines are `Output ` followed by the absolute path of `workdir / "raw.mp4"`, `Set Shell bash`, `Set Width 1280`, `Set Height 720`, `Set FontSize 18`, `Set TypingSpeed 50ms` (the last derived from `TYPING_SPEED`, never a second literal), and then, per scene in order, a block of `Hide`, one `Type` line containing `clear; printf` and that scene's on-screen text (the title card: the plan's `title` and `tagline`; a step: its `say`; the outro: its `say`), `Enter`, `Show`, then for each command of a list `do` a `Type` line quoting the command verbatim followed by `Enter`, then `Sleep ` followed by the hold to one decimal and `s` (`Sleep 3.0s`, `Sleep 3.5s`, `Sleep 1.5s`); runs the fake on binary `vhs` with `timeout` `RECORD_TIMEOUT` and args `[str(workdir / "demo.tape")]`; then probes `workdir / "raw.mp4"` with the `ffprobe` duration argv of row 0102; when the fake `vhs` writes `raw.mp4` and the fake `ffprobe` answers `9.1\n`, `result` is `(workdir / "raw.mp4", [0.0, 3.0, 7.3])` — the plan's computed offsets — and `problems` is `[]`; an `ffprobe` answer of `11.0\n` (drift `2.2`, above `DRIFT_TOLERANCE`) yields `(None, ["launch-demo: recording ran 11.0 s where the plan expected 8.8 s — narration would drift"])`; a `vhs` run that raises `CalledProcessError` with stderr ending `ttyd: command not found` yields `(None, ["launch-demo: terminal recorder failed: ttyd: command not found"])`, and a `TimeoutExpired` the same shape with `cli.detail`'s text; nothing under the publish path is touched by this function (it knows no publish path). Observed red: `AttributeError` before the function exists. Then the function exists, every test is green with none edited, and the full battery is green.
- [x] **WO-0104** assemble, the one ffmpeg call and the ffprobe summary — size:M, blocked by: WO-0102 (PRD-0009 §Success criteria)
  - Accept: tests first, through `launch_demo.assemble(raw, clips, offsets, out, runner)` → `(summary, problems)`: with `raw = workdir / "raw.mp4"`, two clips at offsets `[0.0, 3.0]` and `out = publish / "demo" / "launch.mp4"`, the fake records one run on binary `ffmpeg` with `timeout` `FFMPEG_TIMEOUT` whose args contain, in order, `-y`, `-i` followed by `raw`, `-i` followed by each clip's WAV path in clip order, a `-filter_complex` string holding `adelay=0|0` and `adelay=3000|3000` (milliseconds, `round(offset * 1000)`), one `amix=inputs=2`, and a `scale`/`pad` to `WIDTH`×`HEIGHT`, then `-c:v libx264 -pix_fmt yuv420p -r 30 -c:a aac -movflags +faststart`, and whose last argument is the path of `workdir / "launch.mp4"` — never the publish path; when the fake `ffmpeg` writes that file, `out` exists afterwards (moved into place with `os.replace`, `out.parent` created if absent) and `workdir / "launch.mp4"` does not; the fake `ffprobe` (binary `ffprobe`, `timeout` `PROBE_TIMEOUT`, args `["-v", "error", "-show_entries", "stream=codec_type,codec_name:format=duration", str(out)]`) answers four lines and `summary` is those lines each prefixed `launch-demo: `, `problems` `[]`; an `ffmpeg` run that raises `CalledProcessError` with stderr ending `Unrecognized option 'nope'` yields `(None, ["launch-demo: ffmpeg failed: Unrecognized option 'nope'"])` and no file at `out`; a `TimeoutExpired` the same shape; an `ffprobe` that raises on the result yields `(None, ["launch-demo: ffmpeg failed: " + the last line of ffprobe's stderr])` and no file at `out` (the move happens only after the probe reads it). Observed red: `AttributeError` before the function exists. Then the function exists, every test is green with none edited, `grep -c 'drawtext\|subtitles' launch_demo.py` prints `0` (the recorder draws every word; ffmpeg draws nothing), and the full battery is green.
- [x] **WO-0105** render and the render CLI leg, the order of checks and the verdict — size:M, blocked by: WO-0100, WO-0101, WO-0102, WO-0103, WO-0104 (PRD-0009 §Success criteria)
  - Accept: tests first, through `launch_demo.render(root, config, slug, which, runner, head=None, scratch=None)` → `(verdict, lines, problems)` and through `main(["render", "demo"], …)`, with a fixture root whose config has `"publish": "out"` and a directory `out/demo/` holding `launch.md` (frontmatter, then three labelled sections) and `storyboard.json` cut from it: no `out/demo/launch.md` → `(None, [], ["launch-demo: missing out/demo/launch.md"])`; no `storyboard.json` → `["launch-demo: missing out/demo/storyboard.json"]`; a storyboard with a non-conformant line → `check_storyboard`'s strings, and the fake factory records no run at all (a bad storyboard is problems before any tool runs); every tool present but `vhs` absent from `which` → `("COPY-ONLY", ["launch-demo: missing vhs — …"], [])`, no run recorded, and `out/demo/` still holds exactly `launch.md` and `storyboard.json` (nothing is written to the publish path in COPY-ONLY); everything present → the fakes see, in this order, the `say` runs, their `ffprobe` measurements, the `vhs` run, its `ffprobe` duration probe, the `ffmpeg` run and the summary probe, and the answer is `("PRODUCED", lines, [])` where `lines` holds `launch-demo: scratch ` followed by the scratch directory's path, `launch-demo: wrote out/demo/demo.tape`, `launch-demo: wrote out/demo/launch.mp4`, then the summary lines, and `out/demo/` now holds `launch.md`, `storyboard.json`, `demo.tape` (the tape the recorder ran, copied from scratch) and `launch.mp4`; a `say` failure → `narrate`'s string, nothing written; a drift failure → `record_terminal`'s string, nothing written; an `ffmpeg` failure → `assemble`'s string, nothing written; the scratch directory (from `tempfile.mkdtemp(prefix="launch-demo-")` when `scratch` is None, else the path given) still holds `line-1.wav`, `raw.mp4` and `demo.tape` after a PRODUCED run — left for inspection, named in the output. The copy text handed to `check_storyboard` is `launch.md`'s body after its frontmatter block. Through `main`: `["render", "demo"]` prints each line, then the verdict word alone, then `launch-demo: 0 problem(s)`, returns 0; with problems prints them and `launch-demo: N problem(s)`, no verdict word, returns 1; `["render"]` without a slug prints usage and returns 2 (`CliContract` with `bad_argv = ("render",)` in a second contract class). Observed red: `AttributeError` before `render` exists and the usage test failing before `main` learns the leg. Then both exist, `render` reads nothing about the repo but the config and the slug directory, every test is green with none edited, and the full battery is green — `python3 -m unittest discover tests` prints `OK` with no real `say`, `vhs`, `ffmpeg` or `ffprobe` invoked (the fakes answer every call; a test machine with none of them installed passes).

## Milestone 4: The browser recorder, provable on a fixture

- [x] **WO-0106** The browser fixture page, its storyboard and its copy — size:S, blocked by: WO-0100 (PRD-0009 §Success criteria)
  - Accept: `tests/fixtures/launch-demo/index.html` exists — one static page, no external request (`grep -E 'https?://|<script src' tests/fixtures/launch-demo/index.html` prints nothing), with a heading, a button with `id="count"` that increments a number on click, and a text input with `id="name"` beside a button with `id="greet"` that writes a greeting into a paragraph with `id="out"`, all inline; `tests/fixtures/launch-demo/launch.md` exists with frontmatter `launch: fixture`, `date: 2026-10-08`, `sources: [tests/fixtures/launch-demo/index.html]`, `video: none — rendered by Verify into a throwaway publish directory`, then sections `## What it is`, `## What it does`, `## How it helps`, each two or three plain sentences about the fixture page and naming no element id; `tests/fixtures/launch-demo/storyboard.json` exists in the browser form — `title`, `tagline`, `intro` a sentence of the first section, two steps whose `say` are sentences of the second section and whose `do` are JavaScript strings over the page's ids (`await page.click('#count'); await page.click('#count');` and `await page.fill('#name', 'Ada'); await page.click('#greet');`), `outro` a sentence of the third — and `tests/test_launch_demo.py` gains one test that `check_storyboard` of the fixture storyboard against the fixture `launch.md`'s body (after its frontmatter) for `browser` is `[]` (this is the browser-grammar test input the architecture names); `python3 -m http.server --directory tests/fixtures/launch-demo 8765` serves the page (checked by hand once, result under Notes, dated); `python3 gates.py` prints `gates: 0 problem(s)` (nothing under `tests/` is a scannable doc). The full battery is green.
- [x] **WO-0107** record_browser, reachability, demo.mjs and the measured marks — size:M, blocked by: WO-0105, WO-0106 (PRD-0009 §Success criteria)
  - Accept: tests first, through `launch_demo.reachable(against, head)` → `(True, None)` or `(False, reason)`, `head` an injected callable `(url, timeout) -> status or raise`: a `head` answering 200 → `(True, None)`; one answering 404 → `(True, None)` (any HTTP status counts); one raising `urllib.error.URLError("Connection refused")` → `(False, "Connection refused")`; one raising `TimeoutError` → `(False, "timed out after 5 s")`; the default `head` opens an HTTP `HEAD` through `urllib.request` with `timeout=HEAD_TIMEOUT` and is not exercised by the suite. Through `launch_demo.record_browser(plan, workdir, against, runner)` → `(result, problems)` with a browser plan of two steps (string `do`s, four scenes): the function writes `workdir / "title.html"` and `workdir / "outro.html"` (the title card and the outro, 1280×720, dark, the plan's `title`/`tagline` and the outro `say` as text) and `workdir / "demo.mjs"` whose text contains `import { chromium } from "playwright"`, `recordVideo`, `width: 1280`, `height: 720`, `process.argv[2]` and `process.argv[3]` (the URL and the scratch directory, read from argv, no `process.env`), `title.html`, every step's `do` string verbatim inside an `async (page) =>` wrapper, every `say` as a JSON-escaped caption string, an init script that re-adds the caption bar on every document load, `Date.now()` marks written to `marks.json`, and `outro.html`; runs the fake on binary `node` with `timeout` `RECORD_TIMEOUT` and args `[str(workdir / "demo.mjs"), against, str(workdir)]`; when the fake writes `workdir / "raw.webm"` and `workdir / "marks.json"` as `[1000, 1000, 4100, 8300, 12000]` (page creation, then each scene start, in ms), `result` is `(workdir / "raw.webm", [0.0, 3.1, 7.3, 11.0])` — measured offsets, not the plan's — and `problems` `[]`; a `node` run that raises `CalledProcessError` with stderr ending `Error: browserType.launch: Executable doesn't exist` yields `(None, ["launch-demo: browser recorder failed: Error: browserType.launch: Executable doesn't exist"])`; a `marks.json` with fewer marks than scenes plus one yields `(None, ["launch-demo: browser recorder failed: marks.json has 3 marks for 4 scenes"])`. Through `render` with a browser config (`"against": "http://127.0.0.1:8765"`), a `head` raising `URLError` → `("COPY-ONLY", ["launch-demo: against http://127.0.0.1:8765 is unreachable: Connection refused"], [])` with no narration run and nothing written; a reachable `head` and the fakes → `PRODUCED`, the driver copied to the slug directory as `demo.mjs`, `assemble` called with the measured offsets, the `ffmpeg` args naming `raw.webm`. Observed red: `AttributeError` before the functions exist. Then they exist, `render` picks the adapter by `config["recorder"]` and runs `reachable` only for `browser`, after `probe` and before `narrate`; every test is green with none edited; the full battery is green. The real run against the served fixture is Verify's (PRD-0009's second criterion), recorded there in the PRD's words.

## Milestone 5: The skill exists on every roster and Ship fires it

- [x] **WO-0108** The launch-demo skill and its roster entries, in one commit — size:L, blocked by: WO-0105, WO-0107 (PRD-0009 §Success criteria)
  - Accept: one commit lands all of the following, because each alone turns lint red. `skills/launch-demo/SKILL.md` exists with frontmatter `name: launch-demo` and a `description:` that is a bare YAML scalar (no `: `, no ` #`, no leading indicator, under 1024 characters — `python3 -c "import protocol, pathlib; print(protocol.skill_frontmatter_problems(pathlib.Path('.'), 'launch-demo'))"` prints `[]`), names the two halves (plain copy; a short narrated mp4), the two recorders, the per-repo `docs/launch-demo.json`, the copy-only degradation, the two triggers, and says in one clause that it is not `ship` (ship releases; this records what a release shipped); its body works the architecture's seven steps in order — run `config` and stop on problems; run `probe` and note READY or COPY-ONLY; read the sources (`prd.md`, `verification.md`, `release.md` for a run directory — the one active run when none is named, by the protocol's run discovery — else, for `--pr N`, the pull request's title and body through the forge CLI (`gh pr view N --json title,body`) and the changelog entry naming it when the repo keeps one); write the slug directory's `launch.md` (frontmatter `launch:`, `date:`, `sources:` listing the files or `pr: #N`; the three labelled sections `## What it is`, `## What it does`, `## How it helps`, in plain words, naming no path, function or identifier); find the happy path by the precedence as written (an existing storyboard at the publish path reused unchanged, then an E2E test `verification.md` names or the commands it ran, then `ux.md`'s primary flow, then `verification.md`'s evidence, then the pull request's before-and-after evidence section) and with none stop, writing `video: none — no happy-path source (looked at: …)` and printing `COPY-ONLY`; write `storyboard.json` with every `intro`, `say` and `outro` a verbatim sentence of `launch.md`; run the tool's `render` leg with the slug from the repo root, naming the tool by path relative to the skill's own directory (`../../launch_demo.py`, as `pipeline-board` names `board.py`), report its reason and verdict lines and the paths written, and finish `launch.md`'s `video:` line from the verdict (`launch.mp4` on PRODUCED, otherwise `none — ` followed by the tool's reason line); it states that it never writes a placeholder video, never edits an existing storyboard, never commits, and names no harness tool (the tool is named by path relative to the skill's directory, as `pipeline-board` names `board.py`). `skills/launch-demo/references/brief-grammar.md` exists and the skill names it as `references/brief-grammar.md`; it carries the five-field config table with each field's grammar, the voice swap (any command reading one line on stdin and writing a WAV at `{out}`; its key is its own, outside this config; the two free defaults), the storyboard grammar per recorder (`do` a list of commands typed one per line, or one string of statements inside `async (page) => { … }`, either may be empty), the happy-path precedence, and the three-parts-to-three-scenes rule; no `TEMPLATE.md` exists in the directory. `protocol.UTILITY_SKILLS` gains `"launch-demo"` between `"interactive-architecture-diagram"` and `"mermaid"` (the list is alphabetical). `README.md`'s utility table gains one row whose Skill cell is `launch-demo` in backticks, whose Moment cell is `Around a pull request` as plain text, and whose Why cell is one line distilled from the description naming the copy and the narrated video, placed directly after the `address-pr-review` row; nothing else in `README.md` changes (`git diff main -- README.md` is that one added line). `docs/assets/skill-map.svg`'s "Around a pull request" card grows one row: the two rects at `x="48" y="380"` go from `height="48"` to `height="64"`, and `<text class="row mono" x="60" y="434">launch-demo</text>` follows the `address-pr-review` line (`git diff main -- docs/assets/skill-map.svg` is those three lines; the card now ends at y 444, clear of the `Drawing pictures` card at 496). `LEDGER.md` gains `| launch-demo | draft | — | — |` after the `automate` row. `.claude-plugin/plugin.json`'s description parenthetical gains `launch-demo` between `interactive-architecture-diagram` and `mermaid`, and `version` is `0.4.0` (`git diff main -- .claude-plugin/plugin.json` touches those two lines only); `package.json` is untouched. `evals/routing.json` gains four cases and edits none (`git diff main -- evals/routing.json` is additive): `ld-1` `direct` expecting `launch-demo`, `ld-2` `situational` expecting `launch-demo`, `ld-vs-ship-1` `near-miss` expecting `launch-demo` with `notes` `adjacency: ship vs launch-demo` and a query asking for the launch video of a feature that already shipped, and `ship-vs-ld-1` `near-miss` expecting `ship` whose query says to ship it with pre-flight and rollback and never mentions a demo or video; no query contains the literal `launch-demo`. `python3 factory_init.py update-manifest` is run last in the row, so `factory/manifest.json`'s `version` is `0.4.0` and the `protocol.py` checksum follows (`python3 gates.py` prints `gates: 0 problem(s)`; `python3 -m unittest tests.test_factory_init` prints `OK`). `skills/next/SKILL.md` is untouched (`git diff main -- skills/next/` is empty; `tests.test_protocol_conformance`'s router test stays green). `python3 lint.py` prints `lint: 0 problem(s)` — `check_skills`, `check_skill_assets`, `check_plugin_skills`, `check_readme_skills`, `check_readme_no_orphans`, `check_readme_figure`, `check_ledger`, `check_ledger_no_orphans` and `check_evals` all pass with no checker edited; `python3 -m unittest discover tests` prints `OK`. The routing eval is not run (costs money; the LEDGER row stays `draft` with `—`).
- [x] **WO-0109** The Ship hook — size:S, blocked by: WO-0108 (PRD-0009 §Success criteria)
  - Accept: `skills/ship/SKILL.md` gains one numbered step, `**Launch brief.**`, between the Pre-flight step and the Release step; the steps after it renumber (Release 5, Post-release 6, Write the artifact 7, Hand off 8) with their text otherwise byte-identical (`git diff main -- skills/ship/SKILL.md` shows the new step and the four renumbered leading digits, nothing else); the step says, in its own words: if `docs/launch-demo.json` exists and its `when` is `ship`, load the `launch-demo` skill through the harness's skill-loading mechanism (a skill tool where one exists, otherwise a read of the skill file), run it for this run, commit what it wrote on the branch, and add one numbered Release-log entry quoting the tool's reason line(s) and verdict verbatim; with no config file, or any other `when`, do nothing and write nothing; and that the hook never blocks a release — a COPY-ONLY verdict and a problem exit are each one log line. The step contains neither the words `soft gate` nor the phrase `next stage is` and no backticked `.md` artifact name, so `lint.check_skill_recitals`' pins are unmoved; the `description:` line is byte-identical to main; `skills/ship/TEMPLATE.md` and `skills/next/` are untouched (`git diff main -- skills/ship/TEMPLATE.md skills/next/` is empty); `python3 lint.py` prints `lint: 0 problem(s)` (`check_skill_recitals` and `check_router` pass) and `python3 gates.py` prints `gates: 0 problem(s)`.
- [x] **WO-0110** Full battery and untouched surfaces — size:S, blocked by: WO-0097, WO-0098, WO-0099, WO-0100, WO-0101, WO-0102, WO-0103, WO-0104, WO-0105, WO-0106, WO-0107, WO-0108, WO-0109 (PRD-0009 §Success criteria)
  - Accept: on the branch tip, `python3 -m unittest discover tests` prints `OK`, `python3 lint.py` prints `lint: 0 problem(s)`, and `python3 gates.py && python3 gates.py --selftest` prints `gates: 0 problem(s)` and `selftest: ok` (each output written to a file and grepped); an import sweep over every Python file this run added or edited — `launch_demo.py`, `cli.py`, `protocol.py`, `tests/test_launch_demo.py` — finds only standard-library modules and this repo's own (`python3 -c "import sys, ast, pathlib; names={(n.names[0].name if isinstance(n, ast.Import) else n.module or '').split('.')[0] for p in ['launch_demo.py','cli.py','protocol.py','tests/test_launch_demo.py'] for n in ast.walk(ast.parse(pathlib.Path(p).read_text())) if isinstance(n,(ast.Import,ast.ImportFrom))}; print(sorted(n for n in names if n not in sys.stdlib_module_names))"` prints a list holding only `cli`, `launch_demo`, `protocol`, `cli_contract` and whatever else lives in this repo); `git diff main -- skills/` lists `skills/launch-demo/SKILL.md`, `skills/launch-demo/references/brief-grammar.md` and `skills/ship/SKILL.md` only; `git diff main -- skills/next/ skills/ship/TEMPLATE.md package.json Makefile factory/templates/tools/factory/gates.py` is empty; `git diff main --stat` lists only `cli.py`, `launch_demo.py`, `protocol.py`, `tests/test_launch_demo.py`, `tests/test_cli.py`, the three fixture files under `tests/fixtures/launch-demo/`, `docs/launch-demo.json`, `README.md`, `docs/assets/skill-map.svg`, `LEDGER.md`, `.claude-plugin/plugin.json`, `evals/routing.json`, `factory/manifest.json`, `factory/templates/tools/factory/cli.py`, `factory/templates/tools/factory/protocol.py`, the two skill files, `skills/ship/SKILL.md`, this run's artifacts under `docs/features/launch-demo/`, `docs/backlog.md` (the seed claimed at Idea) and `docs/factory/costs.jsonl` (the ledger rows the Notes policy owes), nothing else; `grep -rn -i -E 'elevenlabs|polly|openai|api[_-]?key' skills/launch-demo/ launch_demo.py` prints nothing; and every row above is checked.

## Milestone 6: What the first real run found

- [x] **WO-0111** The tape's Output path is quoted, and the test says so — size:S, blocked by: WO-0103 (PRD-0009 §Success criteria)
  - Accept: tests first — the tape test in `tests/test_launch_demo.py` (the one pinning `demo.tape`'s first six lines) is corrected to expect `Output "` followed by the absolute path of `workdir / "raw.mp4"` and a closing `"` as the first line: vhs 0.11.0 refuses the unquoted form the first pass pinned (`Expected file path after output`, `parser: 3 error(s)`, verification.md Failure 1), and a test asserting a value the real recorder refuses is a wrong test, so this corrects the test rather than bending it; observed red: `AssertionError` on line 1, `Output /…/raw.mp4` against `Output "/…/raw.mp4"`. Then `_tape` writes the quoted form, every test is green with none else edited, and a tape `_tape` produces for the committed `docs/launches/pipeline-board/storyboard.json`'s plan parses under the real vhs on this machine (`vhs validate <tape>` exits 0 with no parser line; the output quoted under Notes, dated). The full battery is green.
- [x] **WO-0112** Terminal offsets are measured from the recording, not read from the plan — size:M, blocked by: WO-0111 (PRD-0009 §Success criteria)
  - Accept: tests first, through `launch_demo.record_terminal(plan, workdir, against, runner)` with the plan of row 0101 (planned `8.8`, offsets `[0.0, 3.0, 7.3]`): a fake `ffprobe` answering `8.272\n` (94 % of the planned length) yields `result` `(workdir / "raw.mp4", [0.0, 2.82, 6.862])` — every planned offset scaled by the ratio recorded ÷ planned, rounded to three decimals — and `problems` `[]`; an answer of `8.8\n` yields the plan's offsets unchanged; an answer of `6.0\n` (a ratio of 0.68) yields `(None, ["launch-demo: recording ran 6.0 s where the plan expected 8.8 s — a ratio of 0.68, outside 0.75–1.25; narration would drift"])` and `12.0\n` (1.36) the same shape with its numbers; through `render` with row 0105's fakes, a raw duration of `20.0\n` against the planned `10.3` yields the problem `launch-demo: recording ran 20.0 s where the plan expected 10.3 s — a ratio of 1.94, outside 0.75–1.25; narration would drift` and nothing written. `DRIFT_BAND = (0.75, 1.25)` (both ends inclusive) replaces `DRIFT_TOLERANCE`; `plan` is unchanged (its offsets stay the planned ones — the adapter scales them, so the plan remains the one owner of the arithmetic and the adapter the one owner of the measurement); the seam's output shape `((raw, offsets), [])` is unchanged; `record_browser` and its tests are untouched. Observed red: `AssertionError` with the plan's offsets where the scaled ones are expected and the old `— narration would drift` string where the band string is expected. Then every test is green with none else edited; a dated Note records the deviation from the architecture's "offsets computed for vhs" wording and why, for Review. The full battery is green.
- [x] **WO-0113** The browser driver lives where Node can resolve Playwright, and a Node failure's reason names the error — size:M, blocked by: WO-0107 (PRD-0009 §Success criteria)
  - Accept: tests first, through `launch_demo.record_browser(plan, workdir, against, runner)` with row 0107's browser plan: the fake `node` run's first argument — the file Node ran — is a `demo.mjs` whose parent is a fresh `launch-demo-` directory directly under the current working directory (the repo root by the CLI contract, and the place `probe` resolves `playwright` from), neither under `workdir` nor under the system temp directory; its text at run time equals `workdir / "demo.mjs"` (the inspectable copy `render` publishes on success); the other two arguments are still `against` and `str(workdir)`; after the call, success or failure, that directory is gone and `workdir / "demo.mjs"`, `title.html` and `outro.html` remain; a `node` run raising `CalledProcessError` whose stderr is Node's real ESM failure (`node:internal/modules/package_json_reader:314`, the `throw new ERR_MODULE_NOT_FOUND(…)` line, `^`, a blank, `Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright' imported from /x/demo.mjs`, two `    at …` lines, `  code: 'ERR_MODULE_NOT_FOUND'`, `}`, a blank, `Node.js v22.22.3`) yields `(None, ["launch-demo: browser recorder failed: Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright' imported from /x/demo.mjs"])` — a string containing `ERR_MODULE_NOT_FOUND` and not `Node.js v`; the existing `Error: browserType.launch: Executable doesn't exist` case is unchanged; a stderr with no line that begins an error message (`node: bad option: --nope`) still yields `cli.detail`'s last line; `cli.detail` is not edited (`git diff -- cli.py` empty, no manifest change). Observed red: `AssertionError` on the driver's path (under `workdir`) and on the reason line (`Node.js v22.22.3`). Then every test is green with none else edited, and the resolution rule is shown on this machine with the real node against a throwaway package (an `.mjs` under the system temp directory cannot import it; the same file under the working directory can) — quoted under Notes, dated, with where the driver now lives and why. The full battery is green.

- [x] **WO-0125** A Node failure's reason names Playwright's bare error line, and the test holds the real stderr — size:S, blocked by: WO-0113 (PRD-0009 §Success criteria)
  - Accept: tests first — `test_a_failing_node` in `tests/test_launch_demo.py` is corrected to the real stderr of Playwright 1.64.0 under node v22.22.3 with its browser missing, captured on this machine and held verbatim as `NODE_BROWSER_MISSING` (absolute paths trimmed to `/x/…`): Node prints the uncaught error as its bare message, `browserType.launch: Executable doesn't exist at …`, with no `Error: ` prefix (verification.md Failure 5), and a test whose stderr invents that prefix is a wrong test, so this corrects the test rather than bending it; through `record_browser` it yields `(None, ["launch-demo: browser recorder failed: browserType.launch: Executable doesn't exist at /x/browsers/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell"])`. Observed red: `AssertionError`, `Node.js v22.22.3` where the `browserType.launch` line is expected. Then `NODE_ERROR_LINE` takes a flush-left `<name>[ [CODE]]: <message>` line, so the ESM case (`Error [ERR_MODULE_NOT_FOUND]: …`) and every other test stay green with none else edited, while `node:internal/…:123`, the `Node.js v…` banner and indented frames never match; `launch_demo.py` stays under 800 lines. Re-run for real on this machine: the missing-browser render's reason line, and a real ESM failure from a directory with no `node_modules` — quoted under Notes, dated. The full battery is green.

## Coverage

Architecture components to rows, by milestone: the `cli.runner` seam
edit (timeout, stdin, `TimeoutExpired` in the vocabulary, the manifest
regenerated with it) is row 0097; `launch_demo.py`'s `load`, `probe`,
the constants and the `config`/`probe` CLI legs are row 0098, this repo
as first consumer (`docs/launch-demo.json`) row 0099, `check_storyboard`
row 0100, `plan` row 0101, `narrate` (the voice command contract) row
0102, `record_terminal` row 0103, `assemble` row 0104, `render` and the
`render` leg with the verdict row 0105, the browser fixture (page,
storyboard, copy) row 0106, `reachable` and `record_browser` behind the
same `record` contract row 0107; `skills/launch-demo/SKILL.md` with
`references/brief-grammar.md`, and every roster and packaging entry
(`protocol.UTILITY_SKILLS`, the README row, the figure row, the LEDGER
row, `plugin.json`'s description and `0.4.0`, the four eval cases, the
manifest) are row 0108; the Ship hook is row 0109; the close-out row
0110 proves the battery and the untouched surfaces. Every file in the
architecture's tree-claims block is read or edited by a row: `cli.py`
and `tests/test_cli.py` (0097), `protocol.py`, `factory_init.py` and
`factory/manifest.json` (0097, 0108), `factory_config.py` (held
untouched by 0098: the config is no `ARTIFACT_HOMES` entry), `board.py` and `tests/test_fake_gh.py`
(read by 0098), `lint.py` and `gates.py` (run by every row),
`skills/ship/SKILL.md` and `skills/ship/TEMPLATE.md` (0109),
`skills/next/SKILL.md` (held untouched by 0108 and 0110),
`skills/pipeline-board/SKILL.md` (read by 0108 for the tool-naming
shape), `README.md`, `docs/assets/skill-map.svg`, `LEDGER.md`,
`.claude-plugin/plugin.json` and `evals/routing.json` (0108), `prd.md`
(cited by every row). The proposed ADR has no row (frontmatter
assumptions).

PRD-0009 Success criteria to Accept paragraphs:

- Terminal recorder, end to end — rows 0102 (narration), 0103 (the
  tape: title card, captions, outro, all drawn by the recorder), 0104
  (the mux) and 0105 (the verdict and what is written) build it under
  fake runners; row 0099 configures this repo; the real mp4 of one of
  this plugin's own skills, its `ffprobe` block, duration and title-card
  frame are Verify's record.
- Browser recorder, smoke-tested — rows 0106 (the committed fixture
  page, storyboard and copy) and 0107 (the adapter); the served-fixture
  run and its "proves the recorder on a fixture" sentence are Verify's.
- Copy from artifacts, or from the pull request — row 0108 (the skill's
  steps 3 and 4 and the `--pr` path); the two copies in fenced blocks are
  Verify's.
- Copy-only degradation — row 0098 (`probe` and the `probe` leg's
  verdict), row 0105 (nothing written to the publish path in COPY-ONLY;
  a missing tool is COPY-ONLY before any tool runs) and row 0107 (an
  unreachable URL is COPY-ONLY with its reason); the `ls` is Verify's.
- A free voice, no key, no spend by default — row 0098 (the two free
  defaults chosen by platform), row 0102 (the voice command contract;
  no endpoint or key in the tool), row 0108 (the reference documents the
  swap) and row 0110 (the grep over skill and tool).
- Per-repo config, validated — row 0098 (one exact string per field,
  pinned through `load`; `voice` the only default).
- Two triggers, Ship otherwise untouched — row 0109 (the hook; the
  template and the router untouched) and row 0108 (direct invocation
  with or without a run; `skills/next/` untouched), checked again by row
  0110's diffs.
- A utility skill, on every roster — row 0108 (every roster, no
  `TEMPLATE.md`, `0.4.0`, additive evals, the plugin diff two lines).
- Stdlib only; tools are the consuming repo's — rows 0097, 0098, 0102,
  0103, 0104 and 0107 (every CLI behind `cli.runner`, exercised with
  fake runners; no real recorder in the suite), row 0098 (the tool not
  mirrored, `MIRRORS` untouched) and row 0110 (the import sweep,
  detector E green).
- Battery — row 0110, with the per-row runs along the way.

## Design gaps found

None. Two wording gaps met in decomposition are readings, not missing
contracts, and are logged under `assumptions:` and dated under Notes for
Review: the recorder seam's stated inputs omit the config's `against`,
which both adapters need (the tape's `Set Shell`, the browser's first
navigation), so the adapters take it as a parameter; and the browser
driver's two values travel as `node` arguments because the sanctioned
runner has no environment parameter and the seam edit the architecture
asks for is timeout and stdin alone.

## Notes

- 2026-10-08: the merge is gate 3 (ADR-0033). The pull request carries
  this run's `prd.md` and `architecture.md`, so ADR-0036 clause 3 makes
  it a human code-owner merge — the brief's plan: Ship opens the one
  tracking issue, opens the pull request, and stops; the owner watches
  the mp4 and merges. This run's own Ship will fire the hook of row 0109
  against the config of row 0099, which is the terminal end-to-end run
  Verify records.
- 2026-10-08: owner-session ledger policy — detector G reads a checked
  row as a merged work order owed a `docs/factory/costs.jsonl` line, and
  this run's rows are worked by this session with no dispatched agent,
  so each check-off appends one honest zero-cost row via `python3
  budget_guard.py record` with the row's id, `run_id` of the form
  `session-2026-10-08-wo-NNNN`, model `claude-fable-5-1`, `0` tokens,
  `0.0` cost and outcome `owner-session:unmetered`, as the last six
  ledger rows do. The rows' Accept text assumes `gates: 0 problem(s)`
  follows from the edits; the ledger row is what makes it so.
- 2026-10-08 (readings taken where the architecture names a function's
  inputs and outputs but not its parameter list or a value; each is one
  row's Accept, none moves a responsibility): `narrate(lines, voice,
  workdir, runner)` → `(clips, problems)`, `clips` a list of `(wav path,
  seconds)` in line order, stopping at the first failing line, WAVs at
  `line-N.wav` with N from 1; `record_terminal(plan, workdir, against,
  runner)` and `record_browser(plan, workdir, against, runner)` →
  `(result, problems)` with `result` the seam's `(raw video path,
  offsets)` — `against` added because the seam's stated inputs name the
  plan, the scratch directory and the runner, and the tape's `Set
  Shell` and the browser's first navigation both need it; the seam's
  `run` read as the runner factory (`cli.runner` or a fake) because the
  terminal adapter shells out to `vhs` and `ffprobe` both; the
  reachability check as its own `reachable(against, head)` that `render`
  runs for the browser recorder after `probe` and before `narrate`, so an
  unreachable URL costs no narration; `render(root, config, slug, which,
  runner, head=None, scratch=None)` → `(verdict, lines, problems)`;
  `main(argv, root=None, which=shutil.which, runner=cli.runner,
  platform=sys.platform)`; `load(root, platform=sys.platform)` resolving
  the free voice default so every downstream reader sees one shape; the
  `config` leg prints no verdict word (none is named for it) — problems
  then the summary line; the terminal tape's `Set FontSize 18` (the
  architecture names the font, not its size); storyboard steps numbered
  from 1 in problem strings; the missing-tool line (`launch-demo: missing `, the
  name, ` — `, the purpose, `; install: `, the hint); the `launch-demo:
  wrote ` and `launch-demo: scratch ` lines each followed by a path; the `ffprobe` duration argv
  `-v error -show_entries format=duration -of
  default=noprint_wrappers=1:nokey=1`; the constants `PROBE_TIMEOUT`,
  `VOICE_TIMEOUT`, `RECORD_TIMEOUT`, `FFMPEG_TIMEOUT`, `HEAD_TIMEOUT`,
  `WIDTH`, `HEIGHT` beside the five the architecture names; the plan's
  "tape text" realised by the terminal adapter from the plan's scenes,
  the adapter adding only header lines that carry no timing; the agent
  writing `launch.md`'s `video:` line last, from the verdict, because
  `launch.md` is the agent's and a copy-only brief may not name a
  missing mp4.
- 2026-10-08: `cli.detail` answers bytes for a `subprocess.TimeoutExpired`
  that carries stderr (checked in this worktree on Python 3.14.6:
  `b'oops'`), because `subprocess.run` attaches the child's undecoded
  output to that exception even in text mode. The architecture's claim
  that a hung `vhs` or `ffmpeg` becomes a problem string through
  `cli.detail` is therefore true only for a child that wrote nothing;
  row 0097 decodes the bytes inside `detail` as part of the seam edit
  the architecture already asks for. Flagged for Review as a latent
  defect that the new vocabulary member makes reachable, not a design
  change.
- 2026-10-08: `protocol.UTILITY_SKILLS` is alphabetical, so
  `launch-demo` enters between `interactive-architecture-diagram` and
  `mermaid` rather than at the end the architecture's "appended" might
  suggest; `plugin.json`'s parenthetical follows the same order.
  `check_readme_figure` and the other roster checkers report in roster
  order, which is the only effect.
- 2026-10-08: this repo keeps no changelog file, so the skill's `--pr`
  path reads the pull request's title and body alone here and records
  that in `sources:`; the skill's text says "and the changelog entry
  naming it, when the repo keeps one", so a consuming repo that keeps
  one is read.
- 2026-10-08: the proposed ADR (a second reason a skill earns a shipped
  tool, and the per-repo config home of one JSON file under `docs/`) is not a
  row — `docs/adr/` is a human merge gate here and the architecture has
  the implementer open it as its own change for the owner to accept or
  reject. Operate seeds it to the backlog if it has not been opened by
  then.
- 2026-10-08: `docs/launches/` will be created by this run's Ship when
  the hook fires, not by any row; its `launch.md` is scanned by
  detectors C, D and I like any doc, which the copy survives by
  construction (it names no typed id, and in copy-only mode it links to
  no missing mp4). `knowledge_plane.run_dirs` never walks it.
- 2026-10-08 (row 0098 deviation): `factory.py`'s verb table is pinned
  derived — `tests/test_factory_cli.py` asserts one verb per root module
  carrying a `__main__` guard — so a new root tool fails the suite until
  it has its verb. `factory.py` gains `"launch-demo": ("launch_demo",
  "argv")`, one row, in row 0098's commit; `factory.py` is not in
  `factory_init.MIRRORS`, so the manifest is unaffected. Row 0110's list
  of touched files gains `factory.py`; the architecture's tree-claims
  block did not name it.
- 2026-10-08 (row 0099, the real legs on this machine, from the repo
  root): `python3 launch_demo.py config` printed `launch-demo: 0
  problem(s)` and exited 0; `python3 launch_demo.py probe` printed
  `READY` then `launch-demo: 0 problem(s)` and exited 0 — no `missing`
  line, because this machine has ffmpeg, ffprobe, vhs (with ttyd, all
  Homebrew) and `/usr/bin/say`. `docs/launches/` does not exist.
- 2026-10-08 (row 0103): vhs string literals carry no escape processing
  (its lexer reads to the closing delimiter), so the tape writer picks
  the delimiter the text does not contain — backtick first, then `"`,
  then `'` — and quotes the shell words with `shlex.quote`; the
  `\033[1m` bold / `\033[2m` dim escapes travel as literal characters
  for the shell's `printf` to interpret. A by-hand vhs run of such a
  `Type` line parsed and exited 0 here, but its text-output frame was
  not inspected (the session's permission classifier declined the
  read), so the rendered title card is Verify's to confirm with the
  real recording, as the PRD already assigns.
- 2026-10-08 (row 0104 reading): the row's Accept names the summary
  probe's last argument as `out` and, in the same paragraph, has the
  move happen only after the probe reads the file; both cannot hold, and
  the second is the invariant the architecture states (never a partial
  mp4 at the publish path). `assemble` therefore probes the scratch copy
  (`workdir/launch.mp4`) and `os.replace`s it into `out` only once
  ffprobe has read it, so the publish path receives a verified file or
  nothing — its test pins the scratch path as the probe's last
  argument. The summary's lines carry no path, so Verify's paste is
  unchanged. Checked against the owner's ffmpeg 8.1 on synthetic
  inputs: the graph (`scale`/`pad`, one `adelay` per clip,
  `amix=inputs=N:normalize=0`) muxes to h264 + aac at the raw's
  duration; the summary carries ffprobe's `[STREAM]`/`[FORMAT]` wrapper
  lines because the architecture's argv names no `-of` flag.
- 2026-10-08 (row 0106, checked by hand once): `python3 -m http.server
  --directory tests/fixtures/launch-demo 8765` served the page —
  `curl -I http://127.0.0.1:8765/` answered `HTTP/1.0 200 OK` and
  `/index.html` came back as 1158 bytes — then the server was stopped.
- 2026-10-08 (row 0107): the driver's caption bar is re-added on every
  document load by one init script that asks this process for the
  current caption through a context-exposed function
  (`context.exposeFunction`), because `window.name` and storage do not
  survive the title card's `file://` to the product's `http://`
  navigation. The first step's scene starts with `goto(against)` after
  the title card's hold, so that step's mark is the page's first
  navigation. The generated `demo.mjs` for the fixture storyboard parses
  under `node --check` (node 22.22.3 here); Playwright itself was not
  installed in this session, so the real browser run is Verify's, as
  the PRD assigns. `launch_demo.py` is 743 lines, under the 800 cap but
  past the typical band; the two adapters are the natural split if a
  later row grows it.
- 2026-10-08 (row 0110, on the branch tip before this check-off): the
  three outputs were written to files and grepped — `Ran 2030 tests`,
  `OK`; `lint: 0 problem(s) across 26 skills`; `gates: 0 problem(s)`
  and `selftest: ok`. The import sweep over the four Python files
  printed `['cli', 'cli_contract', 'launch_demo']`. `git diff main
  --stat` lists exactly the row's files plus `factory.py` (the row 0098
  deviation above); the five surfaces the row holds untouched diff
  empty; the key/endpoint grep over the skill and the tool prints
  nothing.
- 2026-10-08 (row 0111, correcting a wrong test): the first pass's tape
  test pinned `Output <abs path>` unquoted as `demo.tape`'s first line,
  and vhs 0.11.0 refuses exactly that (`Expected file path after output`,
  `parser: 3 error(s)` — verification.md Failure 1), so the suite was
  green on a tape the recorder cannot run. A test that asserts a value the
  real recorder refuses is a wrong test; it now pins `Output "<abs path>"`
  (vhs's lexer reads a quoted string; a `tempfile.mkdtemp` path never
  holds a double quote). Proved on this machine with vhs 0.11.0 against
  the tape `_tape` writes for the committed
  `docs/launches/pipeline-board/storyboard.json` plan (30 lines, planned
  34.43 s): `vhs validate demo.tape` printed nothing and exited 0; the
  same tape with line 1's quotes stripped printed `^^^^^^ Expected file
  path after output` and exited 1, so the validator discriminates.
- 2026-10-10 (row 0112, a deviation from the architecture for Review):
  the architecture has terminal offsets "computed for vhs" and a
  recording refused past `DRIFT_TOLERANCE = 1.5` s of the planned length.
  That rests on vhs's rendered length being its tape's wall clock, and
  verification.md Failure 2 measured otherwise: the pipeline-board tape
  planned 34.431 s and recorded 32.36 s, every hold 0.4–0.6 s short, a
  uniform ~6 % — so an absolute tolerance refuses every storyboard past
  roughly 25 s, and correctly, because the computed offsets fall late.
  The gap is proportional, so `record_terminal` now scales each planned
  offset by recorded ÷ planned (rounded to three decimals) and refuses a
  ratio outside `DRIFT_BAND = (0.75, 1.25)`, both ends inclusive — a
  ratio that far out is no recording of this plan. `plan` is unchanged
  and still the one owner of the arithmetic; the adapter is the one
  owner of the measurement, as the browser adapter already is of its
  marks. The seam's `((raw, offsets), [])` shape and `record_browser`
  are untouched. Red was observed with the implementation reverted and
  the new tests in place: the scaled-offsets test got `[0.0, 3.0, 7.3]`
  where `[0.0, 2.82, 6.862]` was expected, both band cases and the
  render case got the old `— narration would drift` string, and the
  constant test raised `AttributeError` on `DRIFT_BAND`.
- 2026-10-10 (row 0113): `record_browser` still writes the inspectable
  `workdir/demo.mjs` (the copy `render` publishes), then copies it into
  a fresh `tempfile.mkdtemp(prefix="launch-demo-", dir=Path.cwd())` and
  runs node on that copy, removing the directory in a `finally` on
  success and failure alike. The working directory is the repo root by
  the CLI contract and the place `probe` resolves `playwright` from;
  Node resolves an ES module's bare imports by walking up from the
  importing file, never from the working directory, so a driver under
  the system temp directory cannot see the repo's `node_modules`
  (verification.md Failure 3). Shown here with node v22.22.3 and a
  throwaway package `throwaway` in a scratch directory's
  `node_modules`: `node launch-demo-x/probe.mjs` run from that
  directory printed `resolved` and exited 0; the same file copied into
  a `tempfile.mkdtemp(prefix='launch-demo-')` directory printed `Error
  [ERR_MODULE_NOT_FOUND]: Cannot find package 'throwaway' imported from
  /private/var/folders/…/launch-demo-lv1t8hd2/probe.mjs` then `Node.js
  v22.22.3` and exited 1. This repo's `.gitignore` gains
  `/launch-demo-*/` so a directory left by a killed run is never
  tracked (a consuming repo's ignore file is not the tool's to edit; the
  `finally` is the guarantee there). A failed node run's reason is now
  the last stderr line that begins an error message (`NODE_ERROR_LINE`,
  flush-left `Error`/`TypeError`-style, so indented stack frames never
  match), falling back to `cli.detail`'s last line; `cli.py` is not
  edited (Failure 4's question about the convention stays Review's).
  Test reading: the tests run from a throwaway working directory
  (`CwdMixin`) so no scratch directory is made in the checkout, which
  puts that directory under the system temp directory too — so the
  test pins the driver's grandparent as the working directory and not
  as `tempfile.gettempdir()` itself (the old `mkdtemp` home), rather
  than "not under the system temp directory" literally. Observed red:
  the driver path assertion got `/var/folders/…/work`'s parent where
  the working directory was expected (both path tests) and the reason
  test got `Node.js v22.22.3`. `launch_demo.py` is now 792 lines, close
  to the 800 cap; the two adapters remain the natural split.
- 2026-10-10 (row 0125, correcting a wrong test): row 0113's
  `test_a_failing_node` fed the reason rule `Error: browserType.launch:
  …`, a prefix Node never prints for Playwright's error, so the suite was
  green on a stderr the real driver does not produce (verification.md
  Failure 5). The real one, captured here with Playwright 1.64.0
  (`npm install --no-save`), node v22.22.3, `PLAYWRIGHT_BROWSERS_PATH`
  at an empty scratch directory and the fixture served on 8765, is
  `node:internal/modules/run_main:123`, the indented
  `triggerUncaughtException(` and `^`, a blank, the flush-left
  `browserType.launch: Executable doesn't exist at <dir>/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell`,
  Playwright's nine-line boxed install hint, `    at <repo>/launch-demo-…/demo.mjs:29:32 {`,
  `  log: [],`, `  name: 'Error'`, `}`, a blank and `Node.js v22.22.3`;
  the test's `NODE_BROWSER_MISSING` equals it byte for byte once the two
  absolute paths are replaced by `/x/…`. `NODE_ERROR_LINE` is now
  `[A-Za-z_$][\w$.]*(?: \[\w+\])?: \S` matched at line start: a name
  (dots allowed, so `browserType.launch`), an optional `[CODE]`, then a
  colon and a space. Node's `node:internal/…` header has no space after
  its colon and its banner no colon, and frames and the property dump
  are indented. Before, through the CLI with the throwaway browser config:
  `launch-demo: browser recorder failed: Node.js v22.22.3`; after, the
  same run: `launch-demo: browser recorder failed: browserType.launch:
  Executable doesn't exist at <scratch>/emptybrowsers/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell`,
  exit 1, no `launch-demo-*` directory left at the root. The ESM case,
  `record_browser` with the real runner from a scratch directory with no
  `node_modules` above it: `launch-demo: browser recorder failed: Error
  [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright' imported from
  <scratch>/esm/launch-demo-orrpjqcd/demo.mjs`. `node_modules`,
  `package-lock.json`, `.verify-smoke/` and the throwaway config were
  removed and `docs/launch-demo.json` restored with `git checkout`.
  `launch_demo.py` is 794 lines.
