---
stage: review
run: maintenance:the-placeholder-that-is-a-real-handle
date: 2026-08-28
assumptions: []
---

# Review

Scope: the diff of `agent/the-placeholder-that-is-a-real-handle` against
`origin/main` (622e7c0) — `factory_init.py`,
`factory/templates/.github/CODEOWNERS`, `factory/manifest.json`,
`tests/test_factory_init.py`, `docs/backlog.md`.

## Correctness

**Finding 1 (major, fixed during this run).** The first implementation of
`product_codeowners` dropped *every* comment line, not just the root's
header block. A future root CODEOWNERS with a mid-file comment — the
natural place to annotate a group of security-sensitive paths — would
have had that comment silently vanish from the payload. Losing something
the root said, without saying so, is the exact failure class this run
exists to end, so shipping it inside the fix for it was not acceptable.
Rewritten to walk the leading comment block only, which is total over a
root file with no header at all and does not depend on a blank-line
separator (the fragility ADR-0050 calls out for `product_makefile`).
Pinned by `test_a_comment_below_the_rules_survives`.

**Finding 2 (minor, accepted).** `_OWNER_TOKEN` is `(^|\s)@\S+` under
`re.MULTILINE`, so an owner is a whitespace-delimited token that *starts*
with `@`. Two consequences, both deliberate: an email owner keeps its
local part (`docs/ user@example.com` is untouched — pinned by
`test_it_rewrites_owner_tokens_not_every_at_sign`), and a line naming two
owners yields the placeholder twice. The duplicate reads oddly but is
correct, deterministic, and a reader substituting handles wants both slots
visible. Not defended against; there is nothing to defend.

**Finding 3 (minor, accepted).** The transform is lossy by design for the
root's header — that is its whole point — and the loss is unrecoverable
from the payload. Acceptable because the root file remains the authority
and `TestRealTreeMirrors` regenerates the payload from it on every CI run.

**Checked, no finding.** `rules.strip("\n") + "\n"` normalises a leading
blank line left behind by the dropped header and guarantees a trailing
newline. An empty rule set would produce a header plus a bare newline; a
CODEOWNERS with no rules is not a state that occurs and is not guarded.

## Design

**Finding 4 (major, deferred to a human — gate 2).** ADR-0050's Decision
section says: "The transform is `identity` for the 19 verbatim mirrors
and for `.github/CODEOWNERS`, which joins the table." That sentence is
now false. The ADR's *decision* — MIRRORS entries carry a transform —
stands and is in fact strengthened by this change; only its enumeration
of which entry gets which transform has moved.

This run does **not** edit ADR-0050. The repo's rule is to supersede or
amend, never rewrite (`CLAUDE.md`, `docs/adr/`), and under ADR-0036
clause 3 any PR touching `docs/adr/**` is a human-code-owner merge. The
correct follow-up is a short amending ADR recording that
`.github/CODEOWNERS` moved from `identity` to `product_codeowners` and
why. Flagged here rather than done.

**Finding 5 (minor, deferred).** `skills/doctor/SKILL.md` step 8 checks
"CODEOWNERS is substituted" in prose — "if it still names the template's
owner". With a placeholder now shipping, that check could name the
`@<owner>` token and become mechanical, and
`TestDoctorChecklistMatchesThePayload` is the class that would pin it to
the payload. Left out of this run's scope on purpose: the fix makes all
six documenting surfaces true without touching any of them, and that is
the cleaner change to review. Recorded as a follow-up.

**No finding.** The change is symmetric with the existing
`product_makefile` treatment — a placeholder constant, an authored
product-repo header composed from it, a transform, and the MIRRORS entry
switched — so it reads as the pattern the file already had rather than a
new one. Both MIRRORS comments that described CODEOWNERS as a verbatim
twin were corrected in the same commit; leaving either would have
reproduced the original defect one layer up.

**No finding.** `one_owner.py` still reports nine, the same nine as
before. `OWNER_PLACEHOLDER` is stated once and the header interpolates
it, so the token has a single owner.

## Security

**Finding 6 (major, resolved by the change itself).** The pre-fix payload
distributed this repo owner's GitHub handle into every repo the factory
scaffolds, where it functioned as that repo's sole code owner. Under
ADR-0036 the code-owner review requirement is the one physical control
remaining on the merge path, and ADR-0036 states plainly that the
independent-review requirement "is a security property, not a nicety".
An entry naming a non-collaborator is ignored by GitHub without any
signal, so the stamped repo's merge gate was inert while its own
blueprint, its `make check` and its `/doctor` run all reported health.
This is what the change fixes.

**Finding 7 (minor, accepted, and worth a reviewer's attention).** After
the fix a freshly stamped `.github/CODEOWNERS` is *syntactically invalid*
until substituted: `@<owner>` cannot be a GitHub login. This does not
make the gate weaker — an unsubstituted gate was already inert — but it
changes the failure from silent to loud, which is the point. It is also
why the placeholder uses angle brackets rather than a plausible-looking
handle: a plausible token such as `@YOUR-HANDLE` can be registered by a
stranger, and then an unsubstituted file names not nobody but *someone*.
Pinned by `test_the_placeholder_cannot_be_a_real_github_handle`.

**No finding.** No secrets, no network, no user input. The transform is
pure string work over a repo-local file, run only by
`factory_init.py update-manifest`.

## Verdict

No unfixed critical findings. Finding 1 was fixed inside this run and
re-verified. Findings 4 and 5 are deferred follow-ups with reasons
recorded; Finding 4 is a `docs/adr/**` change and therefore a human gate-2
matter by ADR-0036 clause 3, not something this run may land.

Per ADR-0036 clause 2 this run authored its own change and cannot review
it into main: an independent, non-authoring reviewer must re-execute the
verification and record it on the PR before merge.
