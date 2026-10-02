"""Tests for scripts/link-maintainers-projects.py insertion logic (temp files)."""

import importlib.util
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_script(name):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mod = load_script("link-maintainers-projects")


class MaintainersInsertionTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.projects = Path(self._tmp.name) / "projects"
        self.projects.mkdir(parents=True)
        self._orig_projects = mod.PROJECTS_DIR
        mod.PROJECTS_DIR = self.projects

    def tearDown(self):
        mod.PROJECTS_DIR = self._orig_projects
        self._tmp.cleanup()

    def write_project(self, slug, frontmatter):
        path = self.projects / f"{slug}.md"
        path.write_text(f"+++\n{frontmatter}+++\n\nBody text\n")
        return path

    @staticmethod
    def parsed_frontmatter(path):
        return tomllib.loads(path.read_text(encoding="utf-8").split("+++")[1])

    def test_inserts_top_level_key_with_valid_toml(self):
        path = self.write_project(
            "demo",
            "title = 'Demo'\ndescription = 'd'\n\n[health]\n  score = 50\n[links]\n  github = 'o/r'\n",
        )
        mod.update_project_maintainers({"demo": ["Alice", "Bob"]}, dry_run=False)

        data = self.parsed_frontmatter(path)
        self.assertEqual(data["maintainers"], ["Alice", "Bob"])
        self.assertNotIn("maintainers", data["links"])

        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("+++\ntitle = 'Demo'\n"))  # no blank line injected
        self.assertTrue(text.endswith("\nBody text\n"))
        frontmatter = text.split("+++")[1]
        self.assertLess(frontmatter.index("maintainers ="), frontmatter.index("[health]"))

    def test_second_apply_is_byte_identical(self):
        path = self.write_project("demo", "title = 'Demo'\n\n[links]\n  github = 'o/r'\n")
        mapping = {"demo": ["Alice"]}

        mod.update_project_maintainers(mapping, dry_run=False)
        first = path.read_bytes()
        mod.update_project_maintainers(mapping, dry_run=False)

        self.assertEqual(first, path.read_bytes())
        self.assertEqual(path.read_text(encoding="utf-8").count("maintainers ="), 1)

    def test_existing_top_level_key_left_untouched(self):
        original = "title = 'Demo'\nmaintainers = [\"Carol\"]\n\n[links]\n  github = 'o/r'\n"
        path = self.write_project("demo", original)
        before = path.read_bytes()

        mod.update_project_maintainers({"demo": ["Alice"]}, dry_run=False)

        self.assertEqual(before, path.read_bytes())

    def test_misplaced_key_relocated_and_idempotent(self):
        path = self.write_project(
            "demo",
            "title = 'Demo'\n\n[links]\n  github = 'o/r'\nmaintainers = [\"Carol\"]\n",
        )
        mapping = {"demo": ["Alice"]}

        mod.update_project_maintainers(mapping, dry_run=False)
        data = self.parsed_frontmatter(path)
        self.assertEqual(data["maintainers"], ["Carol"])  # value preserved
        self.assertNotIn("maintainers", data["links"])

        first = path.read_bytes()
        mod.update_project_maintainers(mapping, dry_run=False)
        self.assertEqual(first, path.read_bytes())

    def test_already_invalid_toml_is_not_written(self):
        # Quoted table header with two names is not valid TOML — mirrors the
        # bare `["Name", "Name"]` lines left by the old append bug.
        path = self.write_project(
            "demo", "title = 'Demo'\n\n[metrics]\n  stars = 1\n[\"Alice\", \"Bob\"]\n"
        )
        before = path.read_bytes()

        mod.update_project_maintainers({"demo": ["Alice"]}, dry_run=False)

        self.assertEqual(before, path.read_bytes())

    def test_dry_run_writes_nothing(self):
        path = self.write_project("demo", "title = 'Demo'\n\n[links]\n  github = 'o/r'\n")
        before = path.read_bytes()

        mod.update_project_maintainers({"demo": ["Alice"]}, dry_run=True)

        self.assertEqual(before, path.read_bytes())

    def test_no_tables_appends_key(self):
        path = self.write_project("demo", "title = 'Demo'\ndescription = 'd'\n")
        mod.update_project_maintainers({"demo": ["Alice"]}, dry_run=False)
        self.assertEqual(self.parsed_frontmatter(path)["maintainers"], ["Alice"])


if __name__ == "__main__":
    unittest.main()
