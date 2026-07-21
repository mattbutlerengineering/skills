"""cli seam tests (ADR-0037): the failure vocabulary and the one-line
detail formatter, asserted at the seam's own interface. The caller
suites (label_sync, validator, budget_guard) keep testing their
composition — problem-string labels around a failing runner — without
each re-proving what detail() does.
"""
import subprocess
import unittest

import cli


class TestDetail(unittest.TestCase):
    def test_last_stderr_line_when_the_command_ran(self):
        err = subprocess.CalledProcessError(
            1, ["gh", "issue", "list"],
            stderr="warning: something\nGraphQL: rate limited\n")
        self.assertEqual(cli.detail(err), "GraphQL: rate limited")

    def test_the_os_error_when_the_binary_is_missing(self):
        err = FileNotFoundError(2, "No such file or directory: 'gh'")
        self.assertEqual(cli.detail(err), str(err))

    def test_empty_stderr_falls_back_to_the_error(self):
        err = subprocess.CalledProcessError(1, ["git", "push"], stderr="  \n")
        self.assertEqual(cli.detail(err), str(err))


class TestFailureVocabulary(unittest.TestCase):
    def test_covers_ran_and_failed_and_never_ran(self):
        # The two ways a shell-out goes wrong; callers catch CLI_FAILURES
        # and never a bare Exception.
        self.assertTrue(issubclass(subprocess.CalledProcessError,
                                   cli.CLI_FAILURES))
        self.assertTrue(issubclass(FileNotFoundError, cli.CLI_FAILURES))
        self.assertFalse(issubclass(ValueError, cli.CLI_FAILURES))


class TestRunner(unittest.TestCase):
    def test_a_missing_binary_raises_into_the_vocabulary(self):
        run = cli.runner("definitely-not-a-binary-xyzzy")
        with self.assertRaises(cli.CLI_FAILURES):
            run(["--version"])

    def test_a_real_run_returns_the_completed_process(self):
        run = cli.runner("true")
        self.assertEqual(run([]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
