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

`--metrics RESULTS_FILE [--kind KIND]` runs nothing: it derives per-skill
precision/recall/F1 from an already-recorded results file (read-only).

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


def _flush_block(block, calls, texts):
    """Close one partial-frame content block into a message."""
    kind, name, buffer = block
    if kind != "tool_use":
        if buffer:
            texts.append(buffer)
        return
    try:
        parsed = json.loads(buffer) if buffer else {}
    except json.JSONDecodeError:
        # A timeout can cut the stream mid-input: keep the raw text so
        # transcript-scoped expectations still see what was firing —
        # dropping it would silently un-fire a forbid.
        parsed = {"raw": buffer}
    calls.append({"name": name, "input": parsed})


def _consume_frame(se, block, calls, texts):
    """One stream_event frame into the partial-frame state machine;
    returns the open [kind, name, buffer] block, or None."""
    se_type = se.get("type")
    if se_type == "content_block_start":
        cb = se.get("content_block", {})
        if cb.get("type") in ("tool_use", "text"):
            return [cb["type"], cb.get("name", ""), ""]
        return None
    if se_type == "content_block_delta" and block:
        delta = se.get("delta", {})
        if delta.get("type") == "input_json_delta":
            return [block[0], block[1], block[2] + delta.get("partial_json",
                                                             "")]
        if delta.get("type") == "text_delta":
            return [block[0], block[1], block[2] + delta.get("text", "")]
        return block
    if se_type == "content_block_stop" and block:
        _flush_block(block, calls, texts)
        return None
    return block


def claude_messages(events):
    """Decoded claude stream-json events in, one record per assistant
    message out: {id, parent_tool_use_id, tool_calls, texts}, in order
    of first appearance. Pure, like detect_fired.

    The CLI emits two shapes for one message under
    --include-partial-messages: stream_event partial frames (opened by
    message_start, which names the id) and the legacy full assistant
    message (which carries message.id). They are collected apart and
    the frames win per message id when they hold anything — never
    summed, and never chosen for the whole run, so a message the CLI
    sent in one shape only (a subagent's, say) is still read while its
    neighbours are framed. A message with no id (older output) shares
    the None key. A block still open at the end (a timeout cut) is
    flushed into the message it belongs to."""
    frames, legacy, parents, order = {}, {}, {}, []

    def slot(table, key, parent):
        if key not in parents:
            order.append(key)
            parents[key] = None
        if parents[key] is None:
            parents[key] = parent
        return table.setdefault(key, ([], []))

    current, block = None, None
    for event in events:
        etype = event.get("type")
        if etype == "stream_event":
            se = event.get("event", {})
            if se.get("type") == "message_start":
                current = se.get("message", {}).get("id")
            if se.get("type") in ("message_start", "content_block_start"):
                slot(frames, current, event.get("parent_tool_use_id"))
            # an open block was started under current, so its slot exists
            block = _consume_frame(se, block,
                                   *frames.get(current, ([], [])))
        elif etype == "assistant":
            message = event.get("message", {})
            calls, texts = slot(legacy, message.get("id"),
                                event.get("parent_tool_use_id"))
            for item in message.get("content", []):
                if item.get("type") == "tool_use":
                    calls.append({"name": item.get("name", ""),
                                  "input": item.get("input", {})})
                elif item.get("type") == "text" and item.get("text"):
                    texts.append(item["text"])
    if block:
        _flush_block(block, *slot(frames, current, None))
    records = []
    for key in order:
        calls, texts = frames.get(key, ([], []))
        if not (calls or texts):
            calls, texts = legacy.get(key, ([], []))
        records.append({"id": key, "parent_tool_use_id": parents[key],
                        "tool_calls": calls, "texts": texts})
    return records


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
# hold raw lines themselves; messages reads decoded events as one
# record per assistant message (charter replay's transcript), or is
# None for a harness with no reader yet. Keys are pinned to
# eval_schema.HARNESSES, the vocabulary owner, by test.
Harness = namedtuple("Harness",
                     ("binary", "command", "invocation", "detect", "decode",
                      "messages"))

