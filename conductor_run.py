#!/usr/bin/env python3
"""conductor_run: the Worker runner, `conductor.py run <batch> <item>
<step>` (PRD-0013, WO-0158), split from conductor.py by capability
(breakdown assumption 6). One metered, policy-bound headless harness run
per step of one item, in that item's own worktree.

In order: launch (a state row carrying the run id and this runner's
pid), compose the brief and every harness flag, run under
cli.harness_run with the size's wall-clock limit, keep the result event
as runs/<run_id>.json, meter it with cli.read_execution, commit one
spend row on the item branch, push it (never forced), open or update its
PR from the Worker's uncommitted pr-body.md, and append the run's one
`run` row. Any outcome but a completed run with its expected output
queues a stall ask; nothing retries. The Owner's 2026-10-10 answers
(breakdown.md Notes) fix the branch names, tool list and defaults used.
"""
import json
import os
from pathlib import Path

import conductor_flow as flow
import cost_ledger
import factory_config
from assembler import PR_BODY_FILE
from cli import CLI_FAILURES, child_env, detail, gh_read, harness_run, \
    read_execution
from conductor import WORKER_ENV, append, load, stamp
from knowledge_plane import WO_TOKEN
from orientation_pack import orientation_pack
from protocol import read_frontmatter

HARNESS = "claude"
# Fixed for every step (Owner, 2026-10-10): no git push, no gh at all.
ALLOWED_TOOLS = ("Read", "Edit", "Write", "Glob", "Grep",
                 "Bash(python3 *)", "Bash(make *)", "Bash(git add *)",
                 "Bash(git commit *)", "Bash(git status*)",
                 "Bash(git diff*)", "Bash(git log*)")
WORKTREE = ".claude/worktrees/conductor-{batch}-{n}"
RUNS = "docs/factory/batches/{batch}/runs"
CEILING_OUTCOME = {"timeout": "killed:cost-at-ceiling",
                   "unaccounted": "unaccounted:cost-at-ceiling"}
WORKER_WHY = ("a first failure is evidence about the item as often as about"
              " the agent, so nothing retries without your answer")
OBJECTIVES = {
    "spec": ("Drive issue {item}'s run with the autorun skill, as a"
             " {scale}, writing `stop-after: decompose` into its"
             " autorun-brief.md so it stops at the blueprint gate."),
    "build": "Implement {wo} test-first under the implement skill and"
             " check its row off.",
    "verify": "Verify this item's run under the verify skill and write"
              " verification.md.",
    "review": "Review this item's run under the review skill and write"
              " review.md with `verdict: pass` or `verdict: changes` in"
              " its frontmatter. This brief overrides the reviewer"
              " charter's exit: post no comment, apply no label and merge"
              " nothing.",
    "ship": "Prepare this item's release.md under the ship skill and"
            " execute no release step."}


def harness_command(brief, model, effort, ceiling_usd):
    """Every harness flag, composed in this one function: the headless
    CLI is a volatile vendor surface."""
    return [HARNESS, "-p", brief, "--model", model, "--effort", effort,
            "--max-budget-usd", f"{ceiling_usd:.2f}", "--output-format",
            "json", "--allowedTools", *ALLOWED_TOOLS]


def _span(values):
    return (str(values[0]) if len(values) == 1
            else f"{values[0]}-{values[-1]}")


