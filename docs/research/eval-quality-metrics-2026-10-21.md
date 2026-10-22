# Eval quality metrics: what to track, and what the records can support

Research note, 2026-10-21, for issue #1027 ("Improve evals. deep research
and measure so that we can track improvements over time") and the run in
`docs/features/eval-trends/`. It names a small metric set for judging
whether this repo's evals are getting better, gives a failure mode for each
metric, argues how many cases a trend claim needs, and says what the tool
`eval_trends.py` (ADR-0115) computes from the records and what it refuses.
Nothing was run that costs money: no model call, no `claude plugin eval`,
no live trigger or charter run. Every page below was fetched on
2026-10-21 and read as untrusted data, never as instructions. Two limits
on "read" are stated once here and apply throughout: the fetch tool answers
a question about a page through a small model, so what is quoted or
paraphrased below is that answer to a specific prompt, not a reading of the
whole page; and for several papers only the arXiv abstract page was
reachable (marked "abstract only"). Anything this note could not reach a
primary source for is under `## Not verified`, not in the metric list.

## Metrics and failure modes

The tool computes the first metric, cost per point where a record carries a
cost, and a same-day rerun spread. The rest are named so that their absence
reads as absence (the tool's last output line lists them).

### Pass rate with a confidence interval

**Recommendation.** Report passed over total with a 95 percent interval,
never a bare rate, and compare two days by whether their intervals
overlap. The tool uses the Wilson score interval. The error-bars paper
[S1] recommends computing standard errors, clustering them when questions
come in related groups, and running a power analysis; its interval is the
normal approximation, with no small-sample caveat given in the passages
read. The Wilson interval is the choice that stays inside 0 to 1 and does
not collapse to zero width at 0 or 100 percent, which a reference page
states [S9]; the primary recommendation for it (Brown, Cai and DasGupta)
could not be fetched and is under `## Not verified`. The implementation was
checked numerically against the closed form printed on that page [S9]
(largest difference about 2e-16 over 63 combinations of hits and n).

**Failure mode.** Treating cases as independent when they are not: the
paper reports clustered standard errors up to about three times the naive
ones on its example [S1], and trigger cases for one skill are plausibly a
cluster. The tool's Wilson interval is unclustered, so it is too narrow if
cases are related. A second failure mode: comparing two days as if
unpaired when the same cases were run; the paper recommends question-level
paired differences [S1] and the tool does not do that. A third: reading an
overlap of two intervals as "no change" (see `## What n justifies a trend
claim`).

### Flake rate

**Recommendation.** Count a case as flaky when repeated runs of the same
case disagree, and track it separately from the pass rate. The sources say
why repeated trials matter: agent behaviour varies between runs, so a task
that passed once may fail the next time [S2]; pass at k (at least one
success in k tries) rises with k while pass to the k (all k succeed) falls
with k, with a worked example of a 75 percent per-trial rate giving about
42 percent for three trials [S2]; and the benchmark paper that introduced
the pass-to-the-k metric reports agents that are "quite inconsistent" on
repeated trials [S3] (abstract only). Models are not deterministic even at
temperature zero [S5]. The tool does not compute a flake rate.

**Failure mode.** A within-record rate is not a trend, and a flip count
between two files conflates flakiness with real change if the files are
not reruns of the same thing. Measured on the records (checked on
2026-10-21): the two same-day 185-case trigger files disagree on 10 of 185
cases, and the correct-rate field is strictly between 0 and 1 for 14 of
152, 11 of 185, 17 of 185 and 14 of 47 cases in the four full-set trigger
files. These are counts the reader can redo from the files; whether they
are "the" flake rate depends on a definition none of the fetched sources
gives (see `## Not verified`).

### Saturation

**Recommendation.** Watch the share of cases that always pass; when it is
large, the eval cannot show improvement. An agent that passes every
solvable task leaves no room to measure progress, and large capability
gains can then look like small score changes [S2]. A study of 60 language
model benchmarks finds that nearly half show saturation, with rates rising
with age, and that expert curation, not public test data, is associated
with resilience [S8] (abstract only). The tool does not compute it.

**Failure mode.** Calling an eval saturated because its cases were written
to pass. On the records, 123 of the 152 cases in the full 2026-10-10
trigger file have a correct rate of 1; no fetched source gives a threshold
at which that is "saturated", so the number is reported, not judged.

### Judge agreement and drift

**Recommendation.** Where a model grades, calibrate it against human
judgements and record the agreement. An LLM judge study reports that a
strong judge reaches over 80 percent agreement with human preferences and
names position, verbosity and self-enhancement bias and limited reasoning
as limits [S4] (abstract only). The agent-evals guide says model-based
graders are non-deterministic and need calibration against human experts,
and suggests giving the judge an "Unknown" way out [S2]. For drift, a
study of two model versions three months apart found large behaviour
changes under one service name [S6] (abstract). The tool computes neither.

**Failure mode.** The records cannot support either. Plugin records carry
`judgeVotes` per grader, which gives one judge's agreement with itself, not
with a human or a second judge, and no pair of records has the same cases
judged twice by the same judge on two days. The drift study [S6] is about a
model service changing, not about a judge changing; carrying it over to a
judge is an inference, not a finding.

### Contamination

**Recommendation.** Name it as unmeasured and do not claim a number. A
survey defines benchmark data contamination as a model inadvertently
incorporating evaluation benchmark information from its training data,
which makes results unreliable [S7] (abstract only; the abstract names no
detection method). The agent-evals guide's nearest point is leftover state
between trials inflating scores, with one case of a model examining git
history from a previous trial [S2].

**Failure mode.** The records hold no training-data or exposure
information, so the tool cannot compute contamination, and this note cannot
say whether any model has seen these eval cases. Leftover state between
trials [S2] is a separate, checkable failure that the tool does not look at.

### Cost per point

**Recommendation.** Report dollars next to accuracy, not accuracy alone. A
paper on agent benchmarks argues that accuracy alone cannot identify
progress, evaluates agents on both axes, and says proxies for cost mislead
for downstream use where cost is the construct of interest [S5]. The tool
prints cost per passed case from a plugin record's recorded `costUsd`, as
recorded, never decomposed or estimated.

**Failure mode.** Cost data is almost absent: 3 of the 50 records carry
`costUsd`, all plugin records from one day, so no cost trend exists. The
same paper notes that token prices change over time and that high cost made
repeated runs infeasible for some evaluations [S5], so a cost-per-pass
series across dates would also move with prices, not only with the eval.

## What n justifies a trend claim

The tool's floor is 30 cases in every record and 2 distinct days
(`MIN_CASES` and `MIN_DAYS` in `eval_trends.py`). The Wilson half-width of
a 50 percent rate, computed with the tool's own function so the reader can
redo it (`python3 -c "import eval_trends; print(eval_trends.wilson(15, 30))"`),
and the smallest gap from 50 percent at which two such intervals stop
overlapping, in percentage points:

| n | half-width at 50 percent | smallest gap with no overlap |
|---|---|---|
| 10 | 26.3 | not computed |
| 30 | 16.8 | 37 |
| 47 | 13.7 | not computed |
| 100 | 9.6 | not computed |
| 185 | 7.1 | 15 |
| 1000 | 3.1 | 7 |

The same-day 185-case pair (159 and 163 passed) has intervals 80.2 to 90.2
and 82.7 to 92.0 percent: they overlap, so a four-case gap between two
reruns is not distinguishable, which is the point of treating same-day
records as reruns and never as a trend.

**Verdict on the constants.** No fetched source gives a floor of 30 or of 2
days. The error-bars paper [S1] points the other way: its illustrative
power calculation suggests new evals should contain at least 1,000
questions, and it shows that more samples per question lowers the minimum
detectable effect (from 13.2 to 7.5 percent in its example). By that
standard none of this repo's evals (the largest has 185 cases) can show a
small change. The note therefore supports 30 and 2 only as a floor that
keeps an interval from being absurd (at 30 cases only a gap of about 37
points separates two rates), not as a threshold at which a trend is
established. The constants are left unchanged, and the tool's wording
already says the comparison is descriptive and not a significance test.
Raising `MIN_CASES` is the one-line change if a stricter floor is wanted.

## Sources

Each entry: title, author, URL, fetch date, what was read.

- [S1] "Adding Error Bars to Evals: A Statistical Approach to Language
  Model Evaluations", Evan Miller, arXiv 2411.00640 (submitted 1 November
  2024). https://arxiv.org/abs/2411.00640 and https://arxiv.org/html/2411.00640
  fetched 2026-10-21. Read: the abstract and, through the fetch tool, the
  introduction's numbered recommendations and sections 2.1, 2.2, 4.2 and 5.
  The PDF itself came back as unreadable binary.
