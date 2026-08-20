import os
import tempfile
import unittest
import json

from pydantic import ValidationError

from src.loader import YamlDataLoader


class YamlDataLoaderTest(unittest.TestCase):
    def test_loads_and_sorts_dated_sections_descending(self):
        with tempfile.TemporaryDirectory() as data_dir:
            work_dir = os.path.join(data_dir, 'work')
            os.makedirs(work_dir)
            with open(os.path.join(data_dir, 'basics.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Test User\n')
            with open(os.path.join(work_dir, 'older.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Older\nposition: Engineer\nstartDate: "2020-01"\n')
            with open(os.path.join(work_dir, 'newer.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Newer\nposition: Engineer\nstartDate: "2024-01"\n')

            profile = YamlDataLoader(data_dir).load()

        self.assertEqual(profile['basics']['name'], 'Test User')
        self.assertEqual([item['name'] for item in profile['work']], ['Newer', 'Older'])
        self.assertEqual(profile['projects'], [])

    def test_normalizes_mixed_yaml_date_values_and_returns_json_data(self):
        with tempfile.TemporaryDirectory() as data_dir:
            work_dir = os.path.join(data_dir, 'work')
            os.makedirs(work_dir)
            with open(os.path.join(data_dir, 'basics.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Test User\n')
            with open(os.path.join(work_dir, 'unquoted.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Newer\nposition: Engineer\nstartDate: 2024-02-29\n')
            with open(os.path.join(work_dir, 'quoted.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Older\nposition: Engineer\nstartDate: "2023-01"\n')
            with open(os.path.join(work_dir, 'year.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Year\nposition: Engineer\nstartDate: 2022\n')

            profile = YamlDataLoader(data_dir).load()

        self.assertEqual(profile['work'][0]['startDate'], '2024-02-29')
        self.assertEqual(profile['work'][1]['startDate'], '2023-01')
        self.assertEqual(profile['work'][2]['startDate'], '2022')
        self.assertTrue(all(isinstance(item['startDate'], str) for item in profile['work']))
        json.dumps(profile)

    def test_validation_error_identifies_source_file_and_field(self):
        with tempfile.TemporaryDirectory() as data_dir:
            with open(os.path.join(data_dir, 'basics.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: ""\n')

            with self.assertRaises(ValidationError) as raised:
                YamlDataLoader(data_dir).load()

        self.assertIn('basics.yaml', str(raised.exception))
        self.assertIn('name', str(raised.exception))

    def test_empty_section_file_is_rejected_with_its_source_path(self):
        with tempfile.TemporaryDirectory() as data_dir:
            work_dir = os.path.join(data_dir, 'work')
            os.makedirs(work_dir)
            with open(os.path.join(data_dir, 'basics.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Test User\n')
            with open(os.path.join(work_dir, 'empty.yaml'), 'w', encoding='utf-8'):
                pass

            with self.assertRaises(ValidationError) as raised:
                YamlDataLoader(data_dir).load()

        self.assertIn('empty.yaml', str(raised.exception))

    def test_live_work_and_project_names_are_unique(self):
        profile = YamlDataLoader("data").load()
        work_names = [item["name"] for item in profile["work"]]
        project_names = [item["name"] for item in profile["projects"]]
        self.assertEqual(work_names, list(dict.fromkeys(work_names)))
        self.assertEqual(project_names, list(dict.fromkeys(project_names)))
        self.assertTrue(work_names)
        self.assertTrue(project_names)


if __name__ == '__main__':
    unittest.main()
