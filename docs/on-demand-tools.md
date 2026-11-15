# On-demand tools

Tools this repo keeps outside CI and outside `make check`. `CLAUDE.md`
names them and points here; read a tool's entry before running it.

On demand only (real model runs, costs money, never CI; all three need
the `claude` CLI):

- `python3 trigger_eval.py` — routing eval
- `python3 charter_replay.py` — charter regression suite: golden fixture
  work orders replayed against the role charters. Its scoring seam is pure
  and injected, so CI covers degradation detection offline with recorded
  transcripts; only the live replay costs money. `--control` also replays
  each case with its charter's `## Must never` section deleted and fails
  any case whose stripped run never fires a forbidden pattern (a trap the
  model never takes guards nothing); it doubles the cost.
- `claude plugin eval . --scaffold --model claude-sonnet-5
  --judge-model claude-haiku-4-5 --max-cost-usd 15 --no-publish
  --allow-tools Write Edit "Bash(python3 *)" "Bash(git *)"` — per-skill
  with/without-plugin delta over `plugin-evals/` (the manifest's
  `experimental.evals`, so `evals/results/` is never written; ADR-0081).
  `--tag <skill>` runs one suite. Output lands in gitignored
  `plugin-evals/results/`. A cited run's `aggregate-result.json` is
  copied unedited to append-only `plugin-evals/records/<date>[-N].json`.
  It is eval evidence and never graduates LEDGER maturity.
  <!-- drift-ignore: aggregate-result.json -->

Also on demand, but free and needing nothing installed — a review
pre-pass, deliberately **not** a gate:

- `python3 one_owner.py` — which facts this repo's own Python modules
  state twice (the same value in two modules, or two functions reading
  the same payload keys), as `one-owner:` problem strings. It is outside
  `make check` and outside every workflow, so a finding never colours
  main red — it is a question for a human. A deliberate second owner is
  recorded with a `# one-owner:` marker at the definition it excuses
  (ADR-0061), and the pass re-derives that carve-out in both directions
  on every run.
- `python3 decompose_signals.py` — Decompose outcome signals (re-plan,
  design gaps routed to Architect, review-traced findings) per run and in
  aggregate, read from the git refs the clone already holds, each
  boundary labelled observed or inferred (ADR-0109). Free and outside
  every gate, like `one_owner.py`. It never fetches: PR head refs count
  only after the manual `git fetch origin
  '+refs/pull/*/head:refs/remotes/pr/*'`. `--record` writes the result
  append-only to `evals/results/decompose-signals-<date>[-N].json`, on a
  clean `docs/` only; factory evidence, never LEDGER evidence.
- `python3 eval_trends.py` — a per-surface pass-rate trend view over the
  records the repo already holds (`evals/results/`, `plugin-evals/records/`),
  grouped by comparable suite and case set, each rate with a Wilson 95
  percent interval, and cost per pass where a plugin record carries a cost
  (ADR-0115; the metric set and its failure modes are in
  `docs/research/eval-quality-metrics-2026-10-21.md`). Free, read-only and
  outside every gate: it makes no model or network call and writes nothing,
  so it also sits outside `make check`. Below the minimum (30 cases in every
  record, 2 distinct days) it prints an inventory and `REFUSED` lines in
  place of a trend, and a refusal exits 0 (it is data); only a malformed
  record exits 1. It measures recorded history only and moves no LEDGER
  maturity. `python3 factory.py eval-trends` is the same tool.
- `python3 size_band_calibration.py` — each S/M/L band's past cost
  error against its budget, from the cost ledger joined at read time to
  the breakdown row's `size:`, beside its cost and re-plan rate. Free,
  outside every gate and making no network call, like
  `decompose_signals.py`. It refuses a band below the calibrate floor and
  says so, and excludes unmetered rows with a count, never an estimate.
- `python3 decompose_lessons.py` — the Decompose lessons ledger (ADR-0113):
  contrast pairs of a hit run and a clean run, from the three outcome
  signals only, collapsed to voted, sourced lessons in
  `docs/factory/decompose-lessons.jsonl`, plus a treated-versus-untreated
  re-plan comparison. Free, outside every gate and making no network
  call, like `decompose_signals.py`. With no argument it only reads;
  `update` is the one writer and the Owner runs it. No command takes
  lesson text from a person, and the tool ships no lesson.
  <!-- drift-ignore: docs/factory/decompose-lessons.jsonl -->
- `python3 decompose_grade.py <breakdown.md> <architecture.md> [<prd.md>]` —
  scores a produced Decompose breakdown against the architecture it was
  drafted from and prints one line per defect (a component no item names, a
  dangling `Blocked by`, an uncheckable `Accept` line, an item spanning more
  than three components), exit 0 clean, 1 with defects, 2 on bad input
  (ADR-0114). Free and outside every gate, making no model or network call,
  like the two above. It is calibrated to fixture-spelled breakdowns and is
  not a retroactive audit of shipped runs. Its harness counterpart,
  `plugin-evals/decompose/`, is authored and has never been run; there is no
  LEDGER change.
- `python3 voice_grade.py <reply.md> [<reply.md> ...]` — prints each
  reply's proxy token count and one line per house-voice slop pattern
  found outside code, exit 0 clean, 1 on any slop, 2 on bad input
  (ADR-0119). Free and offline, outside every gate and outside `make
  check`, like the three above. The count is a proxy, not Claude's
  tokenizer: it is valid only for comparing two replies to the same
  prompt. `python3 factory.py voice-grade` is the same tool.
