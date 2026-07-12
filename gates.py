#!/usr/bin/env python3
"""Factory gate detectors (PRD-0001; ADR-0032, ADR-0033, ADR-0034).

Offline, gating checks over the knowledge plane, following the same
conventions as lint.py: every checker takes the repo root and returns
label-prefixed problem strings; the CLI prints them and exits nonzero.
Lettered detectors (audit-evals.py style, letters shared with the
ai-tooling suite where the rule is the same idea):

  A WO-CITATION    — every breakdown work-order row cites a PRD id
  B PR-TRACEABILITY — PR body carries a WO id and Closes #N
                     (event-payload; SKIP locally; [factory-exempt]
                     logged)
  C LINK-INTEGRITY — every PRD-####/ADR-####/WO-#### token resolves;
                     duplicate PRD ids fail
  E SCAFFOLD-SYNC  — factory/manifest.json checksums match the template
                     payload (no hand-edited mirrors)
  F CONFIG-SHAPE   — factory config parses and every field is a valid
                     token (budgets, routing, caps)

`--selftest` runs the checkers against fixture trees and exits nonzero
on a failing assertion. Both run in CI (checks.yml) on every push/PR.
"""
import contextlib
import hashlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from protocol import read_frontmatter

PRD_TOKEN = re.compile(r"\bPRD-\d{4}\b")
ADR_TOKEN = re.compile(r"\bADR-(\d{4})\b")
WO_TOKEN = re.compile(r"\bWO-\d{4}\b")
CLOSES_TOKEN = re.compile(r"\bCloses #\d+\b", re.IGNORECASE)

CONFIG_ROUTES = ("mechanical", "implementation", "architecture_review")


def run_dirs(root):
    """Candidate run directories per the pipeline protocol."""
    dirs = [root / "docs"]
    for parent in ("features", "fixes"):
        base = root / "docs" / parent
        if base.is_dir():
            dirs.extend(p for p in sorted(base.iterdir()) if p.is_dir())
    return [d for d in dirs if d.is_dir()]


def _scannable_files(root):
    docs = root / "docs"
    files = sorted(docs.rglob("*.md")) if docs.is_dir() else []
    context = root / "CONTEXT.md"
    if context.is_file():
        files.append(context)
    return files


def check_wo_citation(root):
    """A: a work-order row that cites no PRD section is untraceable scope."""
    problems = []
    for run in run_dirs(root):
        breakdown = run / "breakdown.md"
        if not breakdown.is_file():
            continue
        for lineno, line in enumerate(
                breakdown.read_text(encoding="utf-8").splitlines(), 1):
            wo = WO_TOKEN.search(line)
            if wo and not PRD_TOKEN.search(line):
                rel = breakdown.relative_to(root)
                problems.append(
                    f"A: {rel}:{lineno} work-order row {wo.group(0)}"
                    " cites no PRD id")
    return problems


def check_pr_traceability(root, env=None):
    """B: a PR whose body cites no work order and closes no issue breaks
    the audit trail from code back to scope. Reads the CI event payload;
    SKIPs silently outside a PR run. [factory-exempt] titles pass but are
    logged so exemptions stay visible and countable in CI logs."""
    if env is None:
        env = os.environ
    event_path = env.get("GITHUB_EVENT_PATH")
    if not event_path:
        return []
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    pr = event.get("pull_request")
    if pr is None:
        return []
    title = pr.get("title") or ""
    body = pr.get("body") or ""
    if title.startswith("[factory-exempt]"):
        print("B: factory-exempt PR (logged)")
        return []
    problems = []
    if not WO_TOKEN.search(body):
        problems.append("B: PR body cites no work-order id")
    if not CLOSES_TOKEN.search(body):
        problems.append("B: PR body has no Closes #N link")
    return problems


def collect_prd_ids(root):
    """Map PRD id -> list of prd.md paths declaring it in frontmatter."""
    ids = {}
    for run in run_dirs(root):
        prd = run / "prd.md"
        if not prd.is_file():
            continue
        fields = read_frontmatter(prd) or {}
        prd_id = fields.get("id")
        if prd_id:
            ids.setdefault(prd_id, []).append(prd.relative_to(root))
    return ids


def collect_wo_rows(root):
    """Set of WO tokens that appear in any breakdown.md row."""
    rows = set()
    for run in run_dirs(root):
        breakdown = run / "breakdown.md"
        if breakdown.is_file():
            rows.update(WO_TOKEN.findall(
                breakdown.read_text(encoding="utf-8")))
    return rows


