import copy
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError

from src.ai import (
    HighlightSelection,
    OpenAIAgentProvider,
    TailoringPlan,
    assemble_profile,
)
from src.generator import for_public_resume
from src.schema import profile_dict


def _profile():
    return {
        "basics": {
            "name": "Source Name",
            "summary": "Source summary that must not be rewritten.",
            "email": "source@example.com",
            "phone": "+886 900 000 000",
        },
        "work": [
            {
                "name": "First Company",
                "position": "ML Engineer",
                "startDate": "2022-01",
                "endDate": "Present",
                "highlights": ["First fact", "Second fact", "Third fact", "Fourth fact"],
            },
            {
                "name": "Second Company",
                "position": "Data Scientist",
                "startDate": "2020-01",
                "endDate": "2021-12",
                "highlights": ["Other fact"],
            },
        ],
        "education": [
            {
                "institution": "Source University",
                "area": "Computer Science",
                "studyType": "Master",
                "startDate": "2018",
                "endDate": "2020",
                "highlights": ["Education fact"],
            }
        ],
        "projects": [
            {
                "name": "Selected Project",
                "startDate": "2023-01",
                "endDate": "2023-06",
                "highlights": ["Project fact"],
            }
        ],
        "skills": [{"name": "Python", "keywords": ["Python"]}, {"name": "SQL", "keywords": ["SQL"]}],
        "certificates": [{"name": "Source Certificate"}],
        "publications": [{"name": "Source Publication"}],
    }


class TailoringPlanTest(unittest.TestCase):
    def test_rejects_duplicate_indices(self):
        with self.assertRaises(ValidationError):
            TailoringPlan(work=[0, 0])
        with self.assertRaises(ValidationError):
            TailoringPlan(
                work=[0],
                work_highlights=[HighlightSelection(item_index=0, highlight_indices=[1, 1])],
            )

    def test_assembler_rejects_out_of_range_indices(self):
        with self.assertRaises(ValueError):
            assemble_profile(_profile(), TailoringPlan(work=[0], skills=[2]))
        with self.assertRaises(ValueError):
            assemble_profile(
                _profile(),
                TailoringPlan(
                    work=[0],
                    work_highlights=[HighlightSelection(item_index=0, highlight_indices=[4])],
                ),
            )

    def test_assembler_copies_selected_source_and_preserves_facts(self):
        profile = _profile()
        original = copy.deepcopy(profile_dict(profile))
        plan = TailoringPlan(
            work=[0],
            work_highlights=[HighlightSelection(item_index=0, highlight_indices=[1])],
            projects=[0],
            skills=[1],
            certificates=[0],
            publications=[0],
        )

        tailored = assemble_profile(profile, plan)

        self.assertEqual(tailored["basics"], original["basics"])
        self.assertEqual(tailored["education"], original["education"])
        self.assertEqual(tailored["work"][0]["highlights"], ["Second fact"])
        self.assertEqual(tailored["skills"], [original["skills"][1]])
        self.assertEqual(profile_dict(profile), original)
        tailored["basics"]["name"] = "Changed locally"
        self.assertEqual(profile["basics"]["name"], "Source Name")

    def test_unselected_highlights_are_limited_to_three(self):
        tailored = assemble_profile(_profile(), TailoringPlan(work=[0]))
        self.assertEqual(
            tailored["work"][0]["highlights"], ["First fact", "Second fact", "Third fact"]
        )

    def test_plan_may_select_four_highlights_for_second_role_shape(self):
        profile = _profile()
        profile["work"][0]["highlights"] = ["A", "B", "C", "D"]
        tailored = assemble_profile(
            profile,
            TailoringPlan(
                work=[0],
                work_highlights=[HighlightSelection(item_index=0, highlight_indices=[0, 1, 2, 3])],
            ),
        )
        self.assertEqual(tailored["work"][0]["highlights"], ["A", "B", "C", "D"])

    def test_highlight_selection_on_unselected_item_fails(self):
        with self.assertRaises(ValueError):
            assemble_profile(
                _profile(),
                TailoringPlan(
                    work=[0],
                    work_highlights=[HighlightSelection(item_index=1, highlight_indices=[0])],
                ),
            )

    def test_empty_work_cannot_validate(self):
        with self.assertRaises(ValidationError):
            TailoringPlan(work=[])

    def test_assembled_items_retain_evidence_until_public_resume(self):
        profile = _profile()
        profile["work"][0]["evidence"] = ["internal metric 67.6%"]
        tailored = assemble_profile(profile, TailoringPlan(work=[0]))
        self.assertEqual(tailored["work"][0]["evidence"], ["internal metric 67.6%"])
        public = for_public_resume(tailored)
        self.assertNotIn("evidence", public["work"][0])
        self.assertEqual(public["work"][0]["highlights"], tailored["work"][0]["highlights"])


