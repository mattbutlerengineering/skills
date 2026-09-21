---
stage: verify
run: maintenance:a-program-lives-in-the-workflow
date: 2026-08-30
---

# Verification — a program lives in the workflow

Every command below was run on this branch. Output is quoted, not
summarized.

## 1. The claim is no longer stated falsely at any site this run owns

The defect brief's grep named three lines. The fix reached **five
authored statements** — seven lines, counting the two the mirror
generates. The brief's grep had not covered the root `Makefile`'s own
header, and writing this artifact turned up a fifth in
`factory_init.py`'s `missing_make_targets`, whose whole job is keeping
the workflows' `make` calls and a stamped repo's Makefile in step (and
which now also covers `pr-event`). All five say what is true: no repo
*tool*, and the plumbing that stays is named.

```
$ grep -rn "no commands of their own\|names no commands of its own" \
    Makefile factory/templates/Makefile factory_init.py validator.py \
    .github/workflows/validator.yml \
    factory/templates/.github/workflows/validator.yml
$ echo "exit=$?"
exit=1

$ grep -rn "no repo tool" Makefile factory/templates/Makefile \
    factory_init.py validator.py .github/workflows/validator.yml \
    factory/templates/.github/workflows/validator.yml
Makefile:4:# .github/workflows/validator.yml names no repo tool of its own, it calls
validator.py:6:The workflows name no repo tool of their own — every tool invocation goes
factory/templates/Makefile:4:# stamped .github/workflows/validator.yml names no repo tool of its own, it
factory_init.py:81:    "# stamped .github/workflows/validator.yml names no repo tool of its"
factory_init.py:295:    update overwrites the workflows, and they name no repo tool of their
.github/workflows/validator.yml:5:# why it names no repo tool of its own. Every tool invocation goes through a
factory/templates/.github/workflows/validator.yml:5:# why it names no repo tool of its own. Every tool invocation goes through a
```

The same sentence appears on the other five workflows and in
`assembler.py`. It was read and deliberately left alone — see the
observation in `review.md`.

## 2. The program has one owner

Three copies became three calls to one target, and the workflow carries
no program of its own.

```
$ grep -c "python3 -c" .github/workflows/validator.yml
0
$ grep -n "make pr-event" .github/workflows/validator.yml
59:          make pr-event PR="$PR" EVENT="${RUNNER_TEMP}/pr-event.json"
115:          make pr-event PR="$PR" EVENT="${RUNNER_TEMP}/pr-event.json"
162:          make pr-event PR="$PR" EVENT="${RUNNER_TEMP}/pr-event.json"
```

## 3. The replacement is behaviour-preserving

