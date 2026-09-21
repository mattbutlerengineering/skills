# A skill that states repo facts runs a shipped tool

- Status: accepted
- Date: 2026-08-25

Every skill in this plugin has been prose plus static assets: the agent
reads instructions and references, and anything the skill asserts about
the world is re-derived by the agent at invocation time. That is fine
when the assertion is taste (a diagram's layout) and corrosive when it
is a repo-owned fact — the `pipeline-board` skill
(docs/features/pipeline-board/) must place every active run on the stage
the protocol's orientation table derives, and its PRD makes that parity
a success criterion. An agent re-deriving orientation from the protocol
doc on every invocation is a second live deriver of a fact
`protocol.py` already owns — untestable, unpinned, and exactly the
one-fact-many-owners class this repo hunts mechanically (ADR-0061) after
watching it recur seven times (docs/fixes/one-fact-one-owner/).

The packaging makes an alternative available: both harnesses ship the
whole repo checkout with the skills (the Claude Code plugin cache holds
the full tree; the omp package does too), so a skill can address a root
module relative to its own base directory the same way every stage
skill already addresses `../../docs/pipeline-protocol.md`.

## Decision

**A skill whose output must agree with a repo-owned fact does not
re-derive the fact — it runs a thin stdlib tool shipped in the same
checkout and consumes the tool's output verbatim.**

The tool is a root module, a thin caller of the seam that owns the
fact; the skill invokes it relative to the skill's base directory,
treats its output as the only source of that fact, and stops (surfacing
the tool's problem string) rather than guessing when the tool fails.
The prose side of the skill keeps everything that is taste — layout,
rendering, wording — and the tool keeps everything that is fact.

First instance: `pipeline-board` runs `board.py`, which states run
placement by calling `protocol.py`'s orientation; the skill renders the
JSON it receives and derives nothing.

## Consequences

- Parity between a skill's surface and the repo's facts becomes a unit
  test on the tool, not a hope about agent behavior.
- Packaging on every harness must carry root tools alongside skills.
  Claude Code's plugin cache already does. On omp this joins an open
  packaging question — the backlog already records that omp cannot
  traverse to `docs/pipeline-protocol.md`; that gap now covers tools
  too, and whatever answers it must answer for both.
- The precedent is deliberately narrow: prose-only remains the default
  skill shape. A skill earns a tool only when it states a fact some
  seam already owns; taste never does.
- A skill's tool is repo code: stdlib-only, tested, linted, and subject
  to the one-owner pass like any other module.