- `python3 svg_check.py <file.svg> [--embed-width PX]` — refuses a DTD or
  entity without expanding it, names every duplicate id, dangling
  `url(#…)` or `href`, external link and missing root `width`/`height` in
  a diagram SVG, and reports its smallest text size at the embed width
  (default 830px). Exit 0 clean, 1 with defects, 2 when the file was not
  checked. Free and offline, outside every gate and outside `make check`,
  like the four above. The size is a report, never a failure.
  `animated-diagram`'s step 7 runs it. `python3 factory.py svg-check` is the
  same tool.
- `python3 reap_worktrees.py [--apply | --no-fetch]` — reaps merged, idle
  worktrees under `.claude/worktrees/` by the four tests in
  `.claude/implement-queue.md` `## reap`. A dry run unless `--apply`: it
  removes no worktree or branch, but it fetches and prunes remote-tracking
  refs unless `--no-fetch` (refused with `--apply`). Never `--force`, never
  the main checkout or a worktree elsewhere (listed with its size), and a
  failed command or fetch is a failure, never a pass. Root-only and outside
  every gate (ADR-0128); it needs `git`, `gh` and `lsof`.
  <!-- drift-ignore: .claude/worktrees/ -->

External, never a dependency and never CI (the repo is stdlib-only):
installed into a throwaway virtualenv outside the repo, and a review
pre-pass only, like the free tools above:

- NVIDIA SkillEvaluator (`skillevaluator`, a pip package) — validates a
  skill against the Agent Skills spec. Install with `uv venv --python
  3.12 <tmp>/.venv && uv pip install --python <tmp>/.venv/bin/python
  skillevaluator`, then per skill `<tmp>/.venv/bin/skillevaluator validate
  skills/<name> --tiers 1 -r json -o <tmp>/r/<name>`. Tier 1 is offline
  and free; Tier 3 (live agent evaluation) needs a model key and costs
  money. A plugin-level run goes over a `git archive origin/main
  .claude-plugin skills` export, never the checkout: on the checkout it
  walks `.claude/worktrees/` and did not finish in 10 minutes, and even
  the 744 KB export takes over 10 minutes. Exit 0 pass, 1 changes
  required (any failed Tier 1 validator). It is good for the spec's
  schema (it found the missing `metadata.author`), secrets and
  unicode-smuggling scans, and a second opinion on description overlap.
  Never evidence for (false positives on this repo's skills, observed
  2026-11-15 with skillevaluator 0.9.0 at origin/main 81adfe1):
  - PII-CRITICAL on any `scheme://user:password@host` URL, placeholders
    included (`USER:PASSWORD@HOST` fails too); `prisma-migrations`'
    examples need the password segment.
  - Security "Hidden Instructions" on the repo's own HTML-comment
    markers: the md-claims ignore marker, the drift-ignore marker and SVG
    authoring comments.
  - "Tool misuse", "anti-refusal" or "credential access" on text that
    forbids the thing or names it in a diagnostic (a sentence forbidding
    a hard git reset, a mention of the netrc file).
  - "Whitespace padding" on Markdown table column alignment.
  - Quality deductions for a missing `version`, `## Purpose`,
    `## Limitations`, `## Troubleshooting` or `## Examples`, for long
    descriptions, and for a `TEMPLATE.md` in a skill root: generic
    template rules that conflict with this repo's skill contract (one
    plugin version, ADR-0095; trigger-tuned descriptions).
  Second pass, same tool and version, origin/main 7a11059 (verified
  2026-11-15):
  - "Unexpected nesting depth for general skill" (every skill): an artifact
    of scanning the checkout, whose folder is itself named `skills`, so
    paths read skills/skills/<name>. On a `git archive` export
    (<tmp>/repo/skills/<name>) the finding disappears; run the per-skill
    checks on the export too.
  - "Broad description without negative triggers" matches the literal
    "Do NOT use" phrasing only. Descriptions that state boundaries in
    house style ("Not `doctor` (...)", "Designing the data model is
    architect; ...") are flagged anyway. Of eight flagged, only
    `architect` truly lacked one (fixed by its own issue).
  - "Deeply nested references" fires when a references file cross-links a
    sibling reference. In all five flagged skills (deepen, implement-queue,
    lean, polish, review) the sibling is also linked directly from
    SKILL.md, so nothing is two levels deep.
  - "Resource-based skill lacks documentation of available resources"
    (`prisma-migrations`) is wrong: SKILL.md lists all three `assets/`
    files.
  - "missing-reference caveats" (info) mean only that targets outside the
    skill folder were not inspected; detector I verifies every markdown
    link target exists.
  - "Description contains vague words" (`factory-init`) and "uses
    first/second person" (`house-voice`, where the "my" sits inside quoted
    user phrases) are keyword hits on specific, third-person descriptions.
  - `author_format` (high, blocking) wants the author as a name followed by
    an address in angle brackets (`Name <email@host>`). The Owner declined
    it (2026-11-15) because it would publish an email address, so every
    skill still exits 1 at Tier 1 on it. A future sweep does not
    re-propose it without the Owner.
  - Tier 2 needs an embedding provider key (`SKILL_EVAL_EMBEDDING_PROVIDER`
    set to `nv_build` with `NVIDIA_API_KEY`, or to `openai` with
    `OPENAI_API_KEY`); it does not run offline.
