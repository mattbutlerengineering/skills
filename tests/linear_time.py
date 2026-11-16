"""The one way a suite pins a linear-time claim (#1794).

An absolute wall-clock bound measures the machine, not the algorithm: two
such pins went red under a loaded full suite on a docs-only diff, and
passed when re-run alone. Growth does not move with load: time F at
input sizes N and FACTOR·N, keep the best of REPEATS runs of each (load
only ever adds time, so the minimum is the least disturbed sample), and
compare. The clock is process CPU time, not wall time: a preempted
process keeps its wall clock running, and the longer large-input run is
preempted more often, which inflated the ratio past the limit (28x, 41x)
under three concurrent suites (#2026). Linear work grows by about FACTOR; quadratic by about FACTOR².

`growth` returns that ratio; `GROWTH_LIMIT` sits between the two at the
default FACTOR, twice the linear ratio and half the quadratic one.
"""
import time

FACTOR = 4
REPEATS = 5
GROWTH_LIMIT = 8.0


def _best(fn, arg, repeats):
    samples = []
    for _ in range(repeats):
        started = time.process_time()
        fn(arg)
        samples.append(time.process_time() - started)
    return min(samples)


def growth(fn, make_input, size, factor=FACTOR, repeats=REPEATS):
    """How much FN's best run time grows when MAKE_INPUT(SIZE)'s size is
    multiplied by FACTOR."""
    small, large = make_input(size), make_input(size * factor)
    return _best(fn, large, repeats) / _best(fn, small, repeats)
