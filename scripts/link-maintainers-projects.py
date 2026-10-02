#!/usr/bin/env python3
"""
Link maintainers to projects bidirectionally.

This script:
1. Reads all maintainer files and extracts their projects
2. Maps project titles to project slugs
3. Adds a top-level 'maintainers' field to project files
4. Reports maintainer 'projects' entries that do not match a cataloged
   project (report only -- never deletes)

Runs as a dry-run by default; pass --apply to write changes.
"""

import re
import json
import tomllib
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


def build_maintainers_line(maintainers: list) -> str:
    """Render a TOML ``maintainers`` assignment line."""
    items = ", ".join(json.dumps(m, ensure_ascii=False) for m in maintainers)
    return f"maintainers = [{items}]"


FRONTMATTER_END = re.compile(r'\n\+\+\+\s*\n')


def replace_frontmatter(text: str, new_frontmatter: str) -> str:
    """Return ``text`` with its TOML frontmatter replaced, fences kept.

    Uses the same boundaries as :func:`extract_frontmatter`, so the leading
    ``+++`` and the newline after it are preserved byte for byte.
    """
    if not text.startswith("+++"):
        return text
    match = FRONTMATTER_END.search(text[3:])
    if not match:
        return text
    end = 3 + match.start()
    return text[:3] + new_frontmatter + text[end:]


def _maintainers_index(lines: list):
    """Index of a top-level ``maintainers =`` assignment line, else None."""
    for i, line in enumerate(lines):
        if re.match(r"^maintainers\s*=", line):
            return i
    return None


def _first_table_index(lines: list):
    """Index of the first TOML table header line, else None."""
    for i, line in enumerate(lines):
        if line.lstrip().startswith("["):
            return i
    return None


def update_project_maintainers(project_to_maintainers: dict, dry_run: bool = True):
    """Add a top-level ``maintainers`` field to project files.

    The key is written before the first ``[table]`` so it stays a top-level
    parameter (upstream reads ``.Params.maintainers``). Running this twice is
    idempotent: an existing top-level key is never duplicated or moved, and a
    relocated one is complete after the first run.
    """
    for slug, maintainers in project_to_maintainers.items():
        project_file = PROJECTS_DIR / f"{slug}.md"
        if not project_file.exists():
            continue

        content = project_file.read_text(encoding="utf-8")
        frontmatter, _ = extract_frontmatter(content)
        if frontmatter is None:
            print(f"  ERROR: No frontmatter found in {slug}")
            continue

        # keepends preserves every byte of the original frontmatter.
        lines = frontmatter.splitlines(keepends=True)
        existing = _maintainers_index(lines)
        table = _first_table_index(lines)

        if existing is not None and (table is None or existing < table):
            # Already a top-level key: leave it (and its value) untouched.
            print(f"  SKIP: {slug} already has top-level maintainers")
            continue

        if existing is not None:
            # Key exists but sits inside a table (e.g. [links]): move that
            # exact line up to the top level without changing its value.
            line = lines.pop(existing)
            if not line.endswith("\n"):
                line += "\n"
            table = _first_table_index(lines)
            insert_at = table if table is not None else len(lines)
            action = "RELOCATE"
        else:
            line = build_maintainers_line(maintainers) + "\n"
            insert_at = table if table is not None else len(lines)
            action = "UPDATE"

        # Keep statements separated when the line before the insertion point
        # (e.g. the last scalar key) had no trailing newline.
        if insert_at > 0 and not lines[insert_at - 1].endswith("\n"):
            lines[insert_at - 1] += "\n"
        lines.insert(insert_at, line)

        new_frontmatter = "".join(lines)

        # Never write TOML we cannot parse back (protects already-broken files).
        try:
            tomllib.loads(new_frontmatter)
        except tomllib.TOMLDecodeError as exc:
            print(f"  ERROR: refusing to write invalid TOML for {slug}: {exc}")
            continue

        if dry_run:
            print(f"  WOULD {action}: {slug} -> {line}")
        else:
            project_file.write_text(
                replace_frontmatter(content, new_frontmatter), encoding="utf-8"
            )
            print(f"  {action}D: {slug}")


def clean_maintainer_projects(title_to_slug: dict):
    """
    Report maintainer 'projects' entries that do not match a cataloged project.

    Report only: nothing is ever removed. Unmatched entries are legitimate
    "known for" data (e.g. foundational work outside this catalog), so they
    are kept. Returns the number of maintainers with unmatched entries.
    """
    reported = 0

    for maintainer_file in MAINTAINERS_DIR.glob("*.md"):
        if maintainer_file.name == "_index.md":
            continue

        content = maintainer_file.read_text(encoding="utf-8")
        frontmatter, _ = extract_frontmatter(content)
        if not frontmatter:
            continue

        original_projects = parse_projects_from_frontmatter(frontmatter)
        matched_projects = []
        unmatched_projects = []

        for project_name in original_projects:
            if find_matching_slug(project_name, title_to_slug):
                matched_projects.append(project_name)
            else:
                unmatched_projects.append(project_name)

        if unmatched_projects:
            print(f"\n{maintainer_file.stem}:")
            print(f"  Matched:   {matched_projects}")
            print(f"  Unmatched (kept, not removed): {unmatched_projects}")
            reported += 1

    return reported


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Link maintainers to projects")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to project files (default is a dry run)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Report maintainer 'projects' entries that match no cataloged "
        "project (report only, never deletes)",
    )
    args = parser.parse_args()
    dry_run = not args.apply

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
    print(f"\n4. {'[DRY RUN] ' if dry_run else ''}Updating project files...")
    update_project_maintainers(project_to_maintainers, dry_run=dry_run)

    # Report unmatched projects (never deletes)
    if args.clean:
        print("\n5. Reporting maintainer 'projects' with no catalog match...")
        reported = clean_maintainer_projects(title_to_slug)
        print(f"   {reported} maintainers have unmatched entries (kept)")

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN complete. Re-run with --apply to write changes.")
    else:
        print("Done!")


if __name__ == "__main__":
    main()