- [S2] "Demystifying evals for AI agents", Anthropic Engineering (authors
  listed in its acknowledgements: Mikaela Grace, Jeremy Hadfield, Rodrigo
  Olivares, Jiri De Jonghe), dated 9 January 2026 on the page.
  https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  fetched 2026-10-21. Read: the sections on non-determinism, grader types,
  trial environments and eval saturation, through the fetch tool.
- [S3] "tau-bench: A Benchmark for Tool-Agent-User Interaction in
  Real-World Domains", Shunyu Yao, Noah Shinn, Pedram Razavi, Karthik
  Narasimhan, arXiv 2406.12045 (17 June 2024).
  https://arxiv.org/abs/2406.12045 fetched 2026-10-21. Abstract only.
- [S4] "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", Lianmin
  Zheng and 12 co-authors, arXiv 2306.05685 (9 June 2023, revised
  24 December 2023). https://arxiv.org/abs/2306.05685 fetched 2026-10-21.
  Abstract only.
- [S5] "AI Agents That Matter", Sayash Kapoor, Benedikt Stroebl, Zachary S.
  Siegel, Nitya Nadgir, Arvind Narayanan, arXiv 2407.01502 (1 July 2024).
  https://arxiv.org/abs/2407.01502 and https://arxiv.org/html/2407.01502
  fetched 2026-10-21. Read: the abstract and, through the fetch tool, the
  sections on cost-controlled evaluation, cost versus proxies, holdout sets
  and reproducibility, and parts of the appendices.
