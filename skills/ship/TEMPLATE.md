---
stage: ship
run: product | feature:<slug>
date: YYYY-MM-DD
outcome: released | rolled-back | prepared
pending-merge: <PR url, while prepared>
released-at: <YYYY-MM-DD, once the pull request merges>
---

# Release: <title / version>

## Pre-flight

- [ ] Verification green (no unresolved failures)
- [ ] No secrets in diff; target config present
- [ ] Migrations/data changes have a tested forward path
- [ ] Rollback plan concrete (commands/steps below)

## Rollback plan

Door: <one-way or two-way> — <why>

Blast radius: <what breaks if the call is wrong>

(the same call the PR body makes under the protocol's Pull request body
section)

```
<the actual commands/steps to undo this release>
```

## Release log

1. <command/action> → <result>

## Post-release checks

- <check performed> → <evidence it works where users get it>
- Fix runs: <producing boundary and its consumers inspected; related cleanup remaining and why>

## Outcome

<Shipped cleanly / shipped with hiccups (listed) / rolled back (why) /
prepared and stopped — waiting on the pull request `pending-merge:` names.>
