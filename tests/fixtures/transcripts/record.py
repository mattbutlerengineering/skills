#!/usr/bin/env python3
"""Record a real claude -p stream-json transcript for detection pinning.

The project layout, flags, detector, and line decode come from the
runner's own harness adapter (trigger_eval.HARNESSES["claude"],
ADR-0038, ADR-0045), so the recording and run_single_query cannot
drift — this script adds only the tee of every raw stdout line to
<name>.jsonl in this directory.
Like the runner, it stops as soon as the detector decides, then writes
the outcome, query, date, CLI version, and invocation facts into
provenance.json. See README.md here for when to re-record; transcripts
are never edited by hand.

Usage (from the repo root, with an authenticated claude CLI):
  python3 tests/fixtures/transcripts/record.py skill-fires "<query>"
  python3 tests/fixtures/transcripts/record.py no-fire "<query>"
"""
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

import cli  # noqa: E402
from trigger_eval import HARNESSES, load_descriptions  # noqa: E402

ADAPTER = HARNESSES["claude"]

# Fixed so the committed transcripts' tool names are reproducible; the
# replay test rebuilds name_to_slug from provenance.json's copy of this.
RUN_ID = "pinned01"


def record(name, query):
    descriptions = load_descriptions(ROOT / "skills")
    name_to_slug = {f"{slug}-skill-{RUN_ID}": slug for slug in descriptions}
    # model=None, isolate=True: the same invocation the eval runner uses
    # (and provenance.json records below)
    project_dir, cmd = ADAPTER.invocation(query, descriptions, RUN_ID,
                                          None, True)
    env = cli.child_env()
    lines = []
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, cwd=project_dir,
                               env=env, text=True)

    def teed_lines():
        for line in process.stdout:
            lines.append(line.rstrip("\n"))
            yield line

    try:
        fired = ADAPTER.detect(ADAPTER.decode(teed_lines()), name_to_slug)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()
        shutil.rmtree(project_dir, ignore_errors=True)

    (HERE / f"{name}.jsonl").write_text("\n".join(lines) + "\n",
                                        encoding="utf-8")
    prov_path = HERE / "provenance.json"
    provenance = (json.loads(prov_path.read_text(encoding="utf-8"))
                  if prov_path.is_file()
                  else {"run_id": RUN_ID, "transcripts": {}})
    provenance["transcripts"][name] = {
        "query": query,
        "fired": fired,
        "recorded": datetime.date.today().isoformat(),
        "cli_version": cli.version("claude"),
        # invocation facts, mirroring what trigger-eval results record
        "model": None,
        "isolated_settings": True,
    }
    prov_path.write_text(json.dumps(provenance, indent=2) + "\n",
                         encoding="utf-8")
    print(f"{name}: fired={fired!r}, {len(lines)} lines recorded")
    return fired


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 1
    record(sys.argv[1], sys.argv[2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
