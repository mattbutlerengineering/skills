# Two run scales

- Status: superseded in part by ADR-0025
- Date: 2026-07-01

A *product run* takes a greenfield product through the full pipeline;
artifacts live at the target repo's docs root. A *feature run* is a
scaled-down pass re-entering at Idea or PRD; artifacts live under
`docs/features/<slug>/`.

Superseded in part by [ADR-0025](0025-maintenance-run-scale.md): the two
run scales become three (a maintenance run joins product and feature).
The product and feature scales described here stand unchanged.
