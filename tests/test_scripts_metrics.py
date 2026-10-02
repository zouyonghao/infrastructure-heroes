"""Tests for scripts/fetch-github-metrics.py (offline, no network)."""

import importlib.util
import sys
import tempfile
import tomllib
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Make the (hyphenated) scripts importable by future tests too.
sys.path.insert(0, str(ROOT / "scripts"))


def load_script(name):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


metrics_mod = load_script("fetch-github-metrics")


class RetryDelayTest(unittest.TestCase):
    def test_exponential_backoff_then_stops(self):
        self.assertEqual(metrics_mod.retry_delay(500, {}, "", 0), 1.0)
        self.assertEqual(metrics_mod.retry_delay(500, {}, "", 1), 2.0)
        self.assertEqual(metrics_mod.retry_delay(500, {}, "", 2), 4.0)
        self.assertEqual(metrics_mod.retry_delay(500, {}, "", 3), 8.0)
        self.assertIsNone(metrics_mod.retry_delay(500, {}, "", 4))

    def test_server_and_throttle_statuses_retry(self):
        self.assertIsNotNone(metrics_mod.retry_delay(502, {}, "", 0))
        self.assertIsNotNone(metrics_mod.retry_delay(503, {}, "", 0))
        self.assertIsNotNone(metrics_mod.retry_delay(504, {}, "", 0))
        self.assertIsNotNone(metrics_mod.retry_delay(429, {}, "", 0))

    def test_retry_after_is_honored_and_capped(self):
        self.assertEqual(metrics_mod.retry_delay(429, {"Retry-After": "5"}, "", 0), 5.0)
        self.assertEqual(metrics_mod.retry_delay(429, {"Retry-After": "120"}, "", 0), 60.0)
        self.assertEqual(
            metrics_mod.retry_delay(403, {"Retry-After": "3"}, "", 0), 3.0
        )
        # HTTP-date form, far in the future -> capped
        self.assertEqual(
            metrics_mod.retry_delay(403, {"Retry-After": "Wed, 21 Oct 2099 07:28:00 GMT"}, "", 0),
            60.0,
        )

    def test_secondary_rate_limit_403_signals(self):
        self.assertEqual(
            metrics_mod.retry_delay(403, {"X-RateLimit-Remaining": "0"}, "", 0), 1.0
        )
        self.assertEqual(
            metrics_mod.retry_delay(403, {}, "API rate limit exceeded", 0), 1.0
        )

    def test_plain_403_is_not_retried(self):
        self.assertIsNone(metrics_mod.retry_delay(403, {}, "Forbidden", 0))
        # 403 for an oversized contributor list is not a retryable rate limit
        body = ("The history or contributor list is too large to list contributors "
                "for this repository via the API.")
        self.assertIsNone(metrics_mod.retry_delay(403, {}, body, 0))

    def test_client_and_success_statuses_are_not_retried(self):
        for status in (200, 201, 400, 401, 404, 422):
            self.assertIsNone(metrics_mod.retry_delay(status, {}, "", 0), status)

    def test_network_errors_are_retried(self):
        self.assertEqual(metrics_mod.retry_delay(None, {}, "timed out", 0), 1.0)
        self.assertIsNone(metrics_mod.retry_delay(None, {}, "timed out", 4))


class ContributorsTooLargeTest(unittest.TestCase):
    def test_detects_oversized_contributor_message(self):
        self.assertTrue(metrics_mod.is_contributors_too_large(
            "The history or contributor list is too large to list contributors "
            "for this repository via the API."
        ))

    def test_other_bodies_are_not_flagged(self):
        self.assertFalse(metrics_mod.is_contributors_too_large("API rate limit exceeded"))
        self.assertFalse(metrics_mod.is_contributors_too_large(""))
        self.assertFalse(metrics_mod.is_contributors_too_large(None))


