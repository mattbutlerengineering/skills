"""decompose_signals.py — Decompose outcome signals from git history.

The run is docs/features/decompose-outcome-signals/ (ADR-0109's boundary
rule, ADR-0110's import edges). Every case here runs against a REAL temp
git repo built by the Repo fixture below, because author-date order and
pathspec semantics are what is under test (architecture.md, Decisions);
a failing fake runner covers only the CLI-failure strings, and a
recording wrapper around the real runner pins the git verbs the tool is
allowed to run.
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling helper imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
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

    def test_a_merge_resolved_to_the_other_parent_hides_no_boundary(self):
        """git log's default history simplification follows only the
        TREESAME parent of a merge. A run branch that merged its trunk
        and took the trunk's breakdown would lose its own boundary
        commits and read as unmeasurable; the walk reads full history."""
        self.repo.commit("feat: base", **{at("README.md"): "hi\n"})
        trunk = self.repo.git("branch", "--show-current")
        self.repo.git("checkout", "-q", "-b", "feat/demo")
        d = self.repo.commit("docs(demo): decompose — plan", **{BD: PLAN})
        i = self.repo.commit("docs(demo): implement — done",
                             **{BD: TICKED})
        self.repo.git("checkout", "-q", trunk)
        self.repo.commit("feat: demo (#1)", **{BD: TICKED})
        self.repo.commit("docs: a later edit", **{BD: TICKED + "\nnote\n"})
        self.repo.git("checkout", "-q", "feat/demo")
        self.repo.git("merge", "-q", "-X", "theirs", trunk, "-m", "merge")
        self.repo.git("branch", "-q", "-D", trunk)
        self.assertEqual(self.bounds(),
                         {"decompose": {"sha": d, "label": "observed"},
                          "implement": {"sha": i, "label": "observed"}})


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


# codex-style-standards-enforcement's renumbering (ebe8b2a -> 5f30760):
# 14 work orders keep every title while WO-0045..0058 become
# WO-0051..0064, their blocked-by clauses renumbered and the first five
# ticked. Keys 0051..0058 sit in both versions on different items.
RENUMBERED_TITLES = (
    "author the real `docs/adr/**` file(s)", "`standards_index.py` parser",
    "wire it into `factory.py`", "detector `K` and selftest fixtures",
    "detector `M` and selftest fixtures", "back-fill normative statements",
    "hand-curate the first entries", "regenerate `docs/standards.json`",
    "the review skill step", "the reviewer charter step",
    "the architect skill step", "the architect charter step",
    "full battery green", "resolve the deferred acceptance bar")


def wo(n):
    return f"WO-{n:04d}"


def renumbered(first, ticked=0):
    """The 14 rows keyed from wo(first), each blocked by the one before."""
    return [row(wo(first + n), title, done=n < ticked,
                rest=" — size:S, blocked by: "
                + (wo(first + n - 1) if n else "—"))
            for n, title in enumerate(RENUMBERED_TITLES)]


class TestTitleFirstIdentity(unittest.TestCase):
    """Owner decision 6: title first, key fallback (architecture.md,
    Work-item diff)."""

    def test_a_renumbering_that_keeps_every_title_is_fourteen_renames(self):
        self.assertEqual(replan(renumbered(45), renumbered(51, ticked=5)),
                         counts(14, renamed=14))

    def test_a_title_differing_in_case_code_marks_spacing_or_stop(self):
        self.assertEqual(
            replan([row("S1", "wire the `factory.py` verb"),
                    row("S2", "Pin it"), S3],
                   [row("S2", "Wire  the factory.py   VERB."),
                    row("S3", "pin it:"), row("S9", "third")]),
            counts(3, renamed=3))

    def test_title_beats_key(self):
        self.assertEqual(
            replan([row("S3", "X"), row("S4", "Y")],
                   [row("S3", "Y"), row("S4", "Z")]),
            counts(2, added=1, dropped=1, renamed=1))

    def test_a_kept_key_under_a_new_title_is_kept(self):
        self.assertEqual(replan([S1, S2], [row("S1", "first, retitled"), S2]),
                         counts(2))

    def test_a_repeated_title_falls_back_to_the_key(self):
        same = [row("S1", "same"), row("S2", "same")]
        self.assertEqual(replan(same, same), counts(2))
        self.assertEqual(
            replan(same, [row("S3", "same"), row("S4", "same")]),
            counts(2, added=2, dropped=2))

    def test_a_dropped_key_an_i_version_item_uses_is_not_cited(self):
        self.assertEqual(
            replan([row("S1", "alpha"), row("S2", "beta")],
                   [row("S2", "alpha"), row("S4", "half of S2"),
                    row("S5", "rest of S2")]),
            counts(2, added=2, dropped=1, renamed=1))

    def test_a_renamed_item_citing_two_added_keys_is_a_split(self):
        self.assertEqual(
            replan([row("S1", "alpha"), S2],
                   [row("S3", "alpha — moved to S4 and S5"), S2,
                    row("S4", "a"), row("S5", "b")]),
            counts(2, added=2, split=1, renamed=1))

    def test_a_duplicate_key_is_checked_before_matching(self):
        self.assertEqual(
            replan([S1, S2], [row("S7", "first"), row("S7", "second")]),
            {"unmeasurable":
             f"duplicate work-item key S7 at {I_SHA[:7]}"})


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


CURRENT = breakdown(S1, S2).splitlines()


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


P = "decompose-signals: "
NO_REVIEW = "review-traced unmeasurable — no review.md"


class ReportCase(unittest.TestCase):
    """main([]) against a real temp repo; every line asserted exactly."""

    def setUp(self):
        self.repo = Repo(self)
        self.repo.commit("feat: base", **{at("README.md"): "hi\n"})

    def main(self, argv=(), run=None):
        return cli_contract.capture(decompose_signals.main, list(argv),
                                    root=self.repo.root,
                                    run=run or git_run())

    def header(self):
        listing = self.repo.git("for-each-ref",
                                "--format=%(refname) %(objectname)")
        lines = sorted(line for line in listing.splitlines()
                       if not line.startswith("refs/stash "))
        digest = hashlib.sha256(
            "".join(f"{line}\n" for line in lines).encode()).hexdigest()
        return [f"{P}refs read — refs/heads ({len(lines)}); refs/stash"
                f" skipped; digest {digest[:12]}",
                f"{P}boundary rule — {decompose_signals.RULE}"]

    def run_lines(self, out):
        return [line for line in out.splitlines()
                if line.startswith(P + "feature:")
                or line.startswith(P + "maintenance:")
                or line.startswith(P + "product ")]

    def only_run_line(self):
        code, out = self.main()
        self.assertEqual(code, 0, out)
        lines = self.run_lines(out)
        self.assertEqual(len(lines), 1, out)
        return lines[0]


def sha7(sha):
    return sha[:7]


class TestTheFiveFixtureRuns(ReportCase):
    def test_a_run_with_no_re_plans(self):
        d = self.repo.commit("docs(demo): decompose — plan", **{BD: PLAN})
        i = self.repo.commit("docs(demo): implement — done", **{BD: TICKED})
        self.assertEqual(self.only_run_line(), (
            f"{P}feature:demo — decompose observed {sha7(d)}, implement"
            f" observed {sha7(i)}; re-plan 0 of 2 (added 0, dropped 0,"
            " split 0, merged 0; renamed 0) observed; design gaps 0"
            f" observed; {NO_REVIEW}"))

    def test_a_run_with_a_split_item(self):
        d = self.repo.commit("docs(demo): decompose — plan", **{BD: PLAN})
        i = self.repo.commit("feat: S1, split", **{BD: breakdown(
            row("S1", "first — superseded by S3 and S4", done=True),
            row("S2", "second"), row("S3", "a"), row("S4", "b"))})
        self.assertEqual(self.only_run_line(), (
            f"{P}feature:demo — decompose observed {sha7(d)}, implement"
            f" inferred {sha7(i)}; re-plan 3 of 2 (added 2, dropped 0,"
            " split 1, merged 0; renamed 0) inferred; design gaps 0"
            f" inferred; {NO_REVIEW}"))

    def test_a_run_routed_back_to_architect(self):
        d = self.repo.commit("docs(demo): decompose — plan", **{BD: PLAN})
        self.repo.commit("docs(demo): architect — the gap",
                         **{ARCH: "# Architecture\n"})
        i = self.repo.commit("docs(demo): implement — done", **{BD: TICKED})
        self.assertEqual(self.only_run_line(), (
            f"{P}feature:demo — decompose observed {sha7(d)}, implement"
            f" observed {sha7(i)}; re-plan 0 of 2 (added 0, dropped 0,"
            " split 0, merged 0; renamed 0) observed; design gaps 1"
            f" observed; {NO_REVIEW}"))

    def test_a_run_with_only_inferred_boundaries(self):
        d = self.repo.commit("feat: plan", **{BD: PLAN})
        i = self.repo.commit("feat: S1", **{BD: TICKED})
        self.assertEqual(self.only_run_line(), (
            f"{P}feature:demo — decompose inferred {sha7(d)}, implement"
            f" inferred {sha7(i)}; re-plan 0 of 2 (added 0, dropped 0,"
            " split 0, merged 0; renamed 0) inferred; design gaps 0"
            f" inferred; {NO_REVIEW}"))

    def test_an_unmeasurable_run(self):
        self.repo.write(f"{RUN}/breakdown.md", PLAN)
        reason = f"no commit on the refs read changes {RUN}/breakdown.md"
        self.assertEqual(self.only_run_line(), (
            f"{P}feature:demo — decompose none, implement none; re-plan"
            f" unmeasurable — {reason}; design gaps unmeasurable —"
            f" {reason}; {NO_REVIEW}"))


class TestARenumberedRun(ReportCase):
    def test_a_renumbering_between_d_and_i_is_no_re_plan(self):
        d = self.repo.commit("feat: plan",
                             **{BD: breakdown(*renumbered(45))})
        i = self.repo.commit("feat: renumber and tick",
                             **{BD: breakdown(*renumbered(51, ticked=5))})
        self.assertEqual(self.only_run_line(), (
            f"{P}feature:demo — decompose inferred {sha7(d)}, implement"
            f" inferred {sha7(i)}; re-plan 0 of 14 (added 0, dropped 0,"
            " split 0, merged 0; renamed 14) inferred; design gaps 0"
            f" inferred; {NO_REVIEW}"))


class TestReviewShapes(ReportCase):
    def setUp(self):
        super().setUp()
        self.repo.commit("feat: plan", **{BD: PLAN})
        self.repo.commit("feat: S1", **{BD: TICKED})

    def review_part(self):
        return self.only_run_line().rsplit("; ", 1)[1]

    def test_no_review_md(self):
        self.assertEqual(self.review_part(), NO_REVIEW)

    def test_a_review_with_no_finding_heading(self):
        self.repo.write(f"{RUN}/review.md", "# Review\n\n## Verdict\n\nOK\n")
        self.assertEqual(
            self.review_part(),
            "review-traced 0 findings — review.md has no finding heading")
        self.assertNotEqual(self.review_part(), NO_REVIEW)

    def test_findings_that_name_an_item(self):
        self.repo.write(f"{RUN}/review.md",
                        "# Review\n\n### Major: S1 is off\n\n"
                        "### Minor: nothing named\n")
        self.assertEqual(self.review_part(),
                         "review-traced 1 of 2 findings name an item")


class TestTheWholeReport(ReportCase, cli_contract.ReportContract,
                         cli_contract.CliContract):
    summary_line = f"{P}3 run(s), 0 problem(s)"
    usage_fragment = "python3 decompose_signals.py [--record]"
    bad_argv = ("--nope",)

    def setUp(self):
        super().setUp()
        a, b = "docs/features/a", "docs/features/b"
        self.a_d = self.repo.commit(
            "docs(a): decompose — plan", **{at(f"{a}/breakdown.md"): PLAN})
        self.b_d = self.repo.commit(
            "feat: plan b", **{at(f"{b}/breakdown.md"): breakdown(
                row("S1", "only"))})
        self.a_i = self.repo.commit(
            "docs(a): implement — done",
            **{at(f"{a}/breakdown.md"): TICKED})
        self.b_i = self.repo.commit(
            "feat: b grows", **{at(f"{b}/breakdown.md"): breakdown(
                row("S1", "only", done=True), row("S2", "new"))})
        self.repo.write(f"{a}/review.md", "## F1 — S1\n\n## F2 — none\n")
        self.repo.write(f"{b}/review.md", "# Review\n")
        self.repo.write("docs/fixes/c/breakdown.md", PLAN)

    def clean_cli(self):
        return self.main()

    def run_cli(self, argv):
        return self.main(argv)

    def test_the_exact_report(self):
        code, out = self.main()
        reason = ("no commit on the refs read changes"
                  " docs/fixes/c/breakdown.md")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), self.header() + [
            f"{P}feature:a — decompose observed {sha7(self.a_d)}, implement"
            f" observed {sha7(self.a_i)}; re-plan 0 of 2 (added 0, dropped"
            " 0, split 0, merged 0; renamed 0) observed; design gaps 0"
            " observed; review-traced 1 of 2 findings name an item",
            f"{P}feature:b — decompose inferred {sha7(self.b_d)}, implement"
            f" inferred {sha7(self.b_i)}; re-plan 1 of 1 (added 1, dropped"
            " 0, split 0, merged 0; renamed 0) inferred; design gaps 0"
            " inferred; review-traced 0 findings — review.md has no"
            " finding heading",
            f"{P}maintenance:c — decompose none, implement none; re-plan"
            f" unmeasurable — {reason}; design gaps unmeasurable —"
            f" {reason}; {NO_REVIEW}",
            f"{P}aggregate re-plan — observed 0/2 over 1 run(s); inferred"
            " 1/1 over 1 run(s); combined 1/3 over 2 run(s); unmeasurable"
            " 1 run(s)",
            f"{P}aggregate design gaps — observed 0/1 over 1 run(s);"
            " inferred 0/1 over 1 run(s); combined 0/2 over 2 run(s);"
            " unmeasurable 1 run(s)",
            f"{P}aggregate review-traced — observed 1/2 over 2 run(s);"
            " inferred 0/0 over 0 run(s); combined 1/2 over 2 run(s);"
            " unmeasurable 1 run(s)",
            self.summary_line])

    def test_the_rule_names_its_adr(self):
        self.assertIn("ADR-0109", decompose_signals.RULE)


class TestReportFailures(ReportCase):
    def test_a_failed_for_each_ref_prints_no_run_lines(self):
        self.repo.commit("feat: plan", **{BD: PLAN})
        code, out = self.main(run=failing(BOOM))
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            f"{P}git for-each-ref failed: fatal: boom",
            f"{P}0 run(s), 1 problem(s)"])

    def test_a_failed_log_prints_no_run_lines(self):
        self.repo.commit("feat: plan", **{BD: PLAN})
        real = git_run()

        def run(args, input=None, cwd=None):
            if args[0] == "log":
                raise BOOM
            return real(args, input=input, cwd=cwd)
        code, out = self.main(run=run)
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(), [
            f"{P}git log failed: fatal: boom", f"{P}0 run(s), 1 problem(s)"])

    def test_a_failed_show_is_read_failed_plus_one_problem(self):
        self.repo.commit("feat: plan", **{BD: PLAN})
        real = git_run()

        def run(args, input=None, cwd=None):
            if args[0] == "show":
                raise BOOM
            return real(args, input=input, cwd=cwd)
        code, out = self.main(run=run)
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines()[2:], [
            f"{P}feature:demo — decompose none, implement none; re-plan"
            " unmeasurable — read failed; design gaps unmeasurable — read"
            f" failed; {NO_REVIEW}",
            f"{P}aggregate re-plan — observed 0/0 over 0 run(s); inferred"
            " 0/0 over 0 run(s); combined 0/0 over 0 run(s); unmeasurable"
            " 1 run(s)",
            f"{P}aggregate design gaps — observed 0/0 over 0 run(s);"
            " inferred 0/0 over 0 run(s); combined 0/0 over 0 run(s);"
            " unmeasurable 1 run(s)",
            f"{P}aggregate review-traced — observed 0/0 over 0 run(s);"
            " inferred 0/0 over 0 run(s); combined 0/0 over 0 run(s);"
            " unmeasurable 1 run(s)",
            f"{P}git show failed: fatal: boom",
            f"{P}1 run(s), 1 problem(s)"])

    def test_only_local_read_only_verbs_are_run_end_to_end(self):
        self.repo.commit("feat: plan", **{BD: PLAN})
        self.repo.commit("feat: S1", **{BD: TICKED})
        real, verbs = git_run(), []

        def run(args, input=None, cwd=None):
            verbs.append(args[0])
            return real(args, input=input, cwd=cwd)
        self.main(run=run)
        self.assertLessEqual(set(verbs), ALLOWED_VERBS)


class TestRecord(ReportCase):
    def setUp(self):
        super().setUp()
        self.repo.commit("feat: plan", **{BD: PLAN})
        self.repo.commit("feat: S1", **{BD: TICKED})
        self.results = self.repo.root / "evals" / "results"
        self.name = (f"decompose-signals-{datetime.date.today().isoformat()}"
                     ".json")

    def snapshots(self):
        return sorted(self.results.glob("*.json")) if \
            self.results.is_dir() else []

    def test_a_clean_record_writes_one_snapshot(self):
        code, out = self.main(["--record"])
        self.assertEqual(code, 0, out)
        self.assertEqual(self.snapshots(), [self.results / self.name])
        self.assertIn(f"{P}recorded evals/results/{self.name}",
                      out.splitlines())
        snapshot = json.loads(self.snapshots()[0].read_text(
            encoding="utf-8"))
        self.assertEqual(sorted(snapshot), sorted(
            ("date", "head", "refs", "refs_digest", "rule", "runs",
             "aggregate")))
        self.assertEqual(snapshot["head"], self.repo.git("rev-parse",
                                                         "HEAD"))
        self.assertEqual(snapshot["rule"], decompose_signals.RULE)
        self.assertEqual([r["run"] for r in snapshot["runs"]],
                         ["feature:demo"])

    def test_a_dirty_docs_tree_refuses(self):
        self.repo.write(f"{RUN}/notes.md", "uncommitted\n")
        code, out = self.main(["--record"])
        self.assertEqual(code, 1)
        self.assertEqual(self.snapshots(), [])
        self.assertIn(f"{P}--record refused: git status --porcelain --"
                      " docs/ is not empty", out.splitlines())

    def test_a_measurement_with_problems_refuses(self):
        real = git_run()

        def run(args, input=None, cwd=None):
            if args[0] == "show":
                raise BOOM
            return real(args, input=input, cwd=cwd)
        code, out = self.main(["--record"], run=run)
        self.assertEqual(code, 1)
        self.assertEqual(self.snapshots(), [])
        self.assertIn(f"{P}--record refused: the measurement has problems",
                      out.splitlines())

    def test_two_records_on_the_same_refs_agree(self):
        self.main(["--record"])
        self.main(["--record"])
        first, second = (json.loads(path.read_text(encoding="utf-8"))
                         for path in self.snapshots())
        for key in ("refs_digest", "runs", "aggregate"):
            with self.subTest(key=key):
                self.assertEqual(first[key], second[key])
        self.assertEqual(len(self.snapshots()), 2)

if __name__ == "__main__":
    unittest.main()
