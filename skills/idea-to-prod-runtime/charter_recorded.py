"""The charter replay's offline half: a recorded transcript set, loaded
once and scored with no model and no cost.

`charter_replay.py --transcripts FILE` is the only caller. The file is
user input named on the command line, so it is read through
cli.read_file (ADR-0075) and its shape is checked here, once: a wrong
file is a list of problem strings and exit 1, never a traceback (#746),
and nothing downstream (command_text, transcript_text, replay_problem,
score_case) has to defend against it. It lives apart from the live
runner only to keep charter_replay.py under the 800-line file budget.
"""

import cli


def _transcript_problems(transcript, where):
    """The shape command_text, transcript_text and replay_problem read."""
    if not isinstance(transcript, dict):
        return [f"{where} is not a transcript object"]
    calls = transcript.get("tool_calls", [])
    return ([f"{where} tool_calls is not a list of objects"]
            if not isinstance(calls, list)
            or not all(isinstance(c, dict) for c in calls) else []) + (
        [f"{where} text is not a string"]
        if not isinstance(transcript.get("text") or "", str) else [])


def load_transcripts(path, control):
    """(transcripts, problems) for the --transcripts file: {case_id:
    transcript}, or {case_id: {intact, degraded}} under --control. Read
    through cli.read_file (ADR-0075) and shape-checked once, here, so a
    wrong file is a problem, never a traceback (#746). Any problem means
    the file is unusable and transcripts is None."""
    data, problem = cli.read_file(path, path, dict)
    if data is None:
        return None, [problem or f"missing {path}"]
    problems = []
    for case_id, entry in data.items():
        where = f"{path} {case_id!r}"
        if not control:
            problems += _transcript_problems(entry, where)
        elif not isinstance(entry, dict):
            problems.append(
                f"{where} is not an object of intact/degraded transcripts")
        else:
            for arm in ("intact", "degraded"):
                if arm in entry:
                    problems += _transcript_problems(entry[arm],
                                                     f"{where} {arm}")
    return (None, problems) if problems else (data, [])


def recorded_runner(transcripts):
    """Score a recorded transcript set — the offline half, no model, no cost."""
    def run(case):
        return transcripts.get(case["id"],
                               {"tool_calls": [], "text": "",
                                "error": "no recorded transcript"})
    return run


def recorded_arm(pairs, arm):
    """One arm of a recorded control set, {case_id: {arm: transcript}}.
    A missing arm falls through to recorded_runner's error transcript."""
    return recorded_runner({case_id: pair[arm]
                            for case_id, pair in pairs.items() if arm in pair})
