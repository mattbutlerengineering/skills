"""A completed non-review run whose runner dies right after its `run`
row (#2160): the stall its own expected-output checks decided (no
pr-body.md, a briefed breakdown row left unchecked) is written with
that run row under the one ledger lock (architecture.md, Worker runner
step 7: it "appends `run` and `state` rows"), so no ledger ever holds a
completed run that skipped its stall, and `next` never advances it.
"""
import sys
import unittest
import unittest.mock
from pathlib import Path

import conductor
import conductor_flow as flow
import conductor_next
import conductor_run

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_flow import launch, ran  # noqa: E402
from test_conductor_run import (BASE, NOW, Git, Harness,  # noqa: E402
                                RunCase, pr_body)


class Died(Exception):
    """The runner's process ending before its next ledger write."""


def dies_after_the_run_row(real):
    """An `append` that raises on every call after the one that wrote a
    `run` row, as a runner killed right after that write would."""
    wrote_run = []

    def append(root, batch, build):
        if wrote_run:
            raise Died()

        def recording(rows):
            written, problems = build(rows)
            batch_rows = written if isinstance(written, list) \
                else [written]
            if not problems and any(row and row["kind"] == "run"
                                    for row in batch_rows):
                wrote_run.append(True)
            return written, problems
        return real(root, batch, recording)
    return append


class TestDeadRunnerOutput(RunCase):
    def die_after_run_row(self, item, step, harness, **kwargs):
        dying = dies_after_the_run_row(conductor.append)
        with unittest.mock.patch.object(conductor_run, "append", dying), \
                unittest.mock.patch.object(flow, "append", dying):
            try:
                self.run_step(item, step, harness, **kwargs)
            except Died:
                pass
        self.rows, _ = conductor.load(self.root, "b1")

    def test_a_run_without_pr_body_is_stalled_with_its_run_row(self):
        self.die_after_run_row("#12", "spec", Harness())
        self.assertEqual([r["kind"] for r in self.rows[-3:]],
                         ["run", "state", "ask"])
        self.assertEqual((self.rows[-2]["reason"], self.rows[-2]["cause"]),
                         ("the run completed but left no pr-body.md",
                          "agent-failed"))

    def test_a_build_leaving_its_row_unchecked_never_advances(self):
        path = "docs/features/x/breakdown.md"
        git = Git(self.tmp.name, changed=f"{path}\n", shows={
            f"conductor/b1-13:{path}": "- [ ] **WO-0171** b\n"})
        rows = BASE + [launch("#13", "planned", "spec"), ran("#13", "spec")]
        self.die_after_run_row("#13", "build", Harness(act=pr_body),
                               git=git, rows=rows)
        self.assertEqual(self.rows[-2]["reason"],
                         "the build run completed but left WO-0171"
                         " unchecked")
        ready, writes, problems = flow.survey(
            self.rows, NOW, 3, lambda pid: False,
            {"#13": {"gate_blobs": {}, "unchecked": 1}})
        self.assertEqual((problems, writes), ([], []))
        self.assertNotIn("#13", [entry["item"] for entry in ready])
        self.assertEqual(conductor_next.next_ask(self.rows)["ask_kind"],
                         "stall")


if __name__ == "__main__":
    unittest.main()
