#!/usr/bin/env python3
"""factory: the one front door over the root tools' CLI legs
(issue #237). Fourteen root modules carry a CLI and every one is invoked
by filename; this is the index that did not exist and a dispatcher over
the mains that already do.

A ROUTER, NOT A SEAM: every verb delegates to a module's main() and the
router owns no knowledge of its own. The verb IS the module's name
(underscores hyphenated) — one vocabulary, not two; the index line IS
the module's own docstring first line, read at print time; and
tests/test_factory_cli.py pins the verb table to a mechanical scan of
the CLI-bearing root modules, so adding or retiring a tool breaks the
build until the table follows. Any logic that landed here would be logic
that stopped being testable where it lives now.

  python3 factory.py <verb> [args...]   delegate: args pass through
                                        verbatim (`factory.py gates
                                        --selftest` is `gates.py
                                        --selftest`)
  python3 factory.py help               the verb index

Verbs whose main() takes no arguments (lint, trigger-eval) refuse extras
rather than dropping them silently.
`cli.py` is the external-CLI/harness-IO seam (ADR-0037/0040/0042), which
is why this file is not called that.
"""
import importlib
import sys

# verb -> (module, calling convention). Pinned derived, never grown by
# hand alone: test_factory_cli asserts one verb per CLI-bearing root
# module and that each verb is its module's name. Conventions: "argv"
# mains take argv[1:]-shaped args, "bare" mains have no argv slot at all
# — a main whose slot merely carries a default must still be routed
# "argv", or calling it bare leaves it reading THIS process's sys.argv.
VERBS = {
    "assembler": ("assembler", "argv"),
    "board": ("board", "argv"),
    "budget-guard": ("budget_guard", "argv"),
    "charter-replay": ("charter_replay", "argv"),
    "cost-report": ("cost_report", "argv"),
    "dashboard": ("dashboard", "argv"),
    "factory-init": ("factory_init", "argv"),
    "gate-digest": ("gate_digest", "argv"),
    "gates": ("gates", "argv"),
    "handoff": ("handoff", "argv"),
    "label-sync": ("label_sync", "argv"),
    "lint": ("lint", "bare"),
    "one-owner": ("one_owner", "argv"),
    "rejection-mining": ("rejection_mining", "argv"),
    "sweeps": ("sweeps", "argv"),
    "trigger-eval": ("trigger_eval", "bare"),
    "validator": ("validator", "argv"),
    "work-queue": ("work_queue", "argv"),
}


def index():
    """The verb index, each line the module's own docstring first line —
    read from the module at print time, never restated here where it
    would drift."""
    width = max(len(verb) for verb in VERBS)
    lines = ["the factory's tools, one verb each:", ""]
    for verb, (module_name, _) in sorted(VERBS.items()):
        doc = importlib.import_module(module_name).__doc__ or ""
        summary = doc.strip().splitlines()[0] if doc.strip() else ""
        lines.append(f"  {verb:<{width}}  {summary}".rstrip())
    lines += ["", "python3 factory.py <verb> [args...] — args pass"
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
        print(f"factory: unknown verb {verb!r} — `python3 factory.py"
              " help` lists what exists")
        return 2
    module_name, style = VERBS[verb]
    module = importlib.import_module(module_name)
    if style == "bare":
        if rest:
            print(f"factory: {verb} takes no arguments"
                  f" (got {' '.join(rest)!r})")
            return 2
        return module.main()
    return module.main(rest)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
