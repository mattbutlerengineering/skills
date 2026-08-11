#!/usr/bin/env python3
"""Trigger (routing) eval for the idea-to-prod skills.

Installs ALL skill descriptions simultaneously in an isolated temporary
project, runs each eval query through the selected harness CLI, and
detects WHICH skill fired — testing cross-skill discrimination rather than
one description in isolation. Exit 0 = all cases pass, 1 = failures.

Two harnesses (ADR-0027, ADR-0031): `claude -p` (primary; descriptions
installed as command files, detection watches the Skill/Read tools) and
`omp -p --mode json` (second harness; descriptions installed as project
.claude/skills entries, detection watches the read tool's skill:// URI).
Results record which harness ran: omp snapshots are named
trigger-omp-<date>[-N].json, claude snapshots stay trigger-<date>[-N].json.

Derived from the skill-creator plugin's scripts/run_eval.py and
scripts/utils.py, Copyright Anthropic, PBC, licensed under the Apache
License, Version 2.0 (see NOTICE and licenses/Apache-2.0.txt). This file
has been modified from the original: multi-skill routing detection,
per-run isolated project directories, settings-source isolation, and a
routing-case schema with confusion-matrix reporting.

POSIX-only (cli.harness_run selects on pipes). Requires the `claude`
CLI (or the `omp` CLI with --harness omp).
"""
import argparse
import datetime
import json
import shutil
import sys
import tempfile
import uuid
from collections import Counter, namedtuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import cli
import eval_schema
import protocol
from protocol import ALL_SKILLS, read_frontmatter

ROOT = Path(__file__).resolve().parent


def load_descriptions(root):
    """Parse every skill's frontmatter description under a plugin root.

    Fails loudly on gaps with lint's exact strings —
    protocol.skill_frontmatter_problems is the one frontmatter contract
    (ADR-0052), so a description over Pi's 1024-char limit refuses to
    eval just as it refuses to lint."""
    problems = [p for slug in ALL_SKILLS
                for p in protocol.skill_frontmatter_problems(root, slug)]
    if problems:
        raise ValueError("; ".join(problems))
    return {slug: read_frontmatter(protocol.skill_path(root, slug))
            ["description"] for slug in ALL_SKILLS}


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


def build_omp_project_dir(descriptions, run_id):
    """Create an isolated project dir with one .claude/skills entry per skill.

    omp discovers project skills from .claude/skills/<name>/SKILL.md. The
    per-run name suffix keeps parallel runs distinct and lets the runner's
    --skills '*-skill-<run_id>' glob exclude every globally installed
    skill, so the eval discriminates only among the run's own candidates.
    """
    project_dir = Path(tempfile.mkdtemp(prefix="i2p-eval-omp-"))
    for slug, description in descriptions.items():
        name = f"{slug}-skill-{run_id}"
        skill_dir = project_dir / ".claude" / "skills" / name
        skill_dir.mkdir(parents=True)
        indented = "\n  ".join(description.split("\n"))
        (skill_dir / "SKILL.md").write_text(
            f"---\n"
            f"name: {name}\n"
            f"description: |\n"
            f"  {indented}\n"
            f"---\n\n"
            f"# {slug}\n\n"
            f"This skill handles: {description}\n",
            encoding="utf-8",
        )
    return project_dir


def _match_slug(text, name_to_slug):
    """Return the slug whose command name appears in text, if any.

    Longest name first: review-skill-<id> is a substring of
    address-pr-review-skill-<id>, so a shorter name checked earlier
    would shadow the longer one and misattribute the fire.
    """
    for clean_name in sorted(name_to_slug, key=len, reverse=True):
        if clean_name in text:
            return name_to_slug[clean_name]
    return None


def detect_fired(events, name_to_slug):
    """Consume decoded stream-json events; return the fired slug or None.

    Pure state machine — no process, pipe, or clock in the interface.
    Early detection via input_json_delta accumulation (returns before
    tool execution), content_block_stop/message_stop fallbacks, the
    legacy full assistant message shape for older CLI output, and a
    non-Skill/Read tool starting first meaning no fire.
    """
    pending_tool = None
    accumulated_json = ""

    for event in events:
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


def _omp_call_slug(tool_name, arguments, name_to_slug):
    """Fired slug for one completed omp tool call, or None.

    In omp a skill loads through the built-in read tool with a
    skill://<name> URI (a direct SKILL.md path also matches); any other
    tool reached first means no skill fired.
    """
    if tool_name != "read" or not isinstance(arguments, dict):
        return None
    return _match_slug(arguments.get("path") or "", name_to_slug)


def detect_omp_fired(events, name_to_slug):
    """Consume decoded omp --mode json events; return the fired slug or None.

    Pure state machine, detect_fired's omp twin. The first completed tool
    call decides: toolcall_end (the model finished emitting the call,
    arguments fully parsed) fires before the tool executes;
    tool_execution_start is the fallback should the assistant-event shape
    drift. agent_end without any tool call means no fire.
    """
    for event in events:
        etype = event.get("type")
        if etype == "message_update":
            ame = event.get("assistantMessageEvent") or {}
            if ame.get("type") == "toolcall_end":
                call = ame.get("toolCall") or {}
                return _omp_call_slug(call.get("name"),
                                      call.get("arguments"), name_to_slug)
        elif etype == "tool_execution_start":
            return _omp_call_slug(event.get("toolName"),
                                  event.get("args"), name_to_slug)
        elif etype == "agent_end":
            return None
    return None


