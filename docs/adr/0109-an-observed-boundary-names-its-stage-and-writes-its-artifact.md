# An observed stage boundary names its stage and writes its artifact

- Status: provisional
- Date: 2026-10-18

Recorded by the `decompose-outcome-signals` feature run
(`docs/features/decompose-outcome-signals/`), unattended, so it is
provisional. The PRD left this choice to Architect, and to the Owner if it
changes what "observed" promises. It does, so the Owner confirms or
replaces it before the first record is cited.

## Context

`decompose_signals.py` measures three Decompose outcome signals from git
history: re-plans, design gaps routed back to Architect, and
review-traced findings. Every number it reports rests on two boundaries,
decompose and implement, and each boundary is labelled observed or
inferred (Owner decision 3, in the run's autorun brief). Steps 2 to 4 of
the Decompose learning loop (#987, #988, #989) calibrate against the
observed population, so the label is the promise the baseline makes.

The protocol's "Commit at the stage boundary" section gives the subject as
`docs(<slug>): <stage> — <one line>`. Real stage commits drift from that
form. Measured 2026-10-18 over the 1086 refs this clone holds (refs/stash
excluded):

- reviewer-token's stage commits use the scope `reviewer-token`, but the
  run directory is `docs/fixes/the-reviewer-token-runs-agent-code/`. Its
  implement commit reads `implement close-out`, with no em dash.
- software-factory's decompose commit (0661682) uses the scope `factory`
  and reads `decompose PRD-0001 into …`.
- Requiring the slug to equal the directory name, plus the em dash, finds
  observed decompose boundaries for 2 runs. The rule below finds 4.

## Decision

A commit is an observed boundary for stage S of run R when both hold:

1. its subject matches `docs(<any scope>): S`, with S as a whole word
   right after `): `. The scope is not compared with R's slug, and no
   em dash is required;
2. it changes R's artifact for S (`protocol.STAGE_ARTIFACTS`:
   `breakdown.md` for decompose and implement, `architecture.md` for
   architect) under R's own directory.

Any other boundary the tool finds is inferred: the commit that first
added `breakdown.md` for decompose, and the first later commit whose
version checks a row for implement. A signal is observed only when every
boundary it reads is observed. There are exactly two labels. The tool
prints this rule in every report and writes it into every record.

## Rejected alternatives

- **Slug-equal and em dash (the protocol's literal form).** It finds 2
  observed decompose boundaries where 4 exist. It also demotes two runs
  whose commits name the stage and write its artifact, which is all the
  protocol's commit rule asks of a stage.
- **A third label, `loose`, for the scope-agnostic matches.** It splits a
  4-run sample three ways, and every downstream consumer would have to
  choose which label to trust. Anchoring to the changed artifact is the
  stronger evidence anyway: a subject alone can be typed by anyone, but a
  subject plus the artifact it names is the protocol's boundary commit.
- **Subject only, with no path check.** A `docs(x): decompose …` commit
  in a batch that only touches another run would count for the wrong run.

## Consequences

- A commit that names one stage but edits another stage's artifact is
  not observed for either.
- Because the scope is ignored, one `docs(<scope>): decompose` commit that
  writes two runs' breakdowns is observed for both. This is accepted: no
  tracked commit does it today.
- The inferred implement boundary (first ticked row) marks the start of
  Implement. The observed one (the protocol's implement commit) marks its
  end. On the 3 runs with an observed implement boundary, the work-item
  keys at the first tick equal the keys at the implement commit, so the
  two windows agree today. The aggregate still reports the populations
  separately, so a future gap shows up as a population difference and is
  not hidden in the combined figure.
- Changing this rule after a record is cited makes later records
  incomparable to it. A replacement ADR has to say whether earlier
  records are re-run under the new rule. Each record carries its rule
  sentence and a ref-tip digest, so a re-run can be checked against the
  original.
