#!/usr/bin/env python3
"""
Update historical data tracking for Infrastructure Heroes
Usage: python scripts/update-historical-data.py

This script:
1. Reads all project health scores
2. Creates a historical snapshot for trend analysis
3. Updates aggregate statistics

Snapshots are stored in data/historical/YYYY-MM.json
"""

import json
import tomllib
from pathlib import Path
from datetime import datetime

# Health buckets used across the site (see layouts/shortcodes/health-trends.html).
HEALTHY_MIN = 80
WARNING_MIN = 60


def split_frontmatter(text: str):
    """Split a Hugo document into (frontmatter, body).

    The frontmatter is the TOML between the leading ``+++`` fences. Returns
    ``(None, text)`` when the file does not start with a ``+++`` fence.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "+++":
        return None, text

    for i in range(1, len(lines)):
        if lines[i].strip() == "+++":
            return "".join(lines[1:i]), "".join(lines[i + 1:])

    return None, text


def load_project_data(project_file: Path) -> dict:
    """Extract health and metrics data from a project's TOML frontmatter.

    A real TOML parser is used, so ``[health]`` is found regardless of where
    it sits relative to the other tables (the old regex only matched when
    another ``[...]`` table followed it).
    """
    frontmatter, _ = split_frontmatter(project_file.read_text(encoding="utf-8"))
    if frontmatter is None:
        raise ValueError("missing +++ TOML frontmatter")

    data = tomllib.loads(frontmatter)

    return {
        "name": data.get("title", project_file.stem),
        "slug": project_file.stem,
        "health": dict(data.get("health") or {}),
        "metrics": dict(data.get("metrics") or {}),
    }


def compute_summary(projects: list) -> dict:
    """Compute the health summary / score distribution for a list of projects.

    Buckets match the site: critical < 60, warning 60-79, healthy >= 80.
    """
    scores = [p["health"]["score"] for p in projects
              if isinstance(p["health"].get("score"), (int, float))]
    return {
        "critical": sum(1 for s in scores if s < WARNING_MIN),
        "warning": sum(1 for s in scores if WARNING_MIN <= s < HEALTHY_MIN),
        "healthy": sum(1 for s in scores if s >= HEALTHY_MIN),
        "avg_score": sum(scores) / len(scores) if scores else None,
        "unrated": len(projects) - len(scores),
    }


def normalize_monthly_data(raw):
    """Normalize a monthly JSON document into a list of snapshots.

    Current files hold a list of snapshots; legacy files held a single
    snapshot object. Anything else is a hard error.
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [raw]
    raise ValueError(
        f"unexpected monthly JSON type {type(raw).__name__}; "
        "expected a list of snapshots or a single snapshot object"
    )


def create_snapshot(
    projects_dir: Path = Path("content/projects"),
    data_dir: Path = Path("data/historical"),
):
    """Create a monthly snapshot of all project health data"""
    data_dir.mkdir(parents=True, exist_ok=True)

    # Load all project data
    project_files = [f for f in projects_dir.glob("*.md") if f.name != "_index.md"]
    projects = []

    for pf in project_files:
        try:
            data = load_project_data(pf)
        except Exception as e:
            print(f"⚠️  Error loading {pf}: {e}")
            continue
        projects.append(data)

    # Create snapshot. total_projects is stored both at the top level and
    # inside summary: summary.json copies the latest snapshot's summary into
    # current_status, which is what the trend report reads.
    today = datetime.now()
    total = len(projects)
    summary = compute_summary(projects)
    summary["total_projects"] = total

    snapshot = {
        "methodology_version": "2.0",
        "date": today.strftime("%Y-%m-%d"),
        "month": today.strftime("%Y-%m"),
        "total_projects": total,
        "projects": projects,
        "summary": summary,
    }

    # Save monthly snapshot
    month_file = data_dir / f"{today.strftime('%Y-%m')}.json"

    # Load existing monthly data if present (list, or legacy single object)
    monthly_data = []
    if month_file.exists():
        with open(month_file, encoding="utf-8") as f:
            monthly_data = normalize_monthly_data(json.load(f))

    # Check if we already have an entry for today
    monthly_data = [e for e in monthly_data
                    if (e["date"], e.get("methodology_version", "1.0")) !=
                    (snapshot["date"], snapshot["methodology_version"])]
    monthly_data.append(snapshot)

    # Save updated monthly file
    with open(month_file, "w", encoding="utf-8") as f:
        json.dump(monthly_data, f, indent=2)

    print(f"✅ Created snapshot: {month_file}")

    # Update summary stats
    update_summary_stats(data_dir)

    return snapshot


