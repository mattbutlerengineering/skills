# Automation catalog

The six categories, each with the same four questions answered: what it
is, **what evidences it**, what makes it inert, and what it costs. Read
the categories you are sweeping plus `## Recommendation format` at the
bottom.

The evidence question is the one that matters. Every category below can
be recommended from marker files alone, and every such recommendation is
worthless — it would be equally true of a repo you have never seen. What
makes a recommendation worth reading is the located friction.

---

## 1. Hooks

Shell commands the harness runs around tool use: `PreToolUse` (before,
can block), `PostToolUse` (after, for formatting and checks),
`SessionStart`, `Stop`. Configured in `settings.json`.

**Evidenced by:**

- A formatting or lint step that CI runs and nothing runs locally, plus
  history showing "fix lint" commits — the fix belongs at write time, not
  at review time.
- A rule in `CLAUDE.md` phrased as an instruction to the agent that the
  agent demonstrably violates in the history ("always run X before Y",
  followed by commits where X did not run).
- A generated file that must be regenerated whenever a source changes,
  where the history shows it being forgotten. This is a `PostToolUse`
  hook on the source's path, and it is one of the highest-value hooks
  available because the failure is silent until a later gate.
- A destructive command that has actually been run by accident.

**Inert when:** the matcher names a tool the repo's work never touches;
the command depends on a binary the environment does not have; a
`PreToolUse` hook blocks on a substring that legitimate code contains, so
the real outcome is that contributors learn to route around it.

**Costs:** latency on every matching tool call, forever. A blocking hook
costs more than its runtime — it costs the workflow of everyone it stops
wrongly. Price the false-positive path. A hook whose command can fail for
environmental reasons needs a decision about whether that failure blocks.

**Kept honest by:** nothing, usually — hooks are configuration and most
repos never test them. Say so; it is part of the cost.

---

## 2. Subagents

Task-scoped agents with their own context, tool set, and system prompt,
defined in `.claude/agents/*.md`.

**Evidenced by:**

- A recurring task that reads far more than it writes — a review pass, a
  security sweep, a dependency check — where the reading pollutes the
  main context and the conclusion is short.
- Work the repo already fans out by hand, visible as several near-identical
  prompts in a run's artifacts.
- A task with a *restricted* tool set as the point: a reviewer that must
  not write, an explorer that must not commit. The restriction is the
  value; a subagent that just "does the task in another context" is
  usually a skill instead.

**Inert when:** nothing dispatches it. Two specific traps in Claude Code,
both silent:

- the agent file has no frontmatter `name:` — the registry keys on that
  field, not the filename, so the type resolves as not found;
- the registry is snapshotted at session start, so an agent added
  mid-session is undispatchable until a fresh session. A recommendation
  that ends "and then use it" is wrong about when.

**Costs:** tokens per dispatch, and the loss of the parent's context — a
subagent inherits none of the calling skill, so every fact it needs must
be in its prompt. That prompt is a maintenance surface.

**Kept honest by:** a check that every `subagent_type` named in the repo
resolves to an agent file with a matching `name:`. Cheap, and catches the
first trap above.

---

## 3. Skills

Packaged instructions the agent loads when a task matches — a `SKILL.md`
with a description that acts as the routing key.

**Evidenced by:**

- A workflow written down somewhere in prose that a human re-explains
  each time: a runbook, a "how we do X here" doc, a checklist in a PR
  template.
- A sequence the repo's own artifacts show being followed inconsistently
  — the same steps in a different order across two runs.
- A task whose hard part is *judgement encoded as rules* rather than
  commands. Commands belong in a `Makefile`; a skill is for the part
  where the rules disagree.

**Inert when:** its description overlaps an installed skill's, so the
router chooses between them by accident. Before recommending one, read
the descriptions of what is already installed and say which pair could
collide — that is a real finding whether or not the new skill ships.

**Costs:** a description in the router's namespace. The price is not the
file; it is what the addition makes ambiguous. A skill also needs a home:
in a repo that vends a plugin, adding one means registration, ledger,
docs, and evals — name that cost, do not hide it behind "just add a
SKILL.md".

