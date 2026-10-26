---
summary: Detectors C and I scan every repo markdown, fences included; an example PRD/ADR/WO id or a sample link fails gates.
sources: gates.py, knowledge_plane.py
verified: fe40d5e7f47f024adb09fe1cfc4453ea44ca802d
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
  anchor to exist on disk, relative to the file (a leading `/` reads
  from the repo root). Targets are read through
  `knowledge_plane.local_link_targets`, the one link grammar kb lint and
  kb drift share since #758: a `"title"` is dropped, an `<angle target>`
  keeps its spaces, and `#fragment` and `?query` are ignored. A sample layout in a
  copied research note — a markdown link to an illustrative
  `pages/x.md` — is a stale link, even inside backticks.

A doc that does not decode as UTF-8 is not scanned at all: detector D
reports it as `cannot read <path>` (#882), so fix the encoding first.

What works: placeholders that cannot match (`WO-####`, `WO-00xx`, ids
with fewer than four digits) and URL-shaped sample links. Run
`python3 gates.py` after writing any doc, not only before committing
code — a docs-only change can turn CI red.

Not the same rule as the PR-body gate: there, ADR-0064 strips fenced
blocks and blockquotes before the work-order scan. Inside the repo's
markdown nothing is stripped.
