---
stage: verify
run: feature:launch-demo
date: 2026-10-10
assumptions:
  - "Re-verification after Implement's fix rows (WO-0111, WO-0112, WO-0113) for the first pass's four Failures. Every one of PRD-0009's ten success criteria was re-demonstrated against the tip `65ba8f7`, not only the two that failed; the first pass (2026-10-08, commit e2da12b) is summarised under Prior verification and kept whole in git history."
  - "No live interview: the soft gate was read from breakdown.md (seventeen rows, all checked) and the criteria list is PRD-0009's ten Success criteria plus two breakdown acceptances no PRD criterion covers: the close-out (every row checked, one ledger row per row) and WO-0113's stated outcome, that a Node failure's reason line names the error."
  - "The terminal subject is still pipeline-board, and its committed storyboard.json was reused unchanged (the skill's happy-path precedence item 1). After the PRODUCED verdict this stage, as the invoker, set launch.md's video: line to launch.mp4 (skill step 7) and commits launch.md, demo.tape and launch.mp4. The architecture's data model decides the mp4 is committed (Git LFS named as the consuming repo's lever if it grows); this one is 432,885 bytes."
  - "The browser smoke test used a throwaway config publishing to .verify-smoke/launches inside the repo, as the first pass did; the directory, node_modules/ and the throwaway config were removed afterwards and docs/launch-demo.json restored with git checkout. Playwright 1.64.0 was installed with npm install --no-save; its chromium headless shell v1248 was already in the user's Playwright cache from the first pass. Nothing from the smoke test is committed except one frame."
  - "The real browser failure was provoked by pointing PLAYWRIGHT_BROWSERS_PATH at an empty scratch directory, so Playwright's own launch fails the way it does on a machine that never ran `npx playwright install`; the user's browser cache was not touched."
  - "Two new PNGs are committed beside this artifact, both frames of tool-produced mp4s and both under 75 KB: title-card.png (the terminal launch.mp4 at 0.5 s) and browser-fixture-step.png (the smoke test's mp4 at 12 s). The first pass's two -diagnostic PNGs stay, as the Prior verification section cites them."
  - "The pull-request copy (#598) is carried forward from the first pass rather than rewritten: its inputs were re-read today and are unchanged (same title, state MERGED, body 1,995 characters), and the copy was re-swept for identifiers."
  - "The macOS voice (/usr/bin/say) is the only voice exercised, as the PRD says."
  - "Second re-verification, 2026-10-10, at `6d550c7` (WO-0125, Failure 5's fix). Not every criterion was re-demonstrated: `git diff 7b868ec..HEAD --stat` shows only launch_demo.py (NODE_ERROR_LINE and a docstring), tests/test_launch_demo.py, breakdown.md and costs.jsonl changed, so evidence for criteria that do not run that code is carried forward by that reasoning (stated under Re-verification at 6d550c7), and the code the change touches — the browser failure path, plus one successful render per recorder as a regression check — was re-run for real."
  - "The regression terminal render rewrote the committed launch.mp4 and demo.tape (different bytes, as any re-recording does: 32.27 s against the committed 33.27 s, and the tape's scratch path); both were restored to HEAD with git checkout, so the committed mp4 remains the one verified at 7b868ec. The browser regression render and the two failures used the same throwaway config, served fixture and npm install --no-save playwright as before, all removed afterwards."
  - "The ESM import failure cannot reach node through `render`, because probe reports playwright missing and degrades to COPY-ONLY first; it was provoked instead by calling launch_demo.record_browser with the real cli.runner from a scratch directory with no node_modules on its path."
---

# Verification: Launch demo

## Summary

**Re-verified 2026-10-10 at `6d550c7`: 10 PASS, 0 FAIL across
PRD-0009's ten success criteria, and both breakdown acceptances no PRD
criterion covers now pass — Failure 5 is resolved by `6d550c7`
(WO-0125).** The same real missing-browser failure that read
`launch-demo: browser recorder failed: Node.js v22.22.3` through
`7b868ec`'s tool now reads `launch-demo: browser recorder failed:
browserType.launch: Executable doesn't exist at …`, and a real ESM
import failure still names `Error [ERR_MODULE_NOT_FOUND]`. One
successful render per recorder after the change: browser 27.53 s,
terminal 32.27 s, both h264+aac 1280x720, `PRODUCED`. The battery is
green. One gap for Review: no test now reaches `_node_reason`'s
`cli.detail` fallback (a mutant of that branch survives the whole
suite). Next stage: Review. The 2026-10-10 pass at `65ba8f7`, below,
holds the full per-criterion evidence.

*Earlier pass, same day:* **Re-verified 2026-10-10 at `65ba8f7`: 10 PASS, 0 FAIL across
PRD-0009's ten success criteria; of the two breakdown acceptances no PRD
criterion covers, the close-out passes and WO-0113's reason line FAILS
on a real Playwright failure.** Both recorders now work end to end as
the skill invokes them: the terminal recorder produced a 33.27 s
h264+aac `launch.mp4` of pipeline-board at the publish path, title card
to outro, with each narration line starting within 0.13 s of its scene;
the browser recorder produced a 27.43 s h264+aac mp4 of the fixture page
from a driver run inside the repo, leaving no scratch directory behind.
The first pass's Failures 1–3 are resolved by `97ee5c5` (WO-0111),
`3c22633` (WO-0112) and `65ba8f7` (WO-0113). Failure 4 is resolved only
for the error class its test names: a real `browserType.launch:
Executable doesn't exist` failure — the most likely browser failure on a
fresh machine — still produces the reason line `Node.js v22.22.3`,
because Playwright's message is printed without the `Error:` prefix the
test assumed. Next stage: Implement, for that one reason-line case;
every PRD criterion holds.

Worktree HEAD `65ba8f7`, twenty-two commits ahead of `main` `736f54b`;
interpreter `Python 3.14.6`; vhs 0.11.0 with ttyd, ffmpeg 8.1, ffprobe,
`/usr/bin/say`, node v22.22.3, Playwright 1.64.0 (installed for the
smoke test, removed after), gh authenticated.

