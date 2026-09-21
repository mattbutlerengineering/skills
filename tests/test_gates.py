"""Factory gate detectors (gates.py) — fixture-tree tests, plus the
live-tree CI guards over .github/workflows/ and the two Makefiles
(TestLockstep and the run-step invariant).

Same discipline as test_lint: every checker is exercised through
its public interface against a temp fixture tree, and tests assert the
exact problem strings callers will print.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import cost_ledger
import gates
from factory_init import product_form

# discover puts tests/ on sys.path; selective package-style runs need it
# added for the sibling helper import
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cli_contract  # noqa: E402
from factory_fixture import CONFIG  # noqa: E402
from fixture_tree import FixtureTree  # noqa: E402
from make_parse import make_recipe  # noqa: E402
import workflow_parse  # noqa: E402


def offending_run_steps(text, allowed=()):
    """Run steps in a workflow text that neither go through make nor open
    with an allowlisted line — the run-step invariant's helper, factored
    out so the guard itself is testable against synthetic drift. A step's
    identity is its first non-comment line."""
    bad = []
    for step in workflow_parse.run_steps(text):
        first = next((line.strip() for line in step.splitlines()
                      if line.strip() and not line.strip().startswith("#")),
                     "")
        if first.startswith("make ") or first in allowed:
            continue
        bad.append(step)
    return bad


class TestWoCitation(unittest.TestCase):
    def test_uncited_row_is_flagged_and_cited_row_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/breakdown.md",
                       "- [ ] WO-0001 slice one (PRD-0001 §Solution)\n"
                       "- [ ] WO-0002 uncited\n")
            problems = gates.check_wo_citation(tree.root)
            self.assertEqual(problems, [
                "A: docs/features/demo/breakdown.md:2 work-order row"
                " WO-0002 cites no PRD id"])


class TestLinkIntegrity(unittest.TestCase):
    def build(self, tmp):
        tree = FixtureTree(tmp)
        tree.write("docs/features/demo/prd.md",
                   "---\nstage: prd\nid: PRD-0001\n---\n# PRD\n")
        tree.write("docs/adr/0001-real.md", "# Real\n")
        return tree

    def test_resolving_tokens_are_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp)
            tree.write("docs/features/demo/breakdown.md",
                       "- [ ] WO-0001 slice (PRD-0001 §Solution)\n")
            tree.write("CONTEXT.md", "PRD-0001 per ADR-0001, see WO-0001.\n")
            self.assertEqual(gates.check_link_integrity(tree.root), [])

    def test_dangling_tokens_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp)
            tree.write("CONTEXT.md", "PRD-0099 and ADR-0042 and WO-0003.\n")
            self.assertEqual(gates.check_link_integrity(tree.root), [
                "C: CONTEXT.md:1 dangling PRD-0099"
                " (no prd.md declares this id)",
                "C: CONTEXT.md:1 dangling ADR-0042 (no docs/adr file)",
                "C: CONTEXT.md:1 dangling WO-0003 (no breakdown row)"])

    def test_duplicate_prd_id_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp)
            tree.write("docs/features/other/prd.md",
                       "---\nstage: prd\nid: PRD-0001\n---\n# PRD\n")
            problems = gates.check_link_integrity(tree.root)
            self.assertEqual(problems, [
                "C: duplicate PRD id PRD-0001 in"
                " docs/features/demo/prd.md, docs/features/other/prd.md"])

    def test_dangling_token_outside_docs_is_now_flagged(self):
        # Issue #456: _scannable_files used to be docs/**/*.md + CONTEXT.md
        # only, so a dangling ADR token in .github/, factory/, skills/ or a
        # root .md file was never seen.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp)
            tree.write("README.md", "See ADR-0042 for context.\n")
            tree.write(".github/PULL_REQUEST_TEMPLATE.md", "Cites ADR-0043.\n")
            tree.write("skills/demo/SKILL.md", "Per ADR-0044.\n")
            tree.write("factory/CHARTERS.md", "Per ADR-0045.\n")
            problems = gates.check_link_integrity(tree.root)
            self.assertEqual(problems, [
                "C: .github/PULL_REQUEST_TEMPLATE.md:1 dangling ADR-0043"
                " (no docs/adr file)",
                "C: README.md:1 dangling ADR-0042 (no docs/adr file)",
                "C: factory/CHARTERS.md:1 dangling ADR-0045"
                " (no docs/adr file)",
                "C: skills/demo/SKILL.md:1 dangling ADR-0044"
                " (no docs/adr file)"])

    def test_factory_templates_and_fixtures_stay_out_of_scope(self):
        # factory/templates/ is a seed tree checked against its OWN
        # numbering by TestSeededADRs, and factory/evals/fixtures/ carries
        # intentionally fake WO-/PRD- tokens. Neither should ever surface
        # a "C:" problem from the live repo's own detector.
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp)
            tree.write("factory/templates/docs/adr/0001-seed.md",
                       "Cites ADR-9999.\n")
            tree.write("factory/evals/fixtures/demo/work-order.md",
                       "WO-9001 (PRD-9001 §Solution)\n")
            self.assertEqual(gates.check_link_integrity(tree.root), [])


class TestBlueprintDrift(unittest.TestCase):
    """D (origin: WO-0008): the approved blueprint is docs/adr — its files,
    its index, and the artifacts that cite it must agree."""

    INDEX_HEAD = ("# ADRs\n\n| ADR | Decision | Status |\n"
                  "|-----|----------|--------|\n")

    def build(self, tmp, *rows):
        tree = FixtureTree(tmp)
        tree.write("docs/adr/README.md", self.INDEX_HEAD + "".join(rows))
        return tree

    def test_indexed_and_cited_blueprint_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp,
                "| [0001](0001-spine.md) | Spine | accepted |\n",
                "| [0002](0002-old.md) | Old | superseded in part by"
                " ADR-0001 |\n")
            tree.write("docs/adr/0001-spine.md",
                       "# Spine\n\n- Status: accepted\n")
            tree.write("docs/adr/0002-old.md",
                       "# Old\n\n- Status: superseded in part by ADR-0001\n")
            tree.write("CONTEXT.md", "Per ADR-0001 and ADR-0002.\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [])

    def test_no_adr_dir_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(gates.check_blueprint_drift(Path(tmp)), [])

    def test_shipping_annotation_does_not_count_as_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, "| [0001](0001-spine.md) | Spine | accepted |\n")
            tree.write("docs/adr/0001-spine.md",
                       "# Spine\n\n- Status: accepted (shipped 2026-07-06)\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [])

    def test_missing_index_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/adr/0001-spine.md",
                       "# Spine\n\n- Status: accepted\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [
                "D: docs/adr/README.md is missing"
                " (ADR files present, no blueprint index)"])

    def test_unstated_and_unknown_status_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp,
                "| [0001](0001-spine.md) | Spine | accepted |\n",
                "| [0002](0002-typo.md) | Typo | aproved |\n")
            tree.write("docs/adr/0001-spine.md", "# Spine\n\nNo status.\n")
            tree.write("docs/adr/0002-typo.md",
                       "# Typo\n\n- Status: aproved\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [
                "D: docs/adr/0001-spine.md declares no Status line",
                "D: docs/adr/0002-typo.md:3 unknown ADR status 'aproved'"])

    def test_unindexed_adr_and_index_row_without_a_file_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, "| [0009](0009-ghost.md) | Ghost | accepted |\n")
            tree.write("docs/adr/0001-spine.md",
                       "# Spine\n\n- Status: accepted\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [
                "D: docs/adr/README.md:5 index row ADR-0009 links to"
                " missing file 0009-ghost.md",
                "D: docs/adr/README.md has no index row for ADR-0001"])

    def test_index_status_out_of_step_with_the_file_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, "| [0001](0001-spine.md) | Spine | accepted |\n")
            tree.write("docs/adr/0001-spine.md",
                       "# Spine\n\n- Status: superseded by ADR-0002\n")
            tree.write("docs/adr/0002-new.md",
                       "# New\n\n- Status: accepted\n")
            problems = gates.check_blueprint_drift(tree.root)
            self.assertIn(
                "D: docs/adr/README.md:5 ADR-0001 index status 'accepted'"
                " does not match the file's 'superseded by ADR-0002'",
                problems)

    def test_artifact_citing_a_superseded_decision_is_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp,
                "| [0001](0001-old.md) | Old | superseded by ADR-0002 |\n",
                "| [0002](0002-new.md) | New | accepted |\n")
            tree.write("docs/adr/0001-old.md",
                       "# Old\n\n- Status: superseded by ADR-0002\n")
            tree.write("docs/adr/0002-new.md",
                       "# New\n\n- Status: accepted\n\nSupersedes ADR-0001.\n")
            tree.write("docs/features/demo/breakdown.md",
                       "- [ ] WO-0001 build it per ADR-0001 (PRD-0001)\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [
                "D: docs/features/demo/breakdown.md:1 cites ADR-0001,"
                " superseded by ADR-0002 (blueprint drift)"])


class TestAdrStatusVocabulary(unittest.TestCase):
    """The ADR README's Statuses prose must name every head that
    gates.ADR_STATUS accepts. The regex is the authority (detector D
    enforces it); the README is where a human learns the vocabulary, and
    the two heads it used to omit — "superseded in part by" and "amended
    by" — are load-bearing precisely because they do NOT retire a
    decision."""

    README = (Path(__file__).resolve().parents[1]
              / "docs" / "adr" / "README.md")
    HEADS = ("accepted", "provisional", "superseded by ADR-",
             "superseded in part by ADR-", "amended by ADR-")

    def statuses_paragraph(self):
        text = self.README.read_text(encoding="utf-8")
        start = text.index("Statuses:")
        return text[start:text.index("\n\n", start)]

    def test_readme_names_every_status_head(self):
        prose = self.statuses_paragraph()
        for head in self.HEADS:
            self.assertIn(head, prose)

    def test_readme_names_the_authority(self):
        self.assertIn("ADR_STATUS", self.statuses_paragraph())

    def test_every_named_head_matches_the_regex(self):
        for example, retired in (
                ("accepted", False),
                ("provisional", False),
                ("superseded by ADR-0042", True),
                ("superseded in part by ADR-0042", False),
                ("amended by ADR-0042", False)):
            match = gates.ADR_STATUS.match(example)
            self.assertIsNotNone(match, example)
            self.assertEqual(bool(match.group("retired")), retired, example)


class TestCostLedger(unittest.TestCase):
    """G (origin: WO-0008, ADR-0034): the append-only cost ledger is the
    factory's measurement substrate; a merged order missing from it is a
    gating finding, and an absent ledger means no runs are recorded yet."""

    # Fixture rows come from the writer seam itself (cost_ledger.entry),
    # so this suite cannot pin G against a shape no current writer
    # produces. The one deliberate exception is the labelled legacy
    # fixture below.
    LINE = cost_ledger.entry("WO-0001", "r-1", "m", 1200, 0.42, "merged",
                             "2026-08-01")

    def build(self, tmp, *lines, row="- [x] WO-0001 slice (PRD-0001)\n"):
        tree = FixtureTree(tmp)
        tree.write("docs/features/demo/breakdown.md", row)
        if lines:
            tree.write(cost_ledger.COST_LEDGER,
                       "".join(json.dumps(line) + "\n" for line in lines))
        return tree

    def test_absent_ledger_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp)
            self.assertEqual(gates.check_cost_ledger(tree.root), [])

    def test_well_formed_ledger_covering_merged_orders_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp, self.LINE)
            self.assertEqual(gates.check_cost_ledger(tree.root), [])

    def test_a_legacy_row_without_at_is_tolerated(self):
        """The ONE deliberately legacy-shaped fixture in this suite: the
        real costs.jsonl still holds pre-`at` rows (the ledger is
        append-only, never backfilled) and G gates the real repo in CI,
        so it must keep accepting them even though no current writer
        produces the shape. Every other fixture builds through
        cost_ledger.entry."""
        legacy = {"wo": "WO-0001", "run_id": "r-1", "model": "m",
                  "tokens": 1200, "cost": 0.42, "outcome": "merged"}
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp, legacy)
            self.assertEqual(gates.check_cost_ledger(tree.root), [])

    def test_merged_order_with_no_ledger_line_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, self.LINE,
                row="- [x] WO-0001 one (PRD-0001)\n"
                    "- [x] WO-0002 two (PRD-0001)\n"
                    "- [ ] WO-0003 unmerged (PRD-0001)\n")
            self.assertEqual(gates.check_cost_ledger(tree.root), [
                "G: docs/features/demo/breakdown.md:2 merged work order"
                " WO-0002 has no line in docs/factory/costs.jsonl"])

    def test_a_row_no_other_accessor_can_parse_is_not_a_merged_order(self):
        """G reaches row_done through a raw WO_TOKEN.search rather than
        through a sibling accessor, so it is the one place the checked-row
        grammar and the row grammar can disagree in production. A line
        whose box has no trailing space is no row to work_queue, the
        reconcile sweep or the dashboard; it must be no merged work order
        here either, or G reports a WO id nothing else can see."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, self.LINE,
                row="- [x] WO-0001 one (PRD-0001)\n"
                    "- [x]a WO-0002 no space after the box (PRD-0001)\n")
            self.assertEqual(gates.check_cost_ledger(tree.root), [])

    def test_pre_ledger_annotated_row_is_exempt_from_recording(self):
        """ADR-0043: a work order merged before the ledger was born carries
        (pre-ledger) on its breakdown row, and G's merged-row-must-be-
        recorded check skips it. The exemption lives in the knowledge
        plane, on the row it describes — never as a repo-specific list in
        this mirrored module, which would leak one repo's WO ids into
        every stamped repo."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, self.LINE,
                row="- [x] WO-0001 one (PRD-0001)\n"
                    "- [x] WO-0002 two (PRD-0001) (pre-ledger)\n")
            self.assertEqual(gates.check_cost_ledger(tree.root), [])

    def test_pre_ledger_as_mid_row_prose_does_not_exempt(self):
        """The annotation is a TRAILING mark (knowledge_plane.row_pre_ledger,
        ADR-0043) — a merged row that merely mentions (pre-ledger) mid-row
        still owes its ledger line."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, self.LINE,
                row="- [x] WO-0001 one (PRD-0001)\n"
                    "- [x] WO-0002 explain the (pre-ledger) mark"
                    " (PRD-0001)\n")
            self.assertEqual(gates.check_cost_ledger(tree.root), [
                "G: docs/features/demo/breakdown.md:2 merged work order"
                " WO-0002 has no line in docs/factory/costs.jsonl"])

    def test_pre_ledger_annotation_does_not_waive_the_reverse_check(self):
        """The annotation waives only must-be-recorded. A recorded wo must
        still have a breakdown row, annotated or not."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, dict(self.LINE, wo="WO-0009"),
                row="- [x] WO-0001 one (PRD-0001) (pre-ledger)\n")
            self.assertEqual(gates.check_cost_ledger(tree.root), [
                "G: docs/factory/costs.jsonl:1 wo WO-0009 has no"
                " breakdown row"])

    def test_malformed_line_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp, self.LINE)
            tree.write(cost_ledger.COST_LEDGER,
                       json.dumps(self.LINE) + "\n{not json\n[1, 2]\n")
            problems = gates.check_cost_ledger(tree.root)
            self.assertEqual(len(problems), 2, problems)
            self.assertTrue(problems[0].startswith(
                "G: docs/factory/costs.jsonl:2 is not valid JSON:"), problems)
            self.assertEqual(
                problems[1],
                "G: docs/factory/costs.jsonl:3 is not a JSON object")

    def test_wrong_fields_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, dict(self.LINE, note="extra"),
                # missing-fields row: deliberately unbuildable through
                # cost_ledger.entry — absent fields ARE the fixture
                {"wo": "WO-0001", "model": "m", "outcome": "merged"})
            self.assertEqual(gates.check_cost_ledger(tree.root), [
                "G: docs/factory/costs.jsonl:1 ledger line has unknown"
                " field(s): note",
                "G: docs/factory/costs.jsonl:2 ledger line is missing"
                " field(s): cost, run_id, tokens"])

    def test_bad_field_values_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, cost_ledger.entry("WO-0009", "", "m", -1, "free",
                                       "merged", "2026-08-01"))
            self.assertEqual(gates.check_cost_ledger(tree.root), [
                "G: docs/factory/costs.jsonl:1 run_id must be a non-empty"
                " string",
                "G: docs/factory/costs.jsonl:1 tokens must be a non-negative"
                " integer",
                "G: docs/factory/costs.jsonl:1 cost must be a non-negative"
                " number",
                "G: docs/factory/costs.jsonl:1 wo WO-0009 has no breakdown"
                " row",
                "G: docs/features/demo/breakdown.md:1 merged work order"
                " WO-0001 has no line in docs/factory/costs.jsonl"])

    def test_untyped_wo_field_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, cost_ledger.entry("nope", "r", "m", 0, 0, "failed",
                                       "2026-08-01"))
            problems = gates.check_cost_ledger(tree.root)
            self.assertIn(
                "G: docs/factory/costs.jsonl:1 wo 'nope' is not a WO-####"
                " token", problems)

    def test_blank_lines_are_tolerated(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp, self.LINE)
            tree.write(cost_ledger.COST_LEDGER,
                       json.dumps(self.LINE) + "\n\n")
            self.assertEqual(gates.check_cost_ledger(tree.root), [])

    def test_a_gate_latency_row_does_not_satisfy_merged_coverage(self):
        """Issue #222: a gate_wait row records queue time — model none,
        0 tokens, $0.00 — and the monthly breaker's sum excludes it
        (cost_report skips gate rows). Counting it as the merged order's
        ledger line kept G green forever while recorded spend stayed
        $0.00; spend coverage now requires a dispatched-run row."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, cost_ledger.gate_entry("WO-0001", "merge", 2379,
                                            "2026-07-12T03:12:55Z"))
            self.assertEqual(gates.check_cost_ledger(tree.root), [
                "G: docs/features/demo/breakdown.md:1 merged work order"
                " WO-0001 has no line in docs/factory/costs.jsonl"])

    def test_a_gate_row_beside_a_spend_row_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, self.LINE,
                cost_ledger.gate_entry("WO-0001", "merge", 2379,
                                       "2026-07-12T03:12:55Z"))
            self.assertEqual(gates.check_cost_ledger(tree.root), [])

    def test_a_gate_row_still_needs_a_breakdown_row(self):
        """Narrowing what satisfies coverage must not waive the reverse
        check: a gate row naming an unknown order is still
        ledger-to-breakdown drift."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, self.LINE,
                cost_ledger.gate_entry("WO-0002", "merge", 10,
                                       "2026-07-12T03:12:55Z"))
            self.assertEqual(gates.check_cost_ledger(tree.root), [
                "G: docs/factory/costs.jsonl:2 wo WO-0002 has no breakdown"
                " row"])


class TestStaleness(unittest.TestCase):
    """I (origin: WO-0008): a doc that points at a path which no longer
    exists is stale — the knowledge plane has moved on without it."""

    def test_resolving_links_are_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/adr/0001-spine.md", "# Spine\n")
            tree.write("CONTEXT.md", "See [spine](docs/adr/0001-spine.md).\n")
            tree.write("docs/guide.md",
                       "[up](../CONTEXT.md), [dir](adr), [anchor](#x),\n"
                       "[web](https://example.com/gone.md), [rooted](/docs)\n")
            self.assertEqual(gates.check_staleness(tree.root), [])

    def test_stale_links_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/guide.md",
                       "[moved](../ARCHIVE.md) and [gone](adr/0009-x.md#why)\n")
            self.assertEqual(gates.check_staleness(tree.root), [
                "I: docs/guide.md:1 stale link ../ARCHIVE.md (no such path)",
                "I: docs/guide.md:1 stale link adr/0009-x.md (no such path)"])


class TestArchitectureDrift(unittest.TestCase):
    """D (origin: #142): architecture.md is a blueprint too. A file it names
    as present or absent must agree with the tree, or the doc has gone stale
    and the build fails. Regression fixtures are the real drift PR #133
    caused: it added a root Makefile and deleted checks.yml while
    architecture.md still asserted the opposite, and D stayed green."""

    ARCH = "docs/features/software-factory/architecture.md"

    # --- declared claims block: the only way to pin a PRESENCE claim, because
    # architecture.md also names files that are planned and do not exist yet.
    def test_declared_claims_that_match_the_tree_are_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/workflows/checks.yml", "on: push\n")
            tree.write(self.ARCH,
                       "# Architecture\n\n```tree-claims\n"
                       "exists: .github/workflows/checks.yml\n"
                       "absent: Makefile\n```\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [])

    def test_declared_exists_claim_for_a_deleted_file_is_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)  # checks.yml deleted, as PR #133 does
            tree.write(self.ARCH,
                       "# Architecture\n\n```tree-claims\n"
                       "exists: .github/workflows/checks.yml\n```\n")
            self.assertEqual(
                gates.check_blueprint_drift(tree.root),
                [f"D: {self.ARCH}:4 claims .github/workflows/checks.yml"
                 " exists, but it does not (architecture.md is stale)"])

    def test_declared_absent_claim_for_a_created_file_is_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("Makefile", "check:\n\tpython3 gates.py\n")
            tree.write(self.ARCH,
                       "# Architecture\n\n```tree-claims\n"
                       "absent: Makefile\n```\n")
            self.assertEqual(
                gates.check_blueprint_drift(tree.root),
                [f"D: {self.ARCH}:4 claims Makefile is absent, but it"
                 " exists (architecture.md is stale)"])

    def test_unparseable_claim_line_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(self.ARCH,
                       "# Architecture\n\n```tree-claims\n"
                       "probably: Makefile\n```\n")
            self.assertEqual(
                gates.check_blueprint_drift(tree.root),
                [f"D: {self.ARCH}:4 unreadable tree claim 'probably:"
                 " Makefile' (expected 'exists: <path>' or"
                 " 'absent: <path>')"])

    def test_blank_lines_and_comments_in_the_block_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(self.ARCH,
                       "# Architecture\n\n```tree-claims\n"
                       "# this repo is not itself stamped\n\n"
                       "absent: Makefile\n```\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [])

    def test_a_glob_or_traversal_claim_is_refused_not_resolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(self.ARCH,
                       "# Architecture\n\n```tree-claims\n"
                       "exists: factory/templates/**\n```\n")
            self.assertEqual(
                gates.check_blueprint_drift(tree.root),
                [f"D: {self.ARCH}:4 tree claim 'factory/templates/**' is not"
                 " a plain repo path (no globs, no '..')"])

    # --- prose claims: a closed keyword vocabulary, anchored at a clause end.
    def test_prose_absence_claim_contradicted_by_the_tree_is_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("Makefile", "check:\n")
            tree.write(self.ARCH,
                       "# Architecture\n\nIt self-hosts by running the root"
                       " scripts directly; there is no `Makefile`, no"
                       " `tools/factory/` here.\n")
            self.assertEqual(
                gates.check_blueprint_drift(tree.root),
                [f"D: {self.ARCH}:3 says there is no Makefile, but it exists"
                 " (architecture.md is stale)"])

    def test_prose_absence_claim_that_holds_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(self.ARCH,
                       "# Architecture\n\nthere is no `Makefile`, no"
                       " `tools/factory/`, no `.github/factory.json` here.\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [])

    def test_prose_presence_claim_contradicted_by_the_tree_is_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(self.ARCH,
                       "# Architecture\n\n`.github/CODEOWNERS` exists here"
                       " and ships in the payload.\n")
            self.assertEqual(
                gates.check_blueprint_drift(tree.root),
                [f"D: {self.ARCH}:3 says .github/CODEOWNERS exists, but it"
                 " does not (architecture.md is stale)"])

    def test_prose_presence_claim_that_holds_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(".github/CODEOWNERS", "* @owner\n")
            tree.write(self.ARCH,
                       "# Architecture\n\n`.github/CODEOWNERS` exists here"
                       " and ships in the payload.\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [])

    # --- the false-positive class. A code span that is not an existence
    # claim must stay silent, or this detector dies the way H's attempts 1-2
    # did. "no X change is needed" modifies a NOUN; it asserts nothing.
    def test_no_followed_by_a_noun_is_not_an_absence_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("gates.py", "print()\n")
            tree.write(self.ARCH,
                       "# Architecture\n\nno `gates.py` change is needed,"
                       " and no `protocol.py` rewrite either.\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [])

    def test_a_bare_mention_of_a_planned_file_is_not_a_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write(self.ARCH,
                       "# Architecture\n\nRoadmap: `validator.yml` incl. the"
                       " non-authoring review job (WO-0004); `checks.yml` runs"
                       " lint and the detector suite.\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [])

    def test_claims_inside_a_fenced_example_are_inert(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("Makefile", "check:\n")
            tree.write(self.ARCH,
                       "# Architecture\n\n```\nthere is no `Makefile`.\n"
                       "```\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [])

    def test_no_architecture_md_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/adr/README.md", "# ADRs\n")
            self.assertEqual(gates.check_blueprint_drift(tree.root), [])


class TestScaffoldSync(unittest.TestCase):
    def manifested_tree(self, tmp, payload="check:\n"):
        tree = FixtureTree(tmp)
        path = tree.write("factory/templates/Makefile", payload)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        tree.write("factory/manifest.json",
                   json.dumps({"files": {"templates/Makefile": digest}}))
        return tree

    def test_matching_payload_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.manifested_tree(tmp)
            self.assertEqual(gates.check_scaffold_sync(tree.root), [])

    def test_tampered_payload_and_unmanifested_file_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.manifested_tree(tmp)
            tree.write("factory/templates/Makefile", "check: tampered\n")
            tree.write("factory/templates/extra.txt", "orphan\n")
            self.assertEqual(gates.check_scaffold_sync(tree.root), [
                "E: factory/templates/Makefile does not match its manifest"
                " checksum (re-run manifest update, never hand-edit)",
                "E: factory/templates/extra.txt is not in the manifest"])

    def test_missing_manifest_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(gates.check_scaffold_sync(Path(tmp)),
                             ["E: missing factory/manifest.json"])

    def test_a_manifest_that_is_not_json_is_a_problem(self):
        """Neither the malformed nor the undecodable manifest had a test
        before this run: E returned early on one and raised on the
        other, and nothing pinned either."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/manifest.json", "{nope")
            problems = gates.check_scaffold_sync(tree.root)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                "E: factory/manifest.json is not valid JSON:"), problems)

    def test_a_manifest_whose_bytes_are_not_utf8_is_a_problem(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/manifest.json", "").write_bytes(
                '{"files": {"a": "caf\u00e9"}}'.encode("latin-1"))
            problems = gates.check_scaffold_sync(tree.root)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                "E: factory/manifest.json is not valid JSON:"), problems)


