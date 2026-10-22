"""Fixture-tree builders for the eval_trends tests: temp record trees in
the shapes the five record locations hold, written by the test and never
under the real evals/ or plugin-evals/. Pure helpers, no test cases."""
import json
from pathlib import Path


def write_json(root, rel, data):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def trigger_record(date, cases, model="m", runs=3, threshold=0.5,
                   harness=None, errors=None):
    """cases: [(id, expected, query, passed)]."""
    results = [{"id": i, "kind": "direct", "expected": e, "query": q,
                "fired": {}, "runs": runs, "errors": 0,
                "correct_rate": 1.0 if p else 0.0, "pass": p}
               for i, e, q, p in cases]
    summary = {"total": len(results),
               "passed": sum(1 for r in results if r["pass"])}
    if errors is not None:
        summary["errors"] = errors
    data = {"date": date, "model": model, "cli_version": "x",
            "runs_per_query": runs, "threshold": threshold,
            "results": results, "summary": summary, "confusion": {}}
    if harness:
        data["harness"] = harness
    return data


def numbered_cases(count, passed, prefix="c"):
    """count trigger cases, the first `passed` of them passing."""
    return [(f"{prefix}{i}", "idea", f"query {prefix}{i}", i < passed)
            for i in range(count)]


def charter_record(date, results, arm="control", model="haiku",
                   charters=None):
    """results: [(id, role, verdict)]."""
    return {"date": date, "source": "live-model", "model": model,
            "arm": arm,
            "charters": charters or {"planner": "aa", "swe": "bb"},
            "results": [{"id": i, "role": r, "verdict": v}
                        for i, r, v in results],
            "summary": {"total": len(results)}}


def output_record(expectations):
    """expectations: [(text, passed)]."""
    return {"expectations": [{"text": t, "passed": p, "evidence": "e"}
                             for t, p in expectations],
            "summary": {"total": len(expectations),
                        "passed": sum(1 for _, p in expectations if p)}}


def plugin_record(started, cases, tags=("next",), cost=0.5, partial=False,
                  ablation="none", model="claude-sonnet-5",
                  judge="claude-haiku-4-5", threshold=1, passed=None):
    """cases: [(name, prompt, [(grader name, grader markdown or None)])]."""
    built = [{"name": n, "promptMarkdown": p,
              "graders": [{"name": g, "type": "llm",
                           **({"graderMarkdown": m} if m else {})}
                          for g, m in graders]}
             for n, p, graders in cases]
    return {"schemaVersion": 1, "startedAt": started, "costUsd": cost,
            "partial": partial,
            "suite": {"ablation": ablation, "modelOverride": model,
                      "judgeModel": judge, "tagFilters": list(tags),
                      "threshold": threshold},
            "cases": built,
            "aggregates": {"casesTotal": len(built),
                           "casesPassed": len(built) if passed is None
                           else passed}}


def signals_record(date):
    return {"date": date, "head": "abc", "refs": 1, "runs": [],
            "aggregate": {}}
