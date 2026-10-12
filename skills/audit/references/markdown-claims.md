# Markdown claims: is the prose still true?

The `audit claims` scope. It audits one kind of documentation rot: a
human-facing doc that states something the repo no longer satisfies — a
command that fails, a flag that was renamed, a file that moved, a
behaviour the code dropped. It reads as authoritative right up until
someone runs it.

Two passes split the work, and they never overlap:

| Pass | Owns | Decides by |
|---|---|---|
| `md_claims.py check` (shipped, deterministic) | Links, inline paths, fenced shell commands: the script exists, each `--flag` appears in its source, the make target or package script is defined | Lookup |
| this mode (the agent) | Everything a lookup cannot settle: does the command still do what the sentence says, is the count right, does the code still behave as described | Judgement |

The tool never runs a documented command — it reads the Makefile,
`package.json` and the script's source. Run it from the repo root, with
the plugin checkout's path in place of the placeholder:

    python3 <this skill's directory>/../../md_claims.py check [root] [path ...]
    python3 <this skill's directory>/../../md_claims.py extract [root] [path ...]

`check` prints one problem per contradicted claim and
`md-claims: N problem(s) across M doc(s)`, exiting 1 when N > 0.
`extract` prints every claim it found as JSON — the inventory this mode
judges. With no paths it reads the root `*.md` (minus the
agent-instruction files) and `docs/**/*.md` (minus date-prefixed
snapshots). Pass paths to narrow it when `docs/` also holds records — run
artifacts, ADRs, research notes — which describe what was true when they
were written and are not corrected. A claim that is right but unprovable
by lookup (a path in the repo the doc is *about*, not this one) is
silenced with `<!-- md-claims: ignore -->` on its line or the line
before; above a fence it covers the whole block.

## Scope

In: `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `docs/**`, package and
service READMEs. Out: `CLAUDE.md`, `AGENTS.md` and other agent-instruction
files (a separate concern with its own reader), and date-prefixed or
run-record docs (they are records, and "correcting" one destroys it).

## Process

1. **Run the mechanical pass.** `md_claims.py check` on the scope. Its
   problems are already settled — list them in the report under their
   own heading, verbatim, and do not re-derive or re-report them as
   findings. A problem that is a false positive (a path in another repo)
   is a suggestion to add the ignore marker, not a finding.
2. **Take the inventory.** `md_claims.py extract` gives the commands and
   paths; read each in-scope doc as well, because the claims a tool
   cannot extract are the expensive ones. A claim is checkable when you
   can name the file, symbol, command or output that would falsify it:
   - **Commands** — does the subcommand exist, does it do what the
     sentence around it says, does its output look like the doc shows?
   - **Flags and options** — still parsed, or renamed, or now required?
   - **Counts and inventories** — "nine checkers", "three modes". Count
     the real thing.
   - **Described behaviour** — "falls back to X on failure". Read the
     code path.
   - **Ports, URLs, env var names** — against the service's own config.
3. **Verify against the tree, not memory.** Read the parser, the
   handler, the config. Reading `--help` output is allowed only for a
   tool the repo owns whose help path is read-only by inspection; never
   run an install, a build, a deploy, or any documented command whose
   effect you have not read. When the checkout may be behind, read the
   default branch (`git show origin/HEAD:<path>`).
4. **Write each finding as a contradiction**: *the doc says X; X is false
   because &lt;evidence&gt;*. A sentence that is vague or badly written but
   not false is not a finding. One you cannot evidence is a suspicion
   (SKILL.md step 3), not a finding.

## Report

The audit's step 5 report, narrowed:

| # | Doc:line | The doc says | Actually | Evidence | Carrier |

Then the mechanical pass's problem lines verbatim, the suspicions, and a
coverage line naming every doc read. Each finding's carrier follows
SKILL.md step 6: almost always a `docs/backlog.md` seed or a maintenance
run through `capture`. The fix for a renamed flag is one line; it still
goes through the pipeline, because the audit that also fixes has
reviewed its own work.

## Headless (non-interactive) mode

The same procedure with no human to ask, for a scheduled CI job. Entry:
a headless agent invoked with a prompt that names this file and
SKILL.md **by path** — the agent reads them; nothing depends on the
skill being installed or routed to.

Headless changes three things and nothing else:

- **It writes nothing.** Not `docs/backlog.md`, not a doc fix, not a
  branch: a runner's writes are discarded, and an unreviewed commit is
  the failure this skill exists to prevent. The report on stdout is the
  whole product; the job publishes it (the run summary, an issue) and a
  human routes the findings.
- **It asks nothing.** Where interactive mode would ask, it records the
  open question under the finding and moves on.
- **It ends with a verdict line** the job can grep:
  `markdown-claims: N finding(s), M suspicion(s)`.

A no-finding run is a good run; it says so in one line and stops.

## Example CI workflow

Not shipped as a workflow — paste and adapt. It pins a checkout of this
plugin beside the repo, runs the mechanical pass (free, gating on its
own), then the headless pass (costs model spend, so weekly, and skipped
with a warning when the key is absent). Replace `<plugin-ref>` with a tag
or commit of the plugin repo.

```yaml
name: Docs claims audit

on:
  schedule:
    - cron: "17 11 * * 2"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  mechanical:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/checkout@v4
        with:
          repository: mattbutlerengineering/skills
          ref: <plugin-ref>
          path: .idea-to-prod
      - name: Mechanical claims (links, paths, commands)
        run: python3 .idea-to-prod/md_claims.py check .

  judgement:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/checkout@v4
        with:
          repository: mattbutlerengineering/skills
          ref: <plugin-ref>
          path: .idea-to-prod
      - name: Headless markdown-claims audit
        run: |
          if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
            echo "::warning::ANTHROPIC_API_KEY is not set; skipping."
            exit 0
          fi
          npm install -g @anthropic-ai/claude-code
          claude -p "Read .idea-to-prod/skills/audit/SKILL.md and
            .idea-to-prod/skills/audit/references/markdown-claims.md and run
            the audit claims scope on this repository in headless mode. The
            tool is at .idea-to-prod/md_claims.py." \
            --allowedTools "Read" "Grep" "Glob" \
              "Bash(python3 .idea-to-prod/md_claims.py *)" \
              "Bash(git log *)" "Bash(git show *)" \
            --max-budget-usd 2 \
            | tee report.md
          cat report.md >> "$GITHUB_STEP_SUMMARY"
```

The two jobs are independent on purpose: link and path problems are
reported even when the agent fails, and the agent run never waits on
them. The allowlist is the read-only rule made mechanical — the agent
cannot run a documented command it was not given.
