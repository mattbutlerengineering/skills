"""skills/prisma-migrations/assets/migration-script.sh reads the verdict from
`prisma migrate status` output: an output that is neither up to date nor
pending is an error (exit 2), never a clean dry run (#1884)."""
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = (Path(__file__).resolve().parent.parent / "skills"
          / "prisma-migrations" / "assets" / "migration-script.sh")


def run_script(status_output, *args):
    with tempfile.TemporaryDirectory() as tmp:
        npx = Path(tmp) / "npx"
        npx.write_text("#!/bin/sh\ncat <<'EOF'\n" + status_output
                       + "\nEOF\nexit 1\n", encoding="utf-8")
        npx.chmod(npx.stat().st_mode | stat.S_IEXEC)
        env = {**os.environ, "PATH": f"{tmp}:{os.environ['PATH']}",
               "DATABASE_URL": "postgres://x"}
        return subprocess.run(["bash", str(SCRIPT), *args], env=env,
                              capture_output=True, text=True)


class TestMigrationScriptStatus(unittest.TestCase):
    def test_an_unreachable_database_is_exit_two_on_a_dry_run(self):
        done = run_script("Error: P1001: Can't reach database server",
                          "--dry-run")
        self.assertEqual(done.returncode, 2, done.stdout)
        self.assertIn("Error checking migration status", done.stdout)
        self.assertNotIn("Dry run complete", done.stdout)

    def test_pending_migrations_are_a_clean_dry_run(self):
        done = run_script("Following migration have not yet been applied:\n"
                          "20260101_init", "--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("Dry run complete", done.stdout)

    def test_an_up_to_date_database_is_exit_zero(self):
        done = run_script("Database schema is up to date!", "--dry-run")
        self.assertEqual(done.returncode, 0, done.stdout)


if __name__ == "__main__":
    unittest.main()
