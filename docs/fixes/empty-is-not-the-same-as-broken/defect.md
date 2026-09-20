---
stage: capture
run: maintenance:empty-is-not-the-same-as-broken
date: 2026-08-25
re-entry: architect
severity: latent
assumptions: ["Severity is `latent`: the streams are healthy today, so nobody is being misled right now. What is broken is the artifact's ability to say so — and the seed exists because this exact blindness already hid a real defect for the harvest's whole life.", "The reproduction drives run_mine with the suite's own injected gh fake. No stage of this run ran the mine against the live repo; the only live calls were read-only listings."]
---

# Defect: an empty harvest and a failed one read the same

## What is wrong

`_change_requests` returns `[]` when the PR listing fails, after appending
the failure to `problems`:

```python
    read = gh_read(list(PR_ARGS), "gh pr list", label="rm", run=run,
                   window=LIST_WINDOW)
    problems.extend(read.problems)
    if read.value is None:
        return []
```

`[]` is also what it returns when the listing succeeds and no PR carries a
change request. `compose_queue` is handed the same empty mapping in both
cases and has no third thing to say, so the queue issue — the artifact a
human reads — is byte-identical.

The failure does reach `problems`, which the CLI prints and the workflow
log keeps. But the reader of issue #294 never sees it.

## Reproduction

Both runs use the suite's injected `gh` fake, one healthy with an empty PR
listing, one with `failing=["pr", "list"]`:

```
=== bodies identical: True
=== problems, healthy: []
=== problems, broken: ['rm: gh pr list failed: boom']
```

The body, in both cases:

```
<!-- factory-toolsmith-queue -->
Toolsmith queue — mined rejections — 2026-08-14

No corrections mined.

Updated weekly by rejection mining (WO-0018); ...
```

One of those two runs harvested nothing because there was nothing to
harvest. The other harvested nothing because it could not look. The issue
says the same sentence.

## The live board is in exactly this shape

Issue #294 carries 35 correction entries and **every one** is a gate
rejection:

```
$ gh issue view 294 --json body --jq '.body' | grep -c "gate rejection"
35
$ gh issue view 294 --json body --jq '.body' | grep -c "change-request"
0
```

And the change-request section is legitimately empty — no PR in the repo
has ever carried a `CHANGES_REQUESTED` review:

```
$ gh pr list --state all --limit 1000 --json number --jq 'length'
157
$ gh pr list --state all --limit 1000 --json number,reviews \
    --jq '[.[] | select(any(.reviews[]?; .state=="CHANGES_REQUESTED")) | .number] | "count=\(length) \(.)"'
count=0 []
```

**Correction to the seed's numbers.** Seed 40 recorded 145 PRs; there are
157 today. The zero is unchanged, and it is the number the claim rests on —
the section is empty because the repo has no change requests, not because
the stream is broken. Today. The point is that nothing in the artifact
distinguishes those.

## Why it matters

This is the shape that hid the mine's own PR-permission defect for the
harvest's entire life: the stream returned nothing, the body said "no
corrections", and the only way to learn otherwise was to open a workflow
log nobody opens on a green run. The grant was fixed by
`maintenance:toolsmith-mine-pr-permissions`; the **tell** was left, and the
seed says so in its own words — *"the grant is fixed but the tell is not"*.

So the next time that stream breaks, the failure mode is identical and the
detection story is identical: silence, indistinguishable from health, until
somebody happens to look at a log.

## The timeline stream is blind the same way

Not named by the seed, found while reading for it. `_timelines` skips an
issue whose timeline fetch fails, records the problem, and returns a
thinner harvest:

```python
        problems.extend(read.problems)
        if read.value is None:
            continue
```

Its docstring is explicit that this is deliberate — *"a failed fetch is a
problem, never a silently thinner harvest"* — and it is right about the
problem list. But the body it feeds carries no mark either, so a harvest
missing three issues' rejections reads exactly like a harvest that found
none. Same defect, same remedy, one stream over.

## Not reproduced

Nothing was run against the live repo except read-only listings. The mine
was not executed in any mode that creates, edits or pins an issue; #294 was
read and not touched.
