#!/usr/bin/env python3
"""
Link maintainers to projects bidirectionally.

This script:
1. Reads all maintainer files and extracts their projects
2. Maps project titles to project slugs
3. Adds 'maintainers' field to project files
4. Cleans up maintainer 'projects' field to only include valid projects
"""

import os
import re
import glob
from pathlib import Path

CONTENT_DIR = Path("content")
PROJECTS_DIR = CONTENT_DIR / "projects"
MAINTAINERS_DIR = CONTENT_DIR / "maintainers"


def extract_frontmatter(content: str) -> tuple:
    """Extract frontmatter and body from markdown content."""
    if not content.startswith("+++"):
        return None, content
    
    # Find the end of frontmatter
    end_match = re.search(r'\n\+\+\+\s*\n', content[3:])
    if not end_match:
        return None, content
    
    frontmatter = content[3:3 + end_match.start()]
    body = content[3 + end_match.end():]
    return frontmatter, body


def parse_projects_from_frontmatter(frontmatter: str) -> list:
    """Parse projects array from frontmatter."""
    # Match projects = ["item1", "item2"] or projects = ['item1', 'item2']
    match = re.search(r'projects\s*=\s*\[(.*?)\]', frontmatter, re.DOTALL)
    if not match:
        return []
    
    items_str = match.group(1)
    # Extract quoted strings
    projects = re.findall(r'["\']([^"\']+)["\']', items_str)
    return projects


def get_project_slug_and_title(project_file: Path) -> tuple:
    """Get the slug and title from a project file."""
    slug = project_file.stem
    content = project_file.read_text()
    
    # Extract title
    match = re.search(r'title\s*=\s*["\']([^"\']+)["\']', content)
    title = match.group(1) if match else slug
    
    return slug, title


def create_project_mappings() -> tuple:
    """Create mappings between project slugs and titles."""
    slug_to_title = {}
    title_to_slug = {}
    
    for project_file in PROJECTS_DIR.glob("*.md"):
        if project_file.name == "_index.md":
            continue
        slug, title = get_project_slug_and_title(project_file)
        slug_to_title[slug] = title
        # Create normalized versions for matching
        title_to_slug[title] = slug
        title_to_slug[title.lower()] = slug
        # Also map common variations
        title_to_slug[title.replace(".", "").lower()] = slug
    
    return slug_to_title, title_to_slug


def normalize_project_name(name: str) -> str:
    """Normalize project name for matching."""
    return name.strip().replace(".", "").lower()


def find_matching_slug(project_name: str, title_to_slug: dict) -> str:
    """Find the project slug that matches a project name."""
    # Direct match
    if project_name in title_to_slug:
        return title_to_slug[project_name]
    
    # Case insensitive match
    normalized = normalize_project_name(project_name)
    if normalized in title_to_slug:
        return title_to_slug[normalized]
    
    # Try common variations
    variations = [
        project_name.replace(" ", ""),
        project_name.replace(" ", "-"),
        project_name.replace(".", "-"),
        project_name.replace(".", ""),
    ]
    for var in variations:
        if var in title_to_slug:
            return title_to_slug[var]
        if var.lower() in title_to_slug:
            return title_to_slug[var.lower()]
    
    return None


def process_maintainers(title_to_slug: dict) -> dict:
    """
    Process all maintainers and return a mapping of:
    {project_slug: [list_of_maintainer_names]}
    """
    project_to_maintainers = {}
    
    for maintainer_file in MAINTAINERS_DIR.glob("*.md"):
        if maintainer_file.name == "_index.md":
            continue
        
        content = maintainer_file.read_text()
        frontmatter, body = extract_frontmatter(content)
        if not frontmatter:
            continue
        
        # Get maintainer name
        match = re.search(r'title\s*=\s*["\']([^"\']+)["\']', frontmatter)
        maintainer_name = match.group(1) if match else maintainer_file.stem
        
        # Get projects
        projects = parse_projects_from_frontmatter(frontmatter)
        
        for project_name in projects:
            slug = find_matching_slug(project_name, title_to_slug)
            if slug:
                if slug not in project_to_maintainers:
                    project_to_maintainers[slug] = []
                if maintainer_name not in project_to_maintainers[slug]:
                    project_to_maintainers[slug].append(maintainer_name)
    
    return project_to_maintainers


