#!/usr/bin/env python3
"""handoff: composes the structured handoff a hard-stopped run leaves behind
(ADR-0034) — why it stopped, which acceptance criteria are done, which
remain, and how to resume. Pure compose function, no IO: callers decide
where the text goes (post_handoff, or their own gh/issue call).

Deliberately takes STRUCTURED fields — short criterion strings the run
itself tracked, never a raw issue or PR body. This mirrors the
prompt-injection boundary assembler.assemble_prompt draws (ADR-0032):
compose()'s signature is the boundary, not a sanitizer bolted on after
the fact.

  python3 handoff.py <wo> <reason> <done_csv> <remaining_csv> <resume>
        Compose and print a handoff for <wo>. <done_csv>/<remaining_csv>
        are comma-separated acceptance criteria (empty string for none), a
        quick hand check outside the agent loop.
"""
import sys


def _bullets(items):
    return [f"- {item}" for item in items] if items else ["- (none)"]


def compose(wo, reason, done, remaining, resume):
    """The handoff text for `wo`'s stopped run: `reason` it stopped (last
    state, may include spend — e.g. budget_guard.decide's reason string),
    `done`/`remaining` sequences of short acceptance-criterion strings, and
    `resume` instructions for whoever (human or next dispatch) picks it up.
    Deterministic text, easy to assert on and easy to skim."""
    lines = [f"## Handoff: {wo}", "", reason.strip(), "", "### Done"]
    lines.extend(_bullets(done))
    lines += ["", "### Remaining"]
    lines.extend(_bullets(remaining))
    lines += ["", "### Resume", resume.strip()]
    return "\n".join(lines) + "\n"


def post_handoff(text, post=print):
    """Hand the composed text to `post` (default: print to stdout, the
    fallback for a local or hand run). Decouples "where a handoff goes"
    (a gh issue comment, in the real workflow) from "what it says"
    (compose), so tests can capture it without touching the network."""
    post(text)


def main(argv):
    if len(argv) != 5:
        print(__doc__.strip())
        return 2
    wo, reason, done_csv, remaining_csv, resume = argv
    done = [item for item in done_csv.split(",") if item]
    remaining = [item for item in remaining_csv.split(",") if item]
    post_handoff(compose(wo, reason, done, remaining, resume))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
