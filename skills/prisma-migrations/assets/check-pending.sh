#!/usr/bin/env bash
#
# Check for pending Prisma migrations.
#
# Exit codes:
#   0 - No pending migrations (up to date)
#   1 - Pending migrations exist
#   2 - Error checking status
#
# Usage:
#   ./check-pending.sh              # Check and print status
#   ./check-pending.sh --quiet      # Exit code only, no output
#
# Useful in CI/CD to conditionally run migrations:
#   if ./check-pending.sh --quiet; then
#     echo "Already up to date"
#   else
#     npx prisma migrate deploy
#   fi
#
# `prisma migrate status` exits nonzero when migrations are pending, not
# only on error, so the verdict is read from its output and an
# unrecognised output is an error, never a guess.

set -uo pipefail

QUIET=false
if [ "${1:-}" = "--quiet" ]; then
  QUIET=true
fi

say() {
  [ "$QUIET" = false ] && printf '%s\n' "$@"
  return 0
}

if [ -z "${DATABASE_URL:-}" ]; then
  say "Error: DATABASE_URL not set"
  exit 2
fi

STATUS_OUTPUT=$(npx prisma migrate status 2>&1)

# Here-strings, not `echo | grep -q`: under pipefail, grep -q exiting on
# its first match can SIGPIPE the echo and fail the whole test.
if grep -q "Database schema is up to date" <<<"$STATUS_OUTPUT"; then
  say "No pending migrations"
  exit 0
elif grep -q "not yet been applied" <<<"$STATUS_OUTPUT"; then
  say "Pending migrations detected:" "$STATUS_OUTPUT"
  exit 1
else
  say "Error checking migration status:" "$STATUS_OUTPUT"
  exit 2
fi