## Re-verification at `6d550c7` (2026-10-10)

### What changed, and which evidence still holds

- Check: the diff since the last full pass (`7b868ec`, which recorded
  the evidence below against code at `65ba8f7`).
- Evidence:
  ```
  $ git diff 7b868ec..HEAD --stat
   docs/factory/costs.jsonl               |  1 +
   docs/features/launch-demo/breakdown.md | 35 ++++++++++++++++++++++++++++++++
   launch_demo.py                         | 10 +++++----
   tests/test_launch_demo.py              | 37 +++++++++++++++++++++++++++++-----
   4 files changed, 74 insertions(+), 9 deletions(-)
  $ git diff 7b868ec..HEAD -- cli.py factory | wc -l
         0
  ```
  The `launch_demo.py` change is the `NODE_ERROR_LINE` regex (from
  `(?:[A-Z]\w*)?Error\b` to `[A-Za-z_$][\w$.]*(?: \[\w+\])?: \S`) and
  `_node_reason`'s docstring; `_node_reason` is its one caller, and it
  runs only when the browser driver's `node` run raises.
- Reasoning, stated rather than silently carried forward: no skill
  text, config schema, copy, storyboard, terminal-recorder, voice,
  mux, Ship-hook, lint, gate or payload file changed, so the evidence
  for *Copy from artifacts*, *Copy-only degradation*, *A free voice*,
  *Per-repo config*, *Two triggers*, *A utility skill* and *Stdlib
  only* holds as recorded at `65ba8f7`. The two recorder criteria share
  the changed module, so each got one fresh successful render below
  (the regex is on the browser failure path only, but the widening is
  the kind of change whose blast radius is cheaper to observe than to
  argue). The battery and close-out were re-run.

### Failure 5, re-demonstrated: the missing-browser reason line

- Check: Playwright 1.64.0 installed (`npm install --no-save
  playwright`), the fixture served on 8765, the throwaway browser config
  (publish `.verify-smoke/launches`, fixture copy and storyboard copied
  to `fixture/` and `fail/`), `PLAYWRIGHT_BROWSERS_PATH` at an empty
  scratch directory; `render fail` through the tip's tool, then the same
  render through `7b868ec`'s `launch_demo.py` (written to an untracked
  `launch_demo_before.py` at the repo root, removed after).
- Evidence, after (`6d550c7`):
  ```
  $ python3 launch_demo.py config
  launch-demo: 0 problem(s)
  $ python3 launch_demo.py probe
  READY
  launch-demo: 0 problem(s)
  $ env PLAYWRIGHT_BROWSERS_PATH=<scratch>/emptybrowsers python3 launch_demo.py render fail
  launch-demo: scratch /var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-p4gei9jt
  launch-demo: browser recorder failed: browserType.launch: Executable doesn't exist at /private/tmp/claude-501/-Users-mbutler-github-skills/7b6c638e-1174-4638-8f1b-d6e10c607be7/scratchpad/emptybrowsers/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell
  launch-demo: 1 problem(s)
  exit=1
  $ ls -A .verify-smoke/launches/fail/
  launch.md
  storyboard.json
  $ ls -d launch-demo-* 2>/dev/null || echo "no launch-demo-* directory at the repo root"
  no launch-demo-* directory at the repo root
  ```
