# ADR compliance pass

The design pass asks whether a decision is missing its ADR. This pass
asks the other question: does the diff break a decision that is already
recorded? An ADR that says "every route uses the shared auth middleware"
is violated by a new route that verifies tokens by hand, and no linter
in the repo will say so.

## 1. List the live ADRs

Run the shipped tool from the target repo's root. It lives two
directories above the review skill's directory in the same checkout:

    python3 <the review skill's directory>/../../adr_status.py [repo root]

It prints one JSON document: `adrs`, each with `id`, `file`, `title`,
`status` (the raw text), `standing` and `superseded_by`. The tool owns
which ADRs are live (ADR-0062). Do not read status lines yourself, and
do not second-guess a standing it reports.

| Standing | What the pass does |
|---|---|
| `active` | Check the diff against it. Accepted, or amended by a later ADR: read the amending ADR too, because the amendment is part of the decision. |
| `provisional` | Check it, but report a violation one severity lower and say the ADR is provisional. It was recorded without live confirmation, so the diff may be the better call. |
| `partial` | Superseded in part. Read the superseding ADR named in `status`, and check only the part it left standing. |
| `retired` | Skip it. Its `superseded_by` ADR carries the decision now. |
| `unrecognized` | The repo uses its own status words, or none. Read `status` and judge. Words like accepted, active or approved mean live. Superseded, deprecated, rejected or withdrawn mean retired. With no status at all, treat it as live and say so in the finding. |

A nonzero exit means the root was wrong: print the tool's output and
fix the path. An empty `adrs` list means the repo records no decisions,
so the pass reports "no ADRs" and has nothing to check.

## 2. Pick the ADRs the diff can touch

Read each live ADR's title, then the Decision section of every one whose
subject the diff could reach. That means a module it edits, a layer it
crosses (routing, auth, persistence, errors, dependencies, styling,
deployment), or a convention it repeats. Skip ADRs about subjects the
diff never reaches, and list them in one line as out of scope. Never
check a diff against an ADR you have not read in full.

## 3. Check the decision, not its wording

Most ADRs a repo cares about are already partly enforced by a lint rule
or a gate. Those checks run in CI. This pass catches what a string match
cannot:

- **The wrong abstraction.** The ADR names a client, a middleware, a
  token set or a helper, and the diff does the same job by hand. Some
  examples: a raw HTTP call where an ADR mandates an API client, a hand
  verification of a token where one mandates an auth package, an inline
  colour where one mandates design tokens. Check the file's imports
  first. Never recommend an abstraction the file already uses.
- **The contract's shape.** The ADR fixes an envelope, a path scheme or
  a field set, for example an error format with required fields or a
  versioned URL prefix. A new response, route or record that is missing
  part of it is a violation, even when the tests pass.
- **The edge the ADR names.** Config, routing tables and infrastructure
  that the ADR binds. A new route the ADR says must bypass a cache, or a
  new service the ADR says must authenticate a certain way.
- **A carve-out used as a loophole.** An ADR with an exception clause,
  where the diff claims the exception without meeting its conditions.

## 4. Report

Each violation is a finding in `review.md`, under the normal severity
ranking. Its heading names the ADR:

    ### <Severity>: ADR-NNNN — <one-line violation>

- Scenario: the decision quoted in one line, the `path:line` that breaks
  it, and what goes wrong because of it.
- Fix: conform to the ADR. If the diff is right and the ADR is stale,
  the fix is a superseding or amending ADR, never an edit to the old
  Decision section (the protocol's "Never rewrite" rule).

Severity follows the consequence, not the ADR. A violation that breaks a
security or data contract is critical. One that only forks a convention
is minor.

## What this pass does not do

- Repeat a check the repo already runs. If a lint rule or gate catches
  the pattern, CI reports it.
- Raise preferences that no live ADR records. A taste no ADR states is
  not a finding here.
- Hunt for plain bugs. That is the correctness pass.

ADR compliance is a judgment, and a false positive costs trust. If you
are unsure whether the diff breaks the decision, record a suspicion with
what would settle it, not a finding. "No ADR violations" is a common and
valid result.
