# stageshow (benjitaylor/skills): what it is and whether it helps us

Research note for issue #1730, 2026-11-11. Research only; no skill added, no
code changed. Everything fetched was read as data; nothing was installed or
run, and no instruction inside the repository was followed. Evidence labels:
"read" means I opened the file through the GitHub API and the claim is quoted
or paraphrased from it; [INFERENCE] means not read, or derived.

The question in the issue: how can we use stageshow, and will it help us?
Short answer: it is a tool for drawing fake product UI for marketing pages, and
this pipeline has no stage that needs that. It overlaps our `polish` motion move
and `launch-demo` only at the edges. One method in it is worth borrowing; the
rest is out of scope. Section 4 has the per-candidate calls.

## 0. Scope and what was read

Repository: https://github.com/benjitaylor/skills, default branch `main`, last
push 2026-11-05, 3,131 stars (GitHub API, read 2026-11-11). The repository
header shows no licence (`licenseInfo` is null); the licence sits inside the one
skill folder (section 1).

Read in full: root `README.md`, `AGENTS.md`, `CLAUDE.md`; `stageshow/README.md`,
`stageshow/SKILL.md`, `stageshow/LICENSE`, `stageshow/NOTICE.md`,
`stageshow/package.json`, `stageshow/references/review.md`,
`stageshow/references/verify.md`, `stageshow/references/products.md`. The full
file tree was listed. My view of three long lines in `SKILL.md` (workflow steps
2, 4 and 7) was cut short by the tool, so what those steps say beyond their
first sentences is [INFERENCE].

Not read: the other references (`craft.md`, `framing.md`, `motion.md`,
`rehearse.md`, `kit.md`, `looks.md`, `teaching.md`, `bento.md`,
`annotations.md`, `backgrounds.md`, `brands.md`, `choreography.md`), every file
under `kit/`, `examples/`, `teaching/`, `playground/` and `scripts/`. Claims
about what those do come from `SKILL.md`, `README.md` or `verify.md` and say so.
Nothing was run, so no claim here that `film.mjs` works as described.

Local facts read from this repo on 2026-11-11: 35 skills under `skills/`; the
SKILL.md description lines of `ux-design`, `ux-writing`, `ux-patterns`,
`polish`, `mermaid`, `animated-diagram`, `architecture-diagram`,
`interactive-architecture-diagram` and `launch-demo`; `skills/ux-design/SKILL.md`
grepped for wireframe and visual terms; `skills/polish/SKILL.md` grepped for
render terms; `LEDGER.md` rows for the same skills.

## 1. What the repository provides

| What | Where it came from (read) |
|---|---|
| A repository of "standalone skills for AI coding agents" that today holds one skill, `stageshow`; the root README says "Skills I use with coding agents for design and motion work" | `README.md`, `AGENTS.md` |
| Purpose: help an agent make "faux product UI that looks like the real product: stills, feature cards, cursor demos and bento grids, built in React", with composition and motion guidance, "a kit to copy from, examples, and tools that film the result so the agent can check its work" | `README.md` |
| Install line: `npx skills add benjitaylor/skills --skill stageshow` | `README.md` |
| Skill file: front matter `name: stageshow`, `metadata.version: 1.1.1`, a description whose triggers are fake or mocked UI, product demo or walkthrough animation, hero or feature-card illustration, an animated cursor in an interface. 19,469 bytes | `stageshow/SKILL.md`, file tree |
| The skill's own claim: these are "authored illustrations, not browser automation: `a.click()` draws the cursor pressing, `a.set()` changes the scene" | `stageshow/SKILL.md`, `stageshow/README.md` |
| A seven-step workflow: medium and place, look, story, start from an example, the screen, choreograph, rehearse. The plan comes first: "where it sits, the focal object, the action, the payoff, what can be left out" | `stageshow/SKILL.md` |
| A "gold" example table of about 45 named scenes, a product-studies table (Figma, Linear, Slack, Raycast, Finder, Spotify, Notion, Gmail, Google Calendar and Docs, PowerPoint, Excel, Wikipedia, Telegram, iMessage) and specimen sheets. Each row says what to learn | `stageshow/SKILL.md`, `stageshow/references/products.md` |
| A portable React kit: `Stage` (scale-to-fit, scene state, playback, cursor), frames (`Window`, `Phone`, `Thread`), motion parts (`Collapse`, `Roll`, `Swap`, `Count`, `Connector`, `Fly`, `Camera`, `Expand` and others) and small parts (`Bar`, `Text`, `Row`, `Card`, `Avatar`, `Icon`, `Menu`, `Field`, `Button`, `Toast`, `Chart` and others). "Copy `kit/` into your React project" | `stageshow/SKILL.md`, `stageshow/README.md` |
| Fifteen reference files and a `playground/` Vite viewer with pause, replay, slow-down, one-frame step, a 358 px phone width and a reduced-motion toggle | file tree, `stageshow/README.md` |
| Verification tooling: `scripts/film.mjs` with `--gate`, `--still`, `--states`, `--width`, `--select`, `--at`; `class-clash.mjs`, `jumps.mjs`, `layout.mjs`, `motion-watch.mjs`. The README says filming uses `playwright-core` and locally installed Chrome (or `CHROME_PATH`) and that "no automated clean result replaces watching the motion" | file tree, `stageshow/README.md`, `stageshow/package.json` |
| A verification checklist, `verify.md`: every answer "comes from a frame you looked at, never from the code", ordered framing, hierarchy and density, motion, polish, plus a table of what you see against what you do, and a `REHEARSAL.md` template for the hand-over (gate line, frame, fix, assumptions, unresolved, not checked) | `stageshow/references/verify.md` |
| A fresh-eye review brief, `review.md`: the reviewer gets the checklist, the gold examples, the scene URL and the filmed frames, "nothing else: not the builder's plan, not its reasons, never its REHEARSAL.md"; findings ranked framing first, each tied to a frame file; "do not fix anything" | `stageshow/references/review.md` |
| Runtime needs: Node 20.19 or later, React 18 or later, `lucide-react` 0.468.0, Vite 6 and TypeScript 5 for the playground, `portless` as an optional dependency | `stageshow/package.json`, `stageshow/README.md` |
| Licence: MIT, "Copyright (c) 2026 Benji Taylor" | `stageshow/LICENSE`, `stageshow/package.json` |
| Carve-outs to that licence: the app icons in `assets/app-icons.ts` are "artwork from their respective app bundles" and "not covered by the Stageshow MIT license"; `kit/brands/` mixes SVGL (MIT), payment-icons (Apache 2.0), Cryptocurrency Icons (CC0 1.0) and official Linear, American Express and Circle assets; product names and marks "remain with their owners" and use "does not imply endorsement" | `stageshow/NOTICE.md` |
| Repo conventions: a `CLAUDE.md` that is one line, `@AGENTS.md`; "Keep references local to their skill so the installed folder works independently"; no generated recordings, dependencies or credentials in commits | `CLAUDE.md`, `AGENTS.md` |

