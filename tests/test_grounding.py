"""Offline grounding checks. No API key and no tailoring extra required."""

from __future__ import annotations

import unittest
from pathlib import Path

from src.compose import (
    GroundedTailoringPlan,
    RoleBullets,
    assemble_composed_profile,
    load_resume_standard,
)
from src.grounding import (
    GroundingErrorList,
    check_profile,
    check_role_bullets,
    extract_groundable_terms,
    extract_proper_nouns,
    is_constraint_evidence,
)
from src.loader import YamlDataLoader
from src.tailor_eval import index_by_name


ROOT = Path(__file__).resolve().parents[1]


def live_profile():
    return YamlDataLoader(str(ROOT / "data")).load()


def live_work(name: str):
    profile = live_profile()
    return profile["work"][index_by_name(profile["work"], name)]


def live_project(name: str):
    profile = live_profile()
    return profile["projects"][index_by_name(profile["projects"], name)]


class ResumeStandardTest(unittest.TestCase):
    def test_standard_file_exists_and_states_hard_rules(self):
        text = load_resume_standard()
        self.assertIn("One idea per line", text)
        self.assertIn("Verb + scope + result", text)
        self.assertIn("40%", text)
        self.assertIn("95%", text)
        self.assertIn("67.6", text)
        self.assertIn("Unity Catalog", text)
        self.assertIn("invent causality", text.lower())
        self.assertIn("template-clip", text.lower())


class EvidenceLayerTest(unittest.TestCase):
    def test_constraint_lines_are_not_publishable_inventory(self):
        self.assertTrue(
            is_constraint_evidence(
                "[Do not claim outbound] 67.6% to 83.0%, Moment team name."
            )
        )
        self.assertTrue(
            is_constraint_evidence(
                "[User confirmed] Internal coaching eval, not outbound: 67.6%."
            )
        )
        self.assertTrue(
            is_constraint_evidence(
                "[Do not invent] Do not write Unity Catalog, Delta, or a table name."
            )
        )
        self.assertFalse(
            is_constraint_evidence(
                "[User confirmed] Public / outbound coverage: 40% to 95% on a versioned eval set."
            )
        )


class ProperNounExtractionTest(unittest.TestCase):
    def test_sentence_initial_verbs_and_genai_are_not_names(self):
        designed = extract_proper_nouns(
            "Designed GenAI infrastructure (AI Gateway, Guardrails, MLflow)."
        )
        self.assertNotIn("Designed GenAI", designed)
        self.assertNotIn("Designed", designed)
        self.assertNotIn("GenAI", designed)
        productionized = extract_proper_nouns(
            "Productionized the DS-built PoC as a Databricks deployment workflow."
        )
        self.assertNotIn("Productionized", productionized)
        self.assertIn("Databricks", productionized)

    def test_invented_product_names_are_still_extracted(self):
        names = extract_proper_nouns(
            "Productionized Spark pipelines with TypeScript and LiteLLM."
        )
        self.assertNotIn("Productionized", names)
        self.assertIn("Spark", names)
        self.assertIn("TypeScript", names)
        self.assertIn("LiteLLM", names)

    def test_product_name_ending_in_ing_is_still_extracted(self):
        self.assertIn("Spring", extract_proper_nouns("Built Spring."))
        self.assertNotIn("Built", extract_proper_nouns("Built Spring."))

    def test_generic_tech_is_groundable_but_not_a_proper_name(self):
        self.assertNotIn("RAG", extract_proper_nouns("Built a RAG pipeline."))
        self.assertEqual(extract_groundable_terms("Built a RAG pipeline."), ["RAG"])


