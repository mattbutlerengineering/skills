---
stage: review
run: maintenance:pid-alive-answers-the-wrong-question
date: 2026-08-27
---

# Review

Scope: the diff this run produced — `10e684d` (capture) and `33910b4`
(the fix and its two regression tests). Scaled to the blast radius
recorded in `defect.md`: test-only, no shipped module, no mirrored file.

Reviewed by the run's own author, which is the weakness of this pass and
is stated rather than hidden. ADR-0036 clause 2 wants a non-authoring
reader before merge; that requirement is unmet here and is carried into
`release.md` as a blocker.

## Findings

### 1. The fix makes the duplication more expensive — minor, accepted

`defect.md` logs the two verbatim `pid_alive` copies as a smell and
declines to fix them, on the repo's own rule: CLAUDE.md gates a new
shared module on *multiple real callers **and** observed divergence*, and
these two had not diverged.

That reasoning still holds, but this change moves the number it depends
on. The duplicated region grows from 6 lines to roughly 30, including a
platform branch and a `/proc` parsing rule. A 6-line duplicate is cheap
to keep in step; a 30-line one with two code paths is materially more
likely to drift — which is the precondition the rule waits for.

**Failure scenario:** someone fixes a `/proc` parsing edge case in the
CLI copy and not the charter-replay copy. The suites then disagree about
whether a process is alive, and the difference surfaces as an unrelated
reaping failure in whichever file was not updated — the same
one-defect-many-names confusion this run exists to end.

**Decision: accept, and record.** Extracting a shared test module is a
design change, out of scope for `re-entry: implement`, and doing it
unasked is exactly the "while I was in there" refactor the repo warns
against. But the honest reading is that this change strengthens the case
for extraction rather than leaving it neutral, and a future reviewer
should not have to re-derive that.

### 2. `ps` missing is an unhandled crash — minor, accepted

The non-Linux branch calls `subprocess.run(["ps", ...])` with no guard.
If `ps` is absent, `FileNotFoundError` propagates out of `pid_alive` and
the test errors instead of failing a clean assertion.

**Failure scenario:** a stripped container image without `procps`, and
without a Linux `/proc` — the error names `ps`, not the predicate, so the
reader is sent to the wrong place.

**Decision: accept.** Both platforms this repo actually runs on always
have one branch or the other: CI is Linux and takes `/proc`; development
is macOS and always ships `ps`. Guarding a state that cannot occur on any
supported platform is the defensive code `implementation-discipline.md`
tells us not to write. Recorded so the judgment is visible.

### 3. The fix adds process churn on macOS — minor, noted

On the `ps` branch every predicate call spawns a subprocess. In the
2-second grace loop that is up to ~40 spawns on the failure path, though
only one or two on the success path, since the loop now exits as soon as
the state is readable.

This is worth stating plainly because of what it touches: PID reuse is
the leading untested hypothesis for the flakes that led here, and PID
reuse is driven by process churn. So on macOS this change nudges the
suspected mechanism in the wrong direction, while on Linux — CI, and the
sandbox where the flakes actually appear — it spawns nothing at all and
the concern does not arise.

**Decision: accept, noted.** It does not affect the environment the
flakes occur in, and no measurement here supports trading it for a more
complex design.

### 4. POSIX-only test helper — not a finding

The regression tests use `os.fork()` and `os.pipe()`, which do not exist
on Windows. This is not a new constraint: the files already require
`/bin/sh`, `os.kill` and process groups, so both suites were POSIX-only
before this change. Recorded so a reader does not raise it as one.

## Verified, not assumed

The reaping suites were re-run after the change rather than reasoned
about — `Ran 4 tests ... OK` — because the fix alters the predicate those
tests' grace loops depend on, and a passing pinned test says nothing
about whether the original assertions still hold.

## Not reviewed

- The Linux `/proc` branch was read but not executed; only the `ps`
  branch ran on this machine. See `verification.md`.
- Nothing outside this run's diff. The five journal flakes are a
  standing open question, not part of this change.
