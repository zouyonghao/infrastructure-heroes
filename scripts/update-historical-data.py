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
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def load_project_data(project_file: Path) -> dict:
    """Extract health data from project frontmatter"""
    content = project_file.read_text()
    
    import re
    
    # Extract title
    title_match = re.search(r'title\s*=\s*"([^"]+)"', content)
    title = title_match.group(1) if title_match else project_file.stem
    
    # Extract health section
    health_data = {}
    health_match = re.search(r'\[health\](.*?)\[', content, re.DOTALL)
    if health_match:
        health_section = health_match.group(1)
        
        # Extract score
        score_match = re.search(r'score\s*=\s*(\d+)', health_section)
        health_data['score'] = int(score_match.group(1)) if score_match else None
        
        # Extract dimensions
        for dim in ['funding', 'maintenance', 'contributors', 'bus_factor']:
            match = re.search(rf'{dim}\s*=\s*"([^"]+)"', health_section)
            health_data[dim] = match.group(1) if match else 'unknown'
    
    # Extract metrics section
    metrics_data = {}
    metrics_match = re.search(r'\[metrics\](.*?)(?:\[|$)', content, re.DOTALL)
    if metrics_match:
        metrics_section = metrics_match.group(1)
        
        for field in ['stars', 'forks', 'contributors', 'commits_30d', 'commits_90d', 'bus_factor_people']:
            match = re.search(rf'{field}\s*=\s*(\d+)', metrics_section)
            if match:
                metrics_data[field] = int(match.group(1))
    
    return {
        'name': title,
        'slug': project_file.stem,
        'health': health_data,
        'metrics': metrics_data
    }


def create_snapshot():
    """Create a monthly snapshot of all project health data"""
    projects_dir = Path('content/projects')
    data_dir = Path('data/historical')
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all project data
    project_files = [f for f in projects_dir.glob('*.md') if f.name != '_index.md']
    projects = []
    
    for pf in project_files:
        try:
            data = load_project_data(pf)
            if data['health'].get('score') is not None:
                projects.append(data)
        except Exception as e:
            print(f"⚠️  Error loading {pf}: {e}")
    
    # Create snapshot
    today = datetime.now()
    snapshot = {
        'date': today.strftime('%Y-%m-%d'),
        'month': today.strftime('%Y-%m'),
        'total_projects': len(projects),
        'projects': projects,
        'summary': {
            'critical': len([p for p in projects if p['health']['score'] < 60]),
            'warning': len([p for p in projects if 60 <= p['health']['score'] < 80]),
            'healthy': len([p for p in projects if p['health']['score'] >= 80]),
            'avg_score': sum(p['health']['score'] for p in projects) / len(projects) if projects else 0
        }
    }
    
    # Save monthly snapshot
    month_file = data_dir / f"{today.strftime('%Y-%m')}.json"
    
    # Load existing monthly data if present
    monthly_data = []
    if month_file.exists():
        with open(month_file) as f:
            monthly_data = json.load(f)
    
    # Check if we already have an entry for today
    monthly_data = [e for e in monthly_data if e['date'] != snapshot['date']]
    monthly_data.append(snapshot)
    
    # Save updated monthly file
    with open(month_file, 'w') as f:
        json.dump(monthly_data, f, indent=2)
    
    print(f"✅ Created snapshot: {month_file}")
    
    # Update summary stats
    update_summary_stats(data_dir)
    
    return snapshot


def update_summary_stats(data_dir: Path):
    """Update aggregate statistics across all historical data"""
    all_snapshots = []
    
    for month_file in sorted(data_dir.glob('*.json')):
        if month_file.name == 'summary.json':
            continue
        try:
            with open(month_file) as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_snapshots.extend(data)
                else:
                    all_snapshots.append(data)
        except Exception as e:
            print(f"⚠️  Error loading {month_file}: {e}")
    
    if not all_snapshots:
        print("⚠️  No historical data found")
        return
    
    # Calculate trends
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_snapshots': len(all_snapshots),
        'date_range': {
            'from': all_snapshots[0]['date'],
            'to': all_snapshots[-1]['date']
        },
        'current_status': all_snapshots[-1]['summary'] if all_snapshots else {},
        'trends': {
            'avg_score_over_time': [
                {'date': s['date'], 'value': s['summary']['avg_score']}
                for s in all_snapshots
            ],
            'critical_count_over_time': [
                {'date': s['date'], 'value': s['summary']['critical']}
                for s in all_snapshots
            ]
        }
    }
    
    # Save summary
    summary_file = data_dir / 'summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Updated summary: {summary_file}")


def generate_trend_report():
    """Generate a markdown report of trends"""
    data_dir = Path('data/historical')
    summary_file = data_dir / 'summary.json'
    
    if not summary_file.exists():
        print("⚠️  No summary data available")
        return
    
    with open(summary_file) as f:
        summary = json.load(f)
    
    # Generate report
    report_path = Path('content/methodology.md')
    if report_path.exists():
        content = report_path.read_text()
        
        # Find or create trends section
        trends_section = f"""

## 📈 Health Trends

_Last updated: {summary['generated_at'][:10]}_

### Current Status

| Metric | Value |
|--------|-------|
| Total Projects | {summary['current_status'].get('total_projects', 'N/A')} |
| 🟢 Healthy (80-100) | {summary['current_status'].get('healthy', 'N/A')} |
| 🟡 Warning (60-79) | {summary['current_status'].get('warning', 'N/A')} |
| 🔴 Critical (0-59) | {summary['current_status'].get('critical', 'N/A')} |
| Average Score | {summary['current_status'].get('avg_score', 0):.1f} |

### Historical Data Points

{summary['total_snapshots']} snapshots recorded from {summary['date_range']['from']} to {summary['date_range']['to']}

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
        
        report_path.write_text(content)
        print(f"✅ Updated trends in {report_path}")


def main():
    print("📊 Infrastructure Heroes - Historical Data Update")
    print("=" * 60)
    
    # Create snapshot
    snapshot = create_snapshot()
    
    # Print summary
    print("\n📋 Current Status:")
    print(f"  Total Projects: {snapshot['summary']['total_projects']}")
    print(f"  🟢 Healthy: {snapshot['summary']['healthy']}")
    print(f"  🟡 Warning: {snapshot['summary']['warning']}")
    print(f"  🔴 Critical: {snapshot['summary']['critical']}")
    print(f"  📊 Average Score: {snapshot['summary']['avg_score']:.1f}")
    
    # Generate trend report
    generate_trend_report()
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
