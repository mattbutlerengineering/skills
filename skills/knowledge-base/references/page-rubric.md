# Page rubric

A page earns its place only by telling an agent something it could not
cheaply learn from the code, the README, or a strong model's training
data. Ask of every claim: *would an agent that read the relevant files
still get this wrong?* If no, it does not belong.

## Admit

- **Invariants** the code relies on but does not state: "every X has
  exactly one Y", "this list must stay sorted because Z bisects it".
- **Gotchas** — something that looks fine and fails: a tool that exits 0
  on failure, a flag that silently does nothing, an ordering that only
  breaks in CI.
- **Cross-module flows** where no single file shows the whole path.
- **The why**, with its ADR: why the obvious alternative was rejected.
  Cite `ADR-####` and summarise in one line; never restate the decision.
- **External-system facts** — an API's undocumented limit, a vendor quirk.
- **What was tried and failed**, so nobody tries it again.
- **A class of one mistake.** When three or more pages or candidates
  turn out to share one cause, propose one class page instead of one
  page each: it states the rule once, lists every instance, and cites
  each instance's own source. An agent applies a stated rule to a case
  nobody listed; it has to pattern-match look-alike pages by hand.

## Refuse

- Overviews, architecture tours, directory listings — measured not to
  help an agent find the right file.
- Anything the code says plainly: signatures, config values, file layout.
- Restated vocabulary — link to the glossary (CONTEXT.md or equivalent).
- Restated decisions — link to the ADR.
- **"Do not X" guardrails.** Those go in the always-loaded file itself,
  where the agent reads them before acting.

## Frontmatter

Every page in `docs/kb/` opens with these four fields, plus three
optional ones. `kb.py lint` checks them.

```
---
summary: One line, the page's index entry. Say the fact, not the topic.
sources: path/to/file.py, path/to/other.py
verified: <full commit sha the claims were checked against>
related: other-slug, another-slug
checked-against: <what the claims were checked against; what they were not>
checked: YYYY-MM-DD
max-age: 30d
---
```

- `summary` — the only owner of the page's index line, one sentence of
  at most 200 bytes (`kb.py lint` checks the cap). "Detector C scans
  run artifacts for WO tokens" beats "Notes about detector C". On a
  gotcha page the summary leads with the symptom an agent meets when
  the gotcha bites (the error text, or the wrong result), then the
  cause and the fix, still inside the same 200 bytes. Lint does not
  check this; it is how the next agent recognises the page.
- `sources` — repo-relative paths the claims rest on. When any of them
  changes in git after `verified`, lint calls the page stale.
- `verified` — the commit at which a person (or an agent with a person
  promoting the edit) last checked every claim against `sources`. Use a
  commit already on the default branch: a squash merge discards a
  feature branch's commits, and a fresh clone then reports the sha as
  not a commit.
- `related` — slugs of sibling pages; may be empty.
- `checked-against` (optional) — what the claims were checked against,
  and what they were not: "the GitHub API; not GitHub's docs", or
  "macOS zsh with gh 2.62; not Linux CI". Alone, it records where a
  claim was verified and never ages.
- `checked` and `max-age` (optional, always as a pair, and only beside
  `checked-against`) — the date of that check and how many whole days
  it holds, written `30d`. Once today is past `checked` plus `max-age`,
  `kb.py lint` reports the page as past its declared age; it never runs
  the check itself. When a claim rests on a system outside the repo,
  so no cited file will ever change, declare all three. A page whose
  claims rest only on repo files needs none of them: `sources` and
  `verified` already age it. There is no default age.

Lists may be bare (`a, b`) or bracketed (`[a, b]`).

## Shape

- One subject per page, short — a screen, not an essay. `kb.py stats`
  prints page lengths.
- Claims as short paragraphs or bullets, each traceable to a source.
- A gotcha page may add one short wrong/right pair: a `Wrong:` line
  with what an agent would naturally do, and a `Right:` line with what
  works. It is optional, and one pair, not a gallery of examples.
- Compile, don't compose. Keep the source's own terms, add no filler or
  framing, and never restructure a page while adding a claim to it.
- A superseded claim stays, struck through or under a "Superseded"
  heading with the date and what replaced it — the history is part of
  the knowledge.
