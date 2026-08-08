# Deepening

How to deepen a cluster of shallow modules safely, and how to design the
interface that results. Assumes the vocabulary in
[`language.md`](language.md).

## Dependency categories

Classify a candidate's dependencies before proposing anything. The
category decides how the deepened module is tested across its seam — and
sometimes decides that the deepening is not available at all.

**1. In-process.** Pure computation, in-memory state, no I/O. Always
deepenable: merge the modules, test through the new interface directly.
No adapter, no port.

**2. Local-substitutable.** A dependency with a real local stand-in that
runs in the suite (an embedded database, an in-memory filesystem).
Deepenable *if the stand-in already exists* — "we could add one" makes
this a two-step recommendation, and the stand-in is step one.

**3. Remote but owned.** Your own services across a network. Define a
**port** at the seam: the deep module owns the logic, the transport is an
injected **adapter**. In-memory adapter in tests, HTTP/queue adapter in
production. Two adapters, both real — the seam is justified.

**4. True external.** Third-party services you do not control. The
module takes the dependency as an injected port; tests supply a mock
adapter. The interface must state the failure modes the real service
actually has, or the mock will make the module look more reliable than it
is.

## Seam discipline

- Two adapters justify a seam; one is indirection. Production plus test
  is the usual honest pair.
- Do not expose an internal seam through the interface just because the
  module's own tests use it. Internal seams stay internal.
- Check that every adapter is *constructed* somewhere reachable. An
  adapter that only exists is an inert seam ([`language.md`](language.md)).

## Test ordering — the part that is a hazard

"Replace, don't layer" is right: once tests exist at the deepened
module's interface, the old unit tests on the shallow parts are waste,
and keeping both means every change costs two edits.

The ordering is what makes it safe, and it is not optional:

1. Write the new tests at the intended interface **first**, against the
   code as it stands today. They will be awkward — that awkwardness is
   the measurement of how shallow the current shape is.
2. Deepen. The new tests keep passing throughout; they are the net.
3. **Then** delete the old shallow-module tests, in the same change, and
   say in the diff which coverage moved where.

Deleting first, or deepening first and testing after, removes the net
before the replacement exists. Every proposal this skill makes states
which existing tests die and which new ones must exist before they do.

Tests assert observable outcomes through the interface, never internal
state. A test that must change when the implementation changes was
testing past the interface, and it should be counted as a cost of the
current shape, not of the deepening.

## Designing the interface twice

Ousterhout's rule: the first design is unlikely to be the best. When the
user wants to explore the shape of a chosen candidate, run this rather
than proposing one interface confidently.

**1. Frame the space, out loud.** Before dispatching anything, write for
the user: the constraints any interface must satisfy, the dependency
category from above, and a rough code sketch that makes the constraints
concrete. It is not a proposal — it is a way to be specific about what is
fixed. The user reads it while the agents work.

**2. Dispatch three or more, in one message, each with a different
constraint.** They run concurrently and must not see each other's work:

- *Minimize the interface* — one to three entry points, maximum leverage
  per entry point.
- *Maximize flexibility* — many use cases, extension points.
- *Optimize the common caller* — the default case becomes trivial.
- *Ports and adapters* — when the dependency category is 3 or 4.

Each brief carries the file paths, the coupling as it actually is, the
dependency category, what sits behind the seam, and both vocabularies —
[`language.md`](language.md)'s and the repo's own glossary — so the
designs come back nameable in the same terms.

Each returns: the interface (types, and the invariants, ordering, and
error modes that are also part of it); a usage example from a real call
site; what the implementation hides; the adapter strategy; and where the
leverage is thin.

**3. Check before presenting.** A returned design is a proposal about
code the agent read quickly. Take its usage example to the real call
sites it claims to serve and confirm they can actually be written that
way. A design that does not fit the callers is not a design; it is a
suggestion to change the callers, which is a different and larger
proposal that must be priced as one.

**4. Present sequentially, then compare in prose** — by depth (leverage
at the interface), locality (where change concentrates), and seam
placement. Then give your own recommendation and say why. Propose a
hybrid when elements combine well. Be opinionated: a menu is not advice.
