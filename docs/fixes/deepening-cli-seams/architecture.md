---
stage: architect
run: maintenance:deepening-cli-seams
date: 2026-08-13
assumptions:
  - "prd.md absent — this is a maintenance run, whose predecessor is defect.md (ADR-0025's maintenance table), not a PRD. The condition brief plus the walked evidence in the deepening review are the design source; no PRD requirement tracing applies"
  - "ux not applicable — the run touches three CLI tools and a module split, no user-facing surface"
---

# Architecture: the three decisions the deepening left open

## Approach

Three of the four candidates the review raised are decisions, not
refactors, and each has been treated the same way: find what the codebase
already decided, then choose the option that adds the least new machinery.
Two of the three come out as *do less than the review implied* — the front
door is already pinned where it matters and needs an audience declared, not
a migration; the gh-listing duplication is a shared rule with per-caller
meaning, which is the shape that argues against a seam. The third is the
opposite: the `protocol.py` split is worth doing on its own merits, and the
question that was thought to block it turns out not to be on its path.

The unifying rule this design applies: **share the rule, keep the meaning
local.** `cli.full_window` already owns the truncation rule; what each
caller owns is what absence means to it. That is also why `factory.py` is
a router and not a seam, and why the frontmatter reader can be split out
while the taxonomy stays.

## Components

### `factory.py` — the front door

- Responsibility: give a human one vocabulary for fourteen root tools — an
  index of what exists and a delegating shortcut to each one's `main()`.
  It owns no knowledge; the verb *is* the module name and the index line
  *is* the module's own docstring, read at print time.
- Collaborators: every CLI-bearing root module, by `importlib` at dispatch
  time. Not the Makefile, not the workflows, not the payload.
- Change: its audience becomes explicit (humans, not files), and the last
  hand-kept fact in its table — the calling-convention column — gets
  pinned the same mechanical way the verb set already is.

### The gh listing sites — five callers, one shared rule

- Responsibility: each of `label_sync.live_labels`,
  `gate_digest.run_daily`, `sweeps.live_issues`, `sweeps.known_keys` and
  `work_queue.ready_issue_numbers` turns one windowed `gh` listing into
  either data its caller may trust or a problem string saying why not.
- Collaborators: `cli.gh_json`, `cli.full_window`, `cli.CLI_FAILURES`,
  `cli.detail` — the vocabulary is already shared and stays shared.
- Change: no new module. Each site states its window policy in one line
  and a test pins it, so a disagreement between two sites is a recorded
  decision rather than an accident (which is what it was until this run).

### `frontmatter.py` — the reader the factory tools need

- Responsibility: parse a `key: value` artifact frontmatter block. One
  function, one error contract (`None` when there is no block).
- Collaborators: `protocol.py`, `trigger_eval.py`, and — through the
  mirror — `tools/factory/gates.py` and `tools/factory/assembler.py`.
- Change: extracted from `protocol.py` (42 lines: the `_FRONTMATTER`
  pattern and `read_frontmatter`) and becomes the `MIRRORS` entry that
  `protocol.py` is today.

### `protocol.py` — the pipeline taxonomy

- Responsibility: unchanged (ADR-0021) — stage/skill taxonomy, artifact
  tables, the skill-file contract, next-stage derivation.
- Change: it imports the reader instead of defining it, and it stops
  being a `MIRRORS` entry. ~250 lines stop shipping into every stamped
  repo.

## Data model

No data model. The artifacts of this run are code, one module split, and
one `MIRRORS` row; no persisted shape changes. The cost ledger, the
manifest and the breakdown grammars are all untouched.

## Interfaces & contracts

### `factory.VERBS` — the verb table

- Input: none; a module-level dict of `verb -> (module, convention)`.
- Output: the dispatch target and how to call it.
- Contract: the verb set equals a mechanical scan of the root's
  CLI-bearing modules, each verb is its module's name hyphenated (both
  already pinned by `tests/test_factory_cli.py`), **and** each row's
  convention equals what that module's `main` signature actually accepts
  — the new pin. The table stays static in the module so dispatch imports
  one module, not fourteen; the derivation lives in the test, which may
  import freely.
- Failure modes: an unknown verb prints one line and exits 2; a `bare`
  verb given arguments refuses rather than dropping them; a new tool
  without a verb, or a row whose convention is wrong, fails the build.

### The gh-listing sites — the declared window policy

- Input: an injected `run` callable and a declared window size.
- Output: `(data, problems)` on a listing the caller may use, or
  `(None, problems)` on one it may not.
- Contract: `None` means *the caller must report nothing about what the
  listing does not show*. Each site declares, in one line at the site,
  which of two answers a full window gets and why — **refuse** when
  absence would be read as a finding (`sweeps.live_issues`,
  `work_queue.ready_issue_numbers`), **report and continue** when absence
  only under-reports (`label_sync.live_labels`, `gate_digest.run_daily`)
  or when re-doing work is cheaper than not sweeping
  (`sweeps.known_keys`, which re-files a duplicate rather than skipping a
  week). A test per site pins its answer.
