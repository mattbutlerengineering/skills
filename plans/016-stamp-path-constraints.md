# Plan 016: `install_path` refuses instead of mangling — stamp destinations constrained to the target tree

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 2e63a04..HEAD -- factory_init.py tests/test_factory_init.py`
> If either file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW (validation-only; current manifest keys all pass)
- **Depends on**: none — but plan 017's maintenance run also edits
  `factory_init.py` (the CODEOWNERS owner substitution). Land this one
  FIRST so 017's implement step rebases on it.
- **Category**: security (hardening; low current reachability)
- **Planned at**: commit `2e63a04`, 2026-08-02

## Why this matters

`factory_init.stamp` writes files into a target repo at paths derived
from `factory/manifest.json` keys. The path derivation is a blind slice:
`install_path` computes `rel[len("templates/"):]` without checking that
`rel` starts with `templates/` — so `'../../evil'` becomes `'evil'`
minus its first 12 characters, `'/tmp/x'` becomes a fragment, and
`'templates/../../etc/x'` keeps its `..` and escapes the target when
joined and `mkdir(parents=True)`+`copyfile`'d. Today the checksum gate
(`gates.check_scaffold_sync`) runs first and the manifest is
operator-controlled, so reachability is low — but a file-writing
operation's destinations should be constrained **by construction**, not
by an upstream checksum happening to hold, and `install_path` silently
mangling malformed keys is wrong in itself.

## Current state

`factory_init.py`:

- Lines 70–75:

  ```python
  # Manifest rel -> install destination; anything unmapped strips "templates/".
  INSTALL_MAP = {"templates/factory.json": ".github/factory.json"}


  def install_path(rel):
      """Destination of a manifest entry in a product repo."""
      return INSTALL_MAP.get(rel, rel[len("templates/"):])
  ```

- `stamp(source, target)` (lines 106–124): runs
  `gates.check_scaffold_sync(source)` first, reads the manifest's
  `files` dict, builds `copies` as `(source path, dest)` pairs — dest is
  `Path("factory") / rel` for the pristine mirror plus
  `Path(install_path(rel))` for the installed copy — pre-checks
  `clashes` via `(target / dest).exists()`, then
  `(target / dest).parent.mkdir(parents=True, exist_ok=True)` +
  `shutil.copyfile`.

- Conventions: functions return label-prefixed problem strings
  (`factory-init:` prefix here); the CLI prints and exits nonzero.
  Existing tests: `tests/test_factory_init.py` — grep `TestInstallPath`
  (or the nearest class covering `install_path`) and the `stamp` suite
  (`test_factory_init.py:268` area runs a real stamp into a tempdir and
  then `gates.py` against it — the end-to-end pattern).
- Is `factory_init.py` itself mirrored? Check `MIRRORS` in the file —
  at planning time it is **not** a mirror source, so no
  `update-manifest` run should be needed; verify with
  `grep -n "factory_init" factory_init.py gates.py` and skip the
  manifest step if truly unreferenced (see STOP conditions).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Full local gate | `make check` | exit 0 |
| Just this suite | `python3 -m unittest tests.test_factory_init -v` | all pass |

## Scope

**In scope**:
- `factory_init.py`
- `tests/test_factory_init.py`
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `factory/manifest.json` and `factory/templates/**` — no key changes;
  this plan only validates them.
- `gates.py` `check_scaffold_sync` / `manifest_files` — the checksum
  gate is a different layer and stays as-is.
- The CODEOWNERS template and any owner-substitution logic — that is
  plan 017's implement step.

## Git workflow

- Branch: `advisor/016-stamp-path-constraints`
- Commit style: `fix(factory-init): install_path refuses malformed
  manifest keys; stamp stays inside the target`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Make `install_path` return `(dest, problem)`

Replace the function:

```python
def install_path(rel):
    """(destination in a product repo, problem). A manifest key must be
    a plain relative path under templates/ — anything else is refused,
    never sliced into something that happens to join cleanly. The
    checksum gate upstream makes a malformed key unlikely; this makes
    the write path safe by construction, not by upstream luck."""
    if rel in INSTALL_MAP:
        return INSTALL_MAP[rel], None
    if not rel.startswith("templates/"):
        return None, (f"factory-init: manifest key {rel!r} is not under"
                      " templates/")
    dest = rel[len("templates/"):]
    parts = dest.split("/")
    if not dest or dest.startswith("/") or ".." in parts or "" in parts:
        return None, (f"factory-init: manifest key {rel!r} does not"
                      " resolve to a plain relative path")
    return dest, None
```

Update `stamp` to collect these problems before any copy:

```python
    copies = [(manifest_src, Path("factory/manifest.json"))]
    problems = []
    for rel in sorted(files):
        copies.append((source / "factory" / rel, Path("factory") / rel))
        dest, problem = install_path(rel)
        if problem:
            problems.append(problem)
            continue
        copies.append((source / "factory" / rel, Path(dest)))
    if problems:
        return problems
```

Then add the belt-and-braces containment assert in the copy loop,
before `mkdir`:

```python
    target_root = target.resolve()
    for src, dest in copies:
        resolved = (target / dest).resolve()
        if not resolved.is_relative_to(target_root):
            return [f"factory-init: destination {dest.as_posix()} escapes"
                    " the stamp target"]
```

(`Path.is_relative_to` is stdlib since 3.9; the repo's CI runs 3.12.)
Keep the existing clash pre-check and copy behavior otherwise unchanged.

**Verify**: `python3 -m unittest tests.test_factory_init -v` → existing
callers of `install_path` in tests fail on the new return shape only;
fix them in step 2.

### Step 2: Update and extend the tests

In `tests/test_factory_init.py`:

- Fix existing `install_path` assertions to the tuple form
  (`self.assertEqual(factory_init.install_path("templates/Makefile"),
  ("Makefile", None))` etc.).
- Add negative cases asserting the exact problem strings from step 1:
  - `"../../evil.sh"` → not-under-templates problem
  - `"/tmp/evil"` → not-under-templates problem
  - `"templates/../../etc/evil"` → not-a-plain-relative-path problem
  - `"templates//x"` and `"templates/"` → not-a-plain-relative-path
  - `"templates/a/../b"` → not-a-plain-relative-path
- Add one `stamp`-level test: a source tree whose manifest contains one
  malformed key → `stamp` returns exactly that problem and writes
  **nothing** into the target (assert the target dir is empty after).
  Model after the existing stamp-into-tempdir tests.

**Verify**: `python3 -m unittest tests.test_factory_init -v` → all pass.

### Step 3: Full gate

**Verify**: `make check` → exit 0 (in particular, the real
`factory/manifest.json` keys all still resolve — proving the validation
is a no-op on the honest tree).

## Test plan

Step 2. Pattern: the existing `test_factory_init.py` style — direct
function assertions for `install_path`, tempdir end-to-end for `stamp`.

## Done criteria

- [ ] `make check` exits 0
- [ ] `install_path` returns `(dest, problem)`; all listed negative
      cases pass with exact strings
- [ ] The malformed-key `stamp` test proves nothing is written
- [ ] No change to `factory/manifest.json` (`git diff --stat` clean there)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `install_path` has callers outside `factory_init.py` and its tests
  (`grep -rn "install_path" --include="*.py" .`) — the return-shape
  change would break them.
- Any real manifest key fails the new validation — the tree contains
  a key shape this plan didn't anticipate; report it rather than
  loosening the rule.
- `factory_init.py` turns out to be in `MIRRORS` at HEAD — then the
  payload mirror + manifest need regenerating and this plan's scope
  statement is stale; report before proceeding.

## Maintenance notes

- Plan 017's maintenance run adds owner substitution to `stamp` — it
  builds on this tuple-returning `install_path`; whoever executes 017
  should read this plan's diff first.
- If a future manifest legitimately needs a key outside `templates/`
  (unlikely — `INSTALL_MAP` is the escape hatch), extend `INSTALL_MAP`,
  never the slice.
- Reviewer should scrutinize: the containment check uses `resolve()` —
  confirm it doesn't break stamping into a symlinked target directory
  (resolve both sides, as the step does, and the comparison holds).
