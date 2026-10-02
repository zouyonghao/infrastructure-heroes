"""Tests for scripts/localize-images.py helpers (no network)."""

import importlib.util
import sys
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "localize_images", REPO_ROOT / "scripts" / "localize-images.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


FRONTMATTER = """+++
title = "Test Person"
role = "Lead"
[links]
  github = "example"
+++
Body text.
"""


class SetFrontmatterValueTest(unittest.TestCase):
    def test_inserts_missing_field_after_role(self):
        result = MODULE.set_frontmatter_value(FRONTMATTER, "avatar", "/images/a.webp")
        front = result.split("+++")[1]
        parsed = tomllib.loads(front)
        self.assertEqual(parsed["avatar"], "/images/a.webp")
        self.assertEqual(parsed["role"], "Lead")
        self.assertEqual(parsed["links"]["github"], "example")
        self.assertIn("Body text.", result)

    def test_replaces_existing_value_in_place(self):
        text = MODULE.set_frontmatter_value(FRONTMATTER, "logo", "/images/one.svg")
        text = MODULE.set_frontmatter_value(text, "logo", "/images/two.webp")
        front = text.split("+++")[1]
        self.assertEqual(tomllib.loads(front)["logo"], "/images/two.webp")
        self.assertEqual(front.count("logo ="), 1)

    def test_rejects_document_without_frontmatter(self):
        with self.assertRaises(ValueError):
            MODULE.set_frontmatter_value("no front matter", "logo", "/x.svg")


class FormatDetectionTest(unittest.TestCase):
    def test_svg_detection_ignores_case_and_leading_markup(self):
        self.assertTrue(MODULE.looks_like_svg(b'<?xml version="1.0"?><SVG xmlns="...">'))
        self.assertFalse(MODULE.looks_like_svg(b"\x89PNG\r\n\x1a\n"))

    def test_is_raster(self):
        self.assertTrue(MODULE.is_raster("image/png", "https://x/y.png"))
        self.assertTrue(MODULE.is_raster("application/octet-stream", "https://x/y.jpeg"))
        self.assertFalse(MODULE.is_raster("image/svg+xml", "https://x/y.svg"))
        self.assertFalse(MODULE.is_raster("text/html", "https://x/y"))


if __name__ == "__main__":
    unittest.main()
