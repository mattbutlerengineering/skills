# Ingest

Ingest turns one source into a proposed, itemised change to the knowledge
base. The agent drafts; a human promotes. Two failure modes shape every
rule here: an unverified page becomes a prior that poisons later work,
and whole-page rewrites erode detail a little more each time.

## The four verbs

| Verb | When | What changes |
|---|---|---|
| ADD | The source teaches a non-inferable fact no page holds | A new claim on an existing page, or a new page |
| UPDATE | A page's claim is now incomplete or wrong | The new claim is added; the old one is kept, marked superseded with the date |
| DELETE | A claim is no longer true and nothing replaces it | The claim is removed; the proposal says what disproves it |
| NOOP | Nothing in the source passes the page rubric | Nothing — say so in one line |

NOOP is the most common right answer. A merged PR that did what its
title says usually teaches nothing the code does not now show.

## The proposal

Present it as a numbered list, one item per claim:

```
1. UPDATE docs/kb/<slug>.md — "<old claim>" → "<new claim>"
   source: path/to/file.py (changed in <sha>); supersedes the 2026-08 claim
2. ADD docs/kb/<new-slug>.md — "<claim>"
   source: path/to/file.py; summary: "<one line>"
3. NOOP — the rename in <PR> is visible in the code
```

Then stop and wait. Apply only the numbers the user promotes, exactly as
proposed. Never fold in an unproposed edit while applying.

## Applying

- Touch only the claims promoted; leave the rest of the page byte-for-byte.
- Set `verified:` to the commit you checked the claims against, and add
  any new source path to `sources:`.
- A new page follows `page-rubric.md`'s frontmatter.
- Run `kb.py index` (its summary line may have changed), then `kb.py lint`.

## Not ingest

- Answering a question from the knowledge base. Read the index, read the
  page, answer, cite the page. If the answer revealed a missing fact,
  offer it as an ADD proposal — do not file it.
- Bulk regeneration of pages from the code. That produces exactly the
  inferable, unverified content this skill exists to keep out.
