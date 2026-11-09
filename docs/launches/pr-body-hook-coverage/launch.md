---
launch: pr-body-hook-coverage
date: 2026-11-09
sources: [docs/features/pr-body-hook-coverage/prd.md, docs/features/pr-body-hook-coverage/verification.md]
video: launch.mp4
---

# Launch: The pull-request check now reads a description written in the same command

## What it is

The early check on pull-request descriptions now reads one more kind of command. It covers a description that is written to a file and used to open the pull request in a single step. It still stays out of the way whenever it cannot be sure what the file will hold.

## What it does

When the description is missing its work-order line or its closing line, the command is stopped before the pull request exists. When the description has both lines, the command goes through untouched. Anything the check cannot read with certainty gets a short note instead of a block.

## How it helps

A bad description used to fail only after the pull request was open and the build had run. Now it fails in seconds, with the same two reasons the build would give. The share of such commands the check can judge roughly doubled, from 13 percent to 26 percent.