- Evidence, before (`7b868ec`'s tool, same environment, same minute):
  ```
  $ env PLAYWRIGHT_BROWSERS_PATH=<scratch>/emptybrowsers python3 launch_demo_before.py render fail
  launch-demo: scratch /var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-ujrm_lmd
  launch-demo: browser recorder failed: Node.js v22.22.3
  launch-demo: 1 problem(s)
  exit=1
  ```
- Evidence, the ESM import failure (a real `node` run via
  `record_browser` and the real `cli.runner`, from a scratch directory
  with no `node_modules` in it or its two parents; `render` cannot reach
  this case because `probe` degrades to COPY-ONLY first — shown):
  ```
  $ cd <scratch>/esm && python3 <repo>/launch_demo.py render fail
  launch-demo: missing playwright — records the browser; install: npm install playwright && npx playwright install chromium, from the repo root
  COPY-ONLY
  launch-demo: 0 problem(s)
  $ cd <scratch>/esm && python3 -c "... launch_demo.record_browser(launch_demo.plan(board, [2.0]*n), '<scratch>/esm-work', 'http://127.0.0.1:8765')"
  (None, ["launch-demo: browser recorder failed: Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright' imported from /private/tmp/claude-501/-Users-mbutler-github-skills/7b6c638e-1174-4638-8f1b-d6e10c607be7/scratchpad/esm/launch-demo-_t5x5nrv/demo.mjs"])
  no launch-demo-* left in cwd
  ```
- Result: PASS — both real failure classes now name their error; the
  driver's directory is removed after each.

### Regression: one successful render per recorder

- Evidence, browser (chromium headless shell v1248 already cached;
  `npx playwright install chromium` printed nothing):
  ```
  $ python3 launch_demo.py render fixture
  launch-demo: scratch /var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-3u_vqe0a
  launch-demo: wrote .verify-smoke/launches/fixture/demo.mjs
  launch-demo: wrote .verify-smoke/launches/fixture/launch.mp4
  ...
  PRODUCED
  launch-demo: 0 problem(s)
  exit=0 (34s wall)
  no launch-demo-* directory at the repo root
  $ ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt:format=duration,size .verify-smoke/launches/fixture/launch.mp4
  codec_name=h264 codec_type=video width=1280 height=720 pix_fmt=yuv420p r_frame_rate=30/1
  codec_name=aac codec_type=audio
  duration=27.533333 size=347828
  ```
- Evidence, terminal (committed config restored first:
  `{"when": "ship", "recorder": "terminal", "against": "bash",
  "publish": "docs/launches"}`):
  ```
  $ python3 launch_demo.py probe
  READY
  $ python3 launch_demo.py render pipeline-board
  launch-demo: scratch /var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-g62hfgv8
  launch-demo: wrote docs/launches/pipeline-board/demo.tape
  launch-demo: wrote docs/launches/pipeline-board/launch.mp4
  ...
  PRODUCED
  launch-demo: 0 problem(s)
  exit=0 (81s wall)
  $ ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt:format=duration,size docs/launches/pipeline-board/launch.mp4
  codec_name=h264 codec_type=video width=1280 height=720 pix_fmt=yuv420p r_frame_rate=30/1
  codec_name=aac codec_type=audio
  duration=32.266667 size=428186
  $ git diff docs/launches/pipeline-board/demo.tape   (the scratch path only)
  -Output "/private/var/folders/.../launch-demo-5gf98v7d/raw.mp4"
  +Output "/private/var/folders/.../launch-demo-g62hfgv8/raw.mp4"
  $ git checkout -- docs/launches/pipeline-board/demo.tape docs/launches/pipeline-board/launch.mp4
  $ shasum -a 256 docs/launches/pipeline-board/launch.mp4
  c6584773a9ae46cac8f6a7b519448c83e0f659575fa44444b8dec7d73f988a49   (HEAD's, as before the render)
  ```
  The re-recording is 1.0 s shorter than the committed 33.27 s one; the
  drift scaling of WO-0112 absorbs run-to-run vhs timing, so this is
  ordinary recording variance, not a change in the tool. The committed
  mp4 was kept — the one verified frame by frame at `7b868ec`.
- Result: PASS — neither recorder regressed.

### Battery and close-out at `6d550c7`

- Evidence:
  ```
  $ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
  Ran 2035 tests in 24.401s
  OK
  $ python3 lint.py | tail -1
  lint: 0 problem(s) across 26 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  $ wc -l launch_demo.py
       794 launch_demo.py
  $ grep -c "^- \[x\] \*\*WO-" docs/features/launch-demo/breakdown.md; grep -c "^- \[ \] \*\*WO-" docs/features/launch-demo/breakdown.md
  18
  0
  $ tail -1 docs/factory/costs.jsonl
  {"wo": "WO-0125", "run_id": "session-2026-10-10-wo-0125", "model": "claude-opus-5-5", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-10"}
  ```
- Result: PASS

### Gap for Review: `_node_reason`'s `cli.detail` fallback is untested

- Check: Implement's breakdown assumption says the widened rule now
  sends `test_a_node_failure_with_no_error_line_keeps_the_last_line`'s
  stderr (`node: bad option: --nope`) through the error-line branch, so
  no test asserts the fallback. Shown by mutating that branch and
  running the whole suite (restored with `git checkout` after):
  ```
  $ sed -i '' 's/... else cli.detail(err)/... else "MUTANT"/' launch_demo.py
  $ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
  Ran 2035 tests in 24.480s
  OK
  $ python3 -c "... launch_demo._node_reason(subprocess.CalledProcessError(1, ['node'], stderr='boom\n'))"
  'boom'
  ```
  The branch works when reached (`boom` → `boom`), but a mutant of it
  survives every test. Not a criterion failure; a test gap for Review
  (a stderr like `boom` would pin it).

## Criteria & evidence (full pass at `65ba8f7`)

### Terminal recorder, end to end

- Check: the `launch-demo` skill followed as written for one of this
  plugin's own skills — `pipeline-board` — under this repo's committed
  config (`terminal`, `bash`, `docs/launches`): the `config` and `probe`
  legs, the committed storyboard reused (precedence item 1) and held to
  the copy, the `render pipeline-board` leg from the repo root, then
  `launch.md`'s `video:` line settled from the verdict. The mp4 was
  `ffprobe`d, four frames extracted and viewed, and the narration's
  onsets measured against the recording's scene changes.
- Evidence, the `config` and `probe` legs and the storyboard check:
  ```
  $ python3 skills/launch-demo/../../launch_demo.py config
  launch-demo: 0 problem(s)
  exit=0
  $ python3 skills/launch-demo/../../launch_demo.py probe
  READY
  launch-demo: 0 problem(s)
  exit=0
  $ python3 -c "... launch_demo.check_storyboard(board, launch_demo._body(copy), 'terminal')"
  check_storyboard: []
  ```
- Evidence, the `render` leg (one invocation, 81 s wall):
  ```
  $ python3 skills/launch-demo/../../launch_demo.py render pipeline-board
  launch-demo: scratch /var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-5gf98v7d
  launch-demo: wrote docs/launches/pipeline-board/demo.tape
  launch-demo: wrote docs/launches/pipeline-board/launch.mp4
  launch-demo: [STREAM]
  launch-demo: codec_name=h264
  launch-demo: codec_type=video
  launch-demo: [/STREAM]
  launch-demo: [STREAM]
  launch-demo: codec_name=aac
  launch-demo: codec_type=audio
  launch-demo: [/STREAM]
  launch-demo: [FORMAT]
  launch-demo: duration=33.266667
  launch-demo: [/FORMAT]
  PRODUCED
  launch-demo: 0 problem(s)
  exit=0 (81 s wall)
  $ ls -la docs/launches/pipeline-board/
  -rw-r--r--  1 mbutler  staff    1046 Oct 10 11:20 demo.tape
  -rw-r--r--  1 mbutler  staff    1193 Oct  8 14:29 launch.md
  -rw-r--r--  1 mbutler  staff  432885 Oct 10 11:20 launch.mp4
  -rw-r--r--  1 mbutler  staff     779 Oct  8 14:23 storyboard.json
  $ head -1 docs/launches/pipeline-board/demo.tape
  Output "/private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-5gf98v7d/raw.mp4"
  ```
- Evidence, `ffprobe` of the published file:
  ```
  $ ffprobe -v error -show_entries stream=index,codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels,duration:format=duration,size docs/launches/pipeline-board/launch.mp4
  [STREAM]
  index=0
  codec_name=h264
  codec_type=video
  width=1280
  height=720
  pix_fmt=yuv420p
  r_frame_rate=30/1
  duration=33.266667
  [/STREAM]
  [STREAM]
  index=1
  codec_name=aac
  codec_type=audio
  sample_rate=22050
  channels=1
  r_frame_rate=0/0
  duration=32.980000
  [/STREAM]
  [FORMAT]
  duration=33.266667
  size=432885
  [/FORMAT]
  ```
  One video stream, one audio stream. **Duration: 33.27 s** (the
  audio track 32.98 s).
- Evidence, narration offsets against the recording. The raw vhs
  recording ran 33.28 s against the plan's 34.431 s, a ratio of 0.9666
  — inside `DRIFT_BAND = (0.75, 1.25)` — so `record_terminal` scaled the
  planned offsets; the published mp4's screen changes and the narration
  track's onsets were then measured independently:
  ```
  $ for f in line-1..4.wav raw.mp4; do ffprobe ... format=duration; done   (scratch dir above)
  line-1.wav 5.797324
  line-2.wav 5.349342
  line-3.wav 7.541315
  line-4.wav 5.493333
  raw.mp4 33.280000
  $ python3 -c "... launch_demo.plan(board, secs)"   -> offsets [0.0, 6.297, 15.497, 28.438], planned 34.431
  $ python3 -c "r=33.28/34.431; ..."
  ratio 0.9666 [0.0, 6.086, 14.979, 27.487]
  $ ffmpeg -i launch.mp4 -vf "freezedetect=n=0.0005:d=0.4" -an -f null -    (screen-change times)
  freeze_start: 0         freeze_end: 6
  freeze_start: 9.433333  freeze_end: 14.966667
  freeze_start: 22.666667 freeze_end: 27.566667
  $ ffmpeg -i launch.mp4 -af silencedetect=noise=-35dB:d=0.3 -vn -f null -
  silence_start: 5.71805   silence_end: 6.125215
  silence_start: 11.379637 silence_end: 14.999093
  silence_start: 19.455102 silence_end: 19.775238
  silence_start: 22.462177 silence_end: 27.515329
  $ ffmpeg -i launch.mp4 -af volumedetect -vn -f null -
  mean_volume: -20.9 dB
  max_volume: -1.1 dB
  ```
  | Scene | Scaled offset | Screen changes | Narration starts |
  |---|---|---|---|
  | step 1 | 6.086 s | 6.0 s | 6.125 s |
  | step 2 | 14.979 s | 14.967 s | 14.999 s |
  | outro | 27.487 s | 27.567 s | 27.515 s |

  Each narration line starts within 0.13 s of its scene (the
  19.46–19.78 s gap is a pause inside line 3, which runs 7.54 s from
  15.0 s).
- Evidence, captions equal narration and every line is cut from the
  copy (the published tape against the storyboard and `launch.md`):
  ```
  narration lines: 4 | on-screen prints: 4
  MISMATCH | sentence of launch.md: True | The pipeline board is a one-page picture of every piece... | shown: The pipeline board
  caption == narration | sentence of launch.md: True | You ask for the board and a small tool reads every run'... | shown: You ask for the board and a small tool r
  caption == narration | sentence of launch.md: True | It lists every active run once, tells feature work from... | shown: It lists every active run once, tells fe
  caption == narration | sentence of launch.md: True | Instead of walking folders and running commands, you fi... | shown: Instead of walking folders and running c
  ```
  The one mismatch is by design: the title card shows the title and
  tagline while the intro is spoken; the two step captions and the outro
  are the narration lines verbatim.
- Frames viewed (extracted with `ffmpeg -ss <t> -i launch.mp4
  -frames:v 1`):
  - **0.5 s** — the title card: a dark terminal with **The pipeline
    board** in bold, "Every run, on its step, at a glance" beneath, and
    a `>` prompt ([`title-card.png`](title-card.png), 21,797 bytes).
  - **11 s** — the dim caption "You ask for the board and a small tool
    reads every run's notes to state which step each one is on.", then
    the typed `python3 board.py . | jq '{generated, repo, runs: (.runs |
    length)}'` and its output, `"runs": 59`.
  - **21 s** — the second caption (wrapping mid-word at the frame's
    edge, "the b / uilding step"), the `jq -c` command, and ten
    `["stage","state"]` lines for this run, `review` marked `current`.
  - **31 s** — the outro sentence alone in bold over a prompt.
- Evidence, the brief's `video:` line settled from the verdict (skill
  step 7):
  ```
  $ head -6 docs/launches/pipeline-board/launch.md
  ---
  launch: pipeline-board
  date: 2026-10-08
  sources: [docs/features/pipeline-board/prd.md, docs/features/pipeline-board/verification.md, docs/features/pipeline-board/release.md]
  video: launch.mp4
  ---
  ```
