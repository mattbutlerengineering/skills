---
stage: architect
run: feature:fail-closed-roll-up
date: 2026-10-17
ux: skipped — Docs, two skill templates and one gate rule; no screens or flows.
assumptions:
  - "No live interview: every open question below was settled from autorun-brief.md, idea.md, prd.md and the code, taking the recommended default. Nothing settled here is irreversible or expensive: the rule is one constant, one regex and one helper inside detector H, and ADR-0107 is provisional."
  - "Recommended default taken (cutoff): ROLLUP_ADOPTED = \"2026-10-17\", today's date and ADR-0107's own date, over a constant that Ship sets at merge. Precedent: COVERAGE_ADOPTED is ADR-0072's own date. A value fixed now is one review sees; a value Ship moves is not. Ship confirms it and changes nothing."
  - "Codebase default taken (missing date): a verification.md with no readable frontmatter date is judged, not grandfathered (fail closed), the convention COVERAGE_ADOPTED and CAPTURE_ADOPTED already follow, so omitting the date cannot dodge the rule. The prototype found 0 of 77 tracked files without a date."
  - "Recommended default taken (no Summary): the rule does not fire on an artifact with no section titled exactly Summary (case-insensitive). 48 of 77 have none; there is no roll-up line to judge. All 29 Summary headings on main are spelled exactly `Summary`."
  - "Recommended default taken (counts or names): one test, not two. The Summary passes when any Summary section carries, outside a fence, a word of the unknown vocabulary; there is no separate pass-word scan for 'asserts an unqualified pass', because a Summary that names the unknown kind is qualified and one that names nothing reads as a pass."
  - "Recommended default taken (head matching): kind-agnostic. Any disclosure word in the Summary satisfies any disclosed criterion ('1 DEFERRED' satisfies a SKIPPED criterion): every disclosure head is the same claim kind, unknown."
  - "Vocabulary widened by evidence, not by fit: the disclosure heads alone fail the honest toolsmith-mine-pr-permissions Summary ('2 NOT YET VERIFIABLE'; ablation output below), so `not yet`, `unknown`, `unmet` and `unproven` join the Summary vocabulary. `unknown` is the claim kind's own name."
---

# Architecture: Fail-closed roll-up for verification Summaries

## Approach

One new rule inside detector H, reading the section parse H already
makes, plus the words and the rule written once in `CONTEXT.md` and
pointed to from the protocol and two templates. `verification_sections`
gains one per-section flag: does an unfenced line carry a word of the
unknown vocabulary. `evidence_problems` gains one check after its
per-section loop. When the artifact's frontmatter `date:` is on or after
`ROLLUP_ADOPTED` (or missing), and a non-Summary section holds a
labelled disclosure (`_is_disclosure`), then some `## Summary` section
must carry that flag, or H reports one problem at the Summary heading.
Nothing outside `gates.py` changes in code. `check_evidence_honesty`
already passes the full text, frontmatter included, so the date is read
from the text. The grammar stays pure over text, exercisable without a
fixture tree, as H's docstrings promise.

The other shape compared: a separate detector (the next free letter, P)
that reads `verification.md` on its own. It loses. It would be a second
parse of the same artifact, which the brief forbids. It would split one
artifact's honesty between two letters. And it would need its own roster
row, selftest leg and mirror note for a rule that is H's second half.

Settled open questions (PRD "Open questions"):

1. **Grammar for "counts or names" and "unqualified pass".** One test.
   The Summary must name the unknown kind: a word from
   `SUMMARY_UNKNOWN_TERM`, read unanchored on any unfenced Summary line.
   The words are H's disclosure heads (n/a, skip/skipped, defer/deferred,
   untested, unverified, pending, todo, tbd, not run / ran / verified /
   executed / checked / tested / attempted) plus `not yet`, `unknown`,
   `unmet` and `unproven`. A count ("1 NOT RUN") satisfies it because the
   count carries the word. There is no pass-word scan: a Summary that
   names the kind is qualified, and one that names nothing reads as a
   pass.
