"""Tests for scripts/logo_urls.json and its consumers (no network)."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
LOGO_JSON = ROOT / "scripts" / "logo_urls.json"
PROJECTS_DIR = ROOT / "content" / "projects"


def load_script(name):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def project_slugs():
    return sorted(p.stem for p in PROJECTS_DIR.glob("*.md") if p.name != "_index.md")


class LogoUrlsJsonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.urls = json.loads(LOGO_JSON.read_text(encoding="utf-8"))

    def test_is_object_of_strings(self):
        self.assertIsInstance(self.urls, dict)
        for key, value in self.urls.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)

    def test_covers_every_project(self):
        missing = [slug for slug in project_slugs() if slug not in self.urls]
        self.assertEqual(missing, [], f"projects without a logo URL: {missing}")

    def test_previously_missing_entries_present(self):
        for slug in ("libjpeg-turbo", "libpng", "libsodium", "tomcat"):
            self.assertIn(slug, self.urls, slug)
            self.assertTrue(self.urls[slug], f"{slug} has an empty URL")

    def test_apt_is_explicitly_empty(self):
        # 'apt' deliberately has no standard logo; the empty value is
        # documented in update_logos.py.
        self.assertEqual(self.urls.get("apt"), "")


class UpdateLogosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.urls = json.loads(LOGO_JSON.read_text(encoding="utf-8"))

    def test_loads_json_mapping(self):
        mod = load_script("update_logos")
        self.assertEqual(mod.LOGO_URLS, self.urls)
        self.assertEqual(mod.LOGO_URLS_PATH, LOGO_JSON)

    def test_repo_root_is_project_root(self):
        mod = load_script("update_logos")
        self.assertEqual(mod.REPO_ROOT, ROOT)
        self.assertTrue((mod.REPO_ROOT / "content" / "projects").is_dir())

    def test_fills_only_empty_logo(self):
        mod = load_script("update_logos")
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.md"
            empty.write_text("+++\ntitle = 'x'\nlogo = ''\n+++\n")
            self.assertTrue(mod.update_project_logo(empty, "https://cdn/x.svg"))
            self.assertIn("logo = 'https://cdn/x.svg'", empty.read_text())

            filled = Path(tmp) / "filled.md"
            filled.write_text("+++\ntitle = 'y'\nlogo = 'https://old/y.svg'\n+++\n")
            before = filled.read_bytes()
            self.assertFalse(mod.update_project_logo(filled, "https://cdn/x.svg"))
            self.assertEqual(before, filled.read_bytes())


class _FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.closed = False

    def close(self):
        self.closed = True


class CheckUrlsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.urls = json.loads(LOGO_JSON.read_text(encoding="utf-8"))

    def setUp(self):
        self.mod = load_script("check_urls")
        self._real_get = self.mod.requests.get

    def tearDown(self):
        self.mod.requests.get = self._real_get

    def test_loads_json_mapping(self):
        self.assertEqual(self.mod.load_logo_urls(), self.urls)
        self.assertEqual(self.mod.LOGO_URLS_PATH, LOGO_JSON)

    def test_uses_browser_like_user_agent(self):
        seen = {}

        def fake_get(url, **kwargs):
            seen.update(kwargs)
            return _FakeResponse(200)

        self.mod.requests.get = fake_get
        self.assertTrue(self.mod.check_url("https://example.invalid/logo.svg"))
        self.assertIn("Mozilla", seen["headers"]["User-Agent"])
        self.assertEqual(seen["timeout"], 10)
        self.assertTrue(seen["stream"])

    def test_200_is_ok_and_closes(self):
        response = _FakeResponse(200)
        self.mod.requests.get = lambda *a, **k: response
        self.assertTrue(self.mod.check_url("https://example.invalid/logo.svg"))
        self.assertTrue(response.closed)

    def test_non_200_is_broken(self):
        self.mod.requests.get = lambda *a, **k: _FakeResponse(403)
        self.assertFalse(self.mod.check_url("https://example.invalid/logo.svg"))

    def test_empty_url_is_not_ok(self):
        self.mod.requests.get = lambda *a, **k: _FakeResponse(200)
        self.assertFalse(self.mod.check_url(""))

    def test_request_error_is_handled(self):
        def boom(*a, **k):
            raise requests.RequestException("nope")

        self.mod.requests.get = boom
        self.assertFalse(self.mod.check_url("https://example.invalid/logo.svg"))


if __name__ == "__main__":
    unittest.main()
