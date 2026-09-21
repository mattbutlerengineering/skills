---
stage: capture
run: maintenance:nothing-notices-a-dropped-readme-mention
date: 2026-09-20
re-entry: implement
assumptions:
  - This run continues the investigation
    docs/fixes/nothing-notices-a-dropped-ledger-row/defect.md (PR #501)
    left open: issue #502 asks specifically whether README.md's reverse
    direction is a checker bug or a design question, having already ruled
    out "every slug-shaped backtick token, whole document" as the
    obvious-but-wrong candidate.
  - The trusted "is a skill, right now" set is the same one check_ledger,
    check_ledger_no_orphans and check_readme_skills already use:
    `protocol.ALL_SKILLS + lint.extra_skills(root)`.
---

# Defect: nothing notices a dropped README.md mention

## What is wrong

`check_readme_skills` closes only the forward direction: every skill in
`protocol.ALL_SKILLS + extra_skills(root)` is named somewhere in
README.md. Nothing closes the reverse — a README.md mention naming a
skill that has since been renamed or removed stays silent forever. Issue
#455 raised this for both LEDGER.md and README.md; PR #501 closed the
LEDGER.md half (`check_ledger_no_orphans`) and filed issue #502
specifically because README.md's reverse direction turned out not to be
the same shape.

## Why it matters

README.md is the plugin's install-time pitch — the first thing a reader
sees when deciding whether to install and what it ships. A mention that
outlives its skill is a false claim sitting in public-facing
documentation indefinitely, and nothing here is like `check_ledger`,
where a maturity row is at least contained to one internal-facing file:
a stale README mention is user-facing. It is also exactly how the
forward gap was found in the first place — `interactive-architecture-diagram`
shipped with no README mention at all until `check_readme_skills` was
added; the reverse failure mode (a mention that outlives its skill) has
no checker at all.

## Investigating the three options issue #502 laid out

Issue #502 named three ways to close this:

1. A new prose convention marking a mention as such (a fixed lead-in
   phrase, or moving utility-skill descriptions into their own list).
2. Accepting reduced recall: check only the structural `## Stages` table.
3. Some other structural marker not yet considered.

Re-reading `README.md`'s actual `## Stages` section (not just the
sentence issue #502 quotes) surfaces one issue #502 didn't name: **the
section already has a structural marker, and it isn't only the table.**

The section reads:

```
## Stages

| Skill | Stage artifact | Style |
|-------|----------------|-------|
| `next` | (a table row per stage skill) |

Beside the stages, the plugin ships utility skills (ADR-0023 — a link to
the ADR, not a skill mention) that act on the work surrounding the
pipeline rather than a run's artifacts: `address-pr-review` works
reviewer feedback on a PR you authored (one sentence per utility skill,
each opening with its own backticked slug) ... `autorun` drives a whole
run end to end ... `mermaid` turns a process ...

The shared rules (run discovery, orientation table, soft gating,
frontmatter conventions) live in the pipeline-protocol doc (linked by
its own backticked path, not a slug — dots and slashes rule it out of
`SLUG_TOKEN`).
```

Every utility skill is introduced by its own slug, in a backtick, at the
front of its own sentence — the same shape the table uses for stage
skills, just in prose instead of a row, because utility skills have no
row of their own (ADR-0023). The whole section — table and paragraph
alike — exists for one purpose: enumerating what the plugin ships. That
is a narrower, and different, claim than "the whole document, including
Development and Install, names skills reliably" — the claim the rejected
whole-document candidate made and the one `` `claude` `` (the CLI tool,
named under the on-demand-commands heading) falsifies.

Tested directly against the section boundary (`## Stages` through the
next `## ` heading) rather than the whole document:

```
$ python3 -c "
import re
text = open('README.md', encoding='utf-8').read()
section = re.search(r'(?ms)^## Stages\n(.*?)(?=^## )', text).group(1)
tokens = set(re.findall(r'\`([a-z0-9][a-z0-9-]*)\`', section))
import protocol
print(sorted(tokens - set(protocol.ALL_SKILLS)))
"
[]
```

Zero exceptions, including `.svg` (backticked twice in the
`architecture-diagram`/`animated-diagram` sentences, but not slug-shaped
— it opens with a dot) and the two in-prose cross-references to `capture`
and `idea` (registered stage skills, not orphans). Scoping to the section
that already exists for this purpose resolves the exact tension issue
#502 named: it is not the whole document (so `` `claude` `` is out of
scope, unlike the rejected candidate), and it is not table-only (so a
retired utility skill's prose-only mention — the case the original
report actually worried about — is still caught).

## What changed

- `lint.readme_stage_mentions(text)`: every slug-shaped backtick token
  inside README.md's `## Stages` section (the table through the next
  `## ` heading), or `None` when that heading is missing.
- `lint.check_readme_no_orphans(root)`: reports every mention
  `readme_stage_mentions` finds that isn't in
  `ALL_SKILLS + extra_skills(root)`. Added to `lint.CHECKERS`, right
  after `check_readme_skills`.
- A missing `## Stages` heading is its own problem string, not a silent
  `[]` — `check_readme_skills`'s forward direction never depended on that
  heading, so nothing else would notice it disappearing.
- Missing `README.md` returns `[]`: `check_readme_skills` already reports
  that absence.

## What this still does not catch, on purpose

- **A skill named only outside `## Stages`** — a cross-reference in
  Development or Install, say. Not this checker's job, the same way
  `check_ledger_no_orphans` does not scan LEDGER.md's reading notes below
  its table: prose outside the enumeration can discuss a retired skill
  historically without a live claim being made.
- **A future non-skill, slug-shaped backtick token added inside
  `## Stages`.** This is the accepted cost of reading prose instead of
  only a table row (unlike `check_ledger_no_orphans`, which never leaves
  its row boundary): today, zero exceptions exist inside the section, but
  nothing stops a later edit from adding one (an aside referencing some
  other tool by a slug-shaped name, say). That edit would read as a false
  orphan here — a bounded, self-correcting cost (the CI run on that same
  edit's own PR would say so), not a silent one, and the trade this run
  makes deliberately in exchange for closing the prose-only utility-skill
  gap.

## Breakdown

- [x] **1. Confirm the whole-document heuristic is still wrong.**
      *Acceptance*: the `` `claude` `` false positive reproduces exactly as
      `nothing-notices-a-dropped-ledger-row/defect.md` found it.
- [x] **2. Look for a narrower anchor already implicit in README.md's own
      structure**, rather than inventing a new authoring convention.
      *Acceptance*: the `## Stages` section boundary is shown, empirically,
      to make every slug-shaped backtick token inside it a real skill
      mention today — table and utility-skill prose alike.
- [x] **3. Pin the gap as a failing test.** *Acceptance*: a planted orphan
      mention (table row and prose-only alike) fails against `lint.py` as
      it was (no `check_readme_no_orphans` to call).
- [x] **4. Implement `readme_stage_mentions` and
      `check_readme_no_orphans`; register it.** *Acceptance*: the planted
      cases pass; the real repo's README.md stays clean.
- [x] **5. Confirm the section boundary excludes the known false
      positive.** *Acceptance*: a planted out-of-section, slug-shaped,
      non-skill token (mirroring `` `claude` ``) is not reported.
- [x] **6. Battery green.** *Acceptance*: unittest OK, `lint: 0`,
      `gates: 0`, `selftest: ok`.
