#!/bin/bash
# Shared scaffold for the knowledge-base paired test (ADR-0078's graduation
# criterion): copy this repo at a pinned commit into the case workspace,
# then keep the knowledge base ("on") or remove it ("off") — docs/kb/ and
# the generated block in CLAUDE.md and AGENTS.md. Everything else is equal.
set -euo pipefail
arm="$1"
root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
git -C "$root" archive 756e9a80e31c04ad2ecd58ea6e8566747b4db88b | tar -x
if [ "$arm" = off ]; then
  rm -rf docs/kb
  for f in CLAUDE.md AGENTS.md; do
    [ -f "$f" ] && python3 - "$f" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p).read()
s = re.sub(r"\n?<!-- BEGIN KB INDEX.*?<!-- END KB INDEX -->\n?", "\n", s, flags=re.S)
open(p, "w").write(s)
PY
  done
fi