2. **Cutoff value and missing date.** `ROLLUP_ADOPTED = "2026-10-17"`,
   ADR-0107's date. A missing date is judged (fail closed).
3. **No `## Summary`.** The rule does not fire. Confirmed, not changed.
4. **Disclosure-head matching.** Kind-agnostic. Any word satisfies any
   disclosed criterion.

## Components

### `verification_sections` (gates.py, extended)

- Responsibility: the one section parse of a verification artifact.
  Each section dict gains `"names_unknown": bool`, true when an unfenced
  line in that section matches `SUMMARY_UNKNOWN_TERM`. It is recorded
  for every section, because the parse does not know which one is the
  Summary, and read only for Summaries. No second parse.
- Collaborators: `_walk_sections`, `_skip_frontmatter` (unchanged).

### `_rollup_problems(sections)` (gates.py, new, private)

- Responsibility: the roll-up rule over already-parsed sections. Summary
  sections are those whose stripped title casefolds to `summary`. The
  disclosed sections are the non-Summary sections with at least one
  `results` verdict that `_is_disclosure` accepts, in artifact order,
  each counted once. It returns `[]` when there is no Summary, no
  disclosed section, or any Summary has `names_unknown`. Otherwise it
  returns one `(lineno, suffix)`, at the first Summary's heading line.
- Collaborators: `_is_disclosure` (unchanged); called by
  `evidence_problems`.

### `evidence_problems(text)` (gates.py, extended)

- Responsibility: unchanged, plus one step after the per-section loop
  and before the artifact-wide backstop. When `_rollup_applies(text)`, it
  extends with `_rollup_problems(sections)`. The backstop needs no
  labelled verdict anywhere and the roll-up needs one, so the two never
  both fire on one artifact.
- `_rollup_applies(text)`: `date = (parse_frontmatter(text) or
  {}).get("date")`. It is false only when `date` is a string `<
  ROLLUP_ADOPTED`, the lexical comparison O and M already make. The
  import widens `from protocol import read_frontmatter` to add
  `parse_frontmatter`. It adds no new module edge, so ADR-0091's
  dual-membership pin does not move.

### `check_evidence_honesty(root, parsed)` (gates.py, unchanged)

- Responsibility: walk each run's `verification.md` and prefix `H:
  {rel}:{lineno}`. The new suffix flows through it untouched.

### Selftest (`gates_selftest.py`, extended)

- `evidence_honesty_defect_fixture` gains one artifact dated on the
  cutoff, with a full-pass Summary over one `NOT RUN` criterion. The H
  `expect` gains its substring. The clean fixture is unchanged: none of
  its three artifacts has both a Summary and a labelled disclosure.

### Docs and templates (no code)

- `CONTEXT.md`, the only owner of the words: **Claim kind**, with
  observed (quoted output), derived (computed from observed), inferred
  (judgement) and unknown (not examined; what NOT RUN, skipped, deferred
  and n/a disclose). Then **Fail-closed roll-up**: unknown, unsupported,
  truncated and skipped never aggregate to pass, so a Summary or Verdict
  counts or names them.
- `docs/pipeline-protocol.md`: one short section that states the rule
  once, links `CONTEXT.md` for the kinds without redefining them, and
  cites ADR-0107 for the gate half.
- `skills/verify/TEMPLATE.md` `## Summary` placeholder and
  `skills/review/TEMPLATE.md` `## Verdict` placeholder: count or name
  every NOT RUN / unknown item, and never read as an unqualified pass
  over them. Each SKILL.md gets the same wording where it describes
  writing that line: `skills/verify/SKILL.md`'s "summary of it" line.
  `skills/review/SKILL.md` never describes the Verdict line (a grep for
  "verdict" finds nothing), so only review's template changes.
- `gates.py`'s module docstring, H roster entry: add the Summary half.

### Payload

- `gates.py` and `gates_selftest.py` are `factory_init.MIRRORS` entries
  (identity transform). Run `python3 factory_init.py update-manifest`
  after the edit (detector E). `.claude-plugin/plugin.json` is not
  touched (ADR-0095).

## Data model