- Failure modes: unchanged and per-caller by design — the problem strings
  stay caller-labelled and exact-string pinned.

### `frontmatter.read_frontmatter(path)`

- Input: a path to a markdown artifact.
- Output: a dict of fields; `{}` for a present-but-empty block; `None`
  when the file has no frontmatter block at all.
- Failure modes: unchanged from today — the single error contract already
  documented on the function. Callers decide what a missing block means.
- Mirror: `frontmatter.py` is an identity `MIRRORS` entry; both trees
  import it as a bare sibling, so stdlib-only standalone execution
  survives in both.

## Stack & dependencies

- Python 3 standard library only — unchanged; nothing here adds a
  dependency.
- No new shared module beyond the split described above, and that split
  removes an interface rather than adding one.

## Decisions & alternatives

- **The front door is for humans; zero file callers is the intended
  state** over routing the Makefile through it (Route A) or deleting the
  dispatcher (Route B). Route A loses on a cost the review did not price:
  `factory.py` is not in the template payload, so a Makefile that said
  `python3 factory.py gates` would either force the front door to ship
  into every stamped repo as a fifteenth mirrored tool, or make
  `factory_init.product_form` translate verbs into payload paths — growing
  the very adapter ADR-0046 wants to delete. Route B loses because the
  dispatcher costs 25 lines and the index alone does not give a human a
  way to *run* what they just discovered.
- **Pin the convention column in the test, not in the router** over
  deriving it at dispatch time by signature inspection — deriving it in
  the module would make a tool CI runs on every push import fourteen
  modules per invocation, to learn something that cannot change without a
  test failing first.
- **No seam for gh's silence** over one reader with a window-policy
  parameter. The review's own precondition was whether only two policies
  are real; walked, there are two answers but three *reasons*, and the
  codebase already states the rule that is genuinely shared —
  `sweeps.known_keys` carries a comment saying the full-window rule is
  `cli.full_window`'s while the message stays its own. A seam absorbing
  the policy would carry a per-caller message and a per-caller policy:
  a configuration table wearing a seam's clothes. What was actually wrong
  was that two sites with the same hazard disagreed by accident; that is
  fixed, and the remaining fix is declaration, not extraction.
- **Split `protocol.py`, and keep the `tools/factory/` identity map
  deferred** over treating the split as the unblocking move. ADR-0046
  names this split as the way out of its dead end, and it pays for itself:
  the payload's interface goes from 15 names to 1 and ~250 lines stop
  shipping. But it does **not** unblock the identity map, and the review's
  framing question — whether a `MIRRORS` entry may pin a root-to-root pair
  — is not on the split's path at all (see below).
- **Do not extend `MIRRORS` to root-to-root pairs** over changing
  ADR-0050's machinery to allow one. Mechanically, a mirror's pin is
  detector E over `manifest_files`, which walks `factory/templates/**`
  only; `install_destination` requires the `templates/` prefix. A root
  pair has no manifest key, so "may a mirror pin a root pair" is today a
  *no* — and the split does not need it to be a yes.

### Why the identity map is still blocked (the part worth writing down)

The split alone keeps every import a bare sibling in both trees:
`protocol.py` at the root imports `frontmatter` at the root; the mirrored
tools import `frontmatter` next to them under `tools/factory/`. Nothing
needs duplicating.

The root-pair question only appears in ADR-0046's *second* step — moving
the mirrored tools to `tools/factory/` at the root so the layouts match.
Do that and `frontmatter.py` moves with them, at which point root
`protocol.py` (which the plugin tools `lint.py` and `trigger_eval.py`
import as a sibling, and which parses frontmatter itself in `_ux_skipped`
and `_re_entry_architect`) can no longer reach it. That is the root-to-root
duplicate the review was asking about — and it belongs to the move, not to
the split.

So ADR-0046 stays accepted, with its blocker narrowed rather than removed:
it is no longer `protocol.py`'s 291-line dual membership, it is the
frontmatter reader's 42-line dual membership. The identity map needs a
smaller answer than before, but it still needs one.

## ADRs

Three decisions here are the "stop re-deriving the dead end" kind that
ADR-0046 and ADR-0053 exist to serve — each was re-derived by this
review after a previous one had already walked it. Recommended, smallest
first:

1. **The front door's audience** — `factory.py` routes humans, not files;
   zero non-test callers is the decided state, and the convention column
   is pinned. (Satisfies the breakdown's B1, whose acceptance criterion
   asks for exactly this record.)
2. **No seam for gh's silence** — the rule is shared, the meaning is
   local; what a full window means is caller knowledge. Records the five
   sites' policies so the next review reads them instead of counting
   copy-paste.
3. **The frontmatter split, and what it does and does not unblock** —
   supersedes nothing; amends ADR-0046's blocker from `protocol.py` to
   the reader, and records that `MIRRORS` pins payload pairs only.
