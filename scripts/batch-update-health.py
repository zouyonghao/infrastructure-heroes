#!/usr/bin/env python3
"""
Batch update activity indicators for all projects
Usage: python scripts/batch-update-health.py [--dry-run] [--limit 10]

This script:
1. Reads all project files
2. Extracts GitHub repo from [links] section
3. Fetches metrics from GitHub API
4. Describes activity indicators using Methodology v2.1
5. Updates project frontmatter

Requirements:
- GITHUB_TOKEN environment variable
- Internet connection to GitHub API
"""

import argparse
import os
import sys
from pathlib import Path

# Repository root (batch-update-health.py lives in <root>/scripts/)
REPO_ROOT = Path(__file__).resolve().parent.parent

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    # Import using importlib since filename has hyphens
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fetch_metrics", 
        str(Path(__file__).resolve().parent / "fetch-github-metrics.py")
    )
    fetch_metrics = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fetch_metrics)
    GitHubMetricsFetcher = fetch_metrics.GitHubMetricsFetcher
    update_hugo_frontmatter = fetch_metrics.update_hugo_frontmatter
    FetchError = fetch_metrics.FetchError
except Exception as e:
    print(f"❌ Could not import fetch-github-metrics: {e}")
    sys.exit(1)


def extract_github_repo(project_file: Path) -> str:
    """Extract GitHub repo from project frontmatter"""
    content = project_file.read_text()
    
    # Find links.github in frontmatter
    import re
    match = re.search(r'\[links\].*?github\s*=\s*"([^"]+)"', content, re.DOTALL)
    if match:
        return match.group(1)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Batch update activity indicators for all Infrastructure Heroes projects"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit to first N projects (for testing)"
    )
    parser.add_argument(
        "--filter",
        help="Only process projects matching this name pattern"
    )
    
    args = parser.parse_args()
    
    # Check for GitHub token (environment only)
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("⚠️  Warning: No GITHUB_TOKEN provided. API rate limits will be strict (60 requests/hour).")
        print("   Set the GITHUB_TOKEN environment variable for higher limits.")
        print()
    
    # Initialize fetcher
    fetcher = GitHubMetricsFetcher(token=token)
    
    # Get all project files
    projects_dir = REPO_ROOT / 'content/projects'
    project_files = sorted([f for f in projects_dir.glob('*.md') if f.name != '_index.md'])
    
    if args.filter:
        project_files = [f for f in project_files if args.filter in f.name]
    
    if args.limit:
        project_files = project_files[:args.limit]
    
    print(f"📊 Found {len(project_files)} projects to process")
    print("="*70)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    failed_projects = []
    
    for i, project_file in enumerate(project_files, 1):
        project_name = project_file.stem
        print(f"\n[{i}/{len(project_files)}] Processing: {project_name}")
        
        # Extract GitHub repo
        github_repo = extract_github_repo(project_file)
        if not github_repo:
            print(f"  ⚠️  No GitHub link found, skipping")
            skip_count += 1
            continue
        
        print(f"  📎 GitHub: {github_repo}")
        
        if args.dry_run:
            print(f"  🔍 Dry run - would fetch metrics and update {project_file}")
            success_count += 1
            continue
        
        # Fetch metrics
        try:
            parts = github_repo.split('/')
            if len(parts) != 2:
                raise ValueError(f"Invalid repo format: {github_repo}")
            
            owner, repo = parts
            metrics = fetcher.fetch_repo_metrics(owner, repo)
            
            if not metrics:
                raise FetchError("no metrics returned")
            
            # Calculate health assessment
            assessment = fetcher.assess_health(metrics)
            
            # Update frontmatter (refuses to write if any required endpoint failed)
            if not update_hugo_frontmatter(project_file, assessment, metrics):
                raise RuntimeError("failed to update front matter")
            
            print(f"  ✅ Updated: automated indicators "
                  f"({assessment.get('maintenance', 'unknown')}/"
                  f"{assessment.get('contributors', 'unknown')}/"
                  f"{assessment.get('bus_factor', 'unknown')}/"
                  f"{assessment.get('funding', 'unknown')})")
            success_count += 1
        except FetchError as e:
            print(f"  ❌ Fetch failed, skipping project: {e}")
            failed_projects.append(project_name)
            error_count += 1
        except Exception as e:
            print(f"  ❌ Error, skipping project: {e}")
            failed_projects.append(project_name)
            error_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("📋 Summary:")
    print(f"  ✅ Successfully updated: {success_count}")
    print(f"  ⏭️  Skipped (no GitHub link): {skip_count}")
    print(f"  ❌ Errors: {error_count}")
    if failed_projects:
        print(f"  Failed projects: {', '.join(failed_projects)}")
    print("="*70)

    # A systemic failure means CI must alert instead of silently committing.
    if not args.dry_run and error_count > len(project_files) / 2:
        print(f"\n❌ Systemic failure: {error_count}/{len(project_files)} projects failed. Exiting nonzero.")
        sys.exit(1)
    
    if not args.dry_run and success_count > 0:
        print("\n📝 Next steps:")
        print("  1. Review the updated files with: git diff content/projects/")
        print("  2. Build site locally: hugo server -D")
        print("  3. Commit changes: git add content/projects/ && git commit -m 'Update activity indicators'")


if __name__ == "__main__":
    main()
