"""Parallel test runner: one `python3 -m unittest tests.<module>` child per
test module, across a pool of workers (faster-sdlc #903).

`python3 -m unittest discover tests` ran the suite serially: 82.5s on
origin/main 8528b1d at 73% of one core. The modules are independent —
each builds its own fixture tree or temp git repo, and tests/README.md
pins the flat layout — so each runs in its own process. Modules are
scheduled longest-first from tests/timings.json (written by `--record`),
so the slowest module starts first and the wall time approaches the
longest module rather than the sum; without a readable timings file the
order is alphabetical.

The child command is the literal `python3 -m unittest tests.<module>`,
so a module here collects exactly what discover collects there, and the
total printed equals discover's count on the same tree.

Root-only (ADR-0060's rule: mirrored iff a payload tool imports it);
factory_init.product_form respells the root Makefile's line back to the
serial discover command, so stamped repos are unchanged. Stdlib only.
"""
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
import subprocess

TIMINGS = Path("tests") / "timings.json"
# unittest's own summary line, the one fact a child reports about size.
RAN = re.compile(r"^Ran (\d+) tests? in [\d.]+s$", re.MULTILINE)
USAGE = ("usage: python3 run_tests.py [-j N] [--record]\n"
         "  -j N      workers in flight at once (default: os.cpu_count())\n"
         "  --record  rewrite tests/timings.json from this run's timings,"
         " when every module passed")


def discover(root):
    """Every `tests/test_*.py` directly under root, as the module name
    its child is told to run, alphabetical. Helpers carry no `test_`
    prefix and fixture trees sit in subdirectories, so neither is here
    — the same selection discover makes with its default pattern."""
    return [f"tests.{path.stem}"
            for path in sorted((Path(root) / "tests").glob("test_*.py"))]


def load_timings(path):
    """{module: seconds} from a committed timings file; {} when the file
    is absent, undecodable, not an object, or holds a non-numeric value
    — any of which just means the alphabetical fallback."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or not all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in data.values()):
        return {}
    return {module: float(seconds) for module, seconds in data.items()}


def schedule(modules, timings):
    """Longest-first by recorded seconds; an unrecorded module counts as
    0s, so ties and the no-timings case fall back to alphabetical."""
    return sorted(modules, key=lambda m: (-timings.get(m, 0.0), m))


@dataclass(frozen=True)
class Result:
    module: str
    code: int
    output: str
    seconds: float

    @property
    def count(self):
        """The child's test count, or None when it never printed one —
        a crash before unittest's summary, which is a failure too."""
        match = RAN.search(self.output)
        return int(match.group(1)) if match else None

    @property
    def failed(self):
        return self.code != 0 or self.count is None


def spawn_child(cmd, cwd):
    """The real subprocess port: (exit code, stdout and stderr merged),
    stderr merged because unittest writes its report there."""
    process = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True,
                             errors="replace")
    return process.returncode, process.stdout


def run_module(module, spawn, root):
    started = time.monotonic()
    code, output = spawn(["python3", "-m", "unittest", module], root)
    return Result(module, code, output, time.monotonic() - started)


def run_all(modules, spawn, workers, root):
    """Results in schedule order; the pool starts them in that order."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda m: run_module(m, spawn, root), modules))


def record_timings(path, results):
    path.write_text(json.dumps(
        {result.module: round(result.seconds, 3)
         for result in sorted(results, key=lambda r: r.module)},
        indent=2) + "\n", encoding="utf-8")


def parse_args(argv, cpu_count):
    """(workers, record) or None when argv is not this tool's."""
    workers, record, rest = None, False, list(argv)
    while rest:
        flag = rest.pop(0)
        if flag == "--record":
            record = True
        elif flag == "-j" and rest and rest[0].isdigit() and int(rest[0]) > 0:
            workers = int(rest.pop(0))
        else:
            return None
    return workers or cpu_count() or 1, record


def main(argv, spawn=spawn_child, root=None, cpu_count=os.cpu_count):
    """Exit 0 only when every module passed. Each failing module is
    reported as `tests: <module> failed` followed by its own output, so
    the failure reads as it would have under discover; the last line
    carries the total test count in the summary grammar."""
    parsed = parse_args(argv, cpu_count)
    if parsed is None:
        print(USAGE)
        return 2
    workers, record = parsed
    root = Path(root or Path(__file__).resolve().parent)
    started = time.monotonic()
    modules = schedule(discover(root), load_timings(root / TIMINGS))
    results = run_all(modules, spawn, workers, root)
    wall = time.monotonic() - started
    failed = [result for result in results if result.failed]
    for result in failed:
        print(f"tests: {result.module} failed")
        print(result.output, end="" if result.output.endswith("\n") else "\n")
    total = sum(result.count or 0 for result in results)
    print(f"tests: {total} tests across {len(results)} modules in {wall:.1f}s"
          f" on {workers} workers, {len(failed)} problem(s)")
    if record and not failed:
        record_timings(root / TIMINGS, results)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
