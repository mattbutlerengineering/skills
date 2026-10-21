---
stage: decompose
run: feature:csv-export
date: 2026-10-20
---

# Breakdown: Scheduled CSV export

Progress lives in the checkboxes below — Implement checks items off as their
acceptance criteria are met.

## Milestone 1: an admin can store an export and read its jobs

- [ ] **S1 Create endpoint** — Export API accepts a new export configuration
  - Accept: `POST /exports` returns 201 with the stored config, 422 on an invalid cron or unknown dashboard, and 403 when the dashboard belongs to another workspace.
  - Blocked by: —
- [ ] **S2 Job status endpoint** — Export API lists recent jobs for a configuration
  - Accept: `GET /exports/{id}/jobs` returns jobs newest first with the error detail on failures, and 404 for a config outside the caller's workspace.
  - Blocked by: S1

## Milestone 2: a due schedule becomes a CSV stream

- [ ] **S3 Scheduler tick** — Export Scheduler enqueues one job per due configuration
  - Accept: a tick once per minute enqueues exactly one `ExportJob` for each due `ExportConfig` and generates or delivers nothing itself.
  - Blocked by: S1
- [ ] **S4 Streaming CSV** — CSV Generator turns one job into an RFC 4180 stream
  - Accept: the stream starts with a header row matching the dashboard's field list, quotes and escapes per RFC 4180, and reads through the streaming cursor so memory stays flat.
  - Blocked by: S1

## Milestone 3: the CSV reaches the customer's bucket on time

- [ ] **S5 Upload with retries** — the S3 uploader sends the stream to the target and records the final status
  - Accept: a failing upload is retried 3 times with exponential backoff and then the job status is `failed` with the S3 error preserved, while a success sets `delivered`.
  - Blocked by: S4
- [ ] **S6 End to end timing** — a due schedule produces a CSV in the configured bucket on time
  - Accept: a scripted run with a schedule due now puts one object named `<prefix>/<dashboard-slug>-<scheduled_for>.csv` in the bucket within 5 minutes of the scheduled time.
  - Blocked by: S2; S3; S5

## Design gaps found

none.

## Notes

none yet.
