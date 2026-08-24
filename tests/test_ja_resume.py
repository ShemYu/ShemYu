import unittest

from src.generator import Jinja2Generator
from src.i18n import translate_profile
from src.loader import YamlDataLoader
from src.select import apply_selection, load_selection


FORBIDDEN = (
    "Japanese Fluent",
    "日本語（Fluent",
    "日本語（N1",
    "N1",
    "ビジネス日本語",
    "ビジネス・ジャパニーズ",
    "67.6",
    "83.0",
    "7名",
    "LiteLLM",
    "distributed AI Gateway",
    "分散AI Gateway",
)


def render_ja(preset: str) -> str:
    spec = load_selection(preset)
    profile = apply_selection(YamlDataLoader("data").load(), spec)
    profile, _missing = translate_profile(profile, "ja")
    profile["generated_on"] = "2026年8月24日"
    profile["selection_meta"] = spec.get("meta") or {}
    return Jinja2Generator("templates").render(profile, "resume_ja.html.j2")


class JapaneseResumeContentTest(unittest.TestCase):
    def test_agent_resume_leads_with_cookpad_agent_facts(self):
        html = render_ja("ly_agent")
        self.assertIn("職務経歴書", html)
        self.assertIn("余顯漁（Shem Yu）", html)
        self.assertIn("ly00493", html)
        self.assertIn("Agent / GenAI", html)
        self.assertIn("Noto Sans JP", html)
        self.assertIn("Noto Sans CJK JP", html)
        self.assertNotIn("Helvetica", html)
        self.assertIn("マルチモーダル・コーチングエージェント", html)
        self.assertIn("40%", html)
        self.assertIn("95%", html)
        self.assertIn("エキスパート根拠", html)
        self.assertIn("バージョン管理された能力ベース", html)
        self.assertIn("段階的マルチモーダル推論パイプライン", html)
        self.assertIn("部門内AIエージェント", html)
        self.assertIn("0.67", html)
        self.assertIn("0.89", html)
        self.assertIn("4名", html)
        self.assertIn("UAP Common Library", html)
        self.assertIn("中国語（母語）", html)
        self.assertIn("英語（限定的な実務）", html)
        self.assertNotIn("2週間から3日", html)
        self.assertNotIn("AI Cloud Platformテンプレート", html)
        for token in FORBIDDEN:
            self.assertNotIn(token, html)
        self.assertNotIn("日本語", html)

    def test_platform_resume_emphasizes_wisers_and_cathay_infra(self):
        html = render_ja("ly_platform")
        self.assertIn("ly00161", html)
        self.assertIn("AI / ML Platform", html)
        self.assertIn("Noto Sans JP", html)
        self.assertIn("FastAPI", html)
        self.assertIn("Kubernetes", html)
        self.assertIn("2週間から3日", html)
        self.assertIn("30以上", html)
        self.assertIn("AI Gateway", html)
        self.assertIn("Guardrails", html)
        self.assertIn("MLflow", html)
        self.assertIn("40%", html)
        self.assertIn("段階的マルチモーダル推論パイプライン", html)
        self.assertIn("バージョン管理された能力ベース", html)
        self.assertIn("中国語（母語）", html)
        self.assertIn("英語（限定的な実務）", html)
        self.assertNotIn("エキスパート根拠のカバレッジを40%から95%", html)
        self.assertNotIn("部門内AIエージェント", html)
        for token in FORBIDDEN:
            self.assertNotIn(token, html)
        self.assertNotIn("日本語", html)

    def test_public_ja_template_strips_evidence(self):
        html = render_ja("ly_agent")
        self.assertNotIn("15-case", html)
        self.assertNotIn("103-unit", html)
        self.assertNotIn("evidence", html.lower())
