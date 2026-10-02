#!/usr/bin/env python3
"""
Add GitHub links to project files based on mapping
Usage: python scripts/add-github-links.py
"""

import json
import re
from pathlib import Path

# Resolve paths relative to the repository root, not the current directory.
REPO_ROOT = Path(__file__).resolve().parent.parent
MAPPING_FILE = Path(__file__).resolve().parent / 'project-github-mapping.json'
PROJECTS_DIR = REPO_ROOT / 'content/projects'

FRONTMATTER_RE = re.compile(r'\A\+\+\+\r?\n(.*?)\r?\n\+\+\+', re.DOTALL)

with MAPPING_FILE.open('r', encoding='utf-8') as f:
    mapping = json.load(f)

updated = 0
skipped = 0
not_found = []

for project_file in sorted(PROJECTS_DIR.glob('*.md')):
    if project_file.name == '_index.md':
        continue

    project_name = project_file.stem

    if project_name not in mapping:
        not_found.append(project_name)
        continue

    github_repo = mapping[project_name]

    content = project_file.read_text(encoding='utf-8')

    # Find the frontmatter; only skip when [links] is already inside it.
    match = FRONTMATTER_RE.match(content)
    if not match:
        print(f"⚠️ No frontmatter found in {project_file}")
        continue

    frontmatter = match.group(1)
    if re.search(r'^\s*\[links\]\s*$', frontmatter, re.MULTILINE):
        skipped += 1
        continue

    # Add links section before the closing +++
    links_section = f'\n[links]\n  github = "{github_repo}"\n'
    new_frontmatter = frontmatter.rstrip() + links_section
    new_content = content[:match.start(1)] + new_frontmatter + content[match.end(1):]

    project_file.write_text(new_content, encoding='utf-8')

    print(f"✅ Added GitHub link to {project_name}: {github_repo}")
    updated += 1

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  Updated: {updated}")
print(f"  Skipped (already has links): {skipped}")
print(f"  Not in mapping: {len(not_found)}")

if not_found:
    print(f"\nProjects not in mapping:")
    for name in not_found:
        print(f"  - {name}")
