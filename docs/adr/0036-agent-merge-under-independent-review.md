# Agent merges permitted under independent review

- Status: accepted
- Date: 2026-07-12

Amends ADR-0033. The third human gate — **PR merge** — was a physical
control: branch protection requiring code-owner review, so a human pressed
merge on every PR. ADR-0033 anticipated relaxing it only by
class-graduation on ≥ 20-PR evidence, and reserved changing a gate as a
human-only decision.

The repository owner has made that decision. The reason is evidence, not
impatience: the mechanism that actually catches bad artifacts before merge
is the **independent (non-authoring) review**, and it demonstrably works —
in the WO-0011 / #147 run an independent adversarial reviewer, dispatched
against a green PR, found two real evidence-honesty bypasses (blockquote
and ordered-list verdicts) that CI and the authoring agent had missed. The
human press-of-the-button added latency without adding that signal.

## Decision

The merge gate becomes a **review gate the reviewer may be an agent**, not
a human-hands-on-merge gate. An agent may merge a PR when **all** hold:

1. **Required status checks pass** — the full detector suite and tests, on
   the merge-result commit. Never bypassed (unchanged from ADR-0033).
2. **An independent, non-authoring review passed** — the reviewer (human
   or agent) is not the PR's author, re-executes the PR's stated
   verification rather than reading it (per the reviewer charter), and its
   pass is recorded on the PR.
3. **The change is not itself a gate change.** PRD approval and
   blueprint/ADR approval (gates 1 and 2) remain human code-owner gates,
   and any PR touching `docs/adr/**`, a run's `prd.md`,
   `architecture.md`, or `docs/design/**` — including this class of
   governance change — still requires a human code-owner merge. An agent
   cannot widen its own authority: the ADR that grants agent-merge is
   itself human-merged.

The human retains an **override and a post-merge audit**: any merge is
revertible, gate-latency and defect-escape stay first-class weekly metrics
(ADR-0033), and a defect escape attributed to agent-merge narrows or
revokes it — the same auto-revoke discipline the class-graduation path
uses.

## Consequences

- Throughput is no longer bounded by a human at every merge; it is bounded
  by review quality, which is the thing that actually protects main.
- The independent-review requirement is now load-bearing, so its integrity
  (the non-authoring guard, the reviewer re-executing not reading) is a
  security property, not a nicety — see #144 on verifying the reviewer's
  identity path against real GitHub before it is relied on at scale.
- Gates 1 and 2, and gate-structure changes, stay human. The blast radius
  of a bad agent-merge is one revertible PR on main; the blast radius of a
  bad PRD or blueprint is every work order beneath it, which is why those
  stay hands-on.
