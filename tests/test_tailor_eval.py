import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from src.ai import HighlightSelection, TailoringPlan, assemble_profile
from src.compose import GroundedTailoringPlan, RoleBullets, assemble_composed_profile
from src.generator import Jinja2Generator
from src.i18n import JA_DISPLAY_NAME_ALIAS, localize_profile
from src.loader import YamlDataLoader
from src.pdf import PdfRenderError, assert_one_page, count_pdf_pages
from src.tailor_eval import (
    evaluate_case,
    index_by_name,
    load_case,
    load_live_fragments,
    main,
    scan_rendered,
)


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DIR = ROOT / "tests" / "tailor_eval" / "profiles" / "synthetic"
CASES_DIR = ROOT / "tests" / "tailor_eval" / "cases"
TEMPLATES_DIR = ROOT / "templates"


def load_synthetic():
    return YamlDataLoader(str(SYNTHETIC_DIR)).load()


def load_named_case(stem: str):
    return load_case(CASES_DIR / f"{stem}.yaml")


def good_plan(source):
    northwind = index_by_name(source["work"], "Northwind Robotics")
    contoso = index_by_name(source["work"], "Contoso Financial")
    harbor = index_by_name(source["projects"], "Harbor Coach")
    genai = index_by_name(source["skills"], "Generative AI & NLP")
    language = index_by_name(source["skills"], "Language")
    cloud = index_by_name(source["certificates"], "Cloud Practitioner")
    return TailoringPlan(
        work=[northwind, contoso],
        projects=[harbor],
        skills=[genai, language],
        certificates=[cloud],
        work_highlights=[
            HighlightSelection(item_index=northwind, highlight_indices=[0, 1, 2]),
        ],
    )


def render_real_templates(tailored, language="en"):
    gen = Jinja2Generator(str(TEMPLATES_DIR), language=language)
    return {
        "resume.md.j2": gen.render(tailored, "resume.md.j2"),
        "resume.html.j2": gen.render(tailored, "resume.html.j2"),
        "resume_bible.html.j2": gen.render(tailored, "resume_bible.html.j2"),
    }


def highlight_index(item, fragment):
    matches = [i for i, text in enumerate(item["highlights"]) if fragment in text]
    if len(matches) != 1:
        raise ValueError(f"highlight {fragment!r} matched {len(matches)} items")
    return matches[0]


def live_platform_plan(source):
    """Hand-written one-page plan matching the Platform / ly00161 quality bar."""

    cookpad = index_by_name(source["work"], "Cookpad")
    cathay = index_by_name(source["work"], "Cathay Financial Holdings")
    wisers = index_by_name(source["work"], "Wisers Information Limited")
    cookpad_item = source["work"][cookpad]
    cathay_item = source["work"][cathay]
    wisers_item = source["work"][wisers]
    return TailoringPlan(
        work=[cookpad, cathay, wisers],
        projects=[],
        skills=[
            index_by_name(source["skills"], "Cloud & Infra"),
            index_by_name(source["skills"], "MLOps & Deployment"),
            index_by_name(source["skills"], "Programming & ML Frameworks"),
            index_by_name(source["skills"], "Generative AI & NLP"),
            index_by_name(source["skills"], "Data Engineering"),
            index_by_name(source["skills"], "Language"),
        ],
        certificates=[
            index_by_name(source["certificates"], "AWS Certified Machine Learning - Specialty"),
            index_by_name(source["certificates"], "AWS Certified Cloud Practitioner"),
        ],
        work_highlights=[
            HighlightSelection(
                item_index=cookpad,
                highlight_indices=[
                    highlight_index(cookpad_item, "40%"),
                    highlight_index(cookpad_item, "staged pipeline"),
                    highlight_index(cookpad_item, "Capability-based evals"),
                ],
            ),
            HighlightSelection(
                item_index=cathay,
                highlight_indices=[
                    highlight_index(cathay_item, "AI Gateway"),
                    highlight_index(cathay_item, "cloud spend by 40%"),
                    highlight_index(cathay_item, "2 hours to 15 minutes"),
                    highlight_index(cathay_item, "0.67 to 0.89"),
                ],
            ),
            HighlightSelection(
                item_index=wisers,
                highlight_indices=[
                    highlight_index(wisers_item, "2 weeks to 3 days"),
                    highlight_index(wisers_item, "70% internal adoption"),
                ],
            ),
        ],
    )


def _pdf_with_page_count(pages: int) -> bytes:
    kids = " ".join(f"{index + 3} 0 R" for index in range(pages))
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        f"2 0 obj << /Type /Pages /Kids [{kids}] /Count {pages} >> endobj",
    ]
    for index in range(pages):
        objects.append(
            f"{index + 3} 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj"
        )
    return ("\n".join(["%PDF-1.1", *objects, "trailer << /Root 1 0 R >>", "%%EOF"]) + "\n").encode()