def update_project_maintainers(project_to_maintainers: dict, dry_run: bool = True):
    """Add maintainers field to project files."""
    for slug, maintainers in project_to_maintainers.items():
        project_file = PROJECTS_DIR / f"{slug}.md"
        if not project_file.exists():
            continue
        
        content = project_file.read_text()
        
        # Check if already has maintainers field
        if "maintainers = " in content:
            print(f"  SKIP: {slug} already has maintainers field")
            continue
        
        # Find position to insert (before closing +++)
        # Look for the last occurrence of +++
        match = re.search(r'\n(\+\+\+)\s*\n', content)
        if not match:
            print(f"  ERROR: Could not find frontmatter end in {slug}")
            continue
        
        # Format maintainers list
        if len(maintainers) == 1:
            maintainers_str = f'["{maintainers[0]}"]'
        else:
            maintainers_str = "[" + ", ".join([f'"{m}"' for m in maintainers]) + "]"
        
        # Insert before closing +++
        insert_pos = match.start(1)
        new_content = (
            content[:insert_pos] +
            f"maintainers = {maintainers_str}\n" +
            content[insert_pos:]
        )
        
        if dry_run:
            print(f"  WOULD UPDATE: {slug} -> {maintainers_str}")
        else:
            project_file.write_text(new_content)
            print(f"  UPDATED: {slug}")


def clean_maintainer_projects(title_to_slug: dict, dry_run: bool = True):
    """
    Clean up maintainer projects field to only include valid projects.
    Returns count of cleaned maintainers.
    """
    cleaned_count = 0
    
    for maintainer_file in MAINTAINERS_DIR.glob("*.md"):
        if maintainer_file.name == "_index.md":
            continue
        
        content = maintainer_file.read_text()
        frontmatter, body = extract_frontmatter(content)
        if not frontmatter:
            continue
        
        # Get projects
        match = re.search(r'(projects\s*=\s*\[.*?)\]', frontmatter, re.DOTALL)
        if not match:
            continue
        
        original_projects = parse_projects_from_frontmatter(frontmatter)
        valid_projects = []
        invalid_projects = []
        
        for project_name in original_projects:
            slug = find_matching_slug(project_name, title_to_slug)
            if slug:
                # Use the actual project title from the slug mapping
                valid_projects.append(project_name)
            else:
                invalid_projects.append(project_name)
        
        if invalid_projects:
            print(f"\n{maintainer_file.stem}:")
            print(f"  Keeping: {valid_projects}")
            print(f"  Removing: {invalid_projects}")
            cleaned_count += 1
    
    return cleaned_count


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Link maintainers to projects")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--clean", action="store_true", help="Also clean invalid projects from maintainers")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Linking Maintainers to Projects")
    print("=" * 60)
    
    # Create mappings
    print("\n1. Creating project mappings...")
    slug_to_title, title_to_slug = create_project_mappings()
    print(f"   Found {len(slug_to_title)} projects")
    
    # Process maintainers
    print("\n2. Processing maintainers...")
    project_to_maintainers = process_maintainers(title_to_slug)
    print(f"   Found {len(project_to_maintainers)} projects with maintainers")
    
    # Show summary
    print("\n3. Projects and their maintainers:")
    for slug in sorted(project_to_maintainers.keys()):
        maintainers = project_to_maintainers[slug]
        print(f"   {slug}: {maintainers}")
    
    # Update project files
    print(f"\n4. {'[DRY RUN] ' if args.dry_run else ''}Updating project files...")
    update_project_maintainers(project_to_maintainers, dry_run=args.dry_run)
    
    # Clean invalid projects
    if args.clean:
        print(f"\n5. {'[DRY RUN] ' if args.dry_run else ''}Cleaning invalid projects from maintainers...")
        cleaned = clean_maintainer_projects(title_to_slug, dry_run=args.dry_run)
        print(f"   Found {cleaned} maintainers with invalid projects")
    
    print("\n" + "=" * 60)
    if args.dry_run:
        print("DRY RUN complete. Use --dry-run=false to apply changes.")
    else:
        print("Done!")


if __name__ == "__main__":
    main()
