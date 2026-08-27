import unittest

from src.generator import for_public_resume
from src.i18n import localize_profile
from src.project import project_profile
from src.schema import Profile, profile_dict


def _role_with_foci() -> dict:
    return {
        "name": "Cathay Financial Holdings",
        "position": "Machine Learning Engineer, team lead",
        "startDate": "2022-09",
        "endDate": "2026-01",
        "summary": "Led 4 full-time reports.",
        "awards": [{"name": "Won CFH Cloud Creative Award 2024 (1st place).", "date": "2024"}],
        "foci": [
            {
                "id": "cathay-dogi",
                "name": "DOGI Multi-Agent Productivity Suite",
                "kind": "product",
                "public_rank": 1,
                "problem": "Internal productivity agents.",
                "stack": ["Multi-Agent System"],
                "startDate": "2025-01",
                "endDate": "2025-12",
                "claims": [
                    {
                        "id": "cathay-dogi-mvp",
                        "layer": "public",
                        "rank": 1,
                        "axis": "社内エージェント",
                        "text": "Developed Departmental Internal AI Agents with Google ADK.",
                        "text_ja": "Google ADKで部門内AIエージェントを開発。",
                    },
                    {
                        "id": "cathay-dogi-session",
                        "layer": "public",
                        "rank": 2,
                        "resume": False,
                        "text": "Designed session persistence and storage strategy using Redis/Postgres.",
                    }
                ],
            },
            {
                "id": "cathay-gaia",
                "name": "GAIA Enterprise Gen-AI Platform",
                "kind": "platform",
                "public_rank": 2,
                "problem": "Shared GenAI infrastructure.",
                "stack": ["Databricks"],
                "startDate": "2024-11",
                "endDate": "2025-06",
                "claims": [
                    {
                        "id": "cathay-gaia-latency",
                        "layer": "public",
                        "rank": 1,
                        "text": "Designed and built GenAI infrastructure, optimizing latency by 60%.",
                    }
                ],
            },
            {
                "id": "cathay-finops",
                "name": "FinOps",
                "kind": "platform",
                "public_rank": 3,
                "problem": "GPU and cloud spend.",
                "startDate": "2025-01",
                "endDate": "2025-12",
                "claims": [
                    {
                        "id": "cathay-finops-gpu",
                        "layer": "public",
                        "rank": 1,
                        "text": "Implemented FinOps agent, achieving 30% GPU cost reduction.",
                    },
                    {
                        "id": "cathay-finops-cloud",
                        "layer": "public",
                        "rank": 2,
                        "text": "Reduced overall cloud spend by 40% through FinOps practices.",
                    },
                    {
                        "id": "cathay-finops-internal",
                        "layer": "archive",
                        "rank": 1,
                        "text": "Do not publish the 20-user launch metric.",
                        "do_not_claim": ["20 active users"],
                    },
                ],
            },
            {
                "id": "cathay-rkb",
                "name": "Regulatory Knowledge Base (RKB)",
                "kind": "product",
                "public_rank": 4,
                "problem": "Regulatory comparison over legal documents.",
                "stack": ["RAG", "Databricks"],
                "startDate": "2024-10",
                "endDate": "2025-09",
                "claims": [
                    {
                        "id": "cathay-rkb-f1",
                        "layer": "public",
                        "rank": 1,
                        "text": "Improved regulatory Agent F1 from 0.67 to 0.89; adopted by 2 of 5 subsidiaries.",
                    }
                ],
            },
        ],
    }