- Result: PASS — the owner watches the mp4 before merge, per the brief's
  Release authorization (Not verified below).

### Browser recorder, smoke-tested

- Check: Playwright installed without touching tracked files (`npm
  install --no-save playwright`, `npx playwright install chromium`); the
  committed fixture served by `python3 -m http.server --directory
  tests/fixtures/launch-demo 8765`; a throwaway config (`browser`,
  `against` `http://127.0.0.1:8765`, publish `.verify-smoke/launches`)
  in place of the committed one; the committed fixture `launch.md` and
  `storyboard.json` copied to `.verify-smoke/launches/fixture/`; `probe`
  and `render fixture` before and after the install, from the repo root;
  then two real failures. **This proves the recorder on a fixture, not on
  a web app.**
- Evidence, the throwaway config, and the probe and render before
  Playwright existed:
  ```
  $ curl -sI http://127.0.0.1:8765/ | head -1
  HTTP/1.0 200 OK
  $ cat docs/launch-demo.json
  {"when": "on-demand", "recorder": "browser", "against": "http://127.0.0.1:8765", "publish": ".verify-smoke/launches"}
  $ python3 launch_demo.py config
  launch-demo: 0 problem(s)
  $ python3 launch_demo.py probe
  launch-demo: missing playwright — records the browser; install: npm install playwright && npx playwright install chromium, from the repo root
  COPY-ONLY
  launch-demo: 0 problem(s)
  exit=0
  $ python3 launch_demo.py render fixture
  launch-demo: missing playwright — records the browser; install: npm install playwright && npx playwright install chromium, from the repo root
  COPY-ONLY
  launch-demo: 0 problem(s)
  exit=0
  $ ls -A .verify-smoke/launches/fixture/
  launch.md
  storyboard.json
  ```
