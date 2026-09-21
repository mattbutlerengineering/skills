# Autorun brief — maintenance:a-timestamp-the-digest-cannot-parse

Collected once, 2026-08-31, at the start of an `/idea-to-prod:autorun`
invocation. This is the brief, not an artifact: it never counts toward
orientation or active-run discovery.

## How this run was chosen

The user selected backlog **seed 25** (`toolsmith-mine` broken in every
stamped repo). Before acting I verified it and found it **stale** — the
`sanitize` import moved from the unmirrored `sweeps` to the mirrored
`knowledge_plane` (`rejection_mining.py:43`), and a freshly stamped repo
runs `tools/factory/rejection_mining.py mine` to a `gh`-auth problem
string, not a `ModuleNotFoundError`. My own second choice, **seed 28**
(validator reds non-WO PRs), is also stale: `Makefile:40` already passes
`--uncited skip`, and merged PRs #314/#316/#318 each show
`merged-label: pass skipping`.

**Seed 26** was on the same menu shown to the user, is verified live
(repro below), and is what this run drives. The substitution was reported
to the user rather than made silently.

## The defect (seed 26, `docs/backlog.md:26`)

> `human_gates.waited_seconds` propagates ValueError on a completed stay
> whose timestamp is truthy but not ISO-8601 — `label_events` admits an
> event on truthiness alone and `gate_digest.run_daily` catches only
> CLI_FAILURES, so the daily digest would die on a traceback rather than
> a problem string; behavior relocated from gate_digest, not introduced,
> and hardening `_parse_ts` is a behavior change to a shipped tool that
> wants its own evidence (from: maintenance:deepening-tool-seams)

### Repro, run on `main` at 622e7c0

```
$ python3 - <<'PY'
import human_gates as hg
timeline = [
    {"event": "labeled",   "label": {"name": "wo:draft"},
     "created_at": "2026-08-30T10:00:00Z"},
    {"event": "labeled",   "label": {"name": "wo:prd-approved"},
     "created_at": "2026-08-30T11:00:00Z"},
    {"event": "unlabeled", "label": {"name": "wo:draft"},
     "created_at": "not-a-timestamp"},
]
events = hg.label_events(timeline)
print("completed_stays:", hg.completed_stays(events, hg.GATES[0]))
for fn in (hg.gate_passages, hg.gate_rejections):
    try:
        print(fn.__name__, "->", fn(events))
    except Exception as err:
        print(f"--- {fn.__name__} raised: {type(err).__name__}: {err}")
PY
completed_stays: [('2026-08-30T10:00:00Z', 'not-a-timestamp', True)]
--- gate_passages raised: ValueError: Invalid isoformat string: 'not-a-timestamp'
gate_rejections -> []
```

Two facts the seed does not state, both from that run:

1. **The partition is asymmetric.** `gate_rejections` never calls
   `waited_seconds`, so the miner survives the same event list that kills
   the digest. ADR-0056's stay partition is meant to be two views of one
   walk; one view is durable and the other is not.
2. **`completed_stays` itself is clean.** It admits the malformed stay and
   returns it. The raise is entirely in `waited_seconds`.

### Blast radius

- `gate_digest.py:124` — `_capture_latency`, via `gate_passages`.
- `gate_digest.py:149` — `_queues`, via `waited_seconds` directly.
- Neither is inside a `try`. `run_daily` guards only `GH_FAILURES`
  (`= cli.CLI_FAILURES`) at `:166/:172/:178/:183`; `main` guards nothing.
  So the traceback escapes `sys.exit(main(sys.argv[1:]))` — the daily
  workflow goes red with a Python traceback instead of a `gd:` problem
  string, which is the exact contract ADR-0039 states a factory CLI never
  breaks.
- **Mirrored.** Both `human_gates.py` and `gate_digest.py` ship under
  `factory/templates/tools/factory/`, so any fix needs
  `python3 factory_init.py update-manifest` and the manifest committed
  with the change (detector E gates manifest↔payload).

