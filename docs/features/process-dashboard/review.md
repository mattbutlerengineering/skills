---
stage: review
run: feature:process-dashboard
date: 2026-08-14
---

# Review: Process dashboard v1

## Scope

The run's full diff — eleven squash-merged PRs (#266–#276,
WO-0019…WO-0029): `dashboard.py` (726 lines: gather, drift, output
join, metrics, rates, reorder, server), `dashboard.html` (367 lines:
pure render half + DOM shim), the `protocol.parse_backlog` line-number
extension (+ mirrored template and manifest), and
`tests/test_dashboard.py` (1161 lines). Three passes: correctness,
design (against `architecture.md`'s contracts), security.

## Findings

### Minor: a failed bind crashed serve with a traceback instead of a problem string

- Scenario: `serve --port 7719` while another instance holds the port
  (the everyday double-launch), or `--port 70000` → raw
  `OSError`/`OverflowError` traceback, breaking the repo's
  problem-string contract at the CLI boundary. Reproduced live before
  fixing.
- Decision: **fixed** in this stage — bind errors now return
  `dashboard: cannot bind 127.0.0.1:<port>: <err>` (two new pinning
  tests; suite at 1191).

### Minor: backlog Save has a read-check-write race

- Scenario: two Saves posted in the same instant both read the file,
  both pass the hash check, and the second write silently discards the
  first's order. The hash token guards the *editor-vs-console* race
  (verified: stale replay → 409) but not two concurrent POSTs — there
  is no lock between read and write.
- Decision: deferred — the console is a single-operator localhost tool
  by design (no auth story, 127.0.0.1 bind); the racing writer is the
  operator racing themself within milliseconds. An in-process lock is
  the fix if multi-operator use ever arrives.

### Minor: run entries carry `stage` only, not the data model's `stage` + `next`

- Scenario: `architecture.md`'s data model lists runs as
  `{"ref", "dir", "stage", "next"}`; the payload emits `stage` alone —
  protocol orientation yields one value (the first incomplete stage),
  which is both "where it stands" and "what's next", so a second key
  would duplicate it. Decayed contract on paper, not in behavior: the
  UX ("run ▸ next step") renders correctly from the one value.
- Decision: deferred as an accepted deviation, recorded here — the
  data model over-specified; if a distinct "current vs next" ever
  exists (it doesn't in the orientation table), the key can be added
  additively.

### Minor: the POST shim trusts Content-Length

- Scenario: a hand-crafted local request with a huge or non-numeric
  `Content-Length` makes the handler allocate that much or throw in
  the shim (connection drops with a stderr traceback; the server
  itself survives — per-request thread). Unreachable off-box by the
  localhost bind.
- Decision: deferred — the only client is the served page on the same
  machine; hardening the shim buys nothing the bind doesn't already
  guarantee. Revisit with any future non-localhost exposure.

## Passes with no findings

- **Security** — no secrets; all boundaries validated (config shape,
  POST body shape, index bounds, port parse); every gh/git invocation
  is argv-list through the `cli.py` runner seam (no shell); the page
  escapes every payload-sourced string before interpolation (pinned:
  the `<b>`-in-title and `<i>`-in-title node tests) and builds links
  only from escaped attributes; error strings name local paths only,
  shown to the local operator.
- **Design** — beyond the `next`-key deviation above: seam usage
  matches the architecture (protocol/knowledge_plane/cost_ledger/
  gate_digest/factory_config/cli own their domains; dashboard stays a
  renderer), problem-string and fail-loud-render-on conventions hold
  throughout, ADR-0032's row-authoritative rule is respected (mirror
  labels give lifecycle; rows give the drift cross-check), and the
  mirrored `protocol.py` edit shipped with its manifest/payload
  regeneration (detector E green).

## Verdict

Ready to ship. One finding fixed in-stage (bind errors), three minors
deferred with reasons; correctness beyond the bind path came back
clean against the verification evidence, and security found nothing.
