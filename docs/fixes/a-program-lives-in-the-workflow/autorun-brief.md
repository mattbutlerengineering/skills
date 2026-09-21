# Autorun brief — a program lives in the workflow

**Scale.** Maintenance run, feature-shaped: `docs/fixes/a-program-lives-in-the-workflow/`.

**What.** `validator.yml` states, in its own header, that it "names no
commands of its own" and that "every step goes through a `make` target".
Three of its four jobs run an inline `python3 -c` program that builds the
synthetic `pull_request` event the PR-shaped detectors consume. The same
claim is repeated by `validator.py`'s module docstring and by the payload
Makefile's header, so the repo says three times that a program which is
present three times is not there at all.

**Why now.** The workflow is mirrored VERBATIM into every stamped product
repo, so both the triplicated program and its three denials ship. The
event shape is a contract — `cli.read_event`'s consumers read it — and a
contract with three hand-maintained copies and no test is the shape of a
defect that appears as a disagreement between two jobs on the same PR.

**Re-entry.** `implement` — the defect is understood, the design is the
repo's own existing convention (tool invocations go through `make`), and
no new architecture is needed.

**Release authorization.** None. Prepare and stop: open a PR, do not
merge. Every open PR is agent-authored and ADR-0036 clause 2 requires a
non-authoring reviewer.

**Scope in.** `validator.py` (the command), `Makefile` and
`factory/templates/Makefile` (the target), `.github/workflows/validator.yml`
and its payload mirror (the three steps and the header), the three claim
sentences, `factory/manifest.json`, `tests/test_validator.py`.

**Scope out.** The `Collect findings` step's `set +e`/`exit 0` shell — it
captures `make check`'s exit code into `$GITHUB_ENV` and cannot itself be
a make target. It is shell plumbing, not a repo tool, and the corrected
claim says so rather than pretending otherwise.
