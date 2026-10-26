---
launch: idea-to-prod
date: 2026-10-25
sources: [README.md, docs/pipeline-protocol.md]
video: launch.mp4
---

# Launch: idea to prod

## What it is

idea to prod is a Claude Code plugin that takes a raw idea all the way to production. Each stage is a skill, and each skill writes one artifact: an idea brief, a P R D, a design, a breakdown, the code, the evidence, the release.

## What it does

The artifacts are the state. Run next, and the router reads what exists and hands you to the stage that comes next. Verify demonstrates instead of asserting. Every pass quotes its evidence, and anything not run is counted, never hidden.

## How it helps

Underneath, a standard-library factory gates every pull request, and nothing merges without the owner's answer. idea to prod. Ship the idea, keep the evidence.

## How the video was made

A 44-second film made with [HyperFrames](https://github.com/heygen-com/hyperframes)
(Apache 2.0, local render, no account). `composition/index.html` is
the HTML and GSAP source. The voice is the free macOS `say` voice:
`composition/make-voice.sh` rebuilds `assets/vo/` from
`composition/voiceover.txt`, whose lines are the copy above, verbatim.
Re-render from `composition/` with `npx hyperframes@0.8.200 render -o
../launch.mp4`. The film's screens are illustrations of the pipeline,
not recordings of a real run.
