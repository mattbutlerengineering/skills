"""The evals' schema knowledge, in one place.

evals/routing.json holds routing cases ({id, kind, expected, query});
this module owns the kind vocabulary, the case shape, the coverage
policy, and load-plus-validate (ADR-0022). evals/output/<slug>.json
holds output-eval records; this module owns their required field set
(issue #25). evals/results/ is append-only; this module owns its naming
grammar — dated stems with -N collision suffixes — for both results
kinds (issue #26, ADR-0024). The structural lint and the trigger-eval
runner are thin callers. Deliberately separate from protocol.py: this
is eval knowledge, not pipeline-protocol knowledge.
"""
import json
import re

KINDS = ("direct", "situational", "near-miss", "distractor", "router")

# The append-only results naming grammar as it appears in LEDGER evidence
# links: trigger-<date>[-N].json files, output/<slug>-<date>[-N]/grading.json,
# N counting up from 2 (results_path below is the generator).
_SUFFIX = r"(?:-(?:[2-9]|[1-9]\d+))?"
_RESULTS_LINK = re.compile(
    r"^evals/results/(?:"
    rf"trigger-\d{{4}}-\d{{2}}-\d{{2}}{_SUFFIX}\.json"
    rf"|output/[a-z0-9-]+-\d{{4}}-\d{{2}}-\d{{2}}{_SUFFIX}/grading\.json)$")


def valid_results_link(target):
    """True when a LEDGER evidence link target follows the results grammar."""
    return bool(_RESULTS_LINK.match(target))


# Every field an output-eval record must carry (docs/output-evals.md
# names this module as the shape's owner).
OUTPUT_FIELDS = ("id", "prompt", "run_fixture", "run_scale",
                 "expected_output", "expectations")


def results_path(results_dir, kind, date, slug=None):
    """Next free results path per the append-only naming grammar (#26).

    trigger -> <results_dir>/trigger-<date>[-N].json (the recorded file)
    output  -> <results_dir>/output/<slug>-<date>[-N] (the grading dir)

    -N starts at 2 and counts past existing same-day results. The path is
    returned, never created — recording stays with the caller.
    """
    if kind == "trigger":
        base, stem, ext = results_dir, f"trigger-{date}", ".json"
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


def _output_field_missing(record, field):
    # expectations must be non-empty (an eval with none checks nothing);
    # any other field is missing only when absent or null — falsy values
    # like id 0 are values, mirroring validate()'s is-None handling
    if field == "expectations":
        return not record.get(field)
    return record.get(field) is None


def validate_output(data, slug, label):
    """Return problem strings for a parsed output-eval set; [] means valid.

    Shape only — filesystem facts (the file's stem, fixture existence)
    stay with the caller. label prefixes every problem, mirroring
    validate().
    """
    evals = data.get("evals", [])
    ids = [e.get("id") for e in evals]
    return (
        ([f"{label} skill_name is {data.get('skill_name')!r}, "
          f"expected {slug!r}"]
         if data.get("skill_name") != slug else [])
        + [f"{label} has duplicate eval id {i!r}"
           for i in sorted({i for i in ids if ids.count(i) > 1})]
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
    cases = data.get("cases", [])

    ids = [c.get("id") for c in cases]
    problems = (
        [f"{label} has duplicate case id {i!r}"
         for i in sorted({i for i in ids if ids.count(i) > 1})]
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
