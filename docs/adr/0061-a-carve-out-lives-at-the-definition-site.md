# A carve-out lives at the definition site and must pay rent

- Status: provisional
- Date: 2026-08-23

The repo's bar is one fact, one owner, and until now the only thing
enforcing it was a human reading the tree during a manual deepening
review — a finder with a measured hit rate of 4 of 7
(docs/fixes/one-fact-one-owner/defect.md). A mechanical pre-pass closes
that gap, but a checker for this class has a false-positive problem the
other detectors do not: this repo has recorded, *deliberate* duplicates,
and a tool that cries wolf on decisions already made gets disabled.

So the pre-pass needs a way to say "this pair is deliberate, and here is
the ADR". The hard part is not where to put that list; it is what stops
the list from going stale — because this repo has already watched one go
stale. ADR-0039 fixed the checkbox-regex roster at three owners, in
prose, in an ADR, three files away from every regex it named. Nineteen
days later `knowledge_plane.DONE_ROW` arrived as a fourth, byte-identical
to `gates.MERGED_ROW`; nothing re-read the roster, and ADR-0058 exists to
record that. The part of that roster that stayed correct is the part that
lived in the tree at the definitions — the cross-references at
`knowledge_plane.py:69-77` and `protocol.py:57-60`, both still accurate.

## Decision

**A deliberate second owner is annotated where it is defined**, in the
comment block immediately above the definition:

    # one-owner: <module>.<name> (ADR-####) — <reason>

**The reason is required.** A bare marker waives nothing — the same rule
`gates.NO_WO_DECLARATION` already applies to the other place a change may
excuse itself.

**The carve-out is re-derived against the tree on every run, and checked
in both directions.**

- *Under-coverage.* Silence is a property of the whole group, never of
  one marker: a group is silent only when every member carries a marker
  **and** every member is named by some other member's marker. A new
  owner therefore cannot admit itself — admitting it means editing an
  existing owner's file, where a reviewer is already looking. This is the
  precise failure ADR-0039 suffered, made impossible.
- *Over-coverage.* Every marker must match a duplicate the pass actually
  finds. A marker whose counterpart was deleted, renamed, or folded
  matches nothing and is reported as stale, by file and line. The list
  cannot rot quietly, because dead entries are findings.

**The citation must resolve** to a file in `docs/adr/`. Whether that ADR
is still live is deliberately not checked: the status grammar's owner is
`gates.ADR_STATUS`, and importing a detector module from a tool is the
coupling ADR-0058 removed. Folding `ADR_STATUS` into `knowledge_plane` is
its own decision, not a ride-along.

**A marker may live in a file that mirrors into the payload, and the
detector-home objection does not transfer to it.** That objection —
which is why the pass is a standalone tool rather than a `gates.py`
detector — was that a detector would turn a stamped product repo's own
`make check` red on source that never agreed to this repo's seam
convention. A `# one-owner:` marker imposes nothing, because it is an
inert comment that no stamped-repo tooling reads: `gates._scannable_files`
is `docs/**/*.md` plus `CONTEXT.md`, so detectors A, C and D never open a
`.py` file, and the pass itself is root-only and ships nowhere. The rule
for every future annotation is therefore that a mirrored file is a
legitimate home for a marker; its whole cost is one
`python3 factory_init.py update-manifest` in the same commit, so the
regenerated payload twin and the manifest land with the annotation.

## Consequences

- The carve-out list has no file of its own. There is no allow-list, no
  suppressions file, and no baseline — each is a roster under another
  name, and the roster is the thing that went stale.
- Adding a deliberate second owner costs two edits, in two files, by
  construction. That is the point, not an oversight.
- Deleting a definition deletes its excuse, and moving it moves it. The
  carve-out cannot outlive the code it describes.
- The first annotation this decision writes is `budget_guard.git_runner`
  / `dashboard.git_runner`, the `runner('git')` pair ADR-0037 sanctions
  explicitly. The canonical pair — `protocol._CHECKBOX` versus
  `knowledge_plane.ROW` — needs no annotation, because the identity rule
  is exact and their patterns and flags genuinely differ.
- Status is provisional: this records a mechanism on first use, and the
  operator has confirmed nothing.