def fail_findings(report):
    return [finding for rec in report.records for finding in rec.findings if finding.severity == "fail"]


class TailorEvalTest(unittest.TestCase):
    def test_real_templates_good_plan_has_zero_fail_findings(self):
        source = load_synthetic()
        plan = good_plan(source)
        tailored = assemble_profile(source, plan)
        rendered = render_real_templates(tailored)
        report = evaluate_case(
            load_named_case("agent_eval_platform"),
            source=source,
            tailored=tailored,
            plan=plan,
            rendered=rendered,
        )
        self.assertEqual(fail_findings(report), [])
        self.assertIn("Senior AI Engineer at Northwind Robotics", rendered["resume.md.j2"])
        self.assertIn("([Link](", rendered["resume.md.j2"])
        self.assertNotIn("67.6%", rendered["resume.html.j2"])
        self.assertIn("67.6%", rendered["resume_bible.html.j2"])
        self.assertTrue(report.passed)
        self.assertIn("Languages:", rendered["resume.html.j2"])

    def test_hostile_plan_including_excluded_work_fails_identity(self):
        source = load_synthetic()
        plan = TailoringPlan(
            work=[
                index_by_name(source["work"], "Northwind Robotics"),
                index_by_name(source["work"], "Contoso Financial"),
                index_by_name(source["work"], "Legacy Retail Analytics"),
            ],
            projects=[index_by_name(source["projects"], "Harbor Coach")],
        )
        tailored = assemble_profile(source, plan)
        report = evaluate_case(
            load_named_case("agent_eval_platform"),
            source=source,
            tailored=tailored,
            plan=plan,
            rendered=render_real_templates(tailored),
        )
        codes = {finding.code for finding in fail_findings(report)}
        self.assertIn("identity_gate", codes)
        self.assertFalse(report.passed)

    def test_hostile_plan_dropping_must_include_fails_identity(self):
        source = load_synthetic()
        plan = TailoringPlan(
            work=[index_by_name(source["work"], "Contoso Financial")],
            projects=[index_by_name(source["projects"], "Harbor Coach")],
        )
        tailored = assemble_profile(source, plan)
        report = evaluate_case(
            load_named_case("agent_eval_platform"),
            source=source,
            tailored=tailored,
            plan=plan,
            rendered=render_real_templates(tailored),
        )
        codes = {finding.code for finding in fail_findings(report)}
        self.assertIn("identity_gate", codes)
        self.assertFalse(report.passed)

    def test_mutated_highlight_after_assemble_fails_verbatim(self):
        source = load_synthetic()
        plan = good_plan(source)
        tailored = assemble_profile(source, plan)
        original = tailored["work"][0]["highlights"][0]
        tailored["work"][0]["highlights"][0] = original.replace("95%", "99%")
        rendered = render_real_templates(tailored)
        report = evaluate_case(
            load_named_case("agent_eval_platform"),
            source=source,
            tailored=tailored,
            plan=plan,
            rendered=rendered,
        )
        codes = {finding.code for finding in fail_findings(report)}
        self.assertTrue(codes & {"ungrounded_number", "verbatim_highlight"})
        self.assertFalse(report.passed)

    def test_scan_rendered_ignores_bible_bytes(self):
        source = load_synthetic()
        plan = good_plan(source)
        tailored = assemble_profile(source, plan)
        rendered = render_real_templates(tailored)
        public_only = {
            "resume.md.j2": rendered["resume.md.j2"],
            "resume.html.j2": rendered["resume.html.j2"],
            "resume_bible.html.j2": "Moment team 67.6%",
        }
        findings = scan_rendered(source, tailored, public_only)
        self.assertEqual([item for item in findings if item.code == "evidence_leak"], [])

    def test_public_highlights_do_not_contain_internal_evidence(self):
        source = load_synthetic()
        northwind = source["work"][index_by_name(source["work"], "Northwind Robotics")]
        public = " ".join(northwind["highlights"])
        self.assertIn("67.6%", " ".join(northwind["evidence"]))
        self.assertIn("Moment team", " ".join(northwind["evidence"]))
        self.assertNotIn("67.6%", public)
        self.assertNotIn("Moment team", public)

    def test_index_by_name_requires_unique_match(self):
        source = load_synthetic()
        self.assertEqual(source["work"][index_by_name(source["work"], "Northwind Robotics")]["name"], "Northwind Robotics")
        with self.assertRaisesRegex(ValueError, "matched 0"):
            index_by_name(source["work"], "Missing Co")

    def test_offline_main_validates_committed_cases(self):
        with patch("sys.stdout", StringIO()):
            self.assertEqual(main([]), 0)

    def test_offline_main_missing_cases_dir_exits_2(self):
        with patch("sys.stderr", StringIO()):
            self.assertEqual(main(["--cases", str(ROOT / "does-not-exist")]), 2)

    def test_live_fragments_file_parses(self):
        fragments = load_live_fragments()
        self.assertIn("67.6%", fragments)
        self.assertIn("Moment team", fragments)

    def test_travel_search_good_plan_passes_identity(self):
        source = load_synthetic()
        plan = TailoringPlan(
            work=[index_by_name(source["work"], "TripNorth Analytics")],
            work_highlights=[
                HighlightSelection(
                    item_index=index_by_name(source["work"], "TripNorth Analytics"),
                    highlight_indices=[0, 1, 2],
                )
            ],
        )
        tailored = assemble_profile(source, plan)
        report = evaluate_case(
            load_named_case("travel_search_ic"),
            source=source,
            tailored=tailored,
            plan=plan,
            rendered=render_real_templates(tailored),
        )
        self.assertEqual(fail_findings(report), [])
        self.assertTrue(report.passed)
        self.assertEqual(report.records[0].quality["role_match"], 1.0)

    def test_cathay_compose_prefers_f1_retry_over_discovery_pick(self):
        """Old pick path could choose the discovery highlight instead of F1/retry.

        Compose writes grounded production sentences from the same role facts.
        """

        source = YamlDataLoader(str(ROOT / "data")).load()
        cathay = index_by_name(source["work"], "Cathay Financial Holdings")
        discovery = source["work"][cathay]["highlights"][highlight_index(
            source["work"][cathay], "mapped the client's regulatory-comparison"
        )]
        plan = GroundedTailoringPlan(
            work=[cathay],
            work_bullets=[
                RoleBullets(
                    item_index=cathay,
                    bullets=[
                        "Improved regulatory Agent F1 from 0.67 to 0.89; adopted by 2 of 5 subsidiaries.",
                        "Regulatory pipeline: per-record processing status; max 3 retries with increasing wait; after 3 failures mark failed and retry the next day.",
                        "DS built the PoC, and I handled production readiness as a Databricks deployment workflow, storing related data on the Databricks data layer.",
                    ],
                )
            ],
        )
        tailored = assemble_composed_profile(source, plan)
        rendered = render_real_templates(tailored)
        report = evaluate_case(
            load_named_case("cathay_compose"),
            source=source,
            tailored=tailored,
            plan=plan,
            rendered=rendered,
        )
        self.assertEqual(fail_findings(report), [])
        self.assertTrue(report.passed)
        page = rendered["resume.html.j2"]
        self.assertIn("0.67", page)
        self.assertIn("0.89", page)
        self.assertIn("3 retries", page)
        self.assertNotIn("Unity Catalog", page)
        self.assertNotIn("67.6", page)
        self.assertNotIn(discovery, page)

    def test_composed_invented_spark_or_unity_catalog_fails_eval(self):
        source = YamlDataLoader(str(ROOT / "data")).load()
        cathay = index_by_name(source["work"], "Cathay Financial Holdings")
        plan = GroundedTailoringPlan(
            work=[cathay],
            work_bullets=[
                RoleBullets(
                    item_index=cathay,
                    bullets=["Ran Spark jobs over 2 TB at 800 QPS on Unity Catalog and Delta."],
                )
            ],
        )
        tailored = assemble_composed_profile(source, plan, ground=False)
        report = evaluate_case(
            load_named_case("cathay_compose"),
            source=source,
            tailored=tailored,
            plan=plan,
            rendered=render_real_templates(tailored),
        )
        codes = {finding.code for finding in fail_findings(report)}
        self.assertTrue(
            codes
            & {
                "invented_product",
                "ungrounded_name",
                "ungrounded_number",
                "must_include_composed_fragments",
            }
        )
        self.assertFalse(report.passed)

    def test_composed_invented_f1_causality_fails_eval(self):
        source = YamlDataLoader(str(ROOT / "data")).load()
        cathay = index_by_name(source["work"], "Cathay Financial Holdings")
        plan = GroundedTailoringPlan(
            work=[cathay],
            work_bullets=[
                RoleBullets(
                    item_index=cathay,
                    bullets=[
                        "Improved regulatory Agent F1 from 0.67 to 0.89, which led to adoption by 2 of 5 subsidiaries."
                    ],
                )
            ],
        )
        tailored = assemble_composed_profile(source, plan, ground=False)
        report = evaluate_case(
            load_named_case("cathay_compose"),
            source=source,
            tailored=tailored,
            plan=plan,
            rendered=render_real_templates(tailored),
        )
        codes = {finding.code for finding in fail_findings(report)}
        self.assertIn("invented_causality", codes)
        self.assertFalse(report.passed)

    def test_composed_cookpad_internal_bench_does_not_reach_the_page(self):
        source = YamlDataLoader(str(ROOT / "data")).load()
        cookpad = index_by_name(source["work"], "Cookpad")
        tailored = assemble_composed_profile(
            source,
            GroundedTailoringPlan(
                work=[cookpad],
                work_bullets=[
                    RoleBullets(
                        item_index=cookpad,
                        bullets=[
                            "Raised the internal coaching eval from 67.6% to 83.0% with 20 users."
                        ],
                    )
                ],
            ),
            ground=False,
        )
        rendered = render_real_templates(tailored)
        findings = scan_rendered(
            source,
            tailored,
            {
                "resume.md.j2": rendered["resume.md.j2"],
                "resume.html.j2": rendered["resume.html.j2"],
            },
        )
        codes = {item.code for item in findings if item.severity == "fail"}
        self.assertIn("unpublished_token", codes)
        self.assertIn("67.6%", rendered["resume.html.j2"])
        self.assertNotIn("67.6%", " ".join(source["work"][cookpad]["highlights"]))


