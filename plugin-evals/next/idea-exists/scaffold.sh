#!/bin/bash
# Seed a feature run whose only artifact is idea.md (abridged from
# evals/fixtures/decompose-feature), so the orientation table's next stage
# is PRD.
set -euo pipefail
mkdir -p docs/features/csv-export
cat > docs/features/csv-export/idea.md <<'MD'
---
stage: idea
run: feature:csv-export
date: 2026-06-20
---

# Idea: Scheduled CSV export

## Problem

"I rebuild the same spreadsheet every Monday by copying numbers out of the
dashboard." Analytics customers need the underlying data in their own tools.

## Who has it

Workspace admins and data analysts at mid-size customers.

## Solution hunch

Let admins schedule recurring CSV exports of a dashboard's data; we deliver
the file to the customer's S3 bucket on schedule.

## Success in one sentence

Customers stop hand-copying dashboard data because a scheduled CSV lands in
their bucket without human involvement.
MD