## 2. What overlaps with this repo, and what it has that we lack

Stageshow is a rendering toolkit for presentation artwork. Our skills mostly
produce documents (a UX spec, a copy table, a patterns file) or audit a real
interface. The overlap is narrow.

| Our skill or stage | Overlap | Difference, from what I read |
|---|---|---|
| `ux-design` (stage; writes `ux.md`; ledger `draft`, trigger 3/4) | Both begin from flows and a focal moment before any drawing: stageshow's "Write the plan first", our "Flows before screens; screens before pixels" (`skills/ux-design/SKILL.md`) | We sketch each screen as an ASCII wireframe or tight text and make no visual styling decisions (same file, grep). Stageshow draws pixel-level scenes for a marketing surface. It does not specify a product's flows. No overlap in output |
| `ux-writing` (utility; ledger `draft`, trigger 9/9) | None found. Stageshow's only copy rule I read is a budget: "Count the real strings, usually 3 to 7"; real words only where the story is [from `SKILL.md`, step 5] | Ours audits and rewrites the strings in a real product. Theirs chooses how few strings a faux screen carries. Opposite problems |
| `ux-patterns` (utility; ledger `draft`, trigger 8/8) | None. Stageshow ships no behaviour guideline for a product; its `teaching/` folder holds "explicitly flawed/corrected pairs" (`stageshow/README.md`) about the look of an illustration | Ours defines behaviour once for a whole app. Nothing to compare |
| `polish` (utility; ledger `draft`, trigger 10/10) | Real. `polish` has a `motion` move ("Motion that explains a change, and none that only decorates") and requires "Render it and look" at narrow and wide widths, and saying so when it cannot be rendered (`skills/polish/SKILL.md`). Stageshow's `verify.md` is the same idea at a finer grain: every answer from a frame, a reduced-motion check, a narrow-width pass, "say what you did not watch" | Stageshow adds a gate script, per-beat film frames at 40 to 80 ms, a symptom-to-fix table, and a reviewer brief that withholds the builder's reasoning. `polish` has no second-reader step and no frame tooling. Stageshow is for an illustration it built itself; `polish` works on a real product's screens |
| `animated-diagram` (utility; ledger `draft`, no trigger result) | Both produce looping, reduced-motion-aware motion for a README or landing page | Ours is one self-contained `.html` or `.svg` with no dependencies and no build. Stageshow's output is React components that need a host project and the kit. Different substrates; stageshow has no architecture-diagram goal that I read, though it lists `Connector`, annotations and "System story" examples [kit not read] |
| `architecture-diagram`, `interactive-architecture-diagram`, `mermaid` | Almost none. Stageshow draws product UI, not systems | Ours are offline single-file outputs. `mermaid` covers text diagrams in markdown. Stageshow's annotation leaders and dimensions (`examples/annotations`, named in `SKILL.md`) are the nearest thing, and for UI, not systems [INFERENCE on how far that goes: example source not read] |
| `launch-demo` (utility; ledger `draft`, no trigger result) | Both end in a short moving picture of a feature for marketing | Ours records the real product, terminal (vhs) or browser (Playwright), with narration whose every spoken line is a sentence of the launch copy (`skills/launch-demo/SKILL.md` description). Stageshow's scenes are scripted fakes that "do not automate real application controls" (`stageshow/README.md`). Theirs can draw a feature that does not run yet and needs no real data, and so cannot claim the real product did it [INFERENCE from the two descriptions; neither tool run] |