No storage. The inputs are the artifact text and three fixed facts in
`gates.py`:

```python
ROLLUP_ADOPTED = "2026-10-17"          # ADR-0107; pinned by a test
SUMMARY_TITLE = "summary"              # casefolded, stripped title match
SUMMARY_UNKNOWN_TERM = re.compile(     # unanchored; outside fences only
    r"(?<![\w/-])(?:n/a|skip(?:ped)?|defer(?:red)?|untested|unverified"
    r"|pending|todo|tbd|not[\s-]+(?:yet|run|ran|verified|executed|checked"
    r"|tested|attempted)|unknown|unmet|unproven)(?![\w/-])",
    re.IGNORECASE)
```

The section dict grows from `{title, lineno, evidence, not_run,
results}` to add `names_unknown`. Existing tests read named keys, never
whole dicts (`tests/test_gates.py` line 2484 is the only direct reader),
so the shape change is additive.

## Interfaces & contracts

### The new H problem string

- Input: one `verification.md` text whose frontmatter `date:` is ≥
  `ROLLUP_ADOPTED` or missing. It has at least one section titled
  `Summary`, and at least one other section holding a labelled verdict
  that leads with a disclosure.
- Output, when no Summary section carries an unknown-vocabulary word
  outside a fence (exactly one per artifact):

  ```
  H: {rel}:{lineno} summary "{title}" neither counts nor names the {n} criterion section(s) disclosed as not run (first: "{criterion}", line {l}); unknown never rolls up to pass
  ```

  `{lineno}` is the first Summary's heading line. `{title}` is that
  heading's text as written. `{n}` is the count of disclosed non-Summary
  sections. `{criterion}` and `{l}` are the first disclosed section's
  title and its first disclosing verdict's line.
- Failure modes: an unreadable file is unchanged (`H: {rel} cannot be
  read: …`). An unclosed fence is reported first, as today, and the
  sections after it are fence content, so a disclosure inside it is not
  read. It is pure and offline: no timeout, no retry question.

### Accepted behaviour changes (old rule vs new rule)

The new rule only adds problems. They differ on exactly one class of
input: a verification artifact dated ≥ 2026-10-17 or undated, with a
`Summary` section and a labelled disclosure elsewhere, whose Summary
carries none of the vocabulary words outside a fence. Run over every
tracked input, that class is empty on main (prototype below, with and
without the cutoff). The changes that class accepts:

