---
stage: idea
run: feature:csv-export
date: 2026-06-20
---

# Idea: Scheduled CSV export

## Problem

"I rebuild the same spreadsheet every Monday by copying numbers out of the
dashboard." Analytics customers need the underlying data in their own tools;
the dashboard is a viewing surface, not a source.

## Who has it

Workspace admins and data analysts at mid-size customers. Today they cope by
screenshotting charts, hand-copying tables, or asking support for one-off
database pulls (support logs ~15 such tickets/month).

## Why now

Two enterprise renewals this quarter listed "data export" as a blocker, and
the new query layer (shipped in May) finally makes tenant-scoped bulk reads
cheap enough to offer.

## Evidence

- 15 support tickets/month requesting manual pulls (ticket tag: `data-export`).
- Renewal notes from Acme Corp and Initech name export as a condition.
- Anecdote (labelled as such): two prospects asked about export in sales calls.

## Solution hunch

Let admins schedule recurring CSV exports of a dashboard's data via the API;
we generate the file and deliver it to the customer's S3 bucket on schedule.

## Success in one sentence

Customers stop hand-copying dashboard data because a scheduled CSV lands in
their bucket without human involvement.

## Unknowns & risks

- Export volume: biggest dashboards may produce files too large to generate
  synchronously — likely needs a background worker.
- Delivery target: is S3 enough, or do customers need email/GCS too? (Start
  with S3, validate.)
- Most likely death: exports that silently stop running erode trust worse
  than no exports at all — failure visibility matters.
