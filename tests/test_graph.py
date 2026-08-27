import tempfile
import unittest
from pathlib import Path

from src.graph.loader import CareerGraph, load_graph
from src.generator import Jinja2Generator
from src.render.adapter import bind_view
from src.render.editorial import validate_bullet
from src.render.views import CareerView, ClaimView, load_view


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
            cookpad["highlights"],
            [
                "Built and iterated a staged video-understanding pipeline spanning observation, ingredient-state reasoning, and cooking-issue detection; improved dish coverage on a fixed evaluation set from 50% to 95% (53/56).",
                "Established capability-based evaluations and automated scoring for observation accuracy, issue coverage, factuality, coherence, and turn-level coaching quality.",
            ],
        )
        self.assertEqual(
            cookpad["highlight_claim_ids"],
            [
                ["cookpad-vu-pipeline", "cookpad-vu-dish-coverage"],
                ["cookpad-vu-evals"],
            ],
        )
        self.assertEqual(
            cathay["highlights"],
            [
                "Designed and built enterprise GenAI infrastructure spanning an AI Gateway, guardrails, and MLflow, reducing latency for internal AI services by 60%.",
                "Designed and delivered internal research automation that reduced a two-hour analysis workflow to 15 minutes.",
                "Mapped a regulatory-comparison workflow with legal and compliance stakeholders, then productionized the PoC on Databricks; improved the agent's F1 from 0.67 to 0.89. The system was adopted by 2 of 5 subsidiaries.",
            ],
        )
        self.assertEqual(
            cathay["highlight_claim_ids"],
            [
                ["cathay-gaia-infra"],
                ["cathay-dogi-agents"],
                ["cathay-rkb-discovery", "cathay-rkb-f1"],
            ],
        )
        for role in profile["work"]:
            self.assertEqual(len(role["highlights"]), len(role["highlight_claim_ids"]))
        self.assertEqual(cathay["position"], "Machine Learning Engineer / Team Lead")
        self.assertEqual(len(profile["work"]), 4)
        self.assertEqual(profile["work"][-1]["name"], "TripSaaS")
        self.assertEqual(
            [row["name"] for row in profile["skills"]],
            ["AI & Agent Systems", "Engineering", "Platforms & MLOps"],
        )

        rendered = Jinja2Generator("templates").render(profile, "resume.html.j2")
        self.assertIn("TripSaaS", rendered)
        self.assertIn("Designed and delivered internal research automation", rendered)
        self.assertNotIn("Reduced overall cloud spend by 40%", rendered)
        self.assertIn("LangGraph", rendered)
        self.assertNotIn("R (basic)", rendered)

    def test_one_pager_cannot_select_internal_claim(self):
        from src.render.adapter import _require_claim

        graph = load_graph("career")
        with self.assertRaisesRegex(ValueError, "internal claim"):
            _require_claim(graph, "cookpad-vu-internal-coaching", view="one-pager")

    def test_detailed_resume_covers_public_career_without_duplicate_results(self):
        graph = load_graph("career")
        profile = bind_view(graph, load_view("views/detailed.yaml"))

        self.assertEqual(len(profile["work"]), 6)
        self.assertEqual(len(profile["projects"]), 3)
        self.assertEqual(
            [project["name"] for project in profile["projects"]],
            [
                "DOGI Multi-Agent Productivity Suite",
                "GAIA Enterprise Gen-AI Platform",
                "Regulatory Knowledge Base (RKB)",
            ],
        )
        self.assertTrue(
            all(
                project["company"] == "Cathay Financial Holdings"
                for project in profile["projects"]
            )
        )

        all_claim_ids = [
            claim_id
            for item in [*profile["work"], *profile["projects"]]
            for claim_ids in item["highlight_claim_ids"]
            for claim_id in claim_ids
        ]
        self.assertEqual(len(all_claim_ids), len(set(all_claim_ids)))
        self.assertNotIn("cathay-dogi-finops-agent", all_claim_ids)
        self.assertNotIn("cookpad-vu-internal-coaching", all_claim_ids)
        self.assertIn("cookpad-vu-multi-agent-recall", all_claim_ids)
        self.assertIn("cookpad-vu-evaluation-grounding", all_claim_ids)
        self.assertIn("cookpad-vu-end-to-end-evaluation", all_claim_ids)
        self.assertIn("cookpad-vu-rag-refactor", all_claim_ids)
        self.assertIn("cookpad-vu-evaluation-to-production", all_claim_ids)

        cookpad = profile["work"][0]
        self.assertEqual(len(cookpad["highlights"]), 5)
        self.assertLessEqual(
            sum(len(highlight.split()) for highlight in cookpad["highlights"]),
            140,
        )

        text = " ".join(
            highlight
            for item in [*profile["work"], *profile["projects"]]
            for highlight in item["highlights"]
        )
        self.assertEqual(text.count("GPU costs by 30%"), 1)
        self.assertEqual(text.count("cloud spend by 40%"), 1)
        self.assertNotIn("F1 led to adoption", text)
        self.assertNotIn("built the poc", text.lower())
        self.assertIn("five-agent productivity suite", text)
        self.assertIn("multi-agent video-understanding system", text)
        self.assertIn("recall from 50% to 95%", text)
        self.assertIn("video context from 40 to 7 minutes", text)
        self.assertIn("end-to-end agent evaluation framework", text)
        self.assertIn("single-agent video-understanding workflow", text)
        self.assertIn("evaluation-to-production architecture", text)
        self.assertNotIn("dish-specific signals in 13 of 14 cases", text)
        self.assertNotIn("versioned, replayable evaluations", text)
        self.assertNotIn("these later changes caused", text)

        rendered = Jinja2Generator("templates").render(
            profile, "resume_detailed.html.j2"
        )
        self.assertIn("Selected Systems & Technical Depth", rendered)
        self.assertIn("Education & Research", rendered)
        self.assertIn("AI Agent 專案架構最佳實踐", rendered)
        self.assertNotIn("internal benchmark", rendered)

    def test_view_cannot_attach_claim_to_the_wrong_role(self):
        graph = load_graph("career")
        view = load_view("views/one-pager.yaml").model_copy(deep=True)
        bullet = view.roles[0].claims[0]
        assert isinstance(bullet, ClaimView)
        bullet.supporting_claims = ["cathay-gaia-infra"]

        with self.assertRaisesRegex(
            ValueError, "cannot attach claim cathay-gaia-infra to role cookpad-senior-ai"
        ):
            bind_view(graph, view)

    def test_supporting_claim_must_be_public(self):
        graph = load_graph("career")
        view = load_view("views/one-pager.yaml").model_copy(deep=True)
        bullet = view.roles[0].claims[0]
        assert isinstance(bullet, ClaimView)
        bullet.supporting_claims = ["cookpad-vu-internal-coaching"]

        with self.assertRaisesRegex(ValueError, "internal claim"):
            bind_view(graph, view)

    def test_multi_claim_bullet_requires_locale_rewrite(self):
        graph = load_graph("career")
        view = load_view("views/one-pager.yaml").model_copy(deep=True)
        bullet = view.roles[0].claims[0]
        assert isinstance(bullet, ClaimView)
        bullet.text = ""

        with self.assertRaisesRegex(ValueError, "requires an editorial rewrite"):
            bind_view(graph, view)

        japanese = load_view("views/one-pager.yaml").model_copy(
            deep=True, update={"locale": "ja"}
        )
        japanese_bullet = japanese.roles[0].claims[0]
        assert isinstance(japanese_bullet, ClaimView)
        japanese_bullet.text_ja = "   "
        with self.assertRaisesRegex(ValueError, "requires an editorial rewrite"):
            bind_view(graph, japanese)

        no_standard = load_view("views/one-pager.yaml").model_copy(
            deep=True, update={"editorial_standard": "none"}
        )
        no_standard_bullet = no_standard.roles[0].claims[0]
        assert isinstance(no_standard_bullet, ClaimView)
        no_standard_bullet.text = "   "
        with self.assertRaisesRegex(ValueError, "requires an editorial rewrite"):
            bind_view(graph, no_standard)

    def test_editorial_standard_rejects_metric_and_tool_first_bullets(self):
        graph = load_graph("career")
        metric_view = load_view("views/one-pager.yaml").model_copy(deep=True)
        metric_bullet = metric_view.roles[0].claims[0]
        assert isinstance(metric_bullet, ClaimView)
        metric_bullet.text = (
            "Raised dish coverage from 50% to 95% on a fixed evaluation set."
        )
        with self.assertRaisesRegex(ValueError, "metric-first"):
            bind_view(graph, metric_view)

        tool_view = load_view("views/one-pager.yaml").model_copy(deep=True)
        tool_bullet = tool_view.roles[1].claims[1]
        assert isinstance(tool_bullet, ClaimView)
        tool_bullet.text = (
            "Built Google ADK agents that automated deep-research workflows and "
            "cut analysis time from 2 hours to 15 minutes."
        )
        with self.assertRaisesRegex(ValueError, "tool-first"):
            bind_view(graph, tool_view)

        with self.assertRaisesRegex(ValueError, "tool-first"):
            validate_bullet(
                "Designed and built a Google ADK agent for internal research automation.",
                standard="senior-impact-v1",
                locale="en",
                skill_titles=["Google ADK"],
            )
        validate_bullet(
            "Built distributed systems that supported reliable production AI workflows.",
            standard="senior-impact-v1",
            locale="en",
            skill_titles=["Google ADK"],
        )

    def test_claim_view_rejects_duplicate_provenance(self):
        with self.assertRaisesRegex(ValueError, "same claim more than once"):
            ClaimView.model_validate(
                {
                    "id": "cookpad-vu-pipeline",
                    "supporting_claims": ["cookpad-vu-pipeline"],
                }
            )

        bullet = ClaimView(id="cookpad-vu-pipeline")
        with self.assertRaisesRegex(ValueError, "same claim more than once"):
            bullet.supporting_claims = ["cookpad-vu-pipeline"]

        graph = load_graph("career")
        view = load_view("views/one-pager.yaml").model_copy(deep=True)
        mutated = view.roles[0].claims[0]
        assert isinstance(mutated, ClaimView)
        mutated.supporting_claims.append(mutated.id)
        with self.assertRaisesRegex(ValueError, "same claim more than once"):
            bind_view(graph, view)

    def test_single_claim_whitespace_rewrite_falls_back_to_canonical_text(self):
        graph = load_graph("career")
        view = load_view("views/one-pager.yaml").model_copy(
            deep=True, update={"locale": "ja"}
        )
        research = view.roles[1].claims[1]
        assert isinstance(research, ClaimView)
        research.text_ja = "   "
        profile = bind_view(graph, view)
        self.assertTrue(profile["work"][1]["highlights"][1].startswith("Google ADK"))

    def test_view_locale_is_closed_to_supported_languages(self):
        payload = load_view("views/one-pager.yaml").model_dump()
        payload["locale"] = "jp"
        with self.assertRaises(ValueError):
            CareerView.model_validate(payload)

    def test_structured_project_claims_keep_provenance_and_focus(self):
        graph = load_graph("career")
        view = load_view("views/full.yaml").model_copy(deep=True)
        rkb = next(project for project in view.projects if project.id == "cathay-rkb")
        rkb.claims = [
            ClaimView(
                id="cathay-rkb-discovery",
                supporting_claims=["cathay-rkb-f1"],
                text="Mapped and productionized the regulatory-comparison workflow on Databricks.",
            )
        ]
        profile = bind_view(graph, view)
        rendered_rkb = next(
            project for project in profile["projects"] if "RKB" in project["name"]
        )
        self.assertEqual(
            rendered_rkb["highlight_claim_ids"],
            [["cathay-rkb-discovery", "cathay-rkb-f1"]],
        )

        structured = rkb.claims[0]
        assert isinstance(structured, ClaimView)
        structured.supporting_claims = ["cathay-gaia-infra"]
        with self.assertRaisesRegex(
            ValueError, "cannot attach claim cathay-gaia-infra to project cathay-rkb"
        ):
            bind_view(graph, view)

    def test_view_rejects_role_owned_by_another_person(self):
        graph = load_graph("career")
        role = graph.get("cookpad-senior-ai")
        role.person = "another-person"
        with self.assertRaisesRegex(ValueError, "cannot attach role"):
            bind_view(graph, load_view("views/one-pager.yaml"))

    def test_graph_rejects_non_reciprocal_claim_links(self):
        graph = load_graph("career")
        focus = graph.get("cookpad-vu")
        focus.claims = [
            claim_id
            for claim_id in focus.claims
            if claim_id != "cookpad-vu-pipeline"
        ]
        with self.assertRaisesRegex(ValueError, "non-reciprocal claim link"):
            CareerGraph(graph.pages)

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