class JapaneseConciseHarnessTest(unittest.TestCase):
    """Offline --language ja path: assemble, localize, same concise template."""

    def test_handwritten_plan_language_ja_renders_headings_and_source_numbers(self):
        source = YamlDataLoader(str(ROOT / "data")).load()
        plan = live_platform_plan(source)
        tailored = assemble_profile(source, plan)
        localized = localize_profile(tailored, "ja")
        html = Jinja2Generator(str(TEMPLATES_DIR), language="ja").render(
            localized, "resume.html.j2"
        )

        for heading in ("職務経歴書", "職務要約", "活かせる経験・スキル", "職務経歴", "学歴", "資格"):
            self.assertIn(heading, html)
        self.assertIn(JA_DISPLAY_NAME_ALIAS, html)
        self.assertIn("中国語（母語）", html)
        self.assertIn("英語（限定的な実務）", html)
        self.assertIn("40%", html)
        self.assertIn("95%", html)
        self.assertIn("60%", html)
        self.assertIn("40%", html)
        self.assertIn("0.67", html)
        self.assertIn("0.89", html)
        self.assertIn("30+", html)
        self.assertIn("70%", html)
        self.assertIn("90%", html)
        self.assertIn("エージェント", html)
        self.assertIn("パイプライン", html)
        self.assertIn("評価", html)
        self.assertIn("AI Gateway", html)
        self.assertIn("FinOps", html)
        self.assertIn("社内エージェント", html)
        self.assertIn("規制エージェント", html)
        self.assertIn("テンプレート", html)
        self.assertIn("ライブラリ", html)
        self.assertNotIn("Fluent", html)
        self.assertNotIn("LiteLLM", html)
        self.assertNotIn("ビジネス日本語", html)
        self.assertNotIn("TripSaaS", html)
        self.assertNotIn("67.6", html)
        self.assertNotIn("Sphinx", html)
        self.assertNotRegex(html, r"日本語.{0,12}(Fluent|N1)")

    def test_language_ja_keeps_english_numbers_from_source_highlights(self):
        source = YamlDataLoader(str(ROOT / "data")).load()
        tailored = assemble_profile(source, live_platform_plan(source))
        html = Jinja2Generator(str(TEMPLATES_DIR), language="ja").render(
            localize_profile(tailored, "ja"), "resume.html.j2"
        )
        english = " ".join(
            highlight
            for item in tailored["work"]
            for highlight in item["highlights"]
        )
        self.assertIn("2 hours to 15 minutes", english)
        self.assertIn("2週間から3日", html)
        self.assertIn("15分", html)

    def test_one_page_pdf_gate_is_documented_and_fails_when_not_one_page(self):
        """After PDF render, the job must fail unless page count == 1.

        CI does not require Chrome. This test documents the gate used by
        ``src.main`` when ``--language ja`` renders a PDF: ``assert_one_page``
        accepts a one-page PDF and raises on any other count.
        """

        self.assertEqual(count_pdf_pages(_pdf_with_page_count(1)), 1)
        self.assertEqual(assert_one_page(_pdf_with_page_count(1)), 1)
        with self.assertRaisesRegex(PdfRenderError, "exactly 1 page"):
            assert_one_page(_pdf_with_page_count(2))


if __name__ == "__main__":
    unittest.main()
