# Audit playbook

What to look for, category by category. Read the category you are
sweeping plus **Finding format** at the bottom — a subagent gets the same
two sections and nothing else, because it does not inherit the skill.

Categories 1–9 follow the taxonomy in shadcn's `improve` skill (MIT).
Categories 10 and 11 are this repo's, and they exist because the two
worst defects found here were invisible to the other nine: a mechanism
that could never fire, and a rule satisfiable without the property it
claimed to enforce. Both passed every gate.

A finding is only a finding with evidence, and evidence is a location:
`path/file.py:142 issues one query per row inside the loop`, never
"probably has N+1s somewhere".

---

## 1. Correctness

- Swallowed errors: bare `except`/empty catch on a path that matters,
  a logged-and-continued failure where the caller needed the failure.
- Async hazards: unawaited work, cancellation and cleanup never wired,
  shared state mutated from two places.
- Null and boundary flows: assertions on values that can be absent,
  empty-collection handling, off-by-one, timezone and locale assumptions.
- State machines: representable impossible states, an enum branch that
  silently no-ops, a transition with no writer (see category 10).
- Concurrency: check-then-act on a shared resource, multi-write
  sequences with no transaction, retries that are not idempotent.
- Resource leaks: handles, connections, and subscriptions never closed.

## 2. Security

Report what the code evidences. Standard platform conventions —
honoring proxy env vars, reading a well-known credentials file — are
intentional behavior; flag them only when the implementation adds risk
beyond the convention.

**Never copy a secret value anywhere.** Cite `file:line` and the
credential type ("live API key at `config.py:12`"), and the fix always
includes rotation: a committed secret is burned even after deletion.

- Secrets in source, in committed env files, in logs, in event history.
- Injection: string-built SQL or shell, HTML sunk from user data,
  `eval` on dynamic input, path traversal on user-supplied names.
- AuthN/Z: an endpoint with no auth check, authorization enforced only
  client-side, object access by id with no ownership check.
- Input validation: request bodies trusted at the boundary, uploads
  unchecked for type/size/path, mass assignment.
- Exposure: PII in logs, stack traces returned to clients.
- Dependencies: the ecosystem's audit command, read-only. Report
  exploitable criticals, not the noise floor.

## 3. Performance

Algorithmic and architectural wins, not micro-optimizations.

- A query or fetch per item inside a loop; missing batching.
- Repeated linear scans where a keyed lookup belongs.
- The same expensive computation repeated per request with no cache.
- Over-fetching, unbounded lists with no pagination.
- Synchronous work that belongs off the request path.
- Build and CI: missing caching, redundant steps, suites that could
  parallelize.

## 4. Test coverage

The goal is never a percentage — it is *which untested code is
dangerous*.

- Map the critical paths (money, auth, data mutation, the thing the
  repo exists for) and name which have zero or trivial coverage.
- High churn plus no tests is the top refactor risk: those want
  characterization tests before anything else touches them.
- Test quality: assertions that assert nothing, mocks deep enough that
  the test exercises the mock, order-dependent or clock-dependent tests.
- Is there a one-command way to know the code works? If not, that is
  finding #1 and it blocks every risky plan behind it.

## 5. Tech debt and architecture

- The same logic implemented in three places, and the copies have
  drifted apart (the drift is the finding, not the duplication).
- Layering violations, cycles, a `utils` module with high fan-in.
- Dead code: unreferenced modules, a flag fully rolled out but still
  branching, manifest dependencies nothing imports.
- Modules an order of magnitude larger than the repo median.
- Three ways of doing the same thing; name which one won.
- Premature abstraction with one implementation, or a missing one where
  every change touches N files in lockstep.

## 6. Dependencies and migrations

Major-version lag with a real cost to staying behind (EOL, security-fix
cutoff, ecosystem incompatibility) — not every minor bump. Deprecated
APIs with announced removal dates. Abandoned packages on critical paths.
Two libraries solving one problem. For each candidate, estimate blast
radius in files touched: that is what decides whether to recommend it.

## 7. DX and tooling

Missing or broken typecheck, lint, formatter, hooks. Feedback loops
measured in minutes. Setup steps in the README that are wrong. Undocumented
required environment. Unstructured logs on a service, debugging that
requires editing code. A repo where agents will do the work and there is
no `CLAUDE.md`/`AGENTS.md` is a high-leverage gap.

## 8. Docs

Lowest default priority; flag only where absence has a concrete cost. A
published API with no reference. A contested decision nobody can
reconstruct. **Stale docs that are actively wrong** — worse than missing,
and category 11 is where they usually turn out to belong.