def compose_brief(step, item, item_type, worktree, branch, block, wo,
                  context, issue_body, ceiling):
    """The Worker's brief in its fixed shape. The issue body is an input
    only for a spec step (ADR-0032: owner-authored issues only)."""
    scale = ("maintenance run from capture" if item_type == "fix"
             else "feature run from idea")
    reserved = ", ".join(f"{kind} {_span(values)}"
                         for kind, values in block.items()) or "none"
    inputs = [f"- {context}"] if context else []
    if step == "spec" and issue_body is not None:
        inputs.append(f"- Issue {item}, verbatim:\n\n{issue_body}")
    return "\n".join([
        "## Objective", "",
        OBJECTIVES[step].format(item=item, scale=scale, wo=wo), "",
        "## Output", "",
        f"The stage artifact or code, as commits on {branch}. Write the"
        f" pull request body to {PR_BODY_FILE} at the worktree root and"
        " leave pr-body.md uncommitted.", "",
        "## Tools", "",
        f"Only these: {', '.join(ALLOWED_TOOLS)}. never git push, and"
        " never run any gh command.", "",
        "## Boundaries", "",
        f"Work only in {worktree}. New PRD, ADR and WO ids come only from"
        f" this item's reserved block ({reserved}); if it runs out, stop"
        " and say so. never edit .claude-plugin/plugin.json's version.",
        "",
        "## Context budget", "",
        "The run directory on this branch, and:", *inputs,
        f"Your budget is ${ceiling:.2f}: the dollar ceiling is the whole"
        " context budget.", ""])


def _git(git, args, what):
    try:
        return git(args).stdout, []
    except CLI_FAILURES as err:
        return None, [f"{what} failed: {detail(err)}"]


def _policy(rows, plan, entry, step):
    """(band, model, effort, ceiling) for the step: the plan row's
    snapshot, one band up after a retry-up answer."""
    planned = next(s for s in entry["steps"] if s["step"] == step)
    band, model, effort = planned["band"], planned["model"], \
        planned["effort"]
    states = [r for r in rows if r["kind"] == "state"
              and r["item"] == entry["item"]]
    if states and states[-1]["to"] == "stalled":
        resumed = flow.latest_answer(rows, entry["item"], "stall",
                                      after=rows.index(states[-1]))
        if resumed and resumed["choice"] == "retry-up" \
                and band in flow.BANDS[:-1]:
            band = flow.BANDS[flow.BANDS.index(band) + 1]
            model, _ = factory_config.resolve_model(band, plan["policy"])
            effort, _ = factory_config.resolve_effort(band, plan["policy"])
    return band, model, effort, planned["ceiling_usd"]


def _issue(gh, item):
    result = gh_read(["issue", "view", item[1:], "--json", "title,body"],
                     f"gh issue view {item}", "cd", run=gh, expect=dict)
    return result.value, result.problems


def _work(rows, entry, step, git, gh, batch, worktree):
    """(wo, context, issue body, problems) for the step's inputs."""
    item = entry["item"]
    if step == "spec":
        issue, problems = _issue(gh, item)
        return item, "", (issue or {}).get("body"), problems
    if step != "build":
        return item, "", None, []
    if entry["type"] == "order":
        issue, problems = _issue(gh, item)
        if problems:
            return None, None, None, problems
        found = WO_TOKEN.search(issue.get("title") or "")
        if not found:
            return None, None, None, [f"cd: {item}'s title names no work"
                                      " order"]
        wo, row = found.group(0), issue["title"]
    else:
        pending, problems = flow.unchecked_rows(
            git, flow.item_branch(batch, item))
        if problems:
            return None, None, None, problems
        if not pending:
            return None, None, None, [f"cd: {item} has no unchecked"
                                      " breakdown row to build"]
        row = pending[0]
        found = WO_TOKEN.search(row)
        wo = found.group(0) if found else item
    return wo, f"{row}\n\n{orientation_pack(worktree, wo, row)}", None, []


def worktree_path(git, batch, item):
    """(the item worktree's path under the main checkout, problems)."""
    out, problems = _git(git, ["rev-parse", "--path-format=absolute",
                               "--git-common-dir"], "cd: git rev-parse")
    if problems:
        return None, problems
    return Path(out.strip()).parent / WORKTREE.format(batch=batch,
                                                      n=item[1:]), []


def _worktree(git, batch, item):
    """(the item worktree, problems), created from origin/main by the
    item's first runner."""
    path, problems = worktree_path(git, batch, item)
    if problems:
        return None, problems
    if not path.exists():
        _, problems = _git(git, ["worktree", "add", "-b",
                                 flow.item_branch(batch, item), str(path),
                                 "origin/main"], "cd: git worktree add")
    return path, problems


