"""decompose_signals.py — Decompose outcome signals from git history.

The run is docs/features/decompose-outcome-signals/ (ADR-0109's boundary
rule, ADR-0110's import edges). Every case here runs against a REAL temp
git repo built by the Repo fixture below, because author-date order and
pathspec semantics are what is under test (architecture.md, Decisions);
a failing fake runner covers only the CLI-failure strings, and a
recording wrapper around the real runner pins the git verbs the tool is
allowed to run.
"""
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling helper imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
import git_repo  # noqa: E402

import cli  # noqa: E402
import decompose_signals  # noqa: E402
from decompose_signals import (boundaries, read_history,  # noqa: E402
                               read_version)

RUN = "docs/features/demo"
OTHER = "docs/features/other"
# 2026-01-01T00:00:00Z; each fixture commit is one minute after the last,
# so author-date order is commit order.
EPOCH = 1767225600


def git_run():
    """The real git port the tool is given: cli.runner with its timeout."""
    return cli.runner("git", timeout=60)


def breakdown(*rows, gaps="None."):
    """A breakdown.md holding `rows` (each a full checkbox line) and a
    `## Design gaps found` section reading `gaps` (None leaves it out)."""
    text = "# Breakdown: demo\n\n## Milestone 1\n\n" + "\n".join(rows) + "\n"
    if gaps is not None:
        text += f"\n## Design gaps found\n\n{gaps}\n"
    return text


def row(label, title, done=False, rest=" — size:S, blocked by: —"):
    return f"- [{'x' if done else ' '}] **{label}** {title}{rest}"


class Repo:
    """A real temp git repo with dated commits, made through git_repo so
    auto-gc never races the cleanup."""

    def __init__(self, case):
        tmp = tempfile.TemporaryDirectory()
        case.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        git_repo.init(self.root)
        self.ticks = 0

    def git(self, *args, env=None):
        return subprocess.run(
            ["git", "-C", str(self.root), "-c", "user.email=t@example.com",
             "-c", "user.name=T", "-c", "commit.gpgsign=false", *args],
            check=True, capture_output=True, text=True,
            env=env).stdout.strip()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def commit(self, message, **files):
        """Write `files` ({rel with / as __: text}) and commit them with
        the next author date; return the full sha."""
        for rel, text in files.items():
            self.write(rel.replace("__", "/"), text)
        self.ticks += 1
        when = f"{EPOCH + 60 * self.ticks} +0000"
        env = {**os.environ, "GIT_AUTHOR_DATE": when,
               "GIT_COMMITTER_DATE": when}
        self.git("add", "-A", env=env)
        self.git("commit", "-q", "--allow-empty", "-m", message, env=env)
        return self.git("rev-parse", "HEAD")


def at(path):
    """A Repo.commit keyword for a repo-relative path."""
    return path.replace("/", "__")


BD = at(f"{RUN}/breakdown.md")
ARCH = at(f"{RUN}/architecture.md")
OTHER_BD = at(f"{OTHER}/breakdown.md")

PLAN = breakdown(row("S1", "first"), row("S2", "second"))
TICKED = breakdown(row("S1", "first", done=True), row("S2", "second"))


class HistoryCase(unittest.TestCase):
    def setUp(self):
        self.repo = Repo(self)
        self.run = git_run()

    def history(self):
        history, problems = read_history(self.repo.root, self.run)
        self.assertEqual(problems, [])
        return history

    def bounds(self, run_rel=RUN):
        history = self.history()

        def read(sha, path):
            text, problems = read_version(self.repo.root, self.run, sha,
                                          path)
            self.assertEqual(problems, [])
            return text
        return boundaries(history["commits"], run_rel, read)


class TestObservedDecompose(HistoryCase):
    def test_any_scope_and_no_em_dash_is_observed(self):
        self.repo.commit("feat: unrelated", **{at("README.md"): "hi\n"})
        sha = self.repo.commit("docs(some-other-scope): decompose the work",
                               **{BD: PLAN})
        self.assertEqual(self.bounds()["decompose"],
                         {"sha": sha, "label": "observed"})

    def test_a_decompose_commit_for_another_run_is_not_observed_here(self):
        first = self.repo.commit("feat: draft the plan", **{BD: PLAN})
        self.repo.commit("docs(x): decompose the other run",
                         **{OTHER_BD: PLAN})
        self.assertEqual(self.bounds()["decompose"],
                         {"sha": first, "label": "inferred"})

    def test_a_decompose_word_inside_another_word_is_not_the_stage(self):
        first = self.repo.commit("docs(x): decomposed by hand",
                                 **{BD: PLAN})
        self.assertEqual(self.bounds()["decompose"],
                         {"sha": first, "label": "inferred"})


