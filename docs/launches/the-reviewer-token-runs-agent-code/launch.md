---
launch: the-reviewer-token-runs-agent-code
date: 2026-10-16
sources: [docs/fixes/the-reviewer-token-runs-agent-code/defect.md, docs/fixes/the-reviewer-token-runs-agent-code/verification.md, docs/fixes/the-reviewer-token-runs-agent-code/release.md]
video: launch.mp4
---

# Launch: The reviewer's key never touches the code it reviews

## What it is

Every pull request gets an automatic review, posted by a separate reviewer account. Until now, that review ran in the same place as the pull request's own code, holding the reviewer's key. This release splits the work in two, so the key and the untrusted code are never in the same room.

## What it does

The pull request's code now runs in a job that holds no secret, and it hands over only its findings, as plain text with a size limit. The reviewer then starts from the trusted main branch, reads those findings as data, and takes its pass or fail verdict from the check's result, never from the text. Even when someone points the review at a pull request branch by hand, the reviewer still starts from main.

## How it helps

A pull request written by an agent can no longer borrow the reviewer's identity to approve itself or act on the repository. Reviews look the same as before, and a failing check still shows as a failure.
