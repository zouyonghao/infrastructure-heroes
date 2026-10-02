#!/usr/bin/env python3
"""
Script to update project logos with accessible URLs.
Uses well-known CDN sources and official brand resources.

The slug -> URL mapping lives in ``scripts/logo_urls.json`` (single source of
truth, also consumed by ``check_urls.py``). Keys are project slugs, i.e. the
markdown filename in ``content/projects/`` without the ``.md`` extension.

An empty URL means "no standard logo is known"; such slugs are skipped
(their ``logo = ''`` is left as-is). Currently only ``apt`` is empty.
"""

import json
import os
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
LOGO_URLS_PATH = SCRIPT_DIR / "logo_urls.json"


def load_logo_urls(path: Path = LOGO_URLS_PATH) -> dict:
    """Load the project slug -> logo URL mapping."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


LOGO_URLS = load_logo_urls()


def update_project_logo(filepath, logo_url):
    """Update the logo field in a project markdown file.

    Only fills an empty ``logo = ''`` line; a logo that is already set is
    never overwritten. Returns True when the file was changed.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if logo is already set (not empty)
    if re.search(r"^logo = '[^']+'", content, flags=re.MULTILINE):
        return False  # Already has a logo

    # Replace the logo line only if it's empty
    new_content = re.sub(
        r"^logo = ''",
        f"logo = '{logo_url}'",
        content,
        flags=re.MULTILINE,
    )

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def main():
    projects_dir = REPO_ROOT / "content" / "projects"

    updated = 0
    skipped = 0

    for filename in os.listdir(projects_dir):
        if not filename.endswith(".md") or filename == "_index.md":
            continue

        project_name = filename.replace(".md", "")
        filepath = os.path.join(projects_dir, filename)

        if project_name in LOGO_URLS:
            logo_url = LOGO_URLS[project_name]
            if update_project_logo(filepath, logo_url):
                print(
                    f"Updated: {project_name} -> {logo_url[:60]}..."
                    if logo_url
                    else f"Cleared: {project_name}"
                )
                updated += 1
            else:
                skipped += 1
        else:
            print(f"No mapping for: {project_name}")

    print(f"\nDone! Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