def update_summary_stats(data_dir: Path):
    """Update aggregate statistics across all historical data"""
    all_snapshots = []

    for month_file in sorted(data_dir.glob("*.json")):
        if month_file.name == "summary.json":
            continue
        try:
            with open(month_file, encoding="utf-8") as f:
                data = json.load(f)
            all_snapshots.extend(normalize_monthly_data(data))
        except Exception as e:
            print(f"⚠️  Error loading {month_file}: {e}")

    if not all_snapshots:
        print("⚠️  No historical data found")
        return

    all_snapshots.sort(key=lambda s: (s["date"], s.get("methodology_version", "1.0")))
    current_summary = all_snapshots[-1].get("summary", {})
    scored_snapshots = [s for s in all_snapshots
                        if s["summary"].get("avg_score") is not None]
    last_scored = scored_snapshots[-1]["summary"] if scored_snapshots else {}

    # Calculate trends
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_snapshots": len(all_snapshots),
        "date_range": {
            "from": all_snapshots[0]["date"],
            "to": all_snapshots[-1]["date"],
        },
        "current_status": current_summary,
        "last_scored_date": scored_snapshots[-1]["date"] if scored_snapshots else None,
        "trends": {
            "avg_score_over_time": [
                {"date": s["date"], "value": s["summary"]["avg_score"]}
                for s in scored_snapshots
            ],
            "critical_count_over_time": [
                {"date": s["date"], "value": s["summary"]["critical"]}
                for s in scored_snapshots
            ],
            # Distribution of the latest scored snapshot; consumed by
            # layouts/shortcodes/health-trends.html.
            "score_distribution": {
                "healthy": last_scored.get("healthy", 0),
                "warning": last_scored.get("warning", 0),
                "critical": last_scored.get("critical", 0),
            },
        },
    }

    # Save summary
    summary_file = data_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Updated summary: {summary_file}")


def generate_trend_report():
    """Generate a markdown report of trends"""
    data_dir = Path("data/historical")
    summary_file = data_dir / "summary.json"

    if not summary_file.exists():
        print("⚠️  No summary data available")
        return

    with open(summary_file, encoding="utf-8") as f:
        summary = json.load(f)

    # Generate report
    report_path = Path("content/methodology.md")
    if report_path.exists():
        content = report_path.read_text(encoding="utf-8")

        # Report collection coverage separately from archived score estimates.
        trends_section = f"""

## 📈 Health Trends

_Last collection: {summary['generated_at'][:10]}_

Projects collected: {summary['current_status'].get('total_projects', 'N/A')}. Projects without an overall rating: {summary['current_status'].get('unrated', 0)}.

{summary['total_snapshots']} snapshots recorded from {summary['date_range']['from']} to {summary['date_range']['to']}.

Earlier numeric scores are archived v1.0 estimates, not current health assessments. See the historical estimates section above.

"""

        # Check if trends section exists
        if '## 📈 Health Trends' in content:
            # Replace existing section
            import re
            content = re.sub(
                r'## 📈 Health Trends.*?(?=\n## |\Z)',
                trends_section.strip() + '\n\n',
                content,
                flags=re.DOTALL
            )
        else:
            # Append to end
            content = content.rstrip() + '\n\n' + trends_section

        report_path.write_text(content, encoding="utf-8")
        print(f"✅ Updated trends in {report_path}")


def main():
    print("📊 Infrastructure Heroes - Historical Data Update")
    print("=" * 60)

    # Create snapshot
    snapshot = create_snapshot()

    # Print summary
    print("\n📋 Current Status:")
    print(f"  Total Projects: {snapshot['total_projects']}")
    print(f"  Unrated: {snapshot['summary']['unrated']}")

    # Generate trend report
    generate_trend_report()

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
