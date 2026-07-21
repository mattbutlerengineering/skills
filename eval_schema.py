"""The evals' schema knowledge, in one place.

evals/routing.json holds routing cases ({id, kind, expected, query});
this module owns the kind vocabulary, the case shape, the coverage
policy, and load-plus-validate (ADR-0022). evals/output/<slug>.json
holds output-eval records; this module owns their required field set
(issue #25). evals/results/ is append-only; this module owns its naming
grammar — dated stems with -N collision suffixes — for every results
kind (issue #26, ADR-0024), including the factory's charter-regression
replays. The structural lint, the trigger-eval runner, and the charter
replay are thin callers. Deliberately separate from protocol.py: this
is eval knowledge, not pipeline-protocol knowledge.
"""
import json
import re

KINDS = ("direct", "situational", "near-miss", "distractor", "router")

# Harnesses a trigger run can drive (ADR-0027, ADR-0031). claude is the
# primary harness and stays unmarked in results stems — every snapshot
# recorded before harness identity existed is a claude run — so only the
# second harness carries its token in the grammar below.
HARNESSES = ("claude", "omp")
_MARKED_HARNESSES = tuple(h for h in HARNESSES if h != "claude")

# The append-only results naming grammar as it appears in LEDGER evidence
# links: trigger[-<harness>]-<date>[-N].json files,
# output/<slug>-<date>[-N]/grading.json, N counting up from 2
# (results_path below is the generator).
_SUFFIX = r"(?:-(?:[2-9]|[1-9]\d+))?"
_HARNESS = rf"(?:-(?:{'|'.join(_MARKED_HARNESSES)}))?"
_RESULTS_LINK = re.compile(
    r"^evals/results/(?:"
    rf"trigger{_HARNESS}-\d{{4}}-\d{{2}}-\d{{2}}{_SUFFIX}\.json"
    rf"|output/[a-z0-9-]+-\d{{4}}-\d{{2}}-\d{{2}}{_SUFFIX}/grading\.json)$")


def valid_results_link(target):
    """True when a LEDGER evidence link target follows the results grammar."""
    return bool(_RESULTS_LINK.match(target))


# Every field an output-eval record must carry (docs/output-evals.md
# names this module as the shape's owner).
OUTPUT_FIELDS = ("id", "prompt", "run_fixture", "run_scale",
                 "expected_output", "expectations")


def results_path(results_dir, kind, date, slug=None, harness=None):
    """Next free results path per the append-only naming grammar (#26).

    trigger -> <results_dir>/trigger[-<harness>]-<date>[-N].json (the
               recorded file; the primary claude harness stays unmarked,
               a second harness carries its token — ADR-0031)
    output  -> <results_dir>/output/<slug>-<date>[-N] (the grading dir)
    charter -> <results_dir>/charter-<date>[-N].json (a charter-regression
               replay, charter_replay.py; factory evidence, not skill
               maturity, so it is not LEDGER-linkable evidence below)

    -N starts at 2 and counts past existing same-day results. The path is
    returned, never created — recording stays with the caller.
    """
    if kind == "trigger":
        if harness is not None and harness not in HARNESSES:
            raise ValueError(f"unknown trigger harness {harness!r}")
        head = ("trigger" if harness in (None, "claude")
                else f"trigger-{harness}")
        base, stem, ext = results_dir, f"{head}-{date}", ".json"
    elif kind == "charter":
        base, stem, ext = results_dir, f"charter-{date}", ".json"
    elif kind == "output":
        if not slug:
            raise ValueError("output results need a slug")
        base, stem, ext = results_dir / "output", f"{slug}-{date}", ""
    else:
        raise ValueError(f"unknown results kind {kind!r}")
    path = base / f"{stem}{ext}"
    suffix = 2
    while path.exists():
        path = base / f"{stem}-{suffix}{ext}"
        suffix += 1
    return path


def _items(data, key, label):
    """(list-of-dict entries, shape problems) for the collection data[key].

    An absent key is legitimate: empty list, no problem (the coverage
    checks in validate() own emptiness). A present non-list — including
    null — is malformed and yields one problem; non-dict entries are
    dropped with a problem each, so no downstream .get() ever hits a
    non-dict. Validators return problem strings; they never raise.
    """
    if key not in data:
        return [], []
    raw = data[key]
    if not isinstance(raw, list):
        return [], [f"{label} {key} is not a list"]
    problems = [f"{label} {key} entry #{n} is not an object"
                for n, e in enumerate(raw) if not isinstance(e, dict)]
    return [e for e in raw if isinstance(e, dict)], problems