class ParseNextLinkTest(unittest.TestCase):
    def test_extracts_next_url(self):
        header = (
            '<https://api.github.com/repos/o/r/commits?per_page=100&page=2>; rel="next", '
            '<https://api.github.com/repos/o/r/commits?per_page=100&page=9>; rel="last"'
        )
        self.assertEqual(
            metrics_mod.parse_next_link(header),
            "https://api.github.com/repos/o/r/commits?per_page=100&page=2",
        )

    def test_next_may_be_first_or_only(self):
        header = '<https://api.github.com/x?page=2>; rel="next"'
        self.assertEqual(metrics_mod.parse_next_link(header),
                         "https://api.github.com/x?page=2")

    def test_no_next_returns_none(self):
        header = ('<https://api.github.com/x?page=1>; rel="prev", '
                  '<https://api.github.com/x?page=5>; rel="last"')
        self.assertIsNone(metrics_mod.parse_next_link(header))
        self.assertIsNone(metrics_mod.parse_next_link(None))
        self.assertIsNone(metrics_mod.parse_next_link(""))


class HealthScoreTest(unittest.TestCase):
    def setUp(self):
        self.fetcher = metrics_mod.GitHubMetricsFetcher(token="dummy")

    def maintenance(self, days_push=365, days_release=365, commits_30d=0):
        return self.fetcher.calculate_maintenance_score({
            "days_since_last_push": days_push,
            "days_since_last_release": days_release,
            "commits_last_30_days": commits_30d,
        })

    def test_maintenance_push_recency_boundaries(self):
        # Isolate the push component: release -> 5, commits -> 0.
        for days, expected in ((0, 45), (6, 45), (7, 40), (29, 40), (30, 30),
                               (59, 30), (60, 20), (89, 20), (90, 15), (179, 15), (180, 10)):
            self.assertEqual(self.maintenance(days_push=days), expected, f"push {days}")

    def test_maintenance_release_recency_boundaries(self):
        for days, expected in ((29, 35), (30, 30), (89, 30), (90, 20),
                               (179, 20), (180, 15), (364, 15), (365, 10)):
            self.assertEqual(self.maintenance(days_release=days), expected, f"release {days}")

    def test_maintenance_activity_boundaries(self):
        for commits, expected in ((50, 40), (49, 35), (20, 35), (19, 30), (10, 30),
                                  (9, 25), (5, 25), (4, 20), (1, 20), (0, 10)):
            self.assertEqual(self.maintenance(commits_30d=commits), expected, f"commits {commits}")

    def test_contributors_score_boundaries(self):
        for active, expected in ((0, 0), (1, 8), (9, 72), (10, 100), (12, 100)):
            self.assertEqual(
                self.fetcher.calculate_contributors_score(
                    {"unique_contributors_last_90_days": active}),
                expected, f"active {active}")

    def test_bus_factor_boundaries(self):
        self.assertIsNone(self.fetcher.calculate_bus_factor_score({}))
        self.assertEqual(
            self.fetcher.calculate_bus_factor_score({"all_commit_authors": ["a"] * 10}), 15)
        self.assertEqual(
            self.fetcher.calculate_bus_factor_score(
                {"all_commit_authors": ["a", "b", "c", "d"]}), 40)
        self.assertEqual(
            self.fetcher.calculate_bus_factor_score(
                {"all_commit_authors": list("abcdef")}), 70)
        self.assertEqual(
            self.fetcher.calculate_bus_factor_score(
                {"all_commit_authors": list("abcdefgh")}), 70)
        self.assertEqual(
            self.fetcher.calculate_bus_factor_score(
                {"all_commit_authors": list("abcdefghi")}), 100)

    def test_popularity_and_donation_links_never_establish_funding(self):
        for metrics in ({"stars": 0}, {"stars": 1000000, "total_contributors": 1000},
                        {"stars": 1000, "total_contributors": None}):
            for funding in (None, {"has_funding_file": True,
                                  "funding_sources": ["github_sponsors", "open_collective"]}):
                self.assertEqual(self.fetcher.calculate_funding_score(metrics, funding),
                                 (None, "unknown"))

    def test_activity_score_excludes_unknown_funding(self):
        metrics = {"days_since_last_push": 0, "days_since_last_release": 0,
                   "commits_last_30_days": 50, "unique_contributors_last_90_days": 10,
                   "all_commit_authors": list("abcdefghij")}
        self.assertEqual(self.fetcher.assess_health(metrics)["overall_score"], 100)
        metrics.update(stars=1000000, funding_info={"has_funding_file": True})
        self.assertEqual(self.fetcher.assess_health(metrics)["overall_score"], 100)

    def test_no_recent_authors_omits_concentration_weight(self):
        metrics = {"days_since_last_push": 400, "days_since_last_release": 400,
                   "commits_last_30_days": 0, "unique_contributors_last_90_days": 0,
                   "all_commit_authors": []}
        assessment = self.fetcher.assess_health(metrics)
        self.assertEqual(assessment["overall_score"], 5)
        self.assertEqual(assessment["bus_factor"], "unknown")

    def test_missing_evidence_is_not_a_composite_or_concentration_score(self):
        assessment = self.fetcher.assess_health({"stars": 1000000})
        self.assertIsNone(assessment["overall_score"])
        self.assertIsNone(assessment["funding_score"])
        self.assertEqual(assessment["bus_factor"], "unknown")
        self.assertEqual(assessment["methodology_version"], "2.1")
        # The CLI must also handle unknown values without formatting None as a number.
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()) as output:
            metrics_mod.print_report({"stars": 1000000}, assessment)
        self.assertIn("not rated", output.getvalue())


