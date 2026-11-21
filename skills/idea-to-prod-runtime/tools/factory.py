#!/usr/bin/env python3
"""factory: the one front door over the root tools' CLI legs
(issue #237). Every root module that carries a CLI is invoked by
filename; this is the index that did not exist and a dispatcher over the
mains that already do. How many there are is VERBS' to say and
`factory.py help` prints them — a number written here would be a second
owner, and the one that used to be here drifted three behind.

A ROUTER, NOT A SEAM: every verb delegates to a module's main() and the
router owns no knowledge of its own. The verb IS the module's name
(underscores hyphenated) — one vocabulary, not two; the index line IS
the module's own docstring summary sentence, read at print time; and
tests/test_factory_cli.py pins the verb table to a mechanical scan of
the CLI-bearing root modules, so adding or retiring a tool breaks the
build until the table follows. Any logic that landed here would be logic
that stopped being testable where it lives now.

  python3 tools/factory.py <verb> [args...]   delegate: args pass through
                                        verbatim (`factory.py gates
                                        --selftest` is `gates.py
                                        --selftest`)
  python3 tools/factory.py help               the verb index

Verbs whose main() takes no arguments (lint) refuse extras
rather than dropping them silently.
`cli.py` is the external-CLI/harness-IO seam (ADR-0037/0040/0042), which
is why this file is not called that.
"""
import importlib
import re
import sys

# verb -> (module, calling convention). Pinned derived, never grown by
# hand alone: test_factory_cli asserts one verb per CLI-bearing root
# module and that each verb is its module's name. Conventions: "argv"
# mains take argv[1:]-shaped args, "bare" mains have no argv slot at all
# — a main whose slot merely carries a default must still be routed
# "argv", or calling it bare leaves it reading THIS process's sys.argv.
VERBS = {
    "adr-status": ("adr_status", "argv"),
    "assembly-line": ("assembly_line", "argv"),
    "assembler": ("assembler", "argv"),
    "board": ("board", "argv"),
    "budget-guard": ("budget_guard", "argv"),
    "charter-replay": ("charter_replay", "argv"),
    "conductor": ("conductor", "argv"),
    "cost-report": ("cost_report", "argv"),
    "dashboard": ("dashboard", "argv"),
    "decompose-grade": ("decompose_grade", "argv"),
    "decompose-lessons": ("decompose_lessons", "argv"),
    "decompose-signals": ("decompose_signals", "argv"),
    "eval-trends": ("eval_trends", "argv"),
    "factory-init": ("factory_init", "argv"),
    "fast-path": ("fast_path", "argv"),
    "gate-digest": ("gate_digest", "argv"),
    "gates": ("gates", "argv"),
    "handoff": ("handoff", "argv"),
    "kb": ("kb", "argv"),
    "label-sync": ("label_sync", "argv"),
    "launch-demo": ("launch_demo", "argv"),
    "lint": ("lint", "bare"),
    "md-claims": ("md_claims", "argv"),
    "npx-bundle": ("npx_bundle", "argv"),
    "one-owner": ("one_owner", "argv"),
    "pr-body-preflight": ("pr_body_preflight", "argv"),
    "reap-worktrees": ("reap_worktrees", "argv"),
    "rejection-mining": ("rejection_mining", "argv"),
    "reviewer-verdict": ("reviewer_verdict", "argv"),
    "run-tests": ("run_tests", "argv"),
    "size-band-calibration": ("size_band_calibration", "argv"),
    "standards-index": ("standards_index", "argv"),
    "svg-check": ("svg_check", "argv"),
    "sweeps": ("sweeps", "argv"),
    "trace": ("trace", "argv"),
    "trigger-eval": ("trigger_eval", "argv"),
    "validator": ("validator", "argv"),
    "voice-grade": ("voice_grade", "argv"),
    "work-queue": ("work_queue", "argv"),
}


# A provenance parenthetical — (PRD-0001; ADR-0032 ...), (feature:x),
# (faster-sdlc #903) — which the index drops: it says where a tool came
# from, not what it does.
_CITATION = re.compile(r"\s*\((?=[^()]*(?:ADR-|PRD-|WO-|feature:|#\d))[^()]*\)")
_SENTENCE = re.compile(r"(.+?\.)(?:\s|$)")
SUMMARY_LIMIT = 100


def summary(doc, names):
    """A docstring's index line: the first sentence of its first
    paragraph (not its first physical line, which wraps mid-phrase),
    citations dropped, a leading `<name>: ` that repeats the verb or
    module dropped, and anything still over SUMMARY_LIMIT cut at its
    first ` — ` clause, else at a word with an ellipsis."""
    paragraph = []
    for line in (doc or "").strip().splitlines():
        if not line.strip():
            break
        paragraph.append(line.strip())
    text = _CITATION.sub("", " ".join(paragraph))
    found = _SENTENCE.match(text)
    line = found.group(1) if found else text
    for name in names:
        for sep in (": ", " — ", " - "):
            if line.lower().startswith(name.lower() + sep):
                line = line[len(name) + len(sep):]
                break
    if len(line) > SUMMARY_LIMIT and " — " in line:
        line = line.split(" — ")[0].rstrip(" ,;:") + "."
    if len(line) > SUMMARY_LIMIT:
        line = line[:SUMMARY_LIMIT].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return line[:1].upper() + line[1:]


def index():
    """The verb index, each line the module's own docstring summary
    (summary()) — read from the module at print time, never restated
    here where it would drift."""
    width = max(len(verb) for verb in VERBS)
    lines = ["the factory's tools, one verb each:", ""]
    for verb, (module_name, _) in sorted(VERBS.items()):
        doc = importlib.import_module(module_name).__doc__
        line = summary(doc, (verb, module_name, f"{module_name}.py"))
        lines.append(f"  {verb:<{width}}  {line}".rstrip())
    lines += ["", "python3 tools/factory.py <verb> [args...] — args pass"
              " through verbatim"]
    return "\n".join(lines)


def main(argv):
    if not argv:
        print(__doc__.strip())
        return 2
    verb, rest = argv[0], argv[1:]
    if verb in ("help", "--help", "-h"):
        print(index())
        return 0
    if verb not in VERBS:
        print(f"factory: unknown verb {verb!r} — `python3 tools/factory.py"
              " help` lists what exists")
        return 2
    module_name, style = VERBS[verb]
    module = importlib.import_module(module_name)
    if style == "bare":
        if rest in (["-h"], ["--help"]):
            print(f"usage: python3 tools/factory.py {verb} (takes no arguments)")
            return 0
        if rest:
            print(f"factory: {verb} takes no arguments"
                  f" (got {' '.join(rest)!r})")
            return 2
        return module.main()
    return module.main(rest)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
