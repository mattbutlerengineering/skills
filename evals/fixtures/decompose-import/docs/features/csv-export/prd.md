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
