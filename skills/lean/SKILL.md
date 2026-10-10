---
name: lean
description: Use when the ask is for the smallest thing that fully works, or for what can be cut — "simplest solution", "keep it minimal", "is this over-engineered", "do we even need this", "what can we delete", "review this diff for bloat", "list the shortcuts we deferred". Before writing code it climbs a fixed ladder — does this need to exist, is it already in this repo, in the standard library, in the platform, in an installed dependency, in a few direct lines — and stops at the first rung that holds. Pointed at a diff or a whole tree it returns a numbered cut-list, each line naming what goes and what replaces it, with every reference checked before anything is called dead. It never trims validation at a trust boundary, data-loss handling, security, accessibility, or anything explicitly asked for. Complexity only — correctness and security defects belong to review, the shape of modules to deepen, a whole-repo defect sweep to audit. Owns no run artifact and is never routed to.
---

# Lean

Solve the problem with the least code that fully solves it — and, pointed
at code that already exists, find what can go. The cheapest line to
maintain is the one nobody wrote; the second cheapest is the one somebody
deleted.

Lean is a claim about the **solution**, never about the **reading**. A
small diff in the wrong place is not lean; it is a second bug. Everything
here runs after the problem is understood, not instead of understanding
it.

This is not a stage in the lifecycle pipeline and it owns no run
artifact. It composes with the pipeline (step 6) and works fine in a
repo that has never heard of it.

| The ask | What this skill does |
|---|---|
| A task to build or change | **Build lean** — steps 1 to 3 |
| A diff, a branch, a pull request | **Review** — step 4, over the changed lines |
| A whole tree | **Sweep** — step 4, over everything, biggest cut first |
| "What did we defer?" | **Debt** — step 5 |

## Process

### 1. Understand before you shrink

Read the task and the code it touches. Trace the real flow end to end,
and list the callers of anything you are about to change. Only then
choose a solution.

For a defect, this is where lean and correct turn out to be the same
thing. A report names a symptom on one path; the fix belongs where every
caller passes through. One guard in the shared function is a smaller
diff than a guard at each call site, and it does not leave the sibling
callers broken.

### 2. Climb the ladder

Ask these in order and stop at the first that holds.
[`references/ladder.md`](references/ladder.md) shows what each rung
looks like in practice, and when the ladder is the wrong tool.

1. **Does this need to exist?** Trace it to something asked for: the
   request, an acceptance criterion, a failing test. A need nobody has
   yet is not a requirement. Leave it out and say so in one line.
2. **Is it already in this repo?** A helper, a type, a pattern, a seam.
   Search before writing — rewriting what lives three files away is the
   most common waste there is.
3. **Does the standard library do it?**
4. **Does the platform do it?** The browser, the database, the operating
   system, the framework already in use.
5. **Does a dependency that is already installed do it?** A new
   dependency is never the answer to something a few lines can do.
6. **Is it a few direct lines?** Write them where they are used.
7. **Only then:** the minimum that meets the acceptance criterion.

When two rungs both hold, take the higher one and move on. The ladder is
a reflex, not a research project.

### 3. Build the rung, and say what you left out

- No structure nobody asked for: no interface with one implementation,
  no factory for one product, no option nothing sets, no scaffolding
  "for later". Later can scaffold for itself.
- Prefer deleting to adding, and boring to clever.
- Two candidates the same size? Take the one that is right at the edges.
  Lean means less code, not a flimsier algorithm.

**The floor.** These are never the thing that gets cut:

- validation where untrusted input enters;
- error handling that prevents data loss;
- security controls;
- accessibility basics;
- anything the user explicitly asked for.

**One check stays.** Logic with a branch, a loop, a parser, or money in
it leaves one runnable check behind — the smallest thing that fails when
the logic breaks. Inside a pipeline run that is the item's failing-first
test, and it is never bloat. A change with no logic in it needs no test;
restraint applies to tests too.

**Mark the shortcut.** A deliberate simplification with a known ceiling
— a global lock, a quadratic scan, a naive heuristic — carries a comment
that starts `lean:` and names the ceiling and what would trigger the
upgrade:

    # lean: one lock for all accounts; per-account locks once
    # contention shows up in a profile

A shortcut with no trigger is how "later" becomes "never" (step 5).

**Report in a few lines.** After the code: what was skipped, and what
would bring it back. If the explanation is longer than the code, the
complexity has only moved into prose. When the user wants the fuller
version anyway, build it without re-arguing — the ladder is advice, and
they have heard it.

### 4. Review or sweep: the cut-list

Read [`references/cut-list.md`](references/cut-list.md) for the line
format, the six tags, and the evidence each one owes.

The product is a numbered list, one finding per entry: where, what goes,
what replaces it. Numbered so the user can say "do 2 and 5". A review
covers the changed lines; a sweep covers the tree and ranks the biggest
cut first.

**Nothing is called dead on a feeling.** Before any entry says *delete*,
search the whole tree for the symbol: tests, fixtures, configuration,
strings and dynamic lookups, and anything the repo publishes — an
exported name, a plugin surface, a documented extension point. The
callers visible inside the tree are not all the callers. A cut whose
references were not enumerated is reported as a suspicion, marked as
one, with what would settle it.

Never list the floor, and never list the one check from step 3.

The list is the whole deliverable. Apply nothing unless asked: a review
that starts editing has stopped being one.

### 5. Debt: harvest the markers

Search the tree for `lean:` comments, skipping vendored and generated
directories, and report one row per marker, grouped by file: where, what
was simplified, the ceiling it names, the trigger it names.

Flag every marker that names no trigger. Those are the ones that rot.

Report only. The ledger goes into a file only when the user asks for
one.

### 6. Hand it off

- **Inside a run, at Implement.** Building lean is how "the minimum
  implementation that passes" gets met. A cut outside the current item
  is logged under the breakdown's Notes, not made — surgical scope
  outranks a tidy diff.
- **A cut-list worth doing, with no run open.** `capture` takes it as a
  condition brief: something degraded rather than broken. A cut worth
  remembering and not worth a run today is a seed for the backlog, which
  this skill never writes itself.
- **Out of lane.** A correctness or security defect noticed on the way
  goes to `review`. A module that is merely thin — its interface as
  costly to learn as its implementation is to read — is a question of
  shape, and `deepen` asks it properly. A hunt across every defect
  category is `audit`.

## Rules

- Lean about the solution, never about the reading. No rung is chosen
  before the flow is traced.
- The floor is not negotiable, and it is never a finding.
- No *delete* without its references enumerated. A confirmed small cut
  beats a speculative large one.
- Complexity only. Bugs, vulnerabilities and slow code are routed, not
  reported as findings.
- Review, sweep and debt are read-only. They list; they do not apply.
- The user's explicit request outranks the ladder. Name the leaner
  option once, then build what was asked.
- Every deliberate shortcut is marked with its ceiling and its trigger,
  or it is not deliberate.
