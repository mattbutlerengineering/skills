"""Factory gate detectors (gates.py) — fixture-tree tests.

Same discipline as test_lint_checkers: every checker is exercised through
its public interface against a temp fixture tree, and tests assert the
exact problem strings callers will print.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import gates


class FixtureTree:
    def __init__(self, root):
        self.root = Path(root)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


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


class TestCostLedger(unittest.TestCase):
    """G (origin: WO-0008, ADR-0034): the append-only cost ledger is the
    factory's measurement substrate; a merged order missing from it is a
    gating finding, and an absent ledger means no runs are recorded yet."""

    LINE = {"wo": "WO-0001", "run_id": "r-1", "model": "m",
            "tokens": 1200, "cost": 0.42, "outcome": "merged"}

    def build(self, tmp, *lines, row="- [x] WO-0001 slice (PRD-0001)\n"):
        tree = FixtureTree(tmp)
        tree.write("docs/features/demo/breakdown.md", row)
        if lines:
            tree.write("docs/factory/costs.jsonl",
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

    def test_malformed_line_is_a_problem_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp, self.LINE)
            tree.write("docs/factory/costs.jsonl",
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
                tmp, {"wo": "WO-0001", "run_id": "r-1", "model": "m",
                      "tokens": 1, "cost": 0.1, "outcome": "merged",
                      "note": "extra"},
                {"wo": "WO-0001", "model": "m", "outcome": "merged"})
            self.assertEqual(gates.check_cost_ledger(tree.root), [
                "G: docs/factory/costs.jsonl:1 ledger line has unknown"
                " field(s): note",
                "G: docs/factory/costs.jsonl:2 ledger line is missing"
                " field(s): cost, run_id, tokens"])

    def test_bad_field_values_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, {"wo": "WO-0009", "run_id": "", "model": "m",
                      "tokens": -1, "cost": "free", "outcome": "merged"})
            self.assertEqual(gates.check_cost_ledger(tree.root), [
                "G: docs/factory/costs.jsonl:1 wo WO-0009 has no breakdown"
                " row",
                "G: docs/factory/costs.jsonl:1 run_id must be a non-empty"
                " string",
                "G: docs/factory/costs.jsonl:1 tokens must be a non-negative"
                " integer",
                "G: docs/factory/costs.jsonl:1 cost must be a non-negative"
                " number",
                "G: docs/features/demo/breakdown.md:1 merged work order"
                " WO-0001 has no line in docs/factory/costs.jsonl"])

    def test_untyped_wo_field_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(
                tmp, {"wo": "nope", "run_id": "r", "model": "m",
                      "tokens": 0, "cost": 0, "outcome": "failed"})
            problems = gates.check_cost_ledger(tree.root)
            self.assertIn(
                "G: docs/factory/costs.jsonl:1 wo 'nope' is not a WO-####"
                " token", problems)

    def test_blank_lines_are_tolerated(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.build(tmp, self.LINE)
            tree.write("docs/factory/costs.jsonl",
                       json.dumps(self.LINE) + "\n\n")
            self.assertEqual(gates.check_cost_ledger(tree.root), [])


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


class TestConfigShape(unittest.TestCase):
    GOOD = {"budgets_usd": {"S": 5, "M": 15, "L": 40},
            "routing": {"mechanical": "m", "implementation": "i",
                        "architecture_review": "a"},
            "wip_cap": 3, "monthly_cap_usd": 300}

    def test_valid_config_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("factory/templates/factory.json", json.dumps(self.GOOD))
            self.assertEqual(gates.check_config_shape(tree.root), [])

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

class TestEvidenceHonesty(unittest.TestCase):
    """H (origin: WO-0011): a criterion that asserts a LABELLED verdict must
    show literal output or disclose that the check was NOT RUN.

    Only a labelled verdict line (`Result:` / `Verdict:` / `Outcome:` /
    `Status:`) creates the obligation. Unlabelled prose and heading text
    assert nothing the detector recognises — a summary may narrate, an
    author may write "Done." — so there is no roll-up excuse to purchase.
    """

    HEAD = "---\nstage: verify\nrun: feature:demo\n---\n\n# Verification\n\n"
    REL = "docs/features/demo/verification.md"

    def verification(self, tmp, body):
        tree = FixtureTree(tmp)
        tree.write("docs/features/demo/verification.md", self.HEAD + body)
        return tree

    def bare(self, title, verdict):
        return (f'H: {self.REL}:%d criterion "{title}" asserts {verdict}'
                " with neither literal evidence nor a NOT-RUN disclaimer"
                " (evidence must be a fenced code block in this section)")

    # ---- the rule, in both directions ---------------------------------

    def test_criterion_with_literal_output_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "## Criteria & evidence\n\n"
                "### Suite is green\n\n"
                "- Check: `python3 -m unittest discover tests`\n"
                "- Evidence:\n"
                "  ```\n"
                "  Ran 212 tests in 4.0s\n\n"
                "  OK\n"
                "  ```\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    def test_criterion_with_not_run_disclaimer_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Non-owner dispatch does not fire\n\n"
                "- Check: NOT RUN — needs a second GitHub account.\n"
                "- Result: NOT VERIFIED\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    def test_asserted_but_unevidenced_criterion_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Suite is green\n\n"
                "- Check: ran the tests, everything looks correct.\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root),
                             [self.bare("Suite is green", "PASS") % 11])

    def test_relabelled_verdict_lines_still_engage_the_rule(self):
        """`Verdict:` / `Outcome:` / `Status:` assert exactly what `Result:`
        asserts; renaming the label must not buy the criterion out."""
        for label in ("Verdict", "Outcome", "Status", "result"):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                tree = self.verification(tmp, (
                    "### Dispatch fires\n\n"
                    "- Check: eyeballed the run.\n"
                    f"- {label}: PASS\n"))
                self.assertEqual(gates.check_evidence_honesty(tree.root),
                                 [self.bare("Dispatch fires", "PASS") % 11])

    def test_evidence_does_not_leak_across_criteria(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Evidenced\n\n"
                "- Evidence:\n"
                "  ```\n"
                "  OK\n"
                "  ```\n"
                "- Result: PASS\n\n"
                "### Bare\n\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root),
                             [self.bare("Bare", "PASS") % 18])

    def test_appendix_fence_does_not_vouch_for_other_criteria(self):
        """Evidence is section-scoped: a throwaway fence in an appendix
        vouches for nothing three headings away."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Dispatch fires\n\n"
                "- Result: PASS\n\n"
                "### Budget guard holds\n\n"
                "- Verdict: PASS\n\n"
                "## Appendix: branch log\n\n"
                "```\n"
                "git log --oneline -3\n"
                "```\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                self.bare("Dispatch fires", "PASS") % 10,
                self.bare("Budget guard holds", "PASS") % 14])

    def test_scoped_hedge_is_not_a_not_run_disclaimer(self):
        """"not tested on Windows" concedes the check DID run. A scoped
        hedge is partial coverage, not a disclosure."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Suite is green\n\n"
                "- Check: ran the suite.\n"
                "- Result: PASS\n"
                "- Caveat: not tested on Windows.\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root),
                             [self.bare("Suite is green", "PASS") % 11])

    def test_body_not_run_note_does_not_excuse_an_asserted_claim(self):
        """A section that CLAIMS PASS and mentions in passing that something
        else was not run has disclosed nothing about the PASS. While any
        unqualified "not run" in the body disarmed the section, "(the retry
        path was not run)" was a two-word licence to fabricate any verdict —
        a bypass that survived attempts 1 and 2. The disclosure has to BE the
        verdict, not sit next to it."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Suite is green\n\n"
                "- Check: ran it.\n"
                "- Result: PASS\n"
                "- Note: the browser matrix was not run.\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root),
                             [self.bare("Suite is green", "PASS") % 11])

    def test_a_verdict_that_makes_no_claim_needs_no_evidence(self):
        """The other side of that line: a verdict which claims nothing —
        NOT VERIFIED, SKIPPED, N/A — IS the disclosure, and owes no output."""
        for verdict in ("NOT VERIFIED", "NOT RUN", "SKIPPED", "N/A"):
            with self.subTest(verdict=verdict), \
                    tempfile.TemporaryDirectory() as tmp:
                tree = self.verification(tmp, (
                    "### Cap breach pauses the factory\n\n"
                    "- Check: needs a month of real cost data.\n"
                    f"- Result: {verdict}\n"))
                self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    def test_a_claim_beside_a_disclosure_still_owes_evidence(self):
        """Declaring one criterion NOT RUN does not buy the section's other,
        affirmative verdict out of showing its output."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Cap breach\n\n"
                "- Result: NOT VERIFIED\n"
                "- Verdict: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root),
                             [self.bare("Cap breach", "PASS") % 11])

    def test_empty_and_placeholder_fences_are_not_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
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
                "- Result: PASS | FAIL\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                self.bare("Empty fence", "PASS") % 13,
                self.bare("Unfilled template", "PASS | FAIL") % 21])

    # ---- bypasses that attempts 1 and 2 left open ----------------------

    def test_fabricated_template_shaped_artifact_is_flagged(self):
        """BYPASS 1. The verify TEMPLATE ships a `## Not verified` heading in
        every artifact. When heading text counted as a NOT-RUN disclosure it
        manufactured an artifact-wide excuse, so a 100%-fabricated,
        template-shaped artifact with ZERO command output passed silently.
        A disclosure is what the author WRITES, never the slot label."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
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
                "Nothing; everything was checked.\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                f"H: {self.REL}:1 verification artifact shows neither literal"
                " evidence nor a NOT-RUN disclaimer (evidence must be a"
                " fenced code block)"])

    def test_renaming_the_lying_section_does_not_excuse_it(self):
        """BYPASS 2. The roll-up excuse was keyed on heading NAME, so calling
        the gaming section Summary/Results/Conclusion/Overview/Verdict bought
        it out. There is no roll-up excuse any more: a labelled verdict owes
        evidence wherever it is written."""
        for name in ("Summary", "Results", "Conclusion", "Overview",
                     "Verdict"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                tree = self.verification(tmp, (
                    f"## {name}\n\n"
                    "- Result: 6/6 criteria PASS\n"
                    "- Verdict: ship it\n\n"
                    "## Not verified\n\n"
                    "Nothing; everything was checked.\n"))
                self.assertEqual(
                    gates.check_evidence_honesty(tree.root),
                    [self.bare(name, "6/6 criteria PASS") % 10])

    def test_one_honest_leaf_does_not_launder_a_lying_rollup(self):
        """BYPASS 3. The excuse asked only whether the artifact's leaves were
        evidenced — never whether the roll-up narrated THOSE criteria — so a
        single throwaway leaf (a fence holding one dot) laundered a roll-up
        making every real claim."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Grammar parses\n\n"
                "- Evidence:\n"
                "  ```\n"
                "  .\n"
                "  ```\n"
                "- Result: PASS\n\n"
                "## Results\n\n"
                "- Result: all 6 PRD criteria PASS\n"
                "- Verdict: ship it\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root),
                             [self.bare("Results", "all 6 PRD criteria PASS")
                              % 18])

    def test_a_hedge_appended_to_a_claim_does_not_disarm_it(self):
        """BYPASS 5. Reading the NOT-RUN token as a SUBSTRING of the verdict
        let a claim buy itself out by appending a hedge: "PASS ... (soak test
        not run)" asserted PASS and showed nothing, in silence. A verdict is
        a disclosure only when the WHOLE value is one."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "## Criterion 1 - payment capture\n\n"
                "- Result: PASS - every acceptance criterion met, full suite"
                " green (soak test not run).\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                self.bare("Criterion 1 - payment capture",
                          "PASS - every acceptance criterion met, full suite"
                          " green (soak test not run).") % 10])

    def test_a_disclosure_may_give_its_reason(self):
        """The other side of anchoring it: an honest disclosure names why the
        check did not run, and that reason must not turn it into a claim."""
        for verdict in ("NOT RUN — the CI runner was offline",
                        "NOT VERIFIED (needs a second GitHub account)",
                        "N/A — no payment provider in this environment",
                        "SKIPPED: covered by the nightly soak",
                        "**NOT RUN**"):
            with self.subTest(verdict=verdict), \
                    tempfile.TemporaryDirectory() as tmp:
                tree = self.verification(tmp, (
                    "### Soak test\n\n"
                    f"- Result: {verdict}\n"))
                self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    def test_verdict_labels_beyond_the_original_four_engage_the_rule(self):
        """BYPASS 6. The label whitelist (Result/Verdict/Outcome/Status) was
        itself the escape hatch: a lying section headed `Conclusion:` was
        invisible. Every verdict noun asserts."""
        for label in ("Conclusion", "Assessment", "Finding", "Determination",
                      "Evaluation", "Judgement", "Judgment", "Disposition",
                      "Decision", "Ruling", "Appraisal"):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                tree = self.verification(tmp, (
                    "### Payments capture\n\n"
                    "- Check: eyeballed the dashboard.\n"
                    f"- {label}: PASS\n"))
                self.assertEqual(gates.check_evidence_honesty(tree.root),
                                 [self.bare("Payments capture", "PASS") % 11])

    def test_one_honest_fence_does_not_launder_relabelled_lies(self):
        """BYPASS 6, as reported: one real fence (lint) satisfied the
        artifact-wide backstop, and the two fabricated criteria beside it used
        labels outside the whitelist, so the whole artifact passed silently.
        Each lying section now owes evidence in its own right."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "## Criterion 0 - lint\n\n"
                "- Evidence:\n"
                "  ```\n"
                "  lint: 0 problem(s)\n"
                "  ```\n\n"
                "## Criterion 1 - payments\n\n"
                "- Conclusion: PASS. All 12 criteria met, full suite green.\n\n"
                "## Criterion 2 - retries\n\n"
                "- Assessment: works correctly under load. Ship it.\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                self.bare("Criterion 1 - payments",
                          "PASS. All 12 criteria met, full suite green.") % 17,
                self.bare("Criterion 2 - retries",
                          "works correctly under load. Ship it.") % 21])

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
        with tempfile.TemporaryDirectory() as tmp:
            tree = FixtureTree(tmp)
            tree.write("docs/features/demo/verification.md", (
                "---\nstage: verify\nstatus: done\nrun: feature:demo\n---\n\n"
                "# Verification\n\n"
                "## Summary\n\n"
                "Everything works; all criteria are comfortably met.\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                f"H: {self.REL}:1 verification artifact shows neither literal"
                " evidence nor a NOT-RUN disclaimer (evidence must be a"
                " fenced code block)"])

    # ---- the fence scanner (CommonMark, not a parity toggle) -----------

    def test_longer_fence_quoting_a_shorter_one_stays_one_block(self):
        """BYPASS 4a. A ```` fence quoting a ``` fence: the shorter marker is
        content, not a delimiter. The parity toggle flipped on it and lost
        the evidence, false-positiving on an author who DID paste output."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Skill doc renders\n\n"
                "- Evidence:\n"
                "  ````\n"
                "  ```bash\n"
                "  make check\n"
                "  ```\n"
                "  ````\n"
                "- Result: PASS\n\n"
                "### Router picks the model\n\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root),
                             [self.bare("Router picks the model", "PASS") % 20])

    def test_backtick_fence_inside_a_tilde_block_does_not_close_it(self):
        """BYPASS 4b. A ``` line inside a ~~~ block is content — a closing
        fence must use the SAME marker. The parity toggle desynced on it and
        silently swallowed every later criterion."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Evidence quotes a snippet\n\n"
                "- Evidence:\n"
                "  ~~~\n"
                "  The README starts with:\n"
                "  ```bash\n"
                "  make check\n"
                "  ~~~\n"
                "- Result: PASS\n\n"
                "### Bare claim\n\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root),
                             [self.bare("Bare claim", "PASS") % 20])

    def test_info_string_line_does_not_close_a_fence(self):
        """A closing fence carries NO info string, so ```bash inside a ```
        block is content (CommonMark)."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Docs quote a shell block\n\n"
                "- Evidence:\n"
                "  ```\n"
                "  ```bash\n"
                "  make check\n"
                "  ```\n"
                "- Result: PASS\n\n"
                "### Bare claim\n\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root),
                             [self.bare("Bare claim", "PASS") % 19])

    def test_unclosed_fence_is_flagged(self):
        """BYPASS 4c. An unclosed fence absorbed the tail of the artifact in
        silence. It must be a problem, not a swallow."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Suite is green\n\n"
                "- Evidence:\n"
                "  ```\n"
                "  Ran 212 tests\n\n"
                "  OK\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                f"H: {self.REL}:11 unclosed code fence — every criterion after"
                " it is unread"])

    def test_headings_inside_a_fence_do_not_split_the_criterion(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### Report renders\n\n"
                "- Evidence:\n"
                "  ```\n"
                "  ### Weekly report\n"
                "  3 work orders merged\n"
                "  ```\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

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
        with tempfile.TemporaryDirectory() as tmp:
            setext = self.verification(tmp, self.SETEXT_BODY)
            problems = gates.check_evidence_honesty(setext.root)
        with tempfile.TemporaryDirectory() as tmp:
            atx = self.verification(tmp, self.ATX_BODY)
            control = gates.check_evidence_honesty(atx.root)

        named = lambda ps: sorted(p.split("criterion ")[1] for p in ps)
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
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "## Criterion\n\n"
                "---\n\n"
                "- Evidence:\n  ```\n  ok\n  ```\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

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
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, self.EVIDENCED_NEIGHBOUR + (
                "## Criterion B - payments\n"
                "> Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                "H: docs/features/demo/verification.md:16 criterion"
                ' "Criterion B - payments" asserts PASS with neither literal'
                " evidence nor a NOT-RUN disclaimer (evidence must be a fenced"
                " code block in this section)"])

    def test_ordered_list_verdict_still_asserts(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, self.EVIDENCED_NEIGHBOUR + (
                "## Criterion B - payments\n"
                "1. Result: PASS\n"))
            problems = gates.check_evidence_honesty(tree.root)
            self.assertEqual(len(problems), 1)
            self.assertIn('"Criterion B - payments" asserts PASS', problems[0])

    def test_blockquoted_not_run_still_discloses(self):
        """The fix widens the marker class, not the claim test: a blockquoted
        NOT-RUN disclaimer is still a disclosure, owing no output."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "## Criterion B - payments\n"
                "> Result: NOT RUN — no staging card\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    def test_verdict_line_inside_a_fence_is_not_a_criterion(self):
        """Quoted output that happens to contain `Result: PASS` is evidence,
        not an assertion of the author's own."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "### CI log renders\n\n"
                "- Evidence:\n"
                "  ```\n"
                "  Result: PASS\n"
                "  ```\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    # ---- false positives: a gate that blocks honest work gets disabled --

    def test_angle_bracket_output_is_evidence_not_a_placeholder(self):
        """Shape-matching `<...>` discarded real DOM dumps and Python reprs
        as "placeholders". Only the template's own filler text is filler."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
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
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    def test_honest_prose_and_headings_are_not_criteria(self):
        """Unlabelled prose asserts nothing the detector reads: an author may
        open a note with "Done." and title a section "all checks pass"."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
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
                "Ok, that is everything.\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    def test_prose_rollup_over_evidenced_criteria_owes_nothing(self):
        """The template's `## Summary` holds "the one-sentence verdict" as
        PROSE. Prose is not a labelled verdict, so it owes no evidence — the
        excuse that used to protect it (and that gaming sections bought) is
        gone, and nothing is lost."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
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
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

    def test_labelled_verdict_in_a_summary_still_owes_evidence(self):
        """The deliberate cost of killing the roll-up excuse: if you write a
        LABELLED verdict, you back it — in that section — wherever you write
        it. Narrate in prose, or show the output."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "## Summary\n\n"
                "- Verdict: all criteria pass.\n\n"
                "## Criteria & evidence\n\n"
                "### Suite is green\n\n"
                "- Evidence:\n"
                "  ```\n"
                "  OK\n"
                "  ```\n"
                "- Result: PASS\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root),
                             [self.bare("Summary", "all criteria pass.") % 10])

    # ---- the artifact-wide backstop ------------------------------------

    def test_prose_only_artifact_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "## Summary\n\n"
                "Everything works; all criteria are comfortably met.\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                f"H: {self.REL}:1 verification artifact shows neither literal"
                " evidence nor a NOT-RUN disclaimer (evidence must be a"
                " fenced code block)"])

    def test_scoped_hedge_does_not_disarm_the_whole_artifact_backstop(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "## Summary\n\n"
                "Everything is fine; the criteria are comfortably met.\n"
                "(Not tested on Windows, but that is out of scope.)\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [
                f"H: {self.REL}:1 verification artifact shows neither literal"
                " evidence nor a NOT-RUN disclaimer (evidence must be a"
                " fenced code block)"])

    def test_written_not_run_disclosure_satisfies_the_backstop(self):
        """The disclaimer branch of the acceptance criterion: an artifact that
        ran nothing and SAYS so is honest, and stays silent."""
        with tempfile.TemporaryDirectory() as tmp:
            tree = self.verification(tmp, (
                "## Summary\n\n"
                "Nothing could be checked this run.\n\n"
                "## Not verified\n\n"
                "The whole suite was not run — the CI runner was offline.\n"))
            self.assertEqual(gates.check_evidence_honesty(tree.root), [])

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


def make_recipe(text, target):
    """The command lines of one make target (tab-indented recipe lines)."""
    lines, capturing = [], False
    for line in text.splitlines():
        if line.startswith(f"{target}:"):
            capturing = True
        elif capturing:
            if line.startswith("\t"):
                lines.append(line.strip())
            elif line.strip():
                break
    return lines


def product_form(command):
    """A root command as its product-repo twin spells it: the factory tools
    live under tools/factory/ there, and the stamped test run is quiet."""
    return (command.replace("python3 gates.py", "python3 tools/factory/gates.py")
            .replace("python3 validator.py", "python3 tools/factory/validator.py")
            .replace("unittest discover tests", "unittest discover -q tests"))


class TestLockstep(unittest.TestCase):
    """Makefile <-> CI lockstep (origin: WO-0003, tightened by WO-0004).

    The old version asserted *membership* — every canonical command appears
    somewhere — so drift by ADDITION was invisible: a step added to CI and
    not to the Makefile passed. These assert exact, ordered equality of the
    command sets, and that the workflow names no command of its own (it goes
    through `make`), which is what lets one workflow file serve both this
    repo and every stamped product repo."""

    REPO = Path(__file__).resolve().parents[1]
    WORKFLOW = REPO / ".github" / "workflows" / "validator.yml"
    PAYLOAD_WORKFLOW = (REPO / "factory" / "templates" / ".github"
                        / "workflows" / "validator.yml")
    MAKEFILE = REPO / "Makefile"
    TEMPLATE_MAKEFILE = REPO / "factory" / "templates" / "Makefile"

    # The one canonical check set. `lint.py` is the plugin's structural lint
    # and has no product-repo counterpart, so only the root Makefile runs it.
    CANONICAL_CHECK = ["python3 gates.py",
                       "python3 gates.py --selftest",
                       "python3 -m unittest discover tests"]
    ROOT_ONLY_CHECK = ["python3 lint.py"]
    VALIDATOR_TARGETS = {
        "review": ["python3 validator.py review --findings $(FINDINGS)"
                   " --status $(STATUS)"],
        "wo-merged": ["python3 validator.py lifecycle --label wo:merged"],
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
        for command in ("make check", "make review", "make wo-merged"):
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


class TestSelftest(unittest.TestCase):
    def test_selftest_passes(self):
        self.assertEqual(gates.selftest(), 0)


if __name__ == "__main__":
    unittest.main()