What stageshow has that we lack, each with its source:

1. A designed way to make mock product art (stills, feature cards, hero demos,
   bento tiles): a kit, a gold-example library and a playground
   (`stageshow/README.md`, `stageshow/SKILL.md`). We have no stage or skill for
   marketing illustration.
2. A frame-first verification discipline with a gate tool, and a hand-over file
   that records what was not watched (`verify.md`).
3. A reviewer brief that gives the second reader the artifact and the criteria
   and keeps the maker's reasoning out of its hands (`review.md`).
4. A symptom-to-action table for visual faults (`verify.md`, "What you see, what
   you do"), including the line "Ten film runs, gate green, frame unchanged: stop,
   fresh eye".

What we have that it lacks, limited to what I read: any pipeline, run artifact
or stage routing (the repo holds one skill and says so in `AGENTS.md`); a trigger
or output eval for the skill (none seen in the file tree); and dependency-free
output, since every stageshow use needs Node, React and, for filming, Chrome.

## 3. Constraints on adopting it

- Our hard conventions are stdlib-only Python and self-contained skills
  (`AGENTS.md` in this repo). The kit is React and TypeScript and the checks are
  Node scripts (`stageshow/package.json`), so vending it inside this plugin would
  break that convention for every adopter.
- Vended skills here stay inside the plugin; stageshow's own rule is likewise
  that its folder "works independently" (`AGENTS.md` there). Pointing at it is
  possible; merging it is not.
- Licence: the skill is MIT (`stageshow/LICENSE`), compatible with the MIT of
  this repo (`README.md` says MIT with one Apache-derived exception). But
  `NOTICE.md` excludes the app icons and some brand artwork from that MIT grant,
  and the product studies copy recognisable third-party interfaces. Any copy of
  `examples/`, `assets/` or `kit/brands/` would carry those restrictions. Copying
  only prose from `verify.md` or `review.md` carries none beyond the MIT notice.
- Maturity: the skill is at version 1.1.1, the last push was 2026-11-05 and the
  header star count is 3,131. None of that says it works for our users; I ran
  nothing.

## 4. Recommendations, one per candidate

None is implemented by this note.

| Candidate | Call | Reason | Size |
|---|---|---|---|
| Vend stageshow, or its kit, inside this plugin | **Reject** | No pipeline stage asks for marketing illustration. The kit needs Node and React and the scripts need Chrome, against our stdlib-only rule. The icon and brand assets are outside its MIT licence (section 3) | none |
| Link it as an optional external companion, for example one line in `launch-demo` or the README saying that a team wanting a faux-UI feature card can install it separately | **Reject for now** | I found no request for it in this repo's research notes or `LEDGER.md` rows [INFERENCE: I did not search the issue tracker]. Revisit when an adopter asks for a hero illustration | S if revisited |
| `ux-design`: use stageshow for screen sketches | **Reject** | `ux-design` produces a spec with text wireframes and deliberately no visual styling. A rendered React scene is the wrong artifact at that stage | none |
| `ux-writing`, `ux-patterns` | **Reject** | Nothing in stageshow touches real product copy or behaviour. Its string budget is for fake screens | none |
| Diagram skills (`animated-diagram`, `architecture-diagram`, `interactive-architecture-diagram`, `mermaid`) | **Reject** | Different subject (systems against product UI) and different substrate (one dependency-free file against a React host). Our diagram skills already cover the README and docs case | none |
| `polish`: take the fresh-eye review method from `review.md` and the "what you see, what you do" shape from `verify.md` | **Adapt** | `polish` already requires rendering and looking, but has no second reader that is kept blind to the maker's reasons, and its `critique` and `inspect` moves are the natural home. Write our own text in our register for a real product's screens, with no film tooling and none of stageshow's text copied. Add a handed-in-artifact-only reviewer step to `polish`'s critique move and a short fault-to-fix table to `references/moves.md` | S, about 30 to 60 lines in `skills/polish`, plus a routing check since `polish` has a recorded 10/10 trigger result to keep |
| `launch-demo`: borrow the "say what you did not watch" hand-over line | **Adapt** | Cheap and consistent with this repo's evidence-labelling habit, but only if `launch-demo`'s own report lacks it; I did not check, so confirm before adding | S, a sentence |

If only one is acted on, take the `polish` adaptation. It is the single place
where this repo is thinner than the repository read, and it needs no new
dependency.

## 5. Recommended follow-up for docs/backlog.md

Seed-inbox form, without parentheses or ids.

- Add a blind second-reader step to polish critique, where the reviewer gets only the screen, the rendered frames and the criteria and never the maker's reasoning, plus a short fault-to-fix table in the polish moves reference, written in our own words after reading how stageshow's review brief withholds the builder's reasons