def _harness(harness, cmd, worktree, minutes, batch):
    """(result event or None, how it ended): completed, timeout,
    missing (no process ever started) or unaccounted (no result)."""
    env = {**child_env(), WORKER_ENV: batch}
    try:
        with harness(cmd, cwd=str(worktree), timeout=minutes * 60,
                     env=env) as events:
            results = [e for e in events
                       if isinstance(e, dict) and e.get("type") == "result"]
            timed_out = events.timed_out
    except OSError as err:
        return None, "missing", str(err)
    if timed_out:
        return None, "timeout", None
    return (results[-1], "completed", None) if results \
        else (None, "unaccounted", None)


def _meter(root, batch, run_id, event, ended, ceiling, model):
    """(tokens, cost, outcome, models reported, stall reason)."""
    if ended == "missing":
        return 0, 0.0, "agent-failed", [], "the harness could not start"
    if event is not None:
        runs = Path(root) / RUNS.format(batch=batch)
        runs.mkdir(parents=True, exist_ok=True)
        kept = runs / f"{run_id}.json"
        kept.write_text(json.dumps(event) + "\n", encoding="utf-8")
        metered, error = read_execution(kept)
        if error is None:
            reported = sorted(event.get("modelUsage") or {})
            if event.get("subtype") == "success" \
                    and not event.get("is_error"):
                return (*metered, "completed", reported, None)
            return (*metered, "agent-failed", reported,
                    f"the Worker run ended {event.get('subtype')}")
        ended = "unaccounted"
    reason = ("the result event could not be metered"
              if ended == "unaccounted" else None)
    return 0, float(ceiling), CEILING_OUTCOME[ended], [], reason


def _deliver(git, gh, worktree, branch, item, batch):
    """Push the item branch (never forced) and open or update its PR from
    pr-body.md. A stall reason on failure, else None."""
    _, problems = _git(git, ["-C", str(worktree), "push", "-u", "origin",
                             branch], f"pushing {branch}")
    if problems:
        return problems[0]
    body = worktree / PR_BODY_FILE
    if not body.is_file():
        return None
    listed = gh_read(["pr", "list", "--head", branch, "--state", "open",
                      "--json", "number"], "gh pr list", run=gh)
    try:
        if listed.problems:
            raise OSError(listed.problems[0])
        if listed.value:
            gh(["api", "-X", "PATCH", "repos/{owner}/{repo}/pulls/"
                f"{listed.value[0]['number']}", "-F", f"body=@{body}"])
        else:
            gh(["pr", "create", "--head", branch, "--base", "main",
                "--title", f"{item}: conductor batch {batch}",
                "--body-file", str(body)])
    except CLI_FAILURES as err:
        return f"opening or updating the PR failed: {detail(err)}"
    return None


def _spend(git, worktree, wo, run_id, model, tokens, cost, outcome, now):
    """Commit the run's one spend row on the item branch. A stall reason
    on failure, else None."""
    cost_ledger.append(worktree, cost_ledger.entry(
        wo, run_id, model, tokens, cost, outcome, now.strftime("%Y-%m-%d")))
    for args in (["add", cost_ledger.COST_LEDGER],
                 ["commit", "-m", f"chore(cost): {run_id}"]):
        _, problems = _git(git, ["-C", str(worktree), *args],
                           f"committing the spend row of {run_id}")
        if problems:
            return problems[0]
    return None


def _verdict(git, worktree, branch):
    """The review.md verdict on the item branch, or None."""
    changed, problems = flow.changed_files(git, branch)
    for path in [] if problems else changed:
        if path.endswith("/review.md") and (worktree / path).is_file():
            fields = read_frontmatter(worktree / path) or {}
            verdict = (fields.get("verdict") or "").strip()
            return verdict if verdict in flow.VERDICTS else None
    return None


