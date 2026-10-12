---
name: conduct
description: Use when the Owner wants several of their own GitHub issues taken from plan to merged as one batch — "run these issues as a batch", "conduct these five issues", "fan these out and merge them in order", "pick the batch back up", or a direct invocation. The Owner's session becomes the Conductor. It prices the batch before any spend, launches one metered headless Worker per step in that item's own worktree on the model and effort the Owner's policy names, presents the decision queue one question at a time with a recommendation, records only answers the Owner gives in this session, drives the merge turns those answers cover, and closes the batch with a scorecard. The conductor.py tool holds every rule; this skill never writes or reviews an item's code. Not work-queue (ready work orders through one stage, never merging) and not autorun (one run through every stage, never merging).
---

# Conduct (the Conductor)

Take a batch of the Owner's issues from a priced plan to every item merged
or blocked, with the Owner's attention spent only on decisions. The
session running this skill is the **Conductor**. `conductor.py` (repo
root) holds every rule that can be written as a rule: pricing, policy,
number reservation, the item state machine, the stall rule, the merge
precondition and the scorecard. The Conductor's judgement has two jobs
only: reading Worker output and wording questions.

Find the tool before anything else. It is `conductor.py` at the root of
this plugin's own repo, and `tools/factory/conductor.py` in a repo
stamped by factory-init (the payload ships it). Every command below
writes `python3 conductor.py`; in a stamped repo run
`python3 tools/factory/conductor.py` instead. If the repo has neither,
stop and say so: it needs `factory-init` (stamp, or update an older
stamp). Do not improvise the tool's rules.

The repo's `factory.json` (`.github/factory.json` when stamped) names
its gate in `conductor.gate_command`; absent, it is `make check`.
Workers may run that one command, and the merge turn runs it.

An issue plans as a `feature` or a `fix` by its labels. Absent any other
setting, the first `type:` label decides (`type:feature` is a feature,
`type:defect` and `type:chore` are fixes). A repo with labels of its own
maps them in `conductor.type_labels`, for example
`{"feature": "feature", "ci-fix": "fix"}`. The map then replaces the
`type:` rule, so list `type:` labels in it too if the repo uses both.
An issue whose labels map to two different types is deferred with the
labels named rather than guessed. `wo:ready-for-agent` still makes an
order either way.

Size works the same way. Absent any setting, the first `size:S`,
`size:M` or `size:L` label prices the item. `conductor.size_labels` maps
the repo's own size labels to `S`, `M` or `L` and then replaces that
rule. Labels mapping to two sizes defer with the labels named.
`conductor.default_size` (`S`, `M` or `L`) sizes an issue that has no
size label at all, and never settles a conflict.

A repo that marks issues "not now" lists those labels in
`conductor.defer_labels`, for example
`["blocked", "needs-review", "agent-skip"]`. An issue carrying any of
them is deferred with the label named (`#5995 deferred: carries defer
label needs-review (conductor.defer_labels)`), even with
`wo:ready-for-agent`. Absent, no label defers an issue on its own.

