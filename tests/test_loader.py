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
        focus_ids = [
            focus["id"]
            for role in profile["work"]
            for focus in role.get("foci") or []
        ]
        self.assertEqual(focus_ids, list(dict.fromkeys(focus_ids)))

    def test_live_one_pager_clip_keeps_locked_public_bullets(self):
        profile = YamlDataLoader("data").load()
        cookpad = next(item for item in profile["work"] if item["name"] == "Cookpad")
        cathay = next(
            item for item in profile["work"] if item["name"] == "Cathay Financial Holdings"
        )
        self.assertEqual(
            cookpad["highlights"][:3],
            [
                "Built and iterated the video-understanding system as a staged pipeline: observable facts → recipe-specific ingredient definitions → ingredient state → cooking issues.",
                "Raised dish coverage from 50% to 95% (53/56) on a fixed 15-case, 56-item eval set; knowledge coverage remains the remaining optimization target.",
                "Capability-based evals and automated scoring for observation accuracy, issue coverage, factuality, coherence, and turn-level coaching quality.",
            ],
        )
        self.assertEqual(
            cathay["highlights"][:3],
            [
                "Developed Departmental Internal AI Agents with Google ADK, automating deep research tasks, reducing analysis time from 2 hours to 15 minutes.",
                "Designed and built GenAI infrastructure (AI Gateway, Guardrails, MLflow), optimizing internal AI service latency by 60%.",
                "Implemented FinOps agent, achieving 30% GPU cost reduction.",
            ],
        )

    def test_foci_are_projected_into_highlights_and_projects(self):
        with tempfile.TemporaryDirectory() as data_dir:
            work_dir = os.path.join(data_dir, "work")
            os.makedirs(work_dir)
            with open(os.path.join(data_dir, "basics.yaml"), "w", encoding="utf-8") as f:
                f.write("name: Test User\n")
            with open(os.path.join(work_dir, "role.yaml"), "w", encoding="utf-8") as f:
                f.write(
                    "\n".join(
                        [
                            "name: Cookpad",
                            "position: Engineer",
                            "startDate: '2026-02'",
                            "endDate: Present",
                            "foci:",
                            "  - id: cookpad-vu",
                            "    name: Video-understanding coaching agent",
                            "    kind: product",
                            "    problem: Infer where a learner is stuck.",
                            "    stack:",
                            "      - multimodal agents",
                            "    claims:",
                            "      - id: cookpad-vu-pipeline",
                            "        layer: public",
                            "        rank: 1",
                            "        text: Built the staged pipeline.",
                            "      - id: cookpad-vu-internal",
                            "        layer: archive",
                            "        text: Internal 67.6 to 83.0 stays off the page.",
                            "",
                        ]
                    )
                )

            profile = YamlDataLoader(data_dir).load()

        self.assertEqual(
            profile["work"][0]["highlights"], ["Built the staged pipeline."]
        )
        self.assertEqual(
            profile["work"][0]["evidence"],
            ["Internal 67.6 to 83.0 stays off the page."],
        )
        self.assertEqual(profile["projects"][0]["name"], "Video-understanding coaching agent")
        self.assertEqual(profile["projects"][0]["keywords"], ["multimodal agents"])


if __name__ == '__main__':
    unittest.main()