class LiveRoleGroundingTest(unittest.TestCase):
    def test_designed_genai_and_productionized_yaml_facts_are_not_ungrounded_names(self):
        cathay = live_work("Cathay Financial Holdings")
        errors = check_role_bullets(
            cathay,
            [
                "Designed GenAI infrastructure (AI Gateway, Guardrails, MLflow), optimizing internal AI service latency by 60%.",
                "Productionized the DS-built PoC as a Databricks deployment workflow, storing related data on the Databricks data layer.",
            ],
        )
        self.assertEqual([item.code for item in errors if item.code == "ungrounded_name"], [])
        self.assertEqual(errors, [])

    def test_invented_proper_name_still_fails_ungrounded_name(self):
        cathay = live_work("Cathay Financial Holdings")
        errors = check_role_bullets(
            cathay,
            ["Designed GenAI infrastructure on the Aetheron platform."],
        )
        name_errors = [item for item in errors if item.code == "ungrounded_name"]
        self.assertTrue(
            any("Aetheron" in item.message for item in name_errors),
            name_errors,
        )
        self.assertFalse(
            any(
                "Designed" in item.message or "GenAI" in item.message
                for item in name_errors
            ),
            name_errors,
        )

    def test_unbacked_spring_fails_ungrounded_name(self):
        cathay = live_work("Cathay Financial Holdings")
        errors = check_role_bullets(cathay, ["Built Spring."])
        self.assertTrue(
            any(
                item.code == "ungrounded_name" and "Spring" in item.message
                for item in errors
            ),
            errors,
        )

    def test_unbacked_generic_tech_still_fails_grounding(self):
        cathay = live_work("Cathay Financial Holdings")
        rag_errors = check_role_bullets(
            cathay, ["Built a RAG pipeline serving production traffic."]
        )
        self.assertTrue(
            any(
                item.code == "ungrounded_tech" and "RAG" in item.message
                for item in rag_errors
            ),
            rag_errors,
        )
        llm_errors = check_role_bullets(cathay, ["Built an LLM evaluation harness."])
        self.assertTrue(
            any(
                item.code == "ungrounded_tech" and "LLM" in item.message
                for item in llm_errors
            ),
            llm_errors,
        )
        rkb = live_project("Regulatory Knowledge Base (RKB)")
        gpu_errors = check_role_bullets(rkb, ["Built a GPU inference pool."])
        self.assertTrue(
            any(
                item.code == "ungrounded_tech" and "GPU" in item.message
                for item in gpu_errors
            ),
            gpu_errors,
        )

    def test_yaml_backed_generic_tech_still_passes(self):
        cathay = live_work("Cathay Financial Holdings")
        self.assertEqual(
            check_role_bullets(
                cathay,
                [
                    "Designed GenAI infrastructure (AI Gateway, Guardrails, MLflow), optimizing internal AI service latency by 60%.",
                    "Implemented FinOps agent, achieving 30% GPU cost reduction.",
                ],
            ),
            [],
        )
        rkb = live_project("Regulatory Knowledge Base (RKB)")
        rag_errors = check_role_bullets(
            rkb, ["Designed ingestion pipelines using enterprise-grade RAG pipelines."]
        )
        self.assertEqual(
            [item.code for item in rag_errors if item.code == "ungrounded_tech"],
            [],
        )

    def test_cathay_grounded_f1_and_retry_pass(self):
        cathay = live_work("Cathay Financial Holdings")
        bullets = [
            "Improved regulatory Agent F1 from 0.67 to 0.89; adopted by 2 of 5 subsidiaries.",
            "Regulatory pipeline: per-record processing status; max 3 retries with increasing wait; after 3 failures mark failed and retry the next day.",
            "DS built the PoC, and I handled production readiness as a Databricks deployment workflow, storing related data on the Databricks data layer.",
        ]
        self.assertEqual(check_role_bullets(cathay, bullets), [])

    def test_cathay_invented_f1_adoption_causality_fails(self):
        cathay = live_work("Cathay Financial Holdings")
        errors = check_role_bullets(
            cathay,
            [
                "Improved regulatory Agent F1 from 0.67 to 0.89, which led to adoption by 2 of 5 subsidiaries."
            ],
        )
        self.assertIn("invented_causality", {item.code for item in errors})

    def test_cathay_invented_unity_catalog_or_delta_fails(self):
        cathay = live_work("Cathay Financial Holdings")
        errors = check_role_bullets(
            cathay,
            ["Stored regulatory data in Unity Catalog and Delta tables on Databricks."],
        )
        codes = {item.code for item in errors}
        self.assertTrue(codes & {"invented_product", "ungrounded_name"})

    def test_cathay_invented_spark_tb_qps_fails(self):
        cathay = live_work("Cathay Financial Holdings")
        errors = check_role_bullets(
            cathay,
            ["Scaled the regulatory pipeline with Spark to 2 TB and 1000 QPS."],
        )
        codes = {item.code for item in errors}
        self.assertTrue(codes & {"invented_product", "ungrounded_number", "ungrounded_name"})

    def test_cathay_poc_ownership_and_team_of_ten_fail(self):
        cathay = live_work("Cathay Financial Holdings")
        poc_errors = check_role_bullets(cathay, ["I built the PoC for regulatory comparison."])
        self.assertIn("invented_claim", {item.code for item in poc_errors})
        ten_errors = check_role_bullets(
            cathay, ["Led 10 cross-functional contributors on the regulatory system."]
        )
        codes = {item.code for item in ten_errors}
        self.assertTrue(codes & {"unpublished_token", "ungrounded_number"})

    def test_cookpad_internal_bench_numbers_fail(self):
        cookpad = live_work("Cookpad")
        errors = check_role_bullets(
            cookpad,
            [
                "Raised the internal coaching eval from 67.6% to 83.0% on a 15-case, 103-unit benchmark."
            ],
        )
        codes = {item.code for item in errors}
        self.assertIn("unpublished_token", codes)
        public = check_role_bullets(
            cookpad,
            ["Raised dish coverage from 50% to 95% (53/56)."],
        )
        self.assertEqual(public, [])
        public_locked = check_role_bullets(
            cookpad,
            [
                "Raised dish coverage from 50% to 95% (53/56) on a fixed 15-case, 56-item eval set."
            ],
        )
        self.assertEqual(public_locked, [])


class AssembleComposedTest(unittest.TestCase):
    def test_live_run_hard_fails_invented_product(self):
        source = live_profile()
        cathay = index_by_name(source["work"], "Cathay Financial Holdings")
        plan = GroundedTailoringPlan(
            work=[cathay],
            work_bullets=[
                RoleBullets(
                    item_index=cathay,
                    bullets=["Deployed the agent on Unity Catalog and Spark at 400 QPS."],
                )
            ],
        )
        with self.assertRaises(GroundingErrorList):
            assemble_composed_profile(source, plan)

    def test_eval_can_collect_findings_without_raising(self):
        source = live_profile()
        cathay = index_by_name(source["work"], "Cathay Financial Holdings")
        tailored = assemble_composed_profile(
            source,
            GroundedTailoringPlan(
                work=[cathay],
                work_bullets=[
                    RoleBullets(
                        item_index=cathay,
                        bullets=[
                            "Improved F1 from 0.67 to 0.89, resulting in adoption by 2 of 5 subsidiaries."
                        ],
                    )
                ],
            ),
            ground=False,
        )
        codes = {item.code for item in check_profile(source, tailored)}
        self.assertIn("invented_causality", codes)


if __name__ == "__main__":
    unittest.main()
