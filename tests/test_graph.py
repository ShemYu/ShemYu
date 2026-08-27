import tempfile
import unittest
from pathlib import Path

from src.graph.loader import load_graph
from src.render.adapter import bind_view
from src.render.views import load_view


class LiveCareerGraphTest(unittest.TestCase):
    def test_vault_loads_with_unique_ids(self):
        graph = load_graph("career")
        self.assertGreater(len(graph.pages), 20)
        self.assertEqual(graph.get("shem").type, "person")
        self.assertEqual(graph.get("cookpad-vu").type, "focus")

    def test_obsidian_graph_block_has_wikilinks(self):
        from src.graph.obsidian import GRAPH_START, graph_markdown

        graph = load_graph("career")
        block = graph_markdown(graph, "cookpad-vu")
        self.assertIn(GRAPH_START, block)
        self.assertIn("[[cookpad-senior-ai|", block)
        self.assertIn("[[cookpad-vu-pipeline]]", block)
        shem = graph_markdown(graph, "shem")
        self.assertIn("[[cookpad-senior-ai|", shem)
        from src.graph.obsidian import CLAIM_START, claim_text_markdown
        from src.graph.schema import Claim

        discovery = graph.get("cathay-rkb-discovery")
        assert isinstance(discovery, Claim)
        body = claim_text_markdown(discovery)
        self.assertIn(CLAIM_START, body)
        self.assertIn("mapped the client's regulatory-comparison workflow", body)
        self.assertNotIn("work...", body.split("\n")[1])

    def test_claim_text_is_not_ellipsis_truncated(self):
        graph = load_graph("career")
        discovery = graph.get("cathay-rkb-discovery")
        self.assertTrue(discovery.text.en.startswith("With a data scientist"))
        self.assertIn("Databricks data layer", discovery.text.en)
        self.assertFalse(discovery.text.en.rstrip().endswith("..."))
        self.assertFalse(discovery.title.rstrip().endswith("..."))

    def test_one_pager_keeps_locked_public_bullets(self):
        graph = load_graph("career")
        view = load_view("views/one-pager.yaml")
        profile = bind_view(graph, view)
        cookpad = profile["work"][0]
        cathay = profile["work"][1]
        self.assertEqual(
            cookpad["highlights"][:3],
            [
                "Built and iterated the video-understanding system as a staged pipeline: observable facts → recipe-specific ingredient definitions → ingredient state → cooking issues.",
                "Raised dish coverage from 50% to 95% (53/56) on a fixed 15-case, 56-item eval set; knowledge coverage remains the remaining optimization target.",
                "Capability-based evals and automated scoring for observation accuracy, issue coverage, factuality, coherence, and turn-level coaching quality.",
            ],
        )
        self.assertEqual(
            cathay["highlights"][:3],
            [
                "Developed Departmental Internal AI Agents with Google ADK, automating deep research tasks, reducing analysis time from 2 hours to 15 minutes.",
                "Designed and built GenAI infrastructure (AI Gateway, Guardrails, MLflow), optimizing internal AI service latency by 60%.",
                "Implemented FinOps agent, achieving 30% GPU cost reduction.",
            ],
        )

    def test_one_pager_cannot_select_internal_claim(self):
        from src.render.adapter import _require_claim

        graph = load_graph("career")
        with self.assertRaisesRegex(ValueError, "internal claim"):
            _require_claim(graph, "cookpad-vu-internal-coaching", view="one-pager")

    def test_bible_view_keeps_internal_evidence(self):
        graph = load_graph("career")
        profile = bind_view(graph, load_view("views/bible.yaml"))
        cookpad = profile["work"][0]
        blob = " ".join(cookpad["evidence"])
        self.assertNotIn("67.6", blob)
        self.assertTrue(any("13 cases" in item for item in cookpad["evidence"]))
        self.assertTrue(any("ObservationAgent" in item for item in cookpad["evidence"]))

    def test_full_view_keeps_legacy_project_claims(self):
        graph = load_graph("career")
        profile = bind_view(graph, load_view("views/full.yaml"))
        dogi = next(item for item in profile["projects"] if "DOGI" in item["name"])
        texts = " ".join(dogi["highlights"])
        self.assertIn("Redis/Postgres", texts)
        self.assertIn("10 contributors", texts)
        self.assertNotIn("30% GPU", texts)
        finops = next(item for item in profile["projects"] if item["name"] == "FinOps")
        self.assertTrue(any("30% GPU" in line for line in finops["highlights"]))


class GraphKernelTest(unittest.TestCase):
    def test_duplicate_id_and_dangling_link_are_rejected(self):
        with tempfile.TemporaryDirectory() as vault:
            root = Path(vault)
            (root / "people").mkdir()
            (root / "people" / "shem.md").write_text(
                "---\nid: shem\ntype: person\ntitle: Test\n---\n\n",
                encoding="utf-8",
            )
            (root / "roles").mkdir()
            (root / "roles" / "missing-company.md").write_text(
                "---\nid: missing-company\ntype: role\ntitle: Eng\ncompany: no-such-co\nstart: '2024'\n---\n\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "dangling"):
                load_graph(root)


if __name__ == "__main__":
    unittest.main()
