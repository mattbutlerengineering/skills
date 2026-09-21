# Autorun brief — a broken taxonomy passes the gate

**Scale.** Maintenance run, feature-shaped:
`docs/fixes/a-broken-taxonomy-passes-the-gate/`.

**What.** Detector J (`gates.check_label_wiring`) computes
`label_sync.load_labels`'s problems and throws them away —
`taxonomy, _ = label_sync.load_labels(root)`. A stamped product repo
whose `.github/labels.json` is corrupt, is not a JSON array, has every
entry malformed, or names a label twice runs `make check` and is told
`gates: 0 problem(s)`.

**Why now.** J's own docstring says it exists because "a taxonomy that
loses a label passes every offline gate and fails in the dispatch plane,
at merge or dispatch time, which is the worst moment to find out". A
taxonomy that cannot be read at all reaches exactly that moment, and J
is the detector standing there. The asymmetry is what makes it bite:
in the factory repo the payload copy is manifest-pinned, so detector E
catches a hand-edit; the *installed* `.github/labels.json` in a stamped
repo is, by J's own docstring, "one of the files docs/setup.md and
factory_init.update both hand to the stamped repo as its own to
curate", so it carries no checksum and nothing else looks at it
offline.

**Why it is a convention violation and not a judgement call.**
`load_labels` has five other callers and every one of them forwards its
problems: `label_sync.sync`, `validator.lifecycle_labels`, and all three
`sweeps.py` call sites. `sweeps.py`'s module docstring states the rule
outright — "the `L:`-prefixed strings from label_sync.load_labels() are
forwarded as they arrive, since a broken taxonomy is that detector's
finding, not ours". J is the one caller that breaks it, and the only
one that runs offline.

**Re-entry.** `implement` — the change is one discarded return value, one
extraction that gives the "is there a taxonomy at all?" question a
single owner, and the tests that pinned the old behaviour.

**Release authorization.** None. Prepare and stop.

**Scope in.** `gates.py` (detector J and its selftest fixture),
`label_sync.py` (extract `taxonomy_path`), `tests/test_gates.py`,
`tests/test_label_sync.py`, and the payload mirrors plus
`factory/manifest.json`.

**Scope out.** Making `load_labels` return unprefixed problems so each
caller owns its own prefix. That is the repo's dominant seam pattern
(`cli.gh_read` returns bare suffixes; `label_sync` and `sweeps` each
prefix them), and `load_labels` is the outlier — but sweeps has already
weighed that question and written down "forwarded as they arrive" as its
answer. Re-litigating it would touch five call sites and two suites for
no behaviour change. Seeded instead.

**Scope out.** Wiring `label_sync` into `make check` or giving it a
Makefile target. It is a network detector by design and there is an
existing backlog seed for its missing target.

**Success criteria.**
1. A stamped repo with a corrupt, non-list, wholly-malformed, or
   duplicate-naming `.github/labels.json` fails `python3
   tools/factory/gates.py`, naming the file and what is wrong with it.
2. A tree with no taxonomy anywhere is still silent — an unstamped repo
   has nothing to be wrong about.
3. A taxonomy with one malformed entry among good ones still reports
   the wiring findings it reported before, and now also reports the
   malformed entry.
4. `make check` stays green on this repo, and the stamped-repo
   acceptance test still passes.
