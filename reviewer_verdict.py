"""ADR-0123's reviewer verdict: the one owner of the pass threshold.

The implement-queue reviewer returns a 0 to 10 score and is told no
line; this module turns the score into the verdict the gate acts on.

`python3 reviewer_verdict.py <score>` prints the first line of the PR's
verdict comment and exits:

- `reviewer-verdict: pass (score 8/10)`, exit 0 — the score is at or
  above PASS_AT.
- `reviewer-verdict: flag (score 5/10)`, exit 1 — below it.
- `reviewer-verdict: error (<reason>)`, exit 2 — no usable score
  (missing, not a number, NaN, infinite, outside 0 to 10, a bool). The
  queue profile's hook reads this as the fail-closed case: errors are
  not passes.

Any finite number from 0 to 10 derives, so 6.5 flags. Pure and
deterministic; no git, network or model call. Root-only (ADR-0060's
rule), stdlib only.
"""
import math
import sys

PASS_AT = 7
USAGE = ("usage: python3 reviewer_verdict.py <score>\n"
         "  prints the verdict comment's first line: exit 0 pass,"
         " 1 flag, 2 error")


def derive(score):
    """("pass" | "flag", number), or ("error", problem string)."""
    if isinstance(score, bool) or score is None:
        return "error", f"reviewer-verdict: no usable score ({score!r})"
    try:
        number = float(score)
    except (TypeError, ValueError):
        return "error", f"reviewer-verdict: score is not a number ({score!r})"
    if not math.isfinite(number):
        return "error", f"reviewer-verdict: score is not finite ({score!r})"
    if not 0 <= number <= 10:
        return "error", f"reviewer-verdict: score outside 0 to 10 ({score!r})"
    value = int(number) if number.is_integer() else number
    return ("pass" if number >= PASS_AT else "flag"), value


def main(argv):
    if len(argv) != 1:
        print(USAGE)
        return 2
    verdict, detail = derive(argv[0])
    if verdict == "error":
        print(f"reviewer-verdict: error ({detail.split(': ', 1)[1]})")
        return 2
    print(f"reviewer-verdict: {verdict} (score {detail}/10)")
    return 0 if verdict == "pass" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