class TestInferredDecompose(HistoryCase):
    def test_the_earliest_commit_changing_the_breakdown(self):
        first = self.repo.commit("feat: add the plan", **{BD: PLAN})
        self.repo.commit("feat: edit the plan",
                         **{BD: PLAN + "\nmore\n"})
        self.assertEqual(self.bounds()["decompose"],
                         {"sha": first, "label": "inferred"})

    def test_no_commit_changes_the_breakdown(self):
        self.repo.commit("feat: unrelated", **{at("README.md"): "hi\n"})
        self.repo.write(f"{RUN}/breakdown.md", PLAN)
        reason = ("no commit on the refs read changes"
                  f" {RUN}/breakdown.md")
        self.assertEqual(self.bounds(),
                         {"decompose": {"unmeasurable": reason},
                          "implement": {"unmeasurable": reason}})

    def test_a_first_version_that_already_checks_rows(self):
        sha = self.repo.commit("feat: land it all", **{BD: breakdown(
            row("S1", "a", done=True), row("S2", "b", done=True),
            row("S3", "c"))})
        reason = f"the first version ({sha[:7]}) already checks 2 of 3 rows"
        self.assertEqual(self.bounds(),
                         {"decompose": {"unmeasurable": reason},
                          "implement": {"unmeasurable": reason}})


class TestImplement(HistoryCase):
    def test_observed_is_the_earliest_implement_commit_after_d(self):
        self.repo.commit("docs(demo): decompose — plan", **{BD: PLAN})
        sha = self.repo.commit("docs(demo): implement — done",
                               **{BD: TICKED})
        self.repo.commit("docs(demo): implement — again",
                         **{BD: TICKED + "\nnotes\n"})
        self.assertEqual(self.bounds()["implement"],
                         {"sha": sha, "label": "observed"})

    def test_an_implement_commit_that_only_writes_architecture(self):
        self.repo.commit("docs(demo): decompose — plan", **{BD: PLAN})
        self.repo.commit("docs(x): implement the design change",
                         **{ARCH: "# Architecture\n"})
        tick = self.repo.commit("feat: S1", **{BD: TICKED})
        self.assertEqual(self.bounds()["implement"],
                         {"sha": tick, "label": "inferred"})

    def test_inferred_is_the_earliest_later_version_with_a_done_row(self):
        self.repo.commit("feat: plan", **{BD: PLAN})
        self.repo.commit("feat: reword", **{BD: PLAN.replace("first",
                                                               "1st")})
        tick = self.repo.commit("feat: S1", **{BD: TICKED})
        self.repo.commit("feat: S2", **{BD: TICKED.replace(
            "- [ ] **S2", "- [x] **S2")})
        self.assertEqual(self.bounds(),
                         {"decompose": {"sha": self.repo.git(
                             "rev-parse", "HEAD~3"), "label": "inferred"},
                          "implement": {"sha": tick, "label": "inferred"}})

    def test_no_later_commit_checks_a_row(self):
        self.repo.commit("docs(demo): decompose — plan", **{BD: PLAN})
        self.repo.commit("feat: reword", **{BD: PLAN + "\nmore\n"})
        self.assertEqual(
            self.bounds()["implement"],
            {"unmeasurable":
             "no implement boundary: no later commit checks a row"})


