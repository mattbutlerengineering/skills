#!/bin/bash
# Seed a feature run at the Decompose stage: the csv-export PRD and
# architecture, committed so the run can commit its breakdown. The two
# heredoc bodies equal the fixture files under
# evals/fixtures/decompose-feature/docs/features/csv-export/ (a test pins
# that); a scaffold runs in a temp dir and cannot reach the repo.
set -euo pipefail
mkdir -p docs/features/csv-export
cat > docs/features/csv-export/prd.md <<'PRD_EOF'
---
stage: prd
run: feature:csv-export
date: 2026-06-22
ux: not-applicable
---

# PRD: Scheduled CSV export

## Problem statement

Analytics customers rebuild spreadsheets by hand-copying dashboard data every
reporting cycle. They need the underlying data delivered to their own tools
on a schedule, without asking support for one-off pulls.

## Solution

Workspace admins configure recurring CSV exports of a dashboard through the
REST API. On schedule, the system generates a CSV of the dashboard's current
data and delivers it to the customer's S3 bucket. Job status (including
failures) is queryable through the same API. No UI surface — this is an
API-only feature, hence `ux: not-applicable`.

## Actors

- **Workspace admin** — configures exports via the API, owns the S3 bucket.
- **Data analyst** — consumes the delivered CSVs; never touches our API.

## User stories

1. As a workspace admin, I want to schedule a recurring CSV export of a
   dashboard, so that analysts get fresh data without manual work.
2. As a workspace admin, I want to see whether recent export jobs succeeded,
   so that I notice broken deliveries before my analysts do.
3. As a data analyst, I want the CSV columns to match the dashboard fields,
   so that my downstream spreadsheets keep working.

## Success criteria

- [ ] An admin can create a scheduled export with `POST /exports` and gets a
      201 response echoing the stored configuration.
- [ ] A due schedule produces a CSV in the configured bucket within 5 minutes
      of its scheduled time.
- [ ] CSV output has a header row matching the dashboard's fields and uses
      RFC 4180 quoting/escaping.
- [ ] A failed delivery is retried 3 times, and the final failure is visible
      via `GET /exports/{id}/jobs`.
- [ ] Every export is scoped to the requesting workspace — no query can
      return another tenant's data.

## Out of scope

- Any dashboard UI for configuring exports (API only in this pass).
- Delivery targets other than S3 (email, GCS, webhooks).
- Formats other than CSV (Excel, Parquet).
- Backfilling historical snapshots — exports reflect data at generation time.

## Open questions

- Max rows per export before we must paginate into multiple files — needs a
  production data-size survey (data team).
PRD_EOF
cat > docs/features/csv-export/architecture.md <<'ARCH_EOF'
---
stage: architect
run: feature:csv-export
date: 2026-06-25
ux: skipped — API-only feature, no UI surface (per prd.md)
---

# Architecture: Scheduled CSV export

## Approach

A small pipeline hanging off the existing job queue: an API layer stores
export configurations, a scheduler tick enqueues due jobs, a generator
streams query results into CSV, and a delivery step uploads to the
customer's bucket with retries. Streaming end-to-end keeps memory flat
regardless of dashboard size; reusing the existing queue avoids new
infrastructure.

## Components

### Export API

- Responsibility: CRUD for export configurations and read access to job
  status; enforces workspace scoping on every request.
- Collaborators: ExportConfig/ExportJob tables; Export Scheduler (reads
  configs it wrote).

### Export Scheduler

- Responsibility: once per minute, find due ExportConfigs and enqueue one
  ExportJob each; never generates or delivers itself.
- Collaborators: existing job queue; Export API's tables.

### CSV Generator

- Responsibility: turn one ExportJob into a CSV stream — runs the
  dashboard's query through the query layer, writes RFC 4180 rows with a
  header from the dashboard's field list.
- Collaborators: query layer (tenant-scoped reads); Delivery (hands off the
  stream).

### Delivery

- Responsibility: upload the CSV stream to the config's S3 target, retrying
  up to 3 times with backoff; record final job status.
- Collaborators: S3 client; ExportJob table (status writes).

## Data model

- **ExportConfig** — id, workspace_id, dashboard_id, schedule (cron expr),
  s3_bucket, s3_prefix, created_by, active flag.
- **ExportJob** — id, config_id, scheduled_for, started_at, finished_at,
  status (pending | running | delivered | failed), attempt_count, error.
- Relationship: ExportConfig 1—N ExportJob. Both rows carry workspace_id
  denormalized for scoping checks.

## Interfaces & contracts

### POST /exports

- Input: dashboard_id, schedule, s3_bucket, s3_prefix.
- Output: 201 with the stored config; 422 on invalid cron or unknown
  dashboard.
- Failure modes: 403 when the dashboard belongs to another workspace.

### GET /exports/{id}/jobs

- Input: config id, optional status filter.
- Output: recent ExportJobs, newest first, including error detail on
  failures.
- Failure modes: 404 for configs outside the caller's workspace (no
  existence leak).

### Delivery → S3

- Input: CSV stream, bucket/prefix from config.
- Output: object named `<prefix>/<dashboard-slug>-<scheduled_for>.csv`.
- Failure modes: 3 attempts with exponential backoff; final failure sets
  job status `failed` with the S3 error preserved.

## Stack & dependencies

- Existing Postgres + job queue — no new infrastructure for a feature run.
- aws-sdk S3 client (already a dependency for asset storage) — reuse, don't
  add.
- Query layer's streaming cursor API (shipped May) — the enabler for flat
  memory.

## Decisions & alternatives

- **Streaming generation** over buffer-then-upload — biggest dashboards
  would exhaust worker memory.
- **Scheduler tick + queue** over per-config OS cron entries — one place to
  reason about due-ness, and the queue already handles retries/visibility.
- **Denormalized workspace_id on jobs** over join-time scoping — makes the
  tenant check un-forgettable at every read path.

## ADRs

none — no decision met the ADR bar.
ARCH_EOF
git init -q
git config user.name "eval"
git config user.email "eval@example.invalid"
git add -A
git commit -q -m "chore: seed the csv-export run"