class TestManifestFiles(unittest.TestCase):
    """The one statement of the manifest's walk-hash-key grammar: what
    update_manifest writes IS what check_scaffold_sync diffs against, so
    the writer/verifier pair cannot diverge (the detector-G discipline,
    applied to detector E)."""

    def test_walks_the_payload_with_posix_keys_and_sha256_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/Makefile", "check:\n")
            tree.write("factory/templates/tools/factory/gates.py", "G = 1\n")
            tree.write("factory/manifest.json", "{}")  # not payload: excluded
            files = gates.manifest_files(tree.root)
            self.assertEqual(
                sorted(files),
                ["templates/Makefile", "templates/tools/factory/gates.py"])
            self.assertEqual(
                files["templates/Makefile"],
                hashlib.sha256(b"check:\n").hexdigest())
            self.assertNotIn("\\", "".join(files))

    def test_no_payload_dir_is_an_empty_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(gates.manifest_files(Path(tmp)), {})

    def test_bytecode_caches_are_not_payload(self):
        """Importing a payload tool from inside the mirrored tree drops a
        __pycache__/ there, and .gitignore keeps it untracked. Hashing it
        pins a key into factory/manifest.json that git never carries, so
        detector E passes for whoever generated the manifest and fails in
        every other checkout — a gate that goes red on a clean tree."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/tools/factory/gates.py", "G = 1\n")
            tree.write("factory/templates/tools/factory/__pycache__/"
                       "gates.cpython-313.pyc", "\x00")
            self.assertEqual(sorted(gates.manifest_files(tree.root)),
                             ["templates/tools/factory/gates.py"])


class TestLabelWiring(unittest.TestCase):
    """Detector J. The tools and the Makefile between them name labels
    the taxonomy must carry, and `.github/labels.json` is explicitly the
    stamped repo's to curate (docs/setup.md), so pruning one is a
    sanctioned edit that used to pass every offline gate and fail only
    when CI flipped the label. Curated also means unpinned — detector E
    checksums the payload copy, nothing checksums the installed one — so
    J is the only offline reader of that file, and what it declines to
    say about it nobody says."""

    REPO = Path(__file__).resolve().parents[1]
    MAKEFILE = ("wo-merged:\n\tpython3 validator.py lifecycle"
                " --label wo:merged\n")

    def taxonomy(self, names):
        return json.dumps([{"name": name, "color": "ededed",
                            "description": name} for name in names])

    def wired_tree(self, tmp, makefile=None):
        """(tree, every label it names) — the correctly curated state."""
        tree = FixtureTree(tmp)
        tree.write("Makefile", self.MAKEFILE if makefile is None else makefile)
        named = sorted(gates.declared_labels(tree.root))
        tree.write(".github/labels.json", self.taxonomy(named))
        return tree, named

    def test_a_taxonomy_carrying_every_named_label_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree, _ = self.wired_tree(tmp)
            self.assertEqual(gates.check_label_wiring(tree.root), [])

    def test_a_pruned_label_is_reported_against_every_site_that_names_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree, named = self.wired_tree(tmp)
            tree.write(".github/labels.json", self.taxonomy(
                [name for name in named if name != "wo:merged"]))
            # wo:merged is named twice over — the Makefile target that
            # flips it and the human_gates entry that counts it — and both
            # sites are reported, because both break
            self.assertEqual(gates.check_label_wiring(tree.root), [
                "J: Makefile:2 names wo:merged but the taxonomy has no such"
                " label (add it to .github/labels.json, or the flip fails"
                " when CI runs it)",
                "J: human_gates.py names wo:merged but the taxonomy has no"
                " such label (add it to .github/labels.json, or the flip"
                " fails when CI runs it)"])

    def test_a_pruned_tool_label_is_reported_without_any_makefile(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree, named = self.wired_tree(tmp, makefile="check:\n\ttrue\n")
            tree.write(".github/labels.json", self.taxonomy(
                [name for name in named if name != "wo:ready-for-agent"]))
            self.assertEqual(gates.check_label_wiring(tree.root), [
                "J: assembler.py names wo:ready-for-agent but the taxonomy"
                " has no such label (add it to .github/labels.json, or the"
                " flip fails when CI runs it)"])

    def test_an_unnamed_taxonomy_label_is_not_a_finding(self):
        # one direction only: wo:blocked is human-applied by design
        # (ADR-0045) and the approval labels are the gates' to set, so
        # "no writer" is never drift
        with tempfile.TemporaryDirectory() as tmp:
            tree, named = self.wired_tree(tmp)
            tree.write(".github/labels.json",
                       self.taxonomy(named + ["area:nobody-writes-this"]))
            self.assertEqual(gates.check_label_wiring(tree.root), [])

    def test_a_tree_with_no_taxonomy_is_silent(self):
        # an unstamped repo has nothing to be wrong about
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("Makefile", self.MAKEFILE)
            self.assertEqual(gates.check_label_wiring(tree.root), [])

    def test_an_unreadable_taxonomy_is_reported_not_a_traceback(self):
        """Two properties, and they used to be asserted as one.

        "Not a traceback" is the requirement — a detector that raises on
        a malformed file takes the whole gate down with it. "Silent" is
        not, and bundling them meant a stamped repo could carry a
        taxonomy nothing can read and be told `gates: 0 problem(s)`.
        The loader already names every one of these; J forwards what it
        says instead of computing it and dropping it."""
        try:
            json.loads("{not json")
        except json.JSONDecodeError as err:
            corrupt = f"L: .github/labels.json is not valid JSON: {err}"
        unusable = {
            "{not json": corrupt,
            "[]": "L: .github/labels.json must be a non-empty JSON array"
                  " of label entries",
            "{}": "L: .github/labels.json must be a non-empty JSON array"
                  " of label entries",
            '[{"name": "wo:merged"}]':
                "L: .github/labels.json[0] entry lacks color, description",
        }
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("Makefile", self.MAKEFILE)
            for payload, expected in unusable.items():
                tree.write(".github/labels.json", payload)
                self.assertEqual(gates.check_label_wiring(tree.root),
                                 [expected], f"unusable taxonomy {payload!r}")

    def test_a_wiring_complete_taxonomy_can_still_be_malformed(self):
        """The case with no wiring finding at all to lean on.

        Every label the tools name is present, so J's own check is
        genuinely satisfied — and the file still says one label twice,
        which GitHub will resolve by taking the last one. Before this,
        nothing offline had any objection to it."""
        with tempfile.TemporaryDirectory() as tmp:
            tree, named = self.wired_tree(tmp)
            entries = json.loads(self.taxonomy(named))
            tree.write(".github/labels.json",
                       json.dumps(entries + [dict(entries[0])]))
            self.assertEqual(
                gates.check_label_wiring(tree.root),
                [f"L: .github/labels.json[{len(entries)}] duplicate label"
                 f" name {entries[0]['name']}"])

    def test_one_malformed_entry_does_not_switch_the_detector_off(self):
        # bailing on any load problem would let a single bad entry silence
        # J entirely — the very failure mode it exists to close
        with tempfile.TemporaryDirectory() as tmp:
            tree, named = self.wired_tree(tmp)
            entries = json.loads(self.taxonomy(
                [name for name in named if name != "wo:merged"]))
            tree.write(".github/labels.json",
                       json.dumps(entries + [{"name": "wo:half-declared"}]))
            found = gates.check_label_wiring(tree.root)
            self.assertIn("J: Makefile:2 names wo:merged but the taxonomy has"
                          " no such label (add it to .github/labels.json, or"
                          " the flip fails when CI runs it)", found)
            # and the bad entry itself is named, not merely survived: an
            # operator told only "add wo:merged" would go looking for a
            # label that is already there
            self.assertIn(f"L: .github/labels.json[{len(entries)}] entry"
                          " lacks color, description", found)

    def test_the_extraction_actually_finds_the_shipped_labels(self):
        """A detector whose extraction silently stops matching is
        vacuously clean forever — worse than no detector. This pins that
        every declarer still yields what it is there for."""
        named = gates.declared_labels(self.REPO)

        def declared_by(site):
            return sorted(label for label, sites in named.items()
                          if site in sites)

        self.assertEqual(declared_by("assembler.py"),
                         ["budget-exhausted", "type:chore", "type:defect",
                          "type:feature", "type:support",
                          "wo:ready-for-agent"])
        # five distinct, not six: wo:prd-approved is the PRD gate's
        # confirming label and the blueprint gate's waiting one
        self.assertEqual(declared_by("human_gates.py"),
                         ["wo:blueprint-approved", "wo:draft", "wo:merged",
                          "wo:needs-review", "wo:prd-approved"])
        # every lifecycle target's --label argument, read off the Makefile
        for label in ("wo:merged", "wo:in-progress", "wo:needs-review",
                      "wo:failed"):
            self.assertTrue(
                any(site.startswith("Makefile") for site in
                    named.get(label, [])), f"{label} not read off Makefile")

    def test_the_shipped_taxonomy_wires_the_shipped_tools(self):
        """The live pin, and the one that would have caught the gap."""
        self.assertEqual(gates.check_label_wiring(self.REPO), [])

    def test_bytes_that_are_not_utf8_are_one_problem_not_a_crash(self):
        """RFC 8259 §8.1 makes JSON a UTF-8 interchange format, so bytes
        that will not decode are exactly as invalid as `not json` and
        belong in the same problem. Detector F reads the same stamped
        `.github/factory.json` a downstream owner hand-edits, so it must
        report what factory_config.load reports rather than abort the
        whole gate run and take the other eight detectors with it."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json", "").write_bytes(
                '{"routing": {"mechanical": "caf\u00e9"}}'.encode("latin-1"))
            problems = gates.check_config_shape(tree.root)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                "F: factory/templates/factory.json is not valid JSON:"),
                problems)


