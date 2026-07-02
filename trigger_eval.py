#!/usr/bin/env python3
"""Trigger (routing) eval for the idea-to-prod skills.

Installs ALL skill descriptions simultaneously as command files in an
isolated temporary project, runs each eval query through `claude -p`, and
detects WHICH skill fired — testing cross-skill discrimination rather than
one description in isolation. Exit 0 = all cases pass, 1 = failures.

Derived from the skill-creator plugin's scripts/run_eval.py and
scripts/utils.py, Copyright Anthropic, PBC, licensed under the Apache
License, Version 2.0 (see NOTICE and licenses/Apache-2.0.txt). This file
has been modified from the original: multi-skill routing detection,
per-run isolated project directories, settings-source isolation, and a
routing-case schema with confusion-matrix reporting.

POSIX-only (uses select.select on pipes). Requires the `claude` CLI.
"""
import argparse
import datetime
import json
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGES = ["idea", "prd", "ux-design", "architect", "decompose",
          "implement", "verify", "review", "ship", "operate"]
ALL_SKILLS = ["next"] + STAGES
KINDS = ("direct", "situational", "near-miss", "distractor", "router")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def load_descriptions(skills_dir):
    """Parse every skill's frontmatter description. Fails loudly on gaps."""
    descriptions = {}
    for slug in ALL_SKILLS:
        path = skills_dir / slug / "SKILL.md"
        match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            raise ValueError(f"{path} has no frontmatter block")
        fields = dict(
            (line.split(":", 1)[0].strip(), line.split(":", 1)[1].strip())
            for line in match.group(1).splitlines()
            if ":" in line
        )
        if not fields.get("description"):
            raise ValueError(f"{path} frontmatter has no description")
        descriptions[slug] = fields["description"]
    return descriptions


def build_project_dir(descriptions, run_id):
    """Create an isolated project dir with one command file per skill."""
    project_dir = Path(tempfile.mkdtemp(prefix="i2p-eval-"))
    commands_dir = project_dir / ".claude" / "commands"
    commands_dir.mkdir(parents=True)
    for slug, description in descriptions.items():
        indented = "\n  ".join(description.split("\n"))
        (commands_dir / f"{slug}-skill-{run_id}.md").write_text(
            f"---\n"
            f"description: |\n"
            f"  {indented}\n"
            f"---\n\n"
            f"# {slug}\n\n"
            f"This skill handles: {description}\n",
            encoding="utf-8",
        )
    return project_dir


def _match_slug(text, name_to_slug):
    """Return the slug whose command name appears in text, if any."""
    for clean_name, slug in name_to_slug.items():
        if clean_name in text:
            return slug
    return None


def _watch_stream(process, name_to_slug, timeout):
    """Watch claude's stream-json output; return the fired slug or None.

    Early detection via stream events (content_block_start / input_json_delta)
    so we can return before tool execution; falls back to the full assistant
    message for older CLI output shapes.
    """
    start_time = time.time()
    buffer = ""
    pending_tool = None
    accumulated_json = ""

    while time.time() - start_time < timeout:
        if process.poll() is not None:
            remaining = process.stdout.read()
            if remaining:
                buffer += remaining.decode("utf-8", errors="replace")
            break

        ready, _, _ = select.select([process.stdout], [], [], 1.0)
        if not ready:
            continue

        chunk = os.read(process.stdout.fileno(), 8192)
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace")

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "stream_event":
                se = event.get("event", {})
                se_type = se.get("type", "")
                if se_type == "content_block_start":
                    cb = se.get("content_block", {})
                    if cb.get("type") == "tool_use":
                        if cb.get("name", "") in ("Skill", "Read"):
                            pending_tool = cb["name"]
                            accumulated_json = ""
                        else:
                            return None  # reached for a different tool first
                elif se_type == "content_block_delta" and pending_tool:
                    delta = se.get("delta", {})
                    if delta.get("type") == "input_json_delta":
                        accumulated_json += delta.get("partial_json", "")
                        slug = _match_slug(accumulated_json, name_to_slug)
                        if slug:
                            return slug
                elif se_type in ("content_block_stop", "message_stop"):
                    if pending_tool:
                        return _match_slug(accumulated_json, name_to_slug)
                    if se_type == "message_stop":
                        return None

            elif event.get("type") == "assistant":
                for item in event.get("message", {}).get("content", []):
                    if item.get("type") != "tool_use":
                        continue
                    tool_input = item.get("input", {})
                    target = (tool_input.get("skill", "")
                              if item.get("name") == "Skill"
                              else tool_input.get("file_path", "")
                              if item.get("name") == "Read"
                              else "")
                    return _match_slug(target, name_to_slug)

            elif event.get("type") == "result":
                return None
    return None


def run_single_query(query, descriptions, timeout, model, isolate):
    """Run one query in a fresh isolated project; return fired slug or None."""
    run_id = uuid.uuid4().hex[:8]
    name_to_slug = {f"{slug}-skill-{run_id}": slug for slug in descriptions}
    project_dir = build_project_dir(descriptions, run_id)

    cmd = [
        "claude", "-p", query,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if isolate:
        cmd.extend(["--setting-sources", "project"])
    if model:
        cmd.extend(["--model", model])

    # Remove CLAUDECODE env var to allow nesting claude -p inside a
    # Claude Code session; the guard is for interactive terminal conflicts.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    process = None
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=project_dir,
            env=env,
        )
        return _watch_stream(process, name_to_slug, timeout)
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        shutil.rmtree(project_dir, ignore_errors=True)