class FrontmatterRewriteTest(unittest.TestCase):
    FRONTMATTER = (
        "dependencies = [\"X\"]\n"
        "date = '2025-06-08T15:30:11+08:00'\n"
        "title = 'Demo'\n"
        "description = 'D'\n"
        "maintainers = [\"Alice\"]\n"
        "\n"
        "[health]\n"
        "  funding = \"old\"\n"
        "  maintenance = \"old\"\n"
        "  contributors = \"old\"\n"
        "  bus_factor = \"old\"\n"
        "  score = 1\n"
        "[links]\n"
        "  github = \"o/r\"\n"
        "[metrics]\n"
        "  updated_at = \"2020-01-01\"\n"
        "  stars = 1\n"
        "  forks = 1\n"
        "  contributors = 42\n"
        "  commits_30d = 1\n"
        "  commits_90d = 1\n"
        "  bus_factor_people = 1\n"
    )

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.path = self.root / "demo.md"
        self.path.write_text(f"+++\n{self.FRONTMATTER}\n+++\n\nBody line 1\nBody line 2\n",
                             encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def update(self, metrics=None, assessment=None):
        assessment = assessment or {
            "overall_score": 88, "funding": "stable", "maintenance": "active",
            "contributors": "healthy", "bus_factor": "low",
        }
        metrics = metrics if metrics is not None else {
            "stars": 100, "forks": 2, "total_contributors": 7,
            "commits_last_30_days": 3, "commits_last_90_days": 9,
            "bus_factor_people": 4,
        }
        return metrics_mod.update_hugo_frontmatter(str(self.path), assessment, metrics)

    def parsed(self):
        text = self.path.read_text(encoding="utf-8")
        return tomllib.loads(text.split("+++")[1]), text

    def test_replaces_sections_and_preserves_everything_else(self):
        self.assertTrue(self.update())
        data, text = self.parsed()

        self.assertEqual(data["health"], {
            "funding": "unknown", "maintenance": "active",
            "contributors": "healthy", "bus_factor": "low",
            "methodology_version": "2.1", "assessment": "automated", "score": 88,
        })
        self.assertEqual(data["metrics"]["stars"], 100)
        self.assertEqual(data["metrics"]["commits_30d"], 3)
        self.assertEqual(data["metrics"]["commits_90d"], 9)
        self.assertEqual(data["metrics"]["bus_factor_people"], 4)
        self.assertEqual(data["metrics"]["contributors"], 7)
        self.assertEqual(data["metrics"]["updated_at"], datetime.now().strftime("%Y-%m-%d"))

        # Untouched front matter keys survive.
        self.assertEqual(data["dependencies"], ["X"])
        self.assertEqual(data["date"], "2025-06-08T15:30:11+08:00")
        self.assertEqual(data["title"], "Demo")
        self.assertEqual(data["maintainers"], ["Alice"])
        self.assertEqual(data["links"], {"github": "o/r"})
        # Body is byte-identical.
        self.assertIn("\n+++\n\nBody line 1\nBody line 2\n", text)
        # Each section appears exactly once.
        self.assertEqual(text.count("[health]"), 1)
        self.assertEqual(text.count("[metrics]"), 1)

    def test_sample_coverage_is_persisted_without_overwriting_editorial_evidence(self):
        original = self.path.read_text()
        self.path.write_text(original.replace("[health]", '[review]\n  source = "https://example.org/report"\n  checked_at = "2026-10-02"\n[health]'))
        self.assertTrue(self.update(metrics={
            "unique_contributors_last_90_days": 7,
            "commits_sample_truncated": True,
            "contributors_unavailable": True,
        }))
        data, _ = self.parsed()
        self.assertTrue(data["metrics"]["commits_sample_truncated"])
        self.assertTrue(data["metrics"]["contributors_unavailable"])
        self.assertEqual(data["metrics"]["contributors_90d"], 7)
        self.assertEqual(data["review"]["source"], "https://example.org/report")
        self.assertEqual(data["health"]["score"], 88)

    def test_metrics_last_section_round_trips(self):
        # The sample already has [metrics] as the final table; a second update
        # must be idempotent.
        self.update()
        first = self.path.read_text(encoding="utf-8")
        self.update()
        self.assertEqual(self.path.read_text(encoding="utf-8"), first)

    def test_unavailable_contributors_preserves_existing_value(self):
        self.assertTrue(self.update(metrics={
            "stars": 100, "forks": 2, "total_contributors": None,
            "contributors_unavailable": True,
            "commits_last_30_days": 3, "commits_last_90_days": 9,
            "bus_factor_people": 4,
        }))
        data, _ = self.parsed()
        self.assertEqual(data["metrics"]["contributors"], 42)

    def test_missing_sections_are_appended(self):
        self.path.write_text("+++\ntitle = 'T'\n+++\n\nBody\n", encoding="utf-8")
        self.assertTrue(self.update())
        data, text = self.parsed()
        self.assertEqual(data["health"]["score"], 88)
        self.assertEqual(data["metrics"]["stars"], 100)
        self.assertEqual(text.count("[health]"), 1)
        self.assertEqual(text.count("[metrics]"), 1)
        self.assertTrue(text.endswith("\n+++\n\nBody\n"))

    def test_invalid_existing_toml_is_refused_untouched(self):
        original = "+++\ntitle = 'T'\nbad = [\n+++\n\nBody\n"
        self.path.write_text(original, encoding="utf-8")
        self.assertFalse(self.update())
        self.assertEqual(self.path.read_text(encoding="utf-8"), original)

    def test_missing_file_returns_false(self):
        self.assertFalse(metrics_mod.update_hugo_frontmatter(
            str(self.root / "nope.md"), {"overall_score": 1}, {}))

    def test_split_frontmatter_round_trip(self):
        text = self.path.read_text(encoding="utf-8")
        prefix, body, suffix = metrics_mod.split_frontmatter(text)
        self.assertEqual(prefix + body + suffix, text)
        self.assertTrue(suffix.startswith("\n+++"))


class CountFromLinkTest(unittest.TestCase):
    def setUp(self):
        self.fetcher = metrics_mod.GitHubMetricsFetcher(token="dummy")

    def test_single_page_without_link_uses_length(self):
        calls = []

        def fake(endpoint, **kwargs):
            calls.append(endpoint)
            return [{"id": 1}, {"id": 2}, {"id": 3}], {}

        self.fetcher._api_request = fake
        self.assertEqual(self.fetcher._count_from_link("/x"), 3)
        self.assertIn("per_page=1", calls[0])

    def test_link_last_page_number_is_the_count(self):
        def fake(endpoint, **kwargs):
            return [{"id": 1}], {
                "Link": ('<https://api.github.com/x?per_page=1&page=2>; rel="next", '
                         '<https://api.github.com/x?per_page=1&page=500>; rel="last"')
            }

        self.fetcher._api_request = fake
        self.assertEqual(self.fetcher._count_from_link("/x"), 500)

    def test_existing_per_page_is_rewritten(self):
        seen = {}

        def fake(endpoint, **kwargs):
            seen["url"] = endpoint
            return [{"id": 1}], {}

        self.fetcher._api_request = fake
        self.fetcher._count_from_link("/x?per_page=100&foo=bar")
        self.assertIn("per_page=1", seen["url"])
        self.assertNotIn("per_page=100", seen["url"])

    def test_unavailable_contributors_propagates(self):
        def fake(endpoint, **kwargs):
            raise metrics_mod.ContributorsUnavailable("too large")

        self.fetcher._api_request = fake
        with self.assertRaises(metrics_mod.ContributorsUnavailable):
            self.fetcher._count_from_link("/contributors", unavailable_on_too_large=True)


def _commit(days_ago, author):
    when = datetime.now() - timedelta(days=days_ago)
    return {
        "commit": {
            "committer": {"date": when.strftime("%Y-%m-%dT%H:%M:%SZ")},
            "author": {"name": author},
        },
        "author": {"login": author},
    }


class _RoutingAPI:
    """Minimal GitHub router for fetch_repo_metrics (no network)."""

    def __init__(self, truncated):
        self.truncated = truncated
        self.calls = []

    def __call__(self, endpoint, *, allow_404=False, unavailable_on_too_large=False):
        self.calls.append(endpoint)
        if endpoint.endswith("/repos/o/r"):
            return {"name": "r", "full_name": "o/r", "stargazers_count": 5,
                    "forks_count": 1, "open_issues_count": 0,
                    "pushed_at": "2026-01-01T00:00:00Z"}, {}
        if "contents/.github/FUNDING.yml" in endpoint:
            return None, {}
        if endpoint.endswith("/topics"):
            return {"names": []}, {}
        if "/releases" in endpoint:
            return [], {}
        if "/contributors" in endpoint:
            return [{"id": 1}], {
                "Link": '<https://api.github.com/repos/o/r/contributors?per_page=1&page=42>; rel="last"'
            }
        if "/commits" in endpoint:
            if "since=" in endpoint:
                page = 7 if "until=" in endpoint else 55
                return [{"id": 1}], {
                    "Link": f'<https://api.github.com/repos/o/r/commits?per_page=1&page={page}>; rel="last"'
                }
            if "page=2" in endpoint:
                link = ('<https://api.github.com/repos/o/r/commits?per_page=100&page=3>; rel="next"'
                        if self.truncated else None)
                return [_commit(1, "b") for _ in range(100)], ({"Link": link} if link else {})
            if self.truncated:
                return ([_commit(1, "a") for _ in range(100)],
                        {"Link": '<https://api.github.com/repos/o/r/commits?per_page=100&page=2>; rel="next"'})
            return ([_commit(1, "a") for _ in range(5)] + [_commit(200, "old")], {})
        raise AssertionError(f"unexpected endpoint {endpoint}")


class CommitCountFallbackTest(unittest.TestCase):
    def run_fetch(self, truncated):
        fetcher = metrics_mod.GitHubMetricsFetcher(token="dummy")
        api = _RoutingAPI(truncated)
        fetcher._api_request = api
        metrics = fetcher.fetch_repo_metrics("o", "r")
        return metrics, api

    def test_non_truncated_sample_needs_no_extra_count_calls(self):
        metrics, api = self.run_fetch(truncated=False)
        self.assertFalse(metrics["commits_sample_truncated"])
        self.assertEqual(metrics["commits_last_30_days"], 5)
        self.assertEqual(metrics["commits_last_90_days"], 5)
        self.assertEqual(metrics["total_contributors"], 42)
        self.assertNotIn("old", metrics["all_commit_authors"])
        self.assertFalse([c for c in api.calls if "since=" in c],
                         "sample reached the boundary; no count calls expected")

    def test_truncated_sample_uses_exact_count_fallback(self):
        metrics, api = self.run_fetch(truncated=True)
        self.assertTrue(metrics["commits_sample_truncated"])
        since_calls = [c for c in api.calls if "since=" in c]
        self.assertEqual(len(since_calls), 2)
        # 30d -> 55, 30-90d -> 7, so 90d -> 62
        self.assertEqual(metrics["commits_last_30_days"], 55)
        self.assertEqual(metrics["commits_last_90_days"], 62)
        # Counts come from the Link "last" page, one request each.
        self.assertEqual(metrics["total_contributors"], 42)


if __name__ == "__main__":
    unittest.main()
