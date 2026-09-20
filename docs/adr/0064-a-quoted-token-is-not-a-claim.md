# A quoted work-order token is not a claim

- Status: provisional
- Date: 2026-08-23

ADR-0057 gave both lifecycle legs `--uncited skip` and gated the
relaxation on one expression: `not WO_TOKEN.findall(body)`. The gate reads
the whole PR body, so any four-digit `WO-` token anywhere in it — inside a
fenced block, inside a blockquote — means "this body names a work order",
and a body that names one and resolves none is a malformed work-order PR
whose job fails.

That is the wrong reading of quoted material, and this repo's own PRs
proved it three times in one day. PRs #328 and #330 both failed
`needs-review-label` because their bodies pasted detector output and
quoted a breakdown row; the tokens were evidence, not claims. Both were
fixed by redacting live ids to `WO-00xx` inside the very fences whose
purpose is to show what the tool printed. A PR that cannot quote a
detector's output without lying about it has a gate problem, not a body
problem.

`cited_work_order` already anticipated this. Its docstring says the body
"legitimately NAMES other work orders — a blocking edge ('builds on
WO-0004'), a quoted Accept line". Its structural answer is right:
resolution takes every token and keeps the ones the PR actually closes.
The gap is one step later — when nothing resolves, ADR-0057's gate reads
the mere presence of a token as an authorial claim.

## Decision

**The skip gate reads the body with quoted material removed.** Fenced
code blocks and blockquote lines are stripped, and the token scan runs on
what is left. `validator._unquoted` does the stripping; `WO_TOKEN` stays
the one owner of the token grammar.

**Inline code is not quoted material.** `` `WO-0001` `` in ordinary prose
is how this repo writes an identifier, including in genuine claims.
Treating backticks as quotation would silence real work-order PRs, which
is the failure this gate exists to prevent.

**Resolution is untouched.** `cited_work_order` still sees the whole
body, so a token inside a fence that *does* resolve to an issue the PR
closes still flips its label. The gate is reached only after resolution
has failed, so no body that passes today starts failing and no flip that
happens today stops happening. Only which *failures* become no-ops
changes.

## Consequences

- ADR-0057 is **amended, not superseded**: both legs still take
  `--uncited skip`, the malformed-citation case is still loud, and the
  missed flip is still reported by the reconcile sweep rather than gated.
  Only the text the gate reads changes.
- A PR body may quote detector output and breakdown rows verbatim. The
  `WO-00xx` redactions this repo has been applying were working around
  this gate; new ones are not needed.
- The blind spot moves rather than closing: a PR that genuinely
  implements a work order and mentions it *only* inside a fence now
  merges quietly. That is the same drift ADR-0057 already accepted and
  the same sweep already reports.
- ADR-0057's last consequence — an `Implements: WO-####` trailer to
  separate provenance from implementation — remains seeded and undecided.
  This ADR does not close it; a trailer obliges every future work-order
  PR body, including assembler- and routine-generated ones, and that is a
  repo-wide convention with a migration.
- An unterminated fence swallows the rest of the body. That biases the
  gate toward skipping, and a skip is a no-op rather than a wrong
  mutation, so the failure direction is the safe one.
- Status is provisional: an autorun decided it, and it narrows a gate an
  accepted ADR wrote deliberately.