### The open design question this run must settle

`label_events`' docstring states the delegation deliberately: *"an
unusable timeline is the fetcher's problem, never this walk's."* So the
run may not simply harden `_parse_ts` and call it done — it has to say
where a malformed timestamp is caught and what the caller then reports.
The plausible answers (a malformed stay is dropped; a malformed stay
becomes a `gd:` problem string; the fetcher validates before the walk)
have materially different behavior, and the seed itself flags this as
"a behavior change to a shipped tool that wants its own evidence."

That is a question with **no skill-supplied default**, so per the autorun
rules the stage that reaches it stops and surfaces rather than guessing.
It is also the reason `re-entry:` may reasonably be `architect` rather
than `implement` — that call belongs to the capture stage, which decides
re-entry depth and records it in `defect.md` frontmatter.

## Run parameters

- **Run scale:** maintenance (fix run), slug
  `a-timestamp-the-digest-cannot-parse`, directory
  `docs/fixes/a-timestamp-the-digest-cannot-parse/`.
- **Entry stage:** capture (`defect.md`). Maintenance runs do not pass
  through Idea/PRD/UX, so this brief carries no Idea-stage inputs — the
  defect above is the whole input.
- **Intake:** backlog seed 26. There is no tracker issue. Capture claims
  the seed in place by appending
  `(claimed: maintenance:a-timestamp-the-digest-cannot-parse)` to
  `docs/backlog.md:26` — appended, never rewritten.
- **In scope:** `human_gates.py` (`_parse_ts`/`waited_seconds` and, if the
  design lands there, `label_events`), `gate_digest.py`'s two call sites,
  their payload twins, `factory/manifest.json`, and regression tests in
  `tests/test_human_gates.py` (and `tests/test_gate_digest.py` if the
  caller changes).
- **Out of scope:** the rest of ADR-0056's partition, `rejection_mining`
  behavior, the dashboard, and every other seed on `docs/backlog.md`. No
  drive-by hardening of unrelated `fromisoformat` calls — flag them as
  seeds instead.
- **Success criteria:** a malformed-but-truthy timestamp anywhere in a
  gate timeline produces a `gd:`-prefixed problem string and a nonzero
  exit, never a traceback; the repro above is a passing regression test;
  the miner/digest asymmetry is either removed or documented as
  intentional; the payload twins and manifest match root.
- **Constraints:** stdlib only; problem-string contract (validators
  return label-prefixed strings, callers print and exit nonzero, never
  raise); ADR-0056 is the authority on the stay partition — supersede
  with a new ADR, never rewrite; ADR-0039's "never a traceback" CLI
  contract applies.
- **Already decided:** nothing beyond the above. In particular the
  catch-site question is open on purpose.

## Standing authorizations (carried forward from this session)

- **Release authorization: prepare-and-stop.** Ship runs the pre-flight
  checks and writes `release.md` recording readiness and the exact steps,
  and executes **no** externally visible release action — no deploy,
  publish, tag, or merge. Merging an agent-authored PR needs human
  approval separately; `/goal` is not that approval.
- **Tracker: no tracker interaction.** No issue is created, edited, or
  closed by this run. The backlog seed claim is the only write outside
  the run directory, and it is an append.
- **User-facing surface:** none. This is a CLI/tooling fix, so no `ux:`
  decision arises.

## Verification commands (the real ones — quote output, never assert)

```
python3 -m unittest discover tests
python3 lint.py
python3 gates.py && python3 gates.py --selftest
```

Baseline on `main` at 622e7c0 is **1344 tests**. `python3 one_owner.py`
is a non-gate pre-pass carrying 9 pre-existing problems on `main`; a fix
run neither needs to clear them nor may add to them.

## Assumptions logged

None at brief time. Every gap the stages hit gets logged in that stage's
artifact frontmatter under `assumptions:`, or stops and surfaces when the
stage skill supplies no default.