HARNESSES = {
    "claude": Harness("claude", _claude_command, _claude_invocation,
                      detect_fired, cli.decode_events, claude_messages),
    "omp": Harness("omp", _omp_command, _omp_invocation,
                   detect_omp_fired, cli.decode_events, None),
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


def score_case(case, fired_counts, runs, threshold, errors=0):
    """Score one case from its Counter of fired slugs ('none' for None).

    runs counts observations actually made; errors counts runs that
    failed before producing one. A failed run is not an observation, so
    it is absent from fired_counts and cannot be mistaken for the router
    declining to fire — which for a distractor case would otherwise score
    as correct. A case whose runs all failed has nothing to score and
    does not pass.
    """
    expected = case["expected"] or "none"
    correct_rate = fired_counts.get(expected, 0) / runs if runs else 0.0
    return {
        "id": case["id"],
        "kind": case["kind"],
        "expected": case["expected"],
        "query": case["query"],
        "fired": dict(fired_counts),
        "runs": runs,
        "errors": errors,
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
        # A case whose every run errored contributes no row: it holds no
        # observations, and an empty row prints as a bare heading.
        if not r["fired"]:
            continue
        expected = r["expected"] or "none"
        row = confusion.setdefault(expected, {})
        for fired, count in r["fired"].items():
            row[fired] = row.get(fired, 0) + count

    return {
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r["pass"]),
            "failed": sum(1 for r in results if not r["pass"]),
            # .get keeps records written before this field readable.
            "errors": sum(r.get("errors", 0) for r in results),
            "by_kind": bucket(results, lambda r: r["kind"]),
            "by_skill": bucket(results, lambda r: r["expected"] or "none"),
        },
        "confusion": confusion,
    }


def _ratio(numerator, denominator):
    """None when the denominator is zero: undefined, not measured-as-0."""
    return numerator / denominator if denominator else None


def skill_metrics(confusion):
    """Per-skill precision/recall/F1 from summarize()'s confusion dict.

    A pure second pass over already-recorded counts (never a re-run).
    Rows are expected, columns fired; "none" is the negative class, so it
    is never itself a skill. For skill S: tp = confusion[S][S], fp = S
    fired under any other expected row, fn = every other fire in S's row
    (including "none" — an under-trigger). Zero-denominator contract:
    precision is None when S never fired, recall is None when S was never
    expected, F1 is None when either is None, and 0.0 when both are 0.0.
    """
    skills = (set(confusion)
              | {fired for row in confusion.values() for fired in row})
    skills.discard("none")
    metrics = {}
    for skill in sorted(skills):
        row = confusion.get(skill, {})
        tp = row.get(skill, 0)
        fn = sum(row.values()) - tp
        fp = sum(r.get(skill, 0) for expected, r in confusion.items()
                 if expected != skill)
        precision = _ratio(tp, tp + fp)
        recall = _ratio(tp, tp + fn)
        if precision is None or recall is None:
            f1 = None
        else:
            f1 = _ratio(2 * precision * recall, precision + recall) or 0.0
        metrics[skill] = {"tp": tp, "fp": fp, "fn": fn, "precision":
                          precision, "recall": recall, "f1": f1}
    return metrics


def _fmt(value):
    return "n/a" if value is None else f"{value:.3f}"


def metrics_report(output, kind=None):
    """Report lines for a recorded results dict, optionally one kind only.

    The confusion matrix is rebuilt through summarize() from the selected
    per-case results, so a kind filter (e.g. near-miss) never needs a
    field the record does not already hold. Micro recall — skill-expected
    runs that fired the expected skill — is the single trackable number.
    """
    results = [r for r in output["results"]
               if kind is None or r["kind"] == kind]
    metrics = skill_metrics(summarize(results)["confusion"])
    lines = [f"kind: {kind or 'all'} ({len(results)} case(s))"]
    tp = sum(m["tp"] for m in metrics.values())
    expected = tp + sum(m["fn"] for m in metrics.values())
    if expected:
        lines.append(f"micro recall: {tp}/{expected} = "
                     f"{_fmt(tp / expected)}")
    else:
        lines.append("micro recall: n/a (no skill-expected runs)")
    for skill, m in metrics.items():
        lines.append(f"  {skill}: tp={m['tp']} fp={m['fp']} fn={m['fn']} "
                     f"precision={_fmt(m['precision'])} "
                     f"recall={_fmt(m['recall'])} f1={_fmt(m['f1'])}")
    return lines


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
        errors_by_case = {}
        done = 0
        for future in as_completed(future_to_case):
            case_id = future_to_case[future]
            counts = fired_by_case.setdefault(case_id, Counter())
            errors_by_case.setdefault(case_id, 0)
            try:
                fired = future.result()
            except Exception as err:
                # Not an observation: a crashed run says nothing about
                # what the router would have done, and bucketing it as
                # "none" would both score it and enter it into the
                # confusion matrix as a fire that never happened.
                print(f"warning: run for {case_id!r} failed: {err}",
                      file=sys.stderr)
                errors_by_case[case_id] += 1
            else:
                counts[fired or "none"] += 1
            done += 1
            print(f"progress: {done}/{len(future_to_case)} runs",
                  file=sys.stderr, end="\r")
    print(file=sys.stderr)

    results = [
        score_case(case, fired_by_case.get(case["id"], Counter()),
                   sum(fired_by_case.get(case["id"], Counter()).values()),
                   threshold, errors_by_case.get(case["id"], 0))
        for case in cases
    ]
    return {"results": results, **summarize(results)}


