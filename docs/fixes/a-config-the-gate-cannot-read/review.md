---
stage: review
run: maintenance:a-config-the-gate-cannot-read
date: 2026-08-27
assumptions: []
---

# Review: a config the gate cannot read

Scope: `factory_config.py` (+11/-3), `label_sync.py` (+7/-2), their two
payload mirrors, `factory/manifest.json` (regenerated), and two test
files (+22).

Written by the same agent that wrote the change, so ADR-0036 clause 2 is
unsatisfied.

## Correctness

**Major, open, not fixed here — detector F holds its own copy of this
hole.** `gates.check_config_shape` reads `factory.json` at
`gates.py:878` through its own `json.loads(path.read_text(...))`, not
through the seam, and still raises `UnicodeDecodeError` on the input
this run fixed everywhere else. The gate that exists to diagnose a
malformed config therefore still crashes on one class of malformed
config.

Not fixed because `gates.py` is claimed by PR #320 and a fix from this
branch would collide with it. Worth its own run once #320 lands, and it
carries a second question that run should answer: whether detector F's
independent read should keep existing at all. Its docstring defends the
divergence on *report order* — it walks every candidate payload-first
where the seam returns the first existing installed-first — which
justifies a different traversal, not a duplicated decode-and-parse.

**Checked, not a finding — the JSON path is untouched.** Splitting the
decode out did not change the message, the prefix, or the return shape
for malformed JSON; criterion 3 quotes it verbatim.

**Checked, not a finding — `OSError` is now caught alongside the decode
error.** That is slightly wider than the demonstrated defect, and it is
deliberate: it matches `cost_ledger.load`, the peer seam loader, whose
phrasing the new messages also copy. It is one clause, not a new code
path.

## Design

The fix follows the existing catch rather than inventing a policy: the
loaders already meant to report a malformed file, and a file that will
not decode is malformed a step earlier. `label_sync` points at
`factory_config` for the reasoning instead of restating it, so the two
copies of the pattern do not become two statements of it.

## Security

No new input surface; the change only converts a crash into a reported
problem. No secrets, no subprocess, no network. Reading a file the
process was already going to read.

## Verdict

No critical findings. One major recorded as open with its blocker named
and a follow-up question attached. The blocking condition on shipping is
ADR-0036 clause 2.
