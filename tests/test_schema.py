import json
import unittest

from pydantic import ValidationError

from src.schema import Basics, Education, Profile, Project, Work


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


if __name__ == "__main__":
    unittest.main()
