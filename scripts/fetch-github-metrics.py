#!/usr/bin/env python3
"""
Infrastructure Heroes - GitHub Metrics Fetcher
Fetches project metrics from the GitHub API and describes activity indicators

Usage:
    python fetch-github-metrics.py --repo owner/repo [--output metrics.json]
    python fetch-github-metrics.py --repo owner/repo --frontmatter content/projects/project.md

Methodology v2.0 publishes activity indicators, not an overall health rating.
Funding is unknown unless separately reviewed against public evidence.

Authentication is read from the GITHUB_TOKEN environment variable only.
"""

import argparse
import base64
import json
import os
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

API_BASE = "https://api.github.com"
MAX_RETRIES = 4           # retries after the initial attempt
MAX_PAGES = 10            # pagination cap for generic list endpoints
COMMIT_SAMPLE_PAGES = 2   # newest 2x100 commits sampled for authors/bus factor
RETRY_BASE_DELAY = 1.0    # seconds, doubled on every attempt
RETRY_MAX_DELAY = 60.0    # upper bound for a single backoff sleep


class FetchError(Exception):
    """A required GitHub API request failed, even after retries."""


class ContributorsUnavailable(Exception):
    """GitHub refuses to enumerate contributors for this repository (list too large)."""


def _get_header(headers, name: str) -> Optional[str]:
    """Case-insensitive header lookup that works for both dicts and HTTPMessage."""
    if not headers:
        return None
    getter = getattr(headers, "get", None)
    if getter is not None:
        value = getter(name)
        if value is not None:
            return value
    lowered = {str(key).lower(): value for key, value in headers.items()}
    return lowered.get(name.lower())


def parse_link_rel(link_header: Optional[str], rel: str) -> Optional[str]:
    """Return the URL for a given ``rel`` in a GitHub ``Link`` header."""
    if not link_header:
        return None
    for part in link_header.split(","):
        match = re.match(r'\s*<([^>]+)>\s*;\s*rel\s*=\s*"([^"]*)"', part)
        if match and rel in match.group(2).split():
            return match.group(1)
    return None


def parse_next_link(link_header: Optional[str]) -> Optional[str]:
    """Return the URL of the ``rel="next"`` entry of a GitHub ``Link`` header."""
    return parse_link_rel(link_header, "next")


def page_from_url(url: Optional[str]) -> Optional[int]:
    """Extract the ``page`` query parameter from a paginated GitHub URL."""
    if not url:
        return None
    match = re.search(r'[?&]page=(\d+)', url)
    return int(match.group(1)) if match else None


def is_contributors_too_large(body: Optional[str]) -> bool:
    """True when a 403 response means GitHub cannot list contributors at all."""
    if not body:
        return False
    text = body.lower()
    return "too large" in text and "contributor" in text


def _retry_after_seconds(header_value: Optional[str]) -> Optional[float]:
    """Parse a ``Retry-After`` header (delay-seconds or HTTP-date) into seconds."""
    if not header_value:
        return None
    header_value = header_value.strip()
    try:
        return max(0.0, float(header_value))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(header_value)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())


def retry_delay(status_code: Optional[int], headers, body: Optional[str], attempt: int,
                max_retries: int = MAX_RETRIES) -> Optional[float]:
    """
    Decide whether a failed request should be retried.

    Returns the number of seconds to wait before the next attempt, or ``None``
    when the response must not be retried. A ``status_code`` of ``None`` denotes
    a network-level failure (timeout, connection reset, ...), which is retryable.

    Retried: 5xx, 429, and 403 responses carrying rate-limit signals
    (``Retry-After``, exhausted ``X-RateLimit-Remaining``, or a rate-limit
    message). ``Retry-After`` is honored (capped at ``RETRY_MAX_DELAY``);
    otherwise exponential backoff is used.
    """
    if attempt >= max_retries:
        return None

    retry_after = _retry_after_seconds(_get_header(headers, "Retry-After"))

    if status_code is None:
        retryable = True
    elif status_code in (429, 500, 502, 503, 504):
        retryable = True
    elif status_code == 403:
        remaining = _get_header(headers, "X-RateLimit-Remaining")
        message = (body or "").lower()
        retryable = bool(
            retry_after is not None or remaining == "0" or "rate limit" in message
        )
    else:
        retryable = False

    if not retryable:
        return None
    if retry_after is not None:
        return min(retry_after, RETRY_MAX_DELAY)
    return min(RETRY_BASE_DELAY * (2 ** attempt), RETRY_MAX_DELAY)


