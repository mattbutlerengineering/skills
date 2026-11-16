"""migration-script.sh's status handling, run against a fake `npx`."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills" / "prisma-migrations" / "assets" / "migration-script.sh"


def run_script(status_output, status_rc, *args):
    with tempfile.TemporaryDirectory() as tmp:
        npx = Path(tmp) / "npx"
        npx.write_text("#!/bin/sh\ncat <<'EOF'\n%s\nEOF\nexit %d\n"
                       % (status_output, status_rc), encoding="utf-8")
        npx.chmod(0o755)
        env = dict(os.environ, PATH=tmp + os.pathsep + os.environ["PATH"],
                   DATABASE_URL="postgres://x")
        return subprocess.run(["bash", str(SCRIPT), *args], env=env,
                              capture_output=True, text=True, cwd=tmp)


class TestMigrationScriptStatus(unittest.TestCase):
    def test_dry_run_exits_2_when_status_output_is_an_error(self):
        # #1884: an unreachable database is not a clean dry run.
        r = run_script("Error: P1001: Can't reach database server", 1,
                       "--dry-run")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("Error checking migration status", r.stdout)
        self.assertNotIn("Dry run complete", r.stdout)

    def test_dry_run_with_pending_migrations_still_exits_0(self):
        r = run_script("Following migration have not yet been applied:", 1,
                       "--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Dry run complete", r.stdout)


if __name__ == "__main__":
    unittest.main()