class TestRefs(HistoryCase):
    def test_a_commit_only_on_refs_stash_is_never_a_boundary(self):
        self.repo.commit("feat: plan", **{BD: PLAN})
        self.repo.write(f"{RUN}/breakdown.md", TICKED)
        self.repo.git("stash", "-q")
        self.assertTrue(self.repo.git("rev-parse", "--verify",
                                      "refs/stash"))
        history = self.history()
        self.assertNotIn("refs/stash", history["refs"])
        self.assertEqual(
            self.bounds()["implement"],
            {"unmeasurable":
             "no implement boundary: no later commit checks a row"})

    def test_namespace_counts_and_the_digest_of_the_ref_tips(self):
        self.repo.commit("feat: plan", **{BD: PLAN})
        self.repo.git("branch", "feat/other")
        self.repo.git("tag", "v1")
        self.repo.git("update-ref", "refs/remotes/pr/7", "HEAD")
        listing = self.repo.git("for-each-ref",
                                "--format=%(refname) %(objectname)")
        lines = sorted(listing.splitlines())
        digest = hashlib.sha256(
            "".join(f"{line}\n" for line in lines).encode()).hexdigest()
        history = self.history()
        self.assertEqual(history["refs"],
                         {"refs/heads": 2, "refs/remotes/pr": 1,
                          "refs/tags": 1})
        self.assertEqual(history["digest"], digest)
        self.assertEqual(len(history["digest"][:12]), 12)

    def test_the_walk_reads_every_ref_not_only_head(self):
        self.repo.commit("feat: base", **{at("README.md"): "hi\n"})
        self.repo.git("checkout", "-q", "-b", "feat/demo")
        sha = self.repo.commit("docs(demo): decompose — plan", **{BD: PLAN})
        self.repo.git("checkout", "-q", "-")
        self.assertEqual(self.bounds()["decompose"],
                         {"sha": sha, "label": "observed"})


def failing(err, after=()):
    """A fake git port that answers the verbs in `after` with an empty
    success and raises `err` for anything else."""
    def run(args, input=None, cwd=None):
        if args[0] in after:
            return subprocess.CompletedProcess(args, 0, stdout="",
                                               stderr="")
        raise err
    return run


BOOM = subprocess.CalledProcessError(128, ["git"], stderr="fatal: boom\n")


class TestGitFailures(unittest.TestCase):
    def test_for_each_ref_failure(self):
        self.assertEqual(
            read_history(Path("."), failing(BOOM)),
            (None, ["decompose-signals: git for-each-ref failed:"
                    " fatal: boom"]))

    def test_log_failure(self):
        def run(args, input=None, cwd=None):
            if args[0] == "for-each-ref":
                return subprocess.CompletedProcess(
                    args, 0, stdout=f"refs/heads/main {'a' * 40}\n",
                    stderr="")
            raise BOOM
        self.assertEqual(
            read_history(Path("."), run),
            (None, ["decompose-signals: git log failed: fatal: boom"]))

    def test_show_failure(self):
        self.assertEqual(
            read_version(Path("."), failing(OSError("no git")), "a" * 40,
                         f"{RUN}/breakdown.md"),
            (None, ["decompose-signals: git show failed: no git"]))


# The only verbs the tool may run: every one is local and read-only.
ALLOWED_VERBS = {"for-each-ref", "log", "show", "rev-parse", "status"}


class TestNoNetwork(HistoryCase):
    def test_only_local_read_only_verbs_are_run(self):
        real, verbs = self.run, []

        def recording(args, input=None, cwd=None):
            verbs.append(args[0])
            return real(args, input=input, cwd=cwd)
        self.run = recording
        self.repo.commit("docs(demo): decompose — plan", **{BD: PLAN})
        self.repo.commit("feat: S1", **{BD: TICKED})
        self.bounds()
        self.assertTrue(verbs)
        self.assertLessEqual(set(verbs), ALLOWED_VERBS)
        self.assertFalse({"fetch", "ls-remote", "pull", "remote"}
                         & set(verbs))

    def test_the_module_names_no_network_verb(self):
        source = Path(decompose_signals.__file__).read_text(encoding="utf-8")
        for verb in ("fetch", "ls-remote", "pull", "remote"):
            with self.subTest(verb=verb):
                self.assertNotIn(f'"{verb}"', source)



def lines(*rows):
    """A breakdown version's lines: a heading, prose, then the rows."""
    return ["# Breakdown", "", "Prose naming S9 is not a row.", "",
            *rows]


class TestItemKeys(unittest.TestCase):
    def test_each_key_shape(self):
        self.assertEqual(decompose_signals.item_keys(lines(
            "- [ ] **WO-0012** wire it — size:S, blocked by: WO-0011",
            "- [ ] WO-0013 a bare token row — size:S",
            "- [ ] **S1 Boundary tests** — cases — size:M",
            "- [x] **I2 — the thing holds.** *(blocked by I1)*",
            "- [ ] **A1** pin it — size:S, blocked by: —",
            "- [x] **Roll-up rule tests** — new cases — size:S",
            "- [ ] a plain row with no bold — size:S",
            "  - Accept: S1 passes.",
        )), ["WO-0012", "WO-0013", "S1", "I2", "A1", "Roll-up rule tests",
             "a plain row with no bold"])

    def test_a_long_word_with_digits_is_not_a_label(self):
        self.assertEqual(decompose_signals.item_keys(lines(
            "- [ ] **ADR0109 notes** — size:S",
            "- [ ] **S1-S3 bundle** — size:S")),
            ["ADR0109 notes", "S1-S3 bundle"])


