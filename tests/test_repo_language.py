"""Guard: all repository text is English (no CJK characters)."""

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

CJK = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\u3000-\u303f\uff00-\uffef]")
TEXT_EXTENSIONS = {
    ".md",
    ".py",
    ".html",
    ".toml",
    ".yaml",
    ".yml",
    ".js",
    ".css",
    ".json",
    ".txt",
    ".sh",
    ".cjs",
    ".mjs",
}
EXCLUDED_DIRS = {"themes", "public", ".git", "__pycache__", "node_modules", ".hugo_build.lock"}


class RepositoryLanguageTest(unittest.TestCase):
    def test_no_cjk_characters_in_text_files(self):
        offenders = []
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(REPO_ROOT)
            if any(part in EXCLUDED_DIRS for part in relative.parts):
                continue
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            match = CJK.search(text)
            if match:
                line = text[: match.start()].count("\n") + 1
                offenders.append(f"{relative}:{line}")
        self.assertEqual(offenders, [], f"CJK characters found in: {offenders}")


if __name__ == "__main__":
    unittest.main()
