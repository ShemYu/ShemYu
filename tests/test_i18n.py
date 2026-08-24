import unittest

from src.generator import format_date_ja
from src.i18n import translate_profile
from src.loader import YamlDataLoader
from src.select import apply_selection, load_selection


class FormatDateJaTest(unittest.TestCase):
    def test_formats_month_and_present(self):
        self.assertEqual(format_date_ja("2026-02"), "2026年2月")
        self.assertEqual(format_date_ja("2020-11-01"), "2020年11月")
        self.assertEqual(format_date_ja("2017"), "2017年")
        self.assertEqual(format_date_ja("Present"), "現在")
        self.assertEqual(format_date_ja("present"), "現在")


class TranslateProfileTest(unittest.TestCase):
    def test_maps_known_strings_and_reports_unmapped_prose(self):
        profile = {
            "basics": {
                "name": "Shem Yu",
                "summary": "Unknown prose that is not in the locale file.",
                "email": "shauns4y@gmail.com",
            },
            "work": [],
            "skills": [],
        }
        translated, missing = translate_profile(profile, "ja")
        self.assertEqual(translated["basics"]["name"], "余顯漁（Shem Yu）")
        self.assertEqual(
            translated["basics"]["summary"],
            "Unknown prose that is not in the locale file.",
        )
        self.assertEqual(translated["basics"]["email"], "shauns4y@gmail.com")
        self.assertIn("Unknown prose that is not in the locale file.", missing)

    def test_english_locale_is_a_noop(self):
        profile = {"basics": {"name": "Shem Yu"}}
        translated, missing = translate_profile(profile, "en")
        self.assertEqual(translated["basics"]["name"], "Shem Yu")
        self.assertEqual(missing, [])


class LiveTranslationCoverageTest(unittest.TestCase):
    def test_selected_ly_profiles_have_expected_english_leftovers_only(self):
        expected_english = {
            "Cathay Financial Holdings",
            "Wisers Information Limited",
            "TripSaaS",
            "AWS Certified Machine Learning - Specialty",
            "AWS Certified Cloud Practitioner",
        }
        for preset in ("ly_agent", "ly_platform"):
            profile = apply_selection(YamlDataLoader("data").load(), load_selection(preset))
            _, missing = translate_profile(profile, "ja")
            self.assertEqual(
                set(missing),
                expected_english,
                f"{preset} unexpected untranslated strings: {missing}",
            )
