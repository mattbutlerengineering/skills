# The tools/factory restructure is blocked by nine files, not one

- Status: provisional
- Date: 2026-08-22

Amends ADR-0046, which deferred the `tools/factory/` restructure on the
grounds that one file has dual membership: "The move is blocked by one
file. `protocol.py` belongs to both root families at once."

That was not true when it was written. Measured at 622e2bf, the commit
that added it, **six** mirrored modules were already imported by
root-only tools, and `cli.py` led them with five such importers to
`protocol.py`'s two. Today there are nine:

| mirrored module | root-only tools that import it |
|---|---|
| `cli.py` | charter_replay, dashboard, factory_init, lint, sweeps, trigger_eval |
| `protocol.py` | dashboard, lint, trigger_eval |
| `factory_config.py` | dashboard, factory_init |
| `knowledge_plane.py` | dashboard, sweeps |
| `cost_ledger.py` | dashboard |
| `cost_report.py` | dashboard |
| `human_gates.py` | dashboard |
| `gates.py` | factory_init |
| `label_sync.py` | sweeps |

Every cross-module import at the root is a bare sibling import, so a file
both families need must be *reachable from both directories* — which,
without a package or a path shim, means present in both.

The blocker is therefore a pattern, not a file. Two primitives are
genuinely shared by both families — `protocol.read_frontmatter` (the one
parser, ADR-0021) and `cli.report` (the problem-string epilogue,
ADR-0051) — and three tools have an arguable family: `sweeps.py` and
`dashboard.py` are factory-facing but unmirrored, and `factory_init.py`
is the stamper and can never be mirrored.

## Decision

**The deferral stands; the diagnosis is replaced.** ADR-0046's judgment —
keep the flat root, do not attempt the restructure yet — is unchanged and
still correct. What it names as the blocker is not.

A future attempt must address all nine: by dual-homing the shared
primitives through the mirror mechanism that already exists for exactly
this case, by reclassifying the root-only tools that import them, or
both. **Resolving `protocol.py` alone does not unblock the move and must
not be described as doing so.**

## Consequences

- A review citing "blocked by one file" is citing a stale premise. This
  is the second correction of its kind this week — ADR-0058 replaced
  ADR-0039's checkbox-regex roster the same way — and both were found by
  re-measuring the tree rather than re-reading the record.
- The `protocol.py` split remains available on its own merits: the
  payload ships 292 lines of which the two factory callers reach 34, so
  258 lines of pipeline taxonomy are stamped into every product repo and
  never executed there. That is a payload-size change, not a restructure
  enabler.
- That split also does not clear the bar ADR-0046 set for it ("multiple
  callers plus observed divergence"): there is one parser and no copies,
  so no divergence has been observed. It needs a different justification
  than the one ADR-0046 anticipated, or it needs to not happen.
- Not decided here: whether a detector or test should pin the
  dual-membership set, so the count cannot drift silently a third time.
- Status is provisional: the deferral it preserves is the owner's call,
  and the replacement diagnosis should be confirmed rather than inherited.