- Evidence, the install, the probe after it, and the render:
  ```
  $ npm install --no-save playwright
  added 2 packages, and audited 3 packages in 632ms
  found 0 vulnerabilities
  $ node -e "console.log(require('playwright/package.json').version)"
  1.64.0
  $ npx playwright install chromium        (no output: v1248 already cached)
  $ python3 launch_demo.py probe
  READY
  launch-demo: 0 problem(s)
  exit=0
  $ python3 launch_demo.py render fixture
  launch-demo: scratch /var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-j315uczu
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
  launch-demo: duration=27.433333
  launch-demo: [/FORMAT]
  PRODUCED
  launch-demo: 0 problem(s)
  exit=0 (36 s wall)
  $ ls -d launch-demo-* 2>/dev/null || echo "no launch-demo-* directory at the repo root"
  no launch-demo-* directory at the repo root
  ```
- Evidence, `ffprobe` of the mp4, the measured marks and the narration:
  ```
  $ ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt:format=duration,size .verify-smoke/launches/fixture/launch.mp4
  [STREAM]
  codec_name=h264
  codec_type=video
  width=1280
  height=720
  pix_fmt=yuv420p
  r_frame_rate=30/1
  [/STREAM]
  [STREAM]
  codec_name=aac
  codec_type=audio
  r_frame_rate=0/0
  [/STREAM]
  [FORMAT]
  duration=27.433333
  size=346484
  [/FORMAT]
  $ cat .../launch-demo-j315uczu/marks.json
  [1791656509112,1791656509112,1791656516479,1791656520806,1791656525919]
  $ ffmpeg -i launch.mp4 -af silencedetect=noise=-35dB:d=0.3 -vn -f null -
  silence_start: 6.687211   silence_end: 7.414422
  silence_start: 10.920635  silence_end: 11.748027
  silence_start: 16.166168  silence_end: 16.896553
  $ ffmpeg -i launch.mp4 -af volumedetect -vn -f null -
  mean_volume: -19.9 dB
  max_volume: -1.0 dB
  ```
  The marks give scene offsets of 0.0, 7.367, 11.694 and 16.807 s; the
  narration starts at 7.414, 11.748 and 16.897 s — each within 0.09 s.
- Frames viewed: **0.5 s** — the dark title card, **Counter and
  greeter** over "The browser recorder, proved on a fixture"; **12 s** —
  the fixture page with "Clicks so far: **2**", the name field holding
  "Ada", "Hello, Ada!" beneath, and the caption bar along the bottom
  reading "Typing a name and pressing the greeting button writes a hello
  to that name beneath it."
  ([`browser-fixture-step.png`](browser-fixture-step.png), 72,204
  bytes); **26.5 s** — the outro card, "A recorder that can count and
  greet here can drive a real product page the same way." alone in bold.
- Evidence, two real failures. First, Playwright's browser missing
  (`PLAYWRIGHT_BROWSERS_PATH` at an empty scratch directory); second, the
  page unreachable (server stopped):
  ```
  $ env PLAYWRIGHT_BROWSERS_PATH=<empty dir> python3 launch_demo.py render fail
  launch-demo: scratch /var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-qxjhg547
  launch-demo: browser recorder failed: Node.js v22.22.3
  launch-demo: 1 problem(s)
  exit=1
  $ ls -A .verify-smoke/launches/fail/
  launch.md
  storyboard.json
  $ ls -d launch-demo-* 2>/dev/null || echo "no launch-demo-* directory at the repo root"
  no launch-demo-* directory at the repo root
  $ kill $(cat http.pid); curl -sI --max-time 2 http://127.0.0.1:8765/ || echo "server stopped"
  server stopped
  $ python3 launch_demo.py render fail   (server stopped)
  launch-demo: against http://127.0.0.1:8765 is unreachable: [Errno 61] Connection refused
  COPY-ONLY
  launch-demo: 0 problem(s)
  exit=0
  ```
  Both failures write no video and leave no scratch directory in the
  repo. The unreachable page's reason line names the cause. The missing
  browser's does not — see the WO-0113 section below.
- Evidence, the clean-up:
  ```
  $ rm -rf node_modules package-lock.json .verify-smoke && git checkout -- docs/launch-demo.json && cat docs/launch-demo.json && git status --short
  {"when": "ship", "recorder": "terminal", "against": "bash", "publish": "docs/launches"}
   M docs/launches/pipeline-board/launch.md
  ?? docs/launches/pipeline-board/demo.tape
  ?? docs/launches/pipeline-board/launch.mp4
  $ pgrep -fl "http.server" || echo "no http.server running"
  no http.server running
  ```
- Result: PASS — the criterion is the recording, produced as the skill
  invokes it; the reason-line defect on one failure class is recorded
  against WO-0113's acceptance, not this criterion.

### Copy from artifacts, or from the pull request

- Check: for the run directory, `pipeline-board`'s `prd.md`,
  `verification.md` and `release.md` are the `sources:` of the committed
  `docs/launches/pipeline-board/launch.md`, the brief the terminal render
  above used. For the pull request, #598 (no run directory, no changelog
  in this repo): its inputs were re-read today, and the copy written from
  them in the first pass is carried forward (frontmatter assumptions).
  Both bodies were swept for a path, function, flag or typed id.
