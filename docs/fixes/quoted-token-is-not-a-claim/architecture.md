---
stage: architect
run: maintenance:quoted-token-is-not-a-claim
date: 2026-08-23
assumptions: ["Chosen without live interview: this run is autorun-driven, so the option comparison is decided on the ADR-0057 text it amends and on the three observed CI failures, both cited so the operator can overturn it by reading rather than re-deriving.", "An ADR IS offered here, unlike the two runs before it, because this changes a gate an accepted ADR wrote and explicitly justified. It is filed provisional — the repo's own status for a recommended answer adopted while awaiting confirmation — because an autorun decided it."]
---

# Architecture: strip the quoted material, then ask the same question

## Approach

Leave `cited_work_order` exactly as it is and change only what
`run_lifecycle`'s skip gate reads: the body with fenced blocks and
blockquote lines removed, instead of the raw body.

The question the gate asks — "does this body name a work order at all?" —
is the right question. It is asked of the wrong text. A fenced block is
quoted output and a blockquote is quoted prose; neither is the author
claiming anything.

**The property that makes this safe.** `cited_work_order` runs first and
is untouched, so a token that genuinely resolves to an issue the PR closes
still flips the label — even if it sits inside a fence. The gate is
reached only when resolution has already failed. So no PR body that passes
today starts failing, and no label flip that happens today stops
happening; the only change is which *failures* become no-ops.

## Components

### `validator._unquoted(body)` — the new helper

- Responsibility: return the body with fenced code blocks and blockquote
  lines removed, so a token scan sees only what the author asserts.
- Deliberately does **not** strip inline code. `` `WO-0001` `` in ordinary
  prose is how this repo writes identifiers, including in real claims;
  treating backticks as quoting would silence genuine work-order PRs.
  Fences and blockquotes are quotation; inline code is typography.
- Lives in `validator.py`, not in a seam. One caller, and no observed
  divergence with anything — the bar CLAUDE.md sets for a shared module is
  multiple real callers AND divergence, and this has neither.
- Collaborator: `knowledge_plane.WO_TOKEN`, unchanged and still the one
  owner of the token grammar. The helper strips text; it does not retype
  what a token is.

### `validator.run_lifecycle` — the skip gate

- One expression changes: `not WO_TOKEN.findall(body)` becomes
  `not WO_TOKEN.findall(_unquoted(body))`.
- Everything else — the label check, `_pull_request`, `cited_work_order`,
  `tracker_issue`, the flip — is untouched.

### `validator.cited_work_order` — resolution

- **Unchanged.** Its docstring already anticipates quoted material and its
  structural answer is correct. This run adds no responsibility to it.

## Data model

No change. A PR body stays a string, read once per job.

## Interfaces & contracts

### `_unquoted(body) -> str`

- Input: a PR body as GitHub returns it, untrusted author-controlled text.
- Output: the same text with ```` ``` ````/`~~~` fenced regions and lines
  beginning with optional whitespace then `>` removed. Line count is not
  preserved — nothing downstream reads line numbers from it.
- Failure modes: none. An unterminated fence swallows the rest of the body,
  which is the conservative direction: it can only make the gate *more*
  likely to skip, and skipping is a no-op rather than a mutation.

### `run_lifecycle(...)` — contract change

- **Narrows what counts as a malformed work-order PR.** A body whose only
  tokens are quoted moves from "problem" to "silent no-op".
- Unchanged for every other input, including a body that claims a work
  order in prose and gets it wrong — still loud, which is what ADR-0057
  was protecting.

## Stack & dependencies

Stdlib `re`, already imported. No new module and no new dependency.
`validator.py` is a `factory_init.MIRRORS` entry, so the edit carries a
regenerated payload copy and manifest. Its manifest line is not adjacent to
`human_gates.py`'s or `knowledge_plane.py`'s, so this run does not add
another conflict to the open queue.

## Decisions & alternatives

- **Strip quoted material** over **the seed's `Implements: WO-####`
  trailer** — the trailer is the more precise mechanism and it is the one
  that would also fix PR #306's prose-provenance case. It loses here
  because it obliges every future work-order PR body, including the ones
  the assembler and the daily routine generate, to carry a new trailer.
  That is a repo-wide convention with a migration, which the autorun rules
  name as the kind of gap to surface rather than assume. Left open, and
  `defect.md` says the seed is only half-closed.
- **Strip quoted material** over **changing `cited_work_order` to ignore
  quoted tokens** — that would also stop a fenced-but-resolvable token
  from flipping its label, losing the no-regression property above for no
  gain. Resolution should see everything; only the *claim* test should not.
- **Fences and blockquotes** over **fences alone** — PR #330's token was
  in a blockquote, so fences alone would not have fixed the observed case.
- **Fences and blockquotes** over **also stripping inline code** —
  rejected above: backticks are how this repo writes identifiers in real
  claims.
- **Strip in `validator.py`** over **a shared helper in the knowledge
  plane** — one caller, no divergence, and "what counts as an authorial
  claim in a PR body" is the validator's concern, not the typed-ID
  grammar's.

## ADRs

**One, and it is owed.** ADR-0057 wrote this gate and justified it in
prose: "the relaxation is gated on `not WO_TOKEN.findall(body)`". Changing
that expression changes a decision an accepted ADR recorded, so it is
amended by **ADR-0062**, filed `provisional`, with ADR-0057's status line
and its index row updated together (detector D reads them byte-for-byte).
ADR-0057's body is not rewritten.
