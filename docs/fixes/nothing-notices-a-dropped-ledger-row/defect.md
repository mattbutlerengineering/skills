---
stage: capture
run: maintenance:nothing-notices-a-dropped-ledger-row
date: 2026-09-20
re-entry: implement
assumptions:
  - The current taxonomy (protocol.ALL_SKILLS + lint.extra_skills(root)) is
    the same "what is a skill, right now" source check_ledger already holds
    LEDGER.md to in the forward direction — issue #455 asked whether the
    reverse direction needs a historical registry, and this run answers
    that question rather than taking it as given.
  - Scope is LEDGER.md only. README.md's reverse direction turned out not
    to be the same shape once checked against the real file; see "Design
    question not resolved here" below.
---

# Defect: nothing notices a dropped LEDGER.md row

## What is wrong

`check_ledger` (and `check_readme_skills`) close only the forward
direction: every skill in `protocol.ALL_SKILLS + extra_skills(root)` has a
row / mention. Nothing closes the reverse — a LEDGER.md row naming a skill
that has since been renamed or removed stays silent forever. Issue #455
found this during the `a-nested-slug-hides-a-dropped-row` run (#371);
`TestLedger.test_every_registered_skill_can_be_reported_missing`'s
docstring says so explicitly: "a stale row for a skill that no longer
exists has no checker at all, here or anywhere."

## Why it matters

LEDGER.md is the maturity record the repo treats as load-bearing — a
skill graduates past draft only via a real run, and the ledger is where
that is written down (ADR-0012). A row for a skill that no longer exists
is a maturity claim about nothing, and it sits there indefinitely: no
gate reads it, no test drops it, no reviewer is prompted to notice unless
they cross-reference the table against `protocol.py` by hand.

## The design question the issue raised

Issue #455 frames the gap as needing "a source of truth for 'was a
skill', which the taxonomy does not keep" — read plainly, a request for
new persistent state: a registry of retired skills.

That framing does not hold up against how `check_ledger` is actually
built. `check_ledger` already has a complete, current source of truth for
"is a skill, right now": `protocol.ALL_SKILLS + extra_skills(root)` — the
same set it walks to find missing rows. A row naming a slug outside that
set is wrong for exactly one reason, "the taxonomy has never heard of
this," and that reason is identical whether the slug was renamed,
dropped last week, or never a skill at all. The checker does not need to
know *which* of those happened, only that it isn't currently one — so no
historical registry is needed to close the LEDGER.md half. This is the
same shape as `check_ledger`, read the other way: same row extraction
(`ledger_rows`), same trusted set, set difference flipped.

**This does not fully resolve the issue as filed.** #455 names two
surfaces, LEDGER.md and README.md, and only the first turned out to be
decidable this way — see below.

## What changed

- `lint.check_ledger_no_orphans(root)`: reads `ledger_rows(LEDGER.md)` (the
  same table-row extraction `check_ledger` and #371 already established)
  and reports every row whose slug is outside
  `ALL_SKILLS + extra_skills(root)`. Row-scoped, not whole-file: the
  reading notes below the table name skills by slug too (#371's own
  finding), and a retired skill can stay in that prose — an explicit
  "dropped" note — without a live row claiming a maturity that no longer
  exists.
- Added to `lint.CHECKERS`, right after `check_ledger`.
- Missing `LEDGER.md` returns `[]`: `check_ledger` already reports that
  absence, and reporting it twice from two checkers was the exact wart
  `check_ledger_links` was written not to repeat.

## Design question not resolved here: README.md's reverse direction

The task brief for this run assumed README.md's reverse direction was the
same shape as LEDGER.md's — "walk README.md's mentions and flag any that
name a skill NOT in the current source" — and asked to confirm that
reading against how `check_readme_skills` is actually structured before
committing to it. It doesn't hold, for a reason specific to README.md's
own shape:

`check_ledger`'s forward direction and `check_ledger_no_orphans`'s reverse
direction both read the *same, narrow, structural* thing — a table row's
first cell (`ledger_rows`). `check_readme_skills`'s forward direction asks
a much looser question: does the *whole document* — a table plus several
paragraphs of prose — name this slug anywhere (`names_slug`, a whole-word
regex search over the full text). That works forward because the search
term is always a known-good slug from the taxonomy. It cannot be reversed
the same way, because there is no equivalent "the set of things README.md
claims are skills" to read back out of free prose — you would have to
invent one, e.g. "every backticked token shaped like a slug is a skill
mention." That invented rule is checked against the real file below, and
it is wrong today:

```
$ python3 -c "
import re
text = open('README.md', encoding='utf-8').read()
for tok in sorted(set(re.findall(r'\`([a-z0-9][a-z0-9-]*)\`', text))):
    print(tok)
" | grep -v -f <(python3 -c "
import protocol
print('\n'.join(protocol.ALL_SKILLS))
")
claude
```

`` `claude` `` is the CLI tool, in the line "(needs the `claude` CLI;
costs real runs)" under the on-demand commands section — not a skill
mention. A checker built on "every slug-shaped backtick token is a skill
claim" would report it as an orphan the moment it was written, against
the *current, correct* README. The Stages table (`## Stages`, `| \`slug\`
| artifact | style |`) is exactly as structural as LEDGER.md's and could
be read back safely on its own, but doing only that leaves the harder
case uncovered: utility skills are documented *only* in the prose
paragraph below the table (ADR-0023), so a table-only check would miss
precisely the mentions a retired utility skill would leave behind — the
case the issue is actually worried about.

Closing README.md's reverse direction for real needs one of:

1. A new prose convention that marks a skill mention as such (e.g. a
   fixed lead-in phrase or a dedicated list), so a reader — human or
   checker — can tell "this backtick token names a skill" from "this
   backtick token names a CLI, a file, or a flag." That is a documentation
   style decision, not a lint fix.
2. Accepting reduced recall: check only the structural Stages table (the
   part that is genuinely LEDGER.md-shaped) and explicitly not cover the
   utility-skill prose paragraph.
3. Some other structural marker not considered here.

Any of those is a real design call about how README.md is written, not a
question this run can settle by reading `lint.py` more closely — which is
the same reason issue #455 gave for not forcing a fix originally, just
aimed at the surface where it turns out to actually apply. Left for a
human; not implemented, not claimed closed.

## Breakdown

- [x] **1. Confirm the source-of-truth blocker is not real for LEDGER.md.**
      *Acceptance*: `check_ledger`'s own trusted set
      (`ALL_SKILLS + extra_skills(root)`) is shown to already answer "is
      this currently a skill" with no new state — done above.
- [x] **2. Pin the gap as a failing test.** *Acceptance*: a planted orphan
      row fails against `lint.py` as it was (no `check_ledger_no_orphans`
      to call).
- [x] **3. Implement `check_ledger_no_orphans` and register it.**
      *Acceptance*: the planted-row test passes; the real repo's
      LEDGER.md stays clean.
- [x] **4. Check the row/prose boundary holds in reverse too.** *Acceptance*:
      a dropped skill named only in the reading notes below the table is
      not reported (mirrors #371's own row-vs-prose finding).
- [ ] **5. README.md's reverse direction.** *Not done*: shown above to be a
      genuine design question, not a checker bug. Deferred to a human;
      issue #455 stays open for this half.
- [x] **6. Battery green.** *Acceptance*: unittest OK, `lint: 0`,
      `gates: 0`, `selftest: ok`.