class OpenAIAgentProviderTest(unittest.TestCase):
    def _provider(self, runner_result=None, api_key="test-key"):
        dotenv_patch = patch("src.ai.load_dotenv")
        dotenv_patch.start()
        self.addCleanup(dotenv_patch.stop)
        env_patch = patch.dict(os.environ, {"OPENAI_API_KEY": api_key}, clear=True)
        env_patch.start()
        self.addCleanup(env_patch.stop)
        provider = OpenAIAgentProvider()
        if runner_result is not None:
            runner_patch = patch(
                "src.ai.Runner.run_sync",
                return_value=SimpleNamespace(final_output=runner_result),
            )
            self.runner_mock = runner_patch.start()
            self.addCleanup(runner_patch.stop)
        return provider

    def test_mock_runner_uses_structured_plan_and_model_default(self):
        provider = self._provider(
            TailoringPlan(
                work=[0],
                projects=[0],
                work_highlights=[HighlightSelection(item_index=0, highlight_indices=[0])],
            )
        )
        result = provider.tailor_profile(_profile(), "ML platform engineer")

        self.assertEqual(provider.model_name, "gpt-5.6-luna")
        self.assertEqual(
            result["work"][0]["highlights"], ["First fact"]
        )
        self.assertEqual(result["education"], profile_dict(_profile())["education"])

    def test_runner_prompt_contains_only_selectable_profile_sections(self):
        provider = self._provider(
            TailoringPlan(work=[0], projects=[0], skills=[0])
        )
        run_sync = self.runner_mock

        provider.tailor_profile(_profile(), "ML platform engineer")

        prompt = run_sync.call_args.args[1]
        self.assertIn("First Company", prompt)
        self.assertIn("Selected Project", prompt)
        self.assertIn("Python", prompt)
        self.assertIn("Source Certificate", prompt)
        self.assertIn("Source Publication", prompt)
        self.assertNotIn("source@example.com", prompt)
        self.assertNotIn("+886 900 000 000", prompt)
        self.assertNotIn("Source University", prompt)

    def test_empty_jd_is_rejected_before_runner(self):
        provider = self._provider()
        with patch("src.ai.Runner.run_sync") as run_sync:
            with self.assertRaises(ValueError):
                provider.tailor_profile(_profile(), "  ")
            run_sync.assert_not_called()

    def test_missing_key_is_rejected_without_runner(self):
        dotenv_patch = patch("src.ai.load_dotenv")
        dotenv_patch.start()
        self.addCleanup(dotenv_patch.stop)
        with patch.dict(os.environ, {}, clear=True):
            provider = OpenAIAgentProvider()
            with patch("src.ai.Runner.run_sync") as run_sync:
                with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
                    provider.tailor_profile(_profile(), "ML platform engineer")
                run_sync.assert_not_called()

    def test_empty_source_work_is_rejected_before_runner(self):
        provider = self._provider()
        empty_profile = _profile()
        empty_profile["work"] = []
        with patch("src.ai.Runner.run_sync") as run_sync:
            with self.assertRaises(ValueError):
                provider.tailor_profile(empty_profile, "ML platform engineer")
            run_sync.assert_not_called()

    def test_japanese_language_keeps_index_only_instructions_and_concise_shape(self):
        provider = self._provider()
        ja_provider = OpenAIAgentProvider(language="ja")
        self.assertIn("Return only zero-based indices", ja_provider.agent.instructions)
        self.assertIn("never write, rewrite", ja_provider.agent.instructions)
        self.assertIn("three newest roles", ja_provider.agent.instructions)
        self.assertIn("3/4/2", ja_provider.agent.instructions)
        self.assertNotIn("日本語", ja_provider.agent.instructions)
        self.assertIn("three bullets per selected item", provider.agent.instructions)


if __name__ == "__main__":
    unittest.main()
