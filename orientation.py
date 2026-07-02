#!/usr/bin/env python3
"""Command-line adapter over the protocol module: given a run directory,
which stage is next? (`python3 orientation.py docs/`.)

The decision table itself lives in protocol.py; the router skill follows
the same table as prose in docs/pipeline-protocol.md.
"""
import sys
from pathlib import Path

from protocol import next_stage


def main(argv):
    if len(argv) != 2:
        print("usage: orientation.py <run-directory>", file=sys.stderr)
        return 2
    run_dir = Path(argv[1])
    if not run_dir.is_dir():
        print(f"orientation: not a directory: {run_dir}", file=sys.stderr)
        return 2
    print(next_stage(run_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
