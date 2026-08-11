# Plan 015: Harden the workflow supply chain — permissions everywhere, pinned agent action and CLIs, current Node, structural no-drift guards

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 2e63a04..HEAD -- .github/workflows/ Makefile factory/templates/Makefile tests/test_gates.py tests/test_design_pipeline.py tests/test_charter_replay.py`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M (mechanical, but touches 4 workflows + both Makefiles + manifest)
- **Risk**: MED (a bad pin breaks CI here and, on the next stamp, downstream)
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `2e63a04`, 2026-08-02

## Why this matters

Four gaps, one theme — unattended behavior change on privileged paths,
propagated to every stamped product repo because these files are mirrored
verbatim by `factory_init.py`:

1. `charter-replay.yml` is the **only** workflow with no `permissions:`
   block, so its `GITHUB_TOKEN` gets the repo default (typically write) —
   in the same job that runs an **unpinned** `npm install -g
   @anthropic-ai/claude-code` next to `ANTHROPIC_API_KEY`, and whose
   whole purpose is provoking an agent into forbidden tool calls.
2. `assembler.yml` runs `anthropics/claude-code-action@v1` — a mutable
   tag — on a job with `contents: write`, `pull-requests: write`,
   `issues: write` and both secrets. A re-pointed tag is a same-day,
   unreviewed change to the factory's most privileged surface.
3. `make web-quality` runs `npx --yes playwright` (latest-at-runtime) on
   Node `20`, which left maintenance in April 2026 — the pin no-ops in
   this repo (no web app) and bites only in stamped repos, where nobody
   is looking.
4. The "CI cannot drift from `make check`" guarantee is enforced by
   hand-curated denylists (four tests each listing 3–4 tool names);
   `tests/test_design_pipeline.py` already has the correct structural
   form (every `run:` step must start with `make `). An unlisted tool
   added to a workflow drifts CI with a green suite.

## Current state

- `.github/workflows/charter-replay.yml` — no `permissions:` key
  anywhere (verify: `grep -c permissions .github/workflows/charter-replay.yml`
  → 0). Steps: checkout, setup-python, `npm install -g
  @anthropic-ai/claude-code` (unversioned), `python3 charter_replay.py`
  with `ANTHROPIC_API_KEY`, `actions/upload-artifact@v4`. Trigger is
  `workflow_dispatch` only with `model`/`only` inputs.
- `.github/workflows/assembler.yml:77-82`:

  ```yaml
        uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
  ```

- `.github/workflows/design.yml:33-35`: `actions/setup-node@v4` with
  `node-version: "20"`.
- `Makefile` `web-quality` target (and its twin in
  `factory/templates/Makefile`):

  ```make
  	@if ls playwright.config.* >/dev/null 2>&1; then \
  		npx --yes playwright install --with-deps; \
  		npx --yes playwright test; \
  	else \
  		echo "web-quality: no playwright.config.* — skipping (no web app to test)"; \
  	fi
  ```

- Denylist guards in `tests/test_gates.py:1568-1645` — four
  tests named `test_the_*_workflow_names_no_command_of_its_own`, each
  iterating a literal tuple of tool names and asserting
  `python3 {tool}` absent. The structural form to generalize:
  `tests/test_design_pipeline.py:66-85` extracts every `run:` line and
  asserts `command.startswith("make ")` plus a token denylist.
- `tests/test_charter_replay.py:431`
  (`test_ci_checks_never_invoke_the_replay`) reads **only**
  `validator.yml`.
- Shared Makefile parsing already exists at `tests/make_parse.py`
  (`make_recipe`). Workflow mirroring: `validator.yml`, `assembler.yml`,
  `design.yml`, `cost-report.yml`, `gate-digest.yml` are in
  `factory_init.MIRRORS`; `sweeps.yml` and `charter-replay.yml` are
  **not** (they are this-repo-only). Any change to mirrored files needs
  `python3 factory_init.py update-manifest`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Full local gate | `make check` | exit 0 |
| Resolve the action tag's current commit | `gh api repos/anthropics/claude-code-action/commits/v1 --jq .sha` | a 40-char SHA |
| Current claude CLI version | `npm view @anthropic-ai/claude-code version` | e.g. `2.x.y` |
| Current playwright version | `npm view playwright version` | e.g. `1.x.y` |
| Node LTS check | verify the current active-LTS majors at https://nodejs.org/en/about/previous-releases before choosing 22 vs 24 | — |
| Refresh mirrors + manifest | `python3 factory_init.py update-manifest` | exit 0 |

## Scope

**In scope**:
- `.github/workflows/charter-replay.yml`, `assembler.yml`, `design.yml`
- `Makefile` and `factory/templates/Makefile` (web-quality pin only)
- `tests/workflow_parse.py` (new), `tests/test_gates.py`,
  `tests/test_charter_replay.py`
- `factory/templates/**`, `factory/manifest.json` — only via
  `update-manifest`
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):
- `actions/checkout@v4`, `actions/setup-python@v5`,
  `actions/upload-artifact@v4`, `actions/setup-node@v4` — first-party
  GitHub actions stay on major tags this round (recorded trade-off:
  the third-party, write-scoped action is the risk that clears the bar;
  SHA-pinning the `actions/*` family adds bump burden with much smaller
  exposure — revisit if a Dependabot-style refresh habit ever lands).
- `validator.yml`, `cost-report.yml`, `gate-digest.yml`, `sweeps.yml` —
  no behavior change; they only gain coverage from the new structural
  test.
- The existing denylist tests — leave them in place (still true, still
  named); the structural test is added alongside, not instead.

## Git workflow

- Branch: `advisor/015-workflow-supply-chain-hardening`
- Commit style: `fix(ci): pin the agent action and CLIs, least-privilege
  charter-replay, structural no-drift guard`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Least-privilege charter-replay + pinned CLI install

In `charter-replay.yml`:

1. Add at workflow level (after `on:`), matching the other workflows'
   idiom:

   ```yaml
   # Checkout + artifact upload is all this job does with the token; the
   # replay's provocations must never hold ambient write authority.
   permissions:
     contents: read
   ```

2. Pin the CLI and make the pin an input (reproducible paid runs):

   ```yaml
   on:
     workflow_dispatch:
       inputs:
         cli_version:
           description: claude CLI version to install (pinned default)
           required: false
           default: "<CURRENT>"   # resolve with: npm view @anthropic-ai/claude-code version
   ```

   and change the install step to
   `npm install -g @anthropic-ai/claude-code@${{ inputs.cli_version }}`.

**Verify**: `python3 -m unittest tests.test_charter_replay -v` → pass
(the trigger-shape tests read `on:`; confirm they still hold).

### Step 2: SHA-pin the agent action

Resolve the current commit of the `v1` tag
(`gh api repos/anthropics/claude-code-action/commits/v1 --jq .sha`),
then in `assembler.yml`:

```yaml
        # Pinned by SHA: this job holds write scopes + the API key, so its
        # third-party code must change only by reviewed commit, never by a
        # re-pointed tag. Bump deliberately: re-resolve the tag, update the
        # SHA and the comment.
        uses: anthropics/claude-code-action@<full-40-char-sha>  # v1 as of 2026-08-02
```

**Verify**: `grep -n "claude-code-action@" .github/workflows/assembler.yml`
→ shows the SHA form, no bare `@v1`.

### Step 3: Current Node + pinned playwright

1. `design.yml`: bump `node-version: "20"` → the current active LTS
   (verify first per the commands table; `"22"` expected — if 22 is
   also past active LTS by execution time, use the verified current one).
2. Both Makefiles' `web-quality`: replace the two `npx --yes playwright`
   invocations with a pinned version, keeping the skip-when-absent shape:

   ```make
   PLAYWRIGHT_VERSION ?= <resolved current, e.g. 1.55.0>

   web-quality:
   	@if ls playwright.config.* >/dev/null 2>&1; then \
   		npx --yes playwright@$(PLAYWRIGHT_VERSION) install --with-deps; \
   		npx --yes playwright@$(PLAYWRIGHT_VERSION) test; \
   	else \
   		echo "web-quality: no playwright.config.* — skipping (no web app to test)"; \
   	fi
   ```

   Both Makefiles must carry the identical recipe (this target is
   path-agnostic and byte-shared — `tests/test_design_pipeline.py`
   pins it; check whether it asserts recipe equality and keep it green).

**Verify**: `python3 -m unittest tests.test_design_pipeline -v` → pass
(its no-command guard checks `run:` lines in the workflow, which still
say only `make web-quality`).

### Step 4: The structural no-drift guard

1. New `tests/workflow_parse.py` (sibling of `tests/make_parse.py`,
   same stdlib-only docstring style):

   ```python
   def run_steps(text):
       """Every `run:` command in a workflow file, one string per step
       (single-line and block-scalar `run: |` forms both)."""
   ```

   Handle the two forms present in this repo's workflows: inline
   (`run: make check`) and block (`run: |` followed by deeper-indented
   lines — return the block joined with newlines as one step).
2. In `tests/test_gates.py`, add a test class:

   ```python
   class TestWorkflowRunStepInvariant(unittest.TestCase):
       """Every run step in every workflow goes through make, except a
       named, reasoned allowlist — enumeration was the old guard's hole:
       a tool absent from the denylist could drift CI from make check."""
   ```

   For each of the 7 workflow files: collect `run_steps`, assert each
   step either starts with `make ` **or** is in that workflow's
   allowlist. Build the allowlist from what actually exists at HEAD,
   with a comment per entry saying why it's legitimate — expected
   entries: `charter-replay.yml` (npm install step; the replay
   invocation block — this workflow is deliberately outside the
   Makefile: it is this-repo-only, never mirrored), `sweeps.yml`
   (its `python3 sweeps.py ...` steps — same this-repo-only reason),
   `cost-report.yml` (the two `gh` mutation blocks — the
   compute/mutate boundary keeps them in YAML), `gate-digest.yml` and
   `validator.yml` (any `gh`/shell glue blocks found; inspect, name,
   justify). A step that is neither `make` nor allowlisted must fail
   with a message naming the file and step.
3. Broaden `test_ci_checks_never_invoke_the_replay` in
   `tests/test_charter_replay.py` to scan every file in
   `.github/workflows/` **except** `charter-replay.yml` for the string
   `charter_replay.py`.

**Verify**: `python3 -m unittest tests.test_gates tests.test_charter_replay -v` → all pass at HEAD (the allowlist covers
exactly what exists; nothing else).

### Step 5: Refresh mirrors

```
python3 factory_init.py update-manifest
```

**Verify**: `make check` → exit 0. `git status` shows payload copies of
`assembler.yml`, `design.yml`, the template Makefile, and
`factory/manifest.json` updated.

## Test plan

Step 4 is the test work. Negative case to include: feed
`run_steps` a synthetic workflow text containing
`run: python3 gates.py` and assert the invariant test's helper flags it
(test the guard itself, not just the current tree).

## Done criteria

- [ ] `make check` exits 0
- [ ] `grep -rn "@v1" .github/workflows/assembler.yml` → no matches
- [ ] `grep -c "permissions" .github/workflows/charter-replay.yml` → ≥1
- [ ] `grep -n "node-version" .github/workflows/design.yml` → not `"20"`
- [ ] `grep -c "npx --yes playwright install" Makefile` → 0 (pinned form only)
- [ ] `tests/workflow_parse.py` exists; invariant test covers all 7 workflows
- [ ] `factory/manifest.json` regenerated and committed
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back if:

- `gh api repos/anthropics/claude-code-action/commits/v1` fails (no
  network / no auth) — do not guess a SHA from memory, ever.
- The claude-code-action's README at the pinned commit documents inputs
  differently from what `assembler.yml` passes (`anthropic_api_key`,
  `github_token`, `prompt`, `claude_args`) — a silent input rename is
  exactly the failure this pin exists to catch; report it.
- Any workflow has a `run:` step you cannot classify as make-target,
  gh-mutation glue, or this-repo-only tool — don't allowlist what you
  can't justify.
- `tests/test_design_pipeline.py` asserts the web-quality recipe
  byte-for-byte in a way the `PLAYWRIGHT_VERSION` variable breaks and
  you can't keep both Makefiles identical — report rather than fork the
  recipes.

## Maintenance notes

- The SHA pin trades freshness for review: bumping
  `claude-code-action` is now a deliberate act (re-resolve tag → update
  SHA + comment → update-manifest → PR). Put it on whatever dependency
  cadence the repo adopts.
- Stamped product repos get the pinned versions on their next stamp —
  which is currently never (no upgrade leg; see plan 017's maintenance
  notes and the unplanned `factory_init upgrade` direction finding).
- Reviewer should scrutinize: the allowlist entries' justifications —
  each one is a hole in the invariant and needs its one-line reason to
  stay true.