**Kept honest by:** a routing eval — cases that must fire it, and
near-miss cases against the skill it most resembles. A skill with no
near-miss case has not been shown to be distinguishable.

---

## 4. Plugins

A distribution unit: several skills, agents, hooks and MCP config
versioned and installed together.

**Evidenced by:**

- Three or more skills already sharing a vocabulary or a protocol
  document, copied between repos by hand.
- A second repo that needs the same set — the copy is the evidence.

**Inert when:** there is one consumer. A plugin for a single repo is a
directory with a manifest and a release process on top, and the release
process is the whole cost.

**Costs:** versioning, a marketplace or install path, and the
compatibility question every future change now has to answer.

**Kept honest by:** an install test — a scratch consumer that installs
the plugin and exercises one skill end to end.

---

## 5. MCP servers

External tool surfaces the agent can call: databases, APIs, browsers,
issue trackers.

**Evidenced by:**

- The repo already shelling out to a CLI for the same service in several
  places, with the failure handling copied and diverging between them.
- A workflow that requires the human to leave the session, do something
  in a web console, and come back — where the thing done has an API.

**Inert when:** the repo does not call that service; the server needs a
credential nobody has provisioned; the harness that runs the repo's
automation is headless and the server authenticates interactively, so it
is present in local sessions and absent in every scheduled run. That last
one is the trap worth checking explicitly — it makes a scheduled job fail
in a way that looks like a code defect.

**Costs:** a network dependency, an auth surface, and a tool schema
occupying every context window that loads it. Where an existing CLI
already does the job under the same credentials, the CLI is usually
cheaper and the recommendation is to say so.

**Never** put a credential value in the recommendation. Name the variable
and the store it comes from.

**Kept honest by:** a startup check that the server resolves and
authenticates in the environment that will actually run it — not the one
you are standing in.

---

## 6. Drift detectors

A check that fails the build when a stated rule stops holding. This
category is not in the automation catalogs this skill descends from, and
it is usually the highest-leverage one available.

**Evidenced by** — and this is the whole method — reading everything the
repo *asserts* about itself and asking, for each assertion, what fails if
it stops being true:

- Conventions in `CLAUDE.md` / `AGENTS.md` / `CONTRIBUTING`: "always X",
  "never Y", "these two files stay in lockstep".
- Decisions in `docs/adr/` that describe an invariant rather than a
  choice.
- Anything generated from something else — a manifest, a lockfile, a
  mirrored copy, a checksum — where the generator is run by hand.
- A rule the history shows being broken and repaired.

If the answer is "nothing fails, someone notices eventually", that is the
recommendation.

**Inert when:** the check is satisfiable without the property it claims
to enforce — it greps for a keyword the convention happens to use rather
than testing the behavior. This is the worst outcome in the whole
catalog, because the rule now *looks* enforced and nobody looks again.
Before recommending a detector, state the change that should fail it and
confirm the proposed check would actually catch that change.

**Costs:** a false-positive budget. A detector that fires on good changes
gets disabled or worked around, and a disabled detector is worse than no
detector.

**Kept honest by:** a self-test — plant the violation, assert the
detector fires, remove it, assert it does not. A detector with no
planted-violation test is an assertion about itself.

---

## Recommendation format

One row per recommendation, and every field is required:

- **Recommendation** — one line, imperative. "PostToolUse hook
  regenerating `manifest.json` when anything under `templates/` is
  written."
- **Category** — one of the six.
- **Friction** — the located evidence. `path/file:line`, a commit range,
  or the artifact that records the manual step. Not a category of
  friction: the instance.
- **What constructs it** — the matcher, the dispatcher, the caller. If
  this field is hard to fill, the recommendation is inert.
- **Cost** — from the category's cost paragraph, made specific to this
  repo.
- **How it fails** — the false-positive path, or the way it goes silently
  inert.

A candidate missing **Friction** or **What constructs it** is not a
recommendation. It is a suspicion, and it goes in the suspicions list
with what would settle it.
