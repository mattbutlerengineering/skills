# house-voice fixtures

Every file here is authored, not recorded model output. Each was written
by hand for the house-voice run, and no file stands for what a model said.

- `slop/<pattern-name>.md` carries exactly one of the slop patterns
  `voice_grade.py` names, and `slop/clean.md` carries none.
- `<case>/before.md` is a long, hedged reply to that case's question.
  `<case>/after.md` is the same answer in the house voice.

The offline tests in `tests/test_voice_grade.py` and
`tests/test_house_voice_suite.py` read these files. The harness reads only
`prompt.md` files, so no file here takes that name or `case.yaml`.
