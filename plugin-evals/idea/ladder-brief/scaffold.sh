#!/bin/bash
# Seed a feature run at the Idea stage: a one-paragraph pitch for a
# made-up scheduling tool and a backlog with its header and one existing
# seed, committed so the run can commit its brief. A scaffold runs in a
# temp dir and cannot reach the repo.
set -euo pipefail
git init -q
git config user.email "eval@example.invalid"
git config user.name "eval"
mkdir -p docs
cat > docs/pitch.md <<'PITCH_EOF'
# Pitch: Slot finder

Shift managers at small restaurants lose an evening every week to the
call-out shuffle. Our scheduling app should become a self-healing shift
rota: when someone calls out, it should find who can cover the station and
fill the gap, so the manager stops rebuilding the week by hand.
PITCH_EOF
cat > docs/backlog.md <<'BACKLOG_EOF'
Seed inbox — advisory only, never orientation state.

- Export the rota as a calendar feed (from: session:2026-07-05)
BACKLOG_EOF
git add -A
git commit -q -m "chore: seed the pitch and backlog"
