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
