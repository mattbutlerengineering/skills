---
stage: verify
run: feature:lean-and-polish
date: 2026-10-10
assumptions:
  - "The routing eval (trigger_eval.py) was NOT RUN: it is paid and the brief forbids it. The 21 lean/polish routing cases are present but unscored; the skills stay at draft. Taken from the brief."
---

# Verification: lean and polish

Every check below ran on the branch tip on 2026-10-10; output is pasted
as it printed.

## Up to date

Result: pass. `origin/main` (41f3266) is merged; no conflict marker
remains, `UTILITY_SKILLS` keeps main's `launch-demo` beside the two new
slugs, and the routing-eval diff against main is additions only.

```
$ git diff origin/main --stat -- evals/routing.json
 evals/routing.json | 139 +++++++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 139 insertions(+)
$ git diff origin/main -- evals/routing.json | grep -c "^-[^-]"
0
$ git grep -c "<<<<<<<\|>>>>>>>" -- protocol.py README.md LEDGER.md evals/routing.json .claude-plugin/plugin.json factory/ docs/assets/skill-map.svg
(no output, exit 1)
```

## On every roster

Result: pass.

```
$ python3 -c "import protocol;print([s for s in protocol.UTILITY_SKILLS if s in ('launch-demo','lean','polish')])"
['launch-demo', 'lean', 'polish']
$ cmp <(sed -n '/^UTILITY_SKILLS/,/]/p' protocol.py) <(sed -n '/^UTILITY_SKILLS/,/]/p' factory/templates/tools/factory/protocol.py) && echo mirror-identical
mirror-identical
$ grep -n "^| \(launch-demo\|lean\|polish\) " LEDGER.md
39:| launch-demo | draft | — | — |
40:| lean | draft | — | — |
41:| polish | draft | — | — |
$ grep -n '"row mono"' docs/assets/skill-map.svg | grep -E ">(deepen|lean|polish)<"
216:  <text class="row mono" x="60" y="310">deepen</text>
217:  <text class="row mono" x="60" y="326">lean</text>
218:  <text class="row mono" x="60" y="342">polish</text>
```

The README rows are lines 97-98 of `README.md`, Moment "Reshaping
what's built"; `check_readme_skills` and `check_readme_figure` pass in
the battery below. The routing file now holds 21 cases whose id or
expected skill names `lean` or `polish`, all carried verbatim from the
WIP commit.

## Figure legible

Result: pass, by looking. The figure was rendered headless in Chrome at
its intrinsic 880x688 in both colour schemes and the screenshots read:
`skill-map-light.png` and `skill-map-dark.png` in this directory. The
"Reshaping what's built" card holds `deepen`, `lean`, `polish` inside
its border with the same inset as the other cards, and a clear gap
remains above "Around a pull request".

```
$ "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --blink-settings=preferredColorScheme=1 --screenshot=.../light.png --window-size=880,688 file://.../docs/assets/skill-map.svg
75354 bytes written to file .../light.png
$ grep -n 'y="272"\|y="380"' docs/assets/skill-map.svg
213:  <rect class="mask" x="48" y="272" width="168" height="80" rx="6"/>
214:  <rect class="node-ext" x="48" y="272" width="168" height="80" rx="6"/>
221:  <rect class="mask" x="48" y="380" width="168" height="64" rx="6"/>
222:  <rect class="node-ext" x="48" y="380" width="168" height="64" rx="6"/>
```

Card bottom 272+80 = 352; last baseline 342; next card top 380. Not checked: the figure as
GitHub renders it in the README (owed to the reviewer on the pull
request page).

## Conventions

Result: pass, no edit needed.

```
lean desc_len 980 colon-space False space-hash False problems []
  ref cut-list.md linked at body lines [107]
  ref ladder.md linked at body lines [46]
  harness terms []
  stage-artifact/soft-gate mentions []
  in UTILITY_SKILLS True routed-to (in STAGES) False
polish desc_len 909 colon-space False space-hash False problems []
  ref moves.md linked at body lines [62]
  ref tells.md linked at body lines [41, 83]
  harness terms []
  stage-artifact/soft-gate mentions []
  in UTILITY_SKILLS True routed-to (in STAGES) False
```

## Packaging

Result: pass.

```
$ python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'], json.load(open('factory/manifest.json'))['version'])"
0.5.0 0.5.0
$ python3 factory_init.py update-manifest
factory-init: 0 problem(s)
```

## Battery

Result: pass.

```
$ python3 -m unittest discover tests 2>&1 | grep -E "^(Ran|OK|FAILED)"
Ran 2066 tests in 27.822s
OK
$ python3 lint.py
lint: 0 problem(s) across 28 skills
$ python3 gates.py && python3 gates.py --selftest
gates: 0 problem(s)
selftest: ok
```

## Owed

- Routing eval: NOT RUN (paid). `python3 trigger_eval.py` scores the 21
  new cases; until it runs, nothing says the descriptions discriminate
  against `review`, `deepen`, `audit` and `ux-design`.
- The figure on github.com, in both appearance settings.
