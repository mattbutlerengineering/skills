---
name: review
description: Use when verified work needs a quality pass before shipping — examining the change for defects, design decay, and security issues — or when the user asks for a code review of the run's changes or says to give the change a quality check. Produces review.md. It is not for acting on reviewer comments left on an open PR — addressing that feedback, resolving threads, and readying a PR for merge is address-pr-review.
---

# Review

Examine the change as a skeptical reviewer before it ships: defects, design
decay, security. Draft-first: read the code, draft the findings, let the user
arbitrate severity.

## Process

1. Read `../../docs/pipeline-protocol.md` for run discovery, gating, and
   frontmatter conventions.

2. **Soft gate.** Predecessor artifact: `verification.md`. If missing, apply
   soft gating — but note that reviewing unverified work inverts the usual
   order, and say so in the artifact.

3. **Scope the diff.** The review covers what this run changed — the diff
   since the run began, not the whole repo.

4. **Review in three passes:**
   - **Correctness** — logic errors, unhandled failure modes, edge cases the
     tests missed. For each suspected bug, state the concrete failure
     scenario (inputs → wrong behavior); a bug you can't scenario-ize is a
     hunch, not a finding.
   - **Design** — does the code match `architecture.md`'s contracts and the
     codebase's existing patterns? Undocumented deviations are findings.
   - **Security** — inputs validated at boundaries, no secrets in code,
     injection surfaces parameterized, errors don't leak internals.

5. **Rank and verify.** Order findings by severity (critical / major /
   minor). Re-read the code for each before writing it down — a false
   finding costs more trust than it's worth.

6. **Write the artifact.** Fill `TEMPLATE.md` (in this skill's directory)
   into the run directory as `review.md` with protocol frontmatter. Record
   what was examined, findings, and the fix/defer decision per finding.

7. **Fix loop.** Critical findings are fixed before Ship (route to
   Implement for anything non-trivial, then re-verify). Majors are fixed or
   explicitly deferred by the user. Minors may be deferred freely.

8. **Hand off.** Next stage is Ship.

## Rules

- Findings target external behavior and maintainability — not style
  preferences the codebase itself doesn't hold.
- Every finding needs a failure scenario or a named decayed contract; "I'd
  have written it differently" is not a finding.
- Deferred findings get a reason logged — deferral is a decision, not a
  shrug.
