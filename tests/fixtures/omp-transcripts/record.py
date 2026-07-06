#!/usr/bin/env python3
"""Record a real omp -p --mode json transcript for detection pinning.

Mirrors the trigger-eval runner's omp invocation — the same flags, env
strip, and isolated project layout as run_single_query with
harness="omp" (keep them in sync when the runner's invocation changes;
nothing pins the two) — while teeing every raw stdout line to
<name>.jsonl in this directory. Like the runner, it stops as soon as
detect_omp_fired decides, then writes the outcome, query, date, CLI
version, and invocation facts into provenance.json. See README.md here
for when to re-record; transcripts are never edited by hand.

Usage (from the repo root, with an authenticated omp CLI):
  python3 tests/fixtures/omp-transcripts/record.py skill-fires "<query>"
  python3 tests/fixtures/omp-transcripts/record.py no-fire "<query>"
"""
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

from trigger_eval import (build_omp_project_dir, cli_version,  # noqa: E402
                          detect_omp_fired, load_descriptions)

# Fixed so the committed transcripts' skill names are reproducible; the
# replay test rebuilds name_to_slug from provenance.json's copy of this.
RUN_ID = "pinned01"

# Pinned so the recording doesn't depend on the local omp config's
# default model; recorded alongside the transcript in provenance.json.
MODEL = "claude-sonnet-5"


def record(name, query):
    descriptions = load_descriptions(ROOT / "skills")
    name_to_slug = {f"{slug}-skill-{RUN_ID}": slug for slug in descriptions}
    project_dir = build_omp_project_dir(descriptions, RUN_ID)
    cmd = ["omp", "--mode", "json", "-p",
           "--no-session", "--no-extensions", "--no-rules",
           "--skills", f"*-skill-{RUN_ID}",
           "--model", MODEL,
           query]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    lines = []
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, cwd=project_dir,
                               env=env, text=True)

    def teed_events():
        for line in process.stdout:
            lines.append(line.rstrip("\n"))
            stripped = line.strip()
            if not stripped:
                continue
            try:
                yield json.loads(stripped)
            except json.JSONDecodeError:
                continue

    try:
        fired = detect_omp_fired(teed_events(), name_to_slug)
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
        "cli_version": cli_version("omp"),
        # invocation facts, mirroring what trigger-eval results record
        "harness": "omp",
        "model": MODEL,
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
