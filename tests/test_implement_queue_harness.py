"""implement-queue names what it needs from a harness (#1715).

Phase 2 spoke in Claude Code's Agent tool (`isolation: "worktree"`, a
per-call model, usage on completion). A harness without them failed a
whole dispatch over the model argument, left the worktree and its
upstream to the orchestrator, and had no rule for a usage-less
telemetry row. Each need is pinned to ITS fallback sentence, the
worktree command and its caveat to their own sentences, and the
telemetry rule to the sentences after the outcome table.
"""
import re
import unittest

from tests.test_implement_queue_head_pin import SKILL
from tests.test_implement_queue_no_verdict import sentence
from tests.test_implement_queue_worker_brief import after_table, phase2


def flat(text):
    return " ".join(text.split())


def passage():
    """The Harness needs passage: from its lead to the Worker brief."""
    return phase2().split("**Harness needs.**", 1)[1].split(
        "### Worker brief", 1)[0]


def need(label):
    """The flattened bullet of one need, by its leading label."""
    for item in re.split(r"(?<=\.) - (?=[A-Z])", passage()):
        item = item.strip().removeprefix("- ")
        if item.startswith(label):
            return flat(item)
    return ""


class TestThePassageSitsInPhaseTwo(unittest.TestCase):
    def test_it_follows_the_dispatch_paragraph(self):
        text = phase2()
        self.assertLess(text.index("Dispatch one worker per issue"),
                        text.index("**Harness needs.**"))
        self.assertLess(text.index("**Harness needs.**"),
                        text.index("### Worker brief"))

    def test_it_is_not_a_top_level_section(self):
        self.assertNotIn("## Harness needs",
                         SKILL.read_text(encoding="utf-8"))

    def test_it_names_all_four_needs(self):
        for label in ("Per-worker worktree.", "Per-worker model.",
                      "Usage on completion.", "Messaging a running worker."):
            self.assertTrue(need(label), label)


class TestTheLeadAndTheWorkOrdersMode(unittest.TestCase):
    def test_the_lead_scopes_no_stop_to_issues(self):
        s = sentence(flat(passage()), "uses its fallback")
        self.assertIn("under `source: issues` none of them stops the run", s)

    def test_the_cut_path_is_under_the_reaped_directory(self):
        s = sentence(need("Per-worker worktree."), "cuts each worktree")
        self.assertIn("under `.claude/worktrees/`", s)

    def test_no_usage_means_no_ledger_row_and_a_named_order(self):
        s = sentence(flat(passage()), "`budget_guard.py record`")
        self.assertIn("Under `source: work-orders`", s)
        self.assertIn("no `budget_guard.py record` row", s)
        self.assertIn("names each unrecorded order", s)
        self.assertIn("reads low", s)

    def test_no_isolation_follows_the_cloud_fallback(self):
        s = sentence(flat(passage()), "Cloud fallback")
        self.assertIn("Under `source: work-orders`", s)
        self.assertIn("without worktree isolation", s)
        self.assertIn("references/work-orders.md", s)
        self.assertIn("not the orchestrator-cut worktree", s)
        self.assertNotIn("budget_guard", s)


class TestOrchestratorCutWorktree(unittest.TestCase):
    def test_the_command_is_no_track_from_the_remote_tracking_ref(self):
        s = sentence(need("Per-worker worktree."), "worktree add")
        self.assertIn("git -C <repo> worktree add --no-track <path> "
                      "-b <branch> refs/remotes/origin/main", s)

    def test_the_caveat_names_the_upstream(self):
        s = sentence(need("Per-worker worktree."), "Without `--no-track`")
        self.assertIn("upstream", s)
        self.assertIn("`origin/main`", s)
        self.assertIn("`main`", s)

    def test_the_worker_pushes_with_an_explicit_branch(self):
        s = sentence(need("Per-worker worktree."), "push with")
        self.assertIn("git push -u origin <branch>", s)
        self.assertIn("never a bare `git push`", s)

    def test_the_orchestrator_removes_it_by_phase_four_and_reap(self):
        s = sentence(need("Per-worker worktree."), "removes the worktree")
        self.assertIn("orchestrator", s)
        self.assertIn("Phase 4 empty-worktree rule", s)
        self.assertIn("no commit", s)
        self.assertIn("`reap` hook", s)
        self.assertIn("merged", s)

    def test_it_is_cut_after_base_freshness(self):
        s = sentence(need("Per-worker worktree."), "cuts each worktree")
        self.assertIn("after `base-freshness`", s)


class TestAnUnusableModelNeverFailsTheBatch(unittest.TestCase):
    def test_dispatch_on_the_default_and_report_it_once(self):
        s = sentence(need("Per-worker model."), "dispatch on")
        self.assertIn("dispatch on the harness's default model", s)
        self.assertIn("advisory", s)
        self.assertIn("once in the run report", s)
        self.assertIn("never fail the batch", s)

    def test_a_refusal_naming_the_model_is_resent_once_without_it(self):
        s = sentence(need("Per-worker model."), "naming the model argument")
        self.assertIn("re-sent once without it", s)

    def test_a_second_refusal_is_a_worker_failure(self):
        s = sentence(need("Per-worker model."), "re-send that is refused")
        self.assertIn("another reason", s)
        self.assertIn("worker failure", s)
        self.assertNotIn("never fail the batch", s)


class TestTelemetryWithoutUsage(unittest.TestCase):
    def test_the_need_points_at_the_telemetry_rule(self):
        s = sentence(need("Usage on completion."), "Absent")
        self.assertIn("leave the usage fields empty", s)
        self.assertIn("still write the row", s)

    def test_the_empty_fields_are_named_and_never_estimated(self):
        s = sentence(after_table(), "never estimated")
        for field in ("tokens in and out", "tool uses", "model tier", "cost"):
            self.assertIn(field, s)
        self.assertIn("never estimated", s)

    def test_a_row_without_usage_is_still_written(self):
        s = sentence(after_table(), "still written")
        self.assertIn("fields it has", s)
        for field in ("issue", "outcome", "duration", "PR"):
            self.assertIn(field, s)

    def test_a_derived_duration_is_allowed_and_labelled(self):
        s = sentence(after_table(), "label-event timestamps")
        self.assertIn("may be read", s)
        self.assertIn("derived", s)

    def test_the_existing_cost_rule_stays(self):
        s = sentence(after_table(), "Leave cost empty")
        self.assertIn("never estimate it", s)


class TestTheMessagingFallbackPointsAtTheBound(unittest.TestCase):
    def test_check_in_becomes_stopping_at_the_bound(self):
        s = sentence(need("Messaging a running worker."), "Absent")
        self.assertIn("stopping the worker at the bound", s)
        self.assertIn("Wall-clock bound", s)

    def test_the_bound_text_still_stops_an_unmessageable_worker(self):
        s = sentence(after_table(), "has not answered")
        self.assertIn("harness cannot message", s)


if __name__ == "__main__":
    unittest.main()