- Evidence, the inputs re-read and the identifier sweep:
  ```
  $ gh pr view 598 --json title,body,state,mergedAt -q '...'
  title: feat(decompose): check the draft for placeholders and drifting names before review
  state: MERGED merged 2026-10-07T20:14:34Z
  body chars: 1995
  $ ls | grep -i changelog || echo "no changelog file at the repo root"
  no changelog file at the repo root
  $ ls docs/features | grep -i decompose || echo "no run directory named for decompose"
  no run directory named for decompose
  $ sed -n '/^# Launch/,$p' docs/launches/pipeline-board/launch.md | grep -nE '[a-z_]+\.(py|md|json)|`|--|[a-z]+_[a-z]+\(|PRD-|WO-|ADR-' || echo "run-dir copy: no path, function, flag or typed id"
  run-dir copy: no path, function, flag or typed id
  $ sed -n '/^# Launch/,$p' pr-copy.md | grep -nE '...|#[0-9]' || echo "pr copy: no path, function, flag or typed id"
  pr copy: no path, function, flag or typed id
  ```
- Evidence, the run-directory copy, from `docs/features/pipeline-board/
  prd.md`, `verification.md` and `release.md`:
  ```
  ---
  launch: pipeline-board
  date: 2026-10-08
  sources: [docs/features/pipeline-board/prd.md, docs/features/pipeline-board/verification.md, docs/features/pipeline-board/release.md]
  video: launch.mp4
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
- Evidence, the pull-request copy, from #598's title and body (`pr:
  #598`):
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
  Both copies have the three labelled parts; the `sources:` frontmatter
  names what was read, as the skill's template requires.
- Result: PASS

### Copy-only degradation

- Check: the `probe` and `render pipeline-board` legs with
  `PATH=/nonexistent` (hiding `/usr/bin/say` and the Homebrew tools) and
  the interpreter by absolute path, with the just-produced `launch.mp4`
  and `demo.tape` moved aside for the run so the `ls` is honest, then
  restored (checksum unchanged). The browser config's copy-only legs are
  under the browser criterion above.
- Evidence:
  ```
  $ shasum launch.mp4    (moved aside)
  449aad69c2d16ccf14cc5891cb7795617b4f5c68
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
  -rw-r--r--  1 mbutler  staff  1137 Oct 10 11:21 launch.md
  -rw-r--r--  1 mbutler  staff   779 Oct  8 14:23 storyboard.json
  $ find docs/launches -name '*.mp4' | wc -l
         0
  $ shasum docs/launches/pipeline-board/launch.mp4    (restored)
  449aad69c2d16ccf14cc5891cb7795617b4f5c68
  ```
  Each missing tool is named with its purpose and install hint, the
  verdict is COPY-ONLY, the exit is 0, and the publish path holds the
  copy and the storyboard only — no placeholder, no empty mp4.
  Playwright's `missing playwright` line is quoted under the browser
  criterion.
- Result: PASS

### A free voice, no key, no spend by default

- Check: the grep over the tool and the skill for a hosted endpoint or
  key; the reference's documented swap; and the real narration, rendered
  by `/usr/bin/say` under the platform default (no `voice` in the
  committed config) in both renders above.
- Evidence:
  ```
  $ grep -rniE 'elevenlabs|openai|api_key|api-key|bearer' launch_demo.py skills/launch-demo/
  grep exit=1   (no match)
  $ grep -n "say --data-format\|espeak-ng -w\|piper --model\|hosted voice" skills/launch-demo/references/brief-grammar.md
  43:- macOS: `say --data-format=LEI16@22050 -o {out}`
  44:- elsewhere: `espeak-ng -w {out}` (one distribution package, no model
  48:(`piper --model en_US-lessac-medium.onnx --output_file {out}`), or a
  49:wrapper script around a hosted voice. A hosted voice's key is its own
  $ ls .../launch-demo-5gf98v7d/      (the terminal render's scratch: say's WAVs)
  demo.tape line-1.wav line-2.wav line-3.wav line-4.wav raw.mp4
  ```
- Result: PASS

### Per-repo config, validated

- Check: the tests that pin each field's exact problem string through
  `launch_demo.load` (`tests/test_launch_demo.py`, class `TestLoad`; the
  pinned strings are listed in the first pass and unchanged by the fix
  rows), the module's tests run, and four malformed configs run live
  through the `config` leg against scratch edits of
  `docs/launch-demo.json`, restored afterwards.
- Evidence:
  ```
  $ python3 -m unittest tests.test_launch_demo
  Ran 88 tests in 0.068s
  OK
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
  $ echo '{}' > docs/launch-demo.json; python3 launch_demo.py config
  launch-demo: docs/launch-demo.json has no when
  launch-demo: docs/launch-demo.json has no recorder
  launch-demo: docs/launch-demo.json has no against
  launch-demo: docs/launch-demo.json has no publish
  launch-demo: 4 problem(s)
  exit=1
  $ (recorder browser, against "bash"); python3 launch_demo.py config
  launch-demo: docs/launch-demo.json against must be an http(s) URL for the browser recorder
  launch-demo: 1 problem(s)
  exit=1
  $ (file moved away); python3 launch_demo.py config
  launch-demo: missing docs/launch-demo.json
  launch-demo: 1 problem(s)
  exit=1
  $ git checkout -- docs/launch-demo.json && cat docs/launch-demo.json
  {"when": "ship", "recorder": "terminal", "against": "bash", "publish": "docs/launches"}
  ```
  An absent `voice` takes the default (the committed config has none and
  both renders narrated with `say`); every other absent or malformed
  field is a label-prefixed problem.
- Result: PASS

### Two triggers, Ship otherwise untouched

- Check: `git diff main -- skills/ship/`, `git diff main --
  skills/next/`, lint's `check_skill_recitals` and `check_router`, and
  direct invocation with no run in flight (both renders above).
- Evidence:
  ```
  $ git diff main --stat -- skills/ship/ skills/next/
   skills/ship/SKILL.md | 18 ++++++++++++++----
   1 file changed, 14 insertions(+), 4 deletions(-)
  $ git diff main -- skills/next/ | wc -c
         0
  $ git diff main -- skills/ship/ | grep '^[-+]' | grep -v '^[-+][-+]'
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
  $ python3 -c "import lint, pathlib; print(lint.check_skill_recitals(pathlib.Path('.'))); print(lint.check_router(pathlib.Path('.')))"
  []
  []
  ```
  The Ship diff is the one new step and four renumbered leading digits;
  `skills/next/` is byte-identical to `main`.
- Result: PASS

### A utility skill, on every roster

- Check: the roster surfaces read directly and the two diffs the PRD
  names; `lint: 0 problem(s)` is under Battery.
- Evidence:
  ```
  $ python3 -c "import protocol; print('launch-demo' in protocol.UTILITY_SKILLS)"
  True
  $ ls skills/launch-demo/
  references
  SKILL.md
  $ grep -n "launch-demo" README.md LEDGER.md docs/assets/skill-map.svg | cut -c1-120
  docs/assets/skill-map.svg:223:  <text class="row mono" x="60" y="434">launch-demo</text>
  README.md:87:| `launch-demo` | Around a pull request | Writes a shipped feature's launch copy in plain words and records
  LEDGER.md:39:| launch-demo | draft | — | — |
  $ python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])"
  0.4.0
  $ git diff main -- .claude-plugin/plugin.json | grep '^[-+]' | grep -v '^[-+][-+]' | cut -c1-60
  -  "description": "Lifecycle-pipeline skills that guide work
  -  "version": "0.3.0",
  +  "description": "Lifecycle-pipeline skills that guide work
  +  "version": "0.4.0",
  $ git diff main --numstat -- evals/routing.json
  26	0	evals/routing.json
  $ git diff main -- evals/routing.json | grep '^+' | grep -E '"expected"' | sort | uniq -c
     3 +      "expected": "launch-demo",
     1 +      "expected": "ship",
  ```
  No `TEMPLATE.md`; the plugin diff is the description and the version;
  the eval diff is additive — three cases expecting `launch-demo` and one
  near-miss expecting `ship`. The plugin description names `launch-demo`
  (first pass's grep; the file is unchanged since).
- Result: PASS

### Stdlib only; tools are the consuming repo's

- Check: an import sweep over every `.py` file this branch adds or
  changes against `main` (wider than the first pass's four files); the
  `cli.py` diff for added imports; whether the fix rows touched `cli.py`
  or the manifest; `factory_init.MIRRORS` for the tool; detector E under
  Battery. The module's 88 tests in 68 ms run no real `say`, `vhs`,
  `ffmpeg` or `node` (injected fake runners).
- Evidence:
  ```
  $ git diff main --name-only --diff-filter=AM -- '*.py'
  cli.py
  factory.py
  factory/templates/tools/factory/cli.py
  factory/templates/tools/factory/protocol.py
  launch_demo.py
  protocol.py
  tests/test_cli.py
  tests/test_launch_demo.py
  $ python3 -c "... absolute imports in those files not in sys.stdlib_module_names"
  ['cli', 'cli_contract', 'launch_demo']
  $ git diff main -- cli.py | grep -E '^\+\s*(import|from) ' || echo "cli.py diff adds no import"
  cli.py diff adds no import
  $ git diff 97ee5c5~1 65ba8f7 --stat -- cli.py factory/manifest.json
  (empty)
  $ python3 -c "import factory_init; print('launch_demo.py' in str(factory_init.MIRRORS))"
  False
  ```
  The only non-stdlib names are this repo's own modules; the tool is not
  mirrored (the architecture's decision), and the fix rows changed
  neither `cli.py` nor the manifest.
- Result: PASS

### Battery

- Check: the three commands on the branch tip `65ba8f7` (with only the
  launch directory's render outputs uncommitted).
- Evidence:
  ```
  $ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
  Ran 2035 tests in 24.981s
  OK
  $ python3 lint.py | tail -1
  lint: 0 problem(s) across 26 skills
  $ python3 gates.py && python3 gates.py --selftest
  gates: 0 problem(s)
  selftest: ok
  ```
- Result: PASS

### Breakdown close-out (acceptance no PRD criterion covers)

- Check: every breakdown row checked, and one zero-cost owner-session
  ledger row per row, which keeps detector G green.
- Evidence:
  ```
  $ grep -c "^- \[x\] \*\*WO-" docs/features/launch-demo/breakdown.md
  17
  $ grep -c "^- \[ \] \*\*WO-" docs/features/launch-demo/breakdown.md
  0
  $ grep -oE '"wo": ?"WO-0(09[7-9]|1[01][0-9])"' docs/factory/costs.jsonl | sort | uniq -c
  1 "WO-0097" ... 1 "WO-0113"   (seventeen ids, one row each)
  $ tail -1 docs/factory/costs.jsonl
  {"wo": "WO-0113", "run_id": "session-2026-10-10-wo-0113", "model": "claude-opus-5-5", "tokens": 0, "cost": 0.0, "outcome": "owner-session:unmetered", "at": "2026-10-10"}
  ```
- Result: PASS

### WO-0113: a Node failure's reason line names the error (breakdown acceptance no PRD criterion covers)

- Check: the row's title promises that "a Node failure's reason names the
  error". Its tests pin two stderr shapes; this check feeds the tool's
  `_node_reason` the real stderr of two real driver failures on this
  machine — the ESM import failure the first pass hit, and Playwright's
  missing browser — and runs the second through `render` (the browser
  section above).
- Evidence, the missing-browser driver run by hand from a `launch-demo-`
  directory under the repo root (removed after), exactly as the tool
  runs it:
  ```
  $ env PLAYWRIGHT_BROWSERS_PATH=<empty dir> node launch-demo-verifyhand/demo.mjs http://127.0.0.1:8765 <scratch>
  node exit=1
  node:internal/modules/run_main:123
      triggerUncaughtException(
      ^

  browserType.launch: Executable doesn't exist at <empty dir>/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell
  ╔════════════════════════════════════════════════════════════╗
  ║ Looks like Playwright was just installed or updated.       ║
  ║ Please run the following command to download new browsers: ║
  ║                                                            ║
  ║     npx playwright install                                 ║
  ║                                                            ║
  ║ <3 Playwright Team                                         ║
  ╚════════════════════════════════════════════════════════════╝
      at /Users/mbutler/github/skills/.claude/worktrees/launch-demo/launch-demo-verifyhand/demo.mjs:29:32 {
    log: [],
    name: 'Error'
  }

  Node.js v22.22.3
  ```
- Evidence, both real stderrs through the tool's reason function:
  ```
  $ python3 -c "... launch_demo._node_reason(subprocess.CalledProcessError(1, ['node'], stderr=<file>))"
  node-esm.txt -> "Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright' imported from /private/var/folders/gg/64y63jcn16z3gtn6131f3tfc0000gn/T/launch-demo-qxjhg547/demo.mjs"
  node-fail.txt -> 'Node.js v22.22.3'
  $ sed -n 1104,1110p tests/test_launch_demo.py
      def test_a_failing_node(self):
          err = subprocess.CalledProcessError(
              1, ["node"], stderr="node:internal\nError: browserType.launch:"
                                  " Executable doesn't exist\n")
  ```
  The ESM failure's reason now names the error. Playwright's real
  uncaught error is printed by Node as its bare message,
  `browserType.launch: Executable doesn't exist at …`, with no `Error:`
  prefix (the class appears only as `name: 'Error'` in the property dump),
  so `NODE_ERROR_LINE` matches nothing and the reason falls back to
  `cli.detail`'s last line, Node's version banner. The test's stderr
  invents an `Error: ` prefix the real output does not carry — the same
  shape as the first pass's Failure 1, a test green on a value the real
  tool never produces.
- Result: FAIL — routed to Implement under Failures (5).
  Since resolved by `6d550c7` (WO-0125) — see Re-verification at
  `6d550c7` above.

## Failures

1. **Resolved by `97ee5c5` (WO-0111).** *Terminal recorder — the tape's
   `Output` line.* The tape now writes `Output "<abs path>"`; vhs parsed
   it and recorded (the render above, `demo.tape` line 1 quoted).
2. **Resolved by `3c22633` (WO-0112).** *Terminal recorder — drift
   against the computed plan.* The adapter now scales the planned offsets
   by recorded ÷ planned inside `DRIFT_BAND = (0.75, 1.25)`; this render's
   ratio was 0.9666 and every narration line started within 0.13 s of
   its measured scene change. Review should still read the breakdown's
   2026-10-10 Note on this deviation from the architecture's "offsets
   computed for vhs".
3. **Resolved by `65ba8f7` (WO-0113).** *Browser recorder — the driver's
   home.* The driver now runs from a `launch-demo-` directory under the
   working directory, removed after; the render produced its mp4, and no
   such directory was left in the repo root after success or either
   failure.
4. **Partly resolved by `65ba8f7` (WO-0113); the remainder is Failure
   5.** *Browser recorder — the reason line.* The ESM import failure's
   reason now names the error.
5. **Resolved by `6d550c7` (WO-0125)** — the same real failure now
   reads `browserType.launch: Executable doesn't exist at …` (before:
   `Node.js v22.22.3`), quoted under Re-verification at `6d550c7`.
   The record as filed: *WO-0113's reason line on a real Playwright
   failure.* When
   Playwright cannot launch its browser — the expected failure on any
   machine that installed the package but not the browser — the problem
   string and so the brief's `video:` line read `launch-demo: browser
   recorder failed: Node.js v22.22.3`. Node prints Playwright's error as
   its bare message (`browserType.launch: Executable doesn't exist at
   …`), which `NODE_ERROR_LINE` does not match, and
   `tests/test_launch_demo.py`'s `test_a_failing_node` pins an `Error: `
   prefix the real output lacks. Routes to Implement: correct that test
   to the real stderr shape quoted above (correcting a wrong test, not
   bending it) and widen the reason rule to catch a flush-left
   `<identifier>: <message>` line or similar. No PRD-0009 criterion
   fails on it.

## Not verified

- **The owner's watch of `launch.mp4`.** Frames at four times were
  viewed and the narration's onsets measured against the scene changes;
  nobody in this stage listened to the audio. The owner watches before
  merge (the brief's Release authorization). Observed while viewing: the
  second step's caption wraps mid-word at the frame's edge ("the b /
  uilding step") — cosmetic, for Review or the owner.
- **A numeric ceiling for "short".** The terminal mp4 is 33.27 s and the
  browser mp4 27.43 s; the PRD leaves the ceiling to the owner.
- **The Ship hook firing live.** Ship has not run for this branch; the
  PRD's check for this criterion is the diff and the lint checkers.
- **The hook's "any other `when`" and absent-config branches** are
  stated in the Ship step's text and not exercised; neither has a tool
  half to run.
- **The browser recorder on a real web app**, and a Linux voice
  (`espeak-ng`, Piper) — out of this run's scope by PRD-0009.
- **The routing eval** (`python3 trigger_eval.py`) was not run — it
  drives the `claude` CLI and costs money; the LEDGER row stays `draft`.
- **Detector B on a live pull request event.** B skips locally without a
  PR event payload; its selftest ran (`selftest: ok`).

## Prior verification (2026-10-08, commit e2da12b)

The first pass recorded 8 PASS, 2 FAIL: both recorders failed at their
first real run. The terminal tape's unquoted `Output` path was rejected
by vhs 0.11.0 (`parser: 3 error(s)`), and a diagnostic with that line
quoted recorded 32.36 s against a planned 34.431 s, past the old 1.5 s
absolute tolerance; the browser driver, written under the system temp
directory, could not import `playwright` (`ERR_MODULE_NOT_FOUND`), and
the reason line carried `Node.js v22.22.3`. Its diagnostic frames remain
beside this artifact as
[`title-card-diagnostic.png`](title-card-diagnostic.png) and
[`browser-fixture-step-diagnostic.png`](browser-fixture-step-diagnostic.png);
the full record is `git show e2da12b:docs/features/launch-demo/verification.md`.
Failures 1–4 above map one to one onto that record's Failures.
