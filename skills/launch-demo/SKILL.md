---
name: launch-demo
description: Use when a feature has shipped, or is about to, and the ask is a launch brief for it — "make the launch video", "write the launch copy for what we just shipped", "record a demo of this feature", "explain this release in plain words, with a clip". Produces two halves in one directory; plain copy (what it is, what it does, how it helps) written from the run's artifacts or from the pull request, and a short narrated mp4 whose every spoken line is a sentence of that copy, recorded by the terminal recorder (vhs) or the browser recorder (Playwright) as the repo's per-repo docs/launch-demo.json configures, with a free local voice by default. Fires two ways — Ship runs it when that config says so, and it is invoked directly for any run or pull request — and degrades to copy only, saying why, when a recorder, the voice or the page is missing. Not `ship` (ship releases; this records what a release shipped), and it never fakes a video.
---

# Launch demo

Turn a shipped feature into a launch brief a stranger can read in a
minute and watch in less: a `launch.md` in plain words, and beside it
a short narrated `launch.mp4` whose every spoken line is a sentence of
that copy. The judgement — the copy, and which sentences become which
scenes — is yours. Everything that must be exact is the shipped tool's:
it validates the repo's config, probes the recorder and the voice,
holds the storyboard to the copy, records, narrates, muxes and gives
the verdict.

The tool lives two directories above this skill's directory, in the
same checkout, and is run from the repo root:

    python3 <this skill's directory>/../../launch_demo.py config
    python3 <this skill's directory>/../../launch_demo.py probe
    python3 <this skill's directory>/../../launch_demo.py render <slug>

Each prints lines prefixed `launch-demo: `, then a verdict word alone
(`READY` or `COPY-ONLY` for `probe`; `PRODUCED` or `COPY-ONLY` for
`render`), then `launch-demo: N problem(s)`. A nonzero exit is problems,
quoted and stopped on; a `COPY-ONLY` verdict exits 0 and is a reason
line to report, never a failure to work around.

One resource, loaded when reached: **`references/brief-grammar.md`** —
the config fields and their grammar, the voice swap, the storyboard
grammar per recorder, the happy-path precedence, and the
three-parts-to-three-scenes rule.

A utility skill: it owns no run artifact, the router never names it,
and it is loaded two ways — by Ship, when the repo's config says
`"when": "ship"`, and directly by a person for any run or pull request.
It is not `ship`: ship releases; this records what a release shipped.

## Input

A feature reference, one of:

- a run directory or slug under `docs/features/` (or the product run at
  `docs/`); with none named, the one active run by the protocol's run
  discovery (`../../docs/pipeline-protocol.md`), and when several are
  active, ask which;
- `--pr <n>`, for a feature that shipped from a bare pull request with
  no run. The slug is a kebab-case cut of the pull request's title.

The publish directory is `<publish>/<slug>/` under the config's
`publish` field.

## Steps

Work these in order. Each stops where it says.

### 1. Validate the config

Run the `config` leg. Problems are quoted verbatim and the work stops
there — a missing `docs/launch-demo.json` is one such problem, with the
reference's field table as the fix. Nothing is written.

### 2. Probe the toolchain

Run the `probe` leg and note the verdict. `READY` means the recorder,
the voice and ffmpeg are present. `COPY-ONLY` lists each missing tool
with what it is for and how to install it; keep those lines — they are
the reason the brief will carry — and continue: the copy needs nothing
installed.

### 3. Read the sources

For a run directory, read `prd.md`, `verification.md` and `release.md`
— what was promised, what was proven, what went out. For `--pr <n>`,
read the pull request's title and body through the forge CLI
(`gh pr view <n> --json title,body`), and the changelog entry naming it
when the repo keeps one. Record what was read; it becomes the
`sources:` line.

### 4. Write the copy

Write `<publish>/<slug>/launch.md` (creating the directory):

```markdown
---
launch: <slug>
date: <YYYY-MM-DD>
sources: [<the files read>]      # or: pr: #<n>
video: <left for step 7>
---

# Launch: <the feature, in plain words>

## What it is

## What it does

## How it helps
```

Each section is two or three plain sentences a stranger understands,
naming no path, function, flag or identifier. Write for the person who
will use the thing, not the person who built it. Every sentence should
be sayable aloud — the next step will cut some of them out verbatim.

### 5. Find the happy path

The video shows one walk through the feature, never guessed. Take the
first source that exists, in this order (the reference states each):

1. a `storyboard.json` already at the publish path — reuse it unchanged;
2. an executable path — an E2E test `verification.md` names, or the
   commands verification ran for the feature;
3. `ux.md`'s primary flow;
4. `verification.md`'s evidence;
5. the pull request body's before-and-after evidence section.

With none, stop here: set `launch.md`'s `video:` line to
`none — no happy-path source (looked at: <what was checked>)`, print
`COPY-ONLY`, and report. The copy stands on its own.

### 6. Write the storyboard

Write `<publish>/<slug>/storyboard.json` in the reference's grammar:
`title` and `tagline` for the title card; `intro`, one sentence of
*What it is*; `steps`, each a `say` that is one sentence of *What it
does* and a `do` in the recorder's form (shell commands typed one per
line for the terminal; one string of Playwright statements for the
browser; either may be empty); `outro`, one sentence of *How it helps*.
Every `intro`, `say` and `outro` is a verbatim sentence of `launch.md`
— the tool refuses one that is not, so cut, never paraphrase. An
existing storyboard is never edited.

### 7. Render and report

Run the `render` leg with the slug, from the repo root. Report its
lines verbatim — the scratch directory it names, what it wrote, the
stream summary — then its verdict word. Then finish `launch.md`'s
`video:` line from that verdict: `launch.mp4` on `PRODUCED`; otherwise
`none — ` followed by the tool's reason line (the missing tool, the
unreachable page, or the problem it quoted). Name the paths written.

Done when: `launch.md` exists with its `video:` line settled, the
storyboard exists when a happy path did, and the report ends in the
tool's verdict. This skill never writes a placeholder video, never edits
an existing storyboard, and never commits — the invoker (Ship, or the
person who asked) commits what it wrote.
