# Autorun brief — a config the gate cannot read

## Provenance

No user-supplied brief exists for this run. It was authored from this
session's own investigation under a standing autorun instruction. The
candidate came from reading the uncontended modules for gaps between a
module's stated convention and its code. Neither `factory_config.py`
nor `label_sync.py` is touched by any open pull request.

## What and why

`factory_config.load` and `label_sync.load_labels` both catch
`json.JSONDecodeError` — the intent to degrade on a malformed file is
explicit — but both read the file with `read_text(encoding="utf-8")`
first, and a decode failure raises `UnicodeDecodeError`, which is not a
`JSONDecodeError` and is not caught. Neither catches `OSError` either,
though the peer seam loader `cost_ledger.load` does.

`factory_config`'s stated convention is "functions return (value,
problems) with config:-prefixed problem strings". A config file saved
in a non-UTF-8 encoding breaks that convention for all five callers of
the seam. Detector F (`gates.check_config_shape`) has the same hole in
its own independent read of the same file, so the gate over a malformed
config crashes on one class of malformed config — but that half lives
in `gates.py`, which PR #320 claims, and is out of scope here. An
earlier draft of this brief said detector F read through the seam; it
does not, and the claim was corrected once a test proved otherwise.

## Scale and re-entry

Maintenance run, slug `a-config-the-gate-cannot-read`. Re-entry is
`implement`: the convention already exists and the peer loader already
implements it; only these two are inconsistent with it.

## Scope

In: make both loaders return a problem string rather than raise when
the file cannot be read or decoded, matching `cost_ledger.load`'s
"cannot read" phrasing under each module's own prefix.

Out: the other unguarded `read_text` sites in this repo. Many are
deliberate and none was demonstrated to break a stated convention;
sweeping them would be a refactor, not this defect. Out: any change to
`gates.py`, which PR #320 claims — the fix is in the loader it calls,
not in the caller.

## Constraints

Stdlib only. Both files are in `factory_init.MIRRORS`, so
`update-manifest` must run and the payload copies ship the fix.

## Release authorization

None. Ship prepares and stops.
