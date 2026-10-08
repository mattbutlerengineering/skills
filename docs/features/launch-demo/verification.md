---
stage: verify
run: feature:launch-demo
date: 2026-10-08
assumptions:
  - "No live interview: the soft gate was read from breakdown.md (fourteen rows, all checked) and the criteria list is PRD-0009's ten Success criteria plus the breakdown's close-out acceptance (every row checked, one zero-cost ledger row per row), which no PRD criterion covers."
  - "The terminal subject is pipeline-board: its run directory carries prd.md, verification.md and release.md, and its tool is a visible terminal action. The happy path is precedence item 2 — the command that run's verification ran (`python3 board.py <dir>`) — shaped into two jq-filtered invocations because the raw JSON for this repo's 59 active runs overflows a 720-pixel frame; the filter is a cut of that command, not a guessed walkthrough."
  - "The storyboard was not re-cut shorter after the drift finding below; a shorter one might squeak under the tolerance and would hide a proportional defect. Implement decides the fix, not this stage."
  - "Two diagnostics were run after the two recorder failures, each labelled as such and neither a verdict: vhs on a copy of the tool's own tape with line 1 alone quoted, and the browser render with TMPDIR pointed inside the repo so the tool's scratch directory sat under the repo's node_modules ancestor. The tool, the config and the fixture were not edited; nothing from either diagnostic is published as a launch.mp4."
  - "The two PNGs committed beside this artifact come from those diagnostic recordings, not from a tool-produced launch.mp4 (none exists), and are named -diagnostic for that reason; both are under 300 KB."
  - "The pull-request subject is #598 (decompose's placeholder scan): a merged feature PR with no run directory. Its slug is this stage's kebab-case cut of the title, decompose-draft-check. The copy was written to the scratch directory and is quoted below rather than published under docs/launches/, because the PR was chosen as a test subject and the criterion's check is the copy in a fenced block."
  - "The browser smoke test used a throwaway config publishing to .verify-smoke/launches inside the repo (the config grammar admits only in-repo paths); the directory, node_modules/ and the throwaway config were removed afterwards and docs/launch-demo.json restored with git checkout. Playwright 1.64.0 was installed with npm install --no-save and its chromium headless shell v1248 (99 MiB) downloaded to the user's Playwright cache, where it remains — outside the repo."
  - "The launch directory committed, docs/launches/pipeline-board/, holds launch.md and storyboard.json only: no launch.mp4 and no demo.tape exist because the render failed, and the skill's step 7 settled the video: line from the verdict."
  - "The macOS voice (/usr/bin/say) is the only voice exercised, as the PRD says; the narration WAVs were rendered for real by it in both runs."
---

# Verification: Launch demo

## Summary

8 PASS, 2 FAIL across PRD-0009's ten success criteria, plus one PASS for
the breakdown's close-out acceptance. The two failures are the two
recorders, each at its first real run on this machine: the terminal
recorder never records because the tape's `Output` line carries an
unquoted absolute path that vhs 0.11.0's parser rejects (and, in a
diagnostic with that one line quoted, the recording runs 2.07 s short of
the plan, past the 1.5 s drift tolerance); the browser recorder never
records because the generated driver is written to a scratch directory
outside the repo, from which Node's module resolution cannot find
`playwright` (and, in a diagnostic with the scratch directory inside the
repo, the same tool produces a 26.5 s h264+aac mp4 with the title card,
the caption bar over the fixture's actions, and the outro). Everything
around the recorders holds: the config grammar, the probe, the copy-only
degradation, the free voice, the copy from both sources, the storyboard
held to the copy, the Ship hook, the roster, the stdlib rule and the
battery. Next stage: Implement, for the two recorder adapters.

Worktree HEAD `ab37864`, fourteen commits ahead of `main` `736f54b`;
interpreter `Python 3.14.6`; vhs 0.11.0 with ttyd, ffmpeg 8.1, ffprobe,
`/usr/bin/say`, node v22.22.3, Playwright 1.64.0 (installed for the
smoke test, removed after), gh authenticated.

## Criteria & evidence

### Terminal recorder, end to end

- Check: the `launch-demo` skill followed as written for one of this
  plugin's own skills — `pipeline-board` (frontmatter assumptions) —
  under this repo's committed config (`terminal`, `bash`,
  `docs/launches`): the `config` and `probe` legs, the sources read
  (`docs/features/pipeline-board/prd.md`, `verification.md`,
  `release.md`), `launch.md` and `storyboard.json` written to
  `docs/launches/pipeline-board/`, the storyboard held to the copy, then
  the `render pipeline-board` leg from the repo root.
- Evidence, the `config` and `probe` legs (each exit 0):
  ```
  $ python3 skills/launch-demo/../../launch_demo.py config
  launch-demo: 0 problem(s)
  $ python3 skills/launch-demo/../../launch_demo.py probe
  READY
  launch-demo: 0 problem(s)
  ```
- Evidence, the storyboard held to the copy before any tool ran:
  ```
  $ python3 -c "... launch_demo.check_storyboard(board, launch_demo._body(copy), 'terminal')"
  check_storyboard: []
  ```
- Evidence, the `render` leg:
  ```
  $ python3 skills/launch-demo/../../launch_demo.py render pipeline-board
  launch-demo: scratch /var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-km2ksyeq
  launch-demo: terminal recorder failed: parser: 3 error(s)
  launch-demo: 1 problem(s)
  exit=1
  ```