The old program and the new target were run against the same real PR
(this repo's own #371) and compared.

```
$ gh api "repos/mattbutlerengineering/skills/pulls/371" \
    | python3 -c 'import json, sys; print(json.dumps({"action": "opened", "pull_request": json.load(sys.stdin)}))' \
    > old371.json
$ GITHUB_REPOSITORY=mattbutlerengineering/skills make pr-event PR=371 EVENT=e371.json
python3 validator.py pr-event --pr 371 --out e371.json
validator: 0 problem(s)
$ python3 -c "import json; print(json.load(open('old371.json')) == json.load(open('e371.json')))"
True
$ diff <(python3 -c "import sys;sys.stdout.write(open('old371.json').read().rstrip('\n'))") e371.json \
    && echo IDENTICAL
IDENTICAL
```

The one byte of difference is the trailing newline `print()` added and
`Path.write_text` does not. `json.loads` ignores trailing whitespace, so
no consumer can tell — recorded here because "identical" without the
qualification would be a lie.

## 4. The consumer's own parser reads it

Not a second copy of the literal — `cli.read_event`, the function every
consumer actually calls.

```
$ python3 -c "
import cli
ev, err = cli.read_event({'GITHUB_EVENT_PATH': 'e371.json'})
print('read_event error:', err)
print('action:', ev['action'])
print('pr number:', ev['pull_request']['number'])
print('top-level keys:', sorted(ev))
"
read_event error: None
action: opened
pr number: 371
top-level keys: ['action', 'pull_request']
```

## 5. The regression test catches the defect the old one could not

One of the three steps was reverted to a hand-built copy — the exact
drift the defect describes — and both tests were run against it.

```
$ python3 -m unittest tests.test_assembler.TestValidatorDispatchLockstep
FAIL: test_every_dispatch_shim_goes_through_the_one_target
AssertionError: 2 != 3
Ran 5 tests in 0.001s
FAILED (failures=1)

$ python3 -c "
t = open('.github/workflows/validator.yml').read()
print('old assertion:', '\"action\": \"opened\"' in t)
"
old assertion: True
```

The old assertion passes on the drifted file. That is the defect, shown
rather than argued. The file was then restored, and the class is green:

```
$ python3 -m unittest tests.test_assembler.TestValidatorDispatchLockstep
Ran 5 tests in 0.000s
OK
```

## 6. The shim's own failure modes are covered

`TestPrEvent` exercises the writer through its public interface with an
injected gh, and every refusal leaves no file behind.

```
$ python3 -m unittest tests.test_validator.TestPrEvent -v 2>&1 \
    | grep "ok$" | sed 's/ (tests.*)//'
test_a_failed_gh_leaves_no_event_behind ... ok
test_a_non_numeric_pr_is_usage_not_a_gh_call ... ok
test_a_response_that_is_not_a_pr_object_leaves_no_event_behind ... ok
test_an_unset_repository_is_refused_before_gh_is_called ... ok
test_an_unwritable_destination_is_a_problem_not_a_traceback ... ok
test_both_options_are_required ... ok
test_the_cli_writes_the_event_for_a_dispatched_pr ... ok
test_the_payload_is_what_read_event_hands_its_consumers ... ok
test_the_pr_is_read_from_the_repository_the_environment_names ... ok
```

## 7. Root and payload stay in lockstep

```
$ diff -q .github/workflows/validator.yml \
       factory/templates/.github/workflows/validator.yml && echo root==payload
root==payload
$ grep -n "pr-event" factory/templates/Makefile
12:.PHONY: web-quality pr-event
29:EVENT ?= pr-event.json
47:pr-event:
48:	python3 tools/factory/validator.py pr-event --pr $(PR) --out $(EVENT)
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
```

`make` with no arguments still defaults to `check` — the new target was
placed after it, not before:

```
$ make -n | head -2
python3 lint.py
python3 gates.py
```

## 8. The full battery

```
$ python3 lint.py
lint: 0 problem(s) across 24 skills
$ python3 gates.py
gates: 0 problem(s)
$ python3 gates.py --selftest
selftest: ok
$ python3 -m unittest discover tests
Ran 1354 tests in 15.840s

OK
```

Baseline on `origin/main` is 1344, so this run adds 10 tests: nine in
`TestPrEvent` and one in `TestValidatorDispatchLockstep`.

The review pre-pass is unchanged, so no second owner was introduced:

```
$ python3 one_owner.py | tail -1
one-owner: 9 problem(s)
```

(`origin/main` reports the same 9.)

## What was NOT verified

- **No GitHub Actions run exercised the new step.** The dispatch path
  only fires on `workflow_dispatch`, which the assembler triggers for a
  PR the factory's own token opened. Everything above is local: the make
  target, the tool, a real `gh api` read, and the payload compared
  against the program it replaces. The step itself is two lines and both
  halves ran here, but "CI has executed it" is not a claim this artifact
  makes.
- **The `Collect findings` shell was left alone** (`set +e`, the
  `$GITHUB_ENV` write, `exit 0`). It captures `make check`'s own exit
  code and cannot be a make target; the corrected claim names it instead
  of pretending otherwise. Out of scope by the brief.
- **`factory_init.py`'s MIRRORS comment was read and left alone.** It
  says validator.yml "is path-agnostic (it runs `make` targets), which is
  what lets it be mirrored byte-for-byte" — true before this change and
  true after, because an inline `python3 -c` is path-agnostic too. It
  states a different fact from the four corrected above, and correcting
  a true sentence would be the wrong kind of tidying.
