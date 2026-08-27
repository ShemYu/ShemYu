import json
import unittest

from pydantic import ValidationError

from src.schema import Basics, Claim, Education, Focus, Metric, Profile, Project, Work, validate_slug


class ProfileSchemaTest(unittest.TestCase):
    def test_extra_fields_are_rejected(self):
        with self.assertRaises(ValidationError):
            Profile.model_validate(
                {
                    "basics": {"name": "Test User", "unexpected": "value"},
                    "work": [
                        {
                            "name": "Company",
                            "position": "Engineer",
                            "startDate": "2024",
                        }
                    ],
                }
            )

    def test_profile_requires_work_history(self):
        with self.assertRaises(ValidationError):
            Profile.model_validate({"basics": {"name": "Test"}, "work": []})

    def test_required_text_fields_must_not_be_empty(self):
        with self.assertRaises(ValidationError):
            Basics.model_validate({"name": "  "})
        with self.assertRaises(ValidationError):
            Work.model_validate({"name": "Company", "position": "", "startDate": "2024"})

    def test_dates_are_validated_and_normalized(self):
        work = Work.model_validate(
            {"name": "Company", "position": "Engineer", "startDate": "2024-02-29"}
        )
        self.assertEqual(work.startDate, "2024-02-29")
        with self.assertRaises(ValidationError):
            Work.model_validate(
                {"name": "Company", "position": "Engineer", "startDate": "2024-02-30"}
            )
        with self.assertRaises(ValidationError):
            Work.model_validate(
                {"name": "Company", "position": "Engineer", "startDate": "Present"}
            )
        education = Education.model_validate(
            {
                "institution": "University",
                "area": "Computer Science",
                "studyType": "Master",
                "startDate": "2024",
                "endDate": "Present",
            }
        )
        self.assertEqual(education.endDate, "Present")
        self.assertEqual(Project.model_validate({"name": "Project"}).startDate, "")
        self.assertEqual(
            Project.model_validate({"name": "Project", "startDate": ""}).startDate,
            "",
        )

    def test_urls_only_allow_http_https_or_empty(self):
        self.assertEqual(Basics.model_validate({"name": "Test", "url": ""}).url, "")
        for unsafe in ("javascript:alert(1)", "data:text/html,x", "ftp://example.com"):
            with self.subTest(unsafe=unsafe), self.assertRaises(ValidationError):
                Basics.model_validate({"name": "Test", "url": unsafe})

    def test_profile_dump_is_json_friendly(self):
        profile = Profile.model_validate(
            {
                "basics": {"name": "Test"},
                "work": [
                    {
                        "name": "Company",
                        "position": "Engineer",
                        "startDate": "2024",
                    }
                ],
            }
        )
        json.dumps(profile.model_dump(mode="json"))

    def test_work_keeps_evidence_off_highlights(self):
        work = Work.model_validate(
            {
                "name": "Cookpad",
                "position": "Engineer",
                "startDate": "2026-02",
                "highlights": ["Public coverage 40% to 95%."],
                "evidence": ["15-case internal benchmark"],
            }
        )
        self.assertEqual(work.highlights, ["Public coverage 40% to 95%."])
        self.assertEqual(work.evidence, ["15-case internal benchmark"])

    def test_metric_accepts_from_and_to_yaml_aliases(self):
        metric = Metric.model_validate(
            {
                "name": "f1",
                "display": "0.67 → 0.89",
                "from": "0.67",
                "to": "0.89",
            }
        )
        self.assertEqual(metric.from_value, "0.67")
        self.assertEqual(metric.to_value, "0.89")
        dumped = metric.model_dump(mode="json")
        self.assertEqual(dumped["from_value"], "0.67")
        self.assertNotIn("from", dumped)

    def test_foci_reject_authored_highlights_and_evidence(self):
        payload = {
            "name": "Cookpad",
            "position": "Engineer",
            "startDate": "2026-02",
            "foci": [
                {
                    "id": "cookpad-vu",
                    "name": "Video understanding",
                    "claims": [
                        {
                            "id": "cookpad-vu-coverage",
                            "layer": "public",
                            "text": "Raised dish coverage from 50% to 95%.",
                        }
                    ],
                }
            ],
            "highlights": ["duplicate authored highlight"],
        }
        with self.assertRaises(ValidationError):
            Work.model_validate(payload)
        payload.pop("highlights")
        payload["evidence"] = ["archive line"]
        with self.assertRaises(ValidationError):
            Work.model_validate(payload)

    def test_slug_strips_obsidian_wikilinks(self):
        self.assertEqual(validate_slug("[[cookpad-vu]]"), "cookpad-vu")
        self.assertEqual(
            validate_slug("[[cookpad-vu|Video understanding]]"), "cookpad-vu"
        )

    def test_focus_and_claim_ids_must_be_slugs_and_unique(self):
        with self.assertRaises(ValidationError):
            Focus.model_validate({"id": "Cookpad VU", "name": "Video understanding"})
        with self.assertRaises(ValidationError):
            Claim.model_validate(
                {"id": "Not_a_slug", "layer": "public", "text": "A claim."}
            )
        with self.assertRaises(ValidationError):
            Profile.model_validate(
                {
                    "basics": {"name": "Test"},
                    "work": [
                        {
                            "name": "Company",
                            "position": "Engineer",
                            "startDate": "2024",
                            "foci": [
                                {
                                    "id": "same-id",
                                    "name": "One",
                                    "claims": [
                                        {
                                            "id": "claim-a",
                                            "layer": "public",
                                            "text": "First.",
                                        }
                                    ],
                                },
                                {
                                    "id": "same-id",
                                    "name": "Two",
                                    "claims": [
                                        {
                                            "id": "claim-b",
                                            "layer": "public",
                                            "text": "Second.",
                                        }
                                    ],
                                },
                            ],
                        }
                    ],
                }
            )


if __name__ == "__main__":
    unittest.main()