class TestConfigShape(unittest.TestCase):
    def test_the_shipped_config_is_silent(self):
        # the config we actually ship, not a synthetic twin — the valid
        # case doubles as the pin that factory.json stays F-clean
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json", json.dumps(CONFIG))
            self.assertEqual(gates.check_config_shape(tree.root), [])

    def test_bool_fields_are_flagged(self):
        """True is an int, so a plain isinstance check waves bools
        through — while the runtime accessors reject them and hard-stop
        every dispatch. The gate must be at least as strict."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json", json.dumps(
                dict(CONFIG, budgets_usd={"S": True, "M": 15, "L": 40},
                     wip_cap=True, monthly_cap_usd=True)))
            rel = "factory/templates/factory.json"
            self.assertEqual(gates.check_config_shape(tree.root), [
                f"F: {rel} budgets_usd.S must be a positive number",
                f"F: {rel} wip_cap must be a positive integer",
                f"F: {rel} monthly_cap_usd must be a positive number"])

    def test_invalid_fields_are_each_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json", json.dumps(
                {"budgets_usd": {"S": 5}, "routing": {"mechanical": "m"},
                 "wip_cap": 0, "monthly_cap_usd": -1}))
            rel = "factory/templates/factory.json"
            self.assertEqual(gates.check_config_shape(tree.root), [
                f"F: {rel} budgets_usd must map exactly S, M, L",
                f"F: {rel} routing must map exactly mechanical,"
                " implementation, architecture_review",
                f"F: {rel} wip_cap must be a positive integer",
                f"F: {rel} monthly_cap_usd must be a positive number"])

    def test_a_config_that_is_not_an_object_is_one_problem(self):
        """F parses the file itself rather than going through
        factory_config.load, so it needs the same object rule the seam
        applies — and it needs it BEFORE its key-set checks, which
        subscript the parsed value. A non-object used to kill the whole
        gate with an AttributeError: `python3 gates.py` is a CI command,
        and in a stamped repo `.github/factory.json` is the repo's own
        curated file, so the gate that exists to police the config's
        shape was the thing a malformed config took down."""
        for text in ("null", "[]", '"factory"', "5", "true"):
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                tree = FixtureTree(tmp)
                tree.write("factory/templates/factory.json", text)
                self.assertEqual(gates.check_config_shape(tree.root), [
                    "F: factory/templates/factory.json is not a JSON"
                    " object"])

    def test_a_non_object_home_does_not_mask_the_other_home(self):
        """F checks every candidate home, not the first hit. A broken
        payload copy must not stop the installed copy being reported —
        the skip is per-file, the same shape as the invalid-JSON
        continue beside it."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json", "null")
            tree.write(".github/factory.json", json.dumps(
                dict(CONFIG, wip_cap=0)))
            self.assertEqual(gates.check_config_shape(tree.root), [
                "F: factory/templates/factory.json is not a JSON object",
                "F: .github/factory.json wip_cap must be a positive"
                " integer"])