## 9. Direction

Not what is broken — what this codebase wants to become. **Grounding
rule**: every suggestion cites evidence from this repo. A suggestion that
would apply to any project in the category is noise.

- Unfinished intent: TODO clusters around one theme, flags never rolled
  out, stubbed modules, abandoned mid-feature work in the history.
- Stated but undelivered: a README promise with no code behind it, a
  flag that is a no-op.
- Surface asymmetries: export without import, create without bulk
  create, CRUD minus one, a public API internal code hand-rolled around.
- The adjacent possible: what the existing architecture makes
  disproportionately cheap — one interface away, one route file away.
- Friction worth absorbing: what users evidently do by hand around this.

Direction findings keep the standard format with two changes: **impact**
is who wants this and why now, and **confidence** measures how grounded
the evidence is, never whether it is the right call. Strategy belongs to
the maintainer. Effort estimates here are coarse; say so.

## 10. Inert mechanisms

Code that exists, gates that stay green, and a mechanism that
structurally cannot fire. Nothing in categories 1–9 sees this, because
nothing is broken — the wiring was never finished, and every check
agrees.

Sweep it by naming, for each mechanism, its **writer** and its
**trigger**, then checking both can be reached:

- A state or label with no writer. Which code path sets it? If the
  answer is "a human, by hand", is that recorded as the design, or is it
  a hole? (Both happen; only one is a finding.)
- A circuit breaker whose only trigger is the condition it exists to
  prevent — it fires exactly once, after the damage.
- A counter, budget, or ledger with a reader and no writer on the
  success path. Read the accumulated data: a total that never moves is
  the fastest confirmation there is.
- A cleanup or release leg that only runs on the path that already
  succeeded, so the failure it exists for leaks forever.
- A queue claim with no matching release: whatever takes an item out
  owes it a terminal state.
- A workflow step behind a condition that the event shape can never
  satisfy.

Reproduction here is usually a trace, not a command: enumerate every
call site of the writer and show the set is empty or unreachable.

## 11. Unpinned facts and hollow rules

The defect class one level under stale docs: **a statement with nothing
that fails when it stops being true.**

- A documented fact restated from an executable source — a count, a
  list, a command, an order — with no check comparing the two. Ask: if
  someone changed the source right now, what goes red? If the answer is
  "nothing, until a reader notices", it is unpinned.
- A rule satisfiable without the property it claims to enforce. Ask the
  adversarial question: *what is the cheapest way to make this check
  pass while the thing it protects is false?* If a cheap way exists, the
  check is decorative.
- A test whose fixture guarantees the outcome regardless of the code
  under test.
- A gate whose condition is met by an unrelated, always-present input —
  the value that satisfies it is not the value it meant to measure.
- Two files that must agree, kept in agreement by discipline alone.

The fix is rarely "update the doc". It is to derive the statement from
its source, or add the check that makes divergence fail — and the
finding should say which.

---

## Finding format

Every finding, every category, comes back in this shape:

```markdown
### [CATEGORY-NN] Short imperative title

- **Evidence**: `path/file.py:123` — what is there, one sentence.
  (2–5 strongest locations; note "and ~N similar sites" if widespread.)
- **Reproduction**: the observation that confirms it — the command and
  its failing output, the assertion that does not hold, the value that
  is wrong. `unreproduced` is a legal value and demotes the finding to a
  suspicion; a plausible argument is not a reproduction.
- **Impact**: what is being paid for this, concretely. "Every list
  render issues 1+N queries", not "suboptimal".
- **Effort**: S (hours) / M (a day) / L (multi-day), for the fix
  including tests.
- **Risk**: what the fix could break — LOW/MED/HIGH plus one line why.
- **Keeps it fixed**: the check that fails if this regresses — an
  existing one, one that ships with the fix, or `nothing` (which is
  itself part of the finding's cost).
- **Fix sketch**: 1–3 sentences. Enough to judge effort honestly, not
  the implementation.
```

## Ordering

Rank by leverage — impact ÷ effort, discounted by fix-risk. Tiebreakers,
in order:

1. Anything that unblocks other findings floats up: a verification
   baseline, characterization tests, a check that would have caught the
   rest.
2. Reproduced beats argued. A confirmed medium outranks a suspected
   large every time.
3. Security findings float above equivalent-leverage findings.
4. Prefer findings whose fix has a clean verification story.
5. "Not worth doing" is a verdict, not an omission. Record it with one
   line of reasoning.