def check_link_integrity(root):
    """C: typed cross-link tokens must resolve; duplicate PRD ids fail."""
    problems = []
    prd_ids = collect_prd_ids(root)
    for prd_id, paths in sorted(prd_ids.items()):
        if len(paths) > 1:
            listed = ", ".join(str(p) for p in paths)
            problems.append(f"C: duplicate PRD id {prd_id} in {listed}")
    adr_dir = root / "docs" / "adr"
    adr_numbers = set()
    if adr_dir.is_dir():
        for path in adr_dir.glob("[0-9][0-9][0-9][0-9]-*.md"):
            adr_numbers.add(path.name[:4])
    wo_rows = collect_wo_rows(root)
    for path in _scannable_files(root):
        rel = path.relative_to(root)
        in_breakdown = path.name == "breakdown.md"
        for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            for token in PRD_TOKEN.findall(line):
                if token not in prd_ids:
                    problems.append(
                        f"C: {rel}:{lineno} dangling {token}"
                        " (no prd.md declares this id)")
            for number in ADR_TOKEN.findall(line):
                if number not in adr_numbers:
                    problems.append(
                        f"C: {rel}:{lineno} dangling ADR-{number}"
                        " (no docs/adr file)")
            if not in_breakdown:
                for token in WO_TOKEN.findall(line):
                    if token not in wo_rows:
                        problems.append(
                            f"C: {rel}:{lineno} dangling {token}"
                            " (no breakdown row)")
    return problems


