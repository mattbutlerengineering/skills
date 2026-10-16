<!--
CI's detector B reads this body (it skips locally): it needs a work-order
id or a `No work order:` line with a non-empty reason, and one closing
keyword per issue. Left as they are, the two lines below FAIL the check —
on purpose, so an unfilled template cannot merge. Never close a permanent
issue (#178, #181, #294, #586, #587, #590, #925, #930) to satisfy it.
Grammar and traps: docs/kb/pr-body-contract.md.
-->
No work order:
Closes #

## What / why

<!-- The reason first, then the change. A reader who sees only this
section should know what would break if the PR were reverted. -->

## Verification

<!-- Paste the three result lines as the commands printed them, never
typed from memory. Then disclose the rest, xerj-style: hiding a skipped
check is the problem; the skip itself is expected and fine. -->

```
tests:
lint:
gates:
```

**Verified** (commands run, output observed):

**Assumed** (not tested, and what would falsify it):

**Not run** (a check above you skipped, and why):

## Merge danger

<!-- Door: one-way or two-way (does a revert restore the previous
state?). Blast radius: which files, which stamped consumers, which
routines read what changed. -->
