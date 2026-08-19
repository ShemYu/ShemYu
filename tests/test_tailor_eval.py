import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from src.ai import HighlightSelection, TailoringPlan, assemble_profile
from src.generator import Jinja2Generator
from src.loader import YamlDataLoader
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


if __name__ == "__main__":
    unittest.main()