class TestPrTraceability(unittest.TestCase):
    def event_env(self, tmp, event):
        path = Path(tmp) / "event.json"
        path.write_text(json.dumps(event), encoding="utf-8")
        return {"GITHUB_EVENT_PATH": str(path)}

    def pr_env(self, tmp, title, body):
        return self.event_env(tmp, {"pull_request":
                                    {"title": title, "body": body}})

    def test_no_event_path_skips_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env={}), [])

    def test_non_pr_event_skips_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.event_env(tmp, {"ref": "refs/heads/main"})
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env), [])

    def test_uncited_body_fires_both_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "fix: something", "no tokens here")
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env), [
                    "B: PR body cites no work-order id",
                    "B: PR body has no Closes #N link"])

    def test_null_body_fires_both_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "fix: something", None)
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env), [
                    "B: PR body cites no work-order id",
                    "B: PR body has no Closes #N link"])

    def test_well_formed_body_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "WO-0003: detector B",
                              "WO-0003 (PRD-0001 §X) — Closes #108")
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env), [])

    def test_every_github_closing_keyword_is_accepted(self):
        forms = ("close #7", "closes #7", "closed #7", "Closes: #7",
                 "fix #7", "fixes #7", "fixed #7", "Fixes: #7",
                 "resolve #7", "resolves #7", "resolved #7", "Resolves: #7",
                 "CLOSES  #7")
        with tempfile.TemporaryDirectory() as tmp:
            for form in forms:
                env = self.pr_env(tmp, "WO-0003: detector B",
                                  f"WO-0003 per breakdown; {form}")
                self.assertEqual(
                    gates.check_pr_traceability(Path(tmp), env=env), [],
                    f"{form!r} should be accepted as a closing keyword")

    def test_non_closing_keyword_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for form in ("see #7", "closes issue 7", "refs #7"):
                env = self.pr_env(tmp, "WO-0003: detector B",
                                  f"WO-0003 per breakdown; {form}")
                self.assertEqual(
                    gates.check_pr_traceability(Path(tmp), env=env),
                    ["B: PR body has no Closes #N link"],
                    f"{form!r} is not a closing keyword link")

    def test_governance_pr_declaring_no_work_order_is_exempt(self):
        """A governance/chore PR implements no work order (e.g. #139's
        merge-auth fix). It declares that explicitly and is exempt from the
        WO-id requirement — but must still close an issue for the audit trail."""
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "docs: governance",
                              "No work order: docs-only governance fix."
                              " Closes #139")
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env), [])

    def test_no_work_order_declaration_still_requires_a_closes_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "docs: governance",
                              "No work order: docs-only governance fix.")
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env),
                ["B: PR body has no Closes #N link"])

    def test_empty_no_work_order_declaration_does_not_exempt(self):
        """The declaration owes a reason, like every other explicit claim in
        this codebase — a bare 'No work order:' does not waive traceability."""
        with tempfile.TemporaryDirectory() as tmp:
            env = self.pr_env(tmp, "docs: x", "No work order:\nCloses #7")
            self.assertEqual(
                gates.check_pr_traceability(Path(tmp), env=env),
                ["B: PR body cites no work-order id"])

    def test_unreadable_event_file_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "nope" / "event.json")
            problems = gates.check_pr_traceability(
                Path(tmp), env={"GITHUB_EVENT_PATH": missing})
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                f"B: cannot read GITHUB_EVENT_PATH {missing}:"), problems)

    def test_malformed_event_file_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text("{not json", encoding="utf-8")
            problems = gates.check_pr_traceability(
                Path(tmp), env={"GITHUB_EVENT_PATH": str(path)})
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                f"B: cannot read GITHUB_EVENT_PATH {path}:"), problems)

    def test_non_object_event_payload_is_a_problem_not_a_skip(self):
        """A JSON array where the event object should be is a broken event
        file, not a non-PR run — cli.read_event reports it (ADR-0042).
        Before the seam this skipped silently."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "event.json"
            path.write_text("[1, 2]", encoding="utf-8")
            self.assertEqual(
                gates.check_pr_traceability(
                    Path(tmp), env={"GITHUB_EVENT_PATH": str(path)}),
                [f"B: GITHUB_EVENT_PATH {path} is not a JSON object"])

class TestEvidenceHonesty(unittest.TestCase):
    """H (origin: WO-0011): a criterion that asserts a LABELLED verdict must
    show literal output or disclose that the check was NOT RUN.

    Only a labelled verdict line (`Result:` / `Verdict:` / `Outcome:` /
    `Status:`) creates the obligation. Unlabelled prose and heading text
    assert nothing the detector recognises — a summary may narrate, an
    author may write "Done." — so there is no roll-up excuse to purchase.

    The grammar is pure text — gates.evidence_problems over
    gates.verification_sections — so its rules are asserted here on TEXT:
    (lineno, suffix) pairs, no fixture tree, line numbers countable in the
    test's own literal. A handful of filesystem tests pin the detector
    wrapper's own job: artifact discovery, the "H: {rel}:{lineno}" prefix,
    frontmatter skipped in situ, and an unreadable artifact reported
    rather than raised.
    """

    HEAD = "---\nstage: verify\nrun: feature:demo\n---\n\n# Verification\n\n"
    REL = "docs/features/demo/verification.md"
    BACKSTOP = ("verification artifact shows neither literal evidence nor a"
                " NOT-RUN disclaimer (evidence must be a fenced code block)")

    def verification(self, tmp, body):
        tree = FixtureTree(tmp)
        tree.write("docs/features/demo/verification.md", self.HEAD + body)
        return tree

    def claim(self, title, verdict):
        """The suffix evidence_problems emits for an unevidenced claim."""
        return (f'criterion "{title}" asserts {verdict} with neither literal'
                " evidence nor a NOT-RUN disclaimer (evidence must be a"
                " fenced code block in this section)")

    # ---- the rule, in both directions ---------------------------------

    def test_criterion_with_literal_output_is_silent(self):
        self.assertEqual(gates.evidence_problems(
            "## Criteria & evidence\n\n"
            "### Suite is green\n\n"
            "- Check: `python3 -m unittest discover tests`\n"
            "- Evidence:\n"
            "  ```\n"
            "  Ran 212 tests in 4.0s\n\n"
            "  OK\n"
            "  ```\n"
            "- Result: PASS\n"), [])

    def test_criterion_with_not_run_disclaimer_is_silent(self):
        self.assertEqual(gates.evidence_problems(
            "### Non-owner dispatch does not fire\n\n"
            "- Check: NOT RUN — needs a second GitHub account.\n"
            "- Result: NOT VERIFIED\n"), [])

    def test_asserted_but_unevidenced_criterion_is_flagged(self):
        """Filesystem: pins the detector wrapper's output — the H: label and
        the rel:lineno prefix around the grammar's suffix (HEAD is 7 lines,
        so the body's line 4 lands on line 11)."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Suite is green\n\n"
                "- Check: ran the tests, everything looks correct.\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                f"H: {self.REL}:11 " + self.claim("Suite is green", "PASS")])

    def test_relabelled_verdict_lines_still_engage_the_rule(self):
        """`Verdict:` / `Outcome:` / `Status:` assert exactly what `Result:`
        asserts; renaming the label must not buy the criterion out."""
        for label in ("Verdict", "Outcome", "Status", "result"):
            with self.subTest(label=label):
                self.assertEqual(gates.evidence_problems(
                    "### Dispatch fires\n\n"
                    "- Check: eyeballed the run.\n"
                    f"- {label}: PASS\n"),
                    [(4, self.claim("Dispatch fires", "PASS"))])

    def test_evidence_does_not_leak_across_criteria(self):
        self.assertEqual(gates.evidence_problems(
            "### Evidenced\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  OK\n"
            "  ```\n"
            "- Result: PASS\n\n"
            "### Bare\n\n"
            "- Result: PASS\n"),
            [(11, self.claim("Bare", "PASS"))])

    def test_appendix_fence_does_not_vouch_for_other_criteria(self):
        """Evidence is section-scoped: a throwaway fence in an appendix
        vouches for nothing three headings away."""
        self.assertEqual(gates.evidence_problems(
            "### Dispatch fires\n\n"
            "- Result: PASS\n\n"
            "### Budget guard holds\n\n"
            "- Verdict: PASS\n\n"
            "## Appendix: branch log\n\n"
            "```\n"
            "git log --oneline -3\n"
            "```\n"),
            [(3, self.claim("Dispatch fires", "PASS")),
             (7, self.claim("Budget guard holds", "PASS"))])

    def test_scoped_hedge_is_not_a_not_run_disclaimer(self):
        """"not tested on Windows" concedes the check DID run. A scoped
        hedge is partial coverage, not a disclosure."""
        self.assertEqual(gates.evidence_problems(
            "### Suite is green\n\n"
            "- Check: ran the suite.\n"
            "- Result: PASS\n"
            "- Caveat: not tested on Windows.\n"),
            [(4, self.claim("Suite is green", "PASS"))])

    def test_body_not_run_note_does_not_excuse_an_asserted_claim(self):
        """A section that CLAIMS PASS and mentions in passing that something
        else was not run has disclosed nothing about the PASS. While any
        unqualified "not run" in the body disarmed the section, "(the retry
        path was not run)" was a two-word licence to fabricate any verdict —
        a bypass that survived attempts 1 and 2. The disclosure has to BE the
        verdict, not sit next to it."""
        self.assertEqual(gates.evidence_problems(
            "### Suite is green\n\n"
            "- Check: ran it.\n"
            "- Result: PASS\n"
            "- Note: the browser matrix was not run.\n"),
            [(4, self.claim("Suite is green", "PASS"))])

    def test_a_verdict_that_makes_no_claim_needs_no_evidence(self):
        """The other side of that line: a verdict which claims nothing —
        NOT VERIFIED, SKIPPED, N/A — IS the disclosure, and owes no output."""
        for verdict in ("NOT VERIFIED", "NOT RUN", "SKIPPED", "N/A"):
            with self.subTest(verdict=verdict):
                self.assertEqual(gates.evidence_problems(
                    "### Cap breach pauses the factory\n\n"
                    "- Check: needs a month of real cost data.\n"
                    f"- Result: {verdict}\n"), [])

    def test_a_claim_beside_a_disclosure_still_owes_evidence(self):
        """Declaring one criterion NOT RUN does not buy the section's other,
        affirmative verdict out of showing its output."""
        self.assertEqual(gates.evidence_problems(
            "### Cap breach\n\n"
            "- Result: NOT VERIFIED\n"
            "- Verdict: PASS\n"),
            [(4, self.claim("Cap breach", "PASS"))])

    def test_empty_and_placeholder_fences_are_not_evidence(self):
        self.assertEqual(gates.evidence_problems(
            "### Empty fence\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  ```\n"
            "- Result: PASS\n\n"
            "### Unfilled template\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  <actual output — quoted, not summarized>\n"
            "  ```\n"
            "- Result: PASS | FAIL\n"),
            [(6, self.claim("Empty fence", "PASS")),
             (14, self.claim("Unfilled template", "PASS | FAIL"))])

    # ---- bypasses that attempts 1 and 2 left open ----------------------

    def test_fabricated_template_shaped_artifact_is_flagged(self):
        """BYPASS 1. The verify TEMPLATE ships a `## Not verified` heading in
        every artifact. When heading text counted as a NOT-RUN disclosure it
        manufactured an artifact-wide excuse, so a 100%-fabricated,
        template-shaped artifact with ZERO command output passed silently.
        A disclosure is what the author WRITES, never the slot label."""
        self.assertEqual(gates.evidence_problems(
            "## Summary\n\n"
            "6/6 criteria pass. Verdict: ship it.\n\n"
            "## Criteria & evidence\n\n"
            "### Test suite\n\n"
            "- Check: ran the full suite; everything passed comfortably.\n\n"
            "### Dispatch\n\n"
            "- Check: watched the workflow run to completion.\n\n"
            "## Failures\n\n"
            "None.\n\n"
            "## Not verified\n\n"
            "Nothing; everything was checked.\n"),
            [(1, self.BACKSTOP)])

    def test_renaming_the_lying_section_does_not_excuse_it(self):
        """BYPASS 2. The roll-up excuse was keyed on heading NAME, so calling
        the gaming section Summary/Results/Conclusion/Overview/Verdict bought
        it out. There is no roll-up excuse any more: a labelled verdict owes
        evidence wherever it is written."""
        for name in ("Summary", "Results", "Conclusion", "Overview",
                     "Verdict"):
            with self.subTest(name=name):
                self.assertEqual(gates.evidence_problems(
                    f"## {name}\n\n"
                    "- Result: 6/6 criteria PASS\n"
                    "- Verdict: ship it\n\n"
                    "## Not verified\n\n"
                    "Nothing; everything was checked.\n"),
                    [(3, self.claim(name, "6/6 criteria PASS"))])

    def test_one_honest_leaf_does_not_launder_a_lying_rollup(self):
        """BYPASS 3. The excuse asked only whether the artifact's leaves were
        evidenced — never whether the roll-up narrated THOSE criteria — so a
        single throwaway leaf (a fence holding one dot) laundered a roll-up
        making every real claim."""
        self.assertEqual(gates.evidence_problems(
            "### Grammar parses\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  .\n"
            "  ```\n"
            "- Result: PASS\n\n"
            "## Results\n\n"
            "- Result: all 6 PRD criteria PASS\n"
            "- Verdict: ship it\n"),
            [(11, self.claim("Results", "all 6 PRD criteria PASS"))])

    def test_a_hedge_appended_to_a_claim_does_not_disarm_it(self):
        """BYPASS 5. Reading the NOT-RUN token as a SUBSTRING of the verdict
        let a claim buy itself out by appending a hedge: "PASS ... (soak test
        not run)" asserted PASS and showed nothing, in silence. A verdict is
        a disclosure only when the WHOLE value is one."""
        self.assertEqual(gates.evidence_problems(
            "## Criterion 1 - payment capture\n\n"
            "- Result: PASS - every acceptance criterion met, full suite"
            " green (soak test not run).\n"),
            [(3, self.claim(
                "Criterion 1 - payment capture",
                "PASS - every acceptance criterion met, full suite green"
                " (soak test not run)."))])

    def test_a_disclosure_may_give_its_reason(self):
        """The other side of anchoring it: an honest disclosure names why the
        check did not run, and that reason must not turn it into a claim."""
        for verdict in ("NOT RUN — the CI runner was offline",
                        "NOT VERIFIED (needs a second GitHub account)",
                        "N/A — no payment provider in this environment",
                        "SKIPPED: covered by the nightly soak",
                        "**NOT RUN**"):
            with self.subTest(verdict=verdict):
                self.assertEqual(gates.evidence_problems(
                    "### Soak test\n\n"
                    f"- Result: {verdict}\n"), [])

    def test_verdict_labels_beyond_the_original_four_engage_the_rule(self):
        """BYPASS 6. The label whitelist (Result/Verdict/Outcome/Status) was
        itself the escape hatch: a lying section headed `Conclusion:` was
        invisible. Every verdict noun asserts."""
        for label in ("Conclusion", "Assessment", "Finding", "Determination",
                      "Evaluation", "Judgement", "Judgment", "Disposition",
                      "Decision", "Ruling", "Appraisal"):
            with self.subTest(label=label):
                self.assertEqual(gates.evidence_problems(
                    "### Payments capture\n\n"
                    "- Check: eyeballed the dashboard.\n"
                    f"- {label}: PASS\n"),
                    [(4, self.claim("Payments capture", "PASS"))])

    def test_one_honest_fence_does_not_launder_relabelled_lies(self):
        """BYPASS 6, as reported: one real fence (lint) satisfied the
        artifact-wide backstop, and the two fabricated criteria beside it used
        labels outside the whitelist, so the whole artifact passed silently.
        Each lying section now owes evidence in its own right."""
        self.assertEqual(gates.evidence_problems(
            "## Criterion 0 - lint\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  lint: 0 problem(s)\n"
            "  ```\n\n"
            "## Criterion 1 - payments\n\n"
            "- Conclusion: PASS. All 12 criteria met, full suite green.\n\n"
            "## Criterion 2 - retries\n\n"
            "- Assessment: works correctly under load. Ship it.\n"),
            [(10, self.claim("Criterion 1 - payments",
                             "PASS. All 12 criteria met, full suite green.")),
             (14, self.claim("Criterion 2 - retries",
                             "works correctly under load. Ship it."))])

    def test_frontmatter_fields_are_not_verdicts(self):
        """BYPASS 6, sibling finding. YAML frontmatter is metadata, not the
        author's assertion: `status: draft` was read as a labelled verdict
        claiming "draft" in an untitled section — a false positive on an
        honest artifact, and (worse) a `results` entry that disarmed the
        artifact-wide backstop."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/verification.md", (
                "---\nstage: verify\nstatus: draft\nrun: feature:demo\n---\n\n"
                "# Verification\n\n"
                "### Suite is green\n\n"
                "- Evidence:\n"
                "  ```\n"
                "  OK\n"
                "  ```\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    def test_frontmatter_status_does_not_buy_off_the_backstop(self):
        """The same bug from the other side: a prose-only artifact whose
        frontmatter carries `status:` had a `results` entry, so the
        artifact-wide backstop never ran and the artifact passed with zero
        evidence."""
        self.assertEqual(gates.evidence_problems(
            "---\nstage: verify\nstatus: done\nrun: feature:demo\n---\n\n"
            "# Verification\n\n"
            "## Summary\n\n"
            "Everything works; all criteria are comfortably met.\n"),
            [(1, self.BACKSTOP)])

    # ---- the fence scanner (CommonMark, not a parity toggle) -----------

    def test_longer_fence_quoting_a_shorter_one_stays_one_block(self):
        """BYPASS 4a. A ```` fence quoting a ``` fence: the shorter marker is
        content, not a delimiter. The parity toggle flipped on it and lost
        the evidence, false-positiving on an author who DID paste output."""
        self.assertEqual(gates.evidence_problems(
            "### Skill doc renders\n\n"
            "- Evidence:\n"
            "  ````\n"
            "  ```bash\n"
            "  make check\n"
            "  ```\n"
            "  ````\n"
            "- Result: PASS\n\n"
            "### Router picks the model\n\n"
            "- Result: PASS\n"),
            [(13, self.claim("Router picks the model", "PASS"))])

    def test_backtick_fence_inside_a_tilde_block_does_not_close_it(self):
        """BYPASS 4b. A ``` line inside a ~~~ block is content — a closing
        fence must use the SAME marker. The parity toggle desynced on it and
        silently swallowed every later criterion."""
        self.assertEqual(gates.evidence_problems(
            "### Evidence quotes a snippet\n\n"
            "- Evidence:\n"
            "  ~~~\n"
            "  The README starts with:\n"
            "  ```bash\n"
            "  make check\n"
            "  ~~~\n"
            "- Result: PASS\n\n"
            "### Bare claim\n\n"
            "- Result: PASS\n"),
            [(13, self.claim("Bare claim", "PASS"))])

    def test_info_string_line_does_not_close_a_fence(self):
        """A closing fence carries NO info string, so ```bash inside a ```
        block is content (CommonMark)."""
        self.assertEqual(gates.evidence_problems(
            "### Docs quote a shell block\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  ```bash\n"
            "  make check\n"
            "  ```\n"
            "- Result: PASS\n\n"
            "### Bare claim\n\n"
            "- Result: PASS\n"),
            [(12, self.claim("Bare claim", "PASS"))])

    def test_unclosed_fence_is_flagged(self):
        """BYPASS 4c. An unclosed fence absorbed the tail of the artifact in
        silence. It must be a problem, not a swallow."""
        self.assertEqual(gates.evidence_problems(
            "### Suite is green\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  Ran 212 tests\n\n"
            "  OK\n"
            "- Result: PASS\n"),
            [(4, "unclosed code fence — every criterion after it is"
                 " unread")])

    def test_headings_inside_a_fence_do_not_split_the_criterion(self):
        text = ("### Report renders\n\n"
                "- Evidence:\n"
                "  ```\n"
                "  ### Weekly report\n"
                "  3 work orders merged\n"
                "  ```\n"
                "- Result: PASS\n")
        sections, unclosed = gates.verification_sections(text)
        self.assertIsNone(unclosed)
        self.assertEqual([s["title"] for s in sections],
                         ["(untitled)", "Report renders"])
        self.assertTrue(sections[1]["evidence"])
        self.assertEqual(sections[1]["results"], [(8, "PASS")])
        self.assertEqual(gates.evidence_problems(text), [])

    # The bypass in #147: the splitter was ATX-only, so a Setext-headed
    # artifact collapsed into one section and a single honest fence
    # disarmed every lying verdict in it. GitHub renders the two
    # identically, so the artifact a reviewer reads looks the same.
    SETEXT_BODY = (
        "Criterion 0 - lint\n------------------\n"
        "- Evidence:\n  ```\n  lint: 0 problem(s)\n  ```\n\n"
        "Criterion 1 - payments\n----------------------\n"
        "- Result: PASS. All 12 acceptance criteria met.\n\n"
        "Criterion 2 - soak\n------------------\n"
        "- Verdict: PASS. 72h soak clean.\n")

    ATX_BODY = (
        "## Criterion 0 - lint\n"
        "- Evidence:\n  ```\n  lint: 0 problem(s)\n  ```\n\n"
        "## Criterion 1 - payments\n"
        "- Result: PASS. All 12 acceptance criteria met.\n\n"
        "## Criterion 2 - soak\n"
        "- Verdict: PASS. 72h soak clean.\n")

    def test_setext_headings_split_sections_like_atx(self):
        """The bypass: one honest fence under criterion 0 silenced criteria 1
        and 2 because the Setext-headed artifact never split into sections.
        The two syntaxes render identically on GitHub, so they must gate
        identically — same criteria named, same verdicts caught."""
        problems = gates.evidence_problems(self.SETEXT_BODY)
        control = gates.evidence_problems(self.ATX_BODY)

        named = lambda ps: sorted(s.split("criterion ")[1] for _, s in ps)
        self.assertEqual(len(problems), 2)  # criterion 0 is honestly evidenced
        self.assertEqual(named(problems), named(control))
        self.assertEqual(named(problems), sorted([
            '"Criterion 1 - payments" asserts PASS. All 12 acceptance criteria'
            ' met. with neither literal evidence nor a NOT-RUN disclaimer'
            ' (evidence must be a fenced code block in this section)',
            '"Criterion 2 - soak" asserts PASS. 72h soak clean. with neither'
            ' literal evidence nor a NOT-RUN disclaimer'
            ' (evidence must be a fenced code block in this section)']))

    def test_setext_underline_is_not_confused_with_frontmatter_or_rule(self):
        """`---` opens the frontmatter fence and also writes a thematic break.
        Neither is a heading; only an underline under a non-blank line is."""
        self.assertEqual(gates.evidence_problems(
            "---\nstage: verify\n---\n\n"
            "## Criterion\n\n"
            "---\n\n"
            "- Evidence:\n  ```\n  ok\n  ```\n"
            "- Result: PASS\n"), [])

    # Independent-review finding on this branch: RESULT_LINE tolerated only a
    # leading unordered bullet, so a verdict written under any other leading
    # CommonMark construct GitHub still renders as visible text — a blockquote
    # or an ordered-list item — slipped past the splitter. Beside one honestly
    # evidenced criterion (so the artifact-wide backstop stays quiet), the
    # smuggled fake PASS produced no problem at all.
    EVIDENCED_NEIGHBOUR = (
        "## Criterion A - login\n"
        "- Evidence:\n  ```\n  1 passed\n  ```\n"
        "- Result: PASS\n\n")

    def test_blockquoted_verdict_still_asserts(self):
        self.assertEqual(
            gates.evidence_problems(self.EVIDENCED_NEIGHBOUR + (
                "## Criterion B - payments\n"
                "> Result: PASS\n")),
            [(9, self.claim("Criterion B - payments", "PASS"))])

    def test_ordered_list_verdict_still_asserts(self):
        self.assertEqual(
            gates.evidence_problems(self.EVIDENCED_NEIGHBOUR + (
                "## Criterion B - payments\n"
                "1. Result: PASS\n")),
            [(9, self.claim("Criterion B - payments", "PASS"))])

    def test_blockquoted_not_run_still_discloses(self):
        """The fix widens the marker class, not the claim test: a blockquoted
        NOT-RUN disclaimer is still a disclosure, owing no output."""
        self.assertEqual(gates.evidence_problems(
            "## Criterion B - payments\n"
            "> Result: NOT RUN — no staging card\n"), [])

    # #151: two further wrappers GitHub renders as a visible verdict slipped
    # the splitter after the blockquote/ordered-list fix — a single-row table
    # cell (`| Result: PASS |`, a row a human reads as PASS) and an inline
    # `<summary>` (`<summary>Result: PASS</summary>`, an always-visible
    # clickable verdict). Beside one honestly evidenced criterion (so the
    # artifact-wide backstop stays quiet), the smuggled fake PASS was silent.
    def test_table_cell_verdict_still_asserts(self):
        self.assertEqual(
            gates.evidence_problems(self.EVIDENCED_NEIGHBOUR + (
                "## Criterion B - payments\n"
                "| Result: PASS |\n")),
            [(9, self.claim("Criterion B - payments", "PASS"))])

    def test_summary_tag_verdict_still_asserts(self):
        self.assertEqual(
            gates.evidence_problems(self.EVIDENCED_NEIGHBOUR + (
                "## Criterion B - payments\n"
                "<summary>Result: PASS</summary>\n")),
            [(9, self.claim("Criterion B - payments", "PASS"))])

    def test_table_and_summary_not_run_still_disclose(self):
        """The fix widens the wrapper class, not the claim test: a NOT-RUN
        disclaimer inside a table cell or a `<summary>` is still a disclosure,
        owing no output — the captured value drops the trailing `|` /
        `</summary>` so `_is_disclosure` reads the verdict's true head."""
        for verdict_line in ("| Result: NOT RUN — no staging card |",
                             "<summary>Result: NOT VERIFIED</summary>"):
            with self.subTest(line=verdict_line):
                self.assertEqual(gates.evidence_problems(
                    "## Criterion B - payments\n" + verdict_line + "\n"), [])

    def test_verdict_line_inside_a_fence_is_not_a_criterion(self):
        """Quoted output that happens to contain `Result: PASS` is evidence,
        not an assertion of the author's own."""
        self.assertEqual(gates.evidence_problems(
            "### CI log renders\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  Result: PASS\n"
            "  ```\n"
            "- Result: PASS\n"), [])

    # ---- false positives: a gate that blocks honest work gets disabled --

    def test_angle_bracket_output_is_evidence_not_a_placeholder(self):
        """Shape-matching `<...>` discarded real DOM dumps and Python reprs
        as "placeholders". Only the template's own filler text is filler."""
        self.assertEqual(gates.evidence_problems(
            "### DOM renders the report\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  <html>\n"
            "  <body><h1>Weekly report</h1></body>\n"
            "  </html>\n"
            "  ```\n"
            "- Result: PASS\n\n"
            "### Model repr is stable\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  <class 'app.models.User'>\n"
            "  ```\n"
            "- Result: PASS\n"), [])

    def test_table_of_evidenced_results_stays_silent(self):
        """#151 guard: a table cell verdict is just another wrapper, but a
        section that shows its literal output owes nothing. A table that
        tabulates real evidenced results (a fenced block in the same section)
        must not fire."""
        self.assertEqual(gates.evidence_problems(
            "### Suite is green\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  Ran 212 tests in 4.0s\n\n"
            "  OK\n"
            "  ```\n"
            "| Result: PASS |\n"), [])

    def test_details_folding_real_output_stays_silent(self):
        """#151 guard: `<details><summary>…</summary>` folding a real fenced
        block is honest evidence — the summary verdict is backed by the output
        it hides, so the section stays silent."""
        self.assertEqual(gates.evidence_problems(
            "### Suite is green\n\n"
            "<details>\n"
            "<summary>Result: PASS</summary>\n\n"
            "```\n"
            "Ran 212 tests in 4.0s\n\n"
            "OK\n"
            "```\n\n"
            "</details>\n"), [])

    def test_honest_prose_and_headings_are_not_criteria(self):
        """Unlabelled prose asserts nothing the detector reads: an author may
        open a note with "Done." and title a section "all checks pass"."""
        self.assertEqual(gates.evidence_problems(
            "## Criteria & evidence\n\n"
            "### Suite is green and lint is passing\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  Ran 212 tests in 4.0s\n\n"
            "  OK\n"
            "  ```\n"
            "- Result: PASS\n\n"
            "## Known-good baseline (all checks pass)\n\n"
            "The previous release's numbers, for comparison only.\n\n"
            "## Notes\n\n"
            "Done. The remaining gap is tracked as a backlog seed.\n"
            "Ok, that is everything.\n"), [])

    def test_prose_rollup_over_evidenced_criteria_owes_nothing(self):
        """The template's `## Summary` holds "the one-sentence verdict" as
        PROSE. Prose is not a labelled verdict, so it owes no evidence — the
        excuse that used to protect it (and that gaming sections bought) is
        gone, and nothing is lost."""
        self.assertEqual(gates.evidence_problems(
            "## Summary\n\n"
            "4/4 criteria pass; suite and lint green on the branch.\n"
            "The feature demonstrably works.\n\n"
            "## Criteria & evidence\n\n"
            "### Suite is green\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  Ran 222 tests in 4.1s\n\n"
            "  OK\n"
            "  ```\n"
            "- Result: PASS\n"), [])

    def test_labelled_verdict_in_a_summary_still_owes_evidence(self):
        """The deliberate cost of killing the roll-up excuse: if you write a
        LABELLED verdict, you back it — in that section — wherever you write
        it. Narrate in prose, or show the output."""
        self.assertEqual(gates.evidence_problems(
            "## Summary\n\n"
            "- Verdict: all criteria pass.\n\n"
            "## Criteria & evidence\n\n"
            "### Suite is green\n\n"
            "- Evidence:\n"
            "  ```\n"
            "  OK\n"
            "  ```\n"
            "- Result: PASS\n"),
            [(3, self.claim("Summary", "all criteria pass."))])

    # ---- the artifact-wide backstop ------------------------------------

    def test_prose_only_artifact_is_flagged(self):
        self.assertEqual(gates.evidence_problems(
            "## Summary\n\n"
            "Everything works; all criteria are comfortably met.\n"),
            [(1, self.BACKSTOP)])

    def test_scoped_hedge_does_not_disarm_the_whole_artifact_backstop(self):
        self.assertEqual(gates.evidence_problems(
            "## Summary\n\n"
            "Everything is fine; the criteria are comfortably met.\n"
            "(Not tested on Windows, but that is out of scope.)\n"),
            [(1, self.BACKSTOP)])

    def test_written_not_run_disclosure_satisfies_the_backstop(self):
        """The disclaimer branch of the acceptance criterion: an artifact that
        ran nothing and SAYS so is honest, and stays silent."""
        self.assertEqual(gates.evidence_problems(
            "## Summary\n\n"
            "Nothing could be checked this run.\n\n"
            "## Not verified\n\n"
            "The whole suite was not run — the CI runner was offline.\n"), [])

    def test_unreadable_artifact_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            path = tree.write("docs/features/demo/verification.md", "")
            path.write_bytes(b"\xff\xfe not utf-8 \xff")
            problems = gates.check_evidence_honesty(tree.root)
            self.assertEqual(len(problems), 1)
            self.assertTrue(problems[0].startswith(
                f"H: {self.REL} cannot be read:"), problems)

    def test_tree_without_a_verification_artifact_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/prd.md", "# PRD\n")
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    def test_repo_verification_artifacts_are_honest(self):
        problems = gates.check_evidence_honesty(TestLockstep.REPO)
        self.assertEqual(problems, [])


