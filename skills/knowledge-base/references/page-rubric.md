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

## Refuse

- Overviews, architecture tours, directory listings — measured not to
  help an agent find the right file.
- Anything the code says plainly: signatures, config values, file layout.
- Restated vocabulary — link to the glossary (CONTEXT.md or equivalent).
- Restated decisions — link to the ADR.
- **"Do not X" guardrails.** Those go in the always-loaded file itself,
  where the agent reads them before acting.

## Frontmatter

Every page in `docs/kb/` opens with exactly these fields. `kb.py lint`
checks them.

```
---
summary: One line, the page's index entry. Say the fact, not the topic.
sources: path/to/file.py, path/to/other.py
verified: <full commit sha the claims were checked against>
related: other-slug, another-slug
---
```

- `summary` — the only owner of the page's index line. "Detector C scans
  run artifacts for WO tokens" beats "Notes about detector C".
- `sources` — repo-relative paths the claims rest on. When any of them
  changes in git after `verified`, lint calls the page stale.
- `verified` — the commit at which a person (or an agent with a person
  promoting the edit) last checked every claim against `sources`. Use a
  commit already on the default branch: a squash merge discards a
  feature branch's commits, and a fresh clone then reports the sha as
  not a commit.
- `related` — slugs of sibling pages; may be empty.

Lists may be bare (`a, b`) or bracketed (`[a, b]`).

## Shape

- One subject per page, short — a screen, not an essay. `kb.py stats`
  prints page lengths.
- Claims as short paragraphs or bullets, each traceable to a source.
- A superseded claim stays, struck through or under a "Superseded"
  heading with the date and what replaced it — the history is part of
  the knowledge.
