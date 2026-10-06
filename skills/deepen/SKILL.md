---
name: deepen
description: Use when the question is the shape of existing code rather than a defect in it — "improve the architecture", "find refactoring opportunities", "this is hard to test", "these modules are too coupled", "make this codebase easier for an agent to navigate". Reviews a codebase for deepening opportunities (shallow modules whose interface is nearly as complex as their implementation), confirms each candidate against its real call sites rather than a feeling of friction, presents them as a self-contained before/after HTML report, then designs the chosen interface with you. Read-only on source; it proposes and hands off, never refactors. Not a pipeline stage — invoke it directly, on any repo. Not `architect` (which designs one run's technical approach from its PRD), not `audit` (which sweeps every category for defects and routes them into the pipeline), and not `interactive-architecture-diagram` (which draws a system without judging its shape).
---

# Deepen

Find where a codebase is **shallow** — where the interface costs nearly
as much to learn as the implementation costs to read — and propose the
deepenings that would fix it. The aim is testability, locality, and a
codebase an agent can navigate without holding six files in its head.

This is not a stage in the lifecycle pipeline and does not own a run
artifact. It composes with the pipeline (step 6) and works fine in a repo
that has never heard of it.

Read [`references/language.md`](references/language.md) before writing a
single candidate. Its vocabulary is not flavour: **module, interface,
implementation, depth, seam, adapter, leverage, locality**. A review that
drifts into "component", "boundary", or "cleaner" cannot be compared to
the last one, and its wins cannot be checked.

## Process

### 1. Read the repo's own language and decisions first

Two inputs constrain everything you may propose:

- **The domain glossary** — `CONTEXT.md` or whatever the repo uses. It
  gives the good seams their names. A deepened module called
  `OrderIntakeHandler` in a codebase whose glossary says *Order* is a
  worse proposal than the same module called the Order intake module.
- **The recorded decisions** — `docs/adr/`, design notes, the "why we did
  it this way" file. These exist so a review does not re-litigate settled
  questions.

**Check each decision's status before treating it as binding.** They are
not equivalent, and this is where reviews waste their credibility:

- *accepted* — binding. A candidate that contradicts it is surfaced only
  when the friction is evidenced, and then framed as reopening the
  decision, never as an oversight.
- *provisional* — the repo has said pivot freely. Contradicting one is
  ordinary, and flagging it as a conflict is noise.
- *superseded* — dead. A candidate is not blocked by it, and citing it as
  a constraint is itself a finding about the docs.

### 2. Explore for friction — then confirm it

Walk the codebase for friction. Organically, not by checklist; when the
harness has read-only explorer agents, dispatch them in one message and
let them roam. What you are listening for:

- Understanding one concept requires bouncing between many small modules.
- A module's interface is nearly as complex as its implementation.
- Pure functions extracted *for testability*, where the real bugs live in
  how they are called — the tests are easy and prove nothing.
- Coupled modules leaking across their seam.
- Code untestable through its current interface, or tested by reaching
  past it.

**Everything that comes back is a lead.** Friction is a feeling, and a
feeling is exactly as available for unfamiliar-but-fine code as for
genuinely shallow code. Confirm each candidate before it reaches the
report:

- **Enumerate the call sites.** Count them, list them, look at them. The
  deletion test is a claim about what happens at N callers; if you did
  not visit the callers you do not know, you are predicting.
- **Quote the interface as it actually reads** — every fact a caller must
  know, not just the signature. Shallowness is a comparison, and half of
  it has to be on the page.
- **Run the deletion test, do not narrate it.** For each caller, say what
  it would have to do if the module vanished. Complexity that reappears
  across callers means the module earns its keep; complexity that simply
  vanishes means it was a pass-through.

Three ways a good-looking candidate dies, all common enough to check for:

- **Shallow on purpose, and recorded.** Step 1 already told you.
- **Consumers you cannot see.** A published package, a plugin surface, a
  documented extension point. The call-site count inside the tree is not
  the caller count, and a deletion test run on a partial set gives a
  confident wrong answer.
- **The friction was yours.** Unfamiliar naming reads as indirection for
  about twenty minutes. If the only evidence is that it took you a while,
  that is not evidence.

A candidate you could not confirm still belongs in the report — as
`Speculative`, marked, with what would settle it. Never promote one to
`Strong` to make the review look decisive.

### 3. Classify the dependencies

Read [`references/deepening.md`](references/deepening.md) and classify
each candidate's dependencies: in-process, local-substitutable, remote
but owned, or true external. The category decides how the deepened module
gets tested across its seam — and sometimes decides the deepening is not
available yet, which is a two-step recommendation rather than a
recommendation.

That file also carries the **test-ordering rule**, which is the part of a
deepening that actually goes wrong: new tests at the intended interface
are written *first*, against today's code; the old shallow-module tests
die last, in the same change. Every card states which tests must exist
and which ones die.

### 4. Present the candidates as a report

Write the review per [`references/report.md`](references/report.md): one
self-contained HTML file in the OS temp directory, never in the repo, no
CDN and no network at open time, before/after diagrams carrying the
argument, an evidence block and a cost block on every card, and a
coverage note saying what the review did not look at.

Then stop and ask which candidate to explore. **Do not propose interfaces
yet** — proposing one is how the conversation skips the part where the
user tells you the constraint you did not know about.

### 5. Grill the chosen candidate

Walk the design tree together: constraints, dependencies, what sits
behind the seam, what the interface must promise, which tests survive.
When the shape is genuinely open, design it twice — the parallel-agent
pattern in [`references/deepening.md`](references/deepening.md), whose
returned designs are checked against real call sites before they are
shown, because a design the callers cannot use is a proposal to change
the callers and must be priced as one.

Two side effects belong to this conversation, and both are writes to the
repo's decision record:

- **A term worth keeping** — a deepened module named after a concept the
  glossary lacks, or a fuzzy term the conversation sharpened. Add it.
- **A rejection worth keeping** — the user turns a candidate down for a
  reason a future review would need in order not to re-suggest it. Offer
  an ADR: *"Want this recorded so the next architecture review does not
  raise it again?"* Only for load-bearing reasons — "not now" is not one.

**Propose the exact text, get agreement, then write.** Both files are the
record other people reason from, and an edit landed mid-conversation
because it seemed agreed is the kind that gets discovered months later.
And never rewrite an existing decision to match the new one — supersede
it, so the reasoning that changed stays legible.

### 6. Hand it off

The deepening is work; this skill does not do it. Hand off with the test
ordering first, then the interface you agreed on, then the call sites
that move.

Where the lifecycle pipeline is installed, a chosen candidate has a
natural entry: `capture` writes a **condition brief** — something
degraded rather than broken — and records `re-entry: architect`, which is
exactly the depth a deepening needs. A candidate worth remembering and
not worth a run today is a seed in `docs/backlog.md` instead. Where the
pipeline is not installed, the hand-off is the report plus the agreed
interface, and that is a complete result.

## Rules

- Read-only on source, without exception. This skill proposes; it does
  not refactor, and "while I was in there" is how a review becomes a
  change nobody agreed to.
- The vocabulary is fixed. Every win is stated as leverage, locality, or
  a test that gets simpler. A win that cannot be stated that way is not
  one — it is a preference, and preferences do not survive the next
  reviewer.
- No candidate reaches `Strong` without its call sites enumerated. A
  confirmed medium beats a speculative large every time.
- Every card carries its cost. Wins-only cards are how a refactor gets
  approved and then discovered to be three weeks.
- Never propose a seam with one adapter, and check that the adapters
  named actually get constructed somewhere — an inert seam costs the
  indirection and returns nothing.
- Never re-litigate a live decision without evidenced friction, and never
  cite a superseded one as a constraint.
- The report never lands in the repo. It is a review, not an artifact,
  and a review file checked in becomes a stale description of a codebase
  that moved.
- Say what was not reviewed. A list of findings with no coverage note
  reads as a complete survey, and it never is.
