"""conductor_run._meter keeps the Worker's result event before it meters it.

The write happens after the Worker has run and spent. A failed write (a
full disk, an unwritable tree) used to escape as an OSError and kill the
step before record_spend: the spend was never recorded. It now meters the
way any event it cannot account for is metered: the ceiling is charged,
never a zero, and the reason says so.
"""
import tempfile
import unittest
from pathlib import Path

import conductor_run
from conductor_spend import CEILING_OUTCOME

EVENT = {"type": "result", "subtype": "success", "is_error": False,
         "total_cost_usd": 1.25,
         "usage": {"input_tokens": 10, "output_tokens": 20}}


class TestMeterWithAnUnwritableRunsDirectory(unittest.TestCase):
    def test_the_ceiling_is_charged_not_a_traceback_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            # docs/factory a regular file: the runs directory cannot be
            # made, for a root user too
            (Path(tmp) / "docs").mkdir()
            (Path(tmp) / "docs" / "factory").write_text("", encoding="utf-8")
            metered = conductor_run._meter(
                tmp, "b1", "run-1", EVENT, "completed", 7.5, "m")
        self.assertEqual(metered, (
            0, 7.5, CEILING_OUTCOME["unaccounted"], [],
            "the result event could not be metered"))


if __name__ == "__main__":
    unittest.main()