def _output_field_missing(record, field):
    # expectations must be non-empty (an eval with none checks nothing);
    # any other field is missing only when absent or null — falsy values
    # like id 0 are values, mirroring validate()'s is-None handling
    if field == "expectations":
        return not record.get(field)
    return record.get(field) is None


def fixture_refs(data):
    """(eval id, run_fixture) per record that names a fixture.

    The accessor callers use instead of reaching into records by string
    key — the lint checks each ref's existence, a filesystem fact that
    stays with it. Records without a fixture are skipped (validate_output
    owns that complaint), and malformed shapes yield nothing rather than
    raising, mirroring _items.
    """
    evals = data.get("evals")
    if not isinstance(evals, list):
        return []
    return [(e.get("id"), e["run_fixture"]) for e in evals
            if isinstance(e, dict) and e.get("run_fixture")]


def validate_output(data, slug, label):
    """Return problem strings for a parsed output-eval set; [] means valid.

    Shape only — filesystem facts (the file's stem, fixture existence)
    stay with the caller. label prefixes every problem, mirroring
    validate().
    """
    evals, shape = _items(data, "evals", label)
    ids = [e.get("id") for e in evals]
    return (
        shape
        + ([f"{label} skill_name is {data.get('skill_name')!r}, "
            f"expected {slug!r}"]
           if data.get("skill_name") != slug else [])
        + [f"{label} has duplicate eval id {i!r}"
           for i in sorted({i for i in ids if ids.count(i) > 1},
                           key=lambda i: (i is None, str(i)))]
        + [f"{label} eval {e.get('id')!r} missing field: {field}"
           for e in evals for field in OUTPUT_FIELDS
           if _output_field_missing(e, field)]
    )


def validate(data, skills, label):
    """Return problem strings for a parsed eval-set dict; [] means valid.

    label prefixes every problem (the lint passes the repo-relative path,
    the runner whatever --eval-set was given), so both callers print the
    same diagnostics for the same defect.
    """
    if "version" not in data:
        return [f"{label} missing 'version' field"]
    cases, shape = _items(data, "cases", label)

    ids = [c.get("id") for c in cases]
    problems = (
        shape
        + [f"{label} has duplicate case id {i!r}"
           for i in sorted({i for i in ids if ids.count(i) > 1},
                           key=lambda i: (i is None, str(i)))]
        + [f"{label} case {c.get('id')!r} has invalid "
           f"expected {c.get('expected')!r}"
           for c in cases
           if c.get("expected") is not None
           and c.get("expected") not in skills]
        + [f"{label} case {c.get('id')!r} has invalid "
           f"kind {c.get('kind')!r}"
           for c in cases if c.get("kind") not in KINDS]
        + [f"{label} case {c.get('id')!r} has no query"
           for c in cases if not c.get("query")]
        # id presence matters as much as query presence: every runner
        # report subscripts case["id"], so an id-less case must be
        # refused here, not become a KeyError mid-run. is-None mirrors
        # the expected/OUTPUT_FIELDS handling: falsy ids are values.
        + [f"{label} case {c.get('id')!r} has no id"
           for c in cases if c.get("id") is None]
    )

    coverage = [c.get("expected") for c in cases]
    problems += [f"{label} covers skill {slug!r} in only "
                 f"{coverage.count(slug)} case(s), need >= 3"
                 for slug in skills if coverage.count(slug) < 3]
    if coverage.count(None) < 3:
        problems += [f"{label} has only {coverage.count(None)} "
                     "distractor case(s) (expected: null), need >= 3"]
    return problems


def load(path, skills, label):
    """Read and validate an eval set; return (cases, problems).

    Any problem means the set is unusable: cases is [] so callers cannot
    half-run an invalid set, and problems carries the diagnostics.
    """
    if not path.is_file():
        return [], [f"missing {label}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [], [f"{label} is not valid JSON: {err}"]
    problems = validate(data, skills, label)
    return ([], problems) if problems else (data.get("cases", []), [])