def check_scaffold_sync(root):
    """E: the template payload must match its checksum manifest exactly."""
    manifest_path = root / "factory" / "manifest.json"
    if not manifest_path.is_file():
        return ["E: missing factory/manifest.json"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        return [f"E: factory/manifest.json is not valid JSON: {err}"]
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        return ["E: factory/manifest.json has no files map"]
    problems = []
    for rel, expected in sorted(files.items()):
        path = root / "factory" / rel
        if not path.is_file():
            problems.append(f"E: manifest lists missing file factory/{rel}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            problems.append(
                f"E: factory/{rel} does not match its manifest checksum"
                " (re-run manifest update, never hand-edit)")
    payload = root / "factory" / "templates"
    if payload.is_dir():
        for path in sorted(payload.rglob("*")):
            if path.is_file():
                rel = str(path.relative_to(root / "factory"))
                if rel not in files:
                    problems.append(f"E: factory/{rel} is not in the manifest")
    return problems


def check_config_shape(root):
    """F: factory config must parse and every field be a valid token."""
    candidates = [root / "factory" / "templates" / "factory.json",
                  root / ".github" / "factory.json"]
    problems = []
    for path in candidates:
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            problems.append(f"F: {rel} is not valid JSON: {err}")
            continue
        budgets = config.get("budgets_usd")
        if not isinstance(budgets, dict) or sorted(budgets) != ["L", "M", "S"]:
            problems.append(f"F: {rel} budgets_usd must map exactly S, M, L")
        else:
            for size, value in budgets.items():
                if not isinstance(value, (int, float)) or value <= 0:
                    problems.append(
                        f"F: {rel} budgets_usd.{size} must be a positive number")
        routing = config.get("routing")
        if not isinstance(routing, dict) or sorted(routing) != sorted(CONFIG_ROUTES):
            expected = ", ".join(CONFIG_ROUTES)
            problems.append(f"F: {rel} routing must map exactly {expected}")
        else:
            for route, model in routing.items():
                if not isinstance(model, str) or not model:
                    problems.append(
                        f"F: {rel} routing.{route} must name a model id")
        wip = config.get("wip_cap")
        if not isinstance(wip, int) or wip < 1:
            problems.append(f"F: {rel} wip_cap must be a positive integer")
        cap = config.get("monthly_cap_usd")
        if not isinstance(cap, (int, float)) or cap <= 0:
            problems.append(f"F: {rel} monthly_cap_usd must be a positive number")
    return problems


CHECKERS = (check_wo_citation, check_pr_traceability,
            check_link_integrity, check_scaffold_sync, check_config_shape)


def run_all(root):
    problems = []
    for checker in CHECKERS:
        problems.extend(checker(root))
    return problems


def selftest():
    """Fixture trees: each detector must catch its planted defect and stay
    silent on the clean tree."""
    failures = []

    def expect(label, problems, *substrings):
        for fragment in substrings:
            if not any(fragment in p for p in problems):
                failures.append(f"{label}: expected a problem containing"
                                f" {fragment!r}, got {problems}")

    def expect_clean(label, problems):
        if problems:
            failures.append(f"{label}: expected no problems, got {problems}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run = root / "docs" / "features" / "demo"
        run.mkdir(parents=True)
        (run / "prd.md").write_text(
            "---\nstage: prd\nid: PRD-0001\n---\n# PRD\n", encoding="utf-8")
        (run / "breakdown.md").write_text(
            "- [ ] WO-0001 do the thing (PRD-0001 §Solution)\n"
            "- [ ] WO-0002 uncited row\n", encoding="utf-8")
        (root / "CONTEXT.md").write_text(
            "See PRD-0001, PRD-0099, ADR-0001 and WO-0003.\n",
            encoding="utf-8")
        (root / "docs" / "adr").mkdir()
        (root / "docs" / "adr" / "0001-real.md").write_text(
            "# Real\n", encoding="utf-8")
        expect("A", check_wo_citation(root), "WO-0002")
        problems = check_link_integrity(root)
        expect("C", problems, "PRD-0099", "WO-0003")
        if any("PRD-0001 " in p and "dangling" in p for p in problems):
            failures.append(f"C: PRD-0001 should resolve, got {problems}")

        factory = root / "factory" / "templates"
        factory.mkdir(parents=True)
        (factory / "Makefile").write_text("check:\n", encoding="utf-8")
        digest = hashlib.sha256((factory / "Makefile").read_bytes()).hexdigest()
        (root / "factory" / "manifest.json").write_text(json.dumps(
            {"files": {"templates/Makefile": digest}}), encoding="utf-8")
        expect_clean("E clean", check_scaffold_sync(root))
        (factory / "Makefile").write_text("check: tampered\n", encoding="utf-8")
        expect("E", check_scaffold_sync(root), "manifest checksum")

        (factory / "factory.json").write_text(json.dumps(
            {"budgets_usd": {"S": 5, "M": 15},
             "routing": {"mechanical": "m"},
             "wip_cap": 0, "monthly_cap_usd": -1}), encoding="utf-8")
        problems = check_config_shape(root)
        expect("F", problems, "budgets_usd", "routing", "wip_cap",
               "monthly_cap_usd")

        event = root / "event.json"
        env = {"GITHUB_EVENT_PATH": str(event)}
        event.write_text(json.dumps({"pull_request": {
            "title": "fix: something", "body": "no tokens here"}}),
            encoding="utf-8")
        expect("B", check_pr_traceability(root, env),
               "cites no work-order id", "no Closes #N link")
        event.write_text(json.dumps({"pull_request": {
            "title": "[factory-exempt] deps", "body": ""}}),
            encoding="utf-8")
        log = io.StringIO()
        with contextlib.redirect_stdout(log):
            problems = check_pr_traceability(root, env)
        expect_clean("B exempt", problems)
        if "factory-exempt PR (logged)" not in log.getvalue():
            failures.append("B exempt: expected the logged line,"
                            f" got {log.getvalue()!r}")
        event.write_text(json.dumps({"ref": "refs/heads/main"}),
                         encoding="utf-8")
        expect_clean("B non-PR", check_pr_traceability(root, env))
        event.write_text(json.dumps({"pull_request": {
            "title": "WO-0003: detector B",
            "body": "WO-0003 (PRD-0001) Closes #108"}}), encoding="utf-8")
        expect_clean("B clean", check_pr_traceability(root, env))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs").mkdir()
        payload = root / "factory" / "templates"
        payload.mkdir(parents=True)
        (payload / "factory.json").write_text(json.dumps(
            {"budgets_usd": {"S": 5, "M": 15, "L": 40},
             "routing": {"mechanical": "m", "implementation": "i",
                         "architecture_review": "a"},
             "wip_cap": 3, "monthly_cap_usd": 300}), encoding="utf-8")
        digest = hashlib.sha256(
            (payload / "factory.json").read_bytes()).hexdigest()
        (root / "factory" / "manifest.json").write_text(json.dumps(
            {"files": {"templates/factory.json": digest}}), encoding="utf-8")
        saved = os.environ.pop("GITHUB_EVENT_PATH", None)
        try:
            expect_clean("clean tree", run_all(root))
        finally:
            if saved is not None:
                os.environ["GITHUB_EVENT_PATH"] = saved

    for failure in failures:
        print(failure)
    print(f"selftest: {'FAIL' if failures else 'ok'}")
    return 1 if failures else 0


def repo_root():
    """Nearest ancestor containing .git (dir or worktree file): correct at
    the factory repo root and stamped at tools/factory/ in a product repo."""
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return here


def main(argv):
    if "--selftest" in argv:
        return selftest()
    root = repo_root()
    problems = run_all(root)
    for problem in problems:
        print(problem)
    print(f"gates: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
