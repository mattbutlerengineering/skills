---
stage: review
run: maintenance:quoted-token-is-not-a-claim
date: 2026-08-24
assumptions:
  - "Severity is arbitrated here rather than by the operator — the run is autorun-driven. F1 is called major because it is a false statement in the one place a caller reads the contract, and it was fixed before Ship. F2 and F3 are deferred with reasons; neither is a regression this run introduced."
  - "Scope is main..HEAD (four commits, 13 files), read as a diff. The pre-existing 80-column line at validator.py:181 and the nine standing one_owner.py groups are outside it and are named, not touched."
---

# Review: one expression, and what it made false

Reviewed `main..HEAD` — `064f35e`, `5210702`, `b15d789`, `b949dd8` — plus
the working-tree F1 fix below. 13 files, +891/−6, of which the production
change is 48 lines in `validator.py` and one deleted line.

## What was examined

- **`validator._unquoted` and the skip gate** — line by line, against
  `architecture.md`'s contract and ADR-0062's decision.
- **Every other statement of the rule in the repo** — `grep` for
  `uncited`, `cites no work order`, `No work order:` across `*.py`,
  `*.md`, `*.yml`. Four hits outside this run's own artifacts: two
  docstrings in `validator.py` (F1), `gates.check_pr_traceability` (F2),
  and `plans/014-dispatch-lifecycle-labels.md`, which is a historical
  implementation plan and is deliberately not rewritten.
- **The one-owner pre-pass**, as a design check rather than a gate.
- **Input handling**, since a PR body is untrusted author-controlled text.

## Findings

### F1 — major, FIXED — two docstrings state the old rule as the contract

`validator.py`'s module docstring said *"A PR that NAMES a work order
which resolves to none stays a problem on both"*, and `run_lifecycle`'s
said *"a body that names a work order but resolves to none … stays loud
in both legs"*. After ADR-0062 both are **false as written**: a body that
names one only inside a fence resolves to none and is now a silent no-op.

Failure scenario, concrete: a maintainer debugging a housekeeping PR that
merged without flipping its label reads `run_lifecycle`'s docstring,
concludes the body must have resolved successfully, and looks for the bug
in `tracker_issue` or `_flip`. The docstring sends them to the wrong half
of the function. That is worse than no docstring.

**Fixed in this stage**, both passages plus the inline comment at the
gate, each now saying that "cites" is read off `_unquoted(body)`. The
battery was re-run after the fix and `validator.py` is mirrored, so the
payload twin and manifest were regenerated with it:

```
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
$ python3 -m unittest discover tests
Ran 1350 tests in 16.745s

OK
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

### F2 — major, DEFERRED — two modules now answer the same question differently

`gates.check_pr_traceability` (detector B, gates.py:304) asks the same
question this run just re-answered — *does this PR body cite a work
order?* — and still reads the raw body:

```
$ sed -n '318,320p' gates.py
    problems = []
    if not WO_TOKEN.search(body) and not NO_WO_DECLARATION.search(body):
        problems.append("B: PR body cites no work-order id")
```

So after ADR-0062 the repo holds two answers. They are not symmetric,
which is why this is a deferral and not a fix:

- **B is lenient where the validator is strict.** A quoted token
  *satisfies* B, so a PR whose only token is in a fence passes B without
  the `No work order: <reason>` waiver — its audit trail records a
  citation the author never made.
- **Nothing regresses.** B behaved exactly this way before this run;
  the change makes the divergence visible rather than creating it.
  Verified against the real case: PR #330 carries `No work order: backlog
  hygiene, not dispatched work and not a pipeline run` as its first line,
  so tightening B would not have broken it either.

Deferred because **tightening B is a convention change, not a bug fix**:
it would newly require a waiver line from every PR that quotes an
identifier without claiming one, which obliges assembler- and
routine-generated bodies exactly as the `Implements: WO-####` trailer
does. That is the boundary `defect.md` drew for this run, and crossing it
here would cross it silently. Seeded for a run that can decide it, where
the honest question is whether "quoted material" has earned a second
caller and belongs in the knowledge plane beside `WO_TOKEN` — CLAUDE.md's
bar is multiple real callers AND observed divergence, and F2 is the
divergence half arriving.

### F3 — minor, DEFERRED — `_unquoted` is a line walk, not a CommonMark parser

A four-backtick fence is closed by the first three-backtick line, an
indented code block is not recognised as one, and a lazy blockquote
continuation is not modelled.

Failure scenario: a body wraps ```` ```` ````-delimited content that
itself contains ``` ; the inner run closes the fence early and the tail
of the body is scanned. Every such mis-read **keeps** a token, so the
outcome is a problem reported rather than a wrong label flip — the same
direction as before this run. Deferred as not worth a markdown parser in
a stdlib-only repo; recorded in `verification.md` under *Not verified* so
it does not read as covered.

## Examined and NOT findings

- **`\r\n` bodies.** GitHub returns CRLF. `str.splitlines()` treats
  `\r\n` as one boundary and drops it, so the fence and blockquote tests
  see clean lines; the real PR #330 body, fetched over the API, strips
  correctly in `verification.md`'s D1 probe.
- **Empty or absent body.** `run_lifecycle` already coerces `None` to
  `""`; `_unquoted("")` returns `""`.
- **Injection and denial of service.** No regex is added and none is
  removed — the helper is `str.lstrip`/`str.startswith` over
  `splitlines()`, linear in the body, no backtracking surface. Nothing is
  interpolated into a shell or a `gh` argument.
- **A body that hides its citation in a fence to dodge a flip.** Possible,
  and it is the consequence ADR-0057 already accepted and ADR-0062
  restates: the missed flip is cross-plane drift, reported by `sweeps.py
  reconcile`, not gated at merge.
- **`defect.md`'s token count.** Corrected in `verification.md` D1 (two
  → one, with the failing run's own log as the authority). A brief that
  over-counted its own evidence is worth naming; it is not a code finding
  and `defect.md` is not rewritten.
- **The one-owner pre-pass.** Nine groups, all pre-existing; neither
  `FENCES` nor `_unquoted` appears in any of them.

```
$ python3 one_owner.py | tail -1
one-owner: 9 problem(s)
$ python3 one_owner.py | grep -c "_unquoted\|FENCES"
0
```

- **`plans/014-dispatch-lifecycle-labels.md`.** Describes the gate as
  built in that plan. Plans are the historical record of what was
  designed then, like ADRs; ADR-0062 is where the change is recorded.
- **`validator.py:181`, 80 columns.** Pre-existing, outside this run's
  scope, logged in `breakdown.md`'s Notes.

## Verdict

**No unfixed critical or major findings.** F1 was fixed and re-verified in
this stage; F2 and F3 are deferred with reasons above and seeded for
Operate. Ship may proceed — as prepare-and-stop, since the brief
authorises no release, and under ADR-0036 clause 2, which requires a
non-authoring reviewer to re-execute the verification before merge.