D_SHA, I_SHA = "d" * 40, "e" * 40
S1 = row("S1", "first")
S2 = row("S2", "second")
S3 = row("S3", "third")


def replan(d_rows, i_rows):
    return decompose_signals.replan(lines(*d_rows), lines(*i_rows), D_SHA,
                                    I_SHA)


def counts(items_at_d, added=0, dropped=0, split=0, merged=0, renamed=0):
    return {"items_at_d": items_at_d, "added": added, "dropped": dropped,
            "split": split, "merged": merged, "renamed": renamed,
            "count": added + dropped + split + merged}


class TestReplan(unittest.TestCase):
    def test_no_change(self):
        ticked = row("S1", "first", done=True)
        self.assertEqual(replan([S1, S2, S3], [ticked, S2, S3]), counts(3))

    def test_one_added_row(self):
        self.assertEqual(replan([S1, S2], [S1, S2, S3]),
                         counts(2, added=1))

    def test_one_dropped_row(self):
        self.assertEqual(replan([S1, S2, S3], [S1, S3]),
                         counts(3, dropped=1))

    def test_a_renumbered_row_with_the_same_title_is_a_rename(self):
        self.assertEqual(
            replan([row("WO-0051", "author the docs"), S2],
                   [row("WO-0061", "Author the `docs`."), S2]),
            counts(2, renamed=1))

    def test_a_kept_row_citing_two_added_keys_is_a_split(self):
        superseded = row("S1", "first — superseded, moved to S4 and S5")
        self.assertEqual(
            replan([S1, S2],
                   [superseded, S2, row("S4", "a"), row("S5", "b")]),
            counts(2, added=2, split=1))

    def test_a_dropped_row_cited_by_two_added_rows_is_a_split(self):
        self.assertEqual(
            replan([S1, S2],
                   [S1, row("S4", "half of S2"), row("S5", "rest of S2")]),
            counts(2, added=2, dropped=1, split=1))

    def test_an_added_row_citing_two_dropped_keys_is_a_merge(self):
        self.assertEqual(
            replan([S1, S2, S3], [S1, row("S4", "folds S2 and S3")]),
            counts(3, added=1, dropped=2, merged=1))

    def test_a_mention_inside_blocked_by_is_never_a_citation(self):
        self.assertEqual(
            replan([S1, S2, S3],
                   [S1, row("S4", "new", rest=" — blocked by: S2, S3")]),
            counts(3, added=1, dropped=2))
        self.assertEqual(
            replan([S1, S2],
                   [row("S1", "first", rest=" — blocked by: S4, S5"), S2,
                    row("S4", "a"), row("S5", "b")]),
            counts(2, added=2))

    def test_a_duplicate_key_makes_the_signal_unmeasurable(self):
        self.assertEqual(
            replan([S1, row("S1", "again")], [S1]),
            {"unmeasurable":
             f"duplicate work-item key S1 at {D_SHA[:7]}"})
        self.assertEqual(
            replan([S1], [S1, row("S1", "again")]),
            {"unmeasurable":
             f"duplicate work-item key S1 at {I_SHA[:7]}"})


def commit(n, subject, *files):
    return {"sha": f"{n:x}" * 40, "author_time": EPOCH + n,
            "subject": subject, "files": list(files)}


D_PATH, A_PATH = f"{RUN}/breakdown.md", f"{RUN}/architecture.md"
WALK = [commit(1, "docs(demo): architect — design", A_PATH),
        commit(2, "docs(demo): decompose — plan", D_PATH),
        commit(3, "docs(demo): architect — gap one", A_PATH),
        commit(4, "docs(x): architect — the other run",
               f"{OTHER}/architecture.md"),
        commit(5, "feat: touch the design", A_PATH),
        commit(6, "docs(demo): architecture rework", A_PATH),
        commit(7, "docs(demo): implement — done", D_PATH),
        commit(8, "docs(demo): architect — after the window", A_PATH)]


def bound(n, label):
    return {"sha": WALK[n - 1]["sha"], "label": label}


def gaps(bounds, d_text=None):
    return decompose_signals.design_gaps(WALK, RUN, bounds, d_text)


