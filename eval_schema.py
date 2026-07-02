"""The routing eval-set's schema knowledge, in one place.

evals/routing.json holds routing cases ({id, kind, expected, query});
this module owns the kind vocabulary, the case shape, the coverage
policy, and load-plus-validate (ADR-0022). The structural lint and the
trigger-eval runner are thin callers reporting identical diagnostics.
Deliberately separate from protocol.py: this is eval-set knowledge, not
pipeline-protocol knowledge.
"""
import json

KINDS = ("direct", "situational", "near-miss", "distractor", "router")


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
