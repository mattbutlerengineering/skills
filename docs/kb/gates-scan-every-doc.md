---
summary: Detectors C and I scan every repo markdown, fences included; an example PRD/ADR/WO id or a sample link fails gates.
sources: gates.py, knowledge_plane.py
verified: 6aacc5cde45558eacc6d8281fdef6da6ac839bb2
related: pr-body-contract, manifest-regen
---

# Gates scan every doc, including the examples in it

`gates._scannable_files` hands detectors C and I every markdown file under
`docs/`, the repo root, `.github/`, `skills/` and `factory/` — minus
`factory/templates/` and `factory/evals/fixtures/`. Each line is scanned
as text: fenced blocks and inline code are not skipped.

- **C** requires every four-digit `PRD-`, `ADR-` and `WO-` token to
  resolve (a `prd.md` declaring it, a `docs/adr/` file, a breakdown row).
  An illustrative id in prose — a made-up work order in a research note,
  an example in a fix brief — is a dangling-token failure.
- **I** requires every markdown link target that is not a URL or an
  anchor to exist on disk, relative to the file. A sample layout in a
  copied research note — a markdown link to an illustrative
  `pages/x.md` — is a stale link, even inside backticks.

What works: placeholders that cannot match (`WO-####`, `WO-00xx`, ids
with fewer than four digits) and URL-shaped sample links. Run
`python3 gates.py` after writing any doc, not only before committing
code — a docs-only change can turn CI red.

Not the same rule as the PR-body gate: there, ADR-0064 strips fenced
blocks and blockquotes before the work-order scan. Inside the repo's
markdown nothing is stripped.
