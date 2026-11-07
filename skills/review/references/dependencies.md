# Dependencies pass

A version bump can pass install, build and tests and still break things
later. It can pull in a major version through an open-ended override,
leave a library resolved at two versions with clashing types, or swap a
coverage engine so the next unrelated PR fails its threshold. This pass
reviews dependency changes: automated bump PRs, override edits and
manual upgrades. Follow the shared contract in
[domain-reviewers.md](domain-reviewers.md).

## What to check

For each dependency the diff adds, removes or moves:

1. **Consumers.** Which packages or modules in the repo use it. In a
   workspace or monorepo, search every manifest, not just the one that
   changed.
2. **Breaking changes.** Read the changelog or release notes for every
   version between the old and the new, not only the target version.
   A major bump with no read changelog is a finding, not a pass.
3. **Required migration steps.** Config keys renamed, APIs removed,
   minimum runtime raised. List each one, and check whether the diff
   already does it.
4. **Override and resolution scope.** An override, resolution or
   constraint entry should be scoped to the vulnerable range. One form
   is `pkg@<range` mapped to a patched version. An open-ended
   `pkg: >=patched` can pull in a future major on the next install.
   Flag the open form.
5. **Peer and type compatibility.** Install with the lockfile frozen to
   surface peer conflicts. For type-only packages (`@types/*`, stub
   packages), check that their major version still matches the runtime
   package's.
6. **Build and tests.** Run the repo's build and tests for the affected
   packages, in a throwaway checkout or with the lockfile frozen, so the
   working tree is left untouched. Report pass or fail with the command
   you ran.
7. **Version mismatch across the workspace.** Compare the version spec
   of every touched dependency across all manifests. When different
   packages land at different specs (`^5.7.1` in one, `^6.0.2` in
   another), flag it. Fix it by aligning every consumer in the same
   change, or by moving the version to the workspace's shared catalog or
   constraints file, if it has one.
8. **Duplicate runtime copies.** After install, check whether a runtime
   library now resolves at two versions. The package manager's "why"
   command shows this, or you can count the library's entries in the
   lockfile. When the two copies share types or a singleton (a client,
   a connection, a context), you get type errors or runtime split-brain
   that look unrelated to the bump. The fix is a scoped override that
   collapses them to one version, per item 4.
9. **Test-tooling threshold risk.** A bump to the test runner or the
   coverage tooling can re-measure coverage downward with no code
   change at all, and break a coverage gate. When the bump touches
   that tooling, run coverage in the packages with the thinnest margin
   over their configured threshold. Name any package within about 2%.
10. **Justification for a new dependency.** A newly added dependency
    needs a reason the diff or the run's artifacts give. Check its
    maintenance state, licence and install scripts. An unexplained new
    dependency is a finding.

## Report

Each problem is a finding in the review's format. Also add one summary
block per bump under the findings:

    Dependency: <package> <old> -> <new>
    Verdict: safe | needs migration | risky
    Consumers: <list>
    Breaking changes: none | <list>
    Build / tests: pass | fail (<command>)
    Workspace alignment: aligned | mismatch (<specs, packages>)
    Duplicate runtime copies: none | dedupe needed (<lib, versions>)
    Coverage-tooling risk: n/a | at risk (<packages>)

## What this pass does not do

- Bump anything itself, or rewrite the lockfile in the working tree.
- Audit the code that calls the library, unless the changelog names a
  change that call site depends on.
