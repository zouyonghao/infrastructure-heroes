"""Tests for scripts/update-historical-data.py (no network, temp dirs only)."""

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_script(name):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


hist = load_script("update-historical-data")


class ComputeSummaryTest(unittest.TestCase):
    @staticmethod
    def _project(score):
        return {"health": {"score": score}}

    def test_bucket_boundaries(self):
        projects = [self._project(s) for s in (0, 59, 60, 79, 80, 100)]
        summary = hist.compute_summary(projects)
        self.assertEqual(summary["critical"], 2)  # 0, 59
        self.assertEqual(summary["warning"], 2)  # 60, 79
        self.assertEqual(summary["healthy"], 2)  # 80, 100
        self.assertAlmostEqual(summary["avg_score"], (0 + 59 + 60 + 79 + 80 + 100) / 6)

    def test_empty(self):
        self.assertEqual(
            hist.compute_summary([]),
            {"critical": 0, "warning": 0, "healthy": 0, "avg_score": 0},
        )


class NormalizeMonthlyDataTest(unittest.TestCase):
    def test_list_passthrough(self):
        data = [{"date": "2026-01-01"}]
        self.assertIs(hist.normalize_monthly_data(data), data)

    def test_legacy_dict_wrapped(self):
        snapshot = {"date": "2026-01-01"}
        self.assertEqual(hist.normalize_monthly_data(snapshot), [snapshot])

    def test_other_types_rejected(self):
        for bad in ("nope", 5, None, 1.5):
            with self.assertRaises(ValueError):
                hist.normalize_monthly_data(bad)


class _TempDirs(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.projects = root / "content" / "projects"
        self.data = root / "data" / "historical"
        self.projects.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def write_project(self, slug, score, health_last):
        if health_last:
            frontmatter = "[links]\n  github = 'o/r'\n[health]\n  score = %d\n" % score
        else:
            frontmatter = "[health]\n  score = %d\n[links]\n  github = 'o/r'\n" % score
        path = self.projects / f"{slug}.md"
        path.write_text(f"+++\ntitle = '{slug}'\n{frontmatter}+++\n\nBody\n")
        return path


class LoadProjectDataTest(_TempDirs):
    def test_health_table_last_is_parsed(self):
        path = self.write_project("a", 90, health_last=True)
        data = hist.load_project_data(path)
        self.assertEqual(data["health"]["score"], 90)
        self.assertEqual(data["name"], "a")

    def test_health_table_middle_is_parsed(self):
        path = self.write_project("b", 42, health_last=False)
        self.assertEqual(hist.load_project_data(path)["health"]["score"], 42)

    def test_missing_frontmatter_raises(self):
        path = self.projects / "broken.md"
        path.write_text("no frontmatter here\n")
        with self.assertRaises(ValueError):
            hist.load_project_data(path)


class CreateSnapshotTest(_TempDirs):
    def test_total_projects_at_top_level_and_in_summary(self):
        self.write_project("a", 90, health_last=True)
        self.write_project("b", 42, health_last=False)
        self.write_project("c", 61, health_last=False)

        snapshot = hist.create_snapshot(projects_dir=self.projects, data_dir=self.data)

        self.assertEqual(snapshot["total_projects"], 3)
        self.assertEqual(snapshot["summary"]["total_projects"], 3)
        self.assertEqual(snapshot["summary"]["healthy"], 1)
        self.assertEqual(snapshot["summary"]["warning"], 1)
        self.assertEqual(snapshot["summary"]["critical"], 1)

        month_file = self.data / f"{snapshot['month']}.json"
        stored = json.loads(month_file.read_text())
        self.assertIsInstance(stored, list)
        self.assertEqual(stored[0]["summary"]["total_projects"], 3)

    def test_legacy_single_object_month_file_is_normalized(self):
        self.write_project("a", 90, health_last=True)
        self.data.mkdir(parents=True, exist_ok=True)
        legacy = {"date": "2026-01-01", "summary": {"avg_score": 1, "critical": 0}}
        # create_snapshot writes to the *current* month file; seed it as a
        # legacy single-object document to exercise normalization.
        month_file = self.data / f"{datetime.now().strftime('%Y-%m')}.json"
        month_file.write_text(json.dumps(legacy))

        snapshot = hist.create_snapshot(projects_dir=self.projects, data_dir=self.data)

        stored = json.loads((self.data / f"{snapshot['month']}.json").read_text())
        self.assertEqual(len(stored), 2)
        self.assertEqual(stored[0], legacy)


class UpdateSummaryStatsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data = Path(self._tmp.name) / "historical"
        self.data.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_month(self, name, payload):
        (self.data / name).write_text(json.dumps(payload))

    def load_summary(self):
        return json.loads((self.data / "summary.json").read_text())

    def test_score_distribution_from_latest_snapshot(self):
        self._write_month(
            "2026-01.json",
            [{"date": "2026-01-05", "summary": {"critical": 1, "warning": 1, "healthy": 1, "avg_score": 50}}],
        )
        latest = {
            "date": "2026-02-05",
            "summary": {
                "critical": 2,
                "warning": 3,
                "healthy": 4,
                "avg_score": 70,
                "total_projects": 9,
            },
        }
        self._write_month("2026-02.json", [latest])

        hist.update_summary_stats(self.data)
        summary = self.load_summary()

        self.assertEqual(
            summary["trends"]["score_distribution"],
            {"healthy": 4, "warning": 3, "critical": 2},
        )
        self.assertEqual(summary["current_status"]["total_projects"], 9)

        # Existing trend keys are preserved unchanged.
        self.assertEqual(
            [p["value"] for p in summary["trends"]["avg_score_over_time"]], [50, 70]
        )
        self.assertEqual(
            [p["value"] for p in summary["trends"]["critical_count_over_time"]], [1, 2]
        )
        self.assertEqual(summary["date_range"], {"from": "2026-01-05", "to": "2026-02-05"})

    def test_legacy_dict_month_file(self):
        self._write_month(
            "2025-12.json",
            {"date": "2025-12-01", "summary": {"critical": 0, "warning": 0, "healthy": 1, "avg_score": 88}},
        )
        hist.update_summary_stats(self.data)
        summary = self.load_summary()
        self.assertEqual(summary["total_snapshots"], 1)
        self.assertEqual(
            summary["trends"]["score_distribution"],
            {"healthy": 1, "warning": 0, "critical": 0},
        )


if __name__ == "__main__":
    unittest.main()