class ProjectProfileTest(unittest.TestCase):
    def test_unmigrated_roles_are_left_alone(self):
        profile = {
            "basics": {"name": "Test"},
            "work": [
                {
                    "name": "Wisers",
                    "position": "Engineer",
                    "startDate": "2020",
                    "highlights": ["Authored bullet"],
                    "evidence": ["Internal note"],
                }
            ],
            "projects": [{"name": "Authored Project", "startDate": "2021"}],
        }
        projected = project_profile(profile)
        self.assertEqual(projected["work"][0]["highlights"], ["Authored bullet"])
        self.assertEqual(projected["work"][0]["evidence"], ["Internal note"])
        self.assertEqual(projected["projects"][0]["name"], "Authored Project")

    def test_public_claims_flatten_by_focus_then_rank_then_awards(self):
        profile = profile_dict(
            {"basics": {"name": "Test"}, "work": [_role_with_foci()]}
        )
        projected = project_profile(profile)
        self.assertEqual(
            projected["work"][0]["highlights"],
            [
                "Developed Departmental Internal AI Agents with Google ADK.",
                "Designed and built GenAI infrastructure, optimizing latency by 60%.",
                "Implemented FinOps agent, achieving 30% GPU cost reduction.",
                "Reduced overall cloud spend by 40% through FinOps practices.",
                "Improved regulatory Agent F1 from 0.67 to 0.89; adopted by 2 of 5 subsidiaries.",
                "Won CFH Cloud Creative Award 2024 (1st place).",
            ],
        )
        self.assertEqual(
            projected["work"][0]["evidence"],
            ["Do not publish the 20-user launch metric."],
        )

    def test_derived_projects_replace_same_name_authored_entries(self):
        authored = {
            "name": "DOGI Multi-Agent Productivity Suite",
            "description": "stale",
            "startDate": "2020-01",
            "highlights": ["stale"],
        }
        profile = profile_dict(
            {
                "basics": {"name": "Test"},
                "work": [_role_with_foci()],
                "projects": [authored],
            }
        )
        projected = project_profile(profile)
        names = [item["name"] for item in projected["projects"]]
        self.assertEqual(names.count("DOGI Multi-Agent Productivity Suite"), 1)
        dogi = next(
            item
            for item in projected["projects"]
            if item["name"] == "DOGI Multi-Agent Productivity Suite"
        )
        self.assertEqual(dogi["description"], "Internal productivity agents.")
        self.assertEqual(dogi["keywords"], ["Multi-Agent System"])
        self.assertIn(
            "Developed Departmental Internal AI Agents with Google ADK.",
            dogi["highlights"],
        )
        self.assertIn(
            "Designed session persistence and storage strategy using Redis/Postgres.",
            dogi["highlights"],
        )
        self.assertNotIn(
            "Designed session persistence and storage strategy using Redis/Postgres.",
            projected["work"][0]["highlights"],
        )

    def test_public_resume_strips_archive_claims_and_constraints(self):
        profile = project_profile(
            profile_dict({"basics": {"name": "Test"}, "work": [_role_with_foci()]})
        )
        public = for_public_resume(profile)
        self.assertNotIn("evidence", public["work"][0])
        layers = [
            claim["layer"]
            for focus in public["work"][0]["foci"]
            for claim in focus["claims"]
        ]
        self.assertEqual(set(layers), {"public"})
        self.assertTrue(
            all("do_not_claim" not in claim for focus in public["work"][0]["foci"] for claim in focus["claims"])
        )

    def test_japanese_uses_claim_text_ja_and_axis(self):
        profile = project_profile(
            profile_dict({"basics": {"name": "Test"}, "work": [_role_with_foci()]})
        )
        localized = localize_profile(profile, "ja")
        self.assertEqual(
            localized["work"][0]["highlights"][0],
            "Google ADKで部門内AIエージェントを開発。",
        )
        self.assertEqual(localized["work"][0]["highlight_axes"][0], "社内エージェント")


class ProfileWithFociTest(unittest.TestCase):
    def test_profile_model_accepts_foci_without_highlights(self):
        profile = Profile.model_validate(
            {"basics": {"name": "Test"}, "work": [_role_with_foci()]}
        )
        self.assertEqual(len(profile.work[0].foci), 4)
        self.assertEqual(profile.work[0].highlights, [])


if __name__ == "__main__":
    unittest.main()
