"""The factory tools' shared CLI contract, tested once.

Every tool's main(argv) follows the same convention (ADR-0021 adapter
discipline): print label-prefixed problems and a summary line, return
0/1/2, never raise. Seven suites each carried a redirect_stdout capture
helper and an unrecognized-argv usage test; the capture and the usage
pin live here, while the per-tool wiring (env dicts, injected runners)
stays in each suite's run_cli.
"""
import contextlib
import io


def capture(main, *args, **kwargs):
    """(exit code, captured stdout) of one main(...) call."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main(*args, **kwargs)
    return code, out.getvalue()


class CliContract:
    """Mixin for a TestCase: an argv the tool does not recognize prints
    usage (carrying `usage_fragment`) and exits 2. Subclasses define
    run_cli(argv) -> (code, stdout) with their own stubs injected, set
    usage_fragment, and override bad_argv when the tool's unrecognized
    input is something other than a bogus subcommand (wrong arity, an
    unknown flag)."""
    usage_fragment = None
    bad_argv = ("nonsense",)

    def test_unrecognized_argv_prints_usage_and_exits_2(self):
        code, out = self.run_cli(list(self.bad_argv))
        self.assertEqual(code, 2)
        self.assertIn(self.usage_fragment, out)
