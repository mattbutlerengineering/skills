# Canon

The design rules that constrain what this skill may draft. Not style
preferences: each one changes an answer the template asks for, and each
one names a mistake that is cheap to make at design time and expensive
to discover later.

`deepen` carries the same body of thinking applied *after* the code
exists, where every fix is a refactor. This is the cheaper end of it.
Read this before drafting, not while reviewing the draft.

## The vocabulary is not this file's

**Module, interface, implementation, depth, seam, adapter, leverage,
locality** are defined by the `deepen` skill and mean the same thing
here. Do not restate them, and do not drift into "component" (the
template's own section heading is the one exception), "boundary", or
"layer" as design terms.

That matters more than tidiness, because the books below use words this
repo has already spent. Translate as you read them:

| The source says | Write |
|---|---|
| boundary (Clean Architecture) | **seam** — "boundary" is taken by DDD's bounded context |
| layer, circle (Clean Architecture) | **policy** and **detail**, plus the direction between them |
| deep module (A Philosophy of Software Design) | **depth** — but as leverage per unit of interface, not a line-count ratio |

## Approach

**Reduced complexity is the success metric, not fewer parts.** The design
that wins is the one that lowers how much a reader must hold at once to
change the system safely. More files, smaller classes, and extra
indirection are all neutral until measured against that.

**Compare at least two shapes before writing the approach paragraph.**
The first shape you think of is a sample of one. This does not need to
be ceremony — one paragraph on the alternative and why it loses is
enough, and it lands in *Decisions & alternatives* anyway.

## Components

**Source dependencies point toward policy.** Business rules must not
import frameworks, HTTP handlers, ORM rows, queue clients, UI types, or
vendor SDKs. When policy needs something from the outside, policy owns
the interface and the outer code implements it. Getting this backwards
is the single most expensive design error here, because unwinding it
later means touching every rule that leaked.

**Split by capability before technical kind.** `orders/`, `billing/`
beats `controllers/`, `services/`, `models/`. A structure that names
what the system does survives a framework change; one that names what
the framework calls things does not.

**Adapters stay humble.** Controllers, handlers, presenters, repository
implementations, and gateway clients translate formats and call inward.
The moment one of them holds a business rule, that rule is now
untestable without the transport it happens to sit behind.

**A component that only forwards is not a component.** Apply the
deletion test at design time: if this component vanished, does
complexity reappear across its callers, or does it simply disappear? If
it disappears, you have drawn a name, not a module.

## Data model

**Choose the model from the access patterns, not from the entity
diagram.** Write down the handful of reads and writes the PRD actually
requires, then pick the shape that serves them. A model chosen from a
picture of the nouns tends to be discovered wrong at the first
list-with-filters screen.

**Invariants live with the entity that owns them.** If a rule spans two
entities, say which one owns it and how the other learns about it. An
invariant with no owner is enforced in whichever call site remembered.

**Say which consistency you need, per interaction, before choosing
storage.** "Must be true the instant the request returns" and "may
settle within seconds" are different requirements with different
costs, and conflating them is how a design acquires a distributed
transaction it never needed.

## Interfaces & contracts

**Depth is the test.** Every interface in the design should hide more
than it exposes. If describing what a caller must know takes about as
long as describing what the thing does, the interface is shallow and
the design has not paid for it yet.

**The interface is every fact a caller must know** — not the signature.
Ordering constraints, required configuration, which errors are
recoverable, what happens on retry, and what it costs are all part of
the contract, and all of them belong in the artifact's *Failure modes*
and *Input/Output* lines rather than in someone's head.

**Failure is part of the contract, and remote failure is a design
input.** For every interface crossing a process or network seam, state
the timeout, what the caller sees when it trips, and whether retrying is
safe. An interface that only describes its happy path has deferred its
hardest question to whoever implements it.

**One adapter is a hypothetical seam; two make it real.** Do not
introduce a port, an interface, or a strategy for a single
implementation. Production plus a genuine test double counts as two;
"we might swap this someday" does not.

## Stack & dependencies

**Volatility decides what sits behind a seam.** The things that change
on someone else's schedule — vendors, frameworks, third-party APIs,
storage engines — are the things worth isolating. Stable, ubiquitous
dependencies do not need a seam and pay for one in indirection.

**A dependency's cost is its interface, not its size.** A large library
behind three calls is cheaper than a small one whose types spread
through every signature in the codebase. Say which of the two a new
dependency is.

## Stop and reconsider when

- Policy needs to import a framework type, a schema class, or a
  transport format to compile. Move the translation outward instead.
- A component is named `*Service`, `*Manager`, `*Helper`, `common`, or
  `core`. These are the names a design uses when it has not decided what
  the thing owns.
- A rule appears in two components. One of them owns it; the other
  should be asking.
- A test of a business rule would need the database, the network, or the
  framework to run. The rule is on the wrong side of a seam.
- Schedule pressure is the argument for skipping a seam. That may be the
  right call — record it in *Decisions & alternatives* with the cost, so
  it is a decision rather than an omission.

## Before writing the artifact

- Does every interface hide more than it exposes?
- Do all source dependencies point toward policy, with policy owning the
  interfaces it needs?
- Does each component have one owner-responsibility that survives
  deletion-testing?
- Is the data model justified by named access patterns and named
  consistency requirements?
- Does every cross-process interface state its timeout, its failure
  mode, and whether retry is safe?
- Does every seam have two adapters, or a recorded reason it does not?

## Sources

Robert C. Martin, *Clean Architecture* (dependency direction, policy and
detail, humble adapters). John Ousterhout, *A Philosophy of Software
Design* (complexity as the metric, depth, information hiding). Martin
Kleppmann, *Designing Data-Intensive Applications* (access patterns,
consistency as a per-interaction choice). Michael Nygard, *Release It!*
(timeouts and failure as contract). Michael Feathers, *Working
Effectively with Legacy Code* (seams). Distilled to the decisions this
stage makes; none of it is quoted.
