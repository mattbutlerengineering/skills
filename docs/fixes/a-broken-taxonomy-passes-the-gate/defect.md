---
stage: capture
run: maintenance:a-broken-taxonomy-passes-the-gate
date: 2026-08-30
re-entry: implement
assumptions:
  - Forwarding label_sync's problem strings verbatim, letter prefix and
    all, is the right shape rather than restamping them with J's own
    letter. sweeps.py faced the identical question at the identical
    seam and wrote its answer into its module docstring; a second
    caller answering it the other way would put the taxonomy-shape
    message text under two owners.
  - Silence belongs to an absent taxonomy, not to an unreadable one.
    J's docstring already scopes its silence that way in words, saying
    an unstamped repo has nothing to be wrong about, so the change
    makes the code say what the prose already says.
---

# A broken taxonomy passes the gate

## What is wrong

`gates.check_label_wiring` — detector J — ends like this:

```python
    taxonomy, _ = label_sync.load_labels(root)
    if not taxonomy:
        return []
```

`load_labels` returns `(labels, problems)`. The problems say whether the
taxonomy file is valid JSON, whether it is a non-empty array, which
entries lack required fields, and which names are duplicated. J computes
all of that and discards it.

The consequence lands in a stamped product repo, and only there. In this
repo the payload copy `factory/templates/.github/labels.json` is
manifest-pinned, so a hand-edit is detector E's finding. The *installed*
`.github/labels.json` a stamped repo runs on is — in J's own words —
"one of the files docs/setup.md and factory_init.update both hand to
the stamped repo as its own to curate". Curated means no checksum. J is
the only offline detector that reads it, and J says nothing.

## Reproduction

`scratchpad/repro_taxonomy.py` stamps a real product repo with
`factory_init.stamp`, writes each broken taxonomy into its curated
`.github/labels.json`, and runs the stamped repo's own gates:

```
stamp: clean
taxonomy                   load_labels problems                         detector J   offline gates
(the stamped taxonomy)     -                                            0 problem(s) gates: 0 problem(s)
corrupt JSON               L: .github/labels.json is not valid JSON: .. 0 problem(s) gates: 0 problem(s)
not a list                 L: .github/labels.json must be a non-empty.. 0 problem(s) gates: 0 problem(s)
empty array                L: .github/labels.json must be a non-empty.. 0 problem(s) gates: 0 problem(s)
every entry malformed      L: .github/labels.json[0] entry lacks colo.. 0 problem(s) gates: 0 problem(s)
duplicate label name       L: .github/labels.json[28] duplicate label.. 0 problem(s) gates: 0 problem(s)
```

Five broken taxonomies. `load_labels` names every one of them. The gate
that reads it reports none of them, and `make check` in that repo is
green.

The duplicate-name row is the sharpest: the taxonomy still carries all
28 labels, so J's wiring check is genuinely satisfied. Nothing offline
has any objection at all, and the repo finds out when `label_sync`
runs against GitHub.

## Why this is J's finding and not a design choice

`load_labels` has six callers. Five forward its problems:

| caller | what it does with `problems` |
|---|---|
| `label_sync.sync` | `if problems: return problems` |
| `validator.lifecycle_labels` | returns them to its caller |
| `sweeps.py:283` | `if problems: return problems` |
| `sweeps.py:317` | `if problems: return [], problems` |
| `sweeps.py:412` | `if problems: return [], problems` |
| `gates.check_label_wiring:848` | `taxonomy, _ =` — discards |

`sweeps.py`'s module docstring writes the rule down:

```
Conventions match label_sync.py/gates.py: functions return problem strings
(`sweeps:`-prefixed for this module's own; the `L:`-prefixed strings from
label_sync.load_labels() are forwarded as they arrive, since a broken taxonomy
is that detector's finding, not ours), the CLI prints them and exits nonzero.
```

"Forwarded as they arrive, since a broken taxonomy is that detector's
finding, not ours." Detector J is the one caller that does not, and the
only caller that runs offline — which is to say, the only one that could
have caught the problem before the dispatch plane.

## Why the existing test did not catch it

`tests/test_gates.py` pins the behaviour on purpose:

```python
    def test_an_unusable_taxonomy_is_silent_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("Makefile", self.MAKEFILE)
            for text in ("[]", "{not json", '[{"name": "wo:merged"}]'):
                tree.write(".github/labels.json", text)
                self.assertEqual(gates.check_label_wiring(tree.root), [],
                                 f"unusable taxonomy {text!r}")
```

The name carries the defect. "Not a traceback" is the real requirement —
a detector that raises on a malformed input takes the whole gate down
with it. "Is silent" is a second property that got bundled into the same
sentence and the same assertion, and it does not follow from the first.
J's docstring scopes its silence narrowly and correctly — "Silent when
there is no taxonomy to check — an unstamped repo has nothing to be
wrong about" — and a corrupt file is not the absence of a file.

## A second, minor finding in the same class

`TestLabelWiring`'s docstring opens:

```
    """Detector J. The tools and the Makefile name 15 labels between them
```

They name **13**. The 15 is a real quantity mislabelled: 13 distinct
labels declared at 15 sites, because `wo:merged` and `wo:needs-review`
are each named twice (a Makefile target and a `human_gates` entry).
Derived from the shipped tree:

```
$ python3 -c "import pathlib, gates; print(len(gates.declared_labels(pathlib.Path('.'))))"
13
```

Minor, and fixed here because it is the docstring of the class this run
rewrites — but it is the same shape as the last three runs' findings: a
hand-typed count in prose that nothing checks.

## Fix

1. Extract `label_sync.taxonomy_path(root)` — the `next(...)` walk over
   `artifact_paths` that `load_labels` already performs — so that "is
   there a taxonomy at all?" has one owner. J asks it instead of
   re-walking the candidates, which is the thing J's docstring already
   refuses to do ("Resolution of WHERE the taxonomy lives stays
   label_sync's, so the gate and the sync tool cannot read different
   files").
2. Detector J forwards `load_labels`'s problems, verbatim, and keeps its
   silence for the absent-taxonomy case only.
3. Split the pinning test into the two properties it was conflating, and
   add the duplicate-name and non-list cases it never had.
4. Plant the defect in the gates selftest fixture, where every other
   detector's is planted.