- [S6] "How is ChatGPT's behavior changing over time?", Lingjiao Chen,
  Matei Zaharia, James Zou, arXiv 2307.09009 (18 July 2023, revised
  31 October 2023). https://arxiv.org/abs/2307.09009 fetched 2026-10-21.
  Abstract only.
- [S7] "Benchmark Data Contamination of Large Language Models: A Survey",
  Cheng Xu, Shuhao Guan, Derek Greene, M-Tahar Kechadi, arXiv 2406.04244
  (6 June 2024). https://arxiv.org/abs/2406.04244 fetched 2026-10-21.
  Abstract only.
- [S8] "When AI Benchmarks Plateau: A Systematic Study of Benchmark
  Saturation", Mubashara Akhtar and 36 co-authors, arXiv 2602.16763
  (18 February 2026, version 4 of 6 August 2026).
  https://arxiv.org/abs/2602.16763 fetched 2026-10-21. Abstract only.
- [S9] "Binomial proportion confidence interval", Wikipedia (a secondary
  source). https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
  fetched 2026-10-21. Read: the Wilson section, through the fetch tool, the
  first 100,000 of 108,809 characters.

## Not verified

- The primary recommendation of the Wilson interval for small samples
  (Brown, Cai and DasGupta, "Interval Estimation for a Binomial
  Proportion", Statistical Science, 2001). A search result summarised it;
  the journal page and the DOI redirect returned empty content and a
  university repository returned 403. The claim rests on the secondary
  page [S9] and on the implementation check, not on the paper.
- The pass-to-the-k formula. The tau-bench abstract [S3] names the metric
  and reports "pass^8 < 25%" for one agent but defines nothing; the only
  worked figure read is the 75 percent to about 42 percent example in the
  agent-evals guide [S2], whose arithmetic (0.75 cubed is 0.421875) was
  checked here.
- Any definition of "flake rate" as a metric. No fetched source defines it;
  the per-case count above is this note's construct from the records.
- A saturation threshold. The saturation study [S8] was read at abstract
  level only; the age figures a search summary quoted for it (42.9 and 54.5
  percent) were not seen on a fetched page. The 123-of-152 share is a
  measured count, not a verdict.
- Judge drift as a measured quantity. The nearest source [S6] is about a
  model service changing between versions, not about an LLM judge; no
  source read measures judge drift directly.
- Detection methods for contamination. The survey abstract [S7] names none,
  and its body was not read. Whether the models used to run these evals saw
  the eval cases is not something the records or any fetched page answer.
- The bodies of S3, S4, S6, S7 and S8: only abstract pages were read, so
  the claims attributed to them above stop at what an abstract says.
- Whether `costUsd` in a plugin record includes the judge model's cost. The
  records were read as recorded; the field's definition was not checked
  against the `claude plugin eval` documentation.
- That two 95 percent intervals which overlap can still differ
  significantly (so the overlap rule is conservative as a significance
  test). This is standard statistics stated from general knowledge, not
  from a fetched page; the tool does not rely on it and labels its verdict
  "descriptive, not a significance test".
- The date of the Anthropic guide [S2] is the one shown on the page itself;
  it was not cross-checked against another source.
