---
description: >-
  Idea, one feature. A scaffold seeds a one-paragraph pitch for a
  scheduling tool; passes when the idea brief is written to the run
  directory with the ambition rung, the demo, the riskiest piece with its
  spike and the cheapest kill test, the pitch's own phrase is kept, and the
  Moonshot is appended to the backlog as a seed. The three llm graders judge
  the brief the reply prints and are model judgement, not deterministic.
tags: [idea]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

I have an idea for a feature. The pitch is in docs/pitch.md. Take it
through the idea stage as a feature run with the slug slot-finder.

Answers to the questions you would ask me, so do not stop to ask them:
the problem is that shift managers spend an evening each week rebuilding
the rota by hand after call-outs; the people who have it are
shift managers at small restaurants, who cope with a spreadsheet and a
group chat; why now is that call-outs have gone up since the schedule
moved to a phone app; the evidence is anecdote, three managers complained
in the last month. For the ambition ladder, my pick is Showstopper. The
demo I would show first is a manager tapping one call-out and the rota
filling the gap before they put the phone down. The product already knows
who is free and who is certified for each station. The riskiest piece is
ranking the replacements; a two-day spike on last month's call-outs would
prove it. The cheapest kill test is to hand-fill ten real call-outs and
see whether the ranking agrees with the manager. Success is one sentence:
a call-out is covered with no more than one tap. Do not design the
solution.

Write the brief to docs/features/slot-finder/idea.md, append any seeds to
docs/backlog.md, then print the whole brief in your reply.
