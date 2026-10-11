---
launch: orchestrator
date: 2026-10-11
sources: [docs/features/orchestrator/prd.md, docs/features/orchestrator/verification.md, docs/features/orchestrator/release.md]
video: launch.mp4
---

# Launch: The Conductor, a batch orchestrator

## What it is

The Conductor runs a batch of issues for you, each piece of work in its own isolated copy of the repository. It keeps every decision it needs from you in one queue and asks them one at a time. This release is prepared but not yet merged, and it has not yet run on a real batch of paid work.

## What it does

You hand it a batch of issues, and it asks you each question one at a time, with the option it recommends first. It refuses an answer that is not one of the options, and it refuses any answer written by one of its own workers. Only your own pick is written down, and only once. Behind those questions, it prices the batch before anything runs, stops launching work when the month's spending cap would be passed, and merges a change only after a separate reviewer has passed it.

## How it helps

Instead of steering every piece of work through one long session, you answer a short queue of questions and the rest moves on its own. Every run, every dollar and every decision is written to a plain record that you can read afterwards. Nothing spends money or merges until you have said yes.
