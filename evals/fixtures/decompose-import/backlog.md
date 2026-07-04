# Open tracker issues (backlog snapshot)

The project's issue tracker currently holds these open issues touching the
csv-export feature. Fixture note: this file stands in for the tracker —
treat its entries as the tracker's open issues; there is no live API.

## #341 — Export delivery must survive transient S3 outages

Deliveries to customer buckets fail hard on the first S3 error today. A
transient outage should not kill the export.

Acceptance criterion recorded on the issue: a failed delivery is retried
up to 3 times with backoff, and the final failure is recorded on the job
with the S3 error preserved.

## #352 — Expose export job status over the API

Workspace admins have no way to see whether recent export jobs ran or
failed; they find out from their analysts. Surface job status through the
export API. (No acceptance criterion recorded on the issue.)