class TestRunAll(unittest.TestCase):
    def test_run_all_threads_env_to_the_pr_detector(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            event = tree.write("event.json", json.dumps(
                {"pull_request": {"title": "x", "body": "nothing"}}))
            problems = gates.run_all(
                tree.root, env={"GITHUB_EVENT_PATH": str(event)})
            self.assertIn("B: PR body cites no work-order id", problems)

    def test_run_all_with_empty_env_skips_the_pr_detector(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            self.assertEqual(
                [p for p in gates.run_all(tree.root, env={})
                 if p.startswith("B:")], [])


class TestLockstep(unittest.TestCase):
    """Makefile <-> CI lockstep (origin: WO-0003, tightened by WO-0004).

    The old version asserted *membership* — every canonical command appears
    somewhere — so drift by ADDITION was invisible: a step added to CI and
    not to the Makefile passed. These assert exact, ordered equality of the
    command sets, and that the workflow names no command of its own (it goes
    through `make`), which is what lets one workflow file serve both this
    repo and every stamped product repo. The root->product respelling the
    assertions lean on is factory_init.product_form — the production
    transform that generates the payload Makefile (ADR-0050) — never a
    test-private copy of the translation rule."""

    REPO = Path(__file__).resolve().parents[1]
    WORKFLOW = REPO / ".github" / "workflows" / "validator.yml"
    PAYLOAD_WORKFLOW = (REPO / "factory" / "templates" / ".github"
                        / "workflows" / "validator.yml")
    ASSEMBLER_WORKFLOW = REPO / ".github" / "workflows" / "assembler.yml"
    PAYLOAD_ASSEMBLER_WORKFLOW = (REPO / "factory" / "templates" / ".github"
                                  / "workflows" / "assembler.yml")
    MAKEFILE = REPO / "Makefile"
    TEMPLATE_MAKEFILE = REPO / "factory" / "templates" / "Makefile"
    ASSEMBLER_TARGET = ["python3 assembler.py resolve"]
    COST_REPORT_WORKFLOW = (REPO / ".github" / "workflows"
                            / "cost-report.yml")
    PAYLOAD_COST_REPORT_WORKFLOW = (REPO / "factory" / "templates"
                                    / ".github" / "workflows"
                                    / "cost-report.yml")
    COST_REPORT_TARGET = ["python3 cost_report.py report"]
    GATE_DIGEST_WORKFLOW = (REPO / ".github" / "workflows"
                            / "gate-digest.yml")
    PAYLOAD_GATE_DIGEST_WORKFLOW = (REPO / "factory" / "templates"
                                    / ".github" / "workflows"
                                    / "gate-digest.yml")
    GATE_DIGEST_TARGET = ["python3 gate_digest.py daily"]
    TOOLSMITH_MINE_WORKFLOW = (REPO / ".github" / "workflows"
                               / "toolsmith-mine.yml")
    PAYLOAD_TOOLSMITH_MINE_WORKFLOW = (REPO / "factory" / "templates"
                                       / ".github" / "workflows"
                                       / "toolsmith-mine.yml")
    TOOLSMITH_MINE_TARGET = ["python3 rejection_mining.py mine"]
    RECORD_TARGET = ["python3 budget_guard.py record-run $(WO) $(RUN_ID)"
                     " $(MODEL) $(FILE) $(OUTCOME)"]

    # The one canonical check set. `lint.py` is the plugin's structural lint
    # and has no product-repo counterpart, so only the root Makefile runs it.
    CANONICAL_CHECK = ["python3 gates.py",
                       "python3 gates.py --selftest",
                       "python3 -m unittest discover tests"]
    ROOT_ONLY_CHECK = ["python3 lint.py"]
    VALIDATOR_TARGETS = {
        "review": ["python3 validator.py review --findings $(FINDINGS)"
                   " --status $(STATUS)"],
        # Both legs carry --uncited skip (ADR-0057): a PR naming no work
        # order is a no-op on open AND on merge. Without it here, every
        # housekeeping PR merged with a red post-merge run while the open
        # leg passed the same body.
        "wo-merged": ["python3 validator.py lifecycle --label wo:merged"
                      " --uncited skip"],
        "wo-in-progress": ["python3 validator.py lifecycle --label"
                           " wo:in-progress --issue $(ISSUE)"],
        "wo-needs-review": ["python3 validator.py lifecycle --label"
                            " wo:needs-review --uncited skip"],
        "wo-failed": ["python3 validator.py lifecycle --label wo:failed"
                      " --issue $(ISSUE) --verdict skip"],
    }

    def recipes(self, path, target):
        return make_recipe(path.read_text(encoding="utf-8"), target)

    def test_root_makefile_check_is_exactly_the_canonical_set(self):
        self.assertEqual(self.recipes(self.MAKEFILE, "check"),
                         self.ROOT_ONLY_CHECK + self.CANONICAL_CHECK)

    def test_template_makefile_check_is_exactly_the_canonical_set(self):
        self.assertEqual(self.recipes(self.TEMPLATE_MAKEFILE, "check"),
                         [product_form(c) for c in self.CANONICAL_CHECK])

    def test_both_makefiles_expose_the_same_validator_targets(self):
        for target, commands in self.VALIDATOR_TARGETS.items():
            self.assertEqual(self.recipes(self.MAKEFILE, target), commands,
                             f"root Makefile target {target}")
            self.assertEqual(
                self.recipes(self.TEMPLATE_MAKEFILE, target),
                [product_form(c) for c in commands],
                f"template Makefile target {target}")

    def test_the_workflow_names_no_command_of_its_own(self):
        """Every check runs through `make`, so CI cannot drift from the local
        gate by adding a step — there is nowhere to add one."""
        text = self.WORKFLOW.read_text(encoding="utf-8")
        for command in ("make check", "make review", "make wo-merged",
                        "make wo-needs-review"):
            self.assertIn(command, text)
        for tool in ("lint.py", "gates.py", "validator.py", "unittest"):
            self.assertNotIn(
                f"python3 {tool}", text,
                f"{tool} is invoked directly in CI; it belongs in a make"
                " target, or the two repos' CI will diverge")

    def test_the_payload_workflow_is_the_mirror_of_this_repo_s(self):
        """One workflow, two repos: the payload copy is a machine mirror
        (factory_init update-manifest), never a hand-maintained fork."""
        self.assertEqual(self.PAYLOAD_WORKFLOW.read_bytes(),
                         self.WORKFLOW.read_bytes())

    def test_the_merged_label_job_fires_only_on_a_merged_pull_request(self):
        text = self.WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github.event.action == 'closed'", text)
        self.assertIn("github.event.pull_request.merged == true", text)

    def test_the_needs_review_job_fires_only_on_an_opened_same_repo_pr(self):
        # ADR-0033 gate 3's queue entry (ADR-0041's latency rows measure
        # the passage). synchronize is deliberately absent — pushes to an
        # open PR must not re-flip an order a human already moved along.
        text = self.WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("needs-review-label:", text)
        self.assertIn("(github.event.action == 'opened'"
                      " || github.event.action == 'reopened')", text)
        self.assertIn("github.event.pull_request.head.repo.full_name"
                      " == github.repository", text)

    def test_a_body_edit_retriggers_the_check(self):
        # Detector B reads the PR body, so the body is an input to the
        # check and correcting it has to re-run it. Without `edited` the
        # only route is close/reopen, and that dispatches a closed-event
        # run against the pre-edit payload whose failure then sits in the
        # PR's status rollup for good (issue #216).
        text = self.WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("types: [opened, reopened, synchronize, edited,"
                      " closed]", text)

    def test_the_review_job_names_the_actions_it_runs_on(self):
        # An allow-list, not `!= 'closed'`: the reviewer posts a comment
        # per run, so a deny-list would enrol it in every title and body
        # edit the moment `edited` was added — and in any trigger type
        # added later.
        text = self.WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("(github.event.action == 'opened'\n"
                      "           || github.event.action == 'reopened'\n"
                      "           || github.event.action == 'synchronize')",
                      text)
        self.assertNotIn("&& github.event.action != 'closed'\n"
                         "      && github.event.pull_request.head.repo",
                         text)

    def test_the_claim_step_gates_the_agent_step(self):
        # ADR-0032: the claim step flips ready -> in-progress and its
        # transitioned output is the dispatch idempotency verdict — the
        # paid agent step runs only on a true claim (the concurrency
        # group only queues repeat label events, it cannot dedupe them).
        text = self.ASSEMBLER_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("make wo-in-progress", text)
        self.assertIn("steps.claim.outputs.transitioned == 'true'", text)

    def test_a_failed_dispatch_flips_the_order_it_claimed(self):
        # ADR-0045: without this step a dying agent run leaves its order on
        # wo:in-progress forever. Gated on the claim's verdict, not on
        # failure() alone — a run that died before claiming the order must
        # leave its state alone (the order is still someone else's to
        # dispatch).
        text = self.ASSEMBLER_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("make wo-failed", text)
        self.assertIn("failure()", text)
        failed = text.split("make wo-failed")[0].rsplit("- name:", 1)[1]
        self.assertIn("failure()", failed)
        self.assertIn("steps.claim.outputs.transitioned == 'true'", failed)

    def test_both_makefiles_expose_the_wo_record_target(self):
        self.assertEqual(self.recipes(self.MAKEFILE, "wo-record"),
                         self.RECORD_TARGET)
        self.assertEqual(self.recipes(self.TEMPLATE_MAKEFILE, "wo-record"),
                         [product_form(c) for c in self.RECORD_TARGET])

    def test_a_finished_dispatch_records_its_spend(self):
        # Issue #222: the ledger's success-path caller. always() — a
        # failed agent still spent money; gated on the claim's verdict
        # and on the execution file existing (the harness's own spend
        # record, never a hand-typed figure). continue-on-error — a
        # ledger refusal must not flip a finished order to wo:failed;
        # the miss shows red here and detector G reds the merge if the
        # line never lands.
        text = self.ASSEMBLER_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("make wo-record", text)
        record = text.split("make wo-record")[0].rsplit("- name:", 1)[1]
        self.assertIn("always()", record)
        self.assertIn("steps.claim.outputs.transitioned == 'true'", record)
        self.assertIn("steps.agent.outputs.execution_file != ''", record)
        self.assertIn("continue-on-error: true", record)

    def test_both_makefiles_expose_the_assembler_target(self):
        self.assertEqual(self.recipes(self.MAKEFILE, "assembler"),
                         self.ASSEMBLER_TARGET)
        self.assertEqual(self.recipes(self.TEMPLATE_MAKEFILE, "assembler"),
                         [product_form(c) for c in self.ASSEMBLER_TARGET])

    def test_the_assembler_workflow_names_no_command_of_its_own(self):
        text = self.ASSEMBLER_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("make assembler", text)
        for tool in ("gates.py", "validator.py", "assembler.py",
                     "budget_guard.py", "unittest"):
            self.assertNotIn(
                f"python3 {tool}", text,
                f"{tool} is invoked directly in CI; it belongs in a make"
                " target, or the two repos' CI will diverge")

    def test_the_payload_assembler_workflow_is_the_mirror_of_this_repo_s(self):
        self.assertEqual(self.PAYLOAD_ASSEMBLER_WORKFLOW.read_bytes(),
                         self.ASSEMBLER_WORKFLOW.read_bytes())

    def test_both_makefiles_expose_the_cost_report_target(self):
        self.assertEqual(self.recipes(self.MAKEFILE, "cost-report"),
                         self.COST_REPORT_TARGET)
        self.assertEqual(
            self.recipes(self.TEMPLATE_MAKEFILE, "cost-report"),
            [product_form(c) for c in self.COST_REPORT_TARGET])

    def test_the_cost_report_workflow_names_no_command_of_its_own(self):
        text = self.COST_REPORT_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("make cost-report", text)
        for tool in ("cost_report.py", "gates.py", "unittest"):
            self.assertNotIn(
                f"python3 {tool}", text,
                f"{tool} is invoked directly in CI; it belongs in a make"
                " target, or the two repos' CI will diverge")

    def test_the_payload_cost_report_workflow_is_the_mirror_of_this_repo_s(self):
        self.assertEqual(self.PAYLOAD_COST_REPORT_WORKFLOW.read_bytes(),
                         self.COST_REPORT_WORKFLOW.read_bytes())

    def test_both_makefiles_expose_the_gate_digest_target(self):
        self.assertEqual(self.recipes(self.MAKEFILE, "gate-digest"),
                         self.GATE_DIGEST_TARGET)
        self.assertEqual(
            self.recipes(self.TEMPLATE_MAKEFILE, "gate-digest"),
            [product_form(c) for c in self.GATE_DIGEST_TARGET])

    def test_the_gate_digest_workflow_names_no_command_of_its_own(self):
        text = self.GATE_DIGEST_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("make gate-digest", text)
        for tool in ("gate_digest.py", "gates.py", "unittest"):
            self.assertNotIn(
                f"python3 {tool}", text,
                f"{tool} is invoked directly in CI; it belongs in a make"
                " target, or the two repos' CI will diverge")

    def test_the_payload_gate_digest_workflow_is_the_mirror_of_this_repo_s(self):
        self.assertEqual(self.PAYLOAD_GATE_DIGEST_WORKFLOW.read_bytes(),
                         self.GATE_DIGEST_WORKFLOW.read_bytes())

    def test_both_makefiles_expose_the_toolsmith_mine_target(self):
        self.assertEqual(self.recipes(self.MAKEFILE, "toolsmith-mine"),
                         self.TOOLSMITH_MINE_TARGET)
        self.assertEqual(
            self.recipes(self.TEMPLATE_MAKEFILE, "toolsmith-mine"),
            [product_form(c) for c in self.TOOLSMITH_MINE_TARGET])

    def test_the_toolsmith_mine_workflow_names_no_command_of_its_own(self):
        text = self.TOOLSMITH_MINE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("make toolsmith-mine", text)
        for tool in ("rejection_mining.py", "gates.py", "unittest"):
            self.assertNotIn(
                f"python3 {tool}", text,
                f"{tool} is invoked directly in CI; it belongs in a make"
                " target, or the two repos' CI will diverge")

    def test_the_payload_toolsmith_workflow_is_the_mirror_of_this_repo_s(self):
        self.assertEqual(self.PAYLOAD_TOOLSMITH_MINE_WORKFLOW.read_bytes(),
                         self.TOOLSMITH_MINE_WORKFLOW.read_bytes())

    def test_the_assembler_gate_is_the_owner_and_the_ready_label(self):
        """ADR-0032's two security invariants, pinned physically in the
        workflow: the job runs only for wo:ready-for-agent applied by the repo
        owner, and the agent step skips gracefully with no credential (never
        a fabricated run). Either credential satisfies the gate — an API key
        or a subscription OAuth token (claude setup-token; the operator's
        Max plan mints no API key), and the action receives both inputs."""
        text = self.ASSEMBLER_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github.event.label.name == 'wo:ready-for-agent'", text)
        self.assertIn(
            "github.event.sender.login == github.repository_owner", text)
        self.assertIn(
            "(env.ANTHROPIC_API_KEY != '' ||"
            " env.CLAUDE_CODE_OAUTH_TOKEN != '')", text)
        self.assertIn(
            "claude_code_oauth_token:"
            " ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}", text)

    def test_the_assembler_gate_honors_the_circuit_breaker(self):
        """ADR-0034's monthly breaker: cost-report.yml sets the
        FACTORY_PAUSED repo variable, and the dispatch job is its one
        reader — without this term the breaker is a variable nobody
        reads and the documented repo-wide pause is inert."""
        text = self.ASSEMBLER_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("vars.FACTORY_PAUSED != 'true'", text)

    def test_the_cost_report_workflow_clears_the_breaker_under_the_cap(self):
        """ADR-0034's breaker is MONTHLY: a new month opening under the
        cap must clear FACTORY_PAUSED (the resume leg) — without it the
        variable latches true forever and the first breach pauses
        dispatch permanently."""
        text = self.COST_REPORT_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("gh variable set FACTORY_PAUSED --body false", text)

    def test_the_agent_action_is_pinned_by_sha(self):
        """The dispatch job holds write scopes and the API key, so its
        third-party action must change only by reviewed commit — a mutable
        tag re-point is a same-day, unreviewed change to the factory's most
        privileged surface. (The byte-mirror test above extends the pin to
        the payload copy.)"""
        text = self.ASSEMBLER_WORKFLOW.read_text(encoding="utf-8")
        self.assertRegex(
            text, r"uses: anthropics/claude-code-action@[0-9a-f]{40}")


class TestRunSteps(unittest.TestCase):
    """workflow_parse.run_steps — the stdlib extractor the run-step
    invariant is built on (sibling of make_parse.make_recipe)."""

    def test_inline_and_block_forms_are_both_extracted(self):
        text = ("jobs:\n  a:\n    steps:\n"
                "      - run: make check\n"
                "      - name: glue\n"
                "        run: |\n"
                "          set +e\n"
                "          make check > findings.txt 2>&1\n"
                "      - run: make review\n")
        self.assertEqual(workflow_parse.run_steps(text), [
            "make check",
            "set +e\nmake check > findings.txt 2>&1",
            "make review"])

    def test_a_block_keeps_comments_and_drops_blank_lines(self):
        text = ("      - run: |\n"
                "          # why this step exists\n"
                "\n"
                "          gh variable set X --body true\n"
                "      - run: make check\n")
        self.assertEqual(workflow_parse.run_steps(text), [
            "# why this step exists\ngh variable set X --body true",
            "make check"])

    def test_a_dedent_ends_the_block(self):
        text = ("        run: |\n"
                "          git push\n"
                "      - name: next step\n"
                "        run: make check\n")
        self.assertEqual(workflow_parse.run_steps(text),
                         ["git push", "make check"])

    def test_a_sibling_key_ends_a_dash_form_block(self):
        # For a `- run: |` sequence item the block's boundary is the KEY
        # column, not the dash column — otherwise a trailing sibling key
        # (env:, if:) is swallowed into the step body.
        text = ("      - run: |\n"
                "          git push\n"
                "        env:\n"
                "          TOKEN: x\n")
        self.assertEqual(workflow_parse.run_steps(text), ["git push"])

    def test_a_chomping_indicator_still_opens_a_block(self):
        # `|-`/`|+`/`>` variants must not degrade into a phantom inline
        # step whose body lines are never inspected.
        text = ("        run: |-\n"
                "          make check\n")
        self.assertEqual(workflow_parse.run_steps(text), ["make check"])


class TestWorkflowRunStepInvariant(unittest.TestCase):
    """Every run step in every workflow OPENS with `make` or a named,
    reasoned allowlist entry — enumeration was the old guard's hole: a
    tool absent from a denylist could drift CI from `make check`. Step
    identity is the first non-comment line, so an allowlisted opener
    admits the rest of its block; the denylist tests above stay as the
    depth guard inside those blocks (they scan whole workflow texts for
    named tools). Together they are the structural closure over all of
    .github/workflows/."""

    WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"
    EXPECTED = {"assembler.yml", "charter-replay.yml", "cost-report.yml",
                "design.yml", "gate-digest.yml", "sweeps.yml",
                "validator.yml"}

    # Each entry is a step's first non-comment line, exact. Each is a
    # deliberate hole in the make-only invariant and carries the reason it
    # stays true. An entry admits the whole step it opens, so re-review the
    # full block whenever an allowlisted step changes.
    ALLOWED = {
        "charter-replay.yml": (
            # this-repo-only, never mirrored: the replay deliberately
            # lives outside the Makefile (paid model runs, manual only);
            # the CLI version rides in env from the pinned dispatch input
            'npm install -g "@anthropic-ai/claude-code@${CLI_VERSION}"',
            # the replay invocation: builds argv from the dispatch inputs
            'args=(--model "$MODEL" --record)',
        ),
        "sweeps.yml": (
            # this-repo-only sweep tools — same reason charter-replay is
            # exempt: never mirrored into a stamped repo's CI
            "python3 sweeps.py ensure-labels",
            "python3 sweeps.py label-drift",
            "python3 sweeps.py reconcile",
            "python3 sweeps.py sentry --payload sentry.json",
            # shell glue: names the missing-secret cause, then fetches the
            # Sentry payload with the token passed on stdin, never argv
            'if [ -z "${SENTRY_TOKEN}" ]; then',
        ),
        "cost-report.yml": (
            # the compute/mutate boundary (workflow header comment): gh
            # mutations stay in YAML, never in a make target
            'gh issue create --title "$REPORT_TITLE" --body "$REPORT_BODY"',
            # the breach leg: names the missing-token cause, then flips
            # FACTORY_PAUSED on
            'if [ -z "${GH_TOKEN}" ]; then',
            # the resume leg: the same gh-mutation boundary, opposite
            # direction — clears FACTORY_PAUSED once a new month's spend
            # is back under the cap
            'if [ -n "${GH_TOKEN}" ]; then',
        ),
        "gate-digest.yml": (
            # git mutation glue: commits the ledger rows `make gate-digest`
            # just wrote (the make target computes, the YAML mutates)
            'git config user.name "github-actions[bot]"',
        ),
        "validator.yml": (
            # shell glue capturing `make check`'s findings and exit code
            # for the review step; the command underneath is still make
            "set +e",
            # the dispatched-PR path (WO-0030): synthesizes the webhook
            # payload from the REST API so the make steps read
            # GITHUB_EVENT_PATH identically on both trigger paths — a gh
            # read plus env glue, no computation to move into make
            'gh api "repos/${GITHUB_REPOSITORY}/pulls/${PR}" \\',
        ),
        "assembler.yml": (
            # the gate-3 hand-off (WO-0030): GITHUB_TOKEN-authored PRs
            # raise no pull_request events, so the validator is dispatched
            # by name — a gh mutation, which the compute/mutate boundary
            # keeps in YAML (the PR number it consumes comes from
            # `make find-pr`, the tested authority)
            "gh workflow run validator.yml -f pr=${{ steps.find.outputs.pr }}",
            # git mutation glue (WO-0031): pushes the spend row `make
            # wo-record` just appended from a fresh origin/main worktree —
            # the agent step may have left HEAD on its WO branch, and only
            # the appended row may travel to main
            'git config user.name "github-actions[bot]"',
        ),
    }

    def test_every_run_step_is_make_or_allowlisted(self):
        # .yaml counts too — GitHub accepts both suffixes, and a workflow
        # invisible to this scan is a hole in the invariant.
        paths = sorted(list(self.WORKFLOWS.glob("*.yml"))
                       + list(self.WORKFLOWS.glob("*.yaml")))
        names = {path.name for path in paths}
        self.assertLessEqual(self.EXPECTED, names,
                             "a known workflow file is missing")
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for step in offending_run_steps(
                    text, self.ALLOWED.get(path.name, ())):
                self.fail(f"{path.name}: run step neither goes through"
                          f" make nor is allowlisted:\n{step}")

    def test_the_helper_flags_a_drifting_step(self):
        # The guard itself, not just the current tree: a tool invoked
        # directly must surface even when no denylist names it.
        text = "jobs:\n  x:\n    steps:\n      - run: python3 gates.py\n"
        self.assertEqual(offending_run_steps(text), ["python3 gates.py"])

    def test_an_allowlisted_first_line_admits_only_that_step(self):
        text = ("      - run: |\n"
                "          set +e\n"
                "          make check\n"
                "      - run: python3 gates.py\n")
        self.assertEqual(offending_run_steps(text, ("set +e",)),
                         ["python3 gates.py"])


class TestMainSummary(cli_contract.ReportContract, unittest.TestCase):
    """gates.main against the real repo — the most load-bearing summary in
    the repo (CI greps `gates: 0 problem(s)`), pinned through the shared
    epilogue. Live-tree run, same precedent as test_factory_init's
    TestAcceptanceStampRealRepo."""

    summary_line = "gates: 0 problem(s)"

    def clean_cli(self):
        return cli_contract.capture(gates.main, [])


class TestSelftest(unittest.TestCase):
    def test_selftest_passes(self):
        self.assertEqual(gates.selftest(), 0)


if __name__ == "__main__":
    unittest.main()