- A Summary that mentions the kind only in negation ("nothing was
  skipped") passes. This is a known dodge, recorded in ADR-0107's
  Consequences.
- A Summary that names the kind only inside a fenced block fails. A
  fence is quoted output, not the author's roll-up.
- A Summary named anything but `Summary` ("Results", "Verdict") is not a
  Summary. A heading rename escapes the rule. The template spells the
  heading, and all 29 on main use it.
- A `### Counts` subsection under `## Summary` is its own section, so its
  words do not count toward the Summary. The prototype found none.

### Prototype (read-only, outside the repo)

A scratch script imported `gates` from this branch at `4db9aee`. It
reused `verification_sections`, `_walk_sections`, `_skip_frontmatter`
and `_is_disclosure`, added the flag above, and ran the rule over `git
ls-files 'docs/**/verification.md' docs/verification.md`. Output:

```
files: 77
no readable date: 0
with a '## Summary' section: 29
with >=1 labelled disclosure (any section): 7
summary-like headings: {'Summary': 29, '2. The recorded output states the failures, per case and in the summary': 1, "A1 — `work_queue.main`'s summary line is pinned on every leg that emits one": 1}
problems on real tree, cutoff 2026-10-17: 0
problems if every file were dated past the cutoff: 0

fixtures:
  failing (post-cutoff, full-pass summary): [(7, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Live dispatch", line 23); unknown never rolls up to pass')]
  failing, dated before cutoff: []
  failing, no date (fail closed): [(6, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Live dispatch", line 22); unknown never rolls up to pass')]
  counts it ('1 PASS, 1 NOT RUN'): []
  names a different kind ('1 deferred'): []
  no disclosed criterion: []
  prose-only 'not run', no labelled disclosure: []
  no Summary heading: []
  summary says 'not run' only inside a fence: [(7, 'summary "Summary" neither counts nor names the 1 criterion section(s) disclosed as not run (first: "Live dispatch", line 26); unknown never rolls up to pass')]

honest shapes on main, re-dated past the cutoff:
  docs/features/orchestrator/verification.md: []
  docs/fixes/toolsmith-mine-pr-permissions/verification.md: []
  docs/features/codex-style-standards-enforcement/verification.md: []
```

Ablation, with the disclosure heads alone and no `not yet` / `unknown`
/ `unmet` / `unproven` (True means the honest file would fail):

```
ablation docs/features/orchestrator/verification.md False
ablation docs/fixes/toolsmith-mine-pr-permissions/verification.md True
ablation docs/features/codex-style-standards-enforcement/verification.md False
```

The existing H tests and selftest fixtures carry no `date:`, so the new
rule judges them (fail closed). A read of every fixture holding a
`## Summary` (`tests/test_gates.py`, `gates_selftest.py`) found none
that also holds a labelled disclosure in another section, so none
changes outcome. Implement confirms this with the full suite.

## Stack & dependencies

- Python 3 stdlib only (`re`, plus `protocol.parse_frontmatter`, already
  a sibling import). No new module and no new mirror entry.

## Decisions & alternatives

- **The rule lives in H, reading H's one parse**, over a new detector
  P. A second parse of the same artifact, and the artifact's honesty
  split across two letters (ADR-0107).
- **Trigger on labelled disclosures (`_is_disclosure`)** over H's prose
  `not_run` flag. The flag fires on ten files whose prose discloses no
  criterion (idea.md) (ADR-0107).
- **Name the kind** over requiring a count. A count rule rewards a
  number, and one honest Summary on main names its kind in a sentence
  (ADR-0107).
- **Kind-agnostic matching** over same-head matching. Every head is
  one claim kind (ADR-0107).
- **No pass-word scan** over judging "unqualified pass" on its own. It
  would be a second free-prose grammar that adds nothing once naming is
  required (ADR-0107).
- **`ROLLUP_ADOPTED` is ADR-0107's date** over a constant Ship sets. A
  constant fixed now is one review sees; the precedent is ADR-0072's
  `COVERAGE_ADOPTED` (ADR-0107).
- **A missing date is judged** over grandfathered. Same direction as
  O and M; omitting the date cannot dodge it (ADR-0107).
  Amended 2026-10-17 (review fix loop, Owner decision): `_rollup_applies`
  grandfathers only a `YYYY-MM-DD` value (quotes and whitespace stripped,
  a datetime read by its date part) before the cutoff, so a quoted,
  empty or non-ISO `date:` is judged; `SUMMARY_UNKNOWN_TERM` gained
  Summary-only not-examined words and lets `-` or `/` follow a word
  (ADR-0107's amendment).
- **A flag on every section** over passing the Summary's raw lines out
  of the parse. One boolean keeps the section dict small, and a
  Summary is just a section to the parser.
- **One problem per artifact** over one per disclosed section. The
  fix is one edit to one line; a count in the string says how many.
- **Review's Verdict is template-only** over gating `review.md`. Out of
  scope (PRD); no parse of review verdicts exists to reuse.
- **`stdlib-only`** holds: no dependency is added.

## ADRs

- [ADR-0107](../../adr/0107-a-summary-never-rolls-unknown-up-to-pass.md):
  a verification Summary never rolls a disclosed NOT RUN up into a pass.
  The rule, its grammar, the cutoff and the missing-date direction.
  Provisional.

PRD traceability: the failing-fixture, passing-fixture, honest-shapes,
prose-only and pre-cutoff criteria map to `_rollup_problems` and
`_rollup_applies` through `evidence_problems`. The constant pinned by a
test maps to `ROLLUP_ADOPTED`. "0 problems on main" is the prototype
above. The `CONTEXT.md`, protocol and template criteria map to the
docs and templates component. The ADR criterion is ADR-0107. Battery
and detector E map to the Payload component.