def _prepare(root, batch, item, step, git, gh):
    """(context dict, problems): everything decided before launch."""
    rows, problems = load(root, batch)
    if problems:
        return None, problems
    plan = flow.plan_row(rows) or {}
    entry = flow.plan_entry(rows, item)
    if entry is None:
        return None, [f"cd: {item} is not an item of this batch's plan"]
    if step not in [s["step"] for s in entry["steps"]]:
        return None, [f"cd: {item} has no {step} step"]
    problems = flow.transition_problems(rows, item, step, {})
    if problems:
        return None, problems
    worktree, problems = _worktree(git, batch, item)
    if problems:
        return None, problems
    wo, context, body, problems = _work(rows, entry, step, git, gh, batch,
                                        worktree)
    if problems:
        return None, problems
    seq = 1 + sum(1 for r in rows if r["kind"] == "state" and r["item"]
                  == item and r["to"] == step and "run_id" in r)
    block = {r["what"]: r["values"] for r in rows
             if r["kind"] == "reserve" and r["item"] == item}
    return {"rows": rows, "plan": plan, "entry": entry, "wo": wo,
            "context": context, "body": body, "worktree": worktree,
            "block": block,
            "run_id": f"conductor-{batch}-{item[1:]}-{step}-{seq}"}, []


def run_step(root, batch, item, step, now, git, gh, harness=harness_run,
             pid=None):
    """(summary, problems): one Worker run. problems only when nothing
    was launched or a ledger write failed; a failed run is a stall."""
    pid = os.getpid() if pid is None else pid
    ctx, problems = _prepare(root, batch, item, step, git, gh)
    if problems:
        return None, problems
    entry, run_id, worktree = ctx["entry"], ctx["run_id"], ctx["worktree"]
    branch = flow.item_branch(batch, item)
    band, model, effort, ceiling = _policy(ctx["rows"], ctx["plan"], entry,
                                           step)
    _, problems = flow.move(root, batch, now, item, step, "launched",
                            run_id=run_id, pid=pid)
    if problems:
        return None, problems
    brief = compose_brief(step, item, entry["type"], worktree, branch,
                          ctx["block"], ctx["wo"], ctx["context"],
                          ctx["body"], ceiling)
    event, ended, _ = _harness(
        harness, harness_command(brief, model, effort, ceiling), worktree,
        flow.WALL_CLOCK_MINUTES[entry["size"]], batch)
    tokens, cost, outcome, reported, stall = _meter(
        root, batch, run_id, event, ended, ceiling, model)
    if ended == "timeout":
        stall = (f"killed at its {flow.WALL_CLOCK_MINUTES[entry['size']]}"
                 "-minute wall-clock limit")
    spent_model = model if model in reported or not reported \
        else reported[0]
    failed = _spend(git, worktree, ctx["wo"], run_id, spent_model, tokens,
                    cost, outcome, now)
    if stall is None and not (worktree / PR_BODY_FILE).is_file():
        stall = "the run completed but left no pr-body.md"
    failed = failed or _deliver(git, gh, worktree, branch, item, batch)
    stall = stall or failed
    charter = next(s["charter"] for s in entry["steps"]
                   if s["step"] == step)
    _, problems = append(root, batch, lambda rows: ({
        "at": stamp(now), "kind": "run",
        "item": item, "step": step, "charter": charter, "band": band,
        "model": model, "models_reported": reported, "effort": effort,
        "run_id": run_id, "pid": pid, "outcome": outcome}, []))
    if problems:
        return None, problems
    if stall is None and step == "review":
        verdict = _verdict(git, worktree, branch)
        if verdict is None:
            stall = "review.md carries no verdict: pass|changes line"
        else:
            _, problems = flow.record_verdict(root, batch, now, item,
                                              verdict, run_id)
    if stall is not None:
        _, problems = flow.queue_stall(root, batch, now, item, stall,
                                       "retry", WORKER_WHY)
    return {"run_id": run_id, "outcome": outcome, "stall": stall}, problems


def run_cli(root, args, now, git, gh, harness):
    if len(args) != 3 or not cost_ledger.ISSUE_KEY.fullmatch(args[1]):
        return None
    batch, item, step = args
    if step not in flow.STEPS:
        return None
    summary, problems = run_step(root, batch, item, step, now, git, gh,
                                 harness=harness or harness_run)
    if summary is not None:
        line = f"cd: run {summary['run_id']} {summary['outcome']}"
        print(line + (f"; stalled: {summary['stall']}"
                      if summary["stall"] else ""))
    return problems