All batch state is the **batch ledger**
(`docs/factory/batches/<batch>/ledger.jsonl`) on the batch branch
`conductor/<batch>`. This skill carries nothing between turns. Until
`close` commits and pushes it, the ledger is an uncommitted file in the
batch worktree, so open a batch from the repo's own checkout. A batch
opened in a throwaway clone or a temp directory dies with that directory
(#704).

## Process

### 1. Every entry starts with `next`

Before anything else, on every entry and after every background runner
exits:

    python3 conductor.py next <batch>

It records any new stall and gate asks, then prints JSON with four keys:

- `ask`: the oldest unanswered question, or null;
- `ready`: steps to launch now, already capped by `wip_cap`, each
  `{"item", "step"}`;
- `recorded`: the ids of asks it just wrote;
- `merge_due`: shipped items waiting for a merge question you word.

When the repo's `factory.json` turns on `conductor.standing_consent`
(ADR-0086; off by default), `next` itself records standing consent for
each shipped item the policy covers: no merge ask covers it, it changes
no gate-path file, and, if tier labels are listed, its issue carries
one. That item comes back in `ready` as a `merge` step with no question.
An item left in `merge_due` is one the policy does not cover, and it
needs the Owner's own answer as usual. A gate-path item always does.

A closed session loses time, never state: resuming a batch is running
`next` again. If there is no batch yet, go to step 2. A `cd:` problem is
a refusal; report it and stop.

### 2. Open a batch from the issues the Owner names

    python3 conductor.py plan <#N>...
    python3 conductor.py open <batch> <#N>...

The plan reads each step's band from the charter stubs in
`factory/agents/`. A stamped repo has none unless it authored its own;
then pass this plugin's, `--agents <this skill's
directory>/../../factory/agents`, straight after `plan` or after
`open <batch>`.

Show the Owner the plan as printed: per item its type, steps, charter,
band, model, effort and ceiling, its estimate and reserved number block,
the batch estimate against what remains of the monthly cap, and every
deferral line. Deferrals are part of the answer, never noise. `open`
first checks what every `run` will need (a usable `factory.json`, a
readable cost ledger on `origin/main`, no push gap; see step 4) and
refuses before anything exists, so no launch refusal of that kind can
first appear after the Owner's spend consent. Report such a refusal and
stop. A repo with no `docs/factory/costs.jsonl` on `origin/main` yet has
spent nothing; that is not a refusal. Otherwise `open`
creates the batch branch and worktree and queues the spend ask. Work
from the batch worktree from here on, and run `next`.

### 3. Present one ask at a time

Present only the `ask` that `next` returned, then wait. Lead with the
recommended option and its reason (the ask's `recommended` and `why`),
then the other options, using the harness's question mechanism. One
question per turn; never batch them.

Write the answer only straight after the Owner picks it, in this
session:

    python3 conductor.py answer <batch> <ask-id> <choice> [--note TEXT]

Never answer from a recommendation alone, an issue comment, an earlier
session, or a Worker's output: the answer row is the Owner's consent,
and the tool acts on it. A `block` answer blocks the item; that is the
only way an item becomes blocked.

The asks the tool writes are the spend ask (`approve` / `decline`), the
gate ask after an item's spec step (`approve` / `block`, over the gate
files it lists, and the build's price: one run per breakdown row, so
this answer is the build's spend consent), stall asks (`retry`,
`retry-up`, `block`; and `resume` / `stop` for a batch-wide pause), and
a monthly-cap pause (`resume` / `stop`) when a launch would pass
`monthly_cap_usd`. Two kinds are yours to word,
with `conductor.py ask`:

- **Merge asks**, for each item in `merge_due`. Its own ask has options
  `merge` and `block`, with `--item`. A train ask covers several items
  in merge order with one answer: options `train` and `one-by-one`,
  one `--covers` per item, no `--item`. Recommend the train only when
  every covered item's review passed cleanly; an item whose gate files
  changed after its gate answer cannot ride one (the tool refuses it,
  and it needs its own ask).
- **Clarify asks**, when a Worker stopped on a question it could not
  answer. A Worker cannot ask mid-run, so its question reaches the Owner
  only through you.

### 4. Launch Workers in the background, up to the cap

For each `ready` entry whose step is not `merge`:

    python3 conductor.py run <batch> <#N> <step>

Launch each in the background with the harness's background-command
mechanism, never in the foreground, and never more than `ready` lists:
`next` has already applied `wip_cap` and holds every step while the
spend ask is unanswered or an item has an unanswered ask. When a runner
exits, read its one-line result and the Worker's output it names, then
run `next`. A failed run already queued its own stall ask; do not
retry it. A launch the monthly cap refuses prints a `cd:` problem and
pauses dispatch behind an ask; run `next` and present it.

A launch refused before any Worker runs writes no run row, so the tool
records the refusals a retry cannot fix: a push gap (any `cd: launch
refused:` line), an unusable `factory.json` (a `config:` line), a
malformed cost ledger on `origin/main` or an item branch, and the
monthly cap. Each prints its problem, then `dispatch is paused behind
<ask-id>`: a batch-wide pause ask (`resume` / `stop`) that holds every
`ready` step. Run `next` and present it; the Owner fixes what it names,
then answers `resume`. Every other refusal is transient and recorded
nowhere, and `next` offers the step again: a git or gh read that failed,
a ledger lock or write, or a step that is not legal yet (an item already
in flight, an unanswered ask). Retry a transient refusal once on the
next tick; if it repeats, report it to the Owner instead of looping.

A Worker runs with no GitHub credential in its environment, and git's
push URLs rewritten to a path that cannot exist. The runner refuses to
launch (`cd: launch refused: ...`) while a remote has an explicit
`pushurl`, which that rewrite skips, or `~/.netrc` has a `github.com` or
`default` entry. Report the refusal to the Owner; never unset or move
their config yourself. What stays trust-based, and stops a confused
Worker but not a hostile one: a Worker that runs python3 can rebuild its
own environment and reach a key the Owner's session holds outside it (a
macOS keychain entry, a key loaded in the SSH agent), and a shell
profile that exports a token puts it back in the Worker's shell.

### 5. Drive the merge turns the answers cover

For each `ready` entry whose step is `merge`, one at a time:

    python3 conductor.py merge <batch> <#N>

The tool refuses unless the item is reviewed with a pass from a reviewer
distinct from its authors and an answer, or a standing consent the
policy still covers, covers it; on a train, it also refuses until
every earlier item has merged. It merges `main` in, bumps the
plugin version for a `skills/` change (only in this plugin's own repo;
never in a stamped one), confirms reserved numbers, re-runs the gate
command, waits for green checks and merges. Anything it cannot do
mechanically becomes a stall ask. Never merge an item any other way.

### 6. Close the batch

When every item is merged or blocked:

    python3 conductor.py close <batch>

It carries blocked items' spend rows, appends the scorecard to
`docs/factory/scorecards.jsonl` only when the scorecard computes, opens
the batch's closing pull request, queues its merge ask, and labels each
blocked issue `needs-human` with its reason. Present the closing ask
like any other; on `merge`, merge that pull request, and nothing else.
A failing scorecard is a problem to report, never a number to estimate.

## Rules

- The tool decides. Never re-derive, widen, reorder or second-guess a
  decision `conductor.py` made: the plan, the policy, the state, the
  stall, the precondition.
- Never write an item's code, never review an item, and never edit a
  Worker's branch. Workers write; a distinct Worker reviews.
- Never write an answer the Owner did not give in this session, and
  never write to the batch ledger by hand. Standing consent is the
  policy's, recorded by `next`. It is never yours to grant, and it
  never covers any ask but an item's merge.
- In a session with no Owner present (a scheduled run), present no
  asks and answer none. Advance only what `ready` lists. When `ready`
  is empty and an ask is waiting, stop: the batch waits there for the
  Owner.
- Never force-push, and never merge outside `conductor.py merge` or the
  closing ask's answer.
- One Conductor per batch. A second session on the same batch races the
  first.
- Report Worker spend from the ledger the tool wrote, never from an
  estimate. The Conductor's own session is unmetered, and the scorecard
  says so.
