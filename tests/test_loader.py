import os
import tempfile
import unittest

from src.loader import YamlDataLoader


class YamlDataLoaderTest(unittest.TestCase):
    def test_loads_and_sorts_dated_sections_descending(self):
        with tempfile.TemporaryDirectory() as data_dir:
            work_dir = os.path.join(data_dir, 'work')
            os.makedirs(work_dir)
            with open(os.path.join(data_dir, 'basics.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Test User\n')
            with open(os.path.join(work_dir, 'older.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Older\nstartDate: "2020-01"\n')
            with open(os.path.join(work_dir, 'newer.yaml'), 'w', encoding='utf-8') as f:
                f.write('name: Newer\nstartDate: "2024-01"\n')

            profile = YamlDataLoader(data_dir).load()

        self.assertEqual(profile['basics']['name'], 'Test User')
        self.assertEqual([item['name'] for item in profile['work']], ['Newer', 'Older'])
        self.assertEqual(profile['projects'], [])


if __name__ == '__main__':
    unittest.main()