class GitHubMetricsFetcher:
    """GitHub project metrics fetcher - Infrastructure Heroes Methodology v2.0"""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.base_url = API_BASE
        self.request_count = 0

    def _request_headers(self) -> dict:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Infrastructure-Heroes-Metrics"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _raw_request(self, url: str):
        self.request_count += 1
        request = urllib.request.Request(url, headers=self._request_headers())
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode('utf-8')
            data = json.loads(raw) if raw.strip() else None
            return data, response.headers

    def _api_request(self, endpoint: str, *, allow_404: bool = False,
                     unavailable_on_too_large: bool = False):
        """
        Send a GitHub API request, retrying transient failures.

        Returns ``(data, headers)``. Raises :class:`FetchError` when the request
        cannot be completed, or :class:`ContributorsUnavailable` for the special
        403 "contributor list is too large" case. ``allow_404`` returns
        ``(None, headers)`` instead of failing when the resource is absent.
        """
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}{endpoint}"

        for attempt in range(MAX_RETRIES + 1):
            try:
                return self._raw_request(url)
            except urllib.error.HTTPError as error:
                body = ""
                try:
                    body = error.read().decode('utf-8', 'replace')
                except Exception:
                    pass

                if error.code == 404 and allow_404:
                    return None, error.headers
                if unavailable_on_too_large and error.code == 403 \
                        and is_contributors_too_large(body):
                    raise ContributorsUnavailable(
                        f"GitHub will not list contributors for {endpoint}"
                    ) from error

                delay = retry_delay(error.code, error.headers, body, attempt)
                if delay is None:
                    raise FetchError(
                        f"HTTP {error.code} for {endpoint}: {body[:200].strip()}"
                    ) from error
                print(f"⚠️  HTTP {error.code} on {endpoint}; retrying in {delay:.1f}s "
                      f"(attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            except FetchError:
                raise
            except Exception as error:
                delay = retry_delay(None, None, str(error), attempt)
                if delay is None:
                    raise FetchError(f"Request failed for {endpoint}: {error}") from error
                print(f"⚠️  Network error on {endpoint}: {error}; retrying in {delay:.1f}s "
                      f"(attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)

        raise FetchError(f"Request failed for {endpoint} after {MAX_RETRIES} retries")

    def _paginate(self, endpoint: str, *, unavailable_on_too_large: bool = False,
                  max_pages: int = MAX_PAGES) -> List[dict]:
        """Follow ``Link rel="next"`` and collect up to ``max_pages`` of list results."""
        items: List[dict] = []
        url: Optional[str] = endpoint
        for _ in range(max_pages):
            if not url:
                break
            data, headers = self._api_request(
                url, unavailable_on_too_large=unavailable_on_too_large
            )
            if isinstance(data, list):
                items.extend(data)
            elif data is not None:
                items.append(data)
            url = parse_next_link(_get_header(headers, "Link"))
        return items

    @staticmethod
    def _commit_date(commit: dict) -> Optional[datetime]:
        if not isinstance(commit, dict):
            return None
        raw = commit.get("commit", {}).get("committer", {}).get("date", "")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None

    def _count_from_link(self, endpoint: str, *,
                         unavailable_on_too_large: bool = False) -> int:
        """
        Return the exact item count for a list endpoint using a single request.

        Requests ``per_page=1`` and reads the ``Link rel="last"`` page number,
        which equals the total item count. When GitHub sends no ``Link`` header
        the response is a single page and its length is the count.
        """
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}{endpoint}"
        if re.search(r'[?&]per_page=\d+', url):
            url = re.sub(r'([?&]per_page=)\d+', r'\g<1>1', url)
        else:
            url += ("&" if "?" in url else "?") + "per_page=1"

        data, headers = self._api_request(
            url, unavailable_on_too_large=unavailable_on_too_large
        )
        if not isinstance(data, list):
            return 0
        last_page = page_from_url(parse_link_rel(_get_header(headers, "Link"), "last"))
        return last_page if last_page is not None else len(data)

    def fetch_commit_sample(self, owner: str, repo: str,
                            stop_before: Optional[datetime] = None,
                            max_pages: int = COMMIT_SAMPLE_PAGES) -> Tuple[List[dict], bool]:
        """
        Fetch the newest commits (newest first) up to ``max_pages`` pages.

        Returns ``(commits, truncated)``. ``truncated`` is True when the page cap
        was reached while more commits (and the 90-day boundary) remained, i.e.
        the sample is not sufficient to count the full activity window.
        """
        commits: List[dict] = []
        url: Optional[str] = f"/repos/{owner}/{repo}/commits?per_page=100"
        truncated = False
        for page_index in range(max_pages):
            if not url:
                break
            data, headers = self._api_request(url)
            if not isinstance(data, list) or not data:
                break
            commits.extend(data)
            next_url = parse_next_link(_get_header(headers, "Link"))
            if stop_before is not None:
                dates = [d for d in (self._commit_date(c) for c in data) if d is not None]
                if dates and min(dates) < stop_before:
                    # Reached the 90-day boundary: the sample is complete for the window.
                    next_url = None
            if next_url and page_index == max_pages - 1:
                truncated = True
            url = next_url
        return commits, truncated

    def fetch_repo_metrics(self, owner: str, repo: str) -> dict:
        """
        Fetch basic and extended repository metrics.

        Raises :class:`FetchError` when a required endpoint fails so callers never
        persist partial metrics.
        """
        print(f"📊 Fetching metrics for {owner}/{repo}...")

        # Basic information
        repo_data, _ = self._api_request(f"/repos/{owner}/{repo}")
        if not isinstance(repo_data, dict):
            raise FetchError(f"Unexpected repository response for {owner}/{repo}")

        metrics = {
            "name": repo_data.get("name"),
            "full_name": repo_data.get("full_name"),
            "description": repo_data.get("description"),
            "url": repo_data.get("html_url"),
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "open_issues": repo_data.get("open_issues_count", 0),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "pushed_at": repo_data.get("pushed_at"),
            "language": repo_data.get("language"),
            "license": repo_data.get("license", {}).get("spdx_id") if repo_data.get("license") else None,
            "archived": repo_data.get("archived", False),
            "disabled": repo_data.get("disabled", False),
        }

        # Time-window metrics
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        ninety_days_ago = today - timedelta(days=90)

        # Sample the newest commits (up to 2 pages / 200) for author counts and bus factor
        commits, truncated = self.fetch_commit_sample(
            owner, repo, stop_before=ninety_days_ago
        )
        metrics["commits_data"] = commits
        metrics["commits_sample_truncated"] = truncated

        recent_30d_commits = 0
        recent_90d_commits = 0
        authors_30d = set()
        authors_90d = set()
        all_commit_authors = []  # used for the bus-factor calculation

        for commit in commits:
            commit_time = self._commit_date(commit)
            if commit_time is None:
                continue
            author = commit.get("author", {}).get("login") if commit.get("author") else None
            if not author:
                # Fall back to the commit author name
                author = commit.get("commit", {}).get("author", {}).get("name")

            if author and commit_time > ninety_days_ago:
                all_commit_authors.append(author)

            if commit_time > thirty_days_ago:
                recent_30d_commits += 1
                if author:
                    authors_30d.add(author)

            if commit_time > ninety_days_ago:
                recent_90d_commits += 1
                if author:
                    authors_90d.add(author)

        if truncated:
            # The commit sample did not reach the 90-day boundary: get exact window counts with two per_page=1 requests.
            since_30d = thirty_days_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
            since_90d = ninety_days_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
            commits_30d = self._count_from_link(
                f"/repos/{owner}/{repo}/commits?since={since_30d}"
            )
            commits_30_to_90d = self._count_from_link(
                f"/repos/{owner}/{repo}/commits?since={since_90d}&until={since_30d}"
            )
            recent_30d_commits = commits_30d
            recent_90d_commits = commits_30d + commits_30_to_90d

        metrics["commits_last_30_days"] = recent_30d_commits
        metrics["commits_last_90_days"] = recent_90d_commits
        metrics["unique_contributors_last_30_days"] = len(authors_30d)
        metrics["unique_contributors_last_90_days"] = len(authors_90d)
        metrics["all_commit_authors"] = all_commit_authors

        # Last push time (pushed_at)
        if metrics.get("pushed_at"):
            try:
                pushed_time = datetime.fromisoformat(metrics["pushed_at"].replace("Z", "+00:00"))
                metrics["days_since_last_push"] = (today - pushed_time.replace(tzinfo=None)).days
            except ValueError:
                metrics["days_since_last_push"] = 365
        else:
            metrics["days_since_last_push"] = 365

        # Contributors: only the total is needed; read Link rel="last" from one per_page=1 request
        try:
            metrics["total_contributors"] = self._count_from_link(
                f"/repos/{owner}/{repo}/contributors",
                unavailable_on_too_large=True,
            )
            metrics["contributors_unavailable"] = False
        except ContributorsUnavailable:
            # GitHub refuses to list contributors for very large repositories; this is neither a failure nor a zero.
            print("⚠️  GitHub will not list contributors for this repository "
                  "(list too large); keeping the existing value.")
            metrics["total_contributors"] = None
            metrics["contributors_unavailable"] = True

        # Recent releases
        releases = self._paginate(f"/repos/{owner}/{repo}/releases?per_page=5", max_pages=1)
        metrics["recent_releases"] = [
            {
                "tag": r.get("tag_name"),
                "published_at": r.get("published_at"),
                "prerelease": r.get("prerelease", False)
            }
            for r in releases if isinstance(r, dict)
        ]

        # Time since the latest release
        if metrics["recent_releases"]:
            try:
                last_release = datetime.fromisoformat(
                    metrics["recent_releases"][0]["published_at"].replace("Z", "+00:00")
                )
                metrics["days_since_last_release"] = (today - last_release.replace(tzinfo=None)).days
            except (ValueError, AttributeError):
                metrics["days_since_last_release"] = 365
        else:
            metrics["days_since_last_release"] = 365

        # Fetch funding information
        funding_info = self.fetch_funding_info(owner, repo)
        metrics["funding_info"] = funding_info

        return metrics

    def calculate_maintenance_score(self, metrics: dict) -> int:
        """
        Compute the maintenance activity score (0-100) - Methodology v2.0

        Criteria:
        - Repository push recency (40 points)
        - GitHub release recency (30 points)
        - Commit activity (30 points)
        """
        score = 0

        # 1. Time since the last commit (40 points)
        days_since_push = metrics.get("days_since_last_push", 365)
        if days_since_push < 7:
            score += 40
        elif days_since_push < 30:
            score += 35
        elif days_since_push < 60:
            score += 25
        elif days_since_push < 90:
            score += 15
        elif days_since_push < 180:
            score += 10
        else:
            score += 5

        # 2. Release frequency (30 points)
        days_since_release = metrics.get("days_since_last_release", 365)
        if days_since_release < 30:
            score += 30
        elif days_since_release < 90:
            score += 25
        elif days_since_release < 180:
            score += 15
        elif days_since_release < 365:
            score += 10
        else:
            score += 5

        # 3. Activity level (30 points) - based on commits in the last 30 days
        commits_30d = metrics.get("commits_last_30_days", 0)
        if commits_30d >= 50:
            score += 30
        elif commits_30d >= 20:
            score += 25
        elif commits_30d >= 10:
            score += 20
        elif commits_30d >= 5:
            score += 15
        elif commits_30d >= 1:
            score += 10
        else:
            score += 0

        return min(score, 100)

    def calculate_contributors_score(self, metrics: dict) -> int:
        """
        Compute the contributor health score (0-100) - Methodology v2.0

        Criteria:
        - Active contributors in last 90 days (80%)
        - Contributor count bonus (20 points at 10+ authors)
        """
        # Based on active contributors in the last 90 days
        contributors_90d = metrics.get("unique_contributors_last_90_days", 0)

        # Base score: 8 points per contributor, capped at 80
        base_score = min(contributors_90d * 8, 80)

        # Count bonus: +20 points when there are 10+ contributors
        trend_bonus = 20 if contributors_90d >= 10 else 0

        return min(base_score + trend_bonus, 100)

    def calculate_bus_factor_score(self, metrics: dict) -> Optional[int]:
        """
        Compute the bus-factor risk score (0-100) - Methodology v2.0

        Higher score = lower risk

        Criteria:
        - Number of people accounting for 50% of recent commits
        - 5+ people = low risk (100)
        - 3-4 people = medium risk (70)
        - 2 people = high risk (40)
        - 1 person = critical risk (15)
        """
        authors = metrics.get("all_commit_authors", [])
        if not authors:
            return None  # No author evidence; unknown is not a midpoint score.

        # Count commits per author
        author_counts = Counter(authors)
        total_commits = len(authors)

        # Number of people needed to cover 50% of commits
        sorted_authors = author_counts.most_common()
        cumulative = 0
        people_for_50_percent = 0

        for author, count in sorted_authors:
            cumulative += count
            people_for_50_percent += 1
            if cumulative >= total_commits * 0.5:
                break

        metrics["bus_factor_people"] = people_for_50_percent

        # Score by bus-factor headcount
        if people_for_50_percent >= 5:
            return 100  # Low risk
        elif people_for_50_percent >= 3:
            return 70   # Medium risk
        elif people_for_50_percent >= 2:
            return 40   # High risk
        else:
            return 15   # Critical risk

    def fetch_funding_info(self, owner: str, repo: str) -> dict:
        """
        Fetch funding information from GitHub API

        Returns dict with funding sources found
        """
        funding_info = {
            "has_funding_file": False,
            "funding_sources": [],
            "has_sponsors": False,
            "sponsor_count": 0
        }

        # Check for FUNDING.yml file (404 == not present, not a failure)
        funding_content, _ = self._api_request(
            f"/repos/{owner}/{repo}/contents/.github/FUNDING.yml", allow_404=True
        )
        if funding_content and funding_content.get("content"):
            try:
                content = base64.b64decode(funding_content["content"]).decode('utf-8')
                funding_info["has_funding_file"] = True

                # Parse funding sources
                if 'github:' in content:
                    funding_info["funding_sources"].append("github_sponsors")
                if 'open_collective:' in content or 'opencollective:' in content:
                    funding_info["funding_sources"].append("open_collective")
                if 'patreon:' in content:
                    funding_info["funding_sources"].append("patreon")
                if 'tidelift:' in content:
                    funding_info["funding_sources"].append("tidelift")
                if 'ko_fi:' in content or 'ko-fi:' in content:
                    funding_info["funding_sources"].append("ko-fi")
                if 'liberapay:' in content:
                    funding_info["funding_sources"].append("liberapay")
                if 'custom:' in content:
                    funding_info["funding_sources"].append("custom")
            except Exception:
                pass

        # Check repository topics for funding-related tags
        topics_data, _ = self._api_request(f"/repos/{owner}/{repo}/topics", allow_404=True)
        if topics_data and "names" in topics_data:
            funding_topics = [t for t in topics_data["names"] if t in
                            ['funding', 'sponsors', 'donate', 'sustainability', 'open-collective']]
            if funding_topics:
                funding_info["funding_sources"].extend(funding_topics)

        return funding_info

    def calculate_funding_score(self, metrics: dict, funding_info: dict = None) -> Tuple[Optional[int], str]:
        """Popularity and donation links do not establish financial sustainability."""
        return None, "unknown"

    def assess_health(self, metrics: dict) -> dict:
        """
        Describe automated activity indicators using Methodology v2.0.
        """
        if not metrics:
            return {}

        # Dimension scores
        maintenance_score = self.calculate_maintenance_score(metrics)
        contributors_score = self.calculate_contributors_score(metrics)
        bus_factor_score = self.calculate_bus_factor_score(metrics)
        funding_info = metrics.get("funding_info")
        funding_score, funding_status = self.calculate_funding_score(metrics, funding_info)

        # Withhold the composite: these proxies cannot establish overall health.
        overall_score = None

        # Dimension status labels
        def get_maintenance_status(score):
            if score >= 70: return "active"
            elif score >= 40: return "moderate"
            else: return "inactive"

        def get_contributors_status(score):
            if score >= 70: return "healthy"
            elif score >= 40: return "declining"
            else: return "critical"

        def get_bus_factor_status(score):
            if score is None: return "unknown"
            if score >= 70: return "low"
            elif score >= 40: return "medium"
            else: return "high"

        assessment = {
            "overall_score": overall_score,
            "funding": funding_status,
            "funding_score": funding_score,
            "maintenance": get_maintenance_status(maintenance_score),
            "maintenance_score": maintenance_score,
            "contributors": get_contributors_status(contributors_score),
            "contributors_score": contributors_score,
            "bus_factor": get_bus_factor_status(bus_factor_score),
            "bus_factor_score": bus_factor_score,
            "calculated_at": datetime.now().isoformat(),
            "methodology_version": "2.0",
            "recommendations": []
        }

        # Recommendations
        if maintenance_score < 40:
            assessment["recommendations"].append("⚠️ Low maintenance activity - consider contributing code or documentation")

        if contributors_score < 40:
            assessment["recommendations"].append("Few authors observed in the recent commit sample; review project context")

        if bus_factor_score is not None and bus_factor_score < 40:
            assessment["recommendations"].append(f"Concentrated commit sample - {metrics.get('bus_factor_people', 1)} author(s) account for 50% of sampled commits")

        if funding_status == "critical":
            assessment["recommendations"].append("💰 Project likely lacks funding - consider sponsorship")

        return assessment


def print_report(metrics: dict, assessment: dict):
    """Print the assessment report."""
    print("\n" + "="*70)
    print(f"📋 Health Report: {metrics.get('full_name')}")
    print(f"   Methodology: v{assessment.get('methodology_version', '1.0')}")
    print("="*70)

    contributors = metrics.get('total_contributors')
    contributors_label = "unavailable" if contributors is None else f"{contributors}"

    print(f"\n📊 Basic Metrics:")
    print(f"  ⭐ Stars: {metrics.get('stars', 0):,}")
    print(f"  🍴 Forks: {metrics.get('forks', 0):,}")
    print(f"  🐛 Open Issues: {metrics.get('open_issues', 0):,}")
    print(f"  👥 Total Contributors: {contributors_label}")

    print(f"\n📈 Activity:")
    print(f"  📝 Commits (30d): {metrics.get('commits_last_30_days', 0)}")
    print(f"  📝 Commits (90d): {metrics.get('commits_last_90_days', 0)}")
    print(f"  👤 Active Contributors (90d): {metrics.get('unique_contributors_last_90_days', 0)}")
    print(f"  📅 Days Since Last Push: {metrics.get('days_since_last_push', 'N/A')}")
    print(f"  📅 Days Since Last Release: {metrics.get('days_since_last_release', 'N/A')}")

    print(f"\n🏥 Health Assessment:")
    print(f"  ┌──────────────────┬────────┬──────────────┐")
    print(f"  │ Dimension        │ Score  │ Status       │")
    print(f"  ├──────────────────┼────────┼──────────────┤")
    print(f"  │ 💰 Funding       │ {str(assessment.get('funding_score') or '—'):>3}/100 │ {assessment.get('funding', 'unknown'):>12} │")
    print(f"  │ 🔧 Maintenance   │ {assessment.get('maintenance_score', 0):>3}/100 │ {assessment.get('maintenance', 'unknown'):>12} │")
    print(f"  │ 👥 Contributors  │ {assessment.get('contributors_score', 0):>3}/100 │ {assessment.get('contributors', 'unknown'):>12} │")
    print(f"  │ 🚌 Bus Factor    │ {str(assessment.get('bus_factor_score') or '—'):>3}/100 │ {assessment.get('bus_factor', 'unknown'):>12} │")
    print(f"  ├──────────────────┼────────┼──────────────┤")
    print("  Overall health: not rated (insufficient evidence)")
    print(f"  └──────────────────┴────────┴──────────────┘")

    # Show funding sources if detected
    funding_info = metrics.get('funding_info', {})
    if funding_info and funding_info.get('funding_sources'):
        print(f"\n💰 Donation links detected (not evidence of income):")
        if funding_info.get('has_funding_file'):
            print(f"  ✅ FUNDING.yml file present")
        sources = funding_info.get('funding_sources', [])
        for source in set(sources):
            print(f"  • {source.replace('_', ' ').title()}")

    if assessment.get('recommendations'):
        print(f"\n⚠️  Recommendations:")
        for rec in assessment['recommendations']:
            print(f"  • {rec}")

    print("\n" + "="*70)
    if funding_info and funding_info.get('funding_sources'):
        print("💡 Donation links do not establish funding received or financial runway.")
    else:
        print("💡 Funding status is unknown; financial evidence requires a separate review.")
    print("="*70)


# --- Hugo front matter rewriting -------------------------------------------

_FRONTMATTER_RE = re.compile(r'\A(\+\+\+\r?\n)(.*?)(\r?\n\+\+\+)', re.DOTALL)
_SECTION_HEADER_RE = re.compile(r'^\s*\[([^\[\]]+)\]\s*$')


def split_frontmatter(content: str) -> Optional[Tuple[str, str, str]]:
    """
    Split a Hugo file into ``(prefix, frontmatter_body, suffix)``.

    ``prefix`` includes the opening ``+++`` line, ``suffix`` the closing
    delimiter and everything after it, so reassembling the three parts is
    byte-for-byte identical to the input.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return None
    # Suffix starts at the newline that precedes the closing delimiter so that
    # ``prefix + body + suffix`` reproduces the original bytes exactly.
    return match.group(1), match.group(2), content[match.start(3):]


def _section_bounds(lines: List[str], name: str) -> Optional[Tuple[int, int]]:
    """Locate a top-level TOML table ``[name]`` in ``lines`` (header to next header)."""
    start = None
    for index, line in enumerate(lines):
        header = _SECTION_HEADER_RE.match(line)
        if not header:
            continue
        if start is not None:
            return start, index
        if header.group(1).strip() == name:
            start = index
    if start is not None:
        return start, len(lines)
    return None


def _toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _render_section(name: str, values: Dict[str, object]) -> List[str]:
    lines = [f"[{name}]\n"]
    for key, value in values.items():
        if value is None:
            continue
        lines.append(f"  {key} = {_toml_value(value)}\n")
    return lines


def rewrite_health_and_metrics(frontmatter: str, health_values: Dict[str, object],
                               metrics_values: Dict[str, object]) -> str:
    """
    Replace only the top-level ``[health]`` and ``[metrics]`` TOML tables.

    Every other line of the front matter is preserved. Missing tables are
    appended. The ``[metrics]`` table is handled first so earlier line indices
    for ``[health]`` stay valid.
    """
    lines = frontmatter.splitlines(keepends=True)
    for name, values in (("metrics", metrics_values), ("health", health_values)):
        bounds = _section_bounds(lines, name)
        replacement = _render_section(name, values)
        if bounds is not None:
            start, end = bounds
            lines[start:end] = replacement
        else:
            if lines and not lines[-1].endswith(("\n", "\r")):
                lines[-1] += "\n"
            if lines and lines[-1].strip():
                lines.append("\n")
            lines.extend(replacement)
    return "".join(lines).rstrip("\r\n")


def update_hugo_frontmatter(filepath: str, assessment: dict, metrics: dict) -> bool:
    """Update a Hugo project file's front matter (replacing only [health] and [metrics])."""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ File not found: {filepath}")
        return False

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"❌ Could not read {filepath}: {error}")
        return False

    split = split_frontmatter(content)
    if not split:
        print(f"❌ Could not find front matter in file: {filepath}")
        return False
    prefix, frontmatter, suffix = split

    try:
        existing = tomllib.loads(frontmatter)
    except tomllib.TOMLDecodeError as error:
        print(f"❌ Existing front matter is not valid TOML ({error}); refusing to rewrite {filepath}")
        return False

    health_values = {
        "funding": "unknown",
        "maintenance": assessment.get('maintenance', 'unknown'),
        "contributors": assessment.get('contributors', 'unknown'),
        "bus_factor": assessment.get('bus_factor', 'unknown'),
        "methodology_version": "2.0",
        "assessment": "automated",
    }

    existing_metrics = existing.get("metrics")
    if not isinstance(existing_metrics, dict):
        existing_metrics = {}

    metrics_values: Dict[str, object] = {
        "updated_at": datetime.now().strftime('%Y-%m-%d'),
        "stars": int(metrics.get('stars', 0) or 0),
        "forks": int(metrics.get('forks', 0) or 0),
    }
    if metrics.get("contributors_unavailable"):
        # Never persist 0 for an endpoint that failed; keep the previous value.
        if "contributors" in existing_metrics:
            metrics_values["contributors"] = existing_metrics["contributors"]
    else:
        metrics_values["contributors"] = int(metrics.get('total_contributors', 0) or 0)
    metrics_values.update({
        "commits_30d": int(metrics.get('commits_last_30_days', 0) or 0),
        "commits_90d": int(metrics.get('commits_last_90_days', 0) or 0),
        "bus_factor_people": int(metrics.get('bus_factor_people', 0) or 0),
        "contributors_90d": int(metrics.get('unique_contributors_last_90_days', 0) or 0),
        "commits_sample_truncated": bool(metrics.get('commits_sample_truncated', False)),
        "contributors_unavailable": bool(metrics.get('contributors_unavailable', False)),
    })

    new_frontmatter = rewrite_health_and_metrics(frontmatter, health_values, metrics_values)

    try:
        tomllib.loads(new_frontmatter)
    except tomllib.TOMLDecodeError as error:
        print(f"❌ Refusing to write invalid front matter for {filepath}: {error}")
        return False

    path.write_text(prefix + new_frontmatter + suffix, encoding="utf-8")
    print(f"✅ Updated front matter in: {filepath}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Fetch GitHub metrics and describe activity indicators for Infrastructure Heroes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python fetch-github-metrics.py --repo openssl/openssl
    python fetch-github-metrics.py --repo torvalds/linux --output linux-metrics.json
    python fetch-github-metrics.py --repo python/cpython --frontmatter content/projects/python.md

Set GITHUB_TOKEN in the environment to raise the API rate limit.
        """
    )
    parser.add_argument(
        "--repo",
        help="Repository in format owner/repo (e.g., openssl/openssl)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for metrics JSON"
    )
    parser.add_argument(
        "--frontmatter",
        "-f",
        help="Update Hugo front matter in specified file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate scores but don't write to file"
    )

    args = parser.parse_args()

    if not args.repo:
        parser.print_help()
        print("\n❌ Please specify a repository with --repo owner/repo")
        sys.exit(1)

    # Parse owner/repo
    try:
        owner, repo = args.repo.split("/")
    except ValueError:
        print("❌ Invalid repo format. Use: owner/repo")
        sys.exit(1)

    # Create the fetcher and fetch metrics
    fetcher = GitHubMetricsFetcher()
    try:
        metrics = fetcher.fetch_repo_metrics(owner, repo)
    except FetchError as error:
        print(f"❌ Failed to fetch metrics: {error}")
        sys.exit(1)

    if not metrics:
        print("❌ Failed to fetch metrics")
        sys.exit(1)

    # Assess health
    assessment = fetcher.assess_health(metrics)

    print(f"🔢 GitHub API requests used: {fetcher.request_count}")

    # Print the report
    print_report(metrics, assessment)

    # Save JSON
    if args.output:
        output_data = {
            "metrics": metrics,
            "assessment": assessment,
            "generated_at": datetime.now().isoformat()
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\n💾 Metrics saved to: {args.output}")

    # Update Hugo front matter
    if args.frontmatter:
        if args.dry_run:
            print(f"\n🔍 Dry run - would update: {args.frontmatter}")
        else:
            success = update_hugo_frontmatter(args.frontmatter, assessment, metrics)
            if not success:
                sys.exit(1)

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
