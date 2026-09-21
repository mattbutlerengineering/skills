---
stage: architect
run: maintenance:closed-intake-mutes-the-detector
date: 2026-08-25
assumptions: ["Chosen without live interview: this run is autorun-driven, so each option below is decided against something already recorded — known_keys' own docstring, the three key namespaces in sweeps.py, and the module's stated preference for reporting a doubt rather than swallowing it — with the citation given so the operator can overturn a call by reading rather than re-deriving.", "NO ADR is offered. Nothing in docs/adr/ records the intake dedupe rule; it lives in known_keys' docstring, which is where this run amends it. The architect skill's bar is hard to reverse, surprising without context, AND the result of a real trade-off — this is one function, reversible by git revert, in a tool no other module imports for this purpose.", "D2 and D3 resolve their unknowns in opposite directions on purpose. The reasoning is blast radius, not taste, and it is written out below so the next reader does not read it as an inconsistency and 'fix' one of them."]
---

# Architecture: a closed intake stops suppressing, unless the source re-reports

## Approach

One function changes. `known_keys` asks the board which intake keys are
already accounted for; today it answers "any key on any issue". It will
answer "any key on any issue, **except** a key whose issue is closed and
whose namespace has no outside source to re-report it".

Everything else — the window rule, `screen`, `file_issues`' cap, the three
intake constructors, Sentry dedupe — is untouched.

## Components

### `sweeps.RE_REPORTED` — new, one line, the whole rule

```python
RE_REPORTED = ("sentry:",)
```

The key namespaces whose signal an outside source keeps re-reporting.
A key in one of these suppresses filing in **any** issue state, which is
today's behaviour and is correct: closing `[sentry] PROJ-7K` is a
maintainer's answer, and Sentry will still lead the payload with it next
week.

Every other namespace is detector-derived. Nothing outside this repository
re-reports it, so a closed issue is not an answer — it is an issue someone
closed while the condition may still hold.

### `sweeps.known_keys` — reads the state, filters on it

The listing gains one field, `state`, on the call it already makes:

```python
    read = gh_read(["issue", "list", "--state", "all", "--json",
                    "number,state,body"], ...)
```

and a key is collected unless it is detector-derived **and** its issue's
state is the literal `CLOSED`.

The name stays. A closed detector intake is genuinely no longer *known* in
the sense this function means — closing it did not answer the condition, so
it accounts for nothing. The docstring says that in as many words.

### `sweeps.file_issues` — unchanged

It calls `known_keys(run)` once and drops plans whose key is in the
returned set. That contract is exactly the same; only the set's membership
rule moved.

### `tests/test_sweeps.py` — the rule's four corners

`TestFileIssues` already drives `known_keys` through fixtures. Four cases
are added: detector key + closed issue (files), detector key + open issue
(suppressed), `sentry:` key + closed issue (suppressed), and a state that
is not `CLOSED` at all (suppressed).

## Data model

No new type. `Intake` is unchanged — see D1 for why the rule cannot live
there.

## Interfaces & contracts

### `known_keys(run=gh_runner) -> (set[str] | None, list[str])`

- **Output shape unchanged.** `(keys, problems)`, or `(None, problems)`
  when the listing failed — dedupe is then impossible and the caller must
  not file.
- **Membership rule, new:** a key is in the set iff it starts with one of
  `RE_REPORTED`, **or** its issue's `state` is not the literal `"CLOSED"`.
- **Failure modes unchanged:** a listing failure still yields `None`; a
  full `LIST_WINDOW` window still reports its own problem string with the
  same wording.

### The `state` field

Read as `issue.get("state")`. Compared against the exact string `"CLOSED"`.
Anything else — absent, `None`, a different spelling, an unexpected value —
takes the suppressing branch, which is today's behaviour.

## Stack & dependencies

Stdlib only. No new import. `sweeps.py` is not in `factory_init.MIRRORS`,
so nothing mirrors into the payload and no manifest regenerates.

## Decisions & alternatives

**D1 — the rule reads a key string, not an intake. Forced, not chosen.**
`known_keys` reads keys off the bodies of issues that already exist. For a
closed issue there is no `Intake` object anywhere — the plan that produced
it ran weeks ago in a different process. So carrying a `kind` field on
`Intake` cannot answer this question, however tidy it would look. The
namespace prefix already in the key is the only thing available, which is
why the key format is load-bearing and now says so in the docstring.

**D2 — list the re-reported namespaces, not the detector-derived ones.**
The two are complements, so the choice is only about what a forgotten
addition does.

- *List detector prefixes (`("sweep:",)`), default re-reported.* A new
  detector-derived intake kind that nobody adds to the list is muted
  forever — silently, which is this defect recurring under a new name.
- *List re-reported prefixes, default detector-derived.* **Chosen.** A new
  upstream-fed kind that nobody adds gets re-filed while its issue is
  closed and its condition holds. Noisy, bounded to that one kind, and
  visible on the board within a day.

A loud wrong answer that someone fixes beats a silent one that nobody sees.

**D3 — only the literal `CLOSED` stops suppression; every other state
value behaves exactly as today.** This resolves its unknown the *opposite*
way to D2, and the reason is blast radius rather than preference:

- D2's unknown is one intake kind, introduced by a person editing this file,
  with a reviewer looking at the diff. Worst case: one duplicate issue per
  sweep run, for one kind, until someone adds a prefix.
- D3's unknown is the listing itself. If `state` stopped arriving — a gh
  change, a field rename, a fixture built wrong — then *every* key would
  stop suppressing at once and *every* open intake would be duplicated on
  *every* run. That is a runaway, and it is exactly the "duplicate factory"
  the window rule two paragraphs up exists to prevent.

So: prefer the loud answer where a human is already looking and the damage
is bounded; prefer today's answer where a data quirk could take the whole
board at once.

**D4 — one more `--json` field, not a second call.** `state` rides the
listing `known_keys` already makes. No extra network call, no new failure
mode, and the window rule keeps applying to the same listing.

**D5 — the filter lives inside `known_keys`, and the name stays.**
- *Return richer data and filter in `file_issues`.* Rejected: the dedupe
  rule would then have two owners — the function that fetches and the
  function that decides — which is the shape `one_owner.py` exists to name.
- *Rename to `suppressing_keys`.* Considered and rejected as churn: the
  function still answers "which keys are already accounted for", and a
  closed detector intake accounts for nothing. The docstring carries the
  precision; the call site and two test references stay put.

## ADRs

None offered — see the frontmatter assumption. Nothing in `docs/adr/`
records the intake dedupe rule. It is stated and argued in `known_keys`'
docstring, and that is where this run amends it: the Sentry paragraph is
kept for the case it actually covers, and the detector-derived case is
written next to it rather than replacing it.
