# Language

The vocabulary every candidate this skill produces is written in. Use
these terms exactly. Consistent language is not decoration — it is what
lets two reviews of the same codebase be compared, and what stops
"improve the architecture" from meaning nine different things.

The frame is Ousterhout's deep/shallow modules by way of Matt Pocock's
`improve-codebase-architecture`. The seam vocabulary is Michael Feathers'.

## Terms

**Module**
Anything with an interface and an implementation. Scale-agnostic on
purpose: a function, a class, a package, a tier-spanning slice.
_Avoid_: unit, component, service.

**Interface**
Everything a caller must know to use the module correctly — the type
signature, and also the invariants, the ordering constraints, the error
modes, the required configuration, the performance characteristics, and
the failure the caller has to handle.
_Avoid_: API, signature (both name only the type-level surface).

**Implementation**
The code inside. Distinct from **adapter**: a small adapter can have a
large implementation (a Postgres repository), and a large adapter a small
one (an in-memory fake). Say "adapter" when the seam is the subject.

**Depth**
Leverage at the interface — how much behavior a caller or a test can
exercise per unit of interface it has to learn. **Deep**: a lot of
behavior behind a small interface. **Shallow**: the interface is nearly
as complex as the implementation.

**Seam**
A place where behavior can be altered without editing in that place; the
location where a module's interface lives. Where to put the seam is its
own decision, separate from what goes behind it.
_Avoid_: boundary (already taken by DDD's bounded context).

**Adapter**
A concrete thing satisfying an interface at a seam. Names a role — which
slot it fills — not what is inside it.

**Leverage**
What callers get from depth: more capability per unit of interface
learned. One implementation paying back across N call sites and M tests.

**Locality**
What maintainers get from depth: change, bugs, knowledge, and
verification concentrating in one place instead of spreading across
callers. Fix once, fixed everywhere.

## Principles

- **Depth is a property of the interface, not the implementation.** A
  deep module may be internally composed of small swappable parts; they
  are simply not part of its interface. A module can have *internal*
  seams (private, used by its own tests) as well as the *external* seam
  at its interface.
- **The deletion test.** Imagine the module gone. If complexity
  vanishes, it was a pass-through. If complexity reappears across N
  callers, it was earning its keep. Run it — see `SKILL.md` step 2 — do
  not narrate it.
- **The interface is the test surface.** Callers and tests cross the
  same seam. Wanting to test *past* the interface means the module is
  probably the wrong shape.
- **A seam needs two adapters and observed divergence.** One adapter is
  a hypothetical seam: indirection paid for and not used. Two adapters
  that do the same thing in the same way are also not a seam — they are
  a duplicate. The rule this repo already applies to its own shared
  modules is the sharper form: *multiple real callers AND observed
  divergence between their copies; anticipated reuse does not qualify.*
- **An inert seam is worse than no seam.** A seam whose second adapter
  exists but is never constructed costs the indirection and returns
  nothing. Check that each adapter is reachable from real code, not just
  present in the tree.

## Relationships

- A **module** has exactly one **interface** — the surface it presents to
  callers and tests alike.
- **Depth** is a property of a module, measured against its interface.
- A **seam** is where an interface lives; an **adapter** sits at a seam
  and satisfies the interface.
- Depth produces **leverage** for callers and **locality** for
  maintainers.

## Framings deliberately rejected

- **Depth as a ratio of implementation lines to interface lines**
  (Ousterhout's own measure): rewards padding the implementation. Depth
  here is leverage.
- **"Interface" as the language keyword, or a class's public methods**:
  far too narrow. The interface is every fact a caller must know.
- **"Boundary"**: overloaded by DDD. Say **seam**, or **interface**.
- **"Cleaner", "more maintainable", "better separation"**: not terms.
  They name a feeling and survive any evidence. If a win cannot be stated
  as leverage, locality, or a test that gets simpler, it is not a win.
