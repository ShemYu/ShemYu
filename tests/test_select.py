import unittest

from src.select import apply_selection


class ApplySelectionTest(unittest.TestCase):
    def test_reorders_work_and_copies_source_highlights_only(self):
        profile = {
            "work": [
                {
                    "name": "Cookpad",
                    "highlights": ["agent", "eval", "pipeline"],
                    "evidence": ["internal"],
                },
                {
                    "name": "Wisers Information Limited",
                    "highlights": ["templates", "uap", "sphinx"],
                },
            ],
            "skills": [
                {"name": "Cloud & Infra", "keywords": ["AWS", "AI Gateway"]},
                {"name": "Generative AI & NLP", "keywords": ["RAG", "LLM"]},
                {"name": "Language", "keywords": ["Chinese (Native)"]},
            ],
            "certificates": [
                {"name": "AWS Certified Cloud Practitioner"},
                {"name": "AWS Cloud Quest: Cloud Practitioner"},
            ],
            "publications": [{"name": "Keep out"}],
            "projects": [{"name": "Harbor", "highlights": ["skip me"]}],
            "education": [{"name": "Ming Chuan University", "institution": "MCU"}],
        }
        result = apply_selection(
            profile,
            {
                "meta": {"axis": "Agent / GenAI", "output_name": "demo"},
                "work": [
                    {"name": "Cookpad", "highlight_indices": [0, 1]},
                    {"name": "Wisers Information Limited", "highlight_indices": [1]},
                ],
                "skills": ["Generative AI & NLP", "Language"],
                "certificates_exclude_substrings": ["Cloud Quest"],
                "include_publications": False,
                "include_projects": False,
                "skill_keyword_limit": 7,
            },
        )
        self.assertEqual([item["name"] for item in result["work"]], ["Cookpad", "Wisers Information Limited"])
        self.assertEqual(result["work"][0]["highlights"], ["agent", "eval"])
        self.assertEqual(result["work"][1]["highlights"], ["uap"])
        self.assertEqual(result["work"][0]["evidence"], ["internal"])
        self.assertEqual([item["name"] for item in result["skills"]], ["Generative AI & NLP", "Language"])
        self.assertEqual([item["name"] for item in result["certificates"]], ["AWS Certified Cloud Practitioner"])
        self.assertEqual(result["publications"], [])
        self.assertEqual(result["projects"], [])
        self.assertEqual(result["selection_meta"]["axis"], "Agent / GenAI")

    def test_rejects_unknown_work_name_and_bad_index(self):
        profile = {"work": [{"name": "Cookpad", "highlights": ["only"]}]}
        with self.assertRaises(KeyError):
            apply_selection(profile, {"work": [{"name": "Missing", "highlight_indices": [0]}]})
        with self.assertRaises(IndexError):
            apply_selection(
                profile,
                {"work": [{"name": "Cookpad", "highlight_indices": [3]}]},
            )
