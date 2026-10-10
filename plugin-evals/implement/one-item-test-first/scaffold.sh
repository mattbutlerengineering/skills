#!/bin/bash
# Seed a feature run at the Implement stage: a one-item breakdown, an empty
# textutil.py and an empty tests package, committed so the run can commit
# at the item boundary.
set -euo pipefail
mkdir -p docs/features/slugify tests
printf '"""Text helpers."""\n' > textutil.py
: > tests/__init__.py
cat > docs/features/slugify/breakdown.md <<'MD'
---
stage: decompose
run: feature:slugify
date: 2026-10-10
---

# Breakdown: slugify

Progress lives in the checkboxes below.

## Milestone 1: Slugs

- [ ] **Item 1** Add `slugify(title)` to `textutil.py` — size:S, blocked by: —
  - Accept: `slugify("Hello, World!")` returns `"hello-world"`; every run
    of characters that are not ASCII letters or digits becomes one hyphen,
    and leading and trailing hyphens are stripped. Pinned by a test in
    `tests/test_textutil.py`, run with `python3 -m unittest discover tests`.

## Notes
MD
git init -q
git config user.name "eval"
git config user.email "eval@example.invalid"
git add -A
git commit -q -m "chore: seed the slugify run"
