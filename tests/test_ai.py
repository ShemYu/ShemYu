import copy
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from src.ai import (
    DEFAULT_PROVIDER,
    DEFAULT_XAI_MODEL,
    PROMPT_INSTRUCTIONS,
    XAI_BASE_URL,
    XAI_TIMEOUT_S,
    HighlightSelection,
    OpenAIAgentProvider,
    TailoringPlan,
    TailorTransportError,
    XAIChatProvider,
    assemble_profile,
    build_provider,
    public_selectable_profile,
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
                "evidence": [
                    "Internal only: 67.6% to 83.0% on a 15-case benchmark.",
                    "Do not claim outbound: Moment team.",
                ],
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
                "evidence": ["Project-only internal note 67.6%"],
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
        self.assertEqual(tailored["work"][0]["evidence"], original["work"][0]["evidence"])
        self.assertEqual(
            tailored["projects"][0]["evidence"], original["projects"][0]["evidence"]
        )
        self.assertEqual(tailored["skills"], [original["skills"][1]])
        self.assertEqual(profile_dict(profile), original)
        tailored["basics"]["name"] = "Changed locally"
        self.assertEqual(profile["basics"]["name"], "Source Name")

    def test_public_selectable_profile_strips_evidence_without_mutating_source(self):
        profile = _profile()
        original_work_evidence = list(profile["work"][0]["evidence"])
        original_project_evidence = list(profile["projects"][0]["evidence"])

        pub = public_selectable_profile(profile)

        self.assertEqual(set(pub), {"work", "projects", "skills", "certificates", "publications"})
        self.assertNotIn("evidence", pub["work"][0])
        self.assertNotIn("evidence", pub["projects"][0])
        self.assertEqual(profile["work"][0]["evidence"], original_work_evidence)
        self.assertEqual(profile["projects"][0]["evidence"], original_project_evidence)

    def test_unselected_highlights_are_limited_to_three(self):
        tailored = assemble_profile(_profile(), TailoringPlan(work=[0]))
        self.assertEqual(
            tailored["work"][0]["highlights"], ["First fact", "Second fact", "Third fact"]
        )

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
        self.assertNotIn("67.6%", prompt)
        self.assertNotIn("Moment team", prompt)
        self.assertNotIn('"evidence"', prompt)

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

    def test_last_usage_is_none_without_runner_usage(self):
        provider = self._provider(TailoringPlan(work=[0]))
        provider.tailor_profile(_profile(), "ML platform engineer")
        self.assertIsNone(provider.last_usage)
        self.assertIsInstance(provider.last_elapsed_s, float)
        self.assertGreaterEqual(provider.last_elapsed_s, 0)

    def test_last_usage_from_runner_result(self):
        usage = SimpleNamespace(input_tokens=10, output_tokens=4, total_tokens=14)
        provider = self._provider(TailoringPlan(work=[0]))
        self.runner_mock.return_value = SimpleNamespace(
            final_output=TailoringPlan(work=[0]),
            context_wrapper=SimpleNamespace(usage=usage),
        )
        provider.tailor_profile(_profile(), "ML platform engineer")
        self.assertEqual(
            provider.last_usage,
            {
                "prompt_tokens": 10,
                "completion_tokens": 4,
                "total_tokens": 14,
            },
        )


class BuildProviderTest(unittest.TestCase):
    def test_default_provider_is_openai(self):
        self.assertEqual(DEFAULT_PROVIDER, "openai")
        with patch("src.ai.load_dotenv"):
            with patch.dict(os.environ, {}, clear=True):
                with patch("src.ai.OpenAIAgentProvider") as provider_cls:
                    instance = provider_cls.return_value
                    result = build_provider()
        provider_cls.assert_called_once_with(None)
        self.assertIs(result, instance)

    def test_dotenv_tailor_provider_is_visible_to_factory(self):
        def load_env(**_kwargs):
            os.environ["TAILOR_PROVIDER"] = "xai"

        with patch.dict(os.environ, {}, clear=True):
            with patch("src.ai.load_dotenv", side_effect=load_env) as load_env_mock:
                with patch("src.ai.XAIChatProvider") as provider_cls:
                    instance = provider_cls.return_value
                    result = build_provider()
        load_env_mock.assert_called_once_with(override=False)
        provider_cls.assert_called_once_with(None)
        self.assertIs(result, instance)

    def test_name_and_model_are_passed_through(self):
        with patch("src.ai.load_dotenv"):
            with patch.dict(os.environ, {"TAILOR_PROVIDER": "xai"}, clear=True):
                with patch("src.ai.OpenAIAgentProvider") as provider_cls:
                    build_provider("openai", "gpt-test")
        provider_cls.assert_called_once_with("gpt-test")

    def test_env_selects_openai(self):
        with patch("src.ai.load_dotenv"):
            with patch.dict(os.environ, {"TAILOR_PROVIDER": "OpenAI"}, clear=True):
                with patch("src.ai.OpenAIAgentProvider") as provider_cls:
                    build_provider()
        provider_cls.assert_called_once_with(None)

    def test_xai_name_selects_xai_provider(self):
        with patch("src.ai.load_dotenv"):
            with patch.dict(os.environ, {}, clear=True):
                with patch("src.ai.XAIChatProvider") as provider_cls:
                    instance = provider_cls.return_value
                    result = build_provider("xai", "grok-test")
        provider_cls.assert_called_once_with("grok-test")
        self.assertIs(result, instance)

    def test_env_selects_xai(self):
        with patch("src.ai.load_dotenv"):
            with patch.dict(os.environ, {"TAILOR_PROVIDER": "XAI"}, clear=True):
                with patch("src.ai.XAIChatProvider") as provider_cls:
                    build_provider()
        provider_cls.assert_called_once_with(None)

    def test_unknown_provider_raises(self):
        with patch("src.ai.load_dotenv"):
            with self.assertRaisesRegex(ValueError, r"Unknown tailoring provider: grok"):
                build_provider("grok")


def _xai_status_error(status_code: int):
    import httpx
    from openai import APIStatusError

    request = httpx.Request("POST", "https://api.x.ai/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return APIStatusError("error", response=response, body=None)


def _xai_timeout_error():
    import httpx
    from openai import APITimeoutError

    return APITimeoutError(
        request=httpx.Request("POST", "https://api.x.ai/v1/chat/completions")
    )


def _xai_connection_error():
    import httpx
    from openai import APIConnectionError

    return APIConnectionError(
        request=httpx.Request("POST", "https://api.x.ai/v1/chat/completions")
    )


class XAIChatProviderTest(unittest.TestCase):
    def _provider(
        self,
        parsed=None,
        content=None,
        usage=None,
        parse_error=None,
        extra_env=None,
        model_name=None,
    ):
        dotenv_patch = patch("src.ai.load_dotenv")
        dotenv_patch.start()
        self.addCleanup(dotenv_patch.stop)
        env = {"XAI_API_KEY": "test-key"}
        if extra_env:
            env.update(extra_env)
        env_patch = patch.dict(os.environ, env, clear=True)
        env_patch.start()
        self.addCleanup(env_patch.stop)

        mock_client = MagicMock()
        if parse_error is not None:
            mock_client.beta.chat.completions.parse.side_effect = parse_error
        else:
            message = SimpleNamespace(parsed=parsed, content=content)
            mock_client.beta.chat.completions.parse.return_value = SimpleNamespace(
                choices=[SimpleNamespace(message=message)],
                usage=usage,
            )
        openai_patch = patch("src.ai.OpenAI", return_value=mock_client)
        self.openai_cls = openai_patch.start()
        self.addCleanup(openai_patch.stop)
        self.parse_mock = mock_client.beta.chat.completions.parse
        return XAIChatProvider(model_name)

    def test_client_uses_xai_base_url_timeout_and_default_model(self):
        provider = self._provider(parsed=TailoringPlan(work=[0]))
        self.assertEqual(provider.model_name, DEFAULT_XAI_MODEL)
        self.assertEqual(DEFAULT_XAI_MODEL, "grok-4.6")
        self.openai_cls.assert_called_once_with(
            api_key="test-key",
            base_url=XAI_BASE_URL,
            timeout=XAI_TIMEOUT_S,
        )
        self.assertEqual(XAI_TIMEOUT_S, 180.0)
        self.assertEqual(XAI_BASE_URL, "https://api.x.ai/v1")

    def test_parse_uses_structured_plan_low_reasoning_and_strips_evidence(self):
        plan = TailoringPlan(
            work=[0],
            projects=[0],
            work_highlights=[HighlightSelection(item_index=0, highlight_indices=[0])],
        )
        provider = self._provider(parsed=plan)
        result = provider.tailor_profile(_profile(), "ML platform engineer")

        self.parse_mock.assert_called_once()
        kwargs = self.parse_mock.call_args.kwargs
        self.assertEqual(kwargs["model"], "grok-4.6")
        self.assertEqual(kwargs["temperature"], 0)
        self.assertEqual(kwargs["extra_body"], {"reasoning_effort": "low"})
        self.assertIs(kwargs["response_format"], TailoringPlan)
        messages = kwargs["messages"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], PROMPT_INSTRUCTIONS)
        user_prompt = messages[1]["content"]
        self.assertIn("First Company", user_prompt)
        self.assertNotIn("67.6%", user_prompt)
        self.assertNotIn("Moment team", user_prompt)
        self.assertNotIn('"evidence"', user_prompt)
        self.assertEqual(result["work"][0]["highlights"], ["First fact"])
        self.assertEqual(result["education"], profile_dict(_profile())["education"])

    def test_parsed_none_with_json_content_falls_back(self):
        content = TailoringPlan(work=[0], projects=[0]).model_dump_json()
        provider = self._provider(parsed=None, content=content)
        result = provider.tailor_profile(_profile(), "ML platform engineer")
        self.assertEqual(result["work"][0]["name"], "First Company")
        self.assertEqual(result["projects"][0]["name"], "Selected Project")

    def test_parsed_none_with_garbage_content_fails_closed(self):
        provider = self._provider(parsed=None, content="not-json")
        with self.assertRaisesRegex(ValueError, "xAI returned an invalid TailoringPlan"):
            provider.tailor_profile(_profile(), "ML platform engineer")

    def test_parsed_none_without_content_fails_closed(self):
        provider = self._provider(parsed=None, content=None)
        with self.assertRaisesRegex(ValueError, "xAI returned an invalid TailoringPlan"):
            provider.tailor_profile(_profile(), "ML platform engineer")

    def test_last_usage_from_completion(self):
        usage = SimpleNamespace(
            prompt_tokens=11,
            completion_tokens=5,
            total_tokens=16,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=3),
        )
        provider = self._provider(parsed=TailoringPlan(work=[0]), usage=usage)
        provider.tailor_profile(_profile(), "ML platform engineer")
        self.assertEqual(
            provider.last_usage,
            {
                "prompt_tokens": 11,
                "completion_tokens": 5,
                "total_tokens": 16,
                "reasoning_tokens": 3,
            },
        )
        self.assertIsInstance(provider.last_elapsed_s, float)
        self.assertGreaterEqual(provider.last_elapsed_s, 0)

    def test_timeout_is_transport_error(self):
        provider = self._provider(parse_error=_xai_timeout_error())
        with self.assertRaises(TailorTransportError):
            provider.tailor_profile(_profile(), "ML platform engineer")

    def test_connection_failure_is_transport_error(self):
        provider = self._provider(parse_error=_xai_connection_error())
        with self.assertRaises(TailorTransportError):
            provider.tailor_profile(_profile(), "ML platform engineer")

    def test_http_429_is_transport_error(self):
        provider = self._provider(parse_error=_xai_status_error(429))
        with self.assertRaises(TailorTransportError):
            provider.tailor_profile(_profile(), "ML platform engineer")

    def test_http_500_is_transport_error(self):
        provider = self._provider(parse_error=_xai_status_error(500))
        with self.assertRaises(TailorTransportError):
            provider.tailor_profile(_profile(), "ML platform engineer")

    def test_schema_4xx_is_invalid_plan(self):
        provider = self._provider(parse_error=_xai_status_error(400))
        with self.assertRaisesRegex(ValueError, "xAI returned an invalid TailoringPlan"):
            provider.tailor_profile(_profile(), "ML platform engineer")

    def test_empty_jd_is_rejected_before_parse(self):
        provider = self._provider()
        with self.assertRaises(ValueError):
            provider.tailor_profile(_profile(), "  ")
        self.parse_mock.assert_not_called()

    def test_empty_source_work_is_rejected_before_parse(self):
        provider = self._provider()
        empty_profile = _profile()
        empty_profile["work"] = []
        with self.assertRaises(ValueError):
            provider.tailor_profile(empty_profile, "ML platform engineer")
        self.parse_mock.assert_not_called()

    def test_missing_key_is_rejected_before_client(self):
        with patch("src.ai.load_dotenv"):
            with patch.dict(os.environ, {}, clear=True):
                with patch("src.ai.OpenAI") as openai_cls:
                    with self.assertRaisesRegex(RuntimeError, "XAI_API_KEY"):
                        XAIChatProvider()
                    openai_cls.assert_not_called()

    def test_generate_highlight_returns_source_summary(self):
        provider = self._provider()
        self.assertEqual(
            provider.generate_highlight(_profile()),
            "Source summary that must not be rewritten.",
        )
        self.parse_mock.assert_not_called()

    def test_model_env_and_argument_override(self):
        provider = self._provider(extra_env={"XAI_MODEL": "grok-from-env"})
        self.assertEqual(provider.model_name, "grok-from-env")
        named = self._provider(
            extra_env={"XAI_MODEL": "grok-from-env"},
            model_name="grok-from-arg",
        )
        self.assertEqual(named.model_name, "grok-from-arg")


if __name__ == "__main__":
    unittest.main()
