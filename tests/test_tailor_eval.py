import json
import os
import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.ai import HighlightSelection, TailorTransportError, TailoringPlan, assemble_profile
from src.generator import Jinja2Generator
from src.loader import YamlDataLoader
from src.tailor_eval import (
    classify_jd,
    evaluate_case,
    index_by_name,
    load_case,
    load_live_fragments,
    main,
    mean_pairwise_jaccard,
    quality_tokens,
    role_match,
    scan_rendered,
    score_quality,
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


def render_real_templates(tailored):
    gen = Jinja2Generator(str(TEMPLATES_DIR))
    return {
        "resume.md.j2": gen.render(tailored, "resume.md.j2"),
        "resume.html.j2": gen.render(tailored, "resume.html.j2"),
        "resume_bible.html.j2": gen.render(tailored, "resume_bible.html.j2"),
    }


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
        self.assertIn("verbatim_highlight", codes)
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

    def test_quality_tokens_drops_short_and_stoplist(self):
        tokens = quality_tokens("This team will work with Agents and NLP from 2026")
        self.assertEqual(tokens, {"agents", "2026"})

    def test_recency_is_one_when_n_work_leq_1(self):
        one = {"work": [{"name": "Only Co", "highlights": []}], "projects": [], "basics": {}}
        none = {"work": [], "projects": [], "basics": {}}
        self.assertEqual(score_quality(one, one, "engineer role")["recency"], 1.0)
        self.assertEqual(score_quality(none, none, "engineer role")["recency"], 1.0)

    def test_role_match_case_folded_first_match_wins_leadership_on_case_1_jd(self):
        case = load_named_case("agent_eval_platform")
        self.assertEqual(classify_jd(case.jd), "leadership")
        self.assertEqual(
            classify_jd("Leadership of a small ML team. Senior engineer."),
            "leadership",
        )
        self.assertEqual(classify_jd("senior engineer to implement production"), "ic")
        source = load_synthetic()
        tailored = assemble_profile(source, good_plan(source))
        # Contoso matches lead/team; Northwind does not.
        self.assertEqual(role_match(source, tailored, case.jd), 0.5)

    def test_mean_pairwise_jaccard(self):
        north_harbor = {"Northwind Robotics", "Harbor Coach"}
        north_contoso = {"Northwind Robotics", "Contoso Financial"}
        self.assertIsNone(mean_pairwise_jaccard([]))
        self.assertIsNone(mean_pairwise_jaccard([north_harbor]))
        self.assertAlmostEqual(
            mean_pairwise_jaccard([north_harbor, north_contoso, north_harbor]),
            5 / 9,
        )

    def test_live_unexpected_400_is_plan_error(self):
        class StatusError(Exception):
            def __init__(self, status_code: int) -> None:
                super().__init__(f"status {status_code}")
                self.status_code = status_code

        source = load_synthetic()
        case = load_named_case("agent_eval_platform")
        ai = MagicMock()
        ai.tailor_profile.side_effect = StatusError(400)
        ai.last_usage = None
        ai.last_elapsed_s = 0.01
        ai.model_name = "mock-model"
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "agent-eval-platform-xai-test.json"
            report = evaluate_case(
                case,
                source=source,
                live=True,
                provider="xai",
                repeats=3,
                ai_provider=ai,
                report_path=report_path,
            )
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(len(report.records), 3)
        self.assertTrue(all(rec.error_class == "plan" for rec in report.records))
        self.assertIsNone(report.jaccard)
        self.assertFalse(report.passed)
        self.assertFalse(report.offline)
        self.assertEqual(ai.tailor_profile.call_count, 3)
        self.assertEqual(payload["records"][0]["error_class"], "plan")
        self.assertFalse(payload["passed"])

    def test_live_transport_error_is_not_config(self):
        source = load_synthetic()
        case = load_named_case("agent_eval_platform")
        ai = MagicMock()
        ai.tailor_profile.side_effect = TailorTransportError("timeout")
        ai.last_usage = None
        ai.last_elapsed_s = 1.2
        ai.model_name = "mock-model"
        report = evaluate_case(
            case,
            source=source,
            live=True,
            provider="xai",
            repeats=3,
            ai_provider=ai,
        )
        self.assertTrue(all(rec.error_class == "transport" for rec in report.records))
        self.assertIsNone(report.jaccard)
        self.assertFalse(report.passed)

    def test_live_stable_repeats_pass(self):
        source = load_synthetic()
        case = load_named_case("agent_eval_platform")
        tailored = assemble_profile(source, good_plan(source))
        ai = MagicMock()
        ai.tailor_profile.return_value = tailored
        ai.last_usage = {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "reasoning_tokens": 2,
            "total_tokens": 17,
        }
        ai.last_elapsed_s = 0.05
        ai.model_name = "mock-model"
        report = evaluate_case(
            case,
            source=source,
            live=True,
            provider="xai",
            repeats=3,
            ai_provider=ai,
        )
        self.assertTrue(report.passed)
        self.assertEqual(report.jaccard, 1.0)
        self.assertEqual(report.repeats, 3)
        self.assertFalse(report.offline)
        self.assertEqual(report.records[0].usage["reasoning_tokens"], 2)
        self.assertEqual(report.records[0].elapsed_s, 0.05)
        self.assertIsNone(report.records[0].error_class)
        self.assertEqual(fail_findings(report), [])

    def test_live_missing_xai_key_exits_2(self):
        with patch("src.tailor_eval._load_env"):
            with patch.dict(os.environ, {"XAI_API_KEY": ""}, clear=False):
                with patch("sys.stderr", StringIO()):
                    self.assertEqual(main(["--live", "--provider", "xai", "--repeats", "3"]), 2)

    def test_live_repeats_out_of_range_exits_2(self):
        with patch("sys.stderr", StringIO()):
            self.assertEqual(main(["--live", "--repeats", "2"]), 2)
            self.assertEqual(main(["--live", "--repeats", "10"]), 2)

    def test_live_unknown_provider_exits_2(self):
        with patch("sys.stderr", StringIO()):
            self.assertEqual(main(["--live", "--provider", "nope", "--repeats", "3"]), 2)

    def test_live_main_writes_report_json(self):
        source = load_synthetic()
        tailored = assemble_profile(source, good_plan(source))
        fake = MagicMock()
        fake.tailor_profile.return_value = tailored
        fake.last_usage = {
            "prompt_tokens": 3,
            "completion_tokens": 1,
            "reasoning_tokens": 4,
            "total_tokens": 8,
        }
        fake.last_elapsed_s = 0.02
        fake.model_name = "grok-4.6"
        with tempfile.TemporaryDirectory() as tmp:
            cases = Path(tmp) / "cases"
            cases.mkdir()
            shutil.copy(
                CASES_DIR / "agent_eval_platform.yaml",
                cases / "agent_eval_platform.yaml",
            )
            out = Path(tmp) / "reports"
            with patch("src.tailor_eval._load_env"):
                with patch.dict(os.environ, {"XAI_API_KEY": "sk-test"}, clear=False):
                    with patch("src.tailor_eval.build_provider", return_value=fake):
                        with patch("sys.stdout", StringIO()) as stdout:
                            code = main(
                                [
                                    "--live",
                                    "--provider",
                                    "xai",
                                    "--repeats",
                                    "3",
                                    "--cases",
                                    str(cases),
                                    "--output",
                                    str(out),
                                ]
                            )
            files = list(out.glob("agent-eval-platform-xai-*.json"))
            self.assertEqual(code, 0)
            self.assertEqual(len(files), 1)
            payload = json.loads(files[0].read_text(encoding="utf-8"))
            self.assertTrue(payload["passed"])
            self.assertEqual(payload["repeats"], 3)
            self.assertIn("PASS agent-eval-platform xai", stdout.getvalue())
            self.assertEqual(fake.tailor_profile.call_count, 3)


if __name__ == "__main__":
    unittest.main()