class TestDesignGapsFromSubjects(unittest.TestCase):
    def test_observed_window_counts_architect_commits_for_this_run(self):
        self.assertEqual(
            gaps({"decompose": bound(2, "observed"),
                  "implement": bound(7, "observed")}),
            {"label": "observed", "routes": 1, "source": "subjects"})

    def test_an_inferred_implement_boundary_makes_it_inferred(self):
        self.assertEqual(
            gaps({"decompose": bound(2, "observed"),
                  "implement": bound(8, "inferred")}),
            {"label": "inferred", "routes": 2, "source": "subjects"})

    def test_no_implement_boundary_is_that_boundarys_reason(self):
        reason = "no implement boundary: no later commit checks a row"
        self.assertEqual(
            gaps({"decompose": bound(2, "observed"),
                  "implement": {"unmeasurable": reason}}),
            {"unmeasurable": reason})

    def test_no_decompose_boundary_is_that_boundarys_reason(self):
        reason = f"no commit on the refs read changes {D_PATH}"
        self.assertEqual(
            gaps({"decompose": {"unmeasurable": reason},
                  "implement": {"unmeasurable": reason}}),
            {"unmeasurable": reason})


MISSING = 'no "Design gaps found" section at the decompose boundary'


class TestDesignGapsFromTheSection(unittest.TestCase):
    INFERRED = {"decompose": bound(2, "inferred"),
                "implement": bound(7, "inferred")}

    def section(self, text):
        return gaps(self.INFERRED, text)

    def test_none_is_zero(self):
        self.assertEqual(self.section(breakdown(S1, gaps="**None.** All "
                                                "of it is designed.")),
                         {"label": "inferred", "routes": 0,
                          "source": "section"})

    def test_other_content_is_one(self):
        self.assertEqual(self.section(breakdown(
            S1, gaps="The cache key was undesigned; routed to Architect.")),
            {"label": "inferred", "routes": 1, "source": "section"})

    def test_a_missing_section(self):
        self.assertEqual(self.section(breakdown(S1, gaps=None)),
                         {"unmeasurable": MISSING})

    def test_a_section_heading_inside_a_fence_is_missing(self):
        fenced = breakdown(S1, gaps=None) + (
            "\n```markdown\n## Design gaps found\n\nnone.\n```\n")
        self.assertEqual(self.section(fenced), {"unmeasurable": MISSING})

    def test_an_inferred_decompose_with_no_implement_still_reads(self):
        self.assertEqual(
            gaps({"decompose": bound(2, "inferred"),
                  "implement": {"unmeasurable": "no implement boundary:"
                                " no later commit checks a row"}},
                 breakdown(S1)),
            {"label": "inferred", "routes": 0, "source": "section"})

    def test_a_failed_read_of_the_decompose_version(self):
        self.assertEqual(self.section(None),
                         {"unmeasurable": "read failed"})


CURRENT = breakdown(S1, S2, row("S10", "tenth")).splitlines()


def findings(text):
    return decompose_signals.review_findings(text, CURRENT)


class TestReviewFindings(unittest.TestCase):
    def test_no_review_md(self):
        self.assertEqual(findings(None), {"unmeasurable": "no review.md"})

    def test_a_review_with_no_finding_heading(self):
        self.assertEqual(
            findings("# Review: demo\n\n## Scope\n\nS1.\n\n## Findings\n\n"
                     "None.\n\n## Verdict\n\nShip.\n"),
            {"findings": 0, "reason": "no finding heading"})

    def test_every_finding_shape_and_which_name_an_item(self):
        text = "\n".join([
            "# Critical: a level-1 heading is the title, S1",
            "## Findings",
            "### Critical: the walk drops a ref (S1)",
            "## Major — ordering",
            "Names nothing.",
            "### **Minor**: emphasis is stripped",
            "In S2's row.",
            "## F1 — ordinal label",
            "Touches S10 only.",
            "### Finding 2 — spelled out",
            "#### Evidence",
            "S2 again, under a sub-heading of the finding.",
            "### 3. numbered",
            "#### high: lower case counts",
            "##### Minor: level 5 is not a finding",
            "```",
            "### Major: inside a fence",
            "```",
            "## Highlights",
            "S1 here is outside every finding.",
            "## Verdict",
        ])
        self.assertEqual(findings(text),
                         {"label": "observed", "findings": 7, "named": 3})

    def test_s1_does_not_match_inside_s10(self):
        self.assertEqual(findings("## F1 — S10 and WS1 and S1x\n"),
                         {"label": "observed", "findings": 1, "named": 0})

if __name__ == "__main__":
    unittest.main()