- Evidence, the scratch directory the tool named (the voice rendered all
  four lines before vhs ran) and vhs's own output on the tool's tape:
  ```
  $ ls -la /var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-km2ksyeq
  -rw-r--r--  1 mbutler  staff    1044 Oct  8 14:24 demo.tape
  -rw-r--r--  1 mbutler  staff  259758 Oct  8 14:24 line-1.wav
  -rw-r--r--  1 mbutler  staff  240002 Oct  8 14:24 line-2.wav
  -rw-r--r--  1 mbutler  staff  336668 Oct  8 14:24 line-3.wav
  -rw-r--r--  1 mbutler  staff  246352 Oct  8 14:24 line-4.wav
  $ head -1 .../launch-demo-km2ksyeq/demo.tape
  Output /private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-km2ksyeq/raw.mp4
  $ vhs .../launch-demo-km2ksyeq/demo.tape
    1 │ Output /private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-km2ksyeq/raw.mp4
        ^^^^^^ Expected file path after output
    1 │ Output /private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-km2ksyeq/raw.mp4
               ^^^^^^^ Invalid command: private
    1 │ Output /private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-km2ksyeq/raw.mp4
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ Invalid command: var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-km2ksyeq/raw.mp4
  parser: 3 error(s)
  recording failed
  vhs exit=1
  ```
- Evidence, the cause isolated with three one-line tapes (an unquoted
  absolute path fails; a quoted absolute path and a relative path both
  record):
  ```
  --- abs.tape: Output /private/tmp/claude-501/x-abs.mp4
        ^^^^^^ Expected file path after output
               ^^^^^^^ Invalid command: private
                        ^^^^^^^^^^^^^^^^^^^^^^^^ Invalid command: tmp/claude-501/x-abs.mp4
  parser: 3 error(s)
  exit=1
  --- quoted.tape: Output "/private/tmp/claude-501/x-quoted.mp4"
  exit=0
  --- rel.tape: Output rel-out.mp4
  exit=0
  -rw-r--r--  1 mbutler  wheel  5332 Oct  8 14:24 /private/tmp/claude-501/x-quoted.mp4
  -rw-r--r--  1 mbutler  wheel  5133 Oct  8 14:24 rel-out.mp4
  ```
  The tool writes `Output {raw.resolve()}` (`launch_demo._tape`, line
  321) and `tests/test_launch_demo.py` lines 576–577 pin that unquoted
  form as the tape's first line, so the suite is green on a tape vhs
  cannot parse. `tempfile.mkdtemp` always yields an absolute path, so
  every terminal render fails here.
- Evidence, the launch directory after the run — no mp4, no tape, no
  placeholder:
  ```
  $ ls -la docs/launches/pipeline-board/
  -rw-r--r--  1 mbutler  staff  1193 Oct  8 14:29 launch.md
  -rw-r--r--  1 mbutler  staff   779 Oct  8 14:23 storyboard.json
  $ find docs/launches -name '*.mp4' | wc -l
         0
  ```
