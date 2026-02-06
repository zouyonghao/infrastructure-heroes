#!/usr/bin/env python3
"""
Add GitHub links to project files based on mapping
Usage: python scripts/add-github-links.py
"""

import json
import os
import re
from pathlib import Path

# Load mapping
with open('scripts/project-github-mapping.json', 'r') as f:
    mapping = json.load(f)

projects_dir = Path('content/projects')
updated = 0
skipped = 0
not_found = []

for project_file in sorted(projects_dir.glob('*.md')):
    if project_file.name == '_index.md':
        continue
    
    project_name = project_file.stem
    
    if project_name not in mapping:
        not_found.append(project_name)
        continue
    
    github_repo = mapping[project_name]
    
    with open(project_file, 'r') as f:
        content = f.read()
    
    # Check if already has links section
    if '[links]' in content:
        skipped += 1
        continue
    
    # Find the frontmatter end
    match = re.search(r'\+\+\+(.*?)\+\+\+', content, re.DOTALL)
    if not match:
        print(f"⚠️ No frontmatter found in {project_file}")
        continue
    
    frontmatter = match.group(1)
    
    # Add links section before the closing +++
    links_section = f'''\n[links]
  github = "{github_repo}"
'''
    
    new_frontmatter = frontmatter.rstrip() + links_section
    new_content = content.replace(match.group(0), f'+++{new_frontmatter}+++')
    
    with open(project_file, 'w') as f:
        f.write(new_content)
    
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
