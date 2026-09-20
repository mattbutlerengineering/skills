---
stage: review
run: maintenance:plugin-description-drift
date: 2026-08-23
assumptions: ["Severity is judged against this repo's own bar — a checker that can be silently wrong is worse than one that is noisy, because the whole point of the change is that nothing was looking", "F4 and F6 are pre-existing and out of this run's surgical scope; they are logged and seeded rather than fixed, per the repo's rule that adjacent smells get flagged not folded in"]
---

# Review: maintenance:plugin-description-drift

Scope: the diff this run created — `lint.py` (`check_plugin_skills`,
`SLUG_TOKEN`, the `CHECKERS` tuple, one import), `tests/test_lint.py`
(`TestPluginSkills`, the clean-tree manifest), `.claude-plugin/plugin.json`
(the description), the claimed backlog seed, and this run's artifacts.

Six findings. **Three fixed before Ship, three deferred. No criticals.**
Each was reproduced before being written down.

## F1 — a longer slug satisfied a shorter one (major, FIXED)

`check_plugin_skills` tested `slug not in description`. Because
`architecture-diagram` is a substring of
`interactive-architecture-diagram`, a description that dropped the shorter
name still passed.

Failure scenario, driven against a temp tree before the fix — the list is
missing `architecture-diagram` and the checker is silent:

```
F1 substring shadowing — drop 'architecture-diagram', keep the interactive one:
   problems: NONE — the incomplete list passes
```

This is the worst class of defect available to this change: the checker
exists precisely to catch a slug going missing from that list, and it was
blind to one of the three slugs that motivated the run.

Fixed by matching whole slug tokens (`SLUG_TOKEN`) instead of substrings.
Re-probed after:

```
    ["plugin.json's description never names utility skill 'architecture-diagram'"]
```

Pinned by `test_a_longer_slug_does_not_satisfy_the_shorter_one`.

## F2 — one missing file, two identical problem strings (minor, FIXED)

`check_manifest` and `check_plugin_skills` both reported a missing
manifest, and both are in `CHECKERS`:

```
F2 missing manifest, both checkers run:
   check_manifest      -> ['missing .claude-plugin/plugin.json']
   check_plugin_skills -> ['missing .claude-plugin/plugin.json']
```

Fixed: `check_plugin_skills` returns nothing for a missing manifest and
leaves the report to `check_manifest`. The aggregate still fails, so
nothing is swallowed.

## F3 — one broken file, two different wordings (minor, FIXED)

Same shape as F2 for unparseable JSON, but worse, because the two strings
disagreed about what was wrong:

```
F3 invalid JSON, both checkers run:
   check_manifest      -> ['plugin.json is not valid JSON: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)']
   check_plugin_skills -> ['plugin.json is not valid JSON, so its skill list cannot be checked']
```

Fixed with F2, and both halves pinned together by
`test_a_missing_manifest_is_left_to_check_manifest`, so the dependency
between the two checkers is asserted in one place rather than assumed.

## F4 — a manifest that parses but is not an object raises (minor, DEFERRED)

```
top-level array    check_manifest       -> AttributeError: 'list' object has no attribute 'get'
top-level array    check_plugin_skills  -> AttributeError: 'list' object has no attribute 'get'
top-level string   check_manifest       -> AttributeError: 'str' object has no attribute 'get'
top-level string   check_plugin_skills  -> AttributeError: 'str' object has no attribute 'get'
```

A traceback where the repo's contract is a problem string. **Pre-existing
in `check_manifest`**; this run's checker inherits the shape rather than
introducing it.

Deferred, with a reason: fixing it here would either special-case one
checker (leaving `check_manifest` still able to traceback) or open the
repo-wide input-policy question that `docs/backlog.md:13` already parks
for `read_text` decode and OS errors. That is a policy decision, not a
ride-along on a description fix. Seeded at Operate.

## F5 — an implicit dependency between two checkers (minor, DEFERRED)

The F2/F3 fix makes `check_plugin_skills` rely on `check_manifest` still
being in `CHECKERS` to report a broken manifest. Removing `check_manifest`
would make a missing file silent.

Deferred as accepted-with-mitigation: the docstring states the dependency
at the point of the early return, and
`test_a_missing_manifest_is_left_to_check_manifest` asserts both halves in
one test, so the pairing breaks loudly rather than quietly. The
alternative — a shared manifest-reading helper — would be a new shared
module for two callers in one file, which this repo's seam bar explicitly
refuses without observed divergence.

## F6 — check_readme_skills has the same blind spot as F1 (minor, DEFERRED)

The checker this one was modelled on carries the identical substring bug,
so README.md can silently drop `architecture-diagram` today:

```
README missing 'architecture-diagram' but keeping the interactive one:
  -> NONE — the same shadowing exists in check_readme_skills
```

Real, reproduced, and **not this run's to fix**: the defect brief scoped
this run to the plugin manifest, and `check_readme_skills` predates it.
Folding a fix in would be exactly the "while I was in there" edit the
repo's surgical-change rule refuses. The fix is small — reuse
`SLUG_TOKEN` — which is what makes it a good seed rather than a good
excuse. Seeded at Operate.

## Passes that found nothing

- **Security.** The change reads one repo-controlled file and emits
  strings. No user input, no secrets, no injection surface, no network,
  no subprocess. `json.loads` on a tracked file is the same trust
  boundary the repo already accepts everywhere.
- **Design.** No `architecture.md` exists (`re-entry: implement`), so the
  contract is the codebase's own shape: the checker takes a root, returns
  label-free problem strings, is registered in `CHECKERS`, and is tested
  through its public interface against a seeded temp tree. It matches
  `check_readme_skills` and `check_ledger` in all four respects.
- **Second owners.** The one-owner pre-pass reports the same nine
  pre-existing groups after this change as before, and names neither
  `lint.py` nor `check_plugin_skills`.

## Ship readiness

No critical findings, and the two fix-before-Ship items are fixed with the
battery green afterwards. Nothing routes back to Implement.