def score_case(case, fired_counts, runs, threshold):
    """Score one case from its Counter of fired slugs ('none' for None)."""
    expected = case["expected"] or "none"
    correct_rate = fired_counts.get(expected, 0) / runs if runs else 0.0
    return {
        "id": case["id"],
        "kind": case["kind"],
        "expected": case["expected"],
        "query": case["query"],
        "fired": dict(fired_counts),
        "runs": runs,
        "correct_rate": round(correct_rate, 3),
        "pass": correct_rate >= threshold,
    }


def summarize(results):
    """Roll per-case results into totals, by-kind/by-skill counts, confusion."""
    def bucket(results, key):
        totals = {}
        for r in results:
            k = key(r)
            entry = totals.setdefault(k, {"total": 0, "passed": 0})
            entry["total"] += 1
            entry["passed"] += 1 if r["pass"] else 0
        return totals

    confusion = {}
    for r in results:
        expected = r["expected"] or "none"
        row = confusion.setdefault(expected, {})
        for fired, count in r["fired"].items():
            row[fired] = row.get(fired, 0) + count

    return {
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r["pass"]),
            "failed": sum(1 for r in results if not r["pass"]),
            "by_kind": bucket(results, lambda r: r["kind"]),
            "by_skill": bucket(results, lambda r: r["expected"] or "none"),
        },
        "confusion": confusion,
    }


def run_eval(cases, descriptions, workers, runs_per_query, timeout,
             threshold, model, isolate):
    """Fan out cases x runs_per_query; return per-case results + summary."""
    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_case = {
            executor.submit(run_single_query, case["query"], descriptions,
                            timeout, model, isolate): case["id"]
            for case in cases
            for _ in range(runs_per_query)
        }
        fired_by_case = {}
        done = 0
        for future in as_completed(future_to_case):
            case_id = future_to_case[future]
            try:
                fired = future.result()
            except Exception as err:
                print(f"warning: run for {case_id!r} failed: {err}",
                      file=sys.stderr)
                fired = None
            counts = fired_by_case.setdefault(case_id, Counter())
            counts[fired or "none"] += 1
            done += 1
            print(f"progress: {done}/{len(future_to_case)} runs",
                  file=sys.stderr, end="\r")
    print(file=sys.stderr)

    results = [
        score_case(case, fired_by_case.get(case["id"], Counter()),
                   sum(fired_by_case.get(case["id"], Counter()).values()),
                   threshold)
        for case in cases
    ]
    return {"results": results, **summarize(results)}


def cli_version():
    try:
        proc = subprocess.run(["claude", "--version"], capture_output=True,
                              text=True, timeout=15)
        return proc.stdout.strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def record(output, results_dir):
    """Write a dated results file, suffixing -2, -3... on collision."""
    results_dir.mkdir(parents=True, exist_ok=True)
    date = output["date"]
    path = results_dir / f"trigger-{date}.json"
    suffix = 2
    while path.exists():
        path = results_dir / f"trigger-{date}-{suffix}.json"
        suffix += 1
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return path


def print_report(output):
    for r in output["results"]:
        status = "PASS" if r["pass"] else "FAIL"
        fired = ", ".join(f"{k}x{v}" for k, v in sorted(r["fired"].items()))
        print(f"  [{status}] {r['id']}: expected={r['expected'] or 'none'} "
              f"fired=[{fired}]", file=sys.stderr)
    summary = output["summary"]
    print(f"trigger eval: {summary['passed']}/{summary['total']} passed",
          file=sys.stderr)
    print("confusion (expected -> fired):", file=sys.stderr)
    for expected, row in sorted(output["confusion"].items()):
        cells = ", ".join(f"{k}: {v}" for k, v in sorted(row.items()))
        print(f"  {expected}: {cells}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Cross-skill trigger/routing eval via claude -p")
    parser.add_argument("--eval-set", default=str(ROOT / "evals" / "routing.json"))
    parser.add_argument("--skills-dir", default=str(ROOT / "skills"))
    parser.add_argument("--num-workers", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30,
                        help="seconds per claude -p run")
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="correct-rate needed to pass a case")
    parser.add_argument("--model", default=None,
                        help="pin the model for reproducibility")
    parser.add_argument("--only", default=None,
                        help="run only cases whose id or expected slug matches")
    parser.add_argument("--record", action="store_true",
                        help="write evals/results/trigger-<date>.json")
    parser.add_argument("--no-isolate-settings", action="store_true",
                        help="drop --setting-sources project (auth fallback)")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text(encoding="utf-8"))
    cases = eval_set["cases"]
    if args.only:
        cases = [c for c in cases
                 if c["id"] == args.only or c["expected"] == args.only]
        if not cases:
            print(f"error: no cases match --only {args.only!r}",
                  file=sys.stderr)
            return 1

    descriptions = load_descriptions(Path(args.skills_dir))
    isolate = not args.no_isolate_settings

    output = {
        "date": datetime.date.today().isoformat(),
        "model": args.model,
        "cli_version": cli_version(),
        "runs_per_query": args.runs_per_query,
        "threshold": args.threshold,
        "isolated_settings": isolate,
        **run_eval(cases, descriptions, args.num_workers,
                   args.runs_per_query, args.timeout, args.threshold,
                   args.model, isolate),
    }

    print_report(output)
    if args.record:
        path = record(output, ROOT / "evals" / "results")
        print(f"recorded: {path.relative_to(ROOT)}", file=sys.stderr)
    print(json.dumps(output, indent=2))
    return 0 if output["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
