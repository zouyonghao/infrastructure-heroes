"""Guard against publishing unsupported ratings or incomplete support records."""

import json
import tomllib
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class EvidenceDataTest(unittest.TestCase):
    def test_every_project_has_a_defined_primary_category(self):
        categories = json.loads((ROOT / "data/project_categories.json").read_text())
        used = set()
        for path in (ROOT / "content/projects").glob("*.md"):
            if path.name == "_index.md":
                continue
            with self.subTest(project=path.stem):
                data = tomllib.loads(path.read_text().split("+++")[1])
                self.assertIn(data.get("category"), categories)
                used.add(data["category"])
        self.assertEqual(used, set(categories), "Remove empty categories from the directory")
        for category in categories.values():
            self.assertTrue(category["name"])
            self.assertTrue(category["description"])

    def test_current_projects_do_not_publish_retired_composite_scores(self):
        for path in (ROOT / "content/projects").glob("*.md"):
            if path.name == "_index.md":
                continue
            with self.subTest(project=path.stem):
                data = tomllib.loads(path.read_text().split("+++")[1])
                self.assertNotIn("score", data["health"])
                self.assertEqual(data["health"]["funding"], "unknown")
                self.assertEqual(data["health"]["methodology_version"], "2.0")

    def test_checked_support_has_project_sources_date_and_concrete_actions(self):
        data = json.loads((ROOT / "data/project_support.json").read_text())
        self.assertTrue(data)
        for slug, entry in data.items():
            with self.subTest(project=slug):
                self.assertTrue((ROOT / "content/projects" / f"{slug}.md").exists())
                date.fromisoformat(entry["checked_at"])
                self.assertTrue(entry["context"])
                self.assertTrue(entry["actions"])
                self.assertTrue(entry["sources"])
                for link in entry["actions"] + entry["sources"]:
                    self.assertTrue(link["label"])
                    url = urlsplit(link["url"])
                    self.assertEqual(url.scheme, "https")
                    self.assertTrue(url.hostname)
                for action in entry["actions"]:
                    self.assertTrue(action["description"])


if __name__ == "__main__":
    unittest.main()