- Diagnostic (not the verdict; frontmatter assumptions): vhs run by hand
  on a copy of the tool's tape whose line 1 alone was changed to a
  quoted path (`diff` of lines 2–30 against the tool's tape was empty),
  to tell Implement whether the rest of the tape holds. It records, and
  the frames show what the tape draws; but the recording is 2.07 s
  shorter than the plan the tool computed from the real narration
  durations, past `DRIFT_TOLERANCE = 1.5`, so the tool's own drift check
  would refuse it with `launch-demo: recording ran 32.4 s where the plan
  expected 34.4 s — narration would drift`:
  ```
  $ ffprobe ... line-1.wav .. line-4.wav   (the real narration durations)
  line-1.wav 5.797324
  line-2.wav 5.349342
  line-3.wav 7.541315
  line-4.wav 5.493333
  $ python3 -c "... launch_demo.plan(board, secs)"
  plan offsets [0.0, 6.297, 15.497, 28.438] holds [6.297, 5.849, 8.041, 5.993] planned 34.431
  $ vhs diag-terminal/demo.tape
  vhs exit=0
  $ ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames:format=duration raw.mp4
  codec_name=h264
  codec_type=video
  width=1280
  height=720
  r_frame_rate=25/1
  nb_frames=809
  duration=32.360000
  $ (bursts of frame change, i.e. scene starts and typing runs)
  burst 5.8..9.28 (20 frames)
  burst 14.56..19.52 (26 frames)
  burst 26.8..26.8 (1 frames)
  ```
  Scene starts land at 5.8, 14.56 and 26.8 s against planned 6.297,
  15.497 and 28.438 s: every hold records 0.4–0.6 s shorter than its
  `Sleep` plus typing, about 6 % of the tape, so the gap grows with the
  video's length and the computed offsets fall increasingly late.
- Diagnostic frames, viewed: at 0.5 s the title card — a dark terminal
  with **The pipeline board** in bold over "Every run, on its step, at a
  glance" and a `>` prompt beneath
  ([`title-card-diagnostic.png`](title-card-diagnostic.png), 20,492
  bytes); at 7.5 s the dim caption "You ask for the board and a small
  tool reads every run's notes to state which step each one is on." over
  the first command being typed; at 21 s the second caption, the full
  `jq` command and its ten `["stage","state"]` lines in green, `verify`
  marked `current`; at 31.5 s the outro line in bold, alone. The tape
  grammar, the hidden `clear; printf` trick and the title card all work.
- Evidence, captions equal narration (the tool's own tape against the
  storyboard and the copy):
  ```
  narration lines: 4 | on-screen prints in the tape: 4 | WAVs the voice wrote: 4
  MISMATCH | sentence of launch.md: True | The pipeline board is a one-page picture of every piece of...
  caption == narration | sentence of launch.md: True | You ask for the board and a small tool reads every run's n...
  caption == narration | sentence of launch.md: True | It lists every active run once, tells feature work from ma...
  caption == narration | sentence of launch.md: True | Instead of walking folders and running commands, you find ...
  last scene printed (outro): 'Instead of walking folders and running commands,...'
  ```
  The one mismatch is by design: the title card prints the title and
  tagline while the intro is spoken (the reference's three-parts table);
  the two step captions and the outro are the narration lines verbatim,
  and all four lines are sentences of the copy.
- Result: FAIL — no invocation produced an mp4; the file does not exist
  at the publish path, so there is no `ffprobe` of it, no duration and
  no title-card frame from it. Two defects, both in the terminal
  adapter: the unquoted `Output` path (blocks every run), and the drift
  of a vhs recording against the computed plan (would refuse this
  storyboard even with the first fixed). Routed to Implement under
  Failures.

### Browser recorder, smoke-tested

- Check: Playwright installed without touching tracked files (`npm
  install --no-save playwright`, then `npx playwright install chromium`
  because the cached browsers did not match 1.64.0's v1248); the fixture
  served by `python3 -m http.server --directory tests/fixtures/launch-demo
  8765`; a throwaway config (`browser`, `against`
  `http://127.0.0.1:8765`, publish `.verify-smoke/launches`) in place of
  the committed one; the committed fixture `launch.md` and
  `storyboard.json` copied to `.verify-smoke/launches/fixture/`; then
  `probe` (before and after the install) and `render fixture` from the
  repo root. **This proves the recorder on a fixture, not on a web app.**
- Evidence, the throwaway config and the probe before Playwright existed
  (the browser degradation names it):
  ```
  $ cat docs/launch-demo.json
  {"when": "on-demand", "recorder": "browser", "against": "http://127.0.0.1:8765", "publish": ".verify-smoke/launches"}
  $ python3 launch_demo.py config
  launch-demo: 0 problem(s)
  $ python3 launch_demo.py probe
  launch-demo: missing playwright — records the browser; install: npm install playwright && npx playwright install chromium, from the repo root
  COPY-ONLY
  launch-demo: 0 problem(s)
  ```
- Evidence, the server, the install and the probe after it:
  ```
  $ curl -sI http://127.0.0.1:8765/ | head -1
  HTTP/1.0 200 OK
  $ npm install --no-save playwright
  added 2 packages, and audited 3 packages in 1s
  $ node -e "console.log(require('playwright/package.json').version)"
  1.64.0
  $ npx playwright install chromium
  Chrome Headless Shell 156.0.8078.4 (playwright chromium-headless-shell v1248) downloaded to /Users/mbutler/Library/Caches/ms-playwright/chromium_headless_shell-1248
  $ python3 launch_demo.py probe
  READY
  launch-demo: 0 problem(s)
  ```
- Evidence, the `render` leg:
  ```
  $ python3 launch_demo.py render fixture
  launch-demo: scratch /var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-_ij6suu7
  launch-demo: browser recorder failed: Node.js v22.22.3
  launch-demo: 1 problem(s)
  exit=1
  $ ls -la .verify-smoke/launches/fixture/
  -rw-r--r--  1 mbutler  staff  740 Oct  8 14:29 launch.md
  -rw-r--r--  1 mbutler  staff  679 Oct  8 14:29 storyboard.json
  ```
- Evidence, the generated driver run by hand from the repo root with the
  tool's own arguments, for the full error the problem string cut to
  Node's last stderr line:
  ```
  $ ls .../launch-demo-_ij6suu7
  demo.mjs  line-1.wav  line-2.wav  line-3.wav  line-4.wav  outro.html  title.html
  $ node .../launch-demo-_ij6suu7/demo.mjs http://127.0.0.1:8765 .../launch-demo-_ij6suu7
  node:internal/modules/package_json_reader:314
    throw new ERR_MODULE_NOT_FOUND(packageName, fileURLToPath(base), null);
          ^

  Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright' imported from /private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-_ij6suu7/demo.mjs
      at Object.getPackageJSONURL (node:internal/modules/package_json_reader:314:9)
      at packageResolve (node:internal/modules/esm/resolve:768:81)
      ...
    code: 'ERR_MODULE_NOT_FOUND'
  }

  Node.js v22.22.3
  node exit=1
  ```
  The probe resolves `playwright` from the working directory (the repo
  root, where `node_modules/` was) and says READY; the driver is written
  to the `tempfile.mkdtemp` scratch directory under `/var/folders`, and
  ES-module resolution walks up from the importing file's own directory,
  never from the working directory, so it finds no `node_modules`. The
  architecture's data model placed the driver inside the repo for this
  exact reason. A second, smaller defect: `cli.detail` takes stderr's
  last line, which for Node is its version banner, so the reason line
  the brief would carry is `Node.js v22.22.3`.
- Diagnostic (not the verdict; frontmatter assumptions): the same tool,
  config and fixture with `TMPDIR` pointed at `.verify-smoke/tmp` inside
  the repo, so the scratch directory sat where resolution reaches the
  repo's `node_modules`. Everything past the import works:
  ```
  $ env TMPDIR="$PWD/.verify-smoke/tmp" python3 launch_demo.py render fixture
  launch-demo: scratch /Users/mbutler/github/skills/.claude/worktrees/launch-demo/.verify-smoke/tmp/launch-demo-j60uqztu
  launch-demo: wrote .verify-smoke/launches/fixture/demo.mjs
  launch-demo: wrote .verify-smoke/launches/fixture/launch.mp4
  launch-demo: [STREAM]
  launch-demo: codec_name=h264
  launch-demo: codec_type=video
  launch-demo: [/STREAM]
  launch-demo: [STREAM]
  launch-demo: codec_name=aac
  launch-demo: codec_type=audio
  launch-demo: [/STREAM]
  launch-demo: [FORMAT]
  launch-demo: duration=26.533333
  launch-demo: [/FORMAT]
  PRODUCED
  launch-demo: 0 problem(s)
  exit=0  (38.1 s wall)
  $ ffprobe -v error -show_entries stream=codec_type,codec_name,width,height:format=duration,size .verify-smoke/launches/fixture/launch.mp4
  codec_name=h264
  codec_type=video
  width=1280
  height=720
  codec_name=aac
  codec_type=audio
  duration=26.533333
  size=345650
  $ cat .verify-smoke/tmp/launch-demo-j60uqztu/marks.json
  [1791495048869,1791495048869,1791495056209,1791495060479,1791495065576]
  $ ffmpeg -i launch.mp4 -af volumedetect -vn -f null -
  mean_volume: -19.9 dB
  max_volume: -1.0 dB
  ```
  Frames viewed: at 0.5 s the dark title card, **Counter and greeter**
  over "The browser recorder, proved on a fixture"; at 12 s the fixture
  page with "Clicks so far: **2**", the name field holding "Ada", "Hello,
  Ada!" beneath, and the caption bar along the bottom reading "Typing a
  name and pressing the greeting button writes a hello to that name
  beneath it."
  ([`browser-fixture-step-diagnostic.png`](browser-fixture-step-diagnostic.png),
  74,734 bytes); at 25.5 s the outro card, the outro sentence alone in
  bold. The measured marks give scene offsets of 0.0, 7.34, 11.61 and
  16.71 s; the narration track is present at −19.9 dB mean.
- Evidence, the clean-up:
  ```
  $ kill $(cat http-server.pid); curl -sI --max-time 2 http://127.0.0.1:8765/ || echo "server stopped"
  server stopped
  $ rm -rf node_modules package-lock.json .verify-smoke && git checkout -- docs/launch-demo.json && cat docs/launch-demo.json && git status --short
  {"when": "ship", "recorder": "terminal", "against": "bash", "publish": "docs/launches"}
  ?? docs/launches/
  ```
- Result: FAIL — the invocation as the skill makes it did not produce an
  mp4: the driver cannot import `playwright` from the scratch directory
  the tool writes it to. The adapter, the driver, the caption bar, the
  marks and the mux all work once the driver sits inside the repo (the
  diagnostic). Routed to Implement under Failures.

### Copy from artifacts, or from the pull request

- Check: both paths of the skill's steps 3–4 followed. For the run
  directory, `pipeline-board`'s `prd.md`, `verification.md` and
  `release.md` were read and `docs/launches/pipeline-board/launch.md`
  written (committed with this artifact). For the pull request, `gh pr
  list --state merged --limit 20` was read, #598 chosen (no run directory
  names it — the only hits for `598` under `docs/features` and
  `docs/fixes` are passing mentions in other runs' prose — and this repo
  keeps no changelog), `gh pr view 598 --json title,body` read, and the
  copy written to scratch (frontmatter assumptions). Each copy was
  grepped for a path, function, flag or identifier.
- Evidence, the run-directory copy, from `docs/features/pipeline-board/
  prd.md`, `verification.md` and `release.md`:
  ```
  ---
  launch: pipeline-board
  date: 2026-10-08
  sources: [docs/features/pipeline-board/prd.md, docs/features/pipeline-board/verification.md, docs/features/pipeline-board/release.md]
  video: none — launch-demo: terminal recorder failed: parser: 3 error(s)
  ---

  # Launch: The pipeline board

  ## What it is

  The pipeline board is a one-page picture of every piece of work in flight
  and the step each one has reached. It is drawn on demand from the notes
  each run leaves behind, so there is nothing to keep up to date. You open
  it when you want to get your bearings without running anything.

  ## What it does

  You ask for the board and a small tool reads every run's notes to state
  which step each one is on. It lists every active run once, tells feature
  work from maintenance work, and shows how far along the building step has
  come. The picture is a single file with no outside dependencies, so it
  opens anywhere and can be sent as it is.

  ## How it helps

  Instead of walking folders and running commands, you find where every run
  stands in one glance. Anyone you share it with can read it with no
  repository and no tools installed. The board never changes a run; it only
  shows where things stand.
  ```
- Evidence, the pull-request inputs — the title and body of #598 as `gh`
  returned them (body 1,995 characters; the Evidence and Test plan
  sections elided here are a battery transcript and two checkboxes):
  ```
  $ gh pr view 598 --json title,body
  title: feat(decompose): check the draft for placeholders and drifting names before review
  body:
  No work order: a skill improvement borrowed from obra/superpowers, tracked as beads wo-aao.
  Closes #594

  ## Why

  decompose went straight from drafting to the user's review of the cut. That review is the only check, and under autorun, or when the user accepts the recommended boundaries as-is, it does not happen live. Superpowers' writing-plans skill runs a self-review first: a placeholder scan, a coverage check, and a check that names stay consistent across tasks.

  ## Change

  - **New step 4 in `skills/decompose/SKILL.md`**, before "Review the cut". Read the draft as the implementer who will pick up one item cold, and fix in place:
    - no `TEMPLATE.md` slot, TBD, TODO, or "same as the item above" survives, and an item that cannot be written yet is a design gap, not a placeholder;
    - every `Accept:` line states a checkable outcome;
    - components keep the architecture's spelling, and every `Blocked by:` names an existing item by exact title or `WO-####` id.
  - Later steps are renumbered. Nothing cites them by number, and lint finds steps by content.
  - **`evals/output/decompose.json`** case 1 gains the matching expectation. This makes the eval stricter, and no earlier result is rewritten.

  A related defect turned up while writing the Blocked-by rule. `knowledge_plane.row_blockers` reads a blocked-by clause with no WO id as "no blockers", so a row can be dispatched early. It is filed separately as beads wo-o3l and is not fixed here.
  $ ls | grep -i changelog || echo "no changelog file at the repo root"
  no changelog file at the repo root
  ```
- Evidence, the pull-request copy written from that title and body:
  ```
  ---
  launch: decompose-draft-check
  date: 2026-10-08
  sources: [pr: #598]
  video: none — no happy-path source (looked at: no run directory for this pull request; the pull request body's Evidence section, which records the test battery rather than a before-and-after walk of the feature; this repo keeps no changelog)
  ---

  # Launch: The breakdown checks itself before you see it

  ## What it is

  When a design is cut into work items, the plan now reads itself over once
  before anyone reviews it. It is the same self-check a careful planner does
  by hand, done every time, whether or not a person is watching.

  ## What it does

  Before the cut is shown for review, the plan is read as the person who
  will pick up one item cold. Any leftover blank, to-do, or "same as above"
  is filled in or turned into a named design gap. Every acceptance line is
  made to state something that can be checked, every component keeps the
  name the design gave it, and every dependency points at an item that
  exists.

  ## How it helps

  Work handed to an agent or a person starts from items that can be acted
  on, not placeholders. An unattended run no longer skips the one review
  that used to catch these problems. The things that used to slip through
  to review are caught where they are cheapest to fix.
  ```
  Neither body names a file path, a function, a flag or a typed id (the
  `sources:` frontmatter names the files read, as the skill's template
  requires); the PR copy's happy-path search ended at precedence item 5
  with no before-and-after section, so it is copy-only with the reason in
  its `video:` line, exactly the skill's step 5.
- Result: PASS

### Copy-only degradation

- Check: the `probe` and `render pipeline-board` legs run before the real
  render, with `PATH=/nonexistent` (which hides `/usr/bin/say` as well as
  the Homebrew tools) and the interpreter by absolute path; then an `ls`
  of the publish path. The browser recorder's missing-Playwright line is
  under the browser criterion above.
- Evidence:
  ```
  $ command -v python3
  /opt/homebrew/bin/python3
  $ env PATH=/nonexistent /opt/homebrew/bin/python3 launch_demo.py probe
  launch-demo: missing ffmpeg — transcodes, pads and muxes the recording; install: brew install ffmpeg (macOS) or apt install ffmpeg
  launch-demo: missing ffprobe — measures narration and recording durations; install: ships with ffmpeg
  launch-demo: missing vhs — records the terminal; install: brew install vhs (needs ttyd) or go install github.com/charmbracelet/vhs@latest
  launch-demo: missing say — renders each narration line to a WAV; install: install it, or point voice in docs/launch-demo.json at any command reading one line on stdin and writing {out}
  COPY-ONLY
  launch-demo: 0 problem(s)
  probe exit=0
  $ env PATH=/nonexistent /opt/homebrew/bin/python3 launch_demo.py render pipeline-board
  launch-demo: missing ffmpeg — transcodes, pads and muxes the recording; install: brew install ffmpeg (macOS) or apt install ffmpeg
  launch-demo: missing ffprobe — measures narration and recording durations; install: ships with ffmpeg
  launch-demo: missing vhs — records the terminal; install: brew install vhs (needs ttyd) or go install github.com/charmbracelet/vhs@latest
  launch-demo: missing say — renders each narration line to a WAV; install: install it, or point voice in docs/launch-demo.json at any command reading one line on stdin and writing {out}
  COPY-ONLY
  launch-demo: 0 problem(s)
  render exit=0
  $ ls -la docs/launches/pipeline-board/
  -rw-r--r--  1 mbutler  staff  1144 Oct  8 14:23 launch.md
  -rw-r--r--  1 mbutler  staff   779 Oct  8 14:23 storyboard.json
  $ find docs/launches -name '*.mp4' | wc -l
         0
  ```
  Each missing tool is named with its purpose and install hint, the
  verdict word is COPY-ONLY, the exit is 0, and the publish path holds
  the copy and the storyboard only — no placeholder, no empty mp4. The
  browser config's `missing playwright` line, before the install, is
  quoted under the browser criterion.
- Result: PASS

### A free voice, no key, no spend by default

- Check: the grep the PRD names over the tool and the skill; the
  reference's documented swap; and the real narration of both runs,
  which `/usr/bin/say` rendered under the platform default with no
  `voice` in the config.
- Evidence:
  ```
  $ grep -rniE 'elevenlabs|openai|api_key|api-key|bearer' launch_demo.py skills/launch-demo/
  grep exit=1   (no match)
  $ grep -n "say --data-format\|espeak-ng -w\|piper --model\|hosted voice" skills/launch-demo/references/brief-grammar.md
  43:- macOS: `say --data-format=LEI16@22050 -o {out}`
  44:- elsewhere: `espeak-ng -w {out}` (one distribution package, no model
  48:(`piper --model en_US-lessac-medium.onnx --output_file {out}`), or a
  49:wrapper script around a hosted voice. A hosted voice's key is its own
  $ ls .../launch-demo-km2ksyeq/line-*.wav      (the terminal run's narration, by say)
  line-1.wav line-2.wav line-3.wav line-4.wav
  ```
  The reference's swap, quoted: "`voice` is any command that reads one
  line of text on stdin and writes a WAV at the path substituted for
  `{out}`. … A hosted voice's key is its own business, read by that
  script from its own environment; this config never carries it, and the
  tool never names an endpoint. Nothing here spends money unless the repo
  chooses a voice that does."
- Result: PASS

### Per-repo config, validated

- Check: the tests that pin each field's exact problem string through
  `launch_demo.load` (`tests/test_launch_demo.py`, class `TestLoad`,
  `LABEL = "launch-demo: docs/launch-demo.json"`), the suite run, and one
  malformed config run live through the `config` leg against a scratch
  edit of `docs/launch-demo.json`, restored afterwards.
- Evidence, the pinned strings by test name:
  ```
  test_no_file_is_the_missing_problem        -> (None, ["launch-demo: missing docs/launch-demo.json"])
  test_bytes_that_are_not_json               -> problems[0].startswith(f"{LABEL} is not valid JSON:")
  test_a_top_level_array                     -> (None, [f"{LABEL} is not a JSON object"])
  test_an_empty_object_names_every_required_field_in_order
                                             -> [f"{LABEL} has no when", f"{LABEL} has no recorder", f"{LABEL} has no against", f"{LABEL} has no publish"]
  test_when_grammar                          -> [f'{LABEL} when must be "ship" or "on-demand"']
  test_recorder_grammar                      -> [f'{LABEL} recorder must be "terminal" or "browser"']
  test_against_must_be_a_non_empty_string    -> [f"{LABEL} against must be a non-empty string"]  (for "" and 7)
  test_the_browser_recorder_needs_a_url      -> [f"{LABEL} against must be an http(s) URL for the browser recorder"]
  test_voice_must_name_out_when_present      -> [f"{LABEL} voice must be a non-empty string naming {out}"]  (for "say -o out.wav" and "")
  test_publish_must_be_a_plain_relative_path -> [f"{LABEL} publish must be a plain relative path inside the repo"]  (for "/tmp/x", "../x", "")
  test_a_valid_file_gets_the_macos_voice_default -> config["voice"] == "say --data-format=LEI16@22050 -o {out}"
  test_a_valid_file_gets_the_espeak_default_elsewhere -> config["voice"] == "espeak-ng -w {out}"
  test_a_set_voice_is_kept                   -> config["voice"] == "piper -o {out}"
  $ python3 -m unittest tests.test_launch_demo
  Ran 83 tests in 0.063s
  OK
  ```
- Evidence, one malformed config live (every field wrong at once, voice
  present but malformed):
  ```
  $ cat docs/launch-demo.json
  {"when": "always", "recorder": "gif", "against": "", "voice": "say -o out.wav", "publish": "../x"}
  $ python3 launch_demo.py config
  launch-demo: docs/launch-demo.json when must be "ship" or "on-demand"
  launch-demo: docs/launch-demo.json recorder must be "terminal" or "browser"
  launch-demo: docs/launch-demo.json against must be a non-empty string
  launch-demo: docs/launch-demo.json voice must be a non-empty string naming {out}
  launch-demo: docs/launch-demo.json publish must be a plain relative path inside the repo
  launch-demo: 5 problem(s)
  exit=1
  $ git checkout -- docs/launch-demo.json && cat docs/launch-demo.json
  {"when": "ship", "recorder": "terminal", "against": "bash", "publish": "docs/launches"}
  ```
- Result: PASS

### Two triggers, Ship otherwise untouched

- Check: the three checks the PRD names — `git diff main --
  skills/ship/`, `git diff main -- skills/next/`, and lint's
  `check_skill_recitals` and `check_router` — plus direct invocation with
  no run in flight (the pipeline-board run is complete, and #598 has no
  run), which the two copy sections above record.
- Evidence:
  ```
  $ git diff main -- skills/ship/
  diff --git a/skills/ship/SKILL.md b/skills/ship/SKILL.md
  @@ -32,11 +32,21 @@ branch.
  -4. **Release.** Execute the project's release mechanism step by step,
  +4. **Launch brief.** If `docs/launch-demo.json` exists in the repo and
  +   its `when` field is `ship`, load the `launch-demo` skill through the
  +   harness's skill-loading mechanism (a skill tool where one exists,
  +   otherwise a read of the skill file), run it for this run, commit what
  +   it wrote on the branch, and add one numbered Release-log entry
  +   quoting the tool's reason line(s) and its verdict verbatim. With no
  +   config file, or any other `when`, do nothing and write nothing. The
  +   hook never blocks a release: a COPY-ONLY verdict and a problem exit
  +   are each one log line, and the release proceeds.
  +
  +5. **Release.** Execute the project's release mechanism step by step,
  -5. **Post-release.** Check the shipped thing actually works where users get
  +6. **Post-release.** Check the shipped thing actually works where users get
  -6. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
  +7. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
  -7. **Hand off.** Next stage is Operate.
  +8. **Hand off.** Next stage is Operate.
  $ git diff main -- skills/next/ | wc -c
         0
  $ git diff main --stat -- skills/next/ skills/ship/TEMPLATE.md | wc -l
         0
  $ python3 -c "import lint, pathlib; print(lint.check_skill_recitals(pathlib.Path('.'))); print(lint.check_router(pathlib.Path('.')))"
  []
  []
  ```
  The Ship diff is the one new step and four renumbered leading digits,
  nothing else; `skills/next/` and `skills/ship/TEMPLATE.md` are
  byte-identical to `main`. The hook itself firing from Ship is not
  exercised by this stage (Not verified).
- Result: PASS

### A utility skill, on every roster

- Check: the roster surfaces read directly and the two diffs the PRD
  names; `lint: 0 problem(s)` is under Battery.
- Evidence:
  ```
  $ python3 -c "import protocol; print('launch-demo' in protocol.UTILITY_SKILLS, protocol.UTILITY_SKILLS)"
  True ['address-pr-review', 'animated-diagram', 'architecture-diagram', 'audit', 'automate', 'autorun', 'deepen', 'doctor', 'factory-init', 'interactive-architecture-diagram', 'launch-demo', 'mermaid', 'pipeline-board', 'work-queue']
  $ ls skills/launch-demo/
  references
  SKILL.md
  $ grep -n "launch-demo" README.md LEDGER.md .claude-plugin/plugin.json docs/assets/skill-map.svg
  docs/assets/skill-map.svg:223:  <text class="row mono" x="60" y="434">launch-demo</text>
  .claude-plugin/plugin.json:3:  "description": "... utility skills (address-pr-review, animated-diagram, architecture-diagram, audit, automate, autorun, deepen, doctor, factory-init, interactive-architecture-diagram, launch-demo, mermaid, pipeline-board, work-queue).",
  README.md:87:| `launch-demo` | Around a pull request | Writes a shipped feature's launch copy in plain words and records a short narrated video whose every line is a sentence of it, from the run's artifacts or the pull request; copy only, with the reason, when a recorder is missing. |
  LEDGER.md:39:| launch-demo | draft | — | — |
  $ python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])"
  0.4.0
  $ git diff main -- .claude-plugin/plugin.json | grep '^[-+]' | grep -v '^[-+][-+]'
  -  "description": "Lifecycle-pipeline skills that guide work from raw idea to production: ...
  -  "version": "0.3.0",
  +  "description": "Lifecycle-pipeline skills that guide work from raw idea to production: ...
  +  "version": "0.4.0",
  $ git diff main --numstat -- evals/routing.json
  26	0	evals/routing.json
  $ git diff main -- evals/routing.json | grep '^+' | grep -E '"id"|"kind"|"expected"' | tr -s ' '
  + "id": "ld-1",
  + "kind": "direct",
  + "expected": "launch-demo",
  + "id": "ld-2",
  + "kind": "situational",
  + "expected": "launch-demo",
  + "id": "ld-vs-ship-1",
  + "kind": "near-miss",
  + "expected": "launch-demo",
  + "id": "ship-vs-ld-1",
  + "kind": "near-miss",
  + "expected": "ship",
  ```
  No `TEMPLATE.md` in the skill directory; the plugin diff is the two
  lines; the eval diff is 26 added lines and 0 removed — four new cases,
  three expecting `launch-demo` and one near-miss expecting `ship`.
- Result: PASS

### Stdlib only; tools are the consuming repo's

- Check: the import sweep the breakdown's close-out row names over
  `launch_demo.py`, `cli.py`, `protocol.py` and
  `tests/test_launch_demo.py`; the `cli.py` diff read for added imports;
  `factory_init.MIRRORS` read for the tool; detector E is in the gates
  run under Battery. That the tests exercise the recorders with injected
  fakes is shown by the suite's `Ran 83 tests in 0.063s` above — 83
  tests in 63 ms invoke no real `say`, `vhs`, `ffmpeg` or `node`.
- Evidence:
  ```
  $ python3 -c "import sys, ast, pathlib; names={(n.names[0].name if isinstance(n, ast.Import) else n.module or '').split('.')[0] for p in ['launch_demo.py','cli.py','protocol.py','tests/test_launch_demo.py'] for n in ast.walk(ast.parse(pathlib.Path(p).read_text())) if isinstance(n,(ast.Import,ast.ImportFrom))}; print(sorted(n for n in names if n not in sys.stdlib_module_names))"
  ['cli', 'cli_contract', 'launch_demo']
  $ git diff main --stat -- cli.py
   cli.py | 35 ++++++++++++++++++++++++-----------
  $ git diff main -- cli.py | grep '^+' | grep -E '^\+\s*(import|from) ' || echo "cli.py diff adds no import"
  cli.py diff adds no import
  $ python3 -c "import factory_init; print('launch_demo.py' in str(factory_init.MIRRORS))"
  False
  ```
  The only non-stdlib names are this repo's own modules; the tool is not
  mirrored (the architecture's decision), and `gates: 0 problem(s)` below
  carries detector E over the regenerated manifest.
- Result: PASS

### Battery

- Check: the three commands on the branch tip before this artifact was
  written, each output captured to a file and its result lines read.
- Evidence:
  ```
  $ python3 --version
  Python 3.14.6
  $ python3 -m unittest discover tests
  Ran 2030 tests in 25.127s
  OK
  $ python3 lint.py
  lint: 0 problem(s) across 26 skills
  $ python3 gates.py
  gates: 0 problem(s)
  $ python3 gates.py --selftest
  selftest: ok
  ```
- Result: PASS

### Breakdown close-out (acceptance no PRD criterion covers)

- Check: every breakdown row checked and one zero-cost owner-session
  ledger row per row, which is what keeps detector G in the green gates
  run above.
- Evidence:
  ```
  $ grep -c "^- \[x\] \*\*WO-" docs/features/launch-demo/breakdown.md
  14
  $ grep -c "^- \[ \] \*\*WO-" docs/features/launch-demo/breakdown.md
  0
  $ grep -oE '"wo": ?"WO-0(09[7-9]|10[0-9]|110)"' docs/factory/costs.jsonl | sort | uniq -c
   1 "wo": "WO-0097"
   ... one line each ...
   1 "wo": "WO-0110"
  $ tail -1 docs/factory/costs.jsonl
  {"wo": "WO-0110", "run_id": "session-2026-10-08-wo-0110", "model": "claude-fable-5-1", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-08"}
  ```
- Result: PASS

## Failures

1. **Terminal recorder, end to end — the tape's `Output` line.**
   `launch_demo._tape` writes `Output {raw.resolve()}` unquoted, and vhs
   0.11.0 answers `Expected file path after output` / `Invalid command:
   private` / `parser: 3 error(s)`; a quoted absolute path records. The
   test at `tests/test_launch_demo.py` lines 576–577 pins the unquoted
   form, so the suite is green on a tape the recorder rejects. Routes to
   Implement: the tape writer and that test (the test asserts a value
   the real recorder refuses, so changing it is correcting the test, not
   bending it).
2. **Terminal recorder, end to end — drift of a vhs recording against
   the computed plan.** With line 1 quoted by hand, the recording ran
   32.36 s where the plan expected 34.431 s (every hold 0.4–0.6 s short
   of its `Sleep` plus typing, about 6 % of the tape), past
   `DRIFT_TOLERANCE = 1.5`, so the tool's own check would refuse this
   storyboard with `launch-demo: recording ran 32.4 s where the plan
   expected 34.4 s — narration would drift`, and the check is right: the
   computed offsets fall late. The gap is proportional, so any storyboard
   past roughly 25 s planned fails it. Routes to Implement, with a note
   for Review: the architecture's "offsets computed for vhs" rests on
   vhs's tape timing being the recorded timing, and here it is not.
3. **Browser recorder, smoke-tested — the driver's home.**
   `record_browser` writes `demo.mjs` into the `tempfile.mkdtemp`
   scratch directory under `/var/folders`, and Node answers `Error
   [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright' imported from
   /private/var/folders/.../launch-demo-_ij6suu7/demo.mjs`: ES-module
   resolution walks up from the importing file, never from the working
   directory the probe resolved from, so `probe` says READY and the
   driver still fails. The architecture's data model has the driver
   written inside the repo for exactly this. With the scratch directory
   inside the repo the same tool produced a 345,650-byte, 26.5 s h264+aac
   mp4 with the title card, the captioned fixture actions and the outro.
   Routes to Implement: where the driver is written (or where the scratch
   directory is made) for the browser adapter.
4. **Browser recorder, smoke-tested — the reason line.** The problem
   string carried `Node.js v22.22.3`, Node's version banner, because
   `cli.detail` takes stderr's last line; the `Error [ERR_MODULE_NOT_FOUND]`
   line sat ten lines up. A brief whose reason line is a version number
   says nothing. Routes to Implement with the third failure (the browser
   adapter could pick the last line that names an error before handing
   stderr to `cli.detail`), and to Review as a question about the
   `cli.detail` convention's fit for Node.

## Not verified

- **A tool-produced terminal `launch.mp4`.** None exists, so its
  `ffprobe` block, duration, title-card frame and the owner's watch
  before merge are all outstanding; the diagnostic recording measured the
  video alone and was not muxed with the narration, so the terminal
  path's narration-to-scene alignment is unobserved.
- **The narration's alignment in the browser mp4.** The diagnostic's
  marks, offsets and the audio track's presence (−19.9 dB mean) were
  checked; nobody listened to the file, so whether each line lands on
  its scene is unobserved.
- **The Ship hook firing live.** Ship has not run for this branch; the
  PRD's check for this criterion is the diff and the lint checkers, which
  pass. Whether Ship, loading the skill, lands on the same two failures
  is for Ship's release log.
- **The browser recorder on a real web app**, and a Linux voice
  (`espeak-ng`, Piper) — both out of this run's scope by PRD-0009; only
  macOS `say` was exercised.
- **The routing eval** (`python3 trigger_eval.py`) was not run — it
  drives the `claude` CLI and costs money; the LEDGER row stays `draft`
  with `—`, as the breakdown's row 0108 planned.
- **Detector B on a live pull request event.** B skips locally without a
  PR event payload; its selftest ran (`selftest: ok`). This run opens no
  PR; Ship does.
- **The hook's "any other `when`" branch and the absent-config branch**
  are stated in the Ship step's text and not exercised; neither has a
  tool half to run.
