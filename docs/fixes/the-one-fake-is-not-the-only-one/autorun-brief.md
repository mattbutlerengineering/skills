# Autorun brief — the one fake is not the only one

**Scale.** Maintenance run, feature-shaped: `docs/fixes/the-one-fake-is-not-the-only-one/`.

**What.** `tests/fake_gh.py` opens "The one fake gh at cli.gh_runner's
seam" and says it is "shared by every suite at the seam", naming four.
Seven suites import it, and `tests/test_work_queue.py` keeps two private
fakes at that same seam — one of which contradicts the shared fake's
first declared behaviour. The file that exists to end a divergence is
the record of a divergence that quietly restarted.

**Why now.** The fake's whole justification is that four suites' private
copies "had diverged on three behaviors", and the module then declares
what the choices are. A suite that reaches the seam through its own
class is outside those declarations by construction, and nothing reports
it. The shared fake also has no test of its own, so the three behaviours
it declares are asserted nowhere.

**Re-entry.** `implement` — the fold is mechanical and the shared fake
already covers both private shapes.

**Release authorization.** None. Prepare and stop.

**Scope in.** `tests/test_work_queue.py` (the fold), `tests/fake_gh.py`
(the stale roll-call), and a new `tests/test_fake_gh.py` pinning the
fake's declared behaviours and the single-owner rule.

**Scope out.** The other six suites' use of the fake — they already go
through it. No production module changes; this run touches `tests/`
only, so no manifest regeneration is owed.