def _claude_command(prompt, model, isolate, run_id=None):
    """argv for one claude -p run — the one home for the claude flag
    grammar. --include-partial-messages is load-bearing for every
    consumer: it emits the current stream_event frames, so no caller
    depends exclusively on the legacy full assistant message shape
    (ADR-0053). run_id is unused: claude isolation is flag-based
    (--setting-sources), not name-based like omp's glob."""
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if isolate:
        cmd.extend(["--setting-sources", "project"])
    if model:
        cmd.extend(["--model", model])
    return cmd


def _omp_command(prompt, model, isolate, run_id=None):
    """argv for one omp -p run — the one home for the omp flag grammar.

    omp has no --setting-sources equivalent, so isolation is always on
    and the isolate flag is unused (claude-only): --skills restricts
    discovery to the run's own *-skill-<run_id> entries, and
    --no-extensions/--no-rules/--no-session keep the user's omp
    environment out of the run.
    """
    cmd = [
        "omp", "--mode", "json", "-p",
        "--no-session", "--no-extensions", "--no-rules",
        "--skills", f"*-skill-{run_id}",
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    return cmd


def _claude_invocation(query, descriptions, run_id, model, isolate):
    """(project_dir, cmd) for one claude -p run."""
    return (build_project_dir(descriptions, run_id),
            _claude_command(query, model, isolate, run_id))


def _omp_invocation(query, descriptions, run_id, model, isolate):
    """(project_dir, cmd) for one omp -p run."""
    return (build_omp_project_dir(descriptions, run_id),
            _omp_command(query, model, isolate, run_id))


# One registration per harness (ADR-0038, ADR-0053): everything
# harness-specific a runner — trigger eval, charter replay, or a
# transcript recorder — needs, as one adapter. binary is the executable
# (provenance probes, fake-harness installs); command is the flag
# grammar, uniform signature (prompt, model, isolate, run_id=None);
# invocation composes the project builder with command, so
# (project_dir, cmd) can only come from the tested path; detect is the
# matching stream detector; decode names the stream's line framing
# (cli.decode_events — the shared JSON-lines decode) for consumers that
# hold raw lines themselves. Keys are pinned to eval_schema.HARNESSES,
# the vocabulary owner, by test.
Harness = namedtuple("Harness",
                     ("binary", "command", "invocation", "detect", "decode"))

HARNESSES = {
    "claude": Harness("claude", _claude_command, _claude_invocation,
                      detect_fired, cli.decode_events),
    "omp": Harness("omp", _omp_command, _omp_invocation,
                   detect_omp_fired, cli.decode_events),
}


def run_single_query(query, descriptions, timeout, model, isolate,
                     harness="claude"):
    """Run one query in a fresh isolated project; return fired slug or None.

    cli.harness_run owns the child's whole lifecycle (own process group,
    drain-after-exit reader, unconditional group kill — ADR-0053); this
    function's residual duty is the per-run project dir."""
    run_id = uuid.uuid4().hex[:8]
    name_to_slug = {f"{slug}-skill-{run_id}": slug for slug in descriptions}
    adapter = HARNESSES[harness]
    project_dir, cmd = adapter.invocation(query, descriptions, run_id,
                                          model, isolate)
    try:
        with cli.harness_run(cmd, cwd=project_dir, timeout=timeout) as events:
            return adapter.detect(events, name_to_slug)
    finally:
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
             threshold, model, isolate, harness="claude"):
    """Fan out cases x runs_per_query; return per-case results + summary."""
    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_case = {
            executor.submit(run_single_query, case["query"], descriptions,
                            timeout, model, isolate, harness): case["id"]
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


def record(output, results_dir):
    """Write a dated results file; eval_schema owns the naming grammar."""
    results_dir.mkdir(parents=True, exist_ok=True)
    path = eval_schema.results_path(results_dir, "trigger", output["date"],
                                    harness=output.get("harness"))
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
        description="Cross-skill trigger/routing eval via claude -p or omp -p")
    parser.add_argument("--harness", choices=eval_schema.HARNESSES,
                        default="claude",
                        help="which CLI drives the queries (ADR-0031)")
    parser.add_argument("--eval-set", default=str(ROOT / "evals" / "routing.json"))
    parser.add_argument("--skills-root", default=str(ROOT),
                        help="plugin root; skill descriptions are read "
                             "from <skills-root>/skills")
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
                        help="write evals/results/trigger[-<harness>]-<date>"
                             ".json")
    parser.add_argument("--no-isolate-settings", action="store_true",
                        help="drop --setting-sources project (auth fallback; "
                             "claude harness only)")
    args = parser.parse_args()

    cases, problems = eval_schema.load(Path(args.eval_set), ALL_SKILLS,
                                       label=args.eval_set)
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    if args.only:
        cases = [c for c in cases
                 if c["id"] == args.only or c["expected"] == args.only]
        if not cases:
            print(f"error: no cases match --only {args.only!r}",
                  file=sys.stderr)
            return 1

    descriptions = load_descriptions(Path(args.skills_root))
    isolate = not args.no_isolate_settings

    output = {
        "date": datetime.date.today().isoformat(),
        "harness": args.harness,
        "model": args.model,
        "cli_version": cli.version(HARNESSES[args.harness].binary),
        "runs_per_query": args.runs_per_query,
        "threshold": args.threshold,
        "isolated_settings": isolate,
        **run_eval(cases, descriptions, args.num_workers,
                   args.runs_per_query, args.timeout, args.threshold,
                   args.model, isolate, args.harness),
    }

    print_report(output)
    if args.record:
        path = record(output, ROOT / "evals" / "results")
        print(f"recorded: {path.relative_to(ROOT)}", file=sys.stderr)
    print(json.dumps(output, indent=2))
    return 0 if output["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