def record(output, results_dir):
    """Write a dated results file; eval_schema owns the recording."""
    return eval_schema.write_snapshot(output, results_dir, "trigger",
                                      harness=output.get("harness"))


def print_report(output):
    for r in output["results"]:
        status = "PASS" if r["pass"] else "FAIL"
        fired = ", ".join(f"{k}x{v}" for k, v in sorted(r["fired"].items()))
        # A case scored on fewer runs than were launched says so on its
        # own line: the surviving runs are not the whole measurement.
        lost = f" errors={r['errors']}" if r.get("errors") else ""
        print(f"  [{status}] {r['id']}: expected={r['expected'] or 'none'} "
              f"fired=[{fired}]{lost}", file=sys.stderr)
    summary = output["summary"]
    print(f"trigger eval: {summary['passed']}/{summary['total']} passed",
          file=sys.stderr)
    if summary.get("errors"):
        print(f"warning: {summary['errors']} run(s) failed and were not "
              f"scored — this eval measured less than it launched",
              file=sys.stderr)
    print("confusion (expected -> fired):", file=sys.stderr)
    for expected, row in sorted(output["confusion"].items()):
        cells = ", ".join(f"{k}: {v}" for k, v in sorted(row.items()))
        print(f"  {expected}: {cells}", file=sys.stderr)


def _is_trigger_result(r):
    """The fields summarize() and metrics_report() read off one result."""
    return (isinstance(r, dict) and "pass" in r
            and isinstance(r.get("kind"), str)
            and (r.get("expected") is None or isinstance(r["expected"], str))
            and isinstance(r.get("fired"), dict)
            and all(isinstance(n, int) for n in r["fired"].values())
            and isinstance(r.get("errors", 0), int))


def load_results(path):
    """(output, problems) for a --metrics results file: a recorded trigger
    snapshot, read through cli.read_file (ADR-0075) and shape-checked
    once, here. A charter snapshot, an array, or an object without
    results is a problem, never a traceback (#746)."""
    output, problem = cli.read_file(path, str(path), dict)
    if output is None:
        return None, [problem or f"missing {path}"]
    results = output.get("results")
    if not isinstance(results, list):
        return None, [f"{path} has no results list"]
    problems = [f"{path} result #{n} is not a trigger result"
                " (fired, kind, expected, pass)"
                for n, r in enumerate(results) if not _is_trigger_result(r)]
    return (None, problems) if problems else (output, [])


def print_metrics(path, kind):
    """Print metrics_report() for one recorded results file; never writes."""
    output, problems = load_results(path)
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1
    print(f"{path.name} (harness: {output.get('harness') or 'claude'})")
    for line in metrics_report(output, kind):
        print(line)
    return 0


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
    parser.add_argument("--metrics", metavar="RESULTS_FILE", default=None,
                        help="run nothing: print per-skill precision/recall/"
                             "F1 derived from an already-recorded results "
                             "file (read-only)")
    parser.add_argument("--kind", default=None,
                        help="with --metrics, only cases of this kind "
                             "(e.g. near-miss)")
    args = parser.parse_args()

    if args.metrics:
        return print_metrics(Path(args.metrics), args.kind)

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
